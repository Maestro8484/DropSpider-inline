#include "machine.h"
#include "config.h"
#include "settings.h"
#include "console.h"
#include "radar.h"
#include <ESP32Servo.h>
#include <FastAccelStepper.h>
#include <soc/gpio_reg.h>

// FastAccelStepper makes the step pulses in the ESP32's own pulse hardware, so a
// rewind runs smoothly while WiFi, the web page and the console carry on. The
// Rev C handoff firmware timed each pulse by hand and froze everything else for
// the 2 to 3 s of a rewind.
static FastAccelStepperEngine engine;
static FastAccelStepper *stepper = nullptr;
static Servo pawl;

enum St {
  ST_BOOT, ST_IDLE, ST_LOCKOUT, ST_WAIT_CLEAR, ST_FAULT,          // at rest
  ST_RELEASE, ST_DROP, ST_SETTLE, ST_REWIND, ST_RETRY_DOWN, ST_RETRY_WAIT,   // cycle
  ST_LOCK_IN, ST_LOCK_SEAT, ST_LOCK_HOLD,                         // cycle or bench
  ST_JOG, ST_BENCH_REL, ST_BENCH_SERVO, ST_BENCH_FREE             // bench only
};

struct Req { Action a; long arg; TriggerSource src; };
static QueueHandle_t queue;

static volatile St state = ST_BOOT;
static uint32_t stateSince = 0;
static bool cycle = false;              // true while running a full drop cycle
static St   benchReturn = ST_WAIT_CLEAR;

static bool driverIsOn = false;
// A dead stop (the switch cut-off) in stealthChop can leave the TMC2209 in a current
// state "from which it cannot recover" or with its outputs switched off on a short
// flag (datasheet rev 1.05 p42); only EN high and low again clears it. Owner found
// the motor nearly free with the driver "on" after such a stop (2026-10-06).
static bool driverSuspect = false;
static int  servoDeg = DEF_SERVO_LOCK;
static bool fingerHeldOut = false;      // servo attached and holding the finger at the release angle
static int  appliedDir = -1;
static bool movingUp = false;           // current move is in the rewind direction
static long moveStartPos = 0;
static bool cutByLimit = false;
static bool ignoreLimit = false;        // this rewind runs on the step count alone

// The switch is also watched by an interrupt, so one closure of any length stops
// the wind on the next tick (2 ms): a stalled motor shakes the flap, and a switch
// that chatters may never read closed for the debounce time. Stopping is always
// safe; winding on against the top is not.
static_assert(PIN_LIMIT >= 32 && PIN_LIMIT <= 39, "limIsr reads the GPIO32-39 input register");
static volatile bool limHit = false;          // closed at least once since the move started
static volatile uint32_t limCloses = 0;       // closed edges seen by the interrupt, bounce included
static uint32_t limPresses = 0;               // steady closures since power-up (what the page shows)
static uint32_t pressAt[3] = {0, 0, 0};        // the last three closures at rest, for the 3-press teach
static int pressN = 0;
static uint32_t limClosesAtStart = 0;
static void IRAM_ATTR limIsr() {
  bool low = !(REG_READ(GPIO_IN1_REG) & BIT(PIN_LIMIT - 32));
  if (low != (S.limitInverted != 0)) { limHit = true; limCloses++; }
}

// Every motor move ends in a lock (finger in, spool let down onto a tooth, driver
// off), so the spider never hangs on the motor alone (owner 2026-10-06: it ran the
// whole line every time it did). After the switch stops a wind, or a rewind stalls,
// the seat move is the 1/8 turn back-off, so the bead rests clear of the flap.
static long lockSeatSteps = SEAT_STEPS;
static const char *lockDoneMsg = "lock: finger in, seated, motor off";
// A wind that ran its whole count with the switch fitted and never closing has
// pulled the spider hard against the top: let it down onto the finger and stop.
static bool faultNow = false;

static long lastRewind = 0;
static bool lastRewindLimit = false;
static int  measuredDrop = 0;

// Rev C.1 drop
static long unloadRan = 0;              // what the unload move actually ran (the switch may cut it)
static long lastDropSteps = 0;          // what the last powered drop was told to run
static bool decelApplied = false;       // the drop has switched to its stopping rate
static int32_t dropDecNow = 0;          // stopping rate for the drop in progress
static uint32_t dropStartMs = 0;
static uint32_t landMs = 0;             // trigger to the end of the drop, last cycle (the page uses it to check the fire distance)

// V14: after a rewind stopped by the switch and a seat move, the spider sits on the
// finger with the switch reading open. homeFlag remembers that (also kept in flash).
static bool upByLimit = false;          // last motion was a rewind that the switch stopped
static bool homeFlag = false;

static TriggerSource lastTrigger = TRIG_NONE;
static uint32_t lastTriggerMs = 0;
static const char *fault = "";
static int faultRun = 0;
static uint32_t drops = 0;

// inputs
static bool sensorNow = false, sensorLast = false;   // the trigger condition
static bool clearNow = true, clearLast = true;       // the doorway is empty (or everyone is far)
static bool viaRadar = false;                        // trigger read from the radar's serial link, not the OUT pin
static uint32_t highSince = 0, lowSince = 0;
static bool btnStable = true, btnLast = true, btnWas = true;
static uint32_t btnAt = 0;
static bool limStable = false, limLast = false;
static uint32_t limAt = 0;

// ---------------------------------------------------------------- helpers

static void enter(St s) { state = s; stateSince = millis(); }
static uint32_t inState() { return millis() - stateSince; }

static bool atRest(St s) { return s == ST_BOOT || s == ST_IDLE || s == ST_LOCKOUT || s == ST_WAIT_CLEAR || s == ST_FAULT; }

