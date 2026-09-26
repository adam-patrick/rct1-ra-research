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

### Guest-count example

Start with the visible count, select `u16` or all types, scan the integer, let guests enter normally, then filter with `Changed`, `Increased`, or `Increased by amount`. Repeat until only a few candidates remain.

### Cash example

For displayed cash such as `$9,516.10`, try raw values such as `951610`, `95161`, or `9516` in separate scans. The tool deliberately does not silently assume a decimal scaling. After a normal purchase, use `Decreased` or `Decreased by amount` with the raw representation you are testing.

## Limitations

Repeated values can produce many candidates, and a saved absolute address may not survive a fresh launch. A candidate is evidence only until controlled gameplay changes and cross-launch validation confirm it. The tool never controls RCT or alters game state.
