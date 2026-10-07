# Audit: why the spider runs away on every downward move

Desk audit of the code, the motion and the drive chain, written 2026-10-06 for the owner, no motion and no flash. It answers `docs/handoff_spider_runaway.md` step 1 (this session) and step 2 (the Codex cold audit, last section).

## Ground truth first

This file is a record of one reading. The repo on disk, the datasheets named below and the board's own log win; if they disagree with this file, this file is stale, say so out loud.

```
git log -1 --oneline                                   # where the repo is now
git log -1 --oneline -- docs/audit_spider_runaway.md   # when this file was last true
```

Board read 2026-10-06 over the network (`/api/status`): state ready, driver on, servo unpowered at 30 (finger out), position -83, no fault, drops 9. Settings as the handoff says: line 2200, rpm 240, setrel 30, setlock 85, dropacc 120000, dropdec 60000, droprpm 500, relms 250. Last log lines: `rel` (unload cut by the switch after 117 of 133 steps), then `jog -200` ran all 200 steps and ended "finger out, motor stays on".

## Verdict

**The slip is at the motor, not in the coupler, the one-way bearing or the finger. The motor is left weak against being pushed backward, and once a stepper has been pushed past one pole it gives almost no braking at all, so the spider runs the whole line with the rotor grinding past its poles.** Three things in the driver setup and the firmware make the motor weak exactly on the down side, and every runaway in the log follows the same trigger: a dead stop at the limit switch while the driver is in its quiet mode, after which the driver is never switched off and on again before the next down move.

Why the chain parts are cleared: winding up carries the spider's weight through the coupler, the clutch rollers, the clutch cup and the spool in the very same direction and at the very same torque as holding it or lowering it. The clutch locks the same way for all three. Winding up worked every time, minutes apart from every runaway, so every mechanical joint is proven to carry the load. The only part of the chain whose strength depends on whether it is pushing or being pushed is the motor.

## What was read

- `src/machine.cpp` whole file, `include/config.h`, `docs/02_electrical.md`, `docs/04_firmware.md`, `docs/01_mechanical_design.md`, `docs/09_fairlead_switch.md`, `docs/commissioning_log.md` rows of 2026-10-06, `cad/generate.py` (`python generate.py` run: finger seats in a tooth gap, window 7.00 to 11.75 degrees, tip 1.38 mm clear of the separator).
- TMC2209 datasheet rev 1.05 (Trinamic, 2020-05-18, Reichelt mirror), pages 8, 9, 23, 25, 35, 42, 50.
- BIGTREETECH TMC2209 V1.3 schematic (GitHub, bigtreetech/BIGTREETECH-Stepper-Motor-Driver, TMC2209/V1.3, found by Codex, read here as a picture) and the V1.2 manual. The V1.3 board in the device was not opened.
- STEPPERONLINE 11HS12-0674S listing (Tindie): 6 N.cm, 0.67 A, 5.6 ohm, inductance listed as "42mH +/-20% (1KHz)", 5 mm shaft. The maker's own datasheet PDF was behind a script wall and is unread.
- NSK needle bearing catalog B230 to B233 and the Nadella drawn cup roller clutch catalog, for what a drawn cup clutch needs from its shaft and housing.

## The numbers behind the verdict

| quantity | value | how |
|---|---|---|
| spider's torque at the barrel | 0.74 N.cm | 30 g at 25 mm radius |
| motor holding torque, rated | 6 N.cm | at 0.67 A, maker's listing |
| run current set | 0.58 A rms, 87 percent of rated | BTT formula Irms = Vref / 1.414 with Vref 0.825 V; same as the datasheet formula with the board's 0.11 ohm sense resistor, page 50 |
| holding torque at run current | about 5.2 N.cm | 87 percent of 6 |
| standstill current | about 0.31 A, 53 percent of run | PDN_UART low on the BTT module (R5 20K to ground on the schematic); datasheet page 8 "slightly more than half of the run current", page 23 OTP default IHOLD 16 = 53 percent |
| holding torque at standstill | about 2.8 N.cm | 46 percent of 6 |
| line speed at 240 rpm | 0.63 m/s | 50 mm barrel |
| peak line pull at a dead stop from 240 rpm, short line at the top | about 5 N, 13 N.cm at the barrel | spider's kinetic energy 6 mJ absorbed by about 0.1 m of size 69 nylon (49 N at 22 percent stretch), 17 times the spider's weight |
| how far the motor would be pushed back by that one jolt if its hold were intact | about 1/50 turn | 6 mJ against 5 N.cm |