static const char *stateName(St s) {
  switch (s) {
    case ST_BOOT:        return "starting up";
    case ST_IDLE:        return "ready";
    case ST_LOCKOUT:     return "lockout after a scare";
    case ST_WAIT_CLEAR:  return "waiting for the doorway to clear";
    case ST_FAULT:       return "stopped, needs a look";
    case ST_RELEASE:     return "finger out, spool unloading";
    case ST_DROP:        return "spider dropping (motor leading)";
    case ST_SETTLE:      return "spider hanging";
    case ST_REWIND:      return "rewinding";
    case ST_RETRY_DOWN:  return "missed the switch: lowering 1/2 turn to try again";
    case ST_RETRY_WAIT:  return "missed the switch: letting the swing settle";
    case ST_LOCK_IN:     return "finger going in";
    case ST_LOCK_SEAT:   return "spool settling onto the finger";
    case ST_LOCK_HOLD:   return "finger holding, motor off";
    case ST_JOG:         return "jogging the motor";
    case ST_BENCH_REL:   return "finger out (bench)";
    case ST_BENCH_SERVO: return "moving the finger (bench)";
    case ST_BENCH_FREE:  return "finger out before the motor turns (bench)";
  }
  return "unknown";
}

const char *triggerName(TriggerSource t) {
  switch (t) {
    case TRIG_SENSOR:  return "radar";
    case TRIG_BUTTON:  return "BOOT button";
    case TRIG_CONSOLE: return "serial console";
    case TRIG_WEB:     return "web page";
    default:           return "nothing yet";
  }
}

long rewindSteps() {
  const float circ = PI * BARREL_DIA_MM;
  float turns = (S.lineMm - SPOOL_TO_EYELET_MM) / circ + OVERSHOOT_TURNS;
  if (turns < 0.5f) turns = 0.5f;
  return (long)(turns * STEPS_PER_TURN);
}

static float mmPerStep() { return PI * BARREL_DIA_MM / STEPS_PER_TURN; }

static void applyDir();

// Coming from off: enable, one microstep up and back, then hold still DRIVER_SETTLE_MS.
// The TMC2209's stealthChop tunes itself at standstill (AT#1, at least 130 ms,
// datasheet p35) and needs the run current for it; with the standstill current cut
// on (PDN_UART low on this board) only a step pulse brings the run current back, so
// the settle without the nudge tuned at half current. Starting 5 ms after enable
// gave an electronic chirp on the release and an untuned first move (owner 2026-10-06).
static void driverOn()  {
  if (driverIsOn) return;
  digitalWrite(PIN_EN, LOW); driverIsOn = true; driverSuspect = false;
  delay(5);
  applyDir();
  stepper->setSpeedInHz(400); stepper->setAcceleration(4000);
  stepper->move(1);  while (stepper->isRunning()) delay(1);
  stepper->move(-1); while (stepper->isRunning()) delay(1);
  delay(DRIVER_SETTLE_MS);
}
static void driverOff() { digitalWrite(PIN_EN, HIGH); driverIsOn = false; }

// EN high clears the driver's error state and its stuck regulation; the coils are
// unpowered for 20 ms, then driverOn's nudge and settle. Call it with the finger in,
// or at the top of the line where nothing can fall far.
static void driverReset() {
  driverOff(); delay(20); driverOn();
}

static void servoWrite(int deg) {
  deg = constrain(deg, 0, 180);
  if (!pawl.attached()) pawl.attach(PIN_SERVO, 500, 2400);
  pawl.write(deg);
  servoDeg = deg;
  fingerHeldOut = (deg == S.servoRel);
}
static void servoOff() { if (pawl.attached()) pawl.detach(); fingerHeldOut = false; }

static bool limitHome() { return S.limitFitted && limStable; }

static void setHome(bool h) { homeFlag = h; homeSave(h); }
static void homeLost() { upByLimit = false; setHome(false); }
// Where the spider is: at the top (switch pressed, or locked after a rewind the switch
// stopped). A drop from anywhere else cannot be wound back to the switch, because the
// rewind after a drop is capped at the drop's own length (2026-10-12: a boot with the
// spider down re-armed, fired, and left it hanging part way up).
static bool homeKnown() { return !S.limitFitted || limitHome() || homeFlag; }

// Teach (owner 2026-10-12): the spider hangs where a drop should stop; the switch
// pressed 3 times fast, or `teach`, winds it up to the switch and counts the steps,
// and that count becomes the drop distance.
static bool teaching = false;
static int teachWasArmed = 0;
// Rehome (owner 2026-10-13, 3 presses of the switch): from anywhere, lower 1/2 turn
// so the stopper is surely below the flap, then wind slowly to the switch.
static bool rehoming = false;
static int rehomeWasArmed = 0;
// A rewind that misses the switch gets one slow second try (lower 1/2 turn, settle,
// wind 2 1/2 turns at FEED_RPM). rewindCarry holds what the first wind netted.
static bool rewindRetried = false;
static long rewindCarry = 0;
static long slowAt = 0;                 // steps into a rewind where it drops to FEED_RPM; 0 = never

// The last cycles, for the page (owner 2026-10-14). recKind is set where the rewind
// decides how it ended, because startLock's seat move clears cutByLimit, and the
// record is written once the lock has finished (never during a move).
static CycleRec cycles[CYCLES_KEPT];
static int cycN = 0;                    // records held
static uint32_t cycSeq = 0;             // bumps at every record
static int recKind = -1;                // -1 = nothing to record at the end of this lock
static uint8_t recEnding = 0;

static void cyclesStore() {
  uint8_t blob[4 + sizeof cycles];
  memcpy(blob, &cycN, 4);
  memcpy(blob + 4, cycles, sizeof cycles);
  cyclesSave(blob, sizeof blob);
}

static void recordCycle(uint8_t kind, uint8_t ending) {
  if (cycN == CYCLES_KEPT) memmove(cycles, cycles + 1, sizeof(CycleRec) * (CYCLES_KEPT - 1));
  else cycN++;
  CycleRec &r = cycles[cycN - 1];
  r.n = kind == 0 ? drops : 0;
  r.upSec = millis() / 1000;
  r.boot = (uint16_t)bootCount();
  r.kind = kind;
  r.trigger = (uint8_t)lastTrigger;
  r.ending = ending;
  r.home = limitHome() || homeFlag;
  r.toldMm = (uint16_t)S.dropMm;
  r.measMm = (uint16_t)(ending == 0 || ending == 1 ? measuredDrop : 0);
  r.landMs = (uint16_t)min(landMs, (uint32_t)65535);
  cycSeq++;
  cyclesStore();
}

