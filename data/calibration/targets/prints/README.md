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
| [ref_2](ref_2.json) | 40–55 | `peg-targets-3x3-12.5mm-ref_2.png` | 2026-09-30 — **4.76 % undersize**, square **11.905 mm**; no anisotropy, shear or page drift |

## ref 1's ids collide with charuco_0001

ref 1 was generated before serials existed, starting at marker id 0.
`charuco_0001` uses **0–30**, so they overlap on fourteen ids and
**must never share a frame** — a frame holding both is readable only
because their markers happen to differ in size, which is luck.

Sheets from ref 2 onward start at `RESERVED_IDS` = 40 and get a fresh
block of sixteen each, so this cannot recur.

## Both prints so far came out about 4.7 % undersize

| | uniform scale | square |
|---|---:|---:|
| ref_1 | 0.95251 | 11.906 mm |
| ref_2 | 0.95238 ± 0.00050 | 11.905 mm |

They agree to **0.013 %**, and ref 1 came from gthumb while ref 2 came
from GIMP, so the application is not the variable.

**The control to check is not "Scale".** Both sheets were printed with
Scale 100 % and Print Scaling None. The dialog reported
`Width 8.106 in, Height 10.491 in, resolution 532.672 dpi` — and the
artwork is 4318 × 5588 px, which is 8.500 × 11.000 in at its own
508 dpi. The image is being laid down at 532.672 dpi to fit the
printable area, a scale of 0.95369.

**Before printing, check "Ignore Page Margins"** — the resolution
boxes are locked until you do — **then set the resolution to 508 so
Width reads 8.500 and Height 11.000.** `PAGE_MARGIN_MM` insets
everything 15 mm against an unprintable border of 5.0–6.5 mm, so
printing at true size clips only blank paper. See
[../../../../docs/planning/printing-the-target-at-size.md](../../../../docs/planning/printing-the-target-at-size.md).

**On a full-size sheet the diagonal will not fit the calipers.** The
layout was capped so the outer diagonal came to exactly 152.71 mm,
which is the whole of the jaw travel; at 4.7 % small it was a
comfortable 145 mm. Take the **four axis spans** (107.84 mm, 71 % of
travel) and skip the diagonals — they only ever bounded shear, none
has been detected on either sheet, and both read 0.35–0.50 % short at
95 % travel because the jaws splay.

A residue of about **0.131 %** is expected to survive even a correct
print — that is the gap between the dialog's predicted 0.95369 and
ref 2's measured 0.95238, and laser fuser shrinkage is its size and
sign. No setting removes it; it is measured, not fixed. so this printer's "fit to printable area"
is highly reproducible — which is useful to know and is still not what
anyone wants. Both sheets predate the `PRINT AT 100 %` line now
printed in the foot. **ref_3 should be printed with scaling off**, and
it should then come out near 1.000.

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

ref 2 paid the protocol back twice. Its between-sitting gaps reached
**0.437 mm, up to 5.5×** the within-sitting scatter; tranche 1 alone
reported a shear at 2.45σ that tranche 2 dissolved to 0.2σ; and the
scale moved from +0.052 % away from ref 1 to −0.013 %.

**Compute the error bar from the (span, sitting) group means, not
from the pooled readings.** Pooling ref 2's 24 as if independent was
1.5× too confident and put a non-existent column drift at 2.13σ.

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
