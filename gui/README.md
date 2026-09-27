# RCT1 read-only research GUI

## Current GUI Features

- Detects the running `RCT.EXE` process and current module base.
- Validates the supported executable hash and displays build status.
- Reads validated Cash, Guest Count, and Park Rating fields.
- Runs Exact and Unknown scans with signed/unsigned 8-, 16-, and 32-bit types.
- Filters candidates by Changed, Unchanged, Increased, Decreased, and known delta.
- Supports background scans, cancellation, bounded results, and memory-safe table rendering.
- Supports module-relative scan ranges and candidate value history.
- Provides sortable candidate columns and read-only neighborhood inspection.
- Supports watches with persistent visual row highlighting.
- Supports editable, build-scoped bookmarks with labels, status, confidence, notes, and locator facts.
- Provides a live bookmark review window with refresh and edit actions.
- Supports continuous one-second refinement filtering.
- Saves and loads build-scoped JSON scan sessions.

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

Add bookmark opens an editor for the human-readable label, status, confidence,
and notes. Multiple selected candidates are edited and saved one at a time.
Existing bookmark metadata is prefilled when editing the same candidate; the
stable build-scoped ID and module-relative locator are retained.
The editor also shows read-only address, module-relative offset, type, and
build identity fields. Watch selected highlights watched rows in the table and
keeps the highlight through refreshes and sorting.

Use `Clear/New scan` to discard the current candidates, baseline, history, and
watched rows without closing the GUI. Bookmarks and the process connection are
preserved.

Use `Review bookmarks` to open a build-scoped bookmark window showing the
current runtime address, module-relative offset, type, current value, status,
confidence, and notes. The window supports refreshing values and editing the
selected bookmark.

Searches may optionally specify a module-relative range such as `0x69c000`
to `0x69d000`. The range applies to new scans and existing candidate/baseline
filters. Candidate rows retain a compact value history across filters, which
is useful for comparing scenario signatures. Click any table heading to sort
ascending; click it again to reverse the sort. The table shows the most recent
history samples for each displayed candidate.

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
