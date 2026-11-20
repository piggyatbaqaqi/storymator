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
