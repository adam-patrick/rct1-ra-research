# Phase 2 runtime research

This directory contains analysis notes and read-only diagnostic scanners.
No game executable, DLL, scenario, or save file is copied here.

The state reader now exposes one empirically validated field: guest count as a
little-endian unsigned 16-bit value at the supported-build locator
`RCT.EXE base + 0x69c9f8`. Cash and park rating remain unavailable. See the
[Phase 2C guest-count report](../reports/rct1_retroachievements_phase2c_guest_count.md)
for evidence and limitations.
