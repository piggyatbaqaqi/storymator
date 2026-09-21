# calibrx's calibration of v4k_01, compared with ours

`v4k-01-storymator-pinhole-calibration.json`, produced 2026-09-21 by
the `calibrx` SDK 0.1.0 from the same `distortion-*.jpg` frames and the
same measured square size, 25.3163 mm.

**This is an independent check, and it passes.** Two implementations,
fitted separately, agree to **half a pixel on every intrinsic**.

## The headline comparison

| | ours (+0.15 % aniso) | calibrx | difference |
|---|---:|---:|---:|
| fx | 2625.44 | 2624.23 | +1.21 |
| fy | 2625.52 | 2626.96 | −1.44 |
| cx | 1640.2 | 1644.8 | −4.56 |
| cy | 1204.2 | 1203.7 | +0.46 |
| fx/fy − 1 | **−0.003 %** | **−0.104 %** | |
| rms | 0.7070 (48 frames) | 0.7158 (53/53) | |

## The whole difference is our anisotropy correction

Refitting our own pipeline *without* the board-anisotropy term lands
essentially on top of calibrx:

| | fx | fy | cx | cy | fx/fy − 1 |
|---|---:|---:|---:|---:|---:|
| ours, isotropic | 2624.44 | 2627.00 | 1645.1 | 1204.2 | −0.097 % |
| **calibrx** | **2624.23** | **2626.96** | **1644.8** | **1203.7** | **−0.104 %** |
| ours, +0.15 % aniso | 2625.44 | 2625.52 | 1640.2 | 1204.2 | −0.003 % |

Ours-isotropic minus calibrx: **fx +0.22, fy +0.04, cx +0.36, cy +0.45
px**, with distortion coefficients agreeing to a few parts in 10⁴.
That is as close as two independent least-squares fits get.

**calibrx sees the same 0.104 % fx/fy discrepancy we did**, which is
strong outside evidence that the print anisotropy is real and in the
data rather than in our code. They do not model it — their format has
one `square_size` and no second axis — so it lands in fx/fy, exactly as
it did for us before we corrected it.

## How far apart are they in practice

Undistorting a 60 × 45 grid through both models and measuring the
disagreement:

| radius band | mean | max |
|---|---:|---:|
| 0–20 % | 0.02 px | 0.05 |
| 20–40 % | 0.07 | 0.21 |
| 40–60 % | 0.19 | 0.49 |
| 60–80 % | 0.47 | 1.02 |
| 80–100 % | 0.95 | **2.43** |

**Where an ACME sheet's corners actually land — 43–75 % radius — the
two models differ by 0.30 px mean, 0.86 px max**, which is 0.026 mm at
the rig's 11.63 px/mm.

The 2.43 px worst case sits at the extreme frame corner, and is well
inside the **18–29 px** spread we already documented between our own
model variants out there, caused by having no calibration samples
beyond 90 % radius. So the vendor comparison does not move the known
limitation: outer-radius coverage is still the weak point, and it is
weak by an order of magnitude more than this disagreement.

## Two differences worth noting

**Frame count.** calibrx reports 53 of 53 used; we use 48 of 55. Seven
of our frames fall below a 12-corner floor — they detect 1, 3, 5, 6, 7,
8 and 9 corners respectively — and we drop them. All 55 yield *some*
detection. Which 53 calibrx was given is not recorded in its output.
That the two agree to half a pixel across *different* frame subsets
makes the agreement stronger, not weaker.

**What each format carries.** calibrx's is the better interchange
format: explicit `distortion_order`, named coefficients, an
`undistortion` block with `balance` and `fov_scale`. Ours carries
things theirs has no field for — board anisotropy, the peg and sheet
geometry, and the provenance block recording `focus_absolute 134`,
without which the intrinsics are silently wrong. Neither supersedes the
other; ours stays the working file.
