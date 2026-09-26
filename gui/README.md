# RCT1 read-only research GUI

This is a small Python/Tkinter frontend for the existing evidence-driven RCT1
research workflow. It detects `RCT.EXE`, derives the current module base from
`/proc/<pid>/maps`, validates the executable SHA-256, reads validated state,
and runs typed candidate scans in a worker thread.

## Run

From the repository root:

```sh
python3 -m gui.rct1_gui
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

Known locations are stored in [`research_metadata.json`](research_metadata.json)
under the supported executable hash. Candidate bookmarks use the same
build-scoped schema and never persist an absolute address as identity. Scan
sessions can be saved and loaded as JSON. Loading is build-scoped and candidate
addresses are treated as stale if the process has restarted.

Unknown or unsupported executable hashes hide validated fields and refuse
scans. If RCT exits or restarts, the status panel reports the new process and
the old absolute addresses are not treated as valid.

## Tests

```sh
PYTHONPATH=. python3 -m unittest gui.test_rct1_gui -v
```
