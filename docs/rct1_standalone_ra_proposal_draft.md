# DRAFT — NOT SUBMITTED

# RCT1 Standalone RetroAchievements Integration
## Technical Feasibility / Proposal Package

**Repository HEAD reviewed:** `94852ae Harden RCT identity and evaluator fixtures`

**Date:** 2026-09-27

**Target:** the original Windows RollerCoaster Tycoon Deluxe `RCT.EXE` build
launched through the repository's isolated Proton 10.0 runtime.

This is a technical proposal draft for review. It has not been submitted to
RetroAchievements, and this project has not contacted RetroAchievements
administrators, authenticated to production services, loaded a production RA
game, or submitted an achievement unlock.

## Evidence vocabulary

- **PROVEN** — supported by a reproducible repository test or field-validation
  report.
- **OBSERVED** — recorded during an experiment but not sufficient by itself for
  a general compatibility claim.
- **PROPOSED** — an architectural or policy design for future review.
- **OPEN QUESTION** — unresolved by repository evidence and current public
  documentation.
- **RA REQUIREMENT** — stated by current official RetroAchievements policy or
  integration documentation.

## 1. Executive summary

This project investigates whether the original Windows RCT1 Deluxe executable
can support a legitimate RetroAchievements standalone integration without
modifying the game. The current target is a 32-bit `RCT.EXE` build distributed
through the local Steam/Proton installation and executed in an isolated test
prefix. The repository records the supported executable's SHA-256 as
`bdfebd64383b231de0252fe0726523d1c45aa2c4da919c2d7ed8bfb7aaa05c76`.

An external helper was selected because the target is a protected, old Windows
executable with no established supported emulator/core memory map. The helper
can validate the executable, discover the live process and module base, read
memory with Linux `process_vm_readv`, and keep the Tkinter research GUI and any
future RA adapter outside the game process. The design intentionally avoids
DLL injection, binary patching, executable replacement, game-file changes, and
memory writes.

**PROVEN locally:** the repository has a pinned official rcheevos `rc_client`
lifecycle spike, a fail-closed supported-build check, a read-only provider, a
coherent multi-field snapshot, deterministic fixtures, and a test-only local
rcheevos condition that triggers against a live RCT snapshot. The current
spike has no network implementation and no credentials.

**UNRESOLVED:** official RA identity/hash and platform assignment, standalone
approval, Hardcore enforcement, save/scenario policy, complete achievement
state coverage, and the production session/Connect API contract for this
particular external helper.

**Recommendation:** the proof of concept is mature enough for an initial,
non-binding discussion with RA administrators about eligibility, identity, and
required integrity controls. It is not mature enough for production networking,
unlock submission, or a claim of Hardcore compliance.

## 2. Target game and eligibility

### Target identity

Repository evidence identifies the target as the original Windows Deluxe
`RCT.EXE`, a 32-bit PE executable from the original-style Infogrames release.
The feasibility report records a 2003-03-12 PE timestamp and the supported
SHA-256 above. The isolated launch report documents the Steam-supplied installer
running under Proton 10.0 in a separate prefix and loading the Forest Frontiers
scenario. The canonical Steam installation is not modified by the research
launcher.

The local SHA-256 is a **compatibility/integrity identity for this project**.
It is not an RA game hash, RA game ID, or evidence that RA already supports this
binary.

### Age and update eligibility

**OBSERVED:** the target executable carries a 2003 PE timestamp and is plainly
an old release in the repository's installation evidence. That makes the
official standalone age threshold appear technically plausible.

**OPEN QUESTION — requires RA clarification:** the public standalone guidance
also discusses non-bugfix updates during the preceding five years and other
eligibility details. This repository does not establish the publisher's formal
final-update status or make an eligibility determination on RA's behalf.

**RA REQUIREMENT:** official standalone support requires the game to meet the
published age/update criteria, requires an appropriate proposer/set-development
arrangement, requires enforceable Hardcore restrictions, and requires admin
approval. Meeting the criteria does not guarantee acceptance.

