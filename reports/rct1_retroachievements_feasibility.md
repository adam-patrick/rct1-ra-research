# RCT1 RetroAchievements Feasibility Report

## Executive Summary

**Conclusion: Feasible but difficult.**

The installed original-style target is `RCT.EXE` from RollerCoaster Tycoon Deluxe, a 32-bit PE executable dated by its PE header to 2003-03-12 and distributed locally through a Steam installation of the 2003 Infogrames release. It is not a normal, analysis-friendly build: relocations and symbols are stripped, code is laid out in a nonstandard way, imports are minimal and partly ordinal-only, most useful strings are absent, and the binary contains an `ExeLock Executable File Protector` notice from StratusBurg. These are strong indicators of protection/packing or an unusual executable wrapper.

That does not make integration impossible. A future runtime analysis could still unpack the process in memory and identify the game state, but this report did not launch, attach to, inject into, or modify the game. No runtime addresses, pointer chains, or signatures were therefore established. On the evidence available, a **launcher plus external read-only helper** is the safest first architecture; a proxy DLL is not currently supported by the local file layout, and an injected DLL should wait until a stable runtime state map exists.

The separate installed `RCTClassic.exe` is a different 32-bit C++ build with OpenGL, FMOD, Steam, XInput, MSVC runtime, relocations, and many semantic strings. It may be a better reverse-engineering target, but it is not the original RCT Deluxe executable analyzed below.

## Installed Build

### Primary target

| Field | Finding |
|---|---|
| Installation path | `$HOME/.steam/steam/steamapps/common/RollerCoaster Tycoon Deluxe` |
| Primary executable | `RCT.EXE` |
| SHA-256 | `bdfebd64383b231de0252fe0726523d1c45aa2c4da919c2d7ed8bfb7aaa05c76` |
| Size | 809,908 bytes |
| PE architecture | PE32, Intel 80386 / 32-bit x86 |
| Subsystem | Windows GUI |
| PE image base | `0x00400000` |
| Entry point RVA | `0x0084628a` |
| PE timestamp | 2003-03-12 16:30:43 according to the header |
| File/product version metadata | No readable version-resource strings were found; `objdump` also reported an anomalous/corrupt resource layout. Do not infer a product version from the timestamp. |
| Distribution | Installed under Steam, app metadata for depot/app `285310`; embedded `285310_install.vdf` also contains GOG.COM install-script registry entries. The content identifies the product as Infogrames RollerCoaster Tycoon: Deluxe, released 2003-03-28 according to `readme.txt`. |
| Adjacent game DLLs | None in the Deluxe game directory. |
| Compatibility files | The retained installer contains legacy DirectX files, including `ddraw.dll`, `dsound.dll`, `dinput.dll`, and `dplayx.dll`; these are installer payloads, not proof that the installed game loads local copies. |

The directory also contains the original scenario set, including `Scenarios/sc0.sc4`, which contains the readable title `Forest Frontiers`. There is one tiny existing file at `Saved Games/001` (3 bytes); it was not opened or changed.

### Separate installed Classic build

| Field | Finding |
|---|---|
| Installation path | `$HOME/.steam/steam/steamapps/common/RollerCoaster Tycoon Classic` |
| Executable | `RCTClassic.exe` |
| SHA-256 | `68b4508a26195ebb209aeec5e37d634ca2d13d9d68a841e51355c04975d6d29f` |
| Size | 10,834,432 bytes |
| Architecture | PE32, Intel 80386 / 32-bit x86 |
| Important adjacent DLLs | `fmod.dll` SHA-256 `150db80e15e8dff00d1c4f99cb6d3259bf53f83aebc433eed7d25a12e25b063a`; `steam_api.dll` SHA-256 `3648e216ecf0c6a474b07e79d39394911bfb9b5c85a52c20886aec1e9709f82d` |

## Technical Findings

### PE layout and protection indicators for Deluxe

`RCT.EXE` reports seven sections, including:

| Section | RVA | Reported size | File contents |
|---|---:|---:|---|
| `.text` | `0x00401000` | `0x00195000` | no normal file-backed offset reported by GNU `objdump` |
| `CODESEG` | `0x00596000` | `0x001f1000` | no normal file-backed offset reported |
| `.rdata` | `0x00787000` | `0x00103000` | no normal file-backed offset reported |
| `.data` | `0x0088a000` | `0x00036000` | no normal file-backed offset reported |
| `DATASEG` | `0x00c3e000` | `0x00001000` | file-backed |
| `.rsrc` | `0x00c3f000` | `0x00005000` | file-backed; resource parser reported corruption |
| `.neolit` | `0x00c46000` | `0x00001bfa` | file-backed; contains the import directory and entry point region |