uint32_t cyclesSeq() { return cycSeq; }

String cyclesJson() {
  String j = "{\"boot\":" + String(bootCount()) + ",\"uptime\":" + String(millis() / 1000) + ",\"seq\":" + String(cycSeq) + ",\"cycles\":[";
  for (int i = cycN - 1; i >= 0; i--) {
    const CycleRec &r = cycles[i];
    if (i != cycN - 1) j += ",";
    j += "{\"n\":" + String(r.n) + ",\"up\":" + String(r.upSec) + ",\"boot\":" + String(r.boot) +
         ",\"kind\":" + String(r.kind) + ",\"trig\":\"" + triggerName((TriggerSource)r.trigger) + "\"" +
         ",\"end\":" + String(r.ending) + ",\"home\":" + String(r.home) + ",\"told\":" + String(r.toldMm) +
         ",\"meas\":" + String(r.measMm) + ",\"land\":" + String(r.landMs) + "}";
  }
  j += "]}";
  return j;
}

static void applyDir() {
  if (appliedDir != S.rewindDir) {
    stepper->setDirectionPin(PIN_DIR, S.rewindDir == 1);
    appliedDir = S.rewindDir;
  }
}

// Start a move of n microsteps at rpm, + = rewind direction. Driver must already
// be on. Reaches full speed within RAMP_STEPS.
static bool startMove(long n, int rpm) {
  applyDir();
  uint32_t hz = (uint32_t)rpm * STEPS_PER_TURN / 60;
  stepper->setSpeedInHz(hz);
  stepper->setAcceleration((int32_t)((uint64_t)hz * hz / (2 * RAMP_STEPS)));
  movingUp = n > 0;
  cutByLimit = false;
  limHit = false;
  limClosesAtStart = limCloses;
  moveStartPos = stepper->getCurrentPosition();
  return stepper->move(n) == MOVE_OK;
}

static void haltMotor() {
  if (stepper->isRunning()) stepper->forceStopAndNewPosition(stepper->getCurrentPosition());
}

static void strike(const char *why) {
  fault = why;
  faultRun++;
  logf("[fault %d of %d] %s", faultRun, FAULT_STRIKES, why);
  logSnapshot();
}

static void disarmForBench() {
  if (S.armed) { S.armed = 0; logf("disarmed for bench work (not saved). Send 'arm' when done."); }
}

// ---------------------------------------------------------------- inputs

static void readInputs() {
  uint32_t now = millis();

  // The trigger. sensor 4002: the radar's serial rule (two readings in a row of someone
  // approaching fast enough to arrive within leadms); if the link goes silent for
  // RADAR_SILENT_MS the sensor's OUT pin on GPIO33 carries it until frames return.
  // sensor 2410: the OUT pin only. The doorway is clear when the radar sees nobody
  // within the setting clearcm, or the pin reads low.
  bool pin = digitalRead(PIN_SENSOR) == HIGH;
  bool link = S.sensor == 4002 && radarTalking();
  if (link != viaRadar) {
    if (S.sensor == 4002 && now > 5000)
      logf(link ? "[radar] frames back: the trigger is the radar's serial rule again"
                : "[radar] FAULT: no result frame for %d ms. The trigger is the OUT pin on GPIO33 until frames return", RADAR_SILENT_MS);
    viaRadar = link;
  }
  sensorNow = link ? radarFire() : pin;
  clearNow = link ? radarClear() : !pin;
  if (sensorNow && !sensorLast) highSince = now;
  if (clearNow && !clearLast) lowSince = now;
  sensorLast = sensorNow; clearLast = clearNow;

  bool b = digitalRead(PIN_BUTTON) == HIGH;             // true = not pressed
  if (b != btnLast) { btnLast = b; btnAt = now; }
  if (now - btnAt >= BUTTON_DEBOUNCE_MS) btnStable = b;

  bool l = digitalRead(PIN_LIMIT) == LOW;               // pulled up; pressed pulls LOW
  if (S.limitInverted) l = !l;
  if (l != limLast) { limLast = l; limAt = now; }
  if (now - limAt >= LIMIT_DEBOUNCE_MS && limStable != l) {
    limStable = l;
    if (l) limPresses++;
    if (l) { if (atRest(state)) pressAt[pressN++ % 3] = now; else pressN = 0; }
    logf("[limit] switch %s", l ? "closed" : "open");
  }
}

static bool buttonEdge() {
  bool edge = btnWas && !btnStable;
  btnWas = btnStable;
  return edge;
}

// ---------------------------------------------------------------- sequences

// M2: the finger cannot swing out while the spider's weight presses a tooth onto
// it. The motor winds the spool up about 1/12 turn at the same moment, so the
// finger rides up the tooth's ramp and out. The driver stays on from here to the
// end of the lock: an unpowered motor drags too much for a clean drop.
static void startRelease() {
  homeLost();
  driverOn();
  ignoreLimit = false;                        // the limit cut-off still guards the unload
  servoWrite(S.servoRel);
  if (!startMove(UNLOAD_STEPS, UNLOAD_RPM)) logf("[release] unload move would not start");
}

// Called once the unload has finished: how far it really went. A switch cut is a
// dead stop, so the driver is reset here, at the top, before anything moves down.
static void noteUnload() {
  unloadRan = stepper->getCurrentPosition() - moveStartPos;
  if (cutByLimit) {
    logf("[release] unload cut short by the limit switch after %ld of %d steps; driver reset", unloadRan, UNLOAD_STEPS);
    driverReset();
  }
}

// The drop in microsteps: the set drop plus whatever the unload wound up, never
// closer than DROP_KNOT_MARGIN_MM to the barrel knot.
static long dropSteps() {
  int mm = S.dropMm;
  if (mm > dropMmMax()) mm = dropMmMax();
  if (mm < 0) mm = 0;
  return (long)(mm / mmPerStep()) + unloadRan;
}

