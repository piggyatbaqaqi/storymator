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

---

# Revisited 2026-09-30: the putty is exonerated, and one target is doing all the damage

Nine frames with **nothing moved** — not the camera, not the disc —
`ref1_nsew_noise_detection-[1-9].png`. This is the control named as
"the cheapest test" above, and it changes two conclusions.

## The putty does not matter. Retracted.

| set | four-target frames | plane normal scatter |
|---|---:|---:|
| disc rotated between frames | 8 | 0.399° ± 0.107 |
| **nothing moved** | 9 | **0.379° ± 0.095** |

They are the same. The quadrature excess attributable to rotation is
0.125°, and the uncertainty on each figure is larger than that, so it
is not significant.

**The two sets were not lit identically** — the static set was shot
without the hand-held phone. That is a confound, and it has to be
checked rather than waved away:

| | rotated (phone) | static (no phone) |
|---|---:|---:|
| mean grey | 106.9 | 71.2 |
| contrast, p95−p5 | 247.9 | 181.2 |
| saturated pixels | **1.101 %** | **0.000 %** |
| pose reprojection rms | 1.057 px | **1.028 px** |

It cuts the safe way. The phone raised brightness and contrast but
blew out 1.1 % of the frame, and pose quality was *slightly worse*
with it. Scaling the static scatter up to matched lighting —
0.379 × 1.057/1.028 — gives 0.390°, and the excess attributable to
rotation shrinks to 0.084°. The retraction survives its own
confound.

**This retracts the previous section.** The 0.914 mm of standoff
scatter is real and the foam's 15 µm uniformity does mean it belongs
to the putty, but it does **not** reach the disc's plane. Whatever the
putty is doing, it is not tilting the working surface by anything the
targets can see. Leave the mount alone; the quarter-degree I said was
cheaply available is not there.

The reasoning that failed is worth keeping: *a standoff that varies
with rotation must tilt the disc* assumed the measurement point and
the tilt axis were related. Five height readings at one place say
nothing about the plane through the whole disc, and the plane is what
was actually wanted.

## Almost all the noise is one target

Leaving each board out in turn, with nothing moving. This is measured
**entirely within the static set**, so the lighting difference above
cannot reach it:

| plane fitted from | normal scatter |
|---|---:|
| all four | 0.379° |
| without N | 0.747° |
| without E | 0.940° |
| without S | 0.806° |
| **without W** | **0.139°** |

Dropping any target but W makes things worse, which is what losing
spread should do. **Dropping W improves the fit 2.7×.**

The per-axis scatter with nothing moving says the same:

| | Z | apparent marker | angle to the line of sight | σ_z |
|---|---:|---:|---:|---:|
| N | 397 mm | 46.9 px | 41.0° | 1.017 mm |
| **E** | **314 mm** | **74.5 px** | **12.0°** | **0.274 mm** |
| S | 397 mm | 46.8 px | 39.3° | 0.907 mm |
| **W** | **482 mm** | **31.3 px** | **51.9°** | **6.744 mm** |

W is 168 mm further away than E, viewed at 52° instead of 12°, and
its markers are 31 px where E's are 74. Its depth is **25× noisier**.
It is also visibly out of focus, which `focus_absolute` 134 cannot
help: one focus setting cannot serve a 168 mm depth range.

σ_z is 2.236 mm over all four and **0.733 mm without W**.

## So the limit is where the camera is, not how the targets are laid out

The camera sits about 380 mm up, and the disc rim is 209.6 mm from
centre, so the rim subtends ±28.9°. Against a 29.7° plane tilt that
puts the near edge at 0.8° and the far edge at **58.6°**. The disc is
simply too wide for this working distance to see evenly.

| camera | rim subtends | near edge | far edge |
|---|---:|---:|---:|
| 380 mm up, 29.7° tilt (now) | ±28.9° | 0.8° | **58.6°** |
| 500 mm up, same tilt | ±22.7° | 7.0° | 52.4° |
| 700 mm up, same tilt | ±16.7° | 13.0° | 46.4° |
| **380 mm up, centred** | ±28.9° | **28.9°** | **28.9°** |

Backing the camera off barely helps and costs pixels as `Z²`.
**Centring it over the disc is what equalises the four targets**, and
it removes the weak link rather than shrinking it.

## What this is worth

| | normal error | at the paper corner | of the 0.804 mm budget |
|---|---:|---:|---:|
| per frame, as shot | 0.399° | 0.701 mm | 87 % |
| **per frame, without W** | **0.139°** | **0.244 mm** | **30 %** |
| mean of 9, as shot | 0.126° | 0.222 mm | 28 % |

A single frame with an evenly-seen set of targets is as good as the
mean of nine is now. That is the difference between needing a
calibration pass and reading the plane off the working frame.

## Status

**Measured**: all of it, from nine static frames, 36/36 poses at
1.03 px rms. No stray marker — the second ChArUco is gone from the
scene and the yield went from 35/36 to 36/36.

**Confounded**: the cross-set comparison only. The static set had no
phone light. Quantified above; it cuts the safe way.

**Computed**: the significance test, the obliquity table and the
budget.

**Retracted**: that the putty wobble contributes to the plane error.

**Not measured**: whether centring the camera actually delivers the
predicted evenness. It is a geometric argument, not an observation.

