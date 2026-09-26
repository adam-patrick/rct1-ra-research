# RCT1 RetroAchievements Phase 2 Runtime Report

## Executive Summary

**Result: Significant blocker encountered.**

The installed `RCT.EXE` can be launched through the local Steam/Proton/Wine
stack and its Windows process can be observed from Linux. However, the game
stops at a legitimate startup dialog requesting the RollerCoaster Tycoon
Loopy Landscapes Pack CD. No CD, ISO, or mounted image was present in the
checked local media locations. Therefore I could not start Forest Frontiers,
make legitimate cash/guest/rating changes, or establish runtime locators.

The runtime evidence is still useful: the process is visible through `/proc`,
the main image was mapped at `0x00400000` in the observed launch, and its
large code/data regions are anonymous or privately mapped rather than simple
file-backed ranges. This is consistent with the unusual PE layout and
protection/loader behavior found in Phase 1, but it is not enough to claim
that ExeLock unpacking was solved.

The architecture remains **promising but not yet stable** for a future
external read-only state reader. The immediate next step is to provide the
legitimate required media or use a separate authorized installation that
passes the CD check, then repeat controlled gameplay and memory filtering.

## Runtime Environment

### Steam launch behavior

- Steam app: `285310`, `RollerCoaster Tycoon: Deluxe`.
- Steam app manifest: `$HOME/.steam/steam/steamapps/appmanifest_285310.acf`.
- Installed prefix: `$HOME/.steam/steam/steamapps/compatdata/285310`.
- Prefix metadata before the test: `10.1000-200`.
- Steam was started with `steam -applaunch 285310`; the client initialized but did not produce an RCT process during the observation window.
- A direct equivalent Proton launch was then used for controlled inspection. Proton 8.0 reached the game, but attempted to downgrade the existing prefix; that path was stopped. A subsequent Proton 10.0 attempt reported a Wine-server version mismatch because the earlier test server was still present.
- The live process observed in the successful launch attempt was served by the Proton 8.0 Wine runtime. This is a runtime-test condition, not a validated statement of Steam’s final selected compatibility tool.

### Process and mappings

Observed process:

| Item | Observation |
|---|---|
| Windows process name | `RCT.EXE` |
| Linux-visible PID | `30031` during the live observation |
| `/proc` visibility | Yes; `/proc/30031/status`, `/proc/30031/maps`, `/proc/30031/cmdline`, and `/proc/30031/fd` were readable |
| Linux executable shim | Proton/Wine `wine-preloader` |
| RCT image base | `0x00400000` in this run |
| ASLR comparison | Not tested across successful game sessions; no valid cross-launch conclusion |
| RCT module paths | `$HOME/.steam/steam/steamapps/common/RollerCoaster Tycoon Deluxe/RCT.EXE` plus anonymous/private runtime ranges |

Selected mapping facts from PID 30031:

```text
00400000-00401000 r-xp ... RCT.EXE
00401000-0088a000 r-xp ... anonymous
0088a000-00c3e000 rwxp ... anonymous
00c3e000-00c3f000 rwxp ... RCT.EXE
00c3f000-00c44000 r-xp ... RCT.EXE
00c44000-00c46000 rwxp ... anonymous
00c46000-00c48000 rwxp ... RCT.EXE
00c48000-00c4c000 rwxp ... anonymous
```

The mapping pattern is materially different from a conventional PE where all
code/data sections are straightforward file-backed mappings. It may reflect
the old executable’s section layout, Wine’s loader, ExeLock, or a combination;
more runtime stages are needed before identifying the cause.

### CD-check result

The visible game dialog stated:

> Please insert your RollerCoaster Tycoon Loopy Landscapes Pack CD in the following drive:

The checked local locations contained no mounted optical media and no likely
RCT CD/image file. I did not bypass the check, alter registry/media settings,
mount an image, or modify game files.

## State Discovery Results