// Motor-led drop: the motor unwinds ahead of the spool, the spool falls behind it
// on the clutch and can never pass it, so the motor sets the top speed and the
// stopping point. FastAccelStepper 0.33.14 has one acceleration per move, so the
// drop starts at dropAcc and step() switches to dropDec when the stop has to begin.
static void startDrop() {
  if (S.dropMm > dropMmMax())
    logf("[drop] dropmm %d reaches too near the knot for line %d mm: using %d", S.dropMm, S.lineMm, dropMmMax());
  long n = dropSteps();
  applyDir();
  stepper->setSpeedInHz((uint32_t)S.dropRpm * STEPS_PER_TURN / 60);
  stepper->setAcceleration(S.dropAcc);
  dropDecNow = S.dropDec;
  decelApplied = dropDecNow >= S.dropAcc;     // a stop as quick as the start needs no switch
  movingUp = false;
  cutByLimit = false;
  moveStartPos = stepper->getCurrentPosition();
  lastDropSteps = n;
  dropStartMs = millis();
  if (stepper->move(-n) != MOVE_OK) logf("[drop] motor would not start");
  enter(ST_DROP);
}

static void startCycle(TriggerSource src) {
  if (!homeKnown()) {
    static uint32_t warnedAt = 0;
    if (warnedAt == 0 || millis() - warnedAt > 10000) {
      warnedAt = millis();
      logf("[cycle] not dropping (%s): the spider is not home. Rewind it, or lower it to where a drop should stop "
           "and press the limit switch 3 times", triggerName(src));
    }
    return;
  }
  cycle = true;
  lastTrigger = src;
  lastTriggerMs = millis();
  dropCountBump();
  drops++;
  if (faultRun == 0) fault = "";
  if (src == TRIG_SENSOR) radarMarkFire(viaRadar);   // keep what the radar saw, for the page
  logf("[cycle] trigger: %s", triggerName(src));
  startRelease();
  enter(ST_RELEASE);
}

static void startRewind(int rpm = 0) {
  driverOn();
  homeLost();
  ignoreLimit = false;
  rewindRetried = false; rewindCarry = 0; slowAt = 0;
  if (limitHome()) {
    if (cycle) {
      // The spider has just fallen, so a pressed switch is lying. Wind the counted
      // length with the switch ignored; the bead stop ends it.
      strike("limit switch still pressed after a drop: check its wiring and the liminv setting");
      ignoreLimit = true;
      faultNow = true;
    } else {
      logf("[rewind] limit switch already pressed, spider is home, nothing to wind");
      moveStartPos = stepper->getCurrentPosition();
      movingUp = false; cutByLimit = false;
      lastRewind = 0; lastRewindLimit = true;
      upByLimit = true;
      enter(ST_REWIND);                       // finishes on the next tick
      return;
    }
  }
  // After a powered drop the spool is down only as far as the drop went, so wind
  // that plus the usual overshoot. The switch or the bead stop ends it first.
  long n = rewindSteps();
  if (cycle && lastDropSteps > 0) {
    n = min(n, lastDropSteps + (long)(OVERSHOOT_TURNS * STEPS_PER_TURN));
    slowAt = max(0L, n - (long)(FEED_ZONE_TURNS * STEPS_PER_TURN));   // fast most of the way, slow onto the switch
    if (slowAt == 0) rpm = FEED_RPM;
  }
  startMove(n, rpm ? rpm : S.rpm);
  enter(ST_REWIND);
}

// The wind ran its whole count, the switch fitted and never closing.
static bool rewindMissed() {
  return S.limitFitted && !cutByLimit && !ignoreLimit &&
         !(stepper->getCurrentPosition() == moveStartPos && limitHome());
}

// Returns true when the wind ran its whole count with the switch fitted and never
// closing: the spider is then pulled hard against the top.
static bool finishRewind() {
  long ran = stepper->getCurrentPosition() - moveStartPos + rewindCarry;
  uint32_t closes = limCloses - limClosesAtStart;
  bool alreadyHome = !cutByLimit && ran == 0 && limitHome();
  if (!alreadyHome) {
    lastRewind = ran;
    lastRewindLimit = cutByLimit;
  }
  if (cutByLimit) upByLimit = true;
  // What the rewind should run after a cycle: the drop, less the unload that went
  // up first. The seat move before the drop can add up to one unload more.
  long expected = lastDropSteps - unloadRan;
  if (S.limitFitted && !alreadyHome) {
    if (cutByLimit) {
      if (cycle && ran < (long)(REWIND_MIN_FRAC * expected)) {
        strike("limit switch tripped far too early: check for a snag or a broken line");
      } else if (cycle) {
        measuredDrop = (int)(ran * mmPerStep());
        long extra = ran - expected - UNLOAD_STEPS;
        if (extra * mmPerStep() > LOST_STEPS_WARN_MM)
          logf("[drop] rewind ran %d mm more than the motor was told to drop: the spool ran past the motor somewhere "
               "(counts are what the motor was told, not what turned)", (int)(extra * mmPerStep()));
        faultRun = 0; fault = "";
      }
    }
  }
  logf("[rewind] ran %ld steps (%.2f turns, %d mm)%s%s, switch edges seen %lu", ran, ran / (float)STEPS_PER_TURN,
       (int)(ran * mmPerStep()), cutByLimit ? ", stopped by the limit switch" : "",
       rewindRetried ? " on the second, slow try" : "", (unsigned long)closes);
  bool stalled = S.limitFitted && !alreadyHome && !cutByLimit && !ignoreLimit;
  if (stalled) {
    strike("full rewind ran without the limit switch closing: either the bead was already above the flap, "
           "or the spool did not follow the motor (one-way bearing slipping or in backwards)");
    faultNow = true;
  }
  return stalled;
}

