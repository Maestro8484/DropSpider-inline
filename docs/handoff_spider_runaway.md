# Handoff: the spider runs away on any downward move

Find and fix why the spool runs ahead of the motor whenever the motor turns down, so the spider falls the whole line. For a session working with Joe (the owner) at the device, the board on the network.

## Ground truth first

This file is a work order, not a record. The repo on disk and the board's own log win; if they disagree with this file, this file is stale, say so out loud. Staleness check:

```
git log -1 --oneline                                     # where the repo is now
git log -1 --oneline -- docs/handoff_spider_runaway.md   # when this file was last true
```

## Before you start

1. Read the newest 2026-10-06 rows of `docs/commissioning_log.md`: every measurement behind this task is there.
2. Read the board: `curl -s http://dropspider.local/api/status` (192.168.1.137 if the name fails). Note `state`, `driverOn`, `servoDeg`, `position`, `fault`, and the `log` lines.
3. Check the settings it reports: `line` 2200, `rpm` 240, `setrel` 30, `setlock` 85. They were set on purpose on 2026-10-06; do not change them without a reason.
4. Open the summary page Joe reads: https://claude.ai/artifact/MMGPq3icuhv68BugqDNhHS ("DropSpider · Spider Runaway").

5. **The coupler's set screws were found a little loose and tightened by Joe on 2026-10-06, after every measurement in this file.** Re-tested the same day: with the screws tight, one `jog -200` (finger out, motor on) still let the spider fall the whole line. So the coupler is not the whole cause; it stays on the list only if a screw is still loose or not on a flat.

## Read first

1. `CLAUDE.md`: the hard constraints, every direction seen from behind the motor, the motor never turns with the finger in, release winds up 1/12 turn first.
2. `src/machine.cpp`: `driverOn`, `startMove`, `haltMotor`, the states `ST_REWIND`, `ST_BACKOFF`, `ST_LOCK_*`, `ST_RELEASE`, `ST_BENCH_*`; `include/config.h`.
3. `docs/02_electrical.md`: the driver is a BIGTREETECH TMC2209 V1.3 in standalone mode (no UART), 1/8 microstep, Vref about 0.825 V.

## What is known (the facts, each with its source in the commissioning log)

- Winding up works and holds: +1 turn winds and stays; rewinds reach the switch. Joe saw it.
- Every downward move lets the spider run: three `jog -1600` (motor 470 mm) let it down about 1750 mm; a switch stop with its 36 mm ease-off and lock let it down about 300 mm; a page drop (motor 633 mm in 0.7 s) ran past 750 mm to the end; `jog -200` lets it fall the whole line. Board log plus Joe.
- A fast grinding noise at the moment it runs. Joe says it comes from the stepper motor, not the finger (the finger is out, confirmed by eye at setrel 30).
- With the driver on, Joe can turn the spool counterclockwise by hand and the motor turns with it; clockwise it freewheels. So the one-way bearing is the right way round.
- Joe's tape on the coupler: at the switch the coupler went back about 1/2 turn while the spider fell about 0.3 m (about 2 spool turns). An eyeball count during a fast spin.
- The one-way bearing cannot be reached without taking the spool off. Joe will not do that on a guess.

## The work, in order

Order set by Joe (2026-10-06): audits first, the tape and watching last.

1. **Full audit by this session (Fable), no motion:** the code, the motion and the problem together. Read every path that moves the motor or the servo in `src/machine.cpp` (driver on and off, `startMove` speeds and ramps, `haltMotor` at the switch, the back-off, the lock and seat, release, jogs, the drop and its stop), `include/config.h`, and the board's log. Check the TMC2209 V1.3 in standalone mode against its datasheet and the BTT board docs: stealthChop (the quiet mode) under a gravity load, the standstill current cut, whether spreadCycle can be chosen on this board, what Vref 0.825 V gives in amps against the motor's rating. **Joe's suspects, audit these first (2026-10-06): the stepper motor's timing, and possibly the finger and ratchet.** Timing: when the driver switches on and off against when steps start and stop (the 200 ms settle, `haltMotor` stopping from 240 rpm within 2 ms at the switch, the drop's 500 rpm stop with `dropacc` and `dropdec`, the back-off and seat speeds), and whether the motor can lose sync at any of them. Finger and ratchet: when the servo moves against when the motor moves (`releaseMs`, `SERVO_MOVE_MS`, `LOCK_SEAT_MS`, when the servo is detached), whether the finger at `setrel` 30 and `setlock` 85 clears or catches the Rev C.4 teeth (`python cad/generate.py` checks the seat; the 2026-10-06 model swing put the tip 0.75 mm inside the tooth tips at about 25 degrees out), and whether a finger caught on half a tooth or pushed out by a tooth explains the falls. Explain every 2026-10-06 measurement above with one cause, or say which it cannot explain. Write the findings as a file, `docs/audit_spider_runaway.md`, ranked, each with the line or datasheet page behind it.
2. **Cold audit by Codex:** run the `codex-auditor` agent (or `/mad`) on the same question and the same files, blind to step 1's conclusions. Verify each Codex finding in the code before it counts; keep its severity and say it came from Codex. Add a section to the audit file: where Codex agrees, where it differs, what survived checking.
3. **Report to Joe:** the ranked cause and the fix, as one flat numbered list, the question in bold on each item. Any firmware fix is built and flashed only after his yes; lock before any flash.
4. **Then the tape and watching, only if the audits leave it open,** with Joe at the device: lock first; marker line across the motor shaft and the coupler, another across the coupler and the rod, tape on the spool's edge, phone on slow motion; send `jog -200`. Motor shaft spins many turns with both lines whole = the motor skips; a line splits = the coupler set screw; motor and coupler nearly still while the spool spins = the one-way bearing.
5. **Fix by cause:** motor or driver = the driver change and firmware so the finger goes in before any downward move ends; coupler = set screw onto a filed flat, blue threadlocker; one-way bearing = spool off, cup glued or `OP_BORE` changed in `cad/generate.py` (export `spool_onepiece` only), Joe decides.
6. Log every run, one row each, in `docs/commissioning_log.md`.

## Tests

- After the fix: `jog -1600` moves the spider down about 157 mm and it stays there. Logged.
- A switch-stopped rewind, then a second rewind, runs about 20 to 35 mm. Logged.
- Ten page drops: each stops at `dropmm` (620 mm) and rewinds to the switch. Logged; this also closes V22 with `docs/handoff_spool_rev_c4.md`.

## Done when

Down moves move the spider only as far as the motor turns, and ten drops pass.

## Rules for the session

- Motion commands only after Joe says in the conversation that he is at the device. Lock before any flash: a network update turns the motor off.
- No guessing at what Joe can reach or see: ask once, then act.
- His names: the disc on the line is "the stopper"; the HF0612 is "the one-way bearing".
- Verdict first, short, plain English, no em dashes. Decisions to him as one flat numbered list, the question in bold on each item.
