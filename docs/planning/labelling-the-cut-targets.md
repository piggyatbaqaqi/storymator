# The empty margin is for the scissors, not for the detector

**Verdict.** Move the labels inside the cut box and shrink them. A
label anywhere outside the board's own ink is **indistinguishable
from no label at all** — 40/40 detections, 9 µm of corner movement,
which is the repeatability of the measurement itself. The white frame
is cutting and gluing tolerance; the detector does not use it.

Proposed: **2.5 mm em**, baseline **2.0 mm** above the board's top
edge, inside the cut box. That is 1.95 mm of ink with 4.05 mm still
clear to the cut line, and it makes every printed piece exactly
53.5 mm square instead of 53.5 × 62.

## What was measured

One 3 × 3 board rendered at 508 dpi with the label `#0  ids 0-3
37.5 mm` at a swept clearance, resampled to the rig's 9 px/mm,
Gaussian blur σ = 1.1 px for defocus, contrast crushed to the 40–240
range for a dull print, and σ = 4 sensor noise. 40 seeds per cell.
Crossed with a 30° oblique view — the corpus's worst — and with the
board sitting on a grey-60 disc as well as on white.

| clearance from board edge | complete detections | worst corner shift |
|---|---:|---:|
| no label at all | 40/40 | — (9 µm repeatability) |
| 0.0 mm (label touching the edge) | 40/40 | 9 µm |
| 0.5 mm | 40/40 | 9 µm |
| 1.0 mm | 40/40 | 9 µm |
| 2.0 mm | 40/40 | 9 µm |
| 4.0 mm | 40/40 | 9 µm |
| **−2.0 mm (label over the board)** | **0/40** | — |

Identical in all four conditions: 0° and 30° tilt, white disc and
grey-60 disc. The 9 µm is the noise floor, not a response — every
non-overlapping cell returns the same number as the label-free
baseline.

## Why it does not matter, and where it starts to

ChArUco does not use the board's outline. It finds the four ArUco
markers, then interpolates the chessboard corners from them, and the
markers are *interior*: in a 3 × 3 board of 12.5 mm squares carrying
9.0 mm markers, the nearest marker edge is **1.75 mm inside** the
board's own boundary. So a label flush with the board edge is already
1.75 mm from anything the detector reads.

The failure is a killed marker, not a disturbed corner:

| clearance | font | markers found | corners returned |
|---|---:|---:|---:|
| 0.0 mm | 4.0 mm | 4 | 4 |
| −1.0 mm | 4.0 mm | 4 | 4 |
| **−2.0 mm** | **4.0 mm** | **3** | **2** |
| **−3.0 mm** | **4.0 mm** | **3** | **2** |
| −4.0 mm | 4.0 mm | 4 | 4 |
| −2.0 mm | 2.0 mm | 4 | 4 |

At −2 mm the 4 mm text reaches the top-middle marker and destroys it,
and three markers interpolate only two of the four corners. At −4 mm
the text has passed *below* the marker and it survives, which is luck
rather than design. A 2 mm font is too thin to break anything even
overlapping.

So the rule is not "keep the margin empty". It is **keep ink off the
markers**, and staying outside the board's edge buys that with
1.75 mm to spare.

## The real reason to keep clearance is the printer and the knife

Nothing above accounts for registration error, ink spread, or a
wobbling blade, none of which the synthetic sweep can model. 2.0 mm
of clearance is free — the band is 8 mm wide and the label needs
2 mm of it — so there is no reason to spend the 1.75 mm of headroom
the geometry already provides.

## What it costs today

The label is drawn 5.5 mm *above* the cut rectangle, so keeping it
means cutting a piece 53.5 mm wide and about 62 mm tall. At 4.0 mm em
the text is also **42.50 mm wide**, wider than the 37.5 mm board.

| em | width of `#0  ids 0-3  37.5 mm` | ink height | ≈ points |
|---:|---:|---:|---:|
| 1.5 mm | 15.95 mm | 1.15 mm | 4.3 |
| **2.0 mm** | **21.25 mm** | **1.50 mm** | **5.7** |
| **2.5 mm** | **26.55 mm** | **1.95 mm** | **7.1** |
| 3.0 mm | 31.85 mm | 2.35 mm | 8.5 |
| 4.0 mm (today) | 42.50 mm | 3.10 mm | 11.3 |

The operator asked for "about half", which is 2.0 mm. 2.5 mm is
recommended instead: it is still narrower than the board, still fits
the band with 4 mm to spare, and 7.1 pt survives a glance at arm's
length in a way 5.7 pt does not. The choice is the operator's; both
fit.

## A consequence worth taking at the same time

`LABEL_SPACE_MM = 8.0` reserves a strip at the top of the page for
labels that will no longer be there. With the labels inside the cut
box it is dead, and `layout()`'s `top` should be `PAGE_MARGIN_MM`
alone. It does not move the boards apart — the caliper cap of
70.482 mm is what binds — it only recentres the block 4 mm up the
page. The advertised spans do not change.

## Status

**Measured**: every detection figure here, by the sweep described
above — synthetic imagery, not rig captures. The text metrics, from
the same DejaVu face and size the renderer uses.

**Computed**: the 1.75 mm marker inset, from the board geometry
(12.5 mm squares, 9.0 mm markers).

**Not measured**: how a 2.0 or 2.5 mm label survives this printer's
ink spread, and whether a human can read it on a glued-down piece at
working distance. Both are answered by printing one sheet.

**The cheapest test**: print the revised sheet, cut one piece out,
and see whether the label is legible. If 2.5 mm is too small, the
band takes 3.0 mm without any other change.
