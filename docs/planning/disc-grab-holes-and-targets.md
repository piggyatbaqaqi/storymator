# Keep the grab holes at 12 and 6, and slide the N and S targets sideways: it costs the plane nothing

*Analysis only, 2026-11-20. Short version: **the 17.5 in laminated disc has room for
exactly one 53.5 mm target on each compass point and nowhere else, and
moving the N and S targets 60 mm off the axis leaves the plane-fit
spread unchanged** — computed from the disc's CAD, not measured on a
built disc.*

The question: the traditional grab holes for turning a disc sit at 12
and 6 o'clock, and that is where the ChArUco targets go now. Which gives
way, and are ref 2's targets the right ones for this disc?

Geometry is from `cad/animation_disc_17_5in.scad` as of `c6b1afd`. Disc
coordinates have their origin at the optical centre of the 12F image
area, which the window is centred on. +Y is north, away from the bar.

## There is no room anywhere but the four compass points

The 12F sheet is 12.5 × 10.5 in. The image area runs 1.00–10.00 in from
the punched edge (operator, 2026-11-20). So the sheet spans
−139.7 to +127.0 mm in Y and ±158.75 mm in X, and it is not centred on
the disc. The bar's outline reaches 143.45 mm south.

| direction | clear radial room | to the step (through-hole limit) |
|---|---:|---:|
| N, sheet edge to rim | 95.2 mm | 81.8 mm |
| S, bar edge to rim | 78.8 mm | 65.3 mm |
| E / W, sheet edge to rim | **63.5 mm** | — |
| far corners (NE, NW) | **19.0 mm** | — |
| punched corners (SE, SW) | **10.8 mm** | — |

A ref 2 piece is 53.5 mm square. **The diagonals cannot take one**, so
the NE-NW-SE-SW layout is as unbuildable here as it was on the 16.5 in
disc (`nsew-disc-plane.md`). N-S-E-W remains the only four-target layout.

**A target and a 1 in grab hole cannot share the N axis radially.**
Sheet edge + 3 mm gap + 53.5 mm piece + 3 mm + 25.4 mm hole reaches
211.9 mm. The step is at 208.8 mm, and a through hole beyond the step
opens onto the desk rather than the desk hole. South has even less
room. So the hole and the target have to sit side by side, not in line.

## Sliding the target sideways is free; moving the hole off-axis is not better

The plane-fit error model from `nsew-disc-plane.md`, measured against
0.399° observed there, is

    normal error  =  σ_z / (√N · in-plane spread of the targets)

so only the targets' spread matters, per axis. Moving N to x = +60 mm
and S to x = −60 mm (anti-symmetric, so the centroid stays put):

| layout | rms spread X | rms spread Y |
|---|---:|---:|
| N and S on the axis | 133.3 mm | 116.7 mm |
| **N at +60, S at −60 (as drawn)** | **139.9 mm** | **116.7 mm** |

Y is untouched, because sliding sideways does not change a target's Y,
and X improves by 5 %. This is the opposite of the NNE-NNW-SSE-SSW
proposal, which put two targets near each pole and lost a whole axis.

**So keep the grab holes on the 12–6 axis**, which is where hands
expect them and where they turn the disc symmetrically, and move the
targets. Clearances as drawn:

| | clearance |
|---|---:|
| N hole to sheet edge | 25.3 mm |
| S hole to bar | 18.9 mm |
| either hole to its target | 20.6 mm |
| S target outer corner to the round-over | **1.1 mm** |

## The south target is the tight one, and it hangs on an unmeasured number

**Superseded reading below**: the punch offset is now measured, and
"the camera fits read 5.0–6.4 mm" misread a correction magnitude as an
offset. See *Revisited 2026-11-20* at the end.

The bar's position comes from the punched-edge-to-peg-line distance.
That distance is **nominal, never measured**: `SheetModel.punch_offset_mm`
is 12.0, and the camera fits in `landmark-detection.md` read
5.0–6.4 mm. At 6 mm the bar moves 6 mm south and pushes the S target
with it:

