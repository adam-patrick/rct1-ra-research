# RCT1 research workflow

Read `README.md`, `phase2/state_reader/README_scanner.md`, and the latest
Phase 2 reports before running a new experiment. The reports are the canonical
record of current locator evidence and confidence; do not infer current status
from an old report's historical next-experiment section.

## Runtime safety

Keep experiments read-only. Use `process_vm_readv()` and `/proc` inspection
only. Do not write process memory, freeze values, inject DLLs, patch binaries,
modify saves, or begin RetroAchievements communication/achievement work before
the state model is stable. Keep the canonical Steam installation untouched and
use the validated isolated launcher.

## Controlled-value protocol

For any value that changes during simulation:

1. Establish the displayed value and pause the game through the normal UI.
2. Scan while paused and record the PID, module base, representation, and
   candidate count.
3. Unpause through the normal UI and perform one controlled gameplay action or
   wait for one known transition.
4. Pause again before scanning; never treat a scan taken during live simulation
   as validation evidence.
5. Apply changed/increased/decreased/delta filters, then repeat an unchanged
   paused check.
6. Restart the game completely, derive the new module base, and repeat the
   read in a fresh process.

Record OBSERVATION, HYPOTHESIS, and VALIDATED FINDING separately. A single
exact-value match is only a candidate. Update the relevant report and state
reader only after the evidence meets the report's validation standard.

Do not push repository changes unless the user explicitly requests it.
