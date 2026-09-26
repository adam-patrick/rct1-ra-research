# RCT1 RetroAchievements Phase 2E — Cash Discovery

## Result

Cash remains **unvalidated**. A controlled normal-gameplay transition changed
the displayed amount from `$10,000.00` to `$9,540.00`, but exact scans did not
produce a candidate that persisted between the two paused states.

Confidence in the negative result: **Medium** for the tested whole-dollar and
integer-cent representations. Other encodings or a more targeted changed-value
scan remain possible.

## Observations

* The fresh process was PID `22603`, with module base `0x00400000`.
* The initial paused display showed `$10,000.00`.
* After a normal simulation transition, the game was repaused at `$9,540.00`.
* A whole-dollar scan for `10000` found candidates including
  `0x00a66575`, `0x00b20300`, and a repeated-pattern region near
  `0x00b63721`; the `9540` scan found `0x00c19a24` but no common address.
* An integer-cent scan for `1000000` produced only a 16-bit false-positive
  match, not a 32-bit candidate. The `954000` scan produced several 16-bit
  matches, with no common address to the initial scan.
* The previously suspected `base + 0x766480` location was not promoted and
  remains explicitly unvalidated.

## Interpretation

The tested exact-value representations do not explain the displayed cash
transition. The result does not prove that cash is inaccessible; it eliminates
the simplest whole-dollar and integer-cent exact scans for this transition.

The next cash experiment should use the scanner's changed-value filtering while
holding the game paused, or inspect a wider set of signed/fixed-point and
split-field representations. It should continue to use normal gameplay for the
value change and read-only process inspection.