| punch offset | S target outer corner | flat top ends at |
|---|---:|---:|
| 12 mm (nominal, as drawn) | 218.0 mm | 219.1 mm |
| 6 mm (the camera-fit reading) | **223.5 mm** — over the edge | 219.1 mm |

Pulling the S target in to x = −45 mm fixes the rim (218.1 mm at 6 mm)
but leaves it 5.6 mm from the hole, against the 12.7 mm the CAD asserts.
**Measure the punch offset before cutting the channel.** It moves the
bar, the S target and the hole clearances together, and the SCAD's
asserts will refuse a layout that no longer fits.

## Keep ref 2's 3 × 3 pieces; this disc caps target size

**Superseded in part below**: the cap applies to *square* pieces. Pieces cut
to the free surface's shape are about twice the size. See *Revisited
2026-11-20 (target design space)* at the end.

Target size is the strong lever (`σ_z ∝ 1/L`, `nsew-disc-plane.md`),
and this disc caps it:

| piece | E / W (63.5 mm room) | N | S |
|---|---|---|---|
| ref 2 3 × 3, 53.5 mm | fits, 5 mm spare | fits | fits, 1.1 mm to the round-over |
| 4 × 4 at the same square, ~63.6 mm | **no** | fits, 0.6 mm spare | **no**, reaches 233 mm |

A bigger board would fit only at N, which improves one target out of
four. **Stay with 3 × 3 at ref 2's 11.905 mm square.** Keep marker ids
at 40 and above so `charuco_0001` can share the frame (`test-rig02.md`
proved that in practice). A fresh print for this disc takes the next
free block in `data/calibration/targets/serials.json`, not ref 2's
ids again.

## The camera has to go higher for 12F

This is computed from `v4k_01`'s half-angles (±31.9° long, ±25.0° short,
calibrated at focus 134, which has since moved), with the camera
centred over the optical centre:

| to frame | needs |
|---|---:|
| the 12F sheet alone | H ≥ 300 mm |
| sheet + all four targets, bar at 6 o'clock | **H ≥ 429 mm** |
| the same, disc turned 90° | H ≥ 462 mm |

The S target binds, on the short axis. `test_rig02` had the camera
340 mm up, so the 7 in risers are needed, not optional.

## Two smaller points

**Through holes leak light.** With the backlight on, each grab hole is
a bright 25 mm disc about 20 mm from a target. Nothing measured says
that disturbs ChArUco detection. `grab_through = false` makes them
½ in blind finger cups, which also stop debris falling into the desk.

**Fingers end up near the targets.** 20.6 mm is enough to keep fingers
off a target while turning the disc, but graphite migrates. Watch
detection yield on N and S over the first week; a target that starts
dropping markers wants replacing, not cleaning.

## What follows

1. Measure the punched-edge-to-peg-line distance on a 12F sheet and set
   `punch_offset` in the SCAD. Everything south of centre depends on it.
2. Cut the grab holes on the 12–6 axis. Put targets at E and W beside
   the sheet, N at +60 mm, and S at −60 mm (or wherever the asserts allow
   once (1) is known).
3. Print a fresh 3 × 3 sheet in the next free id block.
4. Plan on the camera at ~430 mm or above, centred, before
   recalibrating.

## Status

**Operator-supplied**: the image-area placement on the sheet (1.00–10.00 in
from the punched edge).

**Nominal, never measured**: the 12 mm punch offset (and the camera fits
disagree with it); the bar being centred across its width on the peg
line; the bar outline, which is carried over from `acme_12f_disc-3.scad`.

**Measured elsewhere, reused**: ref 2's 11.905 mm square; the plane-error
model, checked against 0.399° in `nsew-disc-plane.md`; `v4k_01`'s
half-angles.

**Computed**: every clearance, spread and camera height above, from the
CAD and a scratch script. Nothing here is measured on a built disc.

**Assumed**: a 1 in grab hole, and a 3 mm gap between a target and the
paper or bar.

**The cheapest test**: one 12F sheet on the bar, a ruler from the
punched edge to the round peg's centre. That one reading settles where
the bar, the S target and the S hole go.

---

# Revisited 2026-11-20: the bar is not centred on its pegs, and the punch offset is 8.73 mm

