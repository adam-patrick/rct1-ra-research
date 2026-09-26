# RCT1 Runtime Scanner

This is a human-driven snapshot/filter scanner for the exact Proton RCT Deluxe runtime. It is intentionally read-only: it uses `/proc/<pid>/maps` and `process_vm_readv()` only. It contains no process-memory write API, DLL injection, input automation, game-function invocation, or file modification.

## Build and run

```bash
cd phase2/state_reader
cc -O2 -Wall -Wextra -o rct1_state_scanner rct1_state_scanner.c
./rct1_state_scanner
```

Start RCT first. The scanner locates `RCT.EXE`, reports PID/module base, and includes readable/writable private mappings in the low 32-bit game address space while excluding shared libraries and unrelated high mappings. Option 15 reports the current selection.

## Interactive workflow

1. Choose `1` and enter the visible value as its raw integer representation.
2. Play normally in RCT.
3. Choose `2` for a new exact value, or `3`–`8` for changed/unchanged/increased/decreased/delta filtering.
4. Use `9` to see addresses, module offsets, types, previous/current values, and deltas.
5. Use `10` to watch candidates refresh approximately once per second; press Enter to return.
6. Use `11` to inspect ±64, ±128, or ±256 bytes around a candidate.
7. Use `12`/`13` to save/load a session and `14` to reset.

The scanner supports signed and unsigned 8-, 16-, and 32-bit interpretations, and records the interpretation for every candidate. Saved absolute addresses are tied to the saved PID/session; after a restart, load only as a starting point and expect invalid addresses.

### Controlled transition protocol

For a value that changes during simulation, use this human-in-the-loop order:

1. Record the displayed value and pause the game through the normal UI.
2. Scan the paused snapshot and record the PID, module base, raw scale/type,
   and candidate count.
3. Unpause normally and perform one controlled action or wait for one known
   transition.
4. Pause again before filtering or rescanning. Do not validate candidates from
   a scan taken while the simulation is running.
5. Use `Changed`, `Increased`, `Decreased`, or a known-delta filter, then repeat
   an unchanged paused check.
6. Restart the game and repeat the read in a fresh process before promoting a
   locator.

This pause/scan/unpause/re-pause coordination is intentional: broad scans can
take long enough for the game to change state while the scan is in progress.

### Guest-count example

Start with the visible count, select `u16` or all types, scan the integer, let guests enter normally, then filter with `Changed`, `Increased`, or `Increased by amount`. Repeat until only a few candidates remain.

### Cash example

For displayed cash such as `$9,516.00`, the validated field currently reads
`95160` (displayed dollars x10). The tool deliberately does not silently
assume a decimal scaling, so use heuristic scales or test representations
explicitly. After a normal cash decrease, pause again and use `Decreased` or
`Decreased by amount` with the raw representation under test.

## Limitations

Repeated values can produce many candidates, and a saved absolute address may not survive a fresh launch. A candidate is evidence only until controlled gameplay changes and cross-launch validation confirm it. The tool never controls RCT or alters game state.
