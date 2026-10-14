# Audit: the web page and the hands-on side, near horizon

Desk audit of `src/web.cpp`, `src/console.cpp`, `src/machine.cpp`, doc 04 and the bench log, written 2026-10-14 for the owner. No motion, no flash, no code changed. Horizon rules apply: each approach starts from a different first principle, the current page is not an option, nothing here is built.

## Ground truth first

This file is a record of one reading. The repo on disk and the board's own page win; if they disagree with this file, this file is stale, say so out loud.

```
git log -1 --oneline                                  # where the repo is now
git log -1 --oneline -- docs/audit_webui_horizon.md   # when this file was last true
```

Board read 2026-10-14 over the network (`/api/status` at 192.168.1.138, the fixed address): waiting for the doorway to clear, armed, home, no fault, driver off, 157 drops, last drop measured 778 mm, trigger to landing 1.79 s. Settings on the board: line 1333, dropmm 848, droprpm 600, rpm 340, settle 1200, firecm 200, clearcm 150, clearms 1000, rearm 0, leadms 900. Page source read from the working tree, which holds the other live session's uncommitted fixed-address work.

## Verdict

**The page shows the machine well and hides what the machine just did. Every button's answer lands in the Console card at the bottom of a long page, three of the four things the owner has asked a session to explain this week were already in that log, and nothing on the page says whether a tuned value has been saved.** The fixes are all small, all page or page plus one firmware struct, and none costs a run or a part.

## What the page is today, read from `src/web.cpp`

| Card, in page order | What is on it | Read |
|---|---|---|
| Status | state line in plain words (18 states), chips (armed, home, trigger, motor powered, fault), 6 rows | good: the state line is the best thing on the page |
| Radar | chips, distance strip, readings table, 7 trigger-rule controls, 5 sensor knobs, Learn the empty room, Save settings, check line, 60 s timeline, a paragraph of help | the tallest card, second from the top, between Status and Run |
| Run | Drop it now, Arm, Stop, Motor and servo off, Clear and re-arm, Bring it home, Last fault log, one grid | Drop (purple) and Stop (red) share a grid with recovery buttons; no confirm on Drop |
| Bench: finger servo | live angle, nudges, go to and store angles | fine |
| Bench: motor | 4 jogs, Rewind, Lock, Release, Set drop length here | three up-moves on the page (Rewind here, Bring it home in Run, Set drop length here) with different results; Set drop length changes a saved setting with no confirm |
| Settings | 14 number fields, applied on change, Save settings, Factory values | nothing marks a changed-but-unsaved value; a second Save button lives in the Radar card |
| Console | 60-line log, command box | the only place a refusal or a `[done]` line is shown |
| Network, Firmware | network name, fixed address, update link | fine |

Facts behind the verdict, each with where it was read:

- **Feedback is far from the finger.** Every button is a console command, and its reply (`[done] ...`, `refused: busy (...)`, `refused: stopped after faults, send clear first`) is written only to the log (`console.cpp` `motion()`, `web.cpp` `tick()`). On a phone the Run card and the Console card are about four screens apart. A settings field that is refused keeps the typed value until the next poll overwrites it, with no sign why.
- **The page has no memory of the last cycle.** `/api/status` carries the last rewind's steps, the measured drop and the landing time, but not whether the switch was hit first try or on the retry, and nothing for the cycles before. The owner's reports this week ("failed to rewind fully", "dropped, went back up, then dropped and now remains hanging") were answered from the log, which only reaches back 60 lines and dies with the power (bench log 2026-10-13 and 2026-10-14).
- **Saved and unsaved look the same.** The owner tunes from the page overnight (dropmm 848, rpm 340, settle 1200, leadms 900 on 2026-10-14) and power cycles the board often. A value changed on the page is live at once and lost at the next power cut unless Save is pressed; no field says which.
- **Two of the three up-moves share a card and a look.** Set drop length here sits beside Rewind in Bench: motor. On 2026-10-13 a page press of it set dropmm to 607 during what the log reads as a manual rewind. The owner kept the number, so no defect, but the button changes a saved setting and the only confirm on the page is on Learn the empty room.
- **The spider's position is on the wire and not on the page.** `position` (microsteps, plus = up) is in every status reply and nothing displays it. 16.3 microsteps are one mm of line, so "about N mm below home, by the motor's count" is one line of page code. It drifts when the clutch slips and resets at every switch stop, so it needs that label.
- **Order is by build, not by use.** For the daily use (is it armed, did it fire, drop it now) the Radar card is in the way; for radar tuning it is the right card to be near the top. Both uses exist this week.

## Approaches, each from a different first principle