The PE flags say relocations and symbols are stripped. The entry point is in the unusual `.neolit` section rather than in the large code sections. The file contains the following protector text:

> ExeLock Executable File Protector  
> Copyright (c) 1998-2001 StratusBurg, LLC  
> Portions Copyright (c) 1997-2001 Lee Hasiuk

The ordinary ASCII strings are dominated by high-entropy or binary-looking data. The only useful embedded UI strings found were generic resource strings such as `Cancel`, `Prompt`, and `MS Sans Serif`; no reliable `cash`, `guest`, `rating`, `objective`, or `Forest Frontiers` strings were found in `RCT.EXE`. This strongly limits static anchor discovery until the protected code is observed after startup.

### Imports and APIs

The Deluxe import table contains:

- `KERNEL32.dll`: `GetProcAddress`, `LoadLibraryA`
- `USER32.dll`: `SystemParametersInfoA`
- `GDI32.dll`: `GdiFlush`
- `ADVAPI32.dll`: `RegCreateKeyExA`
- `comdlg32.dll`: `GetOpenFileNameA`
- `SHELL32.dll`: `Shell_NotifyIconA`
- `ole32.dll`: `CoCreateInstance`
- `WINMM.dll`: `timeGetTime`
- `DINPUT.dll`: `DirectInputCreateA`
- `DPLAYX.dll`: ordinal 2 only
- `DSOUND.dll`: ordinal 2 only

This proves direct use or dynamically mediated use of legacy DirectInput, DirectPlay, DirectSound, WinMM timing, registry, common dialogs, and COM-related functionality. No direct `DDRAW.dll` import was present in the static import table. Because `LoadLibraryA` and `GetProcAddress` are imported, additional APIs may be resolved dynamically; static imports alone are therefore incomplete.

No local proxy target was found beside `RCT.EXE`. The retained installer has old DirectX binaries, but substituting or proxying any of them would be an installation change and was not attempted.

### Data files and anchors

The installed Deluxe directory has a conventional external content layout:

- `Scenarios/*.SC4` for scenario files, including `sc0.sc4` / Forest Frontiers.
- `Saved Games/*` for saves.
- `Tracks/*.TD4` and `*.TP4` for ride designs.
- `Data/*.DAT` and `Game.cfg` for game assets/configuration.

The scenario title is present in `sc0.sc4`, but that is a file-level anchor, not evidence that the same title is kept as a plain in-memory string during play. Scenario/objective identity could eventually be validated against a known scenario checksum, while dynamic values such as guests and rating still require process-state analysis.

### Runtime inspection status

No RCT process was running during inspection. Launching the executable was not performed: doing so could create or update configuration, save, registry, or compatibility-prefix state and would violate the requested no-modification boundary. Consequently:

| Value | Runtime address | Type | Stable locator | Confidence |
|---|---|---|---|---|
| Current cash | Not located | Unknown | None established | Not assessed |
| Guest count | Not located | Unknown | None established | Not assessed |
| Park rating | Not located | Unknown | None established | Not assessed |
| Current scenario | Not located | Unknown | Scenario file anchor only | Not assessed |
| Success/failure state | Not located | Unknown | None established | Not assessed |

No raw absolute address should be used based on this report. A future runtime study must establish whether each value is a fixed module-relative address, a pointer chain, a signature match, or a field in a recognizable global structure, and must repeat that test across launches and scenario/save transitions.

## Candidate Architecture

### A. External helper process — recommended first

Technically feasible in principle. A launcher can verify the known executable hash, start the game under the user’s normal compatibility environment, identify the process, and use read-only process-memory APIs to inspect state. This minimizes game modification and keeps achievement evaluation separate from the protected executable.

The main risk is obtaining a stable state map. If the protector unpacks or relocates code/data at runtime, the helper will need module enumeration plus signatures or pointer validation rather than hard-coded addresses. This is the best fit for an initial proof of concept and for keeping future changes reversible.

### B. Launcher plus injected DLL

Likely technically feasible after runtime reverse engineering, but not yet justified. A helper DLL would have convenient in-process access and could call game functions or read globals, but injection is more invasive, increases crash/compatibility risk, and could interact poorly with ExeLock or any integrity checks. Do not choose this until an external read-only prototype proves the state locations.

### C. Proxy/wrapper DLL

Currently weak. `RCT.EXE` does not statically import `DDRAW.dll`, and there are no local `ddraw.dll`, `dsound.dll`, `dinput.dll`, or `winmm.dll` game-side wrappers. It dynamically imports `DINPUT.dll`, `DPLAYX.dll`, and `DSOUND.dll`, but replacing or proxying those system libraries is not safe or minimally invasive. A proxy approach should be reconsidered only after runtime API monitoring proves that a suitable load boundary exists.