// The teach wind reached the switch: what it ran, plus the unload before it, is the
// line from where the spider hung to the top. That becomes the drop distance (and the
// line length grows if the drop would not fit). Armed goes back to what it was.
static void finishTeach() {
  teaching = false;
  S.armed = teachWasArmed;
  long r = unloadRan + lastRewind;
  int mm = (int)lround(r * mmPerStep());
  int was = S.dropMm;
  if (mm < 100) {
    logf("[teach] only %d mm from where the spider hung to the switch: too short, drop distance kept at %d mm", mm, was);
    return;
  }
  String why;
  int lineNeed = mm + (int)SPOOL_TO_EYELET_MM + DROP_KNOT_MARGIN_MM;
  if (lineNeed > S.lineMm) {
    if (settingsSet("line", String(lineNeed), why)) logf("[teach] line raised to %d mm so the measured drop fits", lineNeed);
    else logf("[teach] line could not grow to %d mm: %s", lineNeed, why.c_str());
  }
  if (mm > dropMmMax()) mm = dropMmMax();
  if (!settingsSet("dropmm", String(mm), why)) { logf("[teach] drop distance not changed: %s", why.c_str()); return; }
  settingsSave();
  fault = ""; faultRun = 0;
  benchReturn = ST_WAIT_CLEAR;
  logf("[teach] wound %ld steps (%.2f turns, %d mm) from where the spider hung up to the switch: "
       "drop distance set to %d mm (was %d) and saved", r, r / (float)STEPS_PER_TURN, (int)lround(r * mmPerStep()), mm, was);
}

// The rehome wind reached the switch: home, fault cleared, armed as it was.
static void finishRehome() {
  rehoming = false;
  S.armed = rehomeWasArmed;
  fault = ""; faultRun = 0;
  benchReturn = ST_WAIT_CLEAR;
  long r = lastRewind - RETRY_DOWN_STEPS + unloadRan;
  logf("[rehome] home: the spider was about %d mm below the switch; fault cleared%s",
       (int)(r * mmPerStep()), S.armed ? ", armed" : ", not armed");
}

// Finger in while the motor holds, then (after a dead stop) the driver is reset
// with the finger in, then the motor lets the spool down onto a tooth (the seat
// move, 1.2/12 turn; the 1/8 turn back-off after the switch). Once a tooth lands
// the clutch slips and the motor runs on alone. Driver off after that, servo off
// after LOCK_SEAT_MS.
static void startLock(const char *done = "lock: finger in, seated, motor off", long seat = SEAT_STEPS) {
  lockDoneMsg = done;
  lockSeatSteps = seat;
  driverOn();                                 // already on after a move; holds the spool
  servoWrite(S.servoLock);
  enter(ST_LOCK_IN);
}

// Owner rule 2026-10-01: the motor never turns with the finger in, except the lock's
// seat move, whose job is to let the spool down onto the finger. So a bench jog or
// rewind first runs the release (finger out with the 1/12 turn unload, M2) unless
// the finger is already out, then the move itself.
static Action pendAct;
static long pendArg;

static void benchMove(Action a, long arg) {
  // Inverted install (2026-10-06): the bead flicks the flap as it passes and the
  // flap drops back behind it, so a second wind from the top never sees the switch
  // and pulls against the top for the whole count. Refuse it.
  if (upByLimit && (a == ACT_REWIND || arg > 0)) {
    logf("refused: the limit switch stopped the last wind and nothing has moved since, so the spider is already at the top. "
         "Send lock, or jog down first");
    if (teaching) { teaching = false; S.armed = teachWasArmed; }
    if (rehoming) { rehoming = false; S.armed = rehomeWasArmed; }
    enter(benchReturn);
    return;
  }
  if (a == ACT_JOG) {
    driverOn();
    homeLost();
    ignoreLimit = false;
    if (!startMove(arg, S.rpm)) { logf("refused: motor would not start"); enter(benchReturn); return; }
    enter(ST_JOG);
  } else {
    startRewind();
  }
}

static void benchMoveFingerOut(Action a, long arg) {
  disarmForBench(); cycle = false;
  if (fingerHeldOut) { benchMove(a, arg); return; }  // held by a powered servo, not just the last angle sent
  logf("[bench] finger out first (the motor never turns with the finger in)");
  pendAct = a; pendArg = arg;
  startRelease();
  enter(ST_BENCH_FREE);
}

static void benchDone(const char *what) {
  logf("[done] %s", what);
  enter(benchReturn);
}

// ---------------------------------------------------------------- requests

static bool isBusy() { return !atRest(state); }

bool machineRequest(Action a, long arg, TriggerSource src, String &why) {
  if (a == ACT_STOP || a == ACT_OFF) {
    haltMotor();                              // safe from any task, takes effect now
    Req r{a, arg, src};
    xQueueSendToFront(queue, &r, 0);
    return true;
  }
  if (a == ACT_CLEAR) {
    Req r{a, arg, src};
    xQueueSend(queue, &r, 0);
    return true;
  }
  if (isBusy()) { why = String("busy (") + stateName(state) + "), send stop first"; return false; }
  switch (a) {
    case ACT_DROP:
      if (state == ST_FAULT) { why = "stopped after faults, send clear first"; return false; }
      break;
    case ACT_JOG:
      if (arg == 0 || labs(arg) > 16000) { why = "steps must be -16000 to 16000, not 0"; return false; }
      if (arg > 0 && limitHome()) { why = "limit switch is pressed, will not wind further"; return false; }
      break;
    case ACT_SERVO:
      if (arg < 0 || arg > 180) { why = "angle must be 0 to 180"; return false; }
      break;
    default: break;
  }
  Req r{a, arg, src};
  if (xQueueSend(queue, &r, 0) != pdTRUE) { why = "queue full"; return false; }
  return true;
}