The operator measured on a 12F sheet seated on `honbay_0001`, with a ruler:

| | measured | was |
|---|---:|---:|
| punched edge to peg centres | **11/32 in = 8.73 mm** | 12.0 mm, nominal |
| bar's punched-side edge beyond the paper edge | **1/32 in = 0.79 mm** | — |
| peg line to the bar's punched-side edge | **12/32 in = 9.53 mm** (derived) | 15.75 mm, assumed |

The reading is good to about ±1/64 in (0.4 mm). That is coarse against the
0.268 mm punch tolerance, but the 12 mm nominal was 3.3 mm off.

## The pegs sit 6.2 mm off the bar's centreline

**Superseded reading below**: the bar is 20 mm wide, not 31.5, and its
pegs are centred to 0.2 mm. See *Revisited 2026-11-20 (later)*.

Checked against what is known about the bar:

| check | result |
|---|---|
| round peg (6.440 mm, slip test) inside the bar | its flank is 6.30 mm from the edge: fits |
| rect pegs (3.197 / 3.087 mm thick) | flanks 7.9 mm from the edge: fits |
| **bar centred on the peg line, 31.5 mm wide** | **no**: 9.53 mm on one side, 21.98 mm on the other |
| `bar_reference.jpg`, eyeballed from an oblique view | pegs about a third of the way across; agrees in direction |

Nothing in the measurements contradicts itself. What fails is the
assumption, carried since the first disc CAD (`1dfeeda`), that the bar is
centred across its width on the pegs. **The 31.5 mm width itself has no
recorded measurement**, so the 21.98 mm figure is only as good as it.
The same photo suggests **the screw holes are not on the peg line** but
nearer the punched-side edge, which rev 3 also assumed away. Both want
a caliper reading.

**This also misplaces rev 3's slot.** `acme_12f_disc-3.scad` centres its
31.5 mm slot on `peg_offset`, so a bar seated in it puts the pegs 6.2 mm
toward the bar's punched-side edge, not at `peg_offset`. On that disc the
offset matters only for where the sheet lands, not for registration,
which reads the pegs. Not changed here.

## The camera-fit "punch offset" was never an offset

`Pose.punch_offset_mm` in `acme/fit.py` is
`norm(correction[:2, 2])`: the length of the rigid correction from the
outline fit to the pegs. It is not a distance from the edge. The
5.0–6.4 mm in `landmark-detection.md`, quoted above as a rival offset,
is how far the 12 mm model was off on the 8.5 × 11 Canson corpus. If
all of that were perpendicular, the Canson offset would be about
5.6–7.0 mm. That is a different paper and punch from this 12F sheet,
so the two readings neither confirm nor contradict each other.

## What it does to this disc

| | nominal 12 mm, bar centred | **measured** |
|---|---:|---:|
| peg line, south of centre | 127.70 mm | **130.97 mm (5 5/32 in)** |
| bar, south edge | 143.45 mm | **140.49 mm (5 17/32 in)** |
| bar over the 9 in window | 2.35 mm | **5.31 mm** |
| bar over the acrylic recess | 12.27 mm | **15.23 mm** |
| bar pilot (if on the peg line) to recess wall | 3.48 mm | 6.75 mm |
| S target outer corner (flat top ends 219.1) | 218.0 mm | **215.2 mm** |
| S hole to bar | 18.9 mm | 21.8 mm |
| camera height to frame all four targets | 429 mm | 422 mm |

**The S target's squeeze is gone**: it now has 3.9 mm to the round-over,
not 1.1. The verdict above stands unchanged: holes at 12 and 6, N and S
targets 60 mm off the axis.

The bar now covers 5.3 mm of the image area's punched-side edge. It lies
under the paper and is opaque, so that strip cannot be backlit by any
disc. It is a property of this sheet on this bar.

## What follows from this

1. **Caliper the bar's width and where its screw holes sit across it.**
   Until then, rout the channel from a template checked against the bar,
   and transfer-punch the holes through the seated bar.
2. **`SheetModel.punch_offset_mm` should become 8.73 for 12F paper.** That
   is a code change and needs its own TDD cycle. Not done here.

## Status

