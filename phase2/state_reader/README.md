# RCT1 phase 2 state tools

Build:

```sh
cc -O2 -Wall -Wextra -o rct1_state_reader rct1_state_reader.c
cc -O2 -Wall -Wextra -o rct1_value_scan rct1_value_scan.c
```

`rct1_state_reader` locates the process named `RCT.EXE`, derives the executable mapping base, and reads the validated unsigned-16 guest-count field at `base + 0x69c9f8`. Cash remains unavailable because the earlier `base + 0x766480` candidate was transient and not validated. The reader does not write to the target process, inject code, or call game functions; park rating remains unavailable until independently validated.
