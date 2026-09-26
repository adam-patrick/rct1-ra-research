# RCT1 phase 2 state tools

Build:

```sh
cc -O2 -Wall -Wextra -o rct1_state_reader rct1_state_reader.c
cc -O2 -Wall -Wextra -o rct1_value_scan rct1_value_scan.c
```

`rct1_state_reader` locates the process named `RCT.EXE`, derives the executable mapping base, and reads one currently validated cash field at `base + 0x766480`. It does not write to the target process, inject code, or call game functions. Guest count and park rating remain intentionally unavailable until independently validated.
