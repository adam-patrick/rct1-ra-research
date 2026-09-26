#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

COMPATDATA="${COMPATDATA:-${PROJECT_ROOT}/runtime-test/compatdata}"
GAME_DIR="${GAME_DIR:-${COMPATDATA}/pfx/drive_c/Program Files (x86)/Infogrames Interactive/RollerCoaster Tycoon Deluxe}"
PROTON="${PROTON:-${HOME}/.steam/steam/steamapps/common/Proton 10.0/proton}"
STEAM_CLIENT_PATH="${STEAM_CLIENT_PATH:-${HOME}/.steam/debian-installation}"
RCT_EXE="${GAME_DIR}/RCT.EXE"
WINDOWS_RCT_EXE='C:\Program Files (x86)\Infogrames Interactive\RollerCoaster Tycoon Deluxe\RCT.EXE'

if [[ ! -x "${PROTON}" ]]; then
    printf 'Error: Proton executable not found or not executable:\n  %s\n' "${PROTON}" >&2
    printf 'Set PROTON to your Proton executable path and try again.\n' >&2
    exit 1
fi

if [[ ! -d "${COMPATDATA}/pfx" ]]; then
    printf 'Error: Proton prefix not found:\n  %s\n' "${COMPATDATA}/pfx" >&2
    printf 'Run the validated installer procedure first; this script does not create or install the prefix.\n' >&2
    exit 1
fi

if [[ ! -f "${RCT_EXE}" ]]; then
    printf 'Error: installed RCT.EXE not found:\n  %s\n' "${RCT_EXE}" >&2
    printf 'Run the validated installer procedure first; this script does not install game files.\n' >&2
    exit 1
fi

cd -- "${GAME_DIR}"

exec env \
    STEAM_COMPAT_CLIENT_INSTALL_PATH="${STEAM_CLIENT_PATH}" \
    STEAM_COMPAT_DATA_PATH="${COMPATDATA}" \
    WINEDEBUG=-all \
    "${PROTON}" \
    run "${WINDOWS_RCT_EXE}"
