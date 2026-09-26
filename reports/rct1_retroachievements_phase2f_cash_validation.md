# RCT1 RetroAchievements Phase 2F — Cash Validation

## Result

Cash was validated for the supported `RCT.EXE` build as a little-endian
unsigned 32-bit runtime field at:

```text
module base + 0x69c590
```

The raw value represents displayed dollars multiplied by 10:

```text
$9,540.00 -> 95400
$9,516.00 -> 95160
$9,316.00 -> 93160
$10,000.00 -> 100000
```

Confidence: **Medium**.

The field survived two controlled cash decreases and a complete fresh-process
restart. Additional scenarios and a fresh non-round cash value would strengthen
the result.

## Evidence classification

### OBSERVATIONS

* The controlled cash process was PID `22603`, with module base `0x00400000`.
* The paused baseline displayed `$9,540.00`.
* A normal gameplay transition changed the display to `$9,516.00`; the
  changed-value scanner reduced 40 scaled candidates to one address, duplicated
  only as signed and unsigned interpretations.
* The candidate was `0x00a9c590`, or `base + 0x69c590`, with raw value `95160`.
* A second normal transition changed the display to `$9,316.00`; the same
  candidate read raw value `93160`.
* A repeated unchanged paused check retained the same candidate.
* Its 256-byte neighborhood contained a cluster of nearby 32-bit and smaller
  state values; no complete structure layout is claimed.
* After a complete restart, the fresh process was PID `25039`, again with
  module base `0x00400000`.
* The fresh process displayed `$10,000.00`, and the state reader read raw
  value `100000` at `base + 0x69c590`.

### HYPOTHESES

* The field is likely a signed/unsigned 32-bit fixed-point cash value with a
  scale of 10 display dollars per raw unit.
* Its proximity to the validated guest-count and park-rating fields suggests a
  shared live park/global state region, but proximity alone does not establish
  field ownership or structure layout.

### VALIDATED FINDING

For the supported executable hash:

```text
bdfebd64383b231de0252fe0726523d1c45aa2c4da919c2d7ed8bfb7aaa05c76
```

read a little-endian unsigned 32-bit value at
`current_RCT_module_base + 0x69c590` and divide by 10 to obtain the displayed
dollar amount. The locator tracked two controlled decreases and survived one
complete fresh launch.

The earlier candidate `base + 0x766480` remains explicitly failed and is not
used by the state reader.

## Experimental procedure

1. Paused at the displayed `$9,540.00` baseline.
2. Used the scanner's heuristic baseline scales (`x1`, `x10`, `x100`, `x1000`)
   across signed and unsigned 8-, 16-, and 32-bit interpretations.
3. Unpaused normally, allowed cash to decrease to `$9,516.00`, and repaused.
4. Applied the scanner's decreased-value filter, reducing 40 candidates to the
   same address in signed and unsigned 32-bit forms.
5. Repeated the transition to `$9,316.00` and retained the same address.
6. Closed and relaunched the unchanged isolated runtime.
7. Confirmed the same module-relative locator read raw `100000` for the fresh
   `$10,000.00` display.

Earlier exact-value scans alone failed to find a stable cash field; the
changed-value workflow was necessary.

## Locator classification

Classification: **stable module-relative offset observed; backing storage is
anonymous/dynamically mapped**.

No pointer chain, signature, or file RVA has been established.

## Code and documentation changes

* `phase2/state_reader/rct1_state_reader.c`: added a read-only `u32` cash read
  at `base + 0x69c590`, reporting the raw value and scale.
* `phase2e_cash_discovery.md` remains the historical negative result for the
  initial exact-value-only attempt.

## Next experiment

Validate all three fields together in one additional fresh launch, then move
to scenario/objective state. Do not begin achievement or RA communication work
until those state boundaries are understood.
