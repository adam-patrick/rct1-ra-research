# RCT1 RetroAchievements Phase 2B — State Discovery

## Executive Summary

**Promising but not yet stable.** In the exact Steam RCT Deluxe build and established Proton 10.0 environment, a live read-only scan found transient integer matches for visible cash values, but the candidate did not remain correct on the next simulation tick. Guest count and park rating were not isolated from coincidental values, so no primary value is claimed as reliable.

## Runtime Baseline

- Proton: `$HOME/.steam/steam/steamapps/common/Proton 10.0/proton`
- Prefix: `$RCT1_RESEARCH_DIR/runtime-test/compatdata`
- Installed copy: `.../compatdata/pfx/drive_c/Program Files (x86)/Infogrames Interactive/RollerCoaster Tycoon Deluxe`
- `RCT.EXE` SHA-256: `bdfebd64383b231de0252fe0726523d1c45aa2c4da919c2d7ed8bfb7aaa05c76`
- Current PID: 35514
- Current module base: `0x00400000`
- Visible session: Forest Frontiers, May Year 1, park closed, cash `$9,567.20`, guests `0`.

## State Discovery Matrix

| State | Found? | Raw Encoding | Field/Offset | Stable Locator | Confidence |
|---|---|---|---|---|---|
| Cash | Candidate only | integer cents observed transiently | several transient matches, including `base + 0x766480` | not established | Low |
| Guest Count | No | — | — | — | Low |
| Park Rating | No | — | — | — | Low |
| Scenario | No | — | — | — | Low |
| Date | Visible only | — | — | — | Low |
| Scenario Status | No | — | — | — | Low |

## Cash Discovery

The visible cash changed from `$9,567.20` to `$9,516.10` during the live session. Read-only scans found matching integer values at multiple writable locations, including transient matches near `base + 0x766480`, but the packaged reader did not reproduce the visible amount on the next check. This demonstrates why a single exact-value hit is insufficient; no cash locator is promoted to a validated result.

The candidate has not yet met the required three-fresh-launch validation rule. It must be confirmed after a normal gameplay cash change and across three fresh launches before being called High confidence.

## Guest Count Discovery

The visible count was `0`. Zero-value scans were not used as proof because writable memory contains many zeroes and repeated structures. The simulation was resumed with the normal in-game pause key, but no reliable guest locator was established in this pass.

## Park Rating Discovery

The current objective panel did not expose a numeric rating field. No reliable runtime locator was established.

## Read-Only State Reader

Source: `phase2/state_reader/rct1_state_reader.c`.

The reader locates `RCT.EXE` and derives the executable base from `/proc/<pid>/maps`, but conservatively reports all state values as unavailable until locators are validated. It uses read-only process inspection only; there is no process-memory write path.

Build and run:

```sh
cd phase2/state_reader
cc -O2 -Wall -Wextra -o rct1_state_reader rct1_state_reader.c
./rct1_state_reader
```

## Remaining Unknowns

- Cash candidate needs normal value-change and three-launch validation.
- Guest count needs controlled transitions from zero after the park is opened.
- Park rating needs a normal UI read and controlled change.
- No alternate scenario or save/load validation has been completed.

## Phase 3 Recommendation

Do not begin RetroAchievements integration yet. The smallest useful next step is controlled validation of the cash candidate, followed by guest-count discovery and park-rating discovery.