**Measured**: the peg offset and the bar-edge overhang, with a ruler, on
one 12F sheet (operator, 2026-11-20).

**Not measured**: the bar's 31.5 mm width and 234 mm length, and the
across-bar position of its screw holes.

**Computed**: the table above, from the CAD as of `af7ea38`.

**The cheapest test**: calipers across the bar at both ends and at the
round peg, plus edge to centre of each screw hole. Five readings settle
the channel and the pilots.

---

# Revisited 2026-11-20 (later): the bar is 20 mm wide and centred, so the off-centre finding is retracted

Calipers on `honbay_0001`, operator: width **19.92 / 19.99 mm**, pegs
centred across it to **0.13–0.21 mm**. Details and the readings are in
`data/calibration/pegs/honbay_0001/README.md`, *The bar's outline*.

## What failed

The 6.2 mm offset above was arithmetic on a 31.5 mm width that had come
in with the first disc CAD and was never measured. The two ruler
readings were fine. **The only unmeasured number in the chain was the
one that produced the finding**, and the earlier section named it as
unmeasured and concluded anyway. A finding that rests on a width should
wait for the width.

## The punch offset, three ways

| source | punched edge to peg line |
|---|---:|
| ruler, directly (operator) | 11/32 in = **8.73 mm** |
| caliper half-width 9.98 − the 1/32 in overhang (ruler) | **9.19 mm** |
| "standard" 3/8 in, from a web summary the operator pasted | 9.525 mm |

The two readings on this paper agree to 0.46 mm, inside two ruler
readings of ±1/64 in each. The quoted standard is 0.3–0.8 mm above them.
The same summary allows ±1/32 in between paper brands, which covers
this. The CAD keeps the direct 8.73. The bar's edge then lands 1.27 mm
past the paper edge, and an assert holds that within 0.04 in of the
1/32 in reading.

## The pasted summary contradicts itself, and the operator's image area

It gives peg line to Academy centre **5.75 in** and centre to top edge
**4.375 in**. A 9 in image reaches 4.5 in above centre, so it would run
**1/8 in off the top** of a 10.5 in sheet. The summary says "inside the
top edge with 1/8 in to spare". Its own numbers say otherwise.

It also disagrees with the operator's image area, 1.00–10.00 in from the
punched edge. That puts the centre 5.50 − 0.34 = **5.16 in** above the
peg line, against the summary's 5.75. **The 0.59 in (15 mm) difference
moves the whole window relative to the pegs.** The CAD follows the
operator. If a printed 12F field guide or the paper's own field marks
say otherwise, they should decide, not the summary.

## What it does to this disc

| | 31.5 mm bar, off-centre | **20 mm bar, centred** |
|---|---:|---:|
| channel, south of centre | 108.99–140.49 mm | **120.97–140.97 mm** |
| bar over the 9 in window | 5.31 mm | **none, 6.7 mm clear** |
| bar into the acrylic recess | 15.23 mm | **3.25 mm** |
| channel length | 234 mm | **249.65 mm** (derived) |
| window screws | ±5.3 in | **±5.5 in** (5.3 now meets the longer bar) |
| S target outer corner (flat top ends 219.1) | 215.2 mm | 215.7 mm |
| S hole to bar | 21.8 mm | 21.3 mm |
| camera height for all four targets | 422 mm | 423 mm |

The bar no longer covers any of the image area. It still enters the
acrylic recess by 3.25 mm, so the channel crosses the seam. Trimming
the acrylic's south ledge to clear it would leave 0.7 mm of wood
between recess and channel, which is worse than crossing. The
grab-hole verdict stands.

**Retracted from the previous section**: the bar covering 5.3 mm of the
image area; rev 3's slot "misplacing its pegs by 6.2 mm" (it is still
wrong, 11.5 mm too wide and probably 16 mm too short for this bar, as
the honbay README records).

## Status

**Measured**: bar width, peg centring, hole-to-end distance (calipers);
peg-line offset and bar overhang (ruler).

**Derived**: bar length 249.65 mm, from rev 3's hole spacing.

**Unresolved**: where the image area sits relative to the pegs. The
operator's 1.00–10.00 in and the pasted summary differ by 0.59 in.

