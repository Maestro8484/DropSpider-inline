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

1. **Settle where it slips, with Joe watching:** lock first. Marker line across the motor shaft and the coupler, another across the coupler and the rod, tape on the spool's edge, phone on slow motion. Send `jog -200`. Read: motor shaft spins many turns with both lines whole = the motor skips (A); a line splits = the coupler set screw (B); motor and coupler nearly still while the spool spins = the one-way bearing (C). Log the result.
2. **If A (Joe's view):** check the TMC2209 against its datasheet and the BTT V1.3 board: stealthChop (the quiet mode) against a gravity load, the standstill current cut, whether spreadCycle can be chosen in standalone mode on this board (a pin or jumper), and what Vref gives in amps. Propose the hardware change as one numbered decision. In firmware, stop asking the motor to hold the spider alone: the finger goes in before any downward move ends.
3. **If B:** set screw onto a filed flat, blue threadlocker; re-run the test.
4. **If C:** the spool comes off; the bearing cup glued or the bore changed (`OP_BORE` in `cad/generate.py`, export `spool_onepiece` only); Joe decides.
5. Log every run, one row each, in `docs/commissioning_log.md`.

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
