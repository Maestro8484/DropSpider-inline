#include "machine.h"
#include "config.h"
#include "settings.h"
#include "console.h"
#include <ESP32Servo.h>
#include <FastAccelStepper.h>

// FastAccelStepper makes the step pulses in the ESP32's own pulse hardware, so a
// rewind runs smoothly while WiFi, the web page and the console carry on. The
// Rev C handoff firmware timed each pulse by hand and froze everything else for
// the 2 to 3 s of a rewind.
static FastAccelStepperEngine engine;
static FastAccelStepper *stepper = nullptr;
static Servo pawl;

enum St {
  ST_BOOT, ST_IDLE, ST_LOCKOUT, ST_WAIT_CLEAR, ST_FAULT,          // at rest
  ST_RELEASE, ST_DROP, ST_SETTLE, ST_REWIND,                      // cycle
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
static int  servoDeg = DEF_SERVO_LOCK;
static int  appliedDir = -1;
static bool movingUp = false;           // current move is in the rewind direction
static long moveStartPos = 0;
static bool cutByLimit = false;
static bool ignoreLimit = false;        // this rewind runs on the step count alone

static long lastRewind = 0;
static bool lastRewindLimit = false;
static int  measuredDrop = 0;

// Rev C.1 drop
static long unloadRan = 0;              // what the unload move actually ran (the switch may cut it)
static long lastDropSteps = 0;          // what the last powered drop was told to run
static bool decelApplied = false;       // the drop has switched to its stopping rate
static int32_t dropDecNow = 0;          // stopping rate for the drop in progress
static uint32_t dropStartMs = 0;

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
static bool sensorNow = false, sensorLast = false;
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

static void driverOn()  { digitalWrite(PIN_EN, LOW); driverIsOn = true; delay(5); }
static void driverOff() { digitalWrite(PIN_EN, HIGH); driverIsOn = false; }

static void servoWrite(int deg) {
  deg = constrain(deg, 0, 180);
  if (!pawl.attached()) pawl.attach(PIN_SERVO, 500, 2400);
  pawl.write(deg);
  servoDeg = deg;
}
static void servoOff() { if (pawl.attached()) pawl.detach(); }

static bool limitHome() { return S.limitFitted && limStable; }

static void setHome(bool h) { homeFlag = h; homeSave(h); }
static void homeLost() { upByLimit = false; setHome(false); }

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
}

static void disarmForBench() {
  if (S.armed) { S.armed = 0; logf("disarmed for bench work (not saved). Send 'arm' when done."); }
}

// ---------------------------------------------------------------- inputs