| State | Found? | Encoding | Runtime Address Example | Stable Locator | Confidence |
|---|---|---|---|---|---|
| Cash | No | Not determined | None | None | Not assessed |
| Guest Count | No | Not determined | None | None | Not assessed |
| Park Rating | No | Not determined | None | None | Not assessed |
| Scenario | No live scenario | Not determined | None | `Scenarios/sc0.sc4` is only a file-level anchor | Not assessed |
| Game Date | No | Not determined | None | None | Not assessed |
| Scenario Status | No | Not determined | None | None | Not assessed |

No values are reported as candidates because the game never reached a running
park and no visible reference values existed for successive-state filtering.

## Cash Investigation

Not completed. The CD check blocked Forest Frontiers before a cash value could
be observed or changed through legitimate gameplay. No search result is being
promoted from a coincidental integer match.

## Guest Count Investigation

Not completed for the same reason. No visitors entered a park, so there were
no consecutive visible guest counts with which to filter 16-bit or 32-bit
memory candidates.

## Park Rating Investigation

Not completed for the same reason. No park state or rating display was
available, so no bounded-value scan was performed.

## Scenario Investigation

The installed file-level Forest Frontiers anchor remains:

```text
$HOME/.steam/steam/steamapps/common/RollerCoaster Tycoon Deluxe/Scenarios/sc0.sc4
```

The file contains the readable title `Forest Frontiers`. The live process did
not reach scenario selection or loading, so no internal scenario ID, filename
pointer, or objective structure was identified.

## Stability Across Launches

| Test | Module Base | Cash Locator | Guest Locator | Rating Locator | Result |
|---|---:|---|---|---|---|
| Attempt 1: Steam `-applaunch` | None | None | None | None | Steam initialized but no RCT process was observed during the first window. |
| Attempt 2: Proton 8 direct | `0x00400000` observed | None | None | None | RCT process reached the CD prompt; no park session. |
| Attempt 3: Proton 10 direct | None | None | None | None | Blocked by stale Wine-server version mismatch after the Proton 8 prefix transition. |

The single observed module base is not a stability result. At least three
successful launches with Forest Frontiers loaded are still required.

## Candidate Data Structures

No coherent `ParkState`-like structure was identified. The only useful runtime
observation is that the mapped RCT image has large anonymous executable and
read/write ranges adjacent to the canonical image base. Those regions are
worth capturing after a successful park load because they may contain the
unpacked code or live globals, but their purpose is currently a hypothesis.

## Proof-of-Concept Reader

Because stable state locators were not established, no fake state reader was
created. Instead, a read-only diagnostic scanner was added:

- Source: [`rct1_state_scanner.c`](../phase2/state_reader/rct1_state_scanner.c)
- Intended build: `cc -O2 -Wall -Wextra -o rct1_state_scanner rct1_state_scanner.c`
- Intended run: `./rct1_state_scanner` or `./rct1_state_scanner 0x00400000 64`
- Privileges: normally the same user as the RCT process; `process_vm_readv()` may be blocked by host ptrace policy.
- Behavior: finds `RCT.EXE`, reports its command line and RCT mappings, and optionally reads a caller-specified byte range. It never writes process memory.
- Current limitation: it reports diagnostics, not cash, guests, rating, or scenario state.

## Risks / Unknowns

- The required Loopy Landscapes Pack CD is not currently available in a
  mounted or discoverable local image.
- Steam’s exact selected compatibility tool was not conclusively resolved from
  the app configuration; the observed direct test used Proton 8.0, while the
  prefix metadata indicated Proton 10.0-era files.
- The Proton 8 test changed only the compatibility prefix’s runtime-managed
  files while upgrading/downgrading it; no installed game files were changed.
- The RCT process ended before controlled memory reads could be used for game
  state. A small read attempt after exit correctly produced no data.
- No debugger attachment, DLL injection, patch, process-memory write, trainer,
  scenario edit, save edit, or RetroAchievements network operation was used.

## Recommended Phase 3

The smallest useful next step is to rerun the controlled test with legitimate
Loopy Landscapes media available and a clean, deliberately selected Proton
prefix. Start Forest Frontiers, manually record displayed cash/guest/rating,
make one normal change at a time, and use the diagnostic scanner or a temporary
read-only memory-dump helper for successive-state filtering. Only after two or
three fresh launches reproduce the first three values should scenario identity,
completion state, ride arrays, or RetroAchievements integration be considered.