The last two rows are the point. A dead stop at the switch can out-pull the motor's hold for an instant, so a few slipped steps at the switch are expected. But a 1/2 turn reversal (the owner's tape) and a whole-line runaway need the hold to be gone, not merely beaten once. Something takes the hold away after that first jolt. The datasheet names it.

## Owner's suspect 1: the stepper motor's timing. Findings, ranked

**1. A dead stop in quiet mode (stealthChop) can leave the driver in a bad current state it cannot leave on its own, and the firmware never resets it.** Datasheet page 42, verbatim: "A motor stall or a sudden change in the motor velocity may lead to the driver detecting a short circuit or to a state of automatic current regulation, from which it cannot recover. Clear the error flags and restart the motor from zero velocity to recover from this situation." Same page: "As StealthChop uses voltage mode driving ... the driver reacts delayed to sudden changes of back EMF, like on a motor stall." In standalone mode the only reset is the EN pin going high and low again. The firmware stops the motor dead at the switch with `forceStopAndNewPosition` (`src/machine.cpp` line 189, called from the hard cut-off at line 513) from 240 rpm, or from the 120 rpm unload, and then keeps the driver on through the back-off, the seat and the holding by design (`driverOn()` at line 147 returns at once when already on; EN only goes high in `driverOff()`, called from the lock at line 628 and `off`). So from the first dead stop until the next lock, every move and every hold runs on a driver that may be regulating the current wrongly or, in the worse case, has switched its outputs off on a short-circuit flag (then the motor is free and the DIAG pin, not wired, is the only sign).

Every runaway in the log has that dead stop in the same powered stretch before the down move:
- row 39 (slid 1 m with no command): rewind stopped by the switch, then ease-off, then holding.
- row 41 (0.3 m lost per cycle): rewind stopped by the switch, then the back-off and seat ran down.
- row 43 (three jog -1600 lost 1.28 m): the release before them was cut short by the switch after 14 of 133 steps (row 42), a dead stop at 120 rpm.
- the page drop that ran to the end: its own release's unload was cut by the switch at the top.
- row 45 (jog -200, whole line): `rel` cut by the switch after 117 of 133 steps, then the jog, as the board's log shows now.

And every wind that worked started fresh: `benchMoveFingerOut` runs `startRelease`, whose `driverOn()` comes after a lock had switched the driver off, so the driver re-tuned itself before the wind (line 147 to 150, the 200 ms settle).

**2. The 200 ms settle happens at the reduced standstill current, not at the run current the tuning needs.** Datasheet page 35, AT#1: "Motor in standstill and actual current scale (CS) is identical to run current (IRUN). If standstill reduction is enabled (pin PDN_UART=0), an initial step pulse switches the drive back to run current." `driverOn()` (line 149) enables and waits 200 ms with no step pulse, so the driver tunes its offset at 53 percent current, then the first move asks for 100 percent. The chirp the owner heard before the settle was added is this tuning; the settle may have moved the chirp rather than cured it. Cheap fix in firmware: one microstep forward and back right after enable, then the 200 ms.

**3. The standstill current is cut to about half, by the board, not by the firmware.** BTT V1.3 schematic: PDN_UART (chip pin 14) is the header pin marked UART_RX, pulled to ground by R6 20K, and it sits in the header position an A4988 calls MS3, so it is under DIP switch 3 of the expansion board. DIP 3 OFF leaves it low, so the standstill current reduction is on (datasheet page 9, PDN_UART "low = automatic standstill current reduction"). Holding the spider on a motor that is at 46 percent of its rated hold is the firmware's own holding state (`rel`, the jog's end, the rewind's end, the back-off's end). A4988-style expansion boards tie an MS pin to 5 V when its switch is ON, so DIP 3 ON should give full run current at standstill with no soldering. NOT verified on this board: a meter on the module's UART_RX pin (5th from the DIR end) with DIP 3 ON must read about 5 V before trusting it.

