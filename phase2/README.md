# Phase 2 runtime research

This directory contains analysis notes and read-only diagnostic scanners.
No game executable, DLL, scenario, or save file is copied here.

The state reader now exposes two empirically validated fields: guest count at
`RCT.EXE base + 0x69c9f8` and park rating at `RCT.EXE base + 0x69ce64`, both as
little-endian unsigned 16-bit values. Cash remains unavailable. See the
[Phase 2C guest-count report](../reports/rct1_retroachievements_phase2c_guest_count.md)
and [Phase 2D park-rating report](../reports/rct1_retroachievements_phase2d_park_rating.md)
for evidence and limitations.