static void handleReq(const Req &r) {
  if (r.a == ACT_STOP || r.a == ACT_OFF) {
    haltMotor();
    bool wasCycle = cycle;
    if (isBusy()) homeLost();                 // stopped part way: nobody knows where the spider is
    if (isBusy() && (wasCycle || teaching || rehoming)) recordCycle(wasCycle ? 0 : teaching ? 2 : 1, 4);
    // A teach or rehome stopped part way is over: otherwise the next plain rewind
    // would finish it (and a stopped teach would set the drop length).
    if (teaching) { teaching = false; S.armed = teachWasArmed; }
    if (rehoming) { rehoming = false; S.armed = rehomeWasArmed; }
    recKind = -1;
    cycle = false;
    faultNow = false;
    if (r.a == ACT_OFF) { driverOff(); servoOff(); }
    disarmForBench();
    logf("[done] %s%s", r.a == ACT_OFF ? "off: motor and servo off" : "stop: everything halted, motor left as it was",
         wasCycle ? " (cycle aborted)" : "");
    enter(state == ST_FAULT ? ST_FAULT : ST_WAIT_CLEAR);
    return;
  }
  if (r.a == ACT_CLEAR) {
    fault = ""; faultRun = 0;
    if (state == ST_LOCKOUT || state == ST_WAIT_CLEAR) {
      enter(ST_IDLE);
      logf(S.armed ? "[done] cleared: armed now, lockout and doorway wait skipped" : "[done] cleared: ready now, not armed");
    } else {
      logf("[done] fault cleared");
      if (state == ST_FAULT) enter(ST_WAIT_CLEAR);
    }
    return;
  }
  if (isBusy()) { logf("refused: busy (%s)", stateName(state)); return; }
  benchReturn = (state == ST_FAULT) ? ST_FAULT : ST_WAIT_CLEAR;
  if (r.a == ACT_REHOME) {
    if (homeKnown()) {
      fault = ""; faultRun = 0;
      logf("[rehome] the spider is already home: fault cleared%s", S.armed ? ", armed" : ", not armed");
      if (state == ST_FAULT || state == ST_LOCKOUT) enter(ST_WAIT_CLEAR);
      return;
    }
    rehomeWasArmed = S.armed;
    rehoming = true;
    logf("[rehome] lowering 1/2 turn so the stopper is below the flap, then winding slowly up to the switch");
    benchMoveFingerOut(ACT_JOG, -RETRY_DOWN_STEPS);
    return;
  }
  if (r.a == ACT_TEACH) {
    if (!S.limitFitted) { logf("[teach] needs the limit switch fitted (limit 1)"); return; }
    if (limitHome() || homeFlag) {
      logf("[teach] the spider is already at the top. Lower it to where a drop should stop (page: -1 turn, -1/8), then press the switch 3 times");
      return;
    }
    teachWasArmed = S.armed;
    teaching = true;
    unloadRan = 0;
    logf("[teach] winding the spider up to the switch to measure the drop distance");
    benchMoveFingerOut(ACT_REWIND, 0);
    return;
  }
  switch (r.a) {
    case ACT_DROP:
      startCycle(r.src);
      break;
    case ACT_REL:
      disarmForBench(); cycle = false;
      startRelease(); enter(ST_BENCH_REL);
      break;
    case ACT_LOCK:
      disarmForBench(); cycle = false;
      startLock();
      break;
    case ACT_REWIND:
    case ACT_JOG:
      benchMoveFingerOut(r.a, r.arg);
      break;
    case ACT_SERVO:
      disarmForBench(); cycle = false;
      homeLost();                             // the finger may have let the spool go
      servoWrite(r.arg); enter(ST_BENCH_SERVO);
      break;
    default: break;
  }
}

// ---------------------------------------------------------------- the task

