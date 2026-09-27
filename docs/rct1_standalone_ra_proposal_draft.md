# DRAFT — NOT SUBMITTED

# RCT1 Standalone RetroAchievements Integration
## Technical Feasibility / Proposal Package

**Repository HEAD reviewed:** `8e3a4f0 Add standalone RA proposal draft`

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

**UNRESOLVED:** the official production architecture (documented Standalones /
Connect API, `rc_client`/rcheevos, a hybrid, or another approved model), RA
game/build identity, standalone approval, Hardcore enforcement, save/scenario
policy, complete achievement state coverage, and the production session
contract for this particular external helper.

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

## 5. Proposed player architecture and unresolved RA model

The local portion is **PROPOSED and partially demonstrated**:

```text
RCT.EXE
  |
  +--> executable/path/local-build validation
  |
  +--> read-only MemoryProvider
             |
             v
        coherent normalized RCTState
             |
             +-----------------------------+
             |                             |
             v                             v
   future rc_client adapter       future Standalones adapter
   (if RA approves this path)     (if RA approves Connect API)
             |                             |
             v                             v
   player login + game load       integration account + player link
   definitions + evaluation       session + local detection/evaluation
             |                             |
             +-------------+---------------+
                           v
                  approved RA events/unlocks
```

The production choice between these branches is **OPEN QUESTION — RA
clarification required**. The current local `rc_client` lifecycle and direct
`rc_runtime` condition experiment prove that rcheevos can be embedded and fed
normalized state; they do not establish that `rc_client` is the required
standalone production protocol. Conversely, the documented Standalones /
Connect API describes a separate integration-account, game-page, player-link,
session, and award model; its documentation does not establish that it is the
only acceptable architecture for this project.

This choice materially affects authentication, game identity, player linking,
definition retrieval, evaluation ownership, session lifecycle, unlock
submission, and host responsibilities. It is not merely a choice of HTTP
library.

Expected process lifecycle for either approved model:

1. The game starts under the supported runtime.
2. The helper discovers the process and mapped executable.
3. The helper verifies the local supported-build identity.
4. The provider attaches read-only and captures coherent snapshots.
5. The approved RA model supplies the official game/session identity and any
   required player authentication.
6. Evaluation runs against the approved logical state/memory boundary.
7. Events are surfaced and, only in an approved production design, submitted
   through the accepted RA path.
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

### B. Official RA game/build identity mechanism

An official RA identity answers a different question:

> “Which approved RA game/page/content and session does this running RCT
> installation represent?”

This should be treated as an **official RA game/build identity mechanism**, not
simply as “the RA hash.” The local SHA-256 and the official server identity may
be two independent layers.

The current rcheevos guide describes two relevant `rc_client` paths:

- `rc_client_begin_identify_and_load_game`, which identifies from a
  console/file or buffer hash path when hash support is compiled in; and
- `rc_client_begin_load_game`, which loads using an already-known hash.

The guide describes the host-provided HTTP callback, game identification,
resolution to a game ID, data loading, and session start. The v12.1.0 header
contains these APIs, with the identify-and-hash API conditional on
`RC_CLIENT_SUPPORTS_HASH`.

The current Standalones documentation describes a different public model:
administrators create Standalones game pages, the integration uses a primary
game ID, an integration account and Connect token, and a player is linked to
that integration before session calls. The documentation does not establish
that this is the only acceptable architecture for an external RCT helper, but
it does establish that a standalone page/game ID and approved server-side
setup are part of that model.

**OPEN QUESTION — RA clarification required:**

1. What official game/build identity mechanism should this RCT1 standalone use?
2. Should the integration follow the documented Standalones / Connect API
   model, `rc_client`/rcheevos, a hybrid, or another approved architecture?
3. What platform/console identity and primary game ID would represent it?
4. What exact bytes/files or custom identity procedure should be associated
   with the approved game/build identity?
5. Can multiple legitimate RCT builds map to one game page while retaining
   separate version-specific state decoders?
6. Can the local executable allowlist coexist with multiple RA-approved builds?

No game ID, console ID, RA hash, server entry, or Windows PE hashing scheme is
invented here.

