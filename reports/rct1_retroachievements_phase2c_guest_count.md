# RCT1 RetroAchievements Phase 2C — Guest Count Discovery

## Result

Guest count was **validated for the currently supported `RCT.EXE` build** as an unsigned 16-bit runtime field at:

```text
module base + 0x69c9f8
```

The observed absolute address was `0x00a9c9f8` in both tested processes. The two processes both mapped `RCT.EXE` at `0x00400000`, so the observed absolute address and module-relative expression agree. The field itself is in an anonymous private executable/read-write mapping, not in a file-backed `RCT.EXE` section.

Confidence: **Medium**.

The field tracked multiple displayed values and survived one complete process restart. A third fresh launch and additional scenarios/save transitions would raise confidence further, but the evidence is sufficient to expose this one field through the conservative state reader. No achievement or RA communication code was added.

## Evidence classification

### OBSERVATIONS

* The validated isolated Proton runtime loaded Forest Frontiers without changing the canonical Steam installation.
* The first process was PID `15840`, with module base `0x00400000`.
* The fresh process was PID `18279`, also with module base `0x00400000`.
* The first run displayed nonzero counts including `80`, `81`, and `82`.
* At `0x00a9c9f8`, repeated read-only `u16` samples held `80` for 12 consecutive one-second samples while the UI displayed `80 Guests`.
* During a live transition, repeated samples at the same address were:

  ```text
  81, 82, 82, 81, 81, 81, 81, 81, 81, 81, 81, 81, 81, 81, 81
  ```

  The screen captured after that watch showed `81 Guests`.
* The fresh process initially displayed `1 Guest`, and the same absolute address `0x00a9c9f8` read `1`.
* The candidate was present in exact-value candidate intersections for the first-run values `82` and `80` as an unsigned 16-bit value.
* A 192-byte neighborhood around `0x00a9c9f8` was readable in both runs. The candidate is 64 bytes from the start of the inspected neighborhood.
* The fresh-process mapping containing the address was:

  ```text
  0088a000-00c3e000 rwxp ... 00 00 0  [anonymous]
  ```

### HYPOTHESES

* The field is likely part of a live park/global structure in the unpacked runtime image because it is stable at the same module-relative expression and is surrounded by structured-looking small values.
* The nearby repeated zeroes and small flags may represent adjacent park state, but no structure layout is claimed from this neighborhood alone.
* The module-relative expression may remain stable because this build's runtime mapping layout is deterministic; more launches are needed before treating it as a signature-independent locator.

### VALIDATED FINDING

For the supported executable hash:

```text
bdfebd64383b231de0252fe0726523d1c45aa2c4da919c2d7ed8bfb7aaa05c76
```

read a little-endian unsigned 16-bit value at `current_RCT_module_base + 0x69c9f8`. In the two tested processes, that value matched the displayed guest count at observed nonzero states and changed in the same direction during live arrivals/departures.

This is not evidence that the address is valid for another executable build, another compatibility runtime, or an arbitrary scenario/save. Unknown hashes must remain unsupported.

## Experimental procedure

1. Launched the unchanged `scripts/launch_rct1.sh` isolated Proton runtime.
2. Loaded Forest Frontiers and opened the park through the normal UI.
3. Used the existing scanner and targeted value scanner without writing process memory.
4. Added only 1-byte support to `rct1_value_scan.c`; the existing utility already handled 2- and 4-byte exact scans.
5. Performed exact-value scans and candidate intersections at known displayed counts. Candidate set sizes included 21 `u8`, 79 `u16`, and 21 `u32` matches for a stable displayed `82` state.
6. Intersected exact candidate sets across displayed values. The promising address `0x00a9c9f8` survived as a `u16` candidate across `82` and `80` scans.
7. Read the candidate directly once per second for 12 stable samples and then for 15 live samples.
8. Closed the game window, confirmed the original PID ended, relaunched the same isolated runtime, and re-identified PID `18279` and base `0x00400000`.
9. Confirmed the same address read `1` while the fresh UI displayed `1 Guest`.

The full-range interactive scanner was useful for filtering but exposed a timing limitation: its initial exact scan over 41 ranges can take long enough for the simulation to advance. Targeted scans and direct repeated reads were used for the final validation evidence. The game's visible pause control/legacy key behavior was also inconsistent during automation, so stable-state claims rely on repeated UI captures rather than assuming a pause state from one input event.

## Locator classification

Classification: **stable module-relative offset observed; backing storage is dynamically mapped/anonymous**.

Not established:

* no pointer chain was required or identified;
* no signature scan was implemented;
* no claim is made that the file RVA equals the runtime location;
* no pointer/structure semantics are claimed beyond the observed neighborhood.

The state reader must derive the address from the current process's validated module base and reject unknown executable hashes in future code.

## Code and documentation changes

* `phase2/state_reader/rct1_value_scan.c`: added 1-byte exact scanning so the targeted utility covers 8-, 16-, and 32-bit positive integer representations.
* `phase2/state_reader/rct1_state_reader.c`: added a read-only `u16` guest-count read at `base + 0x69c9f8`; cash and park rating remain unavailable.
* `reports/rct1_retroachievements_phase2c_guest_count.md`: this evidence report.
* The generated scanner binaries and temporary experiment data remain outside Git/runtime ignored paths.

## Next experiment

Validate the same guest field in one more fresh launch and then move to park rating, while retaining timestamped/coherent snapshots. Cash should not be revisited until there is a controlled need; the previous `base + 0x766480` cash candidate remains explicitly unvalidated.