static void readInputs() {
  uint32_t now = millis();

  sensorNow = digitalRead(PIN_SENSOR) == HIGH;
  if (sensorNow && !sensorLast) highSince = now;
  if (!sensorNow && sensorLast) lowSince = now;
  sensorLast = sensorNow;

  bool b = digitalRead(PIN_BUTTON) == HIGH;             // true = not pressed
  if (b != btnLast) { btnLast = b; btnAt = now; }
  if (now - btnAt >= BUTTON_DEBOUNCE_MS) btnStable = b;

  bool l = digitalRead(PIN_LIMIT) == LOW;               // pulled up; pressed pulls LOW
  if (S.limitInverted) l = !l;
  if (l != limLast) { limLast = l; limAt = now; }
  if (now - limAt >= LIMIT_DEBOUNCE_MS) limStable = l;
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

// Called once the unload has finished: how far it really went.
static void noteUnload() {
  unloadRan = stepper->getCurrentPosition() - moveStartPos;
  if (cutByLimit)
    logf("[release] unload cut short by the limit switch after %ld of %d steps", unloadRan, UNLOAD_STEPS);
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
  cycle = true;
  lastTrigger = src;
  lastTriggerMs = millis();
  dropCountBump();
  drops++;
  if (faultRun == 0) fault = "";
  logf("[cycle] trigger: %s", triggerName(src));
  startRelease();
  enter(ST_RELEASE);
}

static void startRewind() {
  driverOn();
  homeLost();
  ignoreLimit = false;
  if (limitHome()) {
    if (cycle) {
      // The spider has just fallen, so a pressed switch is lying. Wind the counted
      // length with the switch ignored; the bead stop ends it.
      strike("limit switch still pressed after a drop: check its wiring and the liminv setting");
      ignoreLimit = true;
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
  if (cycle && lastDropSteps > 0) n = min(n, lastDropSteps + (long)(OVERSHOOT_TURNS * STEPS_PER_TURN));
  startMove(n, S.rpm);
  enter(ST_REWIND);
}

static void finishRewind() {
  long ran = stepper->getCurrentPosition() - moveStartPos;
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
          logf("[drop] lost steps? rewind ran %d mm more than the drop: the spool got ahead of the motor on the stop",
               (int)(extra * mmPerStep()));
        faultRun = 0; fault = "";
      }
    } else if (cycle && !ignoreLimit) {
      strike("full rewind ran without the limit switch tripping");
    }
  }
  logf("[rewind] ran %ld steps (%.2f turns, %d mm)%s", ran, ran / (float)STEPS_PER_TURN, (int)(ran * mmPerStep()),
       cutByLimit ? ", stopped by the limit switch" : "");
}

