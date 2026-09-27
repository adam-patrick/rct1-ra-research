# RetroAchievements / rcheevos integration spike

This directory is an isolated architecture proof-of-concept. It is deliberately
separate from the Tkinter GUI and does not unlock, submit, or authenticate
against RetroAchievements.

## Current proof

The executable validates the local `rc_client` lifecycle using the pinned
official rcheevos submodule at `v12.1.0` (`6755915`). It creates a client,
installs callbacks, disables Hardcore and background reads for this experiment,
processes a few frames plus an idle tick, and destroys the client cleanly.

It also has a `--rct-state` mode that discovers `RCT.EXE`, derives its current
module base (including Wine/Proton map paths containing spaces), and reads the previously validated Guest, Park Rating, and Cash
fields through `process_vm_readv`. That mode reports safely when RCT is not
running. The provider is read-only and the offsets are explicitly a temporary
module-relative bridge; they are not an official RetroAchievements address
map.

The default spike has:

- no RCT process requirement;
- no credentials;
- no network implementation;
- no game hash or invented RetroAchievements game ID;
- no achievement definitions or unlock submission.

## Build and run

```sh
cd ra_spike
make test
./rc_client_spike --lifecycle
# while the supported RCT.EXE build is running:
./rc_client_spike --rct-state
```

The dependency is a git submodule so the exact rcheevos revision is recorded
in the parent repository. Run `git submodule update --init --recursive` after a
fresh checkout.

## Planned stages

1. Prove the local lifecycle and callbacks.
2. Investigate authentication/session handling with credentials supplied only
   externally; missing credentials must remain a safe no-op.
3. Extend the current read-only RCT provider with coherent snapshots and
   validation against the live supported build.
4. Investigate official game identification and loading without inventing an
   RA game ID.
5. If safe and useful, evaluate local achievement logic without production
   unlock submission.

## Policy and integrity boundaries

**CURRENTLY ENFORCED:** no network, no credentials, Hardcore disabled for the
spike, no unlock submission, no writes to the RCT process, and no GUI coupling.

**POSSIBLE FUTURE CONTROL:** a separate read-only bridge may feed validated
RCT state into a future local evaluator. Any online mode would require an
explicitly reviewed integrity design and official RetroAchievements approval.

**OPEN QUESTION:** what official game identity, hash/load path, and API/session
contract would be accepted for this non-emulator executable?

**RA POLICY REQUIREMENT:** standalone support and Hardcore behavior are subject
to RetroAchievements requirements and approval; this repository does not claim
compliance or support.