The current page "but tidier" is banned. Each one says what it makes easy, what it makes hard, its hidden failure, and what would have to be true for it to be the right answer.

### 1. The answer appears under the finger (principle: feedback is local)

Every button press shows its reply where the press happened: a one-line strip under the Run, Bench and Settings cards that carries the newest `[done]` or `refused` line for 6 s, and a thin bar pinned to the bottom of the screen with the state and the newest log line always visible. Page only; the lines already arrive in the status reply.

- Easy: knowing a press was refused, and why, without scrolling. The Console card can then move down or fold.
- Hard: nothing that is easy now.
- Hidden failure: during a cycle the log writes several lines a second, and a strip that shows each one flickers. It has to show the last line only, and hold a refusal longer than a progress line.
- True if: the page is used on a phone more than on a PC. The bench log says it is.

### 2. The page remembers the last cycles (principle: history beats a live reading)

The firmware keeps a ring of the last 20 cycle records: when, fired by what, drop mm told and measured, time to landing, how the rewind ended (switch first try, switch on the retry, count only, fault), home at the end. Kept in flash with the fault log so a power cut keeps them. The page shows them as one row per cycle with a colored chip for the ending, newest first, and a count of each ending since power-up.

- Easy: the owner's "what happened while I was out" questions, answered on the page, no session needed. The 1-in-25 missed switch of 2026-10-14 would read as one amber chip in a row of green.
- Hard: `machine.cpp` gains a record type that every cycle path must fill (drop, rehome, teach, the retry). One missed path is a wrong row.
- Hidden failure: flash writes on every cycle. Twenty-five drops a night is fine; a few thousand are not a worry either on this chip, but the write goes in the lock state, never in the drop.
- True if: he keeps asking what happened. Four such questions in the log this week.

### 3. Unsaved is a color (principle: persistence is a visible state)

The firmware holds the values as last saved beside the live ones and sends the names that differ. Every changed field gets an amber edge and a small "not saved", one Save bar appears at the top of the page whenever anything is unsaved and goes away when it is not, and the two Save buttons become one. A value that differs from the factory default gets a quiet dot.

- Easy: never losing an evening's tuning to a power cycle; seeing at a glance what has been changed from stock.
- Hard: `settings.cpp` keeps two copies and a compare; small.
- Hidden failure: the radar's own knobs (range, sensitivity, delay) live in the sensor, not in the board's flash, and must not get the amber edge. They need their own "kept in the sensor" mark.
- True if: he tunes from the page and power cycles. Both are in the log.

### 4. Where is the spider (principle: show the geometry, not the number)

A vertical strip beside the Status card: a mark for home (the flap), a mark for where the drop stops (dropmm), a mark for the line's end (line), and the spider drawn at its position by the motor's count, moving live. Dragging the drop mark sets dropmm; the number field still exists beside it. The teach flow becomes: jog the spider to where it should stop, watch the spider mark land there, press Set drop length here, which now asks "Save 612 mm as the drop distance?" with the number shown.

- Easy: setting the drop by eye, and seeing at once when the count and the real spider disagree (the clutch slipped).
- Hard: the drawing is honest only between switch stops. After a slip it is wrong until the next rewind. The label "by the motor's count" has to stay on it.
- Hidden failure: drag on a phone fights page scroll. A pair of coarse and fine buttons beside the mark is the safe form; drag is the nice-to-have.
- True if: he thinks in inches and mm rather than turns and steps. His log entries say he does.

### 5. Cards fold, and the page remembers (principle: progressive disclosure)

Every card gets a header that folds it, the fold state is kept in the browser, and the default is Status and Run open, everything else folded. Card order stays fixed so the spatial map holds; a folded card keeps its place and its height is one line.

- Easy: the daily view fits one phone screen; the radar card is one tap away, not four screens.
- Hard: nothing, once approach 1 exists. Without approach 1, folding the Console hides the only feedback there is, so this one depends on that one.
- Hidden failure: a folded card still polls and draws its canvases; the radar scope should stop drawing while folded or the phone warms up.
- True if: the phone is the main screen. Same evidence as approach 1.

### 6. The page has a far-away face (principle: the display is ambient)

A second view at `/watch`: the state word in letters the height of the screen, background green when armed and ready, amber while moving or waiting, red on a fault, the drop count in the corner. For a phone or tablet left on the hall table.

- Easy: seeing from across the room what the blue LED says, with words.
- Hard: nothing.
- Hidden failure: it duplicates the LED, which the owner asked for and has.
- True if: he watches the device from a distance more than he holds the phone. Not in evidence.

### 7. The bench walks itself (principle: the procedure is the interface)

