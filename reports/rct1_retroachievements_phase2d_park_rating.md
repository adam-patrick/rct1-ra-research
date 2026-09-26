# RCT1 RetroAchievements Phase 2D — Park Rating Discovery

## Result

Park rating was validated for the supported `RCT.EXE` build as a little-endian
unsigned 16-bit runtime field at:

```text
module base + 0x69ce64
```

The observed absolute address in the original process was `0x00a9ce64`. The
same module-relative locator worked in a fresh process at PID `22603`, whose
module base was also `0x00400000`.

Confidence: **Medium**.

The candidate tracked four controlled same-process transitions and then matched
two fresh-process states (`0` and `200`). More scenarios and another fresh
launch would strengthen the result. Cash remains explicitly unvalidated.

## Evidence classification

### OBSERVATIONS

* The original process was PID `18279`, with module base `0x00400000`.
* The game was paused before each rating scan; the value was changed by
  unpausing normally and then repausing before the next scan.
* Same-process displayed rating transitions were:

  ```text
  723 -> 686 -> 678 -> 677
  ```

* The candidate `0x00a9ce64` appeared as a `u16` value for each of those
  paused scans.
* Repeated paused scans at `686` and `678` continued to return the same
  candidate.
* A complete restart produced PID `22603`, again with module base
  `0x00400000`.
* The fresh park initially displayed rating `0`; the state reader read
  `base + 0x69ce64` as `0`.
* After the fresh park advanced to displayed rating `200` and was repaused,
  both the targeted scan and state reader read `base + 0x69ce64` as `200`.
* The same fresh process reported guest count `0` at the rating-`0` state.

### HYPOTHESES

* The field is likely part of the same live park/global state region as the
  validated guest count at `base + 0x69c9f8`, because the two offsets are only
  `0x46c` bytes apart and both survive a process restart.
* The anonymous runtime mapping is dynamically backed state rather than a
  file-backed executable RVA. No structure layout is inferred from proximity
  alone.

### VALIDATED FINDING

For the supported executable hash:

```text
bdfebd64383b231de0252fe0726523d1c45aa2c4da919c2d7ed8bfb7aaa05c76
```

read a little-endian unsigned 16-bit value at
`current_RCT_module_base + 0x69ce64`. It matched the displayed park rating in
four controlled transitions in one process and in two states of a fresh
process.

This is a stable module-relative offset observed for the supported build. It is
not established for other executable hashes, compatibility runtimes, scenarios,
or saves.

## Experimental procedure

1. Opened the normal park-information panel and recorded its displayed rating.
2. Paused the game before each exact-value scan.
3. Used normal unpause/re-pause transitions to produce known rating changes.
4. Scanned the paused values `723`, `686`, `678`, and `677` with the existing
   read-only targeted scanner.
5. Repeated stable scans at intermediate values to exclude timing artifacts.
6. Closed the original game, relaunched the unchanged isolated runtime, and
   re-identified the process and module base.
7. Confirmed fresh-process values `0` and `200` using both the scanner and the
   state reader.

Earlier live scans without a paused-before-scan protocol produced transient
candidate addresses and are not used as validation evidence.

## Locator classification

Classification: **stable module-relative offset observed; backing storage is
anonymous/dynamically mapped**.

No pointer chain, signature, or file RVA has been established.

## Code and documentation changes

* `phase2/state_reader/rct1_state_reader.c`: added a read-only `u16` park-rating
  read at `base + 0x69ce64`.
* This report records the controlled transition and fresh-process evidence.
* Cash remains unavailable because `base + 0x766480` was transient and did not
  track cash reliably.

## Next experiment

Validate both guest count and park rating in one additional fresh launch, then
investigate scenario/objective state. Cash should remain unvalidated until a
separate paused-before-scan experiment produces controlled cash transitions.
