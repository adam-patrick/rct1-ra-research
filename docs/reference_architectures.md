# Reference architectures for an RCT1 standalone integration

## Purpose

This note reviews public RetroAchievements-related projects before this repository commits to a network or achievement-runtime design. The goal is to separate reusable boundaries from assumptions that only make sense for an emulator, a mod framework, or a particular game.

The reviewed references are:

* [Terraria-RetroAchievements](https://github.com/timenoe/Terraria-RetroAchievements), a public tModLoader mod and its [RASharpIntegration](https://github.com/timenoe/RASharpIntegration) C# submodule.
* [wii-ra-adapter](https://github.com/odelot/wii-ra-adapter), a public early-release hardware adapter that embeds the official [rcheevos](https://github.com/RetroAchievements/rcheevos) client.
* [rcheevos `rc_client` integration guide](https://github.com/RetroAchievements/rcheevos/wiki/rc_client-integration) and the [rcheevos repository](https://github.com/RetroAchievements/rcheevos).
* [RetroAchievements standalone support requirements](https://docs.retroachievements.org/general/standalone-support.html) and the [standalone Connect API guide](https://api-docs.retroachievements.org/connect/standalone.html).
* [RAInterface](https://github.com/RetroAchievements/RAInterface) and [RALibretro](https://github.com/RetroAchievements/RALibretro) as emulator-side references, explicitly not as standalone-game precedents.

These are public implementations and documentation, not evidence that an RCT1 set or any reviewed third-party project has been approved by RetroAchievements. Standalone support requires an RA proposal and administrator approval; technical feasibility alone is not acceptance.

## Terraria RetroAchievements

### Architecture and project structure

Terraria-RetroAchievements is a tModLoader mod. The repository puts the mod entry point in `RetroAchievements.cs`, separates game-specific behavior into folders such as `Systems`, `Players`, `NPCs`, `Items`, `Worlds`-equivalent content, and keeps achievement definitions/data under `Achievements` and the `TerrariaAchievementLib` submodule. The top-level README also exposes player-facing commands for login, logout, synchronization, local reset, and rich presence.

The important architectural fact is that this is an in-process, game-aware integration:

```text
Terraria/tModLoader game objects and events
                 |
                 v
       game-specific achievement systems
                 |
                 +--> local achievement metadata/progress
                 |
                 v
       RASharpIntegration NetworkInterface
                 |
                 v
           RetroAchievements APIs
```

State acquisition is therefore supplied by Terraria and tModLoader APIs rather than by a generic memory provider. The mod can observe worlds, players, items, NPCs, multiplayer state, loaded mods, and other semantic game objects directly. This makes the achievement code readable, but it is not a reason to put RCT-specific interpretation into the future RA layer.

### Achievement evaluation and metadata

The mod loads structured JSON achievement data for the selected game. Its main class derives values such as game ID, achievement ID, internal name, progression categories, and whitelisted mods from that data. This is a useful separation between:

* metadata and IDs;
* game event/state observers;
* player-facing commands and menus; and
* network/session operations.

For RCT1, the equivalent should be a versioned metadata file or generated table, but the evaluator should consume a typed `RCTState` rather than read raw process addresses itself. Achievement IDs, titles, descriptions, progression flags, and rich-presence text should not be scattered through low-level memory code.

### RA communication and session handling

Terraria uses the separate RASharpIntegration library. Its README describes a `NetworkInterface` over an application-provided `HttpClient`, with login by username/password, token caching, session start, logout, sync, and host configuration. The integration is intentionally a C# standalone-client abstraction, not `rc_client`.

Reusable lesson: isolate authentication and request formatting behind a small client boundary. Do not make the game-state code know about HTTP, credentials, or token storage.

Non-reusable detail: RCT1 is currently a C/read-only external helper, so copying a .NET library or Terraria's chat-command surface would add technology and UI scope without solving state acquisition. The eventual RCT1 client should use the RA-supported runtime/API path chosen after the project has a stable state model.

### Hardcore and environment validation

Terraria's Challenge Mode is enabled by default in the project and disables Hardcore when the configured conditions make it unsafe, notably multiplayer. The README lists restrictions including Journey Mode, special seeds, multiplayer, external players/worlds, and non-whitelisted external mods. The code also distinguishes internal mods from a configured whitelist.

The reusable pattern is an explicit eligibility policy:

```text
runtime facts --> policy decision --> hardcore allowed / softcore only
```

For RCT1, this suggests a validator that can report reasons, not just a boolean: supported `RCT.EXE` hash, expected scenario/data identity, save provenance if relevant, unsupported process modifications, and whether the developer inspector or any prohibited tooling is active. The exact whitelist must be decided with RA policy guidance; Terraria's list must not be copied.

### Rich presence and player UX

Terraria exposes rich presence and RA status through commands and integrates its local mod UI with the game. The reusable idea is that session state and player feedback are separate from achievement condition evaluation. RCT1 could eventually provide a small external status window or tray/UI surface because it cannot safely add UI inside the protected game without expanding scope.

### What does not apply

Terraria-specific elements that should not be imported into RCT1 include tModLoader hooks, C# mod lifecycle, chat commands, world/player/mod object names, Terraria's save/progress format, and its mod whitelist. Terraria also has direct semantic access to game state that RCT1 does not have. The RCT1 equivalent must first prove read-only process-state locators and a normalized state model.

## Wii RA Adapter

### Architecture and memory acquisition

wii-ra-adapter is a public early-release hardware project for original Wii/GameCube hardware. Its README describes three cooperating roles: a loader, a console-side memory server, and an ESP32-S3 “brain.” The ESP32 runs Wi-Fi, login, `rc_client`, achievement evaluation, and a live web dashboard. The console side reads game RAM and streams snapshots; the game itself remains unmodified.

The architectural shape is the closest reference to this project:

```text
unmodified game RAM
        |
console-side memory server / snapshot transport
        |
memory provider abstraction
        |
rc_client evaluator
        |
RA network + events + dashboard
```

The adapter's console-specific code deals with where memory lives (Wii MEM1/MEM2 or GameCube memory), frame synchronization, hashing, and transport. The ESP32-side evaluator is comparatively independent of that physical layout. This is the right conceptual boundary for RCT1:

```text
RCT.EXE --> process_vm_readv memory provider --> normalized RCT state
                                      \--> future RA memory view / evaluator
```

### Watched-address model

The adapter does not ship the whole RAM image blindly. It loads the achievement set, compiles the referenced addresses and pointer chains into a watchlist, sends that list to the console side, and receives per-frame snapshots. The README describes incremental watchlist updates, sequence numbers, and pointer-chain descriptors.

For RCT1, this suggests a future optimization and a useful diagnostic API: represent a read request as a set of typed addresses/ranges and provide one coherent snapshot to all consumers for a tick. It does not mean the current scanner should be rewritten into a watchlist now. Until the RCT state layout is known, full selected-range snapshots are easier to validate and less likely to hide a bad locator.

The most important rule is snapshot coherence: the achievement evaluator, Hardcore validator, and developer inspector should consume the same captured observation rather than independently racing `process_vm_readv()` calls.

### `rc_client`, hashing, and game identification

The Wii loader computes a game hash, performs a load-game handshake, and the adapter passes the identified game to `rc_client`. The adapter's README describes a fallback game-ID table for some Wii cases and different hashing paths for Wii and GameCube media.

RCT1 has a different identity problem. The current evidence supports an exact executable hash (`bdfebd64383b231de0252fe0726523d1c45aa2c4da919c2d7ed8bfb7aaa05c76`) and file-level scenario anchors, but no RA game hash or runtime scenario locator has been validated. Therefore RCT1 should initially use an explicit supported-build manifest and reject unknown executable hashes. Do not invent a ROM-style hash protocol or infer scenario identity from a one-off pointer.

### UI and debugging

The adapter includes a live web dashboard showing game information, achievement list/progress, unlock notifications, challenge indicators, and rich presence. That is a strong example of keeping observability outside the game and of making the evaluator useful without coupling it to a particular on-screen overlay.

RCT1 can borrow the dashboard's information architecture later, but not its hardware transport or web stack. The existing command-line scanner should remain independently usable; a future GUI can consume a stable read-only inspection protocol.

### What does not apply

The Wii loader, VBlank hooks, console kernel modules, EXI protocol, ESP32 scheduling, pointer-chain compilation for bus transport, and physical trophy overlay do not apply to a Linux/Proton process helper. The project is also explicitly an early release, so its rough edges are evidence of an approach, not a compatibility or RA-approval guarantee.

## rcheevos / `rc_client`

### What it can remove from our code

`rcheevos` is the official C library for parsing/evaluating RA achievement and leaderboard logic. The `rc_client` layer can centralize common client responsibilities: user/session state, login using password or remembered token, game identification/loading, achievement and leaderboard data, event dispatch, progress serialization, rich presence, and server request preparation.

The integration guide shows the intended lifecycle:

1. Create `rc_client_t` with a memory-read callback and server-call callback.
2. Log in asynchronously, usually with a token after the first login.
3. Identify and load the game, then wait for the asynchronous completion callback.
4. Call `rc_client_do_frame()` for every game frame that should be evaluated.
5. Handle events such as achievement triggers, leaderboard changes, reset requests, and errors.
6. Supply UI, image caching, logging, HTTP transport, and local persistence in the host.

This could remove our need to implement RA condition parsing, session state machines, unlock submission, leaderboard processing, rich-presence timing, and achievement progress bookkeeping.

### Callbacks and host responsibilities

The host still owns the critical boundaries:

* `read_memory(address, buffer, size, client)`: map RA-visible addresses to readable RCT process bytes, or expose a deliberately designed normalized memory view.
* `server_call(request, callback, callback_data, client)`: perform asynchronous HTTP(S), preserve callback data, and return status/body/error information.
* event handler: turn unlocks, reset requests, Hardcore changes, and failures into host behavior.
* logging and user-data plumbing.
* game identity input, build/scenario validation, UI, image caching, and local credentials/progress policy.

The guide specifically notes that `rc_client` does not provide HTTP or UI. It also says the runtime is normally driven once per frame and that paused hosts should use `rc_client_idle()` instead of `rc_client_do_frame()`.

### Suitability for RCT1

`rc_client` appears suitable for a future RCT1 client, but only after the state layer answers a more fundamental question: what address space and memory semantics should RA achievement code see? There are two possible designs:

* expose a validated RCT-compatible memory map and let RA conditions read the relevant process bytes; or
* keep a normalized `RCTState` for project logic and add a carefully documented RA memory adapter for any achievement conditions that require raw addresses.

The second option is safer for early development. A normalized state model is testable against recorded snapshots and prevents every achievement from becoming coupled to Wine virtual addresses. If an eventual official set expects RA memory conditions, the adapter can expose stable logical addresses backed by the process layer, provided the mapping is documented and validated.

`rc_client` must not be introduced as a substitute for locator validation. It would make unreliable reads look like an integration bug and would prematurely require credentials, network calls, game identity, and Hardcore policy.

### Hardcore implications

The official guide says Hardcore should be enabled by default once the host is ready, and that restricted features include save-state loading, gameplay cheats, rewind, slowdown/frame advance, debugger/memory windows, and input playback. Enabling or changing Hardcore can request a host reset. It also warns that an unrecognized User-Agent can cause server demotion of Hardcore unlocks.

For RCT1, the developer memory inspector must therefore be clearly unavailable or softcore-only while Hardcore is active. The current scanner is intentionally a research tool, so it must not be presented as a Hardcore-safe player client. A future client needs an explicit mode boundary and a validated User-Agent/RA integration process.

## Other references and how to classify them

| Reference | Classification | Relevance to RCT1 |
|---|---|---|
| [RASharpIntegration](https://github.com/timenoe/RASharpIntegration) | Reusable standalone-client library used by Terraria; not `rc_client` | Shows a thin network/session boundary, token lifecycle, host configuration, and application-owned HTTP. Technology choice does not fit the current C scanner automatically. |
| [wii-ra-adapter](https://github.com/odelot/wii-ra-adapter) | Hardware adapter; public early release | Strong memory-provider/evaluator separation and watchlist/snapshot ideas; Wii transport and kernel components are not portable. |
| [rcheevos](https://github.com/RetroAchievements/rcheevos) | Official RA runtime library | Candidate future evaluator/session layer. It still needs host memory, HTTP, UI, identity, and policy code. |
| [RAInterface](https://github.com/RetroAchievements/RAInterface) | Emulator integration through `RA_Integration.dll` | Useful as an example of host hooks and a Windows overlay boundary. It is not a recommendation to inject or patch RCT.EXE, and it is not a standalone-game architecture for this project. |
| [RALibretro](https://github.com/RetroAchievements/RALibretro) | Emulator/development frontend | Useful for emulator-side UI and RA integration conventions; its ROM/emulator assumptions do not describe RCT1 process inspection. |
| [RetroAchievements standalone guide](https://docs.retroachievements.org/general/standalone-support.html) | Official policy/documentation | Establishes approval, age/update, Hardcore, proposal, and set-plan constraints. It is the authority for process, not a code template. |

No reviewed reference should be described as proof that RCT1 standalone support is approved. The closest technical parallels are a public hardware adapter and a public game mod; neither eliminates the need for an RCT-specific proposal and validated prototype.

## Proposed RCT1 architecture

The reference implementations support this refinement of the project's original model:

```text
RCT.EXE
  |
  | process discovery, executable/build checks, read-only snapshots
  v
RCT Process Layer
  |
  v
RCT Memory Provider  -----> raw ranges / typed reads / snapshot records
  |
  v
RCT State Decoder -------> validation evidence and confidence
  |
  v
normalized RCTState
  |             |                 |
  |             |                 +--> developer inspector / CLI / later GUI
  |             +--------------------> Hardcore eligibility/policy
  +----------------------------------> future achievement runtime
                                             |
                                             v
                                          rc_client
                                             |
                              host HTTP, UI, identity, events
                                             |
                                             v
                                      RetroAchievements
```

The decoder should be the only layer that knows that a field came from `base + offset`, a pointer chain, a signature, or a validated anonymous mapping. The RA runtime should not know about `/proc`, Proton, or `process_vm_readv`.

## Component responsibilities

### `process/`

* Find the intended `RCT.EXE` process and handle process exit/restart.
* Inspect `/proc/<pid>/maps` and readable ranges.
* Verify executable identity, architecture, and supported hash.
* Perform read-only reads and coherent snapshot capture.
* Never expose write, injection, patch, freeze, or game-function invocation APIs.

### `rct/`

* Decode raw snapshots into typed fields such as cash, guests, rating, date, scenario, objective status, and rides.
* Record locator/version/scenario provenance and confidence.
* Reject incomplete or inconsistent state rather than returning plausible defaults.
* Provide a stable `RCTState` test fixture format for recorded observations.

### `tools/`

* Keep the current human-driven scanner and value-scan utilities.
* Add snapshot export, candidate annotations, and validation reports only when they help the next experiment.
* Keep developer inspection separate from any Hardcore-capable runtime.

### `hardcore/`

* Enforce the supported executable hash and expected file/scenario identity.
* Track unsupported modifications, invalidated reads, debugger/inspector mode, pause/clock policy, and save/load policy.
* Return structured reasons such as `unsupported_build`, `state_unverified`, or `developer_inspector_active`.
* Defer final policy decisions to an RA proposal and documented rules.

### `ra/`

* Later own `rc_client`, login/token lifecycle, game loading, frame/idle calls, event handling, rich presence, and unlock/leaderboard notifications.
* Consume a stable memory/state interface; do not discover RCT addresses.
* Keep the host HTTP implementation and User-Agent in one place.

### `ui/`

* Later provide status, current scenario/state confidence, achievement progress, and unlock notifications.
* Never become the only way to run the scanner or evaluator.
* Disable or clearly mark memory inspection when Hardcore policy requires it.

## Recommended repository evolution

Do not reorganize the existing scanner into a production tree yet. A practical incremental layout is:

```text
phase2/state_reader/        current read-only scanner and utilities
docs/                       research and architecture notes
tools/                      future snapshot/validation commands
src/process/                process discovery and read-only provider
src/rct/                    decoders, typed RCTState, fixtures
src/hardcore/               eligibility policy and reasons
src/ra/                     future rc_client host adapter
src/ui/                     optional external status/debug client
tests/fixtures/             redacted/derived snapshot fixtures, no game assets
```

The first production-oriented code can remain a small C or C-compatible library around the existing read-only primitives. The scanner can call that library later, after behavior is covered by fixtures. Avoid a GUI, `rc_client`, or a broad refactor while the first state locator is still unvalidated.

## Near-term recommendation

Build next:

1. A repeatable controlled state-discovery experiment for guest count, using the already validated isolated runtime and transitions from `0` to `10`, `11`, `12`, and so on.
2. Snapshot export and candidate validation across several simulation ticks and three fresh launches.
3. A minimal typed decoder for one field only after its locator and raw encoding are proven.
4. Cross-check cash, guest count, and rating against the same snapshot timestamp before modeling scenario/objective and ride structures.

Do not begin a full RA client yet. The evidence currently says that memory/state reliability is the bottleneck, not network plumbing. A future `rc_client` spike should happen only after at least one stable field, a coherent snapshot API, and a decision about the RA-visible memory map.

## GUI consideration

GUI work should begin **after one validated state field**, and only as a thin client over the scanner/provider boundary. That timing gives the GUI one trustworthy RCT-specific value to display and forces a useful separation between backend and presentation without committing to a generic Cheat Engine replacement.

The first GUI milestone should be deliberately small:

* process/build status;
* one or more validated RCT fields;
* candidate bookmarks and watched values;
* snapshot freshness and confidence;
* a clear developer/research mode indicator.

Login/status panels, achievement lists, rich presence, and unlock toasts belong after the core `RCTState` model and Hardcore policy exist. The command-line scanner remains the authoritative research tool until then.

## Conclusions

* The reusable core is a memory-provider/evaluator boundary, not any particular Terraria or Wii transport.
* `rcheevos` is a credible future runtime choice, but it does not provide HTTP, UI, RCT state decoding, or Hardcore enforcement for us.
* RCT1 should identify the supported executable conservatively by hash and validate scenario/data identity separately.
* A normalized, snapshot-based `RCTState` should sit between process reads and both the developer tools and future RA integration.
* The next technical milestone is a validated state field and recorded snapshot workflow, not achievement definitions, GUI implementation, or network integration.