**The cheapest test**: measure the bar end to end, and read the image
area off a printed 12F field guide pegged on the bar.

---

# Revisited 2026-11-20 (target design space): four big lobe-shaped boards get almost everything paving would

*Analysis only. Short version: **flanking the grab holes with pairs is a
modest gain (35 % to 28 % of budget per frame), paving is a large one (to
14 %), and four boards each cut to fill one free area get 15 %, nearly all
of paving's gain, with four poses and no inter-tile survey.** All figures
are the plane-fit model evaluated at this disc's CAD as of 95f9ec2.
Nothing is measured on this disc.*

The operator asked for pros and cons of two layouts: a target on either
side of each grab hole, and continuous ChArUco paving outside the window.

## The model, and its one input that is not measured here

As in `nsew-disc-plane.md`: worst-axis normal error = σ_z / (√N · rms
spread), with σ_z ∝ 1/L for a board of size L. σ_z = 0.90 mm is that doc's
projection for a camera centred at 433 mm. It is computed, not measured,
and it sets the absolute column. **The ratios between rows do not depend
on it.** Paper-corner error uses that doc's 0.296 mm per 0.236°, against
the 0.804 mm budget. Scoring script: a scratch file, not in the repo; every
input it used is listed here.

## The free surface is four lobes, not a ring

The flat top ends at 219.1 mm. Taking out the sheet plus a plain band, the
bar channel plus 3 mm, each grab hole plus 12.7 mm, and the last 3 mm
before the round-over leaves:

| lobe | 3 mm band | 10 mm band | extent (3 mm band) |
|---|---:|---:|---|
| N | 18 960 mm² | 16 575 mm² | x ±174, y 128 to 216 |
| S | 14 041 mm² | 12 316 mm² | x ±164, y −140 to −216 |
| E, W each | 10 628 mm² | 8 766 mm² | 54 mm deep, y −139 to 127 |
| total | 54 257 mm² = 19.0 ref-2 pieces | 46 423 mm² = 16.2 pieces | |

The lobes join only at the far corners, through 9.8 mm (3 mm band) or
2.8 mm (10 mm band). At the punched corners there is 1.6 mm, or nothing.
**"Continuous" paving is four crescents** with a thin bridge across the
north corners.

## Scores

| layout | N | rms spread X / Y | worst-axis normal | paper corner | of budget |
|---|---:|---:|---:|---:|---:|
| **now**: N, S 60 mm off axis; E, W | 4 | 139.9 / 115.9 mm | 0.222° | 0.279 mm | **35 %** |
| **A**: a pair flanking each hole; E, W | 6 | 116.9 / 133.8 | 0.180° | 0.226 mm | **28 %** |
| A without E, W | 4 | 52.1 / 163.8 | 0.494° | 0.620 mm | **77 %** |
| **B**: paving, 3 mm band, as 19.0 independent pieces | 19.0 | 132.0 / 137.8 | 0.090° | 0.113 mm | **14 %** |
| B, 10 mm band | 16.2 | 131.6 / 141.4 | 0.097° | 0.122 mm | 15 % |
| **C**: four lobe boards, one pose each, L_eff 116 mm | 4 | 129.9 / 119.4 | 0.099° | 0.124 mm | **15 %** |
| C, 10 mm band, L_eff 108 mm | 4 | 132.8 / 122.3 | 0.105° | 0.131 mm | 16 % |

For A, each piece's inner edge is 12.7 mm from its hole, so the piece
centres sit at x = ±52.1 mm. Outer corners: 199.7 mm (N) and 212.8 mm (S).
That is inside the E and W pieces' 216.9 mm, so A needs **no extra camera
height**. B and C reach the 216 mm edge of the free area. That too is
inside the 217 mm already framed, but with no slack.

B is scored as if its area were that many independent ref-2 pieces. A
single rigid model over the whole paving would do better, but only if the
position of every tile is known. C extrapolates σ_z ∝ 1/L from square
boards to crescents, taking L = √area. A crescent's tilt about its long
axis is weaker than a square's, which this ignores.

## A: pairs flanking the grab holes