**The cheapest test**: move the camera over the disc centre and shoot
nine more static frames. If σ_z comes back near 0.7 mm for all four
targets, the geometry is settled and N-S-E-W is finished business.

---

# Raising the camera: worth about 2×, and it costs a lens calibration

The camera cannot be centred where it is. Recovered from the static
set, it sits **321.1 mm above the disc plane and 240.0 mm off centre**,
400.9 mm from the disc's middle, with the plane at 29.6°. Centred at
that height the targets fall outside the frame, which is what the
operator found: **+4.5 in** to see all four, **+7 in** to keep them
through a 90° rotation.

The short axis is what binds — ±25.0° against ±31.9° on the long one:

| to fit | needs | from now |
|---|---:|---:|
| N/S target, paper-limited, r = 133.4 mm | H ≥ 286 mm | −1.4 in |
| E/W target, paper-limited, r = 165.2 mm | H ≥ 354 mm | +1.3 in |
| W as actually placed, r = 202.1 mm | H ≥ 433 mm | **+4.4 in** |

which agrees with the measured +4.5 in for a single rotation.

## What it buys

Calibrating `σ_z = k · Z² / cos θ` on the three in-focus boards gives
`k = 4.01 × 10⁻⁶` (W fits 17.9 × 10⁻⁶, four times worse, which is the
defocus the model cannot express):

| | Z | obliquity | σ_z | normal | incidence | at the paper corner | budget |
|---|---:|---:|---:|---:|---:|---:|---:|
| now, off-centre | 314–482 | 12–52° | 2.24 mm | 0.379° | 29.7° | 0.666 mm | **83 %** |
| centred, +4.5 in | 462 | 19.6° | 0.91 | 0.238° | 22.1° | **0.297 mm** | **37 %** |
| centred, +7 in | 522 | 17.3° | 1.15 | 0.300° | 19.5° | 0.327 mm | 41 % |

Centring wins twice: it equalises the targets *and* it shrinks the
incidence angle that turns a depth error into a lateral one, from
29.7° to about 20°. Raising works against it — `σ_z ∝ Z²` — which is
why +7 in is slightly worse than +4.5 in and why backing off further
would lose.

**Take the +7 in.** The whole question is the plane *in every
orientation*, and 4 % of budget is a cheap price for not losing a
target whenever the disc turns.

## The cost nobody has priced yet

Z at the targets goes from 314–482 mm to about **522 mm**.
`focus_absolute` is pinned at **134**, set for roughly 380 mm, and the
W target at 482 mm is already visibly soft. At 522 mm the whole frame
would be.

So the camera has to be refocused — and `v4k_01.json` was calibrated
at focus 134, with its provenance naming `focus_absolute` among the
controls that must be pinned *because the intrinsics move with it*.

**Raising the camera invalidates the lens calibration.** Budget 48
frames of `charuco_0001` at the new height, and a new
`camera_settings.gpfl`, before any of the numbers above can be
believed.

## Do not build the height out of M3 standoffs

The camera-to-base screw is M3 × 12 mm. M3 standoffs are cheap and it
is tempting. Deflection goes as `L³`:

| M3 column | static sag under a 100 g camera |
|---|---:|
| 12 mm, as fitted | 0.002 mm |
| 114 mm (+4.5 in) | **1.52 mm** |
| 178 mm (+7 in) | **5.74 mm** |

Cantilever `FL³/3EI`, M3 minor diameter 2.39 mm, steel. Fifteen times
the length is 3375 times the sag. A 178 mm M3 column would sag 5.7 mm
under the camera's own weight before anything touched it, and would
ring at a touch.

**Raise the base, not the joint.** Put the whole mount on a rigid
column or block and leave the M3 × 12 doing the job it was sized for.
A longer screw into the camera body also risks bottoming out or going
through something.

## There is a cheaper path, and it may be the better one

Because rotation does not move the plane, the plane does not have to
be recovered from the working frame at all:

| | error at the paper corner | budget | cost |
|---|---:|---:|---|
| **A.** leave the rig, average 9 static frames | 0.222 mm | **28 %** | a calibration pass; nothing else |
| **B.** centre and raise +7 in | 0.327 mm | 41 % | a new lens calibration, a new mount |

**A is both cheaper and more accurate.** Its catch is that it needs a
calibration pass, and it assumes the disc is not *lifted* between that
pass and the work — rotation is proven safe, lifting is not tested.

B earns its keep only if the plane must come off the working frame
itself, with no separate pass. That is a workflow question, not a
measurement one, and it is the operator's to answer.

## Status

**Measured**: the camera's height and offset, recovered from 36 static
poses. The four boards' Z, obliquity and σ_z. The frame's half-angles,
from the stored intrinsics.

**Computed**: the `σ_z` model and everything projected through it, the
heights needed to frame each radius, and the standoff deflection.

**Assumed**: a 100 g camera, and steel standoffs. A plastic or nylon
standoff is roughly 60× more flexible again.

**Not measured**: whether `focus_absolute` 134 is usable at 522 mm at
all, and how much the intrinsics actually move when it is changed.
This project has never measured focus-dependence; it pinned the
control instead.

**The cheapest test**: before building any mount, hold the camera at
the new height by hand, refocus, and check whether a ChArUco frame
still detects cleanly. If the intrinsics have moved enough to matter
it will show as reprojection error against the old calibration.