// Finger in while the motor holds, then the motor lets the spool down onto a
// tooth (the seat move). Once a tooth lands the clutch slips and the motor runs
// on alone. Driver off after that, servo off after LOCK_SEAT_MS.
static void startLock() {
  driverOn();                                 // already on after a rewind; holds the spool
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
  if (servoDeg == S.servoRel) { benchMove(a, arg); return; }
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
    cycle = false;
    if (r.a == ACT_OFF) { driverOff(); servoOff(); }
    disarmForBench();
    logf("[done] %s%s", r.a == ACT_OFF ? "off: motor and servo off" : "stop: everything halted, motor left as it was",
         wasCycle ? " (cycle aborted)" : "");
    enter(state == ST_FAULT ? ST_FAULT : ST_WAIT_CLEAR);
    return;
  }
  if (r.a == ACT_CLEAR) {
    fault = ""; faultRun = 0;
    logf("[done] fault cleared");
    if (state == ST_FAULT) enter(ST_WAIT_CLEAR);
    return;
  }
  if (isBusy()) { logf("refused: busy (%s)", stateName(state)); return; }
  benchReturn = (state == ST_FAULT) ? ST_FAULT : ST_WAIT_CLEAR;
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
  if (movingUp && !ignoreLimit && stepper->isRunning() && limitHome()) {
    haltMotor();
    cutByLimit = true;
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

  switch (state) {
    case ST_BOOT:
      if (inState() < 50) break;              // let the switch readings settle
      // V14: after a lock seat the switch reads open by design. Home is the switch
      // pressed, or the last lock having followed a rewind the switch stopped.
      if (S.limitFitted && !limitHome() && !homeFlag) {
        fault = "spider not home at power-up. Boot never rewinds on its own: use rewind, then lock.";
        logf("[boot] %s", fault);
      } else if (S.limitFitted && !limitHome()) {
        logf("[boot] switch open, spider home from the last lock (seated below the switch)");
      }
      enter(ST_WAIT_CLEAR);
      lowSince = now;
      break;

    case ST_IDLE:
      if (pressed) { startCycle(TRIG_BUTTON); break; }
      if (S.armed && sensorNow && now - highSince >= TRIGGER_DEBOUNCE_MS) startCycle(TRIG_SENSOR);
      break;

    case ST_LOCKOUT:
      if (pressed) { startCycle(TRIG_BUTTON); break; }
      if (inState() >= (uint32_t)S.rearmMs) enter(ST_WAIT_CLEAR);
      break;

    case ST_WAIT_CLEAR:  // someone still standing there: wait until the doorway is empty
      if (pressed) { startCycle(TRIG_BUTTON); break; }
      if (!sensorNow && now - lowSince >= CLEAR_BEFORE_REARM) {
        enter(ST_IDLE);
        logf(S.armed ? "[armed] doorway clear" : "[ready] doorway clear, not armed");
      }
      break;

    case ST_FAULT:
      if (pressed) { fault = ""; faultRun = 0; logf("[done] fault cleared by button"); enter(ST_WAIT_CLEAR); }
      break;

    case ST_RELEASE:
      if (inState() < (uint32_t)S.releaseMs || stepper->isRunning()) break;
      noteUnload();
      startDrop();
      break;

    case ST_DROP: {
      if (stepper->isRunning()) break;
      long ran = moveStartPos - stepper->getCurrentPosition();
      logf("[drop] ran %ld steps (%d mm) in %lu ms at up to %d rpm; motor holding",
           ran, (int)(ran * mmPerStep()), (unsigned long)(millis() - dropStartMs), S.dropRpm);
      enter(ST_SETTLE);
      break;
    }

    case ST_SETTLE:
      if (inState() >= (uint32_t)S.settleMs) startRewind();
      break;

    case ST_REWIND:
      if (stepper->isRunning()) break;
      finishRewind();
      if (cycle) startLock();
      else { servoOff(); benchDone("rewind (finger out, motor stays on until lock)"); }
      break;

    case ST_LOCK_IN:
      if (inState() < SERVO_MOVE_MS) break;
      ignoreLimit = false;
      if (!startMove(-SEAT_STEPS, SEAT_RPM)) logf("[lock] seat move would not start");
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
      logf("[lock] seated. Limit switch %s%s", !S.limitFitted ? "not fitted" : limitHome() ? "pressed" : "open",
           upByLimit ? "; spider home" : "; home not known (last rewind was not stopped by the switch)");
      if (cycle) {
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
        benchDone("lock: finger in, seated, motor off");
      }
      break;

    case ST_JOG:
      if (stepper->isRunning()) break;
      logf("[jog] ran %ld steps%s", stepper->getCurrentPosition() - moveStartPos,
           cutByLimit ? ", stopped by the limit switch" : "");
      servoOff();
      benchDone("jog (finger out, motor stays on)");
      break;

    case ST_BENCH_FREE:
      if (inState() < (uint32_t)S.releaseMs || stepper->isRunning()) break;
      noteUnload();
      benchMove(pendAct, pendArg);
      break;

    case ST_BENCH_REL:
      if (inState() < (uint32_t)S.releaseMs || stepper->isRunning()) break;
      noteUnload();
      servoOff();
      benchDone("rel: finger out, motor on and holding the spider (jog to lower it, off lets it slide down)");
      break;

    case ST_BENCH_SERVO:
      if (inState() >= SERVO_MOVE_MS) {
        char buf[48]; snprintf(buf, sizeof buf, "servo %d (holding)", servoDeg);
        benchDone(buf);
      }
      break;
  }

  // LED: slow blink = armed and ready, solid = working, fast blink = stopped on faults
  bool led = false;
  if (state == ST_IDLE && S.armed) led = (now / 1000) % 2;
  else if (state == ST_FAULT)      led = (now / 150) % 2;
  else if (isBusy())               led = true;
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
  pinMode(PIN_LED, OUTPUT);

  engine.init();
  stepper = engine.stepperConnectToPin(PIN_STEP);
  if (!stepper) logf("[boot] ERROR: stepper engine would not attach to GPIO%d", PIN_STEP);
  pinMode(PIN_DIR, OUTPUT);

  ESP32PWM::allocateTimer(0);
  pawl.setPeriodHertz(50);

  drops = dropCount();
  homeFlag = homeSaved();
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
  m.limitRaw = limStable;
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
  m.fault = fault;
  m.faultRun = faultRun;
  return m;
}