Sources: [Game Identification](https://docs.retroachievements.org/developer-docs/game-identification.html),
[rcheevos `rc_client` integration](https://github.com/RetroAchievements/rcheevos/wiki/rc_client-integration),
[rcheevos README/API overview](https://github.com/RetroAchievements/rcheevos/blob/develop/README.md),
[Standalone Connect API](https://api-docs.retroachievements.org/connect/standalone.html).

## 7. Authentication and session model

Authentication is dependent on the architecture RA approves. The two
documented models are not interchangeable.

### A. `rc_client` / rcheevos model

The pinned v12.1.0 API exposes:

- `rc_client_begin_login_with_password(client, username, password, callback, userdata)`;
- `rc_client_begin_login_with_token(client, username, token, callback, userdata)`;
- `rc_client_get_user_info(client)`;
- `rc_client_logout(client)`;
- asynchronous callbacks carrying result/error state; and
- a host-supplied `rc_client_server_call_t` responsible for HTTP behavior.

The official integration guide describes a player login/token flow, recommends
using a remembered token after the initial password login, and expects the host
to provide networking, UI, persistence, and a unique versioned User-Agent.

### B. Standalones / Connect API model

The current Standalones guide describes an integration account, a Web API key,
a Connect API token, a Standalones game page/primary game ID, and a player-link
flow using a generated key in the player's account motto. It says OAuth2 is a
future direction and is not production-ready in that guide. The Connect token
and Web API key are secrets, not player credentials to commit or embed.

This model has different trust and identity boundaries: the integration account
represents the standalone integration, while the linked player account is the
person for whom a session and award are made. A Connect session uses the
approved primary game ID and linked username; it is not the same operation as
`rc_client` player login and game loading.

**PROPOSED future behavior for either model:** credentials would be supplied
outside the repo, stored in an OS-appropriate secret store, never logged, and
cleared/invalidated on logout. Missing credentials would leave the helper in
local, non-networked mode. Shutdown would invalidate the state/session and
perform the approved logout/unload behavior.

**NOT DONE:** no login API has been called, no Connect request has been made,
no server callback performs HTTP, and no credential/token exists in this
repository.

Choosing Connect versus `rc_client` is therefore not merely an HTTP-library
decision: it changes player authentication, integration identity, game loading,
definition retrieval, evaluation ownership, session handling, and unlock
submission.

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

### Eventual approved paths

```text
approved RA definitions
        -> approved local evaluator (possibly rcheevos / rc_client)
        -> RCT memory/state adapter
        -> evaluation each game frame/tick
        -> approved session/unlock path
```

If RA approves `rc_client`, the rcheevos guide requires the host to call
`rc_client_do_frame` for every emulated frame and `rc_client_idle` when paused
rather than silently stopping processing. If RA approves the Standalones /
Connect model, the host-side evaluator and session/award calls have a different
responsibility split. For RCT, the cadence, pause semantics, definition source,
and event/submission boundary require RA review because this is not a
conventional emulator frame loop.

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

The central unresolved question is:

> How much responsibility does RA expect an external RCT helper to assume for
> detecting or preventing cheating performed outside the helper itself?

The helper can reject an unknown executable and incomplete snapshot, but it
cannot currently prove the absence of another process writing memory, a
debugger, a trainer, injected code, altered saves, or external automation. It
would be misleading to treat process-name detection for a tool such as Cheat
Engine as adequate enforcement. No invasive anti-cheat is proposed here.

| Threat / condition | Current state | Possible mitigation | RA requirement / question |
|---|---|---|---|
| Modified/unknown `RCT.EXE` | Supported SHA-256 gate fails closed | Signed/immutable manifest; recheck identity | **CURRENTLY ENFORCED** locally; RA acceptance TBD |
| Executable replaced after startup | Not continuously revalidated | Recheck mapped file/inode/hash and PID | **PROPOSED**; required policy TBD |
| Unsupported build/layout | Rejected before reads | Versioned provider manifests | **CURRENTLY ENFORCED** for known build only |
| RCT process restart | One-shot provider detects current PID | Invalidate state/session and require fresh attach | **PROPOSED** |
| Helper/client restart | No production client exists | Drop session and require new validated start | **PROPOSED** |
| Provider disconnect/read failure | Snapshot rejects incomplete reads | Disable evaluation and report reason | **PROPOSED** |
| `process_vm_writev` by this helper | No write API exists | Maintain build/test prohibition | **CURRENTLY ENFORCED** |
| Another process writes memory | Not detectable by current reader | OS policy, conservative Hardcore disable, or an RA-approved trust model | **REQUIRES RA POLICY DECISION**; possibly not reliably enforceable |
| Cheat Engine/memory editor | Not detected | Detect known tools only if RA accepts; this cannot prove absence generally | **OPEN QUESTION — RA clarification**; possibly not reliably enforceable |
| Generic trainer | Not detected | Policy/allowlist or Hardcore disqualification | **REQUIRES RA POLICY DECISION** |
| DLL injection/binary patch | Not detected | Module/integrity checks; tooling policy | **POSSIBLY NOT RELIABLY ENFORCEABLE** externally |
| RCT mods/altered data files | Not validated | Hash/data manifest and conservative mode downgrade | **REQUIRES RA POLICY DECISION** |
| Modified scenario files | Not validated | Scenario checksum/identity manifest | **OPEN QUESTION** |
| Modified save files | Not validated | Save provenance impossible to prove from current fields | **POSSIBLY NOT RELIABLY ENFORCEABLE** |
| Arbitrary save loading | No player mode exists | Reset/flag rules or Casual-only handling | **RA REQUIREMENT / policy clarification** |
| Save scumming | Not detected | Define whether permitted per set/policy | **OPEN QUESTION** |
| Pause | Provider can sample while paused | Use `rc_client_idle`; define pause-safe conditions | **PROPOSED**, RA review needed |
| Speed changes/frame advance | No player controls in helper | Prohibit/disable in Hardcore; detect where possible | **RA REQUIREMENT** |
| OS clock changes | Not relevant to current fields | Avoid wall-clock trust; use game state/ticks | **REQUIRES MORE RESEARCH** |
| Proton/Wine behavior | One supported runtime observed | Pin/test supported runtime; reject unknown environments if needed | **OPEN QUESTION** |
| Debugger attachment | Not detected | Detect ptrace/debugger where reliable; otherwise disqualify | **RA REQUIREMENT / clarification** |
| External automation/macros | Not detected | No input automation in helper; policy cannot be proven fully | **POSSIBLY NOT RELIABLY ENFORCEABLE** |
| Achievement helper tampering | No player helper exists | Signed distribution, integrity checks, server validation | **REQUIRES RA POLICY DECISION** |

**Important limitation:** an executable hash proves only that the mapped file
matches the local allowlist at the time checked. It does not prove that another
process has not modified memory, that a save is legitimate, or that no debugger
or trainer is present. The current project must not claim Hardcore compliance.

**RA REQUIREMENT:** official Hardcore documentation requires disabling cheats,
rewind, slowdown, frame advance, and save-state loading; it also requires a
unique versioned User-Agent and addresses memory editors/debuggers/TAS tooling.
The standalone page additionally requires enforceable Hardcore restrictions.

The current Hardcore Compliance Requirements also state that an emulator, or
the parent emulator it is forked from, must have been publicly available for at
least six months before Hardcore compliance approval. The page scopes that
wording to emulator/parent-emulator approval. **OPEN QUESTION — RA clarification
required:** whether and how this public-availability period applies to a newly
developed external standalone helper such as this one. It may be relevant to a
future compliance timeline, but it is not claimed here as a blocker to an
initial prototype discussion or standalone proposal.

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
| Production architecture choice (`rc_client`, Connect, hybrid, other) | No | Yes | Open |
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

There is no repository-side blocker to asking for initial guidance. There are,
however, blockers to production implementation: no decision between the
Standalones / Connect API and `rc_client` models, no RA identity, no approved
standalone page, no Hardcore design, no save/scenario policy, and incomplete
state coverage.

### Useful before contacting RA

- keep the proposal and evidence terminology precise;
- preserve the deterministic fixture and fail-closed identity tests;
- add scenario/objective and save-provenance evidence only as a separate,
  read-only workstream if needed;
- prepare a conceptual set plan and threat model;
- identify a potential RA developer/set-design partner if required by policy.

Further private engineering should not choose a production protocol before RA
answers the architecture question. More local work is useful only where it is
protocol-independent, such as state validation, fixtures, provenance, and
threat-model evidence.

### Can wait until after RA guidance

- choosing the final RA game/build identity and production protocol;
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

1. Would RA consider an external, read-only helper for the original Windows
   RCT1 executable an acceptable standalone architecture?
2. Should this integration follow the documented Standalones / Connect API
   model, use `rc_client`/rcheevos for local evaluation, use a combination, or
   follow another RA-supported architecture?
3. Assuming the project is accepted, what official game/build identity
   mechanism should the helper use, and how should the Standalones game page
   and primary game ID process apply?
4. Can multiple legitimate RCT1 executable builds be supported by one game
   page while the helper maintains separate validated memory decoders?
5. Is exposing a normalized logical RCTState memory space to achievement
   definitions acceptable rather than exposing raw RCT process addresses?
6. What integrity controls would RA expect an external helper to enforce for
   memory editors/trainers, debugger attachment, DLL injection, runtime
   modification, altered scenarios, and Proton/Wine?
7. How should normal RCT saved-game loading be handled in Hardcore,
   particularly for achievements intended to require a fresh scenario start?
8. Does the current six-month public-availability requirement in Hardcore
   Compliance Requirements apply to a newly developed standalone helper?
9. If the architecture is acceptable in principle, what development/testing
   workflow should be used before any real RA session or unlock submission?
10. What additional prototype evidence would RAdmin want before considering
    formal standalone approval?

## 17. Proposed next phase

**Recommendation B — the prototype is mature enough for an initial non-binding
RA discussion, but not for production integration or Hardcore approval.**

The recommendation is based on repository evidence: a supported-build gate,
read-only provider, coherent snapshots, rcheevos lifecycle, deterministic
fixtures, and a live local condition event. The remaining uncertainty is now
primarily the RA-specific production architecture, identity, policy, and
approval—not whether a read-only external prototype can technically observe and
evaluate a small amount of RCT state.

The purpose of initial contact would be to obtain architectural and policy
guidance before creating technical debt around the wrong production protocol.
It would not request immediate approval, achievements, Hardcore certification,
or production credentials.

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
