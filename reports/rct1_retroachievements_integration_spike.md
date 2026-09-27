# RCT1 RetroAchievements integration spike

## Scope

This report records an isolated architecture experiment. It does not change
the Tkinter GUI, submit unlocks, authenticate, or claim standalone
RetroAchievements support.

## OBSERVATION — pinned client lifecycle validated

The repository now contains an official rcheevos submodule pinned to
`v12.1.0`, commit `6755915f2bdf6c11c83b3e0e68c4623a39c0dabe`. The `ra_spike`
executable successfully:

- creates `rc_client_t`;
- installs read-memory, server, logging, and event callbacks;
- disables Hardcore and background reads for the experiment;
- processes three frames and an idle tick; and
- destroys the client cleanly.

The smoke test passes without RCT, credentials, achievement data, or network
traffic. The server callback rejects requests instead of attempting a network
operation.

## OBSERVATION — read-only RCT bridge added

`--rct-state` discovers `RCT.EXE` by `/proc` name, derives the current
file-backed module base from `/proc/<pid>/maps`, and reads the previously
validated Guest, Park Rating, and Cash fields with `process_vm_readv` only.
The bridge returns a safe error if RCT is absent or the expected module mapping
cannot be found. It does not write process memory or inject code.

The live Proton/Wine test exposed a path-parsing defect: executable map paths
contain spaces under `Program Files (x86)`. Matching now uses the complete
`/proc/<pid>/maps` line rather than a whitespace-truncated path token. The
corrected bridge found PID `68694`, derived base `0x400000`, read all three
fields, and initialized `rc_client` with the provider while networking remained
disabled.

## OBSERVATION — coherent state snapshot validated

The provider now reads Guests, Park Rating, and Cash with one multi-iovec
`process_vm_readv` operation. It reports the snapshot as valid only when the
complete byte total is returned; otherwise it rejects the snapshot rather than
combining fields sampled at different times. A live test produced
`snapshot_coherent=1` with Guests `4`, Park Rating `500`, and Cash raw `97295`.

## OBSERVATION — local evaluator proof completed

`--local-eval` feeds the coherent snapshot into a direct local rcheevos runtime
with synthetic experiment-only addresses. A test condition requiring Guests and
Park Rating to be nonzero produced a local achievement-trigger event. The
runtime is explicitly initialized as an active loaded-game experiment; this is
not a claim that official game loading has been solved. No `rc_client` game
load, network request, account session, or unlock submission occurs.

## OBSERVATION — deterministic fixtures and identity gate added

The spike now has an offline `--fixture-test` path exercised by `make test`.
It verifies that a complete synthetic snapshot triggers the local condition and
that a snapshot missing Guests is rejected. The live provider also hashes the
mapped executable before reading memory and accepts only the supported
`RCT.EXE` SHA-256:

`bdfebd64383b231de0252fe0726523d1c45aa2c4da919c2d7ed8bfb7aaa05c76`

An unknown or modified executable fails closed.

The bridge currently uses these repository-validated offsets for the supported
build:

| Field | Type | Module-relative offset |
|---|---:|---:|
| Guests | u16 | `0x69c9f8` |
| Park Rating | u16 | `0x69ce64` |
| Cash raw value | u32 | `0x69c590` |

These are an RCT provider convention, not an official RA memory map. A future
`rc_client` integration must define an explicit translation layer rather than
silently presenting these offsets as canonical RA addresses.

## HYPOTHESIS — local evaluation can precede online integration

The cleanest next experiment is to feed a coherent, read-only RCT snapshot to
local rcheevos evaluation while keeping server calls disabled. This would test
memory semantics and lifecycle integration without creating online account or
unlock side effects.

## OPEN QUESTION — game identity and session contract

No RetroAchievements game ID is invented here. Official game identification,
hash/load behavior, account session handling, User-Agent requirements, and the
eligibility of this non-emulator executable remain unresolved. Credentials must
stay external to the repository and absent by default.

## OBSERVATION — official identity path remains unresolved

Official rcheevos uses a console-specific `rhash` pipeline and an RA-supported
game/hash entry. The provider's local SHA-256 allowlist is only an integrity
gate for this executable; it is not an RA hash and does not prove that the
executable is known to RA. No RA console ID, game ID, or approved hash entry
has been established for this external RCT process.

Official standalone guidance also requires administrative approval and strict
Hardcore enforcement. Therefore the next online-facing step is an identity and
proposal investigation, not credential handling or server calls. See the
[official game identification documentation](https://docs.retroachievements.org/developer-docs/game-identification.html),
[rcheevos API overview](https://github.com/RetroAchievements/rcheevos/blob/develop/README.md),
and [standalone support requirements](https://docs.retroachievements.org/general/standalone-support.html).

## CURRENTLY ENFORCED

- No network implementation or server requests.
- No credentials stored, read, or required.
- Hardcore disabled in the lifecycle spike.
- No achievement unlock or leaderboard submission.
- Read-only `process_vm_readv`; no process-memory write API.
- GUI remains separate from the RA experiment.
- No broad memory discovery work in this spike.

## POSSIBLE FUTURE CONTROL

A future online mode would need explicit game identity, integrity validation,
coherent snapshots, strict unsupported-state handling, and a separately reviewed
policy/compliance plan. It should default to local/spectator behavior until
those controls are proven.

## RA POLICY REQUIREMENT

RetroAchievements documents standalone support as an approval-based process and
requires Hardcore restrictions for supported standalone integrations. This
spike is not a submission and does not assert compliance. Consult the official
[standalone support requirements](https://docs.retroachievements.org/general/standalone-support.html),
[Hardcore compliance requirements](https://docs.retroachievements.org/general/hardcore-compliance-requirements.html),
and [rc_client integration guide](https://github.com/RetroAchievements/rcheevos/wiki/rc_client-integration)
before any online or production-facing work.