The planned Calibrate card, roadmap item 6: one card that shows the current bench step, what to do with the hands, one button that runs the move, Pass and Fail buttons, results written to the log. The T1 to T8 tests and the radar walk tests S1 to S5 become the card's steps.

- Easy: running the bench without the handoff open on another screen; a log row written in the right shape every time.
- Hard: the step list lives in firmware and changes whenever a test changes.
- Hidden failure: a card that says "pass" when the owner pressed the wrong button; nothing on the board can check a Pass.
- True if: the bench tests are run more than once. They are, on every flash.

## Adversarial pass: what dies and why

- **Approach 6 dies.** The LED already does this, the owner asked for the LED and has it, and nothing in the log says he watches from a distance. A far-away face is a page nobody opens.
- **Approach 7 is parked, not dead.** It is already on the roadmap at 6 and belongs after the T tests have settled; building it now means rebuilding it when the tests change.
- **Approach 4 loses the drag.** A drag handle on a phone page that also scrolls is a fight the page loses. The strip, the live spider mark, the drop mark and the confirm on Set drop length here survive; dragging does not.
- **Approach 5 survives only behind approach 1.** Folding the Console with no other feedback makes the page worse.
- **Approach 2 survives with a smaller ring.** Twenty records at about 40 bytes each is under a kilobyte, kept in flash beside the fault log. It does not need a day's history; it needs last night's.
- **Approaches 1, 2 and 3 survive whole.** Each answers something the owner asked a session this week.

## Field name

The people who build this for a living call it operator HMI design (human machine interface: the screen a person uses to run one machine), and on small network devices the nearest prior art is the phone pages of the open-source firmware for lamps and plugs (the names worth searching are WLED and Tasmota; not read this session, so they are leads for the next search, not findings). Their habits that match this audit: a sticky state bar, settings marked saved or not, a fold per section.

## Advised order, with cost

| Order | What | Where | Size | Needs a flash |
|---|---|---|---|---|
| 1 | Reply strip under each button card, state and last log line pinned to the bottom | `src/web.cpp` page only | about 30 lines | yes, page lives in firmware |
| 2 | Confirm on Set drop length here, with the number it will save; one Save button | `src/web.cpp` | about 5 lines | yes |
| 3 | Unsaved marker and the one Save bar | `src/settings.cpp`, `src/web.cpp` | about 40 lines | yes |
| 4 | Last 20 cycles, kept through a power cut | `src/machine.cpp`, `src/settings.cpp`, `src/web.cpp`, doc 04 | about 120 lines | yes |
| 5 | Spider position strip, by the motor's count, with the drop and line marks | `src/web.cpp` | about 60 lines | yes |
| 6 | Cards fold, state remembered | `src/web.cpp` | about 30 lines | yes |
| parked | Calibrate card | roadmap item 6 | after the T tests | |

Items 1 to 3 fit one flash. Items 4 and 5 fit a second. No item costs a run, a part or a helper agent. The other live session holds uncommitted changes in `src/web.cpp`, `src/console.cpp` and `src/settings.cpp`; nothing here is built until that work has landed.

## Decisions, ruled by the owner 2026-10-14 ("1 yes, 2 yes, 3 yes, 4 yes, 5 later, 6 yes to now")

1. **Reply strip and pinned state bar.** Built the same day.
2. **Confirm on Set drop length here, one Save button.** Built the same day.
3. **Unsaved marker and Save bar.** Built the same day.
4. **Last 20 cycles on the page, kept through a power cut.** Built the same day, in the same flash as 1 to 3.
5. **Spider position strip.** Later: `ROADMAP.md` item 9.
6. **Cards fold with the state remembered.** Built the same day.

Status of the build is in `CHANGELOG.md` under 2026-10-14; what has and has not been seen working on the board is in `docs/commissioning_log.md`.

## How this was checked

- Page, handlers and JSON: `src/web.cpp` in the working tree, read 2026-10-14 (includes the other session's uncommitted fixed-address work).
- Command replies and the log ring: `src/console.cpp`; state names and the cycle paths: `src/machine.cpp` lines 113 to 132 and 711 to 880.
- Settings and the saved keys: `include/settings.h`, `include/config.h`.
- What the owner has asked and done from the page: `docs/commissioning_log.md`, rows 2026-10-11 to 2026-10-14.
- The planned Calibrate card: `docs/build_guide/build_guide.src.html` section 09, `ROADMAP.md` item 6.
- Board: one read of `/api/status` at 192.168.1.138, nothing sent.
- Not checked: the page on a real phone this session (read from source only); WLED and Tasmota pages (named as leads).
