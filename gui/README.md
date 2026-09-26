# RCT1 read-only research GUI

This is a small Python/Tkinter frontend for the existing evidence-driven RCT1
research workflow. It detects `RCT.EXE`, derives the current module base from
`/proc/<pid>/maps`, validates the executable SHA-256, reads validated state,
and runs typed candidate scans in a worker thread.

## Run

From the repository root:

```sh
python3 -m gui
```

Tkinter is part of the standard Ubuntu Python installation used by this
project. No third-party GUI package is required.

The GUI only uses `/proc` metadata and Linux `process_vm_readv()`. There is no
memory-write API, value editor, freeze control, input automation, injection,
patching, or RetroAchievements communication.

## Workflow

Start RCT and pause it through the normal game UI. Connect the GUI, confirm the
supported build and snapshot of Cash/Guests/Park Rating, then run an Exact or
Unknown scan. After a controlled human-performed transition, pause again and
apply Changed/Unchanged/Increased/Decreased or known-delta filtering. Candidate
addresses are always displayed both absolutely and as module-relative offsets.
Use Add bookmark for a research candidate and Watch selected for occasional
manual refresh.

The `Continuous filter (1s)` option repeats a refinement filter after each
pass completes, with a one-second delay between passes. It never overlaps
scans, does not automate game input, and is available only for Changed,
Unchanged, Increased, Decreased, and known-delta filters. Clear the option or
press Cancel to stop the loop. Keep the game paused when using a filter as
validation evidence; continuous mode is a convenience for observation, not a
replacement for the controlled scan protocol.

Known locations are stored in [`research_metadata.json`](research_metadata.json)
under the supported executable hash. Candidate bookmarks use the same
build-scoped schema and never persist an absolute address as identity. Scan
sessions can be saved and loaded as JSON. Loading is build-scoped and candidate
addresses are treated as stale if the process has restarted. Runtime session
JSON files are ignored by Git because they contain local process IDs, addresses,
and experiment state; validated research metadata is kept in
`research_metadata.json` instead.

Unknown or unsupported executable hashes hide validated fields and refuse
scans. If RCT exits or restarts, the status panel reports the new process and
the old absolute addresses are not treated as valid.

## Tests

```sh
PYTHONPATH=. python3 -m unittest gui.test_rct1_gui -v
```