static void step() {
  readInputs();

  // HARD CUT-OFF: winding in and the limit switch is pressed, stop now, whatever
  // state this is. The bead stop at the eyelet is still the mechanical backstop.
  if (movingUp && !ignoreLimit && S.limitFitted && stepper->isRunning() && (limHit || limLast)) {
    haltMotor();
    cutByLimit = true;
    driverSuspect = true;                   // a dead stop: reset the driver before trusting it again
  }

  // Drop: switch to the gentler stopping rate just before the stop must begin.
  // Speed and position are the ramp generator's, which runs a few ms ahead of the
  // motor, so the margin only has to cover this task's own tick.
  if (state == ST_DROP && !decelApplied && stepper->isRunning()) {
    float v = labs(stepper->getCurrentSpeedInMilliHz(false)) / 1000.0f;
    long left = labs(stepper->targetPos() - stepper->getPositionAfterCommandsCompleted());
    if (left <= v * v / (2.0f * dropDecNow) + v * DECEL_MARGIN_S + DECEL_MARGIN_STEPS) {
      stepper->setAcceleration(dropDecNow);
      stepper->applySpeedAcceleration();
      decelApplied = true;
    }
  }

  Req r;
  if (xQueueReceive(queue, &r, 0) == pdTRUE) handleReq(r);

  uint32_t now = millis();
  bool pressed = buttonEdge();

  // Rehome by hand: the limit switch pressed 3 times within TEACH_WINDOW_MS while at
  // rest, then let go for TEACH_QUIET_MS (owner 2026-10-13: he pressed it 3 times to
  // recover a spider left part way down; setting the drop length is the page's job).
  if (pressN >= 3) {
    uint32_t first = pressAt[(pressN - 3) % 3], last = pressAt[(pressN - 1) % 3];
    if (!atRest(state) || now - last > TEACH_WINDOW_MS) pressN = 0;
    else if (last - first <= TEACH_WINDOW_MS && !limStable && now - limAt >= TEACH_QUIET_MS) {
      pressN = 0;
      logf("[rehome] limit switch pressed 3 times");
      handleReq(Req{ACT_REHOME, 0, TRIG_BUTTON});
    }
  }

  switch (state) {
    case ST_BOOT:
      if (inState() < 50) break;              // let the switch readings settle
      // V14: after a lock seat the switch reads open by design. Home is the switch
      // pressed, or the last lock having followed a rewind the switch stopped.
      if (S.limitFitted && !limitHome() && !homeFlag) {
        fault = "spider not home at power-up. Boot never rewinds on its own: rewind, or lower it to the drop length and press the switch 3 times.";
        logf("[boot] %s", fault);
        enter(ST_FAULT);
        break;
      } else if (S.limitFitted && !limitHome()) {
        logf("[boot] switch open, spider home from the last lock (seated below the switch)");
      }
      enter(ST_WAIT_CLEAR);
      lowSince = now;
      break;

    case ST_IDLE:
      if (pressed) { startCycle(TRIG_BUTTON); break; }
      if (S.armed && sensorNow && (viaRadar || now - highSince >= TRIGGER_DEBOUNCE_MS)) startCycle(TRIG_SENSOR);
      break;

    case ST_LOCKOUT:
      if (pressed) { startCycle(TRIG_BUTTON); break; }
      if (inState() >= (uint32_t)S.rearmMs) enter(ST_WAIT_CLEAR);
      break;

    case ST_WAIT_CLEAR:  // someone still standing there: wait until the doorway is empty
      if (pressed) { startCycle(TRIG_BUTTON); break; }
      if (clearNow && now - lowSince >= CLEAR_BEFORE_REARM) {
        enter(ST_IDLE);
        logf(S.armed ? "[armed] doorway clear" : "[ready] doorway clear, not armed");
      } else if (S.clearMs && inState() >= (uint32_t)S.clearMs) {
        enter(ST_IDLE);   // safe: the rule still wants a fresh approach before it fires
        logf(S.armed ? "[armed] re-armed after %d ms waiting (clearms), doorway not clear" : "[ready] after %d ms waiting (clearms), not armed", S.clearMs);
      }
      break;

    case ST_FAULT:
      if (pressed) { fault = ""; faultRun = 0; logf("[done] fault cleared by button"); enter(ST_WAIT_CLEAR); }
      break;

    case ST_RELEASE:
      // Never start the drop before the finger has finished its swing: relms (250)
      // was shorter than the finger's travel time (SERVO_MOVE_MS), and with setrel 30
      // the swing is 55 degrees (2026-10-06).
      if (inState() < (uint32_t)max((int)S.releaseMs, SERVO_MOVE_MS + 150) || stepper->isRunning()) break;
      noteUnload();
      startDrop();
      break;

    case ST_DROP: {
      if (stepper->isRunning()) break;
      long ran = moveStartPos - stepper->getCurrentPosition();
      logf("[drop] ran %ld steps (%d mm) in %lu ms at up to %d rpm; motor holding",
           ran, (int)(ran * mmPerStep()), (unsigned long)(millis() - dropStartMs), S.dropRpm);
      if (cycle && lastTriggerMs) landMs = millis() - lastTriggerMs;
      enter(ST_SETTLE);
      break;
    }

    case ST_SETTLE:
      if (inState() >= (uint32_t)S.settleMs) startRewind();
      break;

    case ST_REWIND:
      if (stepper->isRunning()) {
        if (slowAt && stepper->getCurrentPosition() - moveStartPos >= slowAt) {
          slowAt = 0;
          stepper->setSpeedInHz((uint32_t)FEED_RPM * STEPS_PER_TURN / 60);
          stepper->applySpeedAcceleration();
        }
        break;
      }
      if (!rewindRetried && rewindMissed()) {
        long ranFirst = stepper->getCurrentPosition() - moveStartPos + rewindCarry;
        rewindRetried = true;
        rewindCarry = ranFirst - RETRY_DOWN_STEPS;
        logf("[rewind] the switch did not close in %ld steps (%d mm): lowering 1/2 turn, then one slow try",
             ranFirst, (int)(ranFirst * mmPerStep()));
        if (!startMove(-RETRY_DOWN_STEPS, FEED_RPM)) logf("[rewind] lowering move would not start");
        enter(ST_RETRY_DOWN);
        break;
      }
      // Stalled against the top, or stopped by the switch: finger in now, driver reset
      // with the finger in, then the 1/8 turn back-off lets the spool down onto a tooth
      // and the bead clear of the flap. Owner rule 2026-10-06: the motor never loses
      // power before the finger is holding, and the spider never hangs on the motor
      // alone (it ran the whole line every time it did).
      recKind = cycle ? 0 : rehoming ? 1 : teaching ? 2 : -1;
      if (finishRewind()) {
        recEnding = 3;
        if (teaching) { teaching = false; logf("[teach] the switch never closed, so nothing was measured; drop distance kept at %d mm", S.dropMm); }
        if (rehoming) { rehoming = false; S.armed = rehomeWasArmed; logf("[rehome] the switch never closed: check the stopper meets the flap, and for a snag on the line"); }
        logf("[fault] full rewind without the switch: locking, then stopped. Send clear when it is fixed.");
        startLock("lock (stopped on a fault)", BACKOFF_STEPS);   // faultNow stays set: the lock ends in ST_FAULT
        break;
      }
      if (cutByLimit) {
        recEnding = rewindRetried ? 1 : 0;
        if (teaching) finishTeach();
        if (rehoming) finishRehome();
        startLock(cycle ? "drop" : "rewind (stopped by the switch, finger in, seated, motor off)", BACKOFF_STEPS);
        break;
      }
      recEnding = 2;
      if (teaching) { teaching = false; S.armed = teachWasArmed; }
      if (rehoming) { rehoming = false; S.armed = rehomeWasArmed; }
      startLock(cycle ? "drop" : "rewind (finger in, seated, motor off)");
      break;

    case ST_RETRY_DOWN:
      if (stepper->isRunning()) break;
      enter(ST_RETRY_WAIT);
      break;

    case ST_RETRY_WAIT:
      if (inState() < RETRY_SETTLE_MS) break;
      if (!startMove(RETRY_UP_STEPS, FEED_RPM)) logf("[rewind] second try would not start");
      enter(ST_REWIND);
      break;

    case ST_LOCK_IN:
      if (inState() < SERVO_MOVE_MS) break;
      if (driverSuspect) { logf("[lock] driver reset after the dead stop, finger in"); driverReset(); }
      ignoreLimit = false;
      if (!startMove(-lockSeatSteps, SEAT_RPM)) logf("[lock] seat move would not start");
      enter(ST_LOCK_SEAT);
      break;

    case ST_LOCK_SEAT:
      if (stepper->isRunning()) break;
      driverOff();
      enter(ST_LOCK_HOLD);
      break;

    case ST_LOCK_HOLD:
      if (inState() < LOCK_SEAT_MS) break;
      servoOff();
      setHome(upByLimit);
      logf("[lock] seated (let down %d mm). Limit switch %s%s", (int)(lockSeatSteps * mmPerStep()),
           !S.limitFitted ? "not fitted" : limitHome() ? "pressed" : "open",
           upByLimit ? "; spider home" : "; home not known (last rewind was not stopped by the switch)");
      if (recKind >= 0) { recordCycle((uint8_t)recKind, recEnding); recKind = -1; }
      if (faultNow) {
        faultNow = false; cycle = false;
        logf("[fault] stopped: %s. Send clear when it is fixed, or press the limit switch 3 times to bring it home.", fault);
        logf("[done] lock (stopped on a fault)");
        logSnapshot();
        enter(ST_FAULT);
      } else if (cycle) {
        cycle = false;
        if (faultRun >= FAULT_STRIKES) {
          logf("[cycle] done, %d faults in a row: stopped. Send clear, or press BOOT.", faultRun);
          logf("[done] drop (stopped on faults)");
          enter(ST_FAULT);
        } else {
          logf("[cycle] done, lockout %d ms", S.rearmMs);
          logf("[done] drop");
          enter(ST_LOCKOUT);
        }
      } else {
        benchDone(lockDoneMsg);
      }
      break;

    case ST_JOG:
      if (stepper->isRunning()) break;
      logf("[jog] ran %ld steps%s", stepper->getCurrentPosition() - moveStartPos,
           cutByLimit ? ", stopped by the limit switch" : "");
      if (rehoming) { startRewind(FEED_RPM); break; }
      if (cutByLimit) { startLock("jog (stopped by the switch, finger in, seated, motor off)", BACKOFF_STEPS); break; }
      startLock("jog (finger in, seated, motor off)");
      break;

    case ST_BENCH_FREE:
      if (inState() < (uint32_t)max((int)S.releaseMs, SERVO_MOVE_MS + 150) || stepper->isRunning()) break;
      noteUnload();
      benchMove(pendAct, pendArg);
      break;

    case ST_BENCH_REL:
      // The servo stays powered: it was detached after relms (250 ms), shorter than
      // the finger's own travel time (SERVO_MOVE_MS), so the finger could stop part
      // way out, near the teeth (2026-10-06). Lock, a jog, a rewind or off end it.
      if (inState() < (uint32_t)max((int)S.releaseMs, SERVO_MOVE_MS + 150) || stepper->isRunning()) break;
      noteUnload();
      benchDone("rel: finger out and held by the servo, motor on and holding the spider (jog to lower it, off lets it slide down)");
      break;

    case ST_BENCH_SERVO:
      if (inState() >= SERVO_MOVE_MS) {
        char buf[48]; snprintf(buf, sizeof buf, "servo %d (holding)", servoDeg);
        benchDone(buf);
      }
      break;
  }

  // LED (owner 2026-10-11): solid = armed and ready, fast blink = stopped on a fault
  // or the spider not home (send clear, rewind, or teach), slow blink = working,
  // off = not armed or waiting to re-arm
  bool led = false;
  if (state == ST_FAULT || (atRest(state) && !homeKnown())) led = (now / 150) % 2;
  else if (state == ST_IDLE && S.armed) led = true;
  else if (isBusy())               led = (now / 500) % 2;
  digitalWrite(PIN_LED, led);
}

