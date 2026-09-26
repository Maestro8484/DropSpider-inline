# M1 fix handoff: mechanical owner to software/electrical team

Date: 2026-09-24. Revision: Rev C.1 (no reprints, no new hardware).

## Verdict

**M1 is confirmed and was a design error on the mechanical side.** A one-way clutch only lets the spool overrun the rod in the same direction the rod can drive it. As drawn in Rev C, the motor could never wind the spool up. The team's reading of doc 01 was correct.

**Fix: flip the HF0612 and make the drop motor-led.** The motor spins out ahead in the unwind direction under power, and the spool runs down behind it on the clutch. Same parts, firmware change only. Docs 01, 05, 07, 08 and `CLAUDE.md` are already updated by the mechanical owner. Firmware and doc 04 are yours.

## Why the other fixes were rejected

| Option | Why not |
|---|---|
| Let the spider back-drive the unpowered motor (clutch flipped, driver off) | Owner tested: the stepper's unpowered drag is too high for a clean fall |
| Relay to open the motor coils during the drop | Owner rule for Rev C.1: existing hardware only |
| Servo-actuated dog clutch or tilt-spool | New mechanism and reprints; that is Mechanism B (`dropspider-tiltspool`), not a fix |

## How the clutch works now

All directions seen from the 606ZZ end. Spider falling = spool turns clockwise (CW). Winding up = counterclockwise (CCW).

| Situation | Spool vs rod | Clutch | Result |
|---|---|---|---|
| Rod held, spool turned CW by hand | spool CW relative | **locks** | assembly check |
| Rod held, spool turned CCW by hand | spool CCW relative | free | assembly check |
| Rewind: motor turns rod CCW, spider weight holds spool back | spool CW relative | **locks** | motor winds the spool up |
| Drop: motor turns rod CW faster than the spool falls | spool CCW relative | free | spool falls at gravity, lagging the rod |
| Drop: spool catches up to the rod's speed | spool CW relative | **locks** | fall speed capped at the motor's speed |
| Lock seat: motor turns rod CW after a tooth lands on the finger | spool CCW relative | free | motor runs on harmlessly, spool stays on the tooth |

The spool can never travel faster than the motor. So the motor sets the top speed and the stopping point of every drop, and the knot never slams. The line's stretch (6 lb mono) is the backstop in case the motor loses its grip.

## Second finding: M2, the finger cannot release under load

Found while reworking the sequence, not yet tested. With the spider hanging, the tooth presses the finger up onto the ledge. The release swing moves the finger tip toward the floor, straight into the same tooth's steep face. As drawn, the servo would be fighting the tooth.

Fix: wind the spool CCW about 1/12 turn **while** the servo swings out. In that direction the finger rides up the tooth's ramp and out, the same way a ratchet clicks. The motor is already powered for the drop, so this costs about 100 ms.

## Firmware spec (yours to implement in `src/machine.cpp`, settings, console, web)

Directions below use the firmware's own convention: + = rewind (CCW), - = unwind (CW).

**Drop sequence (replaces `startCycle` / `ST_RELEASE`):**
1. `driverOn()`.
2. At the same moment: `servoWrite(S.servoRel)` and start an unload move of `+UNLOAD_STEPS` (default `STEPS_PER_TURN / 12`) at a slow speed (default 120 rpm).
3. Wait `S.releaseMs` from the servo command (default 250 ms; finger clear of the teeth).
4. Drop move: `-dropSteps()` at `S.dropRpm`, acceleration `S.dropAcc`, deceleration `S.dropDec`.
5. Driver stays on: the motor holds the spider at the bottom through the clutch. Then `ST_SETTLE` as today.

`dropSteps()` = `(S.dropMm + unload distance) / (PI * BARREL_DIA_MM) * STEPS_PER_TURN`. Refuse any `dropMm` that would reach within 30 mm of the knot: `dropMm <= lineMm - SPOOL_TO_EYELET_MM - 30`.

**Rewind:** unchanged. Limit switch and bead stop work as before.

