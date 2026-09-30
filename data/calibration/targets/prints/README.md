# Physical prints of the generated targets

Each record here is named for a **serial** issued by
[../serials.json](../serials.json). `bin/make-peg-targets` allocates
one per sheet, prints it at the foot of every cut piece, puts it in
the artwork's filename, and writes the stub in this directory for the
measurements to land in.

The serial names the *artwork*, so the discipline it needs is
**generate once, print once**. Print the same PNG twice and two sheets
answer to one number, differing in scale — which is the failure the
serial exists to prevent.

The artwork in `../` is a file; these are the pieces of paper. They
are separate records because **a print is not its artwork**: the same
PNG through a different printer, or the same printer with "fit to
page" left on, is a different physical object with a different scale,
and every measurement taken with it inherits that scale.

`charuco_0001` learned this the expensive way — its print came out
1.27 % oversize with a 0.15 % anisotropy between the axes, and the
0.15 % turned out to be the whole of a discrepancy that had been
blamed on the sensor. See `../README.md`.

| print | ids | artwork | measured |
|---|---|---|---|
| [ref_1](ref_1.json) | 0–15 ⚠ | `peg-targets-3x3-12.5mm.png` | 2026-09-30 — **4.75 % undersize**, square **11.906 mm**; no anisotropy, shear or page drift |

## ref 1's ids collide with charuco_0001

ref 1 was generated before serials existed, starting at marker id 0.
`charuco_0001` uses **0–30**, so they overlap on fourteen ids and
**must never share a frame** — a frame holding both is readable only
because their markers happen to differ in size, which is luck.

Sheets from ref 2 onward start at `RESERVED_IDS` = 40 and get a fresh
block of sixteen each, so this cannot recur.

## ref 1 came out 4.75 % undersize

"Fit to printable area" was on. A uniform 0.9503 leaves 5.37 mm side
and 6.95 mm top-and-bottom margins on a 215.9 × 279.4 mm page, which
is an ordinary unprintable border. The content is inset 15 mm, so a
100 % reprint clips nothing — **print the next one with scaling
off**.

ref 1 is still usable as long as its measured square size, 11.906 mm,
travels with every measurement taken from it. What it must not do is
be read off its own printed face, which still claims the design
nominals.

Note also that the spans printed on the sheet are between *interior
chessboard corners*, and a caliper jaw cannot seat on one. Measure
the **outside of the black squares** instead: 107.98 mm across and
down and 152.71 mm on the diagonal, at design scale.

## Measure before you cut

The nominals are printed on the sheet because they are only
measurable while the sheet is whole. Once the four pieces are
separated the longest baseline inside one of them is 17.68 mm, and
six readings on it carry 0.76 % against a print error worth about
1.27 %. Intact, the same six readings carry 0.11 %.

**All four spans — across on both rows, down on both columns — and
three readings in one sitting plus three in another.**

Not six in one go. On ref 1 the same `down` span came out 0.707 mm
higher in a second sitting, **thirteen times** the 0.055 mm scatter
within a sitting, and that systematic produced and then destroyed a
reported +0.273 % anisotropy. Readings taken back to back share a jaw
seating and a grip, and their agreement measures neither.

And all four spans, even though ref 1's two rows agreed to 0.013 mm
and its two columns to 0.005. The second pair is half the sample —
dropping it costs √2 on the scale and the anisotropy — and it is the
only check that all four pieces share one scale. An undetected
row-to-row drift at the 0.212 % detection floor would put two pieces'
depths 0.804 mm apart at Z ≈ 380 mm, which is the whole error budget,
and a plane fit turns that straight into a spurious tilt. After
cutting it is unrecoverable.

Readings go straight into the print's `measured` block. The reasoning is
in
[../../../../docs/planning/moveable-targets.md](../../../../docs/planning/moveable-targets.md)
and
[../../../../docs/planning/measuring-the-printed-target.md](../../../../docs/planning/measuring-the-printed-target.md).

Licence: as `../README.md`.