static void task(void *) {
  for (;;) { step(); vTaskDelay(pdMS_TO_TICKS(MACHINE_TICK_MS)); }
}

// ---------------------------------------------------------------- public

void machineBegin() {
  // EN is already HIGH (coils off) from the first line of setup().
  pinMode(PIN_SENSOR, INPUT_PULLDOWN);
  pinMode(PIN_BUTTON, INPUT_PULLUP);
  pinMode(PIN_LIMIT, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_LIMIT), limIsr, CHANGE);
  pinMode(PIN_LED, OUTPUT);

  engine.init();
  stepper = engine.stepperConnectToPin(PIN_STEP);
  if (!stepper) logf("[boot] ERROR: stepper engine would not attach to GPIO%d", PIN_STEP);
  pinMode(PIN_DIR, OUTPUT);

  ESP32PWM::allocateTimer(0);
  pawl.setPeriodHertz(50);

  drops = dropCount();
  homeFlag = homeSaved();
  {
    uint8_t blob[4 + sizeof cycles];
    if (cyclesLoad(blob, sizeof blob) == sizeof blob) {
      memcpy(&cycN, blob, 4);
      if (cycN < 0 || cycN > CYCLES_KEPT) cycN = 0;
      memcpy(cycles, blob + 4, sizeof cycles);
    }
  }
  if (faultLogLoad().length()) logf("[boot] the log up to the last fault is kept: send lastlog (page: Last fault log)");
  limLast = limStable = [] { bool l = digitalRead(PIN_LIMIT) == LOW; return S.limitInverted ? !l : l; }();
  btnLast = btnStable = btnWas = digitalRead(PIN_BUTTON) == HIGH;
  limAt = btnAt = millis();

  // Assume the spider is up. Seat the finger; never auto-rewind at boot.
  servoWrite(S.servoLock); delay(SERVO_MOVE_MS + 300); servoOff();

  queue = xQueueCreate(8, sizeof(Req));
  enter(ST_BOOT);
  xTaskCreatePinnedToCore(task, "machine", 4096, nullptr, 2, nullptr, 1);
}

void machineSafeStop() {
  haltMotor();
  driverOff();
  servoOff();
  // The task handles the queue before it looks at its state, so the cycle is
  // aborted on its next tick rather than carrying on with the lock sequence.
  Req r{ACT_OFF, 0, TRIG_NONE};
  xQueueSendToFront(queue, &r, 0);
}

MachineStatus machineStatus() {
  MachineStatus m;
  m.state = stateName(state);
  m.busy = isBusy();
  m.armed = S.armed;
  m.sensor = sensorNow;
  m.viaRadar = viaRadar;
  m.limitRaw = limStable;
  m.limitCloses = limPresses;
  m.limitFitted = S.limitFitted;
  m.home = limitHome() || homeFlag;
  m.driverOn = driverIsOn;
  m.servoAttached = pawl.attached();
  m.servoDeg = servoDeg;
  m.motorRunning = stepper && stepper->isRunning();
  m.position = stepper ? stepper->getCurrentPosition() : 0;
  m.rewindSteps = rewindSteps();
  m.lastRewindSteps = lastRewind;
  m.lastRewindByLimit = lastRewindLimit;
  m.measuredDropMm = measuredDrop;
  m.drops = drops;
  m.lastTrigger = lastTrigger;
  m.lastTriggerAgoMs = lastTriggerMs ? millis() - lastTriggerMs : 0;
  m.landMs = landMs;
  m.fault = fault;
  m.faultRun = faultRun;
  return m;
}