* **For:** 1.24× better than now. Six targets means losing one to a hand
  or a cable still leaves five and a residual. Three targets fit a plane
  exactly and give no warning when one is wrong. The holes stay on the
  12–6 axis. No extra camera height, and it is ref 2's piece, already
  understood.
* **Against:** fingers land 12.7 mm from four targets every time the disc
  turns. That means smudges, edge wear, and a hand resting in the hole
  during a capture. Two more pieces to cut and measure. **Do not drop E
  and W to pay for it**: four targets at the poles is the
  NNE-NNW-SSE-SSW trap again, at 77 %.

## B: continuous paving

* **For:** the best number, 2.5× better than now. It degrades gracefully:
  a hand, tape, a cable or a bigger sheet hides squares, not targets. It
  works at any rotation, and with partial framing. It gives a dense
  out-of-plane map of the disc right up to the paper edge, an independent
  measurement of lamination warp.
* **Against:**
  * **It isn't continuous** (above).
  * **It can't be printed as one piece on anything here.** The N lobe
    alone is 348 mm wide. Large-format prints have unmeasured scale, the
    lesson of the 4.0624 in bar. Tiles avoid that, but then each tile is
    either its own board, which is what the score assumes, or its
    position has to be surveyed. A bundle adjustment across many
    rotations could do the survey, but that is software nobody has
    written.
  * **About 190 markers** at ref 2's 11.905 mm square. That needs a
    4×4_250 or 5×5 dictionary and an id block well clear of
    `charuco_0001`'s 0–30. Larger dictionaries have smaller minimum
    Hamming distance, so they produce more false detections.
  * **The pattern runs right up to the sheet's edge**, where the outline
    detection needs contrast. A 10 mm plain band costs one point of
    budget (14 % to 15 %) and should be kept.
  * **It's under the animator's hands everywhere.** It needs a matte
    laminate, because gloss throws glare into the camera. It is also a
    busy field around the drawing at the desk.

## C, the suggestion: one board per lobe

Cut four boards to the lobe shapes, with the grab holes as cut-outs (a
ChArUco board tolerates missing squares). That keeps **15 % of budget
against paving's 14 %**: almost all of the gain comes from size, not
from covering every scrap. Each board has its own pose, so no inter-board
survey is needed. Each fits one sheet of paper: N 348 × 88 mm and S
328 × 76 mm fit legal (356 mm); E and W, 266 × 54 mm, fit letter. Each
board still tolerates partial occlusion within itself.

Against: N and S are longer than a letter flatbed (297 mm). Measuring
their printed scale needs a legal flatbed, or the board split in two. An
E or W board is only 54 mm deep, so it gains little over a square in that
direction; its gain is mostly length.

## And the option that costs nothing

`nsew-disc-plane.md` measured the plane **not moving with rotation**, so it
can be averaged over frames. Eight frames of the current layout give
35 % / √8 ≈ **12 %**, better than any layout per frame. **Layout only
matters if the plane has to be fitted per frame.** That was measured on
test_rig01's foam disc, not this one, which will ride on a 1/16 in step
clearance in the desk hole and may rock.

## What follows

1. **First, measure whether this disc's plane holds across rotations.**
   Nine frames, the same procedure as `nsew-disc-plane.md`, with the four
   current pieces. If it holds, keep the current layout and average:
   nothing to build.
2. **If it rocks, go to C**, four lobe boards with a 10 mm plain band
   round the sheet. That is the same gain as paving with four poses, four
   prints and no survey software.
3. **A is the fallback** if C's prints can't be measured: six ref-2-style
   pieces, keeping E and W.
4. **Don't pave tile-by-tile** unless survey-by-bundle-adjustment is
   written for some other reason.

## Status

**Measured** (elsewhere, not on this disc): the model's agreement with
0.399° observed on test_rig01; the plane's stability under rotation, on
the foam disc.

**Computed**: every row above, from the CAD and σ_z = 0.90 mm.

**Extrapolated**: C's σ_z ∝ 1/√area for non-square boards.

**The cheapest experiment**: nine rotations of this disc in the desk with
the current four pieces. If the normal scatters by noise alone, layout is
moot.

