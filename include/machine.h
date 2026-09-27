// The machine: stepper, finger servo, radar OUT pin, BOOT button, limit switch,
// and the order everything happens in. Runs on a FreeRTOS task of its own, so the
// serial console, the web page and network updates all stay live during a cycle.
#pragma once
#include <Arduino.h>

enum TriggerSource { TRIG_NONE, TRIG_SENSOR, TRIG_BUTTON, TRIG_CONSOLE, TRIG_WEB };

// What can be asked of the machine. Motion requests are refused with a reason
// while a cycle is running; stop and off are always accepted.
enum Action { ACT_DROP, ACT_REL, ACT_LOCK, ACT_REWIND, ACT_JOG, ACT_SERVO, ACT_OFF, ACT_STOP, ACT_CLEAR };

struct MachineStatus {
  const char *state;        // plain-English state name
  bool     busy;            // a cycle or a bench move is running
  bool     armed;
  bool     sensor;          // radar OUT right now
  bool     limitRaw;        // limit switch reads pressed right now (after the invert setting)
  bool     limitFitted;
  bool     driverOn;
  bool     servoAttached;
  int      servoDeg;        // last angle commanded
  bool     motorRunning;
  long     position;        // stepper position in microsteps, + = rewind
  long     rewindSteps;     // what a full rewind is set to run
  long     lastRewindSteps; // what the last rewind actually ran
  bool     lastRewindByLimit;
  int      measuredDropMm;  // from the last cycle's rewind stopped by the switch, 0 if none
  bool     home;            // switch pressed, or seated on the finger after a switch-stopped rewind (V14)
  uint32_t drops;
  TriggerSource lastTrigger;
  uint32_t lastTriggerAgoMs;// 0 if never
  const char *fault;        // "" when all is well
  int      faultRun;
};

void machineBegin();                           // call once from setup(), after settingsBegin()
bool machineRequest(Action a, long arg, TriggerSource src, String &why);
MachineStatus machineStatus();
void machineSafeStop();                        // everything still, coils off, servo off (network update)
const char *triggerName(TriggerSource t);
long rewindSteps();
