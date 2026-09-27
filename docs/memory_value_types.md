# Understanding Memory Value Types

This guide explains the basic type choices used while searching RCT1 memory.
It is a research aid, not a claim about any particular game field. A field's
actual type must be validated through controlled changes and fresh launches.

## 1. What `u`, `s`, and the number mean

The letter describes whether the value is unsigned or signed. The number is
the number of bits used to store it.

| Type | Bytes | Meaning | Range |
|---|---:|---|---:|
| `u8` | 1 | unsigned 8-bit | 0 to 255 |
| `s8` | 1 | signed 8-bit | −128 to 127 |
| `u16` | 2 | unsigned 16-bit | 0 to 65,535 |
| `s16` | 2 | signed 16-bit | −32,768 to 32,767 |
| `u32` | 4 | unsigned 32-bit | 0 to 4,294,967,295 |
| `s32` | 4 | signed 32-bit | −2,147,483,648 to 2,147,483,647 |

Unsigned values are normally used for quantities that cannot be negative:
guests, ratings, counts, prices, and identifiers. Signed values are appropriate
when negative values are meaningful, such as a balance represented as debt.

The type does not describe how important a value is. It only describes how the
same memory bytes are interpreted.

## 2. Why the size matters

The size determines how many bytes the scanner reads and how large a value can
be.

For example, a value of `500` can fit in all of these types:

```text
u8, s16, u16, s32, and u32
```

That does not mean all of them are correct. If the game stores the value in
four bytes, searching as `u8` may find one byte inside the field or an unrelated
value elsewhere.

A value above `255` cannot fit in a normal `u8`. A value above `65,535` cannot
fit in a `u16`, so `u32` becomes necessary unless the game uses a different
representation.

## 3. Signed versus unsigned interpretation

Signed and unsigned types use the same bytes but assign different meanings to
the high bit.

For two bytes:

```text
FF FF as u16 = 65,535
FF FF as s16 = -1
```

For four bytes:

```text
FF FF FF FF as u32 = 4,294,967,295
FF FF FF FF as s32 = -1
```

If a candidate changes from `100` to `99`, both signed and unsigned searches
will usually report the same address. The search result alone does not prove
whether the game considers the field signed. The field's allowed behavior and
boundary values matter more.

## 4. Byte order: little-endian values

The supported RCT1 build stores ordinary multi-byte integer values in
little-endian order. The least significant byte comes first.

The number `500` is hexadecimal `0x01F4`. As a little-endian `u16`, it is
stored as:

```text
F4 01
```

The number `1,000` is hexadecimal `0x03E8`, stored as:

```text
E8 03
```

The GUI and state reader interpret the bytes as little-endian integers. If a
value looks nonsensical, confirm the byte order before rejecting the candidate.

## 5. Current RCT1 examples

These fields have been validated for the supported `RCT.EXE` SHA-256 build:

| Field | Type | Module-relative locator | Notes |
|---|---|---|---|
| Guests | `u16` | `base + 0x69c9f8` | Nonnegative guest count |
| Park Rating | `u16` | `base + 0x69ce64` | Nonnegative displayed rating |
| Cash | `u32` | `base + 0x69c590` | Raw value is displayed dollars ×10 |

The cash field is a good example of the difference between a stored value and
a displayed value. If the game displays `$9,675.40`, the raw value may be
`96754` because:

```text
96754 / 10 = 9675.4 displayed dollars
```

The cash field is not automatically a signed or unsigned fact just because it
represents money. The observed field is currently handled as `u32`; loan or
balance fields must be validated independently.

## 6. Choosing a search type

Use the smallest plausible type that can represent the expected value, but do
not assume the smallest type is the game's actual storage type.

Useful starting rules:

- A small flag or percentage: try `u8` or `s8`.
- Guest count or rating: try `u16`/`s16`.
- Money, totals, scores, or values that may exceed 65,535: try `u32`/`s32`.
- A value that may be negative: include the signed interpretation.
- An unknown field: search multiple types, then validate the surviving address
  with controlled transitions.

Searching both signed and unsigned forms is often useful. The important final
question is not “which type produced a candidate?” but:

> Does this address track the visible game value correctly across controlled
> changes, pauses, scenarios, saves, and fresh processes?

## 7. Avoiding false conclusions

A candidate is not validated merely because its number matches once. Common
false positives include:

- the same number appearing in unrelated memory;
- a smaller byte inside a larger field;
- a pointer whose low bytes happen to match the target value;
- a display/cache value that is not the authoritative game state;
- a value that changes because the scenario is loading rather than because the
  target field changed;
- a candidate that works only in one process or one executable build;
- a signed interpretation that appears plausible only because the current value
  is below `32,768`.

Keep the following evidence separate:

- **Observation:** what the scanner or reader returned.
- **Hypothesis:** what the bytes might represent.
- **Validated finding:** repeated controlled evidence, including fresh-process
  checks, supports the interpretation for a specific executable identity.

## 8. Value fields versus pointers

An integer field stores a number directly. A pointer stores an address that
leads somewhere else.

For example:

```text
direct field:  80 00 00 00  -> value 128
pointer:       20 A0 A9 00  -> address 0x00A9A020
```

Treating a pointer as a value can produce a candidate that changes whenever the
allocator moves data. Treating a value as a pointer can lead the reader into
unrelated memory. The current validated Guests, Park Rating, and Cash fields
are direct integer reads; no pointer-chain claim is being made.

## 9. A practical validation workflow

For a visible value such as a loan amount:

1. Record the displayed value and pause the game normally.
2. Search plausible types, usually `u16`, `s16`, `u32`, and `s32` as needed.
3. Make one controlled in-game change, such as borrowing a known amount.
4. Pause again before filtering.
5. Use Changed, Increased, Decreased, or a known delta.
6. Repeat the same transition and confirm the candidate changes correctly.
7. Keep the process paused for unchanged checks.
8. Restart RCT completely and confirm the module-relative candidate again.
9. Test another scenario or valid state before calling it validated.

For a boolean such as park open/closed, record the exact raw values in both
states. Do not assume that `0` and `1` are the only possibilities; the game may
use a bit flag, enum, counter, or a related status field.

## 10. Search interpretation versus final documentation

The GUI's candidate type records how the scanner interpreted the bytes during a
search. It is useful evidence, but it is not automatically a final type
declaration.

Final documentation should record:

- executable SHA-256/build identity;
- module-relative locator;
- width in bits;
- signed or unsigned interpretation;
- endianness;
- scaling or display conversion;
- controlled transitions tested;
- fresh-process evidence;
- confidence and unresolved caveats.

The goal is a reproducible field definition, not merely a surviving table row.

## 11. Typed-memory viewer

The GUI now provides a read-only viewer for a selected candidate or bookmark.
It displays a bounded neighborhood of raw bytes and decodes them as:

- individual `u8`/`s8` values;
- little-endian `u16`/`s16` values;
- little-endian `u32`/`s32` values;
- optionally, big-endian comparison values and ASCII text.

For a byte sequence such as:

```text
E8 03 01 00
```

the viewer should make the possible interpretations visible at once:

```text
u16 LE: 1000, 1
u32 LE: 66536
```

The viewer must remain read-only. It should either update live while the game
is running or provide an explicit refresh action; a refresh timestamp and the
current PID/module base should be visible so stale observations are not
mistaken for current values. The first implementation focuses on a candidate
neighborhood/bookmark, not broad unbounded memory rendering. It provides a
manual Refresh action and an optional one-second live-refresh mode.

### Next viewer enhancement

Keep the current decoded table, but add a second presentation modeled on the
memory-grid view used by tools such as the screenshot reference:

- address column with grouped hexadecimal bytes;
- selectable 8-bit, 16-bit, and 32-bit display modes;
- visible bit positions and little-endian grouping;
- automatic live updates enabled by default while the window is open;
- a control to pause live updates, plus manual Refresh as a fallback.

The view must remain bounded to the selected candidate/bookmark neighborhood
and read-only. A pause/unpause flag should therefore change in the viewer
automatically when the game changes it, without requiring the user to press
Refresh.
