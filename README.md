# RCT1 RetroAchievements Research

Research, experiments, and small read-only tools for investigating whether the
original RollerCoaster Tycoon Deluxe (`RCT.EXE`) can support a reliable
RetroAchievements integration.

This is a conservative reverse-engineering and runtime-state discovery project.
Local rcheevos feasibility has now been demonstrated in an isolated spike, but
production RA communication, authentication, and unlock submission remain
disabled while official standalone identity, approval, and Hardcore questions
are investigated.

## Current status

The project has reached a reproducible baseline, but it does not yet have a
validated achievement implementation.

- A clean, isolated Proton 10.0 runtime can launch the installer-created Deluxe
  copy and load the Forest Frontiers scenario.
- The target executable is the 32-bit `RCT.EXE` build identified by SHA-256
  `bdfebd64383b231de0252fe0726523d1c45aa2c4da919c2d7ed8bfb7aaa05c76`.
- Read-only scanning has validated one guest-count field for the supported
  build at `RCT.EXE base + 0x69c9f8` as a little-endian unsigned 16-bit value.
  Park rating is also validated at `RCT.EXE base + 0x69ce64` as a little-endian
  unsigned 16-bit value, and cash at `RCT.EXE base + 0x69c590` as a little-endian
  unsigned 32-bit value scaled by 10. Scenario and completion locators remain
  unvalidated.
- The recommended architecture remains an external read-only helper, not an
  injected DLL or binary patch.

**Next milestone:** review the [standalone proposal draft](docs/rct1_standalone_ra_proposal_draft.md)
and, if appropriate, seek initial RA guidance. Scenario/objective memory
discovery continues as a separate future workstream.

## Launching RCT1

The validated runtime uses Proton 10.0 with an isolated prefix under
`runtime-test/compatdata`. The canonical Steam game directory remains
untouched. The Steam-supplied installer must already have been run into the
isolated prefix; the launcher does not create, reinstall, download, or modify
the runtime or game files.

From the repository root, run:

```sh
./scripts/launch_rct1.sh
```

`runtime-test/` is intentionally excluded from Git because it contains the
local Proton/Wine prefix and installed game files. For the complete setup and
installation procedure, see the [Phase 2A launch report](reports/rct1_retroachievements_phase2a_launch.md).

## Project layout

```text
phase2/
├── README.md                    Phase 2 scope and findings
└── state_reader/
    ├── README.md                Reader notes
    ├── README_scanner.md        Scanner notes and usage
    ├── rct1_state_reader.c      Conservative process-state reader
    ├── rct1_state_scanner.c     Read-only memory scanner
    └── rct1_value_scan.c        Targeted value-scan utility

reports/
├── rct1_retroachievements_feasibility.md
├── rct1_retroachievements_phase2_runtime.md
├── rct1_retroachievements_phase2a_launch.md
├── rct1_retroachievements_phase2b_state_discovery.md
├── rct1_retroachievements_phase2c_guest_count.md
├── rct1_retroachievements_phase2d_park_rating.md
├── rct1_retroachievements_phase2e_cash_discovery.md
└── rct1_retroachievements_phase2f_cash_validation.md
```

The local `runtime-test/` directory is intentionally excluded from Git. It
contains Proton/Wine prefixes, installed game files, logs, and other machine-
specific runtime state.

## Reproducing the reader locally

From `phase2/state_reader/`:

```sh
cc -O2 -Wall -Wextra -o rct1_state_reader rct1_state_reader.c
./rct1_state_reader
```

The tools are diagnostic and read-only. They locate the running `RCT.EXE`
process and inspect mapped memory, but do not write process memory, patch the
game, inject a DLL, or send achievement/network requests.

The exact launch environment and successful Forest Frontiers procedure are
documented in
[`rct1_retroachievements_phase2a_launch.md`](reports/rct1_retroachievements_phase2a_launch.md).

## Research principles

- Prefer reproducible observations over assumptions from static strings or
  one-off memory hits.
- Validate candidate locators across fresh launches, scenario transitions,
  saves, and controlled gameplay changes.
- Keep the canonical game installation untouched; use an isolated runtime for
  experiments.
- Identify the supported executable by hash and reject unknown builds by
  default.
- Keep copyrighted game files, saves, and compatibility prefixes out of this
  repository.

## Scope and limitations

This repository contains research notes and original diagnostic source code. It
does not redistribute `RCT.EXE`, game data, scenarios, save files, DLLs, or
other copyrighted game assets. A legitimate local copy and a compatible runtime
may be required to reproduce the experiments.

RetroAchievements integration, achievement definitions, authentication, and
unlock writes remain intentionally disabled. Local rcheevos feasibility is
documented in the isolated `ra_spike/`; official standalone identity,
approval, Hardcore policy, and complete RCT state coverage are unresolved.

## Roadmap

1. Review the technical feasibility/proposal package and unresolved RA questions.
2. If guidance supports continuing, identify scenario and success/failure state
   transitions with the existing read-only tools.
3. Model ride objects well enough to evaluate coaster excitement.
4. Extend the versioned external state evaluator with executable, scenario, and
   save identity checks.
5. Keep production RA communication disabled until identity and policy guidance
   is received.

## Reports

Start with the [feasibility report](reports/rct1_retroachievements_feasibility.md)
for the target-build analysis, then read the [launch report](reports/rct1_retroachievements_phase2a_launch.md)
and [state-discovery report](reports/rct1_retroachievements_phase2b_state_discovery.md)
for the current runtime evidence. The validated guest-count and park-rating
findings are documented in the [Phase 2C report](reports/rct1_retroachievements_phase2c_guest_count.md)
and [Phase 2D report](reports/rct1_retroachievements_phase2d_park_rating.md).
The cash exact-scan negative result and changed-value validation are documented
in the [Phase 2E report](reports/rct1_retroachievements_phase2e_cash_discovery.md)
and [Phase 2F report](reports/rct1_retroachievements_phase2f_cash_validation.md).
