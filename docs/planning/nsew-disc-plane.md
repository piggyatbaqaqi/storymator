# N-S-E-W works, the disc is flat, and the plane does not move when you spin it

**Verdict.** Keep N-S-E-W. Three results, in order of how much they
change what to do next:

1. **Do not go to NNE-NNW-SSE-SSW.** It collapses the east-west
   spread from 109.6 mm to 59.3 mm and makes the disc normal
   **1.85× worse** on its weak axis. N-S-E-W is the best four-target
   layout that this disc and this sheet of paper allow.
2. **The disc plane does not change as the disc rotates.** Across
   nine rotations the recovered normal scatters by exactly what
   measurement noise predicts and no more, so there is nothing left
   to attribute to real movement. That means the plane can be
   measured **once, by averaging**, instead of per frame — which
   takes it from 87 % of the error budget to 31 %.
3. **There is a second ChArUco pattern in the scene**, bottom right,
   and it emits a valid marker id 5 that collides with board #1. It
   silently wrecked three of the nine frames. Remove it.

## What was recovered

35 of 36 board poses, from `data/calibration/rigs/test_rig01/*.png`,
using the four ArUco markers per board rather than the four
chessboard corners — marker corners raised the yield from 31/36 to
35/36 and span the whole board rather than its middle. Reprojection
0.78–1.35 px against the lens's own 0.707 px calibration rms.

Frame 7 lost board #3 entirely. Frames with only three targets are
worth noting separately: **three points define a plane exactly, so
they give no residual and no warning when one of them is wrong.**

## The layout, as actually built

| board | bearing from #0 | radius on the disc | mean out-of-plane |
|---|---:|---:|---:|
| 0 | — | 138.5 mm | +0.31 mm |
| 1 | 90.6° ± 0.2 | 164.9 mm | −0.45 mm |
| 2 | 183.0° ± 0.6 | 137.9 mm | +0.81 mm |
| 3 | 269.1° ± 0.3 | 176.6 mm | −0.75 mm |

