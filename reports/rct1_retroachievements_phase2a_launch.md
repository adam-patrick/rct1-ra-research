# RCT1 RetroAchievements Phase 2A Launch Report

## Executive Summary

**Clean launch achieved.**

The legitimate Steam-owned RollerCoaster Tycoon Deluxe package can reach a
playable Forest Frontiers park under a clean, isolated Proton 10.0 prefix
without changing the canonical Steam installation and without bypassing DRM.

The key was to run the Steam-supplied InstallShield installer inside the clean
prefix, then launch the installed copy using the registry and files created by
that installer. Launching the bare canonical Steam directory in a clean prefix
continued to show the CD prompt. The installer-created copy reached the RCT
window, displayed the Loopy Landscapes content, opened the scenario selector,
loaded Forest Frontiers, and remained stable for more than four minutes.

This is now a valid starting point for Phase 2 runtime state discovery. Do not
use the canonical game directory as writable state; use the isolated installed
copy and the exact runtime/prefix procedure recorded here.

## Canonical Installation Integrity

Canonical path:

```text
$HOME/.steam/steam/steamapps/common/RollerCoaster Tycoon Deluxe
```

`RCT.EXE` before testing:

```text
SHA-256: bdfebd64383b231de0252fe0726523d1c45aa2c4da919c2d7ed8bfb7aaa05c76
Size:    809908 bytes
Mtime:   2026-02-15 17:41:16.485920551 -0600
```

`RCT.EXE` after testing:

```text
SHA-256: bdfebd64383b231de0252fe0726523d1c45aa2c4da919c2d7ed8bfb7aaa05c76
Size:    809908 bytes
Mtime:   2026-02-15 17:41:16.485920551 -0600
```

The canonical hash, size, timestamp, and mode were unchanged. No canonical
game file was overwritten. The isolated installed copy also has the same
executable hash and the original 2003-03-12 executable timestamp:

```text
$RCT1_RESEARCH_DIR/runtime-test/compatdata/pfx/drive_c/Program Files (x86)/Infogrames Interactive/RollerCoaster Tycoon Deluxe/RCT.EXE
SHA-256: bdfebd64383b231de0252fe0726523d1c45aa2c4da919c2d7ed8bfb7aaa05c76
```

## Steam Package Findings

The Steam installation contains a complete secondary InstallShield package:

```text
$HOME/.steam/steam/steamapps/common/RollerCoaster Tycoon Deluxe/RCTdeluxe_install
```

Important assets include:

- `setup.exe` — SHA-256 `e25cadc80ea5163e0f1c6fd703479469d9f23b47ade244fac5f22bcdb01b39bd`
- `setup.ini` — SHA-256 `c55d033fd2f358031363dbb3b44936bbc566be467ea8817ec1ff2637e1eb2073`
- `data1.cab` — SHA-256 `0229bec8e0eee54d9fb7b1f0bc128d88ff9f24ec05797f3c2bdce46f4c85e35f`
- `data1.hdr` — SHA-256 `66ff6b290a3b42b6957953c86eaa828b70e8e9b0122e15b6e5a0c3fc6353d894`
- `data2.cab` — SHA-256 `683038f602b5588b30a79fe6e4e7dc432f679d4adab22a34034542f12cc9dc04`
- `engine32.cab` — SHA-256 `bd3581f52a75fc9f0f044d239e152a2d542efa552131662ab32edc753224f0ad`

The package also includes the full Deluxe data/scenario/track content and
legacy DirectX installer payloads. The installer’s `setup.ini` identifies the
product as Infogrames Interactive RollerCoaster Tycoon Deluxe, with product
GUID `{924EAD66-F854-4605-8493-696DD59A113B}`.

The installer does contain the Deluxe/Loopy Landscapes content. The successful
launch screen visibly showed `Corkscrew Follies Pack` and `Loopy Landscapes
Pack`, and the scenario selector exposed the Loopy Landscapes tab.