**4. The quiet mode itself is the wrong chopper for a load that pushes the motor.** stealthChop drives the coils with a voltage and corrects the current slowly (datasheet page 42 and the autoscale rules on page 35, one change per 8 full steps); spreadCycle regulates the current every chopper cycle (page 7: "SpreadCycle at higher velocity for high dynamics"). On the V1.3 module the mode is the empty resistor place R7 between the chip's SPREAD pin and VIO: the schematic's own note reads "R7=20K SpreadCycle, R7=NC StealthChop" (the V1.2 manual's picture of moving a resistor on the underside is the older board). One 20K resistor soldered at R7, or a 20K between the SPREAD pin and the module's VIO pin. Soldering, and the module comes out of its socket to do it. With spreadCycle the dead-stop state of finding 1 does not arise, the hold is a true current hold, and the motor is louder.

**5. The drop's start outruns gravity, so the clutch slams at the stop.** `dropacc` 120000 microsteps/s^2 is 1.2 g at the barrel (config.h line 108 says 100000 is about 1 g). The rod runs ahead faster than the spider can fall, the clutch freewheels for the whole drop, and the spool only catches the rod during the stop, at speed, as a jolt onto a motor that is braking at 0.6 g (`dropdec` 60000) with its weakest torque at 500 rpm. A `dropacc` of 80000 (0.8 g) keeps the spool on the rod from the first step, so the stop is a steady pull, not a slam. Settings change on the page, no flash.

**6. The motor's listed inductance, if true, limits its torque above about 100 rpm.** 42 mH with 5.6 ohm gives a current rise time of 7.5 ms, longer than one full step at 240 rpm (1.25 ms). The driver can then push only about a third of the run current at 240 rpm and a sixth at 500 rpm. Winding up at 240 rpm still has a margin over 0.74 N.cm, which fits what was seen. The 500 rpm drop stop has none. Unverified: the listing may be a typo for 4.2 mH; measure or read the maker's own sheet before acting on it. Either way the fix list below does not depend on it.

Timing items checked and cleared: `startMove` ramps to speed in 600 steps (line 179) so a jog -200 never passes 98 rpm; the back-off and seat moves run at 30 rpm; the release waits the full finger swing (`max(relms, SERVO_MOVE_MS + 150)`, line 578) before the drop; the unload is 133 steps at 120 rpm with the switch guarding it. None of these is a defect on its own. The hard cut-off at the switch has no ramp because the flap's hard face is only 1 mm of bead travel past the click (doc 09 step 4), about 10 microsteps, 1.6 ms at 240 rpm; a ramp cannot fit, so the dead stop stays and the driver must be reset after it instead.

## Owner's suspect 2: the finger and the ratchet. Cleared as the cause of the runaway

A pawl cannot let a ratchet run. The teeth are cut so the spool slips under the finger when winding (clockwise) and meet the finger's face when falling (counterclockwise). A finger that is still grazing the teeth during a down move catches a tooth and stops the spool; the motor runs on because the clutch frees in that direction (rod counterclockwise against a stopped spool is the free way). That gives a spider that does not move and a motor that keeps stepping, never a spider that runs. The owner confirmed the finger out at setrel 30 by eye, and the model shows 1.38 mm of air between the tip and the separator (`python cad/generate.py`).

Where the finger does matter: it is the only thing that can hold the spider when the motor's hold is gone. Today the firmware leaves the spider on the motor alone after `rel`, after a jog, after a rewind that was not stopped by the switch, and for the 36 mm back-off after a switch stop (lines 605, 665, 603 to 616). Each of those is a runaway waiting for a bump. The lock sequence itself (finger in 350 ms, seat 1.2/12 turn at 30 rpm, driver off, servo off after 700 ms, lines 619 to 657) is sound and the logged locks all read "seated"; the 300 mm losses of row 41 were measured by the owner's tape at the switch, before the lock, not during it.

setlock 85 against the drawn finger: the CAD check seats the finger over a 4.75 degree window of spool angle, with the finger at its drawn in-position; the firmware's 85 is the owner's calibration of the servo to that position and is not readable from the model. Nothing in the data says the lock lets go; leave it.

## The drive chain, part by part

| part | holds the load winding up (proven) | can it slip only going down? | verdict |
|---|---|---|---|
| set-screw coupler, 5 mm motor shaft, 6 mm rod | yes, every wind | no, a slipping clamp slips both ways | cleared by the asymmetry; the loose screws were a real but separate fault, now tightened |
| clutch rollers on the 6 mm rod (doc 01: hardened rod) | yes | no, it is the same wedge direction for winding, holding and lowering | cleared by the asymmetry |
| clutch cup in the PLA hole (10.2 mm, bearing measured 9.99) | yes | no, same direction | cleared for the runaways; stays a slow-creep risk under a day of standing load, see the catalogs below |
| motor | yes, 5.2 N.cm pushing | yes: pushed, in quiet mode, after a dead stop, at half current, it can go to almost nothing | the cause |

What the catalogs say about the cup, for the record: drawn cup clutches "perform best only with press fitting into a normal housing", steel housings are the design case, an aluminium housing is rated at 50 percent of the catalog torque and the NSK FCP series exists for plastic housings (NSK B231). Nadella: "an insufficient press fit and use of a lower strength housing material can result in more internal clearance and reduced performance of the clutch." HF0612 is rated 1.76 N.m; the spider asks 0.0074 N.m, 0.4 percent of that. So the PLA housing is far below best practice and still has a wide margin against the spider's own weight; it cannot be the thing that lets go only on the down side. A marker line across the bearing rim and the plastic (owed since row 38) is still worth one minute when the spool is next in reach.

## Every 2026-10-06 measurement against the one cause

| measurement | explained by "driver left in a bad state after the dead stop, motor at half hold, then pushed past a pole" |
|---|---|
| +1 turn winds and stays; rewinds reach the switch | yes: fresh driver after a lock, motor pushing, 5.2 N.cm against 0.74 |
| three jog -1600 let down about 1750 mm | yes: the release was cut dead by the switch first; every jog then ran on the upset driver |
| switch stop, ease-off and lock let down about 300 mm | yes: the dead stop at 240 rpm, then the back-off ran down on the upset driver with the spider on the motor alone |
| page drop ran past 750 mm to the end | yes: unload cut dead at the top, then a clutch slam at the stop (finding 5) onto the weakest torque point |
| jog -200 let it fall the whole line, coupler tight | yes: `rel` cut dead by the switch after 117 steps, then the jog |
| slid about 1 m with no command, driver on, after minutes | yes if the driver had tripped off or settled at a low current after the switch stop; the trigger for the exact moment is not known. This is the one row where the cause is inferred, not shown |
| fast grinding noise from the motor | yes: the rotor dragged past its poles |
| spool counterclockwise by hand turns the motor with it | yes: the chain is engaged; the hand out-pulls a 2.8 N.cm hold easily |
| tape: coupler back about 1/2 turn while the spider fell about 2 turns | only if the eyeball count is low by 1.5 turns, or 1.5 turns slipped in the clutch at the same moment. This is the one measurement that points away from the motor, and it was a count during a fast spin. The slow-motion test settles it |

## Fixes, cheapest first

1. **Firmware: finger in before any down move ends, and reset the driver after every dead stop.** At a switch stop: finger in first (350 ms), then driver off and on again (the EN cycle the datasheet asks for, with one step pulse then the settle so the tuning runs at run current), then the seat move lets the spool down onto a tooth, then driver off. The spider can never fall more than one tooth (30 degrees, 13 mm of line). Do the same at the end of `rel`, jogs and rewinds: the firmware's own message "off lets it slide down" is the state to retire. No hardware. Needs a flash, after a lock, after the owner's yes.
   Same flash, from Codex: a detached servo no longer counts as "finger out" (`servoDeg` check at line 412), and the "lost steps on the stop" log line stops naming one cause and stops clearing the fault count.
2. **Settings: `dropacc` 80000.** Keeps the spool on the rod during the drop. Page or console, no flash.
3. **DIP switch 3 ON on the expansion board, after a meter check** that the module's 4th pin then reads about 5 V. Removes the standstill current cut: full 0.58 A hold. If the pin reads 0 V with the switch on, this road is closed and finding 3 stays as it is.
4. **Vref to 0.95 V** (0.67 A, the motor's rating): 15 percent more torque everywhere. Pot on the module, motor unplugged, 12 V on, as doc 02 says.
5. **spreadCycle:** solder a 20K resistor at the empty R7 place on the V1.3 module (SPREAD pin to VIO, the schematic's own note). Soldering. This is the one change that removes finding 1 at the root; 1 to 4 make the motor strong enough that finding 1 rarely bites.
6. **Only if 1 to 5 leave a runaway:** the marker test of the handoff, slow motion, and the bearing rim line.

## Tests that prove it, in order

- Before anything: the owner turns the spool counterclockwise by hand now, driver on as the board reports. If the motor resists as it did this morning, the hold is there and finding 1's milder form (bad current state) is the one in play; if it turns nearly free, the driver has tripped off and finding 1's worse form is confirmed. **Answered by Joe the same evening: nearly free.** The driver chip had switched the motor off on its own fault flag with the firmware still reporting it on. Fix 1 (with the driver reset) and fix 2 were built, flashed and set that evening; fixes 3 and 4 are his hands; fix 5 is "later" by his word.
- With the device locked: hang the spider on the finger alone (driver and servo off, as a lock leaves it) for ten minutes and read the line's height before and after. The finger at setlock 85 holding a static load is Codex's bench check and the proof that fix 1 has something to lean on.
- After fix 1: `jog -1600` moves the spider down about 157 mm and the finger holds it there. Logged.
- A switch-stopped rewind, then a second rewind, runs 20 to 35 mm. Logged.
- Ten page drops at `dropacc` 80000, each stopping at 620 mm. Logged.

## Codex cold audit (step 2)

Codex (codex-cli 0.153.4, read-only, blind to the section above) was given the same question, the same facts and the same six files. It returned six MAJOR and three MINOR findings, no blocker. Each was checked here against the code or the schematic before it counts. Severities are Codex's own.

**Where Codex agrees, and what checked out:**
- MAJOR, `machine.cpp` 189 and 603, TMC2209 section 6.5 to 6.6: the dead stop at the switch followed at once by the reverse back-off, with the driver never cycled; Codex: "StealthChop explicitly permits unrecoverable regulation or protection faults after abrupt stops" and notes that `driverOn()` returning early means release, drop, rewind, back-off and jogs give no recovery. Same as finding 1. Verified in the code.
- MAJOR, `machine.cpp` 149 and 243, section 6.1: the 200 ms settle does not meet AT#1 (needs run current, which needs one step first). Codex adds that the unload "actually peaks around 40 rpm over only 16.6 full steps", so it does not meet AT#2 either (the velocity tuning, 60 to 300 rpm over up to 400 full steps). Checked by arithmetic: 133 steps at a 120 rpm setting with the 600-step ramp peaks at 40 rpm in 0.25 s. So a down move that has not been preceded by a full-speed rewind in the same powered stretch runs with the driver's velocity tuning still at its factory starting point. This sharpens finding 2 and is added to it.
- MAJOR, `machine.cpp` 369, 620, 628: after the dead stop the finger stays out through the 1.2 s back-off, then 350 ms, then the 1.1 s seat; the driver goes off before the 700 ms servo hold. Timings verified by arithmetic (200 and 160 steps at 30 rpm with the 600-step ramp). Codex's fix, finger engaged and the motor still holding through the seating dwell, is fix 1 here. Its hardware ask, calibrate `setlock 85` against the ledge under a static load, is a fair bench check and goes in the tests.
- MAJOR, `config.h` 108, doc 01 line 62: the drop's 1.2 g start outruns gravity and the 0.6 g stop needs about 1.18 N.cm from the spider alone, with no shown braking margin. Same as finding 5; Codex rightly adds that the drop settings cannot explain the jog or the idle slide on their own.
- MINOR, doc 02 line 30, sections 3.4 and 5.2: PDN_UART low gives about 53 percent standstill current, about 0.31 A at 0.825 V, "but that reduction alone does not establish why a nominal 6 N.cm motor loses a 0.74 N.cm static load". Agreed on both halves; this is why finding 3 is a contributor and finding 1 is the cause. Codex's fix is the same DIP 3 check, and it supplied the V1.3 schematic, which confirmed that the DIP 3 position is PDN_UART (UART_RX, R6 pull-down).
- MINOR, doc 02 line 32: no chopper-mode comparison was ever done, and "successful upward motion does not validate downward regulation or holding". Agreed; this is the asymmetry argument from the other side. Codex's fix for V1.3, populate R7 with 20K to VIO, corrected fix 5 here (the V1.2 manual's moved resistor is the older board).
- MINOR, `machine.cpp` 412 and 664: a jog's end detaches the servo but keeps `servoDeg` at 30, so the next jog skips the release because of the last command alone, with the finger unpowered. Verified; the board is in exactly that state now (servo off, 30). Codex also notes the CAD seat check tests one drawn finger pose, not the 85 and 30 calibration. Agreed; added as a small firmware fix (invalidate the finger-out state on detach, or keep the servo powered until lock).

**Where Codex differs:**
- Its top MAJOR (doc 01 line 9, `generate.py` 183) keeps the mechanical joints open and puts witness marks on every joint first: the tape count "requires relative motion downstream of the coupler if those counts are accurate, which motor step loss alone cannot explain", and the once-slipping 10.3 housing "makes cup retention a priority". This audit ranks the motor first on the ground that every joint carried the same torque in the same direction on every wind that worked. Codex's point stands as the one measurement this audit cannot absorb without doubting the eyeball count, so the marker test stays in the plan as the arbiter, after the free fixes rather than before them.
- MAJOR, `machine.cpp` 347 to 349 and doc 04 line 108: the "lost steps on the stop" log line names one cause for excess rewind travel and clears the fault count. Verified in the code. A logging and wording defect, not a motion one; worth fixing with the firmware change (log distances as commanded, keep a latched "spool ran past the motor" note).

**What survived:** all nine, with the first one surviving as a disagreement on order, not on fact. Nothing Codex raised contradicts the datasheet readings above, and two of its items (AT#2 never reached on the unload; R7 on V1.3) improved this file.

## How this was checked, 2026-10-06

- Board: `/api/status` over the network, read once at the start of the session, no commands sent.
- Firmware: the files named above, read in full at commit 7fdf7de.
- Datasheet quotes: TMC2209 rev 1.05 pages 8, 9, 23, 35, 42, 50, pulled as text from the Reichelt mirror.
- BTT: V1.3 schematic read as a picture (PDN_UART = header UART_RX, R6 20K to ground, in the MS3 position; SPREAD pin to VIO through the empty R7, "R7=20K SpreadCycle, R7=NC StealthChop"); V1.2 manual page 8 for the older board's method.
- Codex: run through the `codex-auditor` agent, read-only, its findings verified line by line as the section above records.
- Motor: Tindie listing of 11HS12-0674S. Inductance unverified.
- Catalog quotes: NSK B230 to B233, Nadella drawn cup roller clutches, pulled as text.
- Torque and jolt figures: arithmetic from those numbers, stated in the table.
- Not verified: which form finding 1 takes on this board (bad current state or tripped off); what DIP 3 connects on this expansion board; the motor's inductance; the V1.3 module's resistor layout.