The bearings are N-S-E-W to better than a degree. The **radii differ
by 38.6 mm**, and that is not carelessness — it is the paper. The
sheet lies **landscape**, 279.4 mm east-west by 215.9 north-south
(`v4k_01.json`'s `sheet` block), so it reaches 139.70 mm east and
west but only 107.95 mm north and south. A 50.96 mm cut piece has to
clear it, which pushes the **east and west** targets out to 164.9 and
176.6 mm and lets north and south sit in at 138.5 and 137.9. The disc
rim is at 209.6 mm.

**The disc is flat.** Those mean out-of-plane figures span 1.56 mm
peak to peak over a 419 mm disc. The foam board did its job.

## How well the plane is determined, and what it costs

Fitting the plane frame by frame, the normal scatters **0.399° rms**
over the eight four-target frames, worst case 1.47°.

The paper's corner is 176.7 mm from the disc centre, and the targets
sit at 138–177 mm, so the fit **interpolates** rather than
extrapolating — a real virtue of this layout. At a 29.7° view, a
normal error `δθ` puts a corner out of position by
`d · δθ · tan(29.7°)`:

| | normal error | lateral error at the paper corner | of the 0.804 mm budget |
|---|---:|---:|---:|
| one frame | 0.399° | 0.702 mm | **87 %** |
| worst frame | 1.47° | 2.58 mm | 321 % |
| **mean of 8 frames** | **0.141°** | **0.248 mm** | **31 %** |

One frame spends the whole budget on plane orientation alone and
leaves nothing for anything else. Averaging is what makes this
layout work.

## The error model, and why it can be trusted for the next layout

    normal error  =  σ_z / (√N · in-plane spread of the targets)

with `σ_z = 1.4 mm`, the measured per-target out-of-plane scatter.
For N-S-E-W at 155 mm this predicts **0.366°** against **0.399°**
observed. That agreement is what licenses the comparison below.

| layout | spread E-W | spread N-S | worst-axis normal | vs N-S-E-W |
|---|---:|---:|---:|---:|
| **N-S-E-W (now)** | 109.6 | 109.6 | 0.366° | **1.00×** |
| NNE-NNW-SSE-SSW | 143.2 | 59.3 | 0.676° | **1.85× worse** |
| NE-NW-SE-SW | 109.6 | 109.6 | 0.366° | 1.00× |
| six, every 60° | 109.6 | 109.6 | 0.299° | 0.82× |

NE-NW-SE-SW ties on paper and **cannot be built**: the paper's
corners reach 176.7 mm and the rim is at 209.5 mm, leaving 32.8 mm
for a 50.96 mm piece.

Two targets near north and two near south is the one thing to avoid.
A plane needs spread in *both* directions, and clustering trades away
the axis that was already only as good as the other.

## If it needs to be better than averaging gives

`σ_z ∝ Z² · σ_px / (f · L)`, so **target size is the only strong
lever**. Doubling the board halves the depth noise; six targets
instead of four buys 18 %. **North and south** have 101.6 mm of
radial room between paper and rim, against 69.9 mm east and west, so
that is where a larger piece fits — which is also, unhelpfully, the
direction in which extra spread is worth least.

That is the tension behind the NNE-NNW-SSE-SSW proposal: the room is
north and south, and the optical value is east and west.

## The phantom marker

In frames 1, 2 and 3 marker id **5** is detected twice: once on the
real board #1 at (928, 1178) at 70 px a side, and once at
(2894, 2306) at 39 px a side, on a printed pattern lying on the desk
at bottom right, half-crossed by a cable. Fitted naively it gave
board #1 a pose at Z = −4 mm with a reprojection error of 8737 px.

RANSAC removes it, but that is a workaround. `bin/make-peg-targets`'s
docstring already says why: *"two pieces carrying the same ids are
indistinguishable, and a detector that mixes them up produces a
confident wrong pose rather than a failure."* It was written about
two cut targets, and it applies just as well to anything else in the
room carrying the same dictionary.

**Clear the desk.** The hand, the cable, the phone and the sunglasses
cost nothing; a second ChArUco costs three frames — or rather, it
would have.

### The set does not need reshooting

Dropping frames 1–3 entirely and refitting from the six clean frames
moves the mean disc normal by **0.084°**, which is 0.147 mm at the
paper corner, 18 % of the budget. And the clean frames scatter
slightly *worse* — 0.458° against 0.399° for all nine — because there
are fewer of them.

| | four-target frames | normal scatter |
|---|---:|---:|
| all nine | 8 | 0.399° |
| frames 4–9 only | 5 | 0.458° |

Per-frame deviations run 0.37, 0.41, 0.59, 0.51, 0.16, **1.49**,
0.56, 0.12 degrees. The contaminated frames are not the outliers;
frame 6 is, and it has no stray marker in it. RANSAC repaired the
damage completely, so the nine frames stand. Fix the desk for the
next set, not for this one.

## Status

**Measured**: every pose, residual, radius, bearing and normal here,
from the nine frames, with `v4k_01`'s stored intrinsics and ref 1's
measured 11.906 mm square.

**Computed**: the error model and the layout comparison, the lateral
cost at the paper corner, and the radial room left by the paper.

**Assumed**: the disc is 419 mm across, from conversation, not
measured. A different diameter changes the radial-room arithmetic but
not the layout ranking.

**Not measured**: whether the plane survives *lifting* the disc, as
opposed to rotating it. Everything here says rotation is safe; it says
nothing about picking the disc up and putting it down.

**The cheapest test**: nine more frames at the same layout without
touching the disc between them, to separate the noise floor from
whatever the rotation itself contributes.

---

# The putty is the next thing to fix

Added 2026-09-30 from the operator's own measurements, which change
one number above.

The disc sits on a lazy susan on adhesive putty. The standoff from
desk to the underside of the foam, measured at five rotations, is
**16.69, 16.51, 18.63, 17.46, 16.49 mm** — mean 17.156, **sd 0.914,
range 2.14 mm**. The foam itself is 4.993 ± 0.015 mm and the
paperboard facing adds 0.560, so the working surface sits 22.71 mm
above the desk.

The foam is uniform to 15 µm. **The 0.914 mm belongs to the putty.**

As a tilt about the disc centre that is **0.250° rms**, and it is
rotation-dependent by construction. Set against the plane fit:

| | |
|---|---:|
| observed per-frame normal scatter | 0.399° |
| predicted by measurement noise alone | 0.366° |
| room left for real movement | **≤ 0.159°** |
| tilt implied by the putty measurements | 0.250° |

Those are the same order. The putty measurement is, if anything,
slightly larger than the plane fit will allow, so the wobble is real
but at the small end of what the calipers suggest.

**This revises the averaging claim.** A mean plane is only as good as
the wobble it averages over:

| | normal error | at the paper corner | of budget |
|---|---:|---:|---:|
| one frame | 0.399° | 0.701 mm | 87 % |
| mean of 8, if the wobble is zero | 0.141° | 0.248 mm | 31 % |
| **mean of 8, with the wobble** | **0.212°** | **0.373 mm** | **46 %** |

Still comfortably inside budget, but 46 % rather than 31 %, and the
difference is entirely a mounting problem rather than an optical one.

**Replace the putty with something rigid** — a full-face double-sided
bond, or a three-point kinematic seat that cannot compress unevenly.
It is the cheapest 0.25° available anywhere in this rig, and unlike
target size it costs no redesign.