## Compatibility Runtime

The successful test used one runtime consistently:

| Setting | Value |
|---|---|
| Runtime | Proton 10.0 |
| Proton executable | `$HOME/.steam/steam/steamapps/common/Proton 10.0/proton` |
| Proton prefix version | `10.1000-105` |
| Isolated compatdata | `$RCT1_RESEARCH_DIR/runtime-test/compatdata` |
| Prefix | `$RCT1_RESEARCH_DIR/runtime-test/compatdata/pfx` |
| Steam client path | `$HOME/.steam/debian-installation` |
| Architecture | 32-bit Windows game under Proton/Wine WoW64 support |
| Game process | `RCT.EXE`, observed PID `35514` |
| Module base in successful run | `0x00400000` |
| Canonical install | Read-only; never used as the installer destination |

The isolated installer-created game path was:

```text
C:\Program Files (x86)\Infogrames Interactive\RollerCoaster Tycoon Deluxe
```

On Linux, this corresponds to:

```text
$RCT1_RESEARCH_DIR/runtime-test/compatdata/pfx/drive_c/Program Files (x86)/Infogrames Interactive/RollerCoaster Tycoon Deluxe
```

## Launch Tests

| Method | Runtime | Prefix | Main Menu | CD Prompt | Forest Frontiers | Result |
|---|---|---|---|---|---|---|
| Steam `steam -applaunch 285310` | Steam client with its runtime startup | Existing Steam prefix | Not observed during the initial window | Not determined | No | Steam initialized, but no RCT process appeared during the observation window. |
| Direct canonical `RCT.EXE` | Proton 10.0 | New isolated prefix before installer completion | RCT process/window started | Yes in the prior clean-prefix path | No | Bare canonical directory did not satisfy the original media check. |
| Steam-supplied `RCTdeluxe_install/setup.exe` | Proton 10.0 | `$RCT1_RESEARCH_DIR/runtime-test/compatdata` | Installer completed | N/A | N/A | Installed full game tree and created registry/install records in the isolated prefix. |
| Installed copy from isolated prefix | Proton 10.0 | Same isolated prefix | Yes | No | **Yes** | Forest Frontiers loaded and remained playable for more than four minutes. |
| Steam-supplied installer comparison | Plain Wine 9.0 | Separate `plain-wine-prefix` | No completed game install observed | N/A | N/A | No usable installed RCT copy was found in the comparison prefix. |

## Registry / Install-State Findings

The successful installer run created legitimate state in the isolated prefix;
no registry values were manually invented or added. Relevant entries include:

```text
HKLM\Software\Wow6432Node\Fish Technology Group\RollerCoaster Tycoon Setup
  AddOn=1
  Executable="rct.exe"
  Path="C:\Program Files (x86)\Infogrames Interactive\RollerCoaster Tycoon Deluxe"
  SetupPath="Z:\home\adam\.steam\steam\steamapps\common\RollerCoaster Tycoon Deluxe\RCTdeluxe_install"

HKLM\Software\Wow6432Node\Infogrames Interactive\RollerCoaster Tycoon Deluxe\1.00.000

HKLM\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{924EAD66-F854-4605-8493-696DD59A113B}
  DisplayName="RollerCoaster Tycoon Deluxe"
  DisplayVersion="1.00.000"
  InstallLocation="C:\Program Files (x86)\Infogrames Interactive\RollerCoaster Tycoon Deluxe"
```

The installer-created copy contained `RCT.EXE`, `Data`, `Scenarios`, `Tracks`,
the manual, and other expected product files. The registry path and the
installed directory agree. This explains the difference from launching the
bare canonical directory: normal installation state is present in the
successful prefix.

## Successful Procedure

The following procedure is reproducible without writing to the canonical Steam
directory:

1. Create a fresh isolated compatdata directory:

   ```bash
   mkdir -p "$RCT1_RESEARCH_DIR/runtime-test/compatdata"
   ```

2. Run the Steam-supplied installer from its existing package using only Proton
   10.0 and the isolated prefix:

   ```bash
   cd "$HOME/.steam/steam/steamapps/common/RollerCoaster Tycoon Deluxe/RCTdeluxe_install"
   STEAM_COMPAT_CLIENT_INSTALL_PATH="$HOME/.steam/debian-installation" \
   STEAM_COMPAT_DATA_PATH="$RCT1_RESEARCH_DIR/runtime-test/compatdata" \
   WINEDEBUG=-all \
   "$HOME/.steam/steam/steamapps/common/Proton 10.0/proton" \
   run "$PWD/setup.exe"
   ```

3. Launch the installed copy from its isolated prefix, keeping the working
   directory at the installed game directory:

   ```bash
   cd "$RCT1_RESEARCH_DIR/runtime-test/compatdata/pfx/drive_c/Program Files (x86)/Infogrames Interactive/RollerCoaster Tycoon Deluxe"
   STEAM_COMPAT_CLIENT_INSTALL_PATH="$HOME/.steam/debian-installation" \
   STEAM_COMPAT_DATA_PATH="$RCT1_RESEARCH_DIR/runtime-test/compatdata" \
   WINEDEBUG=-all \
   "$HOME/.steam/steam/steamapps/common/Proton 10.0/proton" \
   run 'C:\Program Files (x86)\Infogrames Interactive\RollerCoaster Tycoon Deluxe\RCT.EXE'
   ```

4. In the game window, choose the normal New Game control, select the
   original RCT tab if necessary, select `Forest Frontiers`, and wait for the
   park to load.

5. Confirm the park UI is visible. The observed successful screenshot showed:

   - Window title: `RollerCoaster Tycoon`
   - Scenario objective window: `Forest Frontiers`
   - Cash: `$10,000.00`
   - Guests: `0 Guests`
   - Date: `March, Year 1`
   - Park map and normal toolbar visible
   - Simulation window remained alive during a more-than-four-minute check

Evidence screenshots are retained in:

- `runtime-test/logs/rct_window.png` — installed copy/menu
- `runtime-test/logs/rct_after_click1.png` — scenario selector with Forest Frontiers listed
- `runtime-test/logs/rct_forest_frontiers.png` — Forest Frontiers loaded with objective and initial UI values
- `runtime-test/logs/rct_forest_stable.png` — park still running after the stability interval

## Remaining Issues

- Steam’s GUI `-applaunch` behavior was not needed for the successful isolated
  procedure and was not fully observable in the initial headless command
  window. The successful method reproduces the Proton environment directly.
- The existing Steam compatdata had previously been mixed between Proton 8 and
  Proton 10 during earlier phases. The successful procedure avoids it entirely
  with a new prefix.
- The plain Wine comparison was not used for the successful result.
- No memory scanning, debugger attachment, DLL injection, process-memory write,
  patch, no-CD workaround, or RetroAchievements network operation was used.

## Phase 2 Resume Point

**READY TO RESUME RUNTIME STATE DISCOVERY**

Resume with the isolated installed copy and the successful configuration:

- Process name: `RCT.EXE`
- PID discovery: scan `/proc/*/comm` for `RCT.EXE`, then inspect `/proc/<pid>/maps`
- Successful observed PID: `35514` (future runs will differ)
- Module base behavior: `0x00400000` in the successful run; validate again in
  later runs rather than assuming it is stable
- Runtime: Proton 10.0 at `$HOME/.steam/steam/steamapps/common/Proton 10.0/proton`
- Prefix: `$RCT1_RESEARCH_DIR/runtime-test/compatdata`
- Launch: the installed-copy command in the Successful Procedure section
- Initial known visible state: cash `$10,000.00`, guests `0`, March Year 1,
  Forest Frontiers active