**Lock sequence (replaces `ST_LOCK_IN` / `ST_LOCK_SEAT`):**
1. Motor on and holding (end of rewind). `servoWrite(S.servoLock)`, wait `SERVO_MOVE_MS`. The finger may land on a tooth tip; that is fine.
2. Seat move: `-SEAT_STEPS` (default `STEPS_PER_TURN / 12 * 1.2`) at `SEAT_RPM` (default 30). The spool follows down until a tooth lands on the finger; after that the clutch slips and the motor runs on alone.
3. `driverOff()`, then `servoOff()` after `LOCK_SEAT_MS`.

**Bench commands:** `rel` must now use the drop sequence steps 1 to 3 (unload + release) with the driver on, then stop; a bare servo release with the driver off will jam per M2. Add `dropnow` or reuse `drop` for the full powered drop.

**New settings** (NVS, console, web page, all with range checks):

| Setting | Console | Default | Range | Meaning |
|---|---|---|---|---|
| dropMm | `dropmm` | lineMm - 40 - 60 | 100 to lineMm - 70 | how far the spider travels |
| dropRpm | `droprpm` | 500 | 100 to 900 | top speed of the drop |
| dropAcc | `dropacc` | 120000 | 20000 to 400000 | microsteps/s squared. 100000 is about 1 g at the barrel |
| dropDec | `dropdec` | 60000 | 10000 to 200000 | about 0.6 g. Must stay low: see torque note |
| releaseMs | `relms` | 250 | 100 to 600 | finger travel time before the drop starts |

Unit check for the team: one microstep = pi x 50 mm / 1600 = 0.098 mm of line. 1 m/s is about 610 rpm.

**Torque note:** stopping the spider takes motor torque on top of holding its weight. At 0.6 A and 500 rpm this motor has roughly 2.5 to 3 Ncm (estimate, not measured). That stops a spider of 60 g or less at about 0.6 g. A 100 g spider needs `dropDec` near 20000 and a longer stop. If the motor loses steps during the stop, the spool runs free and the line's stretch catches it: a scare, not a failure. Log it as a fault only if it repeats.

**FastAccelStepper:** check whether it supports a separate deceleration within one move. If not, the known pattern is to change acceleration part-way through the move (`setAcceleration` + `applySpeedAcceleration`) at the point where the gentler stop needs to begin. Name the approach you use and why.

**Limit switch interplay:** the seat move lets the bead drop up to about 13 mm below the switch. Check that `limitHome()` still reads pressed after a seat (depends on lever travel). If it does not, the boot check and the "spider not home" message need a tolerance, not a code path that rewinds.

**Unchanged:** boot never rewinds; armed idle = driver off and servo detached; servo on GPIO13.

## Bench tests (add to `commissioning_log.md` as T1 to T8)

| # | Test | Pass |
|---|---|---|
| T1 | Clutch direction by hand, per the table above | Rod held: spool locks CW, free CCW |
| T2 | `rewind` from the bottom | Spool winds up, limit switch stops it |
| T3 | Release under load (M2), 10 times | Finger clears every time, no servo buzz, spider starts falling |
| T4 | Full `drop`, 5 times at 500 rpm; phone slow-motion video of the drop | 0.7 m in 0.7 s or less; no lost steps logged |
| T5 | Stop height, 10 drops | Spider stops within 20 mm of the same height each time; no bounce off the line's end |
| T6 | Lock seat, 10 times | Finger seats every time; spider drops no more than 13 mm; limit reading as expected |
| T7 | Raise `droprpm` in steps of 100 until steps are lost | Record the highest clean speed with the real spider; set 100 below it |
| T8 | 20 full cycles | Motor warm, not hot; no ESP32 resets; coupler screws tight |

## Doc status

| Doc | Status |
|---|---|
| 01 mechanical design | updated by mechanical owner |
| 05 assembly (B2, B4, 11) | updated |
| 07 commissioning (7, 8, 10, troubleshooting) | updated |
| 08 open items (M1, M2, V13, V14) | updated |
| CLAUDE.md hard constraints | updated |
| 04 firmware, web page help text | **yours**, after the firmware lands |
