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