Sources: [Standalone Support](https://docs.retroachievements.org/general/standalone-support.html),
[Game Info and Hub Guidelines](https://docs.retroachievements.org/guidelines/content/game-info-and-hub-guidelines.html).

## 3. Why standalone and why an external helper

The target is not being approached as a conventional ROM/emulator integration:

```text
original RCT.EXE under Proton/Wine
            |
            v
external read-only provider
  /proc + validated hash + process_vm_readv
            |
            v
coherent normalized RCTState
            |
            v
future RA adapter / rcheevos
```

The existing GUI is a developer research tool, not a player client. Keeping the
provider and future adapter external provides a clear safety boundary and avoids
making the research GUI an implicit unlock client.

**PROPOSED benefits:**

- no binary patching or DLL injection;
- no replacement executable or modified canonical installation;
- no process-memory write path;
- a single place to reject unsupported executable identities;
- a typed snapshot boundary that can be tested without RCT;
- a future adapter that does not need to know `/proc` or Proton details.

**OPEN QUESTION:** whether RA would accept an external helper as the supported
standalone integration mechanism, and what distribution and trust model would
be required.

## 4. Current proof of concept

The isolated implementation is under [`ra_spike/`](../ra_spike/). It consumes
official rcheevos pinned as submodule `v12.1.0`, commit
`6755915f2bdf6c11c83b3e0e68c4623a39c0dabe`.

| Capability | Status | Evidence |
|---|---|---|
| `rc_client_create` / callbacks / destroy | **PROVEN** | `ra_spike/Makefile`, `make test` |
| Dynamic `RCT.EXE` PID discovery | **PROVEN** | `rct_memory_provider.c`, live spike run |
| Dynamic module-base discovery | **PROVEN** | `/proc/<pid>/maps`, live base `0x400000` |
| Proton/Wine map paths with spaces | **PROVEN** | fixed full-line map matching; live PID `68694` |
| Supported-build SHA-256 gate | **PROVEN** | fixture/live provider code and `make test` |
| Read-only process access | **PROVEN** | only `process_vm_readv` is used |
| Coherent three-field snapshot | **PROVEN** | one multi-iovec read; incomplete reads rejected |
| Local rcheevos condition evaluation | **PROVEN** | `--local-eval`, live test-only trigger |
| Production RA game loading | **NOT DONE** | no RA game ID/hash or server call |
| Production authentication/session | **NOT DONE** | no credentials and no HTTP implementation |
| Unlocks, leaderboards, Rich Presence | **NOT DONE** | intentionally disabled |
| Hardcore compliance | **NOT ESTABLISHED** | current spike explicitly disables Hardcore |

### Validated state fields

The following are **PROVEN for the supported executable build only**, with
Medium confidence in the historical field reports:

| Field | RCT-provider locator | Representation | Evidence |
|---|---|---|---|
| Cash | `current_module_base + 0x69c590` | little-endian `u32`; displayed dollars = raw / 10 | Phase 2F controlled decreases and fresh launch |
| Guest Count | `current_module_base + 0x69c9f8` | little-endian `u16` | Phase 2C controlled values and restart |
| Park Rating | `current_module_base + 0x69ce64` | little-endian `u16` | Phase 2D controlled values and restart |

These are module-relative **RCT-provider locators**, not official RA memory
addresses. They are backed by anonymous runtime state, not established file
RVAs or universal structures. Unknown executable hashes are rejected before
reads.

### Test boundaries

The fixture test proves that a complete synthetic snapshot can trigger a
test-only local condition and that a missing field is rejected. The live local
evaluator maps synthetic experiment addresses into rcheevos and explicitly
starts the test trigger active. It does not call `rc_client_begin_load_game`,
does not authenticate, and does not send an unlock.

Therefore the correct claim is **local evaluator feasibility demonstrated**, not
**production RA integration validated**.

## 5. Proposed player architecture

The following is **PROPOSED**, not implemented:

```text
RCT.EXE
  |
  +--> executable/path/hash validation
  |
  +--> read-only MemoryProvider
             |
             v
        coherent RCTState
             |
             v
        RA adapter / address translation
             |
             v
           rc_client
          /    |     \
      login  game load  definitions/evaluation
                         |
                         v
                       RA events
```

Expected process lifecycle:

1. The game starts under the supported runtime.
2. The helper discovers the process and mapped executable.
3. The helper verifies the local supported-build identity.
4. The provider attaches read-only and captures coherent snapshots.
5. A future approved adapter authenticates a player and loads an approved RA
   game/session identity.
6. rcheevos evaluates definitions against the adapter's logical memory/state.
7. Events are surfaced to the player and, only in an approved production
   design, transmitted through the accepted RA path.
8. Process exit, executable replacement, module change, identity failure, or
   provider disconnect invalidates the session and disables evaluation.

The player-facing client would need a visible achievement list, mode state,
session status, failure reason, and safe logout/shutdown behavior. None of that
is claimed by the current Tkinter research GUI.

## 6. Game identity and hash model

### A. Local compatibility identity

The local SHA-256 answers:

> “Do we recognize this exact executable as one whose observed runtime layout
> we are willing to read?”

It is an allowlist, not a server identity. It must remain local and fail closed.

### B. RetroAchievements identity

An RA identity answers a different question:

> “Which RA game/page and approved content definition does this running game
> correspond to?”

The official rcheevos guide describes `rc_client_begin_identify_and_load_game`
for a console/file or buffer hash path, and `rc_client_begin_load_game` for an
already-known hash. The current v12.1.0 header exposes both APIs, with the
identify-and-hash API conditional on `RC_CLIENT_SUPPORTS_HASH`. The guide says
the client hashes/identifies the game, resolves it to a game ID, fetches data,
and starts a session; the host supplies HTTP and memory callbacks.

The public game-identification documentation is console-specific. It does not
establish a Windows RCT1 hashing method or a console assignment for this
external process. The standalone Connect documentation says standalone game
pages and primary game IDs are set up by the RA administration and are required
for session calls.

**OPEN QUESTION — RA clarification required:**

1. What console/platform identity should this RCT standalone use?
2. Would RA establish a Standalones game page and primary game ID?
3. Should the integration use `rc_client_begin_load_game` with an approved RA
   hash, a custom standalone Connect API game ID, or another approved path?
4. What exact bytes/files or custom identity procedure should be hashed?
5. Can multiple legitimate RCT builds map to one RA game page, and would each
   require separate version-specific state maps?
6. Can a local executable allowlist coexist with multiple RA-approved hashes?

No game ID, console ID, RA hash, or server entry is invented here.

Sources: [Game Identification](https://docs.retroachievements.org/developer-docs/game-identification.html),
[rcheevos `rc_client` integration](https://github.com/RetroAchievements/rcheevos/wiki/rc_client-integration),
[rcheevos README/API overview](https://github.com/RetroAchievements/rcheevos/blob/develop/README.md),
[Standalone Connect API](https://api-docs.retroachievements.org/connect/standalone.html).

## 7. Authentication and session model

The pinned v12.1.0 API exposes:

- `rc_client_begin_login_with_password(client, username, password, callback, userdata)`;
- `rc_client_begin_login_with_token(client, username, token, callback, userdata)`;
- `rc_client_get_user_info(client)`;
- `rc_client_logout(client)`;
- asynchronous callbacks carrying result/error state;
- a host-supplied `rc_client_server_call_t` responsible for HTTP behavior.

The official integration guide says the host must provide networking and must
use a unique versioned User-Agent. It also recommends replacing password use
with a stored token after initial login. The standalone Connect guide describes
a separate integration account, Web API key, Connect token, and player-linking
flow; it explicitly treats those tokens as secrets.

**PROPOSED future behavior:** credentials would be supplied outside the repo,
stored in an OS-appropriate secret store, never logged, and cleared/invalidated
on logout. A failed or missing credential would leave the helper in local,
non-networked mode. Client shutdown would unload the game, logout if the
approved session model requires it, abort outstanding async work, and destroy
`rc_client`.

**NOT DONE:** no login API has been called, no server callback performs HTTP,
and no credential/token exists in this repository.

Sources: [rcheevos integration — Login](https://github.com/RetroAchievements/rcheevos/wiki/rc_client-integration#login),
[Standalone Connect API](https://api-docs.retroachievements.org/connect/standalone.html).

## 8. Achievement evaluation

### Current local path

```text
coherent RCT snapshot
        |
        v
test-only synthetic rcheevos memory addresses
        |
        v
direct rc_runtime condition
        |
        v
local trigger event
```

This path is **PROVEN locally** for one test condition requiring nonzero Guests
and Park Rating. It is deliberately direct `rc_runtime` experimentation, not a
production loaded RA game.

### Eventual approved path

```text
approved RA definitions
        -> rcheevos / rc_client
        -> RCT memory/state adapter
        -> evaluation each game frame/tick
        -> event handler
        -> approved session/unlock path
```

The rcheevos guide requires the host to call `rc_client_do_frame` for every
emulated frame and `rc_client_idle` when paused rather than silently stopping
processing. For RCT, the equivalent cadence and pause semantics require RA
review because this is not a conventional emulator frame loop.

**PROVEN:** local condition evaluation.

**NOT PROVEN / intentionally not attempted:** official definitions, game load,
server session, unlock submission, leaderboard submission, Rich Presence, or
Hardcore eligibility.

## 9. RCTState and memory model

The current provider reads physical process locations using RCT-relative
locators. rcheevos expects a host read callback over a logical 32-bit address
space. Two designs are possible:

### A. Direct translated RCT addresses

The adapter would map each RA logical address to a validated RCT module-relative
locator and read the current process. This is close to conventional emulator
memory semantics, but it exposes version-specific layout assumptions and makes
raw pointers, invalid ranges, and mixed snapshots easier to mishandle.

### B. Normalized coherent RCTState space

The provider would capture a typed `RCTState`, and the adapter would expose a
small versioned logical view containing only validated fields. The current local
evaluator already demonstrates the shape of this approach with synthetic
addresses.

**PROPOSED direction:** use normalized coherent state as the public boundary,
while keeping a private version-specific decoder for raw RCT offsets. This
better isolates build differences, supports deterministic fixtures, makes
provenance/confidence visible, and avoids making achievement definitions depend
on anonymous pointers. It does not solve identity or policy, and the final RA
address semantics require review.

**OPEN QUESTION:** whether RA developers would prefer standard logical memory
definitions over a custom normalized adapter for a standalone title. Do not
freeze a final address contract before that discussion.

## 10. Hardcore and integrity threat model

The table separates what this research currently enforces from what a future
player client might technically attempt and what RA must decide. The current
research GUI is never a Hardcore-safe player client.

| Threat / condition | Current state | Possible mitigation | RA requirement / question |
|---|---|---|---|
| Modified/unknown `RCT.EXE` | Supported SHA-256 gate fails closed | Signed/immutable manifest; recheck identity | **CURRENTLY ENFORCED** locally; RA acceptance TBD |
| Executable replaced after startup | Not continuously revalidated | Recheck mapped file/inode/hash and PID | **PROPOSED**; required policy TBD |
| Unsupported build/layout | Rejected before reads | Versioned provider manifests | **CURRENTLY ENFORCED** for known build only |
| RCT process restart | One-shot provider detects current PID | Invalidate state/session and require fresh attach | **PROPOSED** |
| Helper/client restart | No production client exists | Drop session and require new validated start | **PROPOSED** |
| Provider disconnect/read failure | Snapshot rejects incomplete reads | Disable evaluation and report reason | **PROPOSED** |
| `process_vm_writev` by this helper | No write API exists | Maintain build/test prohibition | **CURRENTLY ENFORCED** |
| Another process writes memory | Not detectable by current reader | OS policy, anti-tamper signals, conservative Hardcore disable | **REQUIRES RA POLICY DECISION** |
| Cheat Engine/memory editor | Not detected | Detect known tools only if RA accepts; cannot prove absence generally | **OPEN QUESTION — RA clarification** |
| Generic trainer | Not detected | Policy/allowlist or Hardcore disqualification | **REQUIRES RA POLICY DECISION** |
| DLL injection/binary patch | Not detected | Module/integrity checks; tooling policy | **POSSIBLY UNENFORCEABLE** externally |
| RCT mods/altered data files | Not validated | Hash/data manifest and conservative mode downgrade | **REQUIRES RA POLICY DECISION** |
| Modified scenario files | Not validated | Scenario checksum/identity manifest | **OPEN QUESTION** |
| Modified save files | Not validated | Save provenance impossible to prove from current fields | **POSSIBLY UNENFORCEABLE** |
| Arbitrary save loading | No player mode exists | Reset/flag rules or Casual-only handling | **RA REQUIREMENT / policy clarification** |
| Save scumming | Not detected | Define whether permitted per set/policy | **OPEN QUESTION** |
| Pause | Provider can sample while paused | Use `rc_client_idle`; define pause-safe conditions | **PROPOSED**, RA review needed |
| Speed changes/frame advance | No player controls in helper | Prohibit/disable in Hardcore; detect where possible | **RA REQUIREMENT** |
| OS clock changes | Not relevant to current fields | Avoid wall-clock trust; use game state/ticks | **REQUIRES MORE RESEARCH** |
| Proton/Wine behavior | One supported runtime observed | Pin/test supported runtime; reject unknown environments if needed | **OPEN QUESTION** |
| Debugger attachment | Not detected | Detect ptrace/debugger where reliable; otherwise disqualify | **RA REQUIREMENT / clarification** |
| External automation/macros | Not detected | No input automation in helper; policy cannot be proven fully | **POSSIBLY UNENFORCEABLE** |
| Achievement helper tampering | No player helper exists | Signed distribution, integrity checks, server validation | **REQUIRES RA POLICY DECISION** |

**Important limitation:** an executable hash proves only that the mapped file
matches the local allowlist at the time checked. It does not prove that another
process has not modified memory, that a save is legitimate, or that no debugger
or trainer is present. The current project must not claim Hardcore compliance.

**RA REQUIREMENT:** official Hardcore documentation requires disabling cheats,
rewind, slowdown, frame advance, and save-state loading; it also requires a
unique versioned User-Agent and addresses memory editors/debuggers/TAS tooling.
The standalone page additionally requires enforceable Hardcore restrictions.

Sources: [Hardcore Compliance Requirements](https://docs.retroachievements.org/general/hardcore-compliance-requirements.html),
[Global Leaderboard and Achievement Hunting Rules](https://docs.retroachievements.org/guidelines/users/global-leaderboard-and-achievement-hunting-rules.html).

## 11. Save and scenario policy

RCT scenarios and saved parks are central to the game. The repository has
validated fields for current economy/population/rating state but has not
validated runtime scenario identity, objective type, target, deadline,
success/failure, or save provenance.

### Technical possibilities

- hash and whitelist canonical scenario files;
- identify scenario/objective state in memory;
- record a session-start state and invalidate on arbitrary save loading;
- expose scenario identity and completion through a future normalized `RCTState`;
- require fresh scenario starts for specific set logic;
- keep achievements that cannot establish provenance in Casual/local mode.

### Policy questions

**OPEN QUESTION — RA clarification required:** whether a standalone RCT set may
allow arbitrary saved parks, whether scenario-start provenance is expected, how
save scumming should be treated, and whether individual achievements may define
different save/reset restrictions.

No save or scenario restriction is currently claimed or enforced.

## 12. Conceptual set plan

This is **PROPOSED research scope only**, not an approved or final achievement
set. It identifies state domains that a legitimate set would likely need:

| Conceptual category | Example state needed | Current status |
|---|---|---|
| Scenario completion | scenario identity, objective, deadline, success flag | Not located |
| Guest milestones | current guests, possibly sustained/peak count | Guest count validated |
| Park rating | current rating and duration/threshold semantics | Park rating validated |
| Finance | cash, loan, admission, park/company value | Cash validated; others open |
| Rides | count, type, operating state, ratings, construction completion | Open |
| Scenario restrictions | required ride/theme/guest/objective conditions | Open |
| Calendar/simulation | day/month/year/tick, pause/simulation state | Open |
| Staff/research | staff counts, research status, unlocks | Open |
| Park identity | park name and scenario/save provenance | Open |

Potential categories include completing scenarios, reaching guest/rating
milestones, financial challenges, ride construction/operation challenges, and
scenario-specific restrictions. No IDs, titles, conditions, or unlock behavior
are being created in this task.

## 13. Memory research still required

Broad discovery is intentionally paused for this proposal. The retained future
targets are:

- **Park/economy:** loan amount, park open/closed, admission price, park value,
  company value.
- **Calendar/simulation:** tick, day, month, year, pause/simulation state.
- **Ride state:** ride count, ride records, ride type, operating state, ratings,
  construction/completion.
- **Scenario state:** scenario identity, objective type/target/deadline,
  completion and failure.
- **Other:** staff, research state, park name.

These matter because future conditions must be semantic and reproducible rather
than based only on three convenient fields. Scenario/objective state is also
central to save provenance and Hardcore eligibility. Each future locator needs
fresh-process, build-scoped, scenario/save-aware evidence.

## 14. Approval and dependency matrix

| Item | We can solve locally? | Requires RA/admin input? | Status |
|---|---:|---:|---|
| RCT process discovery | Yes | No | Proven |
| Supported-build identity | Yes | No | Proven for one hash |
| Read-only provider | Yes | No | Proven prototype |
| Coherent snapshots | Yes | No | Proven prototype |
| Local evaluation | Yes | No | Proven test-only |
| RCT semantic state coverage | Partly | No | Incomplete |
| RA console/platform assignment | No | Yes | Open |
| RA game ID/page | No | Yes | Open |
| Official hash strategy | Partly | Yes | Open |
| Standalone approval | No | Yes | Not requested |
| Account authentication | Technically | Yes for approved path | Not implemented |
| Achievement set/IDs | No | Set developer/RA process | Not created |
| Hardcore policy | Partly | Yes | Not compliant/untested |
| Unlock submission | Technically later | Yes/approved credentials | Not attempted |
| Rich Presence | Technically later | Approval/definitions | Not attempted |
| Leaderboards | Technically later | Approval/definitions | Not attempted |

## 15. Gap analysis

### Blocker before contacting RA

There is no technical blocker to asking for initial guidance. There are,
however, blockers to production implementation: no RA identity, no approved
standalone page, no Hardcore design, no save/scenario policy, and incomplete
state coverage.

### Useful before contacting RA

- keep the proposal and evidence terminology precise;
- preserve the deterministic fixture and fail-closed identity tests;
- add scenario/objective and save-provenance evidence only as a separate,
  read-only workstream if needed;
- prepare a conceptual set plan and threat model;
- identify a potential RA developer/set-design partner if required by policy.

### Can wait until after RA guidance

- choosing the final RA hash/console/game identity;
- implementing production HTTP and credential storage;
- player UI, achievement list, placard, Rich Presence, and leaderboard UX;
- final Hardcore enforcement and distribution model;
- production unlock testing.

### Long-term implementation

- versioned RCTState decoders for approved builds;
- scenario/save policy enforcement;
- signed or otherwise trusted distribution;
- approved online session/unlock adapter;
- complete set development and regression testing.

## 16. Questions for RAdmin

These are deliberately limited to questions not answered by the current public
documentation:

1. Is the original Windows RCT Deluxe executable an eligible standalone target,
   and which RA platform/console identity should represent it?
2. Would RA create a Standalones game page and primary game ID for this project?
3. What identity/hash input should an external helper use for a Windows PE game
   whose runtime state is read from a separate process?
4. Can several approved RCT executable builds map to one game page, and how
   should build-specific memory maps be represented or reviewed?
5. Is a normalized logical RCTState adapter acceptable, or must the integration
   expose a conventional RA memory address space?
6. What exact Hardcore restrictions are expected for external trainers,
   debuggers, memory editors, DLL injection, Proton/Wine, and arbitrary saves?
7. Should arbitrary saved parks be allowed in Hardcore, and what scenario-start
   or save-provenance evidence is expected?
8. What is the approved development/test-server workflow before any production
   session or unlock call is made?
9. What distribution, User-Agent, privacy, and support requirements apply to a
   small external helper rather than a conventional emulator?
10. Is an RA Developer/set-design partner required before a formal proposal can
    proceed under the current standalone process?

## 17. Proposed next phase

**Recommendation B — the proof of concept is mature enough for an initial RA
discussion, but not for production integration.**

The recommendation is based on repository evidence: a supported-build gate,
read-only provider, coherent snapshots, rcheevos lifecycle, deterministic
fixtures, and a live local condition event. The remaining uncertainty is now
primarily RA-specific identity, policy, and approval—not whether a read-only
external prototype can technically observe and evaluate a small amount of RCT
state.

An eventual outreach package should include this draft, the concise proof
summary, the executable/build identity distinction, the threat model, the
conceptual set plan, and the questions above. It should explicitly say that no
production communication or unlock submission has occurred and should request
guidance rather than imply entitlement to a game page or Hardcore status.

## Sources consulted

- [RetroAchievements Standalone Support](https://docs.retroachievements.org/general/standalone-support.html)
- [Hardcore Compliance Requirements](https://docs.retroachievements.org/general/hardcore-compliance-requirements.html)
- [Global Leaderboard and Achievement Hunting Rules](https://docs.retroachievements.org/guidelines/users/global-leaderboard-and-achievement-hunting-rules.html)
- [Game Identification Methods by Console](https://docs.retroachievements.org/developer-docs/game-identification.html)
- [Standalone Connect API](https://api-docs.retroachievements.org/connect/standalone.html)
- [rcheevos `rc_client` integration guide](https://github.com/RetroAchievements/rcheevos/wiki/rc_client-integration)
- [rcheevos README/API overview](https://github.com/RetroAchievements/rcheevos/blob/develop/README.md)
- Repository evidence: [`reports/rct1_retroachievements_integration_spike.md`](../reports/rct1_retroachievements_integration_spike.md),
  field-validation reports, [`docs/reference_architectures.md`](reference_architectures.md),
  and the pinned `ra_spike/deps/rcheevos` submodule.