### D. Binary patch/mod

Possible only in a broad technical sense, but unsuitable for this phase. The protected/nonstandard layout and the user’s no-patch constraint make it the highest-maintenance option. It would also complicate checksum validation and Hardcore-mode trust.

### E. Alternative

A read-only helper that combines process-memory reads with file identity checks is the cleanest architecture. If RCT Classic is later accepted as the target, its semantic strings and conventional PE layout suggest a separate investigation could be substantially easier, but it would require a different achievement/state map and a different supported-version identity.

## Achievement-State Matrix

| Achievement | Required State | State Located? | Reliability | Notes |
|---|---|---|---|---|
| Start Forest Frontiers | Active scenario identity equals canonical Forest Frontiers / `sc0.sc4` | No runtime state located | Unknown | File anchor exists in `Scenarios/sc0.sc4`; validate scenario checksum and runtime identity later. |
| Reach 800 park rating | Current park rating at least 800 | No | Unknown | Likely a numeric field or derived value in the live park structure; requires runtime scan and transition testing. |
| Reach 1,000 guests | Current guest count at least 1,000 | No | Unknown | Likely a global/park field, but no static anchor or type was established. |
| Own a roller coaster with at least 7.00 excitement | Iterate ride objects; identify coaster type/ownership and excitement value | No | Unknown / hardest | Requires ride-array structure, ownership/type fields, and the game’s stored rating scale; a single HUD value is insufficient. |
| Successfully complete Forest Frontiers | Active scenario is canonical Forest Frontiers and success/completion flag is set | No | Unknown | Need objective structure plus success/failure transition or a reliable end-state flag; do not infer from UI text alone. |

## RetroAchievements-Specific Concerns

A future standalone implementation should support only a known executable identity, at minimum the exact Deluxe `RCT.EXE` SHA-256 recorded above, and should reject unknown hashes by default. It should also validate the scenario file set and the canonical `sc0.sc4` hash before treating Forest Frontiers achievements as eligible. Scenario editors, custom scenarios, altered save files, trainers, cheats, and unsupported mods can invalidate assumptions about objectives and values.

Hardcore-mode validation should be conservative: a state read should be accepted only when the process identity, executable hash, scenario identity, and expected structure checks all pass. Save-state manipulation, speed changes, and external trainers are policy questions for a later implementation; this investigation did not attempt anti-cheat logic.

The eventual RetroAchievements Connect integration would need the supported game/version identity, user/session authentication or the supported client-mediated connection method, achievement definitions and IDs, and a state evaluator that reports only validated conditions. No network requests or unlock writes were made here.

## Risks / Unknowns

- The ExeLock layer may unpack or decrypt the real game code/data only after launch.
- Static PE section output is anomalous; offsets shown by `objdump` should not be treated as reliable file-to-memory mappings without independent parsing.
- No runtime state addresses or pointer chains were established.
- No debugger, memory scanner, API monitor, or process-memory reader was attached.
- The game may require legacy DirectX/CD-era behavior that differs under Wine/Proton or another compatibility layer.
- The exact current release/version beyond the hash and embedded distribution evidence is not exposed as a trustworthy version resource.
- A raw address that works for one launch would not be sufficient; ASLR, unpacking, saves, and scenario loads must be tested.
- The ride-excitement achievement requires object iteration and scale interpretation, not just one scalar field.

## Recommended Next Steps

1. Make a byte-for-byte backup or separate forensic copy of the installed directory, without changing the original.
2. Run the game only in a disposable, isolated compatibility prefix or VM whose writable game/config paths are redirected away from the installation.
3. Attach a debugger before or immediately after entry-point execution and document the protector’s unpacking behavior; do not patch or inject.
4. Use read-only memory snapshots and controlled gameplay to identify cash, guests, rating, scenario, and success/failure transitions.
5. Repeat each candidate locator across fresh launches, reloads, different scenarios, and saves; prefer signatures or validated pointer paths over absolute addresses.
6. Build a read-only external helper that reports state without sending network traffic. Only after that passes stability tests should injection or RetroAchievements API work be considered.

## Commands and Tools Used

Read-only inspection used GNU `file`, `sha256sum`, `stat`, `ls`, `find`, `strings`, `od`, `objdump`, `ps`, and `sed`. No executable, DLL, scenario, save, registry entry, system hook, process injection, network request, or achievement data was modified or created by this investigation. The only deliverable created is this Markdown report.
