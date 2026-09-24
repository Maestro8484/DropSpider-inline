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
  ST_RELEASE, ST_SETTLE, ST_REWIND, ST_LOCK_IN, ST_LOCK_SEAT,     // cycle or bench
  ST_JOG, ST_BENCH_REL, ST_BENCH_SERVO                            // bench only
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
static int  measuredLine = 0;

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
    case ST_RELEASE:     return "finger out, spider dropping";
    case ST_SETTLE:      return "spider hanging";
    case ST_REWIND:      return "rewinding";
    case ST_LOCK_IN:     return "finger going in";
    case ST_LOCK_SEAT:   return "spool settling onto the finger";
    case ST_JOG:         return "jogging the motor";
    case ST_BENCH_REL:   return "finger out (bench)";
    case ST_BENCH_SERVO: return "moving the finger (bench)";
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

// Start a move of n microsteps, + = rewind direction. Driver must already be on.
static bool startMove(long n) {
  if (appliedDir != S.rewindDir) {
    stepper->setDirectionPin(PIN_DIR, S.rewindDir == 1);
    appliedDir = S.rewindDir;
  }
  uint32_t hz = (uint32_t)S.rpm * STEPS_PER_TURN / 60;
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

static void startCycle(TriggerSource src) {
  cycle = true;
  lastTrigger = src;
  lastTriggerMs = millis();
  dropCountBump();
  drops++;
  if (faultRun == 0) fault = "";
  logf("[cycle] trigger: %s", triggerName(src));
  driverOff();
  servoWrite(S.servoRel);                     // spider free-falls here
  enter(ST_RELEASE);
}

static void startRewind() {
  driverOn();
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
      enter(ST_REWIND);                       // finishes on the next tick
      return;
    }
  }
  startMove(rewindSteps());
  enter(ST_REWIND);
}

static void finishRewind() {
  long ran = stepper->getCurrentPosition() - moveStartPos;
  bool alreadyHome = !cutByLimit && ran == 0 && limitHome();
  if (!alreadyHome) {
    lastRewind = ran;
    lastRewindLimit = cutByLimit;
  }
  if (S.limitFitted && !alreadyHome) {
    if (cutByLimit) {
      if (cycle && ran < (long)(REWIND_MIN_FRAC * rewindSteps())) {
        strike("limit switch tripped far too early: check for a snag or a broken line");
      } else {
        if (cycle) measuredLine = (int)(ran / (float)STEPS_PER_TURN * PI * BARREL_DIA_MM + SPOOL_TO_EYELET_MM);
        if (cycle) { faultRun = 0; fault = ""; }
      }
    } else if (cycle && !ignoreLimit) {
      strike("full rewind ran without the limit switch tripping");
    }
  }
  logf("[rewind] ran %ld steps (%.2f turns)%s", ran, ran / (float)STEPS_PER_TURN,
       cutByLimit ? ", stopped by the limit switch" : "");
}

static void startLock() {
  // finger in while the motor still holds, then let the spool back onto a tooth
  // while the servo keeps pushing
  servoWrite(S.servoLock);
  enter(ST_LOCK_IN);
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
      driverOff(); servoWrite(S.servoRel); enter(ST_BENCH_REL);
      break;
    case ACT_LOCK:
      disarmForBench(); cycle = false;
      startLock();
      break;
    case ACT_REWIND:
      disarmForBench(); cycle = false;
      startRewind();
      break;
    case ACT_JOG:
      disarmForBench(); cycle = false;
      driverOn();
      ignoreLimit = false;
      if (!startMove(r.arg)) { logf("refused: motor would not start"); return; }
      enter(ST_JOG);
      break;
    case ACT_SERVO:
      disarmForBench(); cycle = false;
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

  Req r;
  if (xQueueReceive(queue, &r, 0) == pdTRUE) handleReq(r);

  uint32_t now = millis();
  bool pressed = buttonEdge();

  switch (state) {
    case ST_BOOT:
      if (inState() < 50) break;              // let the switch readings settle
      if (S.limitFitted && !limitHome()) {
        fault = "spider not home at power-up. Boot never rewinds on its own: use rewind, then lock.";
        logf("[boot] %s", fault);
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
      if (inState() >= SERVO_MOVE_MS) enter(ST_SETTLE);
      break;

    case ST_SETTLE:
      if (inState() >= (uint32_t)S.settleMs) startRewind();
      break;

    case ST_REWIND:
      if (stepper->isRunning()) break;
      finishRewind();
      if (cycle) startLock();
      else benchDone("rewind (motor stays on until lock)");
      break;

    case ST_LOCK_IN:
      if (inState() >= SERVO_MOVE_MS) { driverOff(); enter(ST_LOCK_SEAT); }
      break;

    case ST_LOCK_SEAT:
      if (inState() < LOCK_SEAT_MS) break;
      servoOff();
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
        benchDone("lock: finger in, motor off");
      }
      break;

    case ST_JOG:
      if (stepper->isRunning()) break;
      logf("[jog] ran %ld steps%s", stepper->getCurrentPosition() - moveStartPos,
           cutByLimit ? ", stopped by the limit switch" : "");
      benchDone("jog (motor stays on)");
      break;

    case ST_BENCH_REL:
      if (inState() >= SERVO_MOVE_MS) { servoOff(); benchDone("rel: finger out"); }
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
  m.driverOn = driverIsOn;
  m.servoAttached = pawl.attached();
  m.servoDeg = servoDeg;
  m.motorRunning = stepper && stepper->isRunning();
  m.position = stepper ? stepper->getCurrentPosition() : 0;
  m.rewindSteps = rewindSteps();
  m.lastRewindSteps = lastRewind;
  m.lastRewindByLimit = lastRewindLimit;
  m.measuredLineMm = measuredLine;
  m.drops = drops;
  m.lastTrigger = lastTrigger;
  m.lastTriggerAgoMs = lastTriggerMs ? millis() - lastTriggerMs : 0;
  m.fault = fault;
  m.faultRun = faultRun;
  return m;
}
