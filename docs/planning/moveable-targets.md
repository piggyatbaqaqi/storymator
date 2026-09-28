# Measure ref 1 before you cut it, and compare placements on the pegs

**Verdict.** The experiment is the right one, and two things about it
are time-critical or easy to get wrong:

1. **Measure ref 1's corner spans now, while the sheet is intact.**
   The measurement is irreversible: once the four pieces are
   separated, the longest baseline left inside one piece is 17.68 mm,
   and six readings on it carry 0.76 % against a print error worth
   about 1.27 %. On the intact sheet the same six readings carry
   0.11 %. Cutting first throws away a factor of seven and cannot be
   undone.
2. **Compare placements by what they predict, not by their
   reprojection rms.** Fit from the targets, predict the *pegs*, and
   report `Pose.peg_residuals_mm` against the 0.804 mm threshold.
   Reprojection rms rewards exactly the bad placement — targets
   clustered near the axis — because it measures fit, not prediction.

The repositionable adhesive is fine. The standoff is not the risk.

## 1. The anisotropy is unrecoverable after the scissors

Six readings, 0.33 mm of technique scatter — the figure measured in
`data/calibration/targets/README.md` and the reason the nominals are
printed on the sheet at all:

| what is left to measure | baseline | one reading | mean of six |
|---|---:|---:|---:|
| intact sheet, diagonal | 117.35 mm | 0.28 % | **0.11 %** |
| intact sheet, across or down | 83.92 mm | 0.39 % | **0.16 %** |
| one cut piece, corner diagonal | 17.68 mm | 1.87 % | 0.76 % |
| one cut piece, corner to corner | 12.50 mm | 2.64 % | 1.08 % |

The quantity being chased is the print's scale and anisotropy, worth
about 1.27 % and 0.15 % respectively on `charuco_0001`. A 0.76 %
error bar cannot see a 0.15 % anisotropy. A 0.11 % one can.

So: six readings on each of the four printed spans, **before any
cutting**, and they go in ref 1's record.

## 2. The adhesive layer is not the risk; a lifted edge is

Out-of-plane error projects as `h·tanθ`, and one detected corner is
worth 0.102 mm — the 0.707 px calibration rms at 144.4 µm/px, which
is this rig's scale at its measured 379 mm working distance.

| standoff `h` | at 15° | at 30° | at 45° |
|---|---:|---:|---:|
| 0.05 mm | 0.013 | 0.029 | 0.050 mm |
| 0.10 mm — a repositionable coat | 0.027 | **0.058** | 0.100 mm |
| 0.25 mm | 0.067 | 0.144 | 0.250 mm |
| 1.00 mm — a lifted corner | 0.268 | **0.577** | 1.000 mm |
| 2.00 mm | 0.536 | 1.155 | 2.000 mm |

A 0.1 mm adhesive layer costs 0.058 mm at 30°, which is **half the
noise of a single corner** and 7 % of the threshold. It does not
matter.

A corner lifted 1 mm costs 0.577 mm, **72 % of the threshold**, and
repositionable adhesive is dot-coated and weak precisely so it will
let go. That is the failure to guard against: press the whole face,
check all four edges before each session, and re-press after every
move. The risk is adhesion, not thickness.

## 3. Four targets cover 6.9 % of the frame

At 379 mm the frame spans 471 × 353 mm and a 53.5 mm piece is 371 px
square. Four of them occupy **6.9 %** of the 3264 × 2448 sensor.

A distortion model fitted from one placement is therefore
interpolating inside 6.9 % of the frame and extrapolating across the
other 93 %. That is not an argument against the experiment — it is
the argument *for* it, and for pooling placements into one fit rather
than trusting any single one. The existing `v4k_01` model came from
48 frames of the 175 × 225 mm board, which is a different regime
entirely.

## 4. Do not compare distortion coefficients

The `v4k_01` radial polynomial is already non-monotonic:

| off axis | radial displacement | at 379 mm |
|---:|---:|---:|
| 37.9 mm | +0.178 % | 0.07 mm |
| 135.1 mm | +1.720 % | 2.32 mm |
| 199.9 mm | +2.492 % | 4.98 mm |
| **212 mm (peak)** | **+2.522 %** | 5.35 mm |
| 264.8 mm | +2.147 % | 5.69 mm |
| 297.2 mm (corner) | +1.636 % | 4.86 mm |

It rises to +2.52 % and comes back down to +1.64 % at the corner.
`k1 = +0.182`, `k2 = −0.399`, `k3 = +0.238` are a set that trade off
against each other; individually they mean nothing, and two
calibrations with very different triples can describe nearly the same
lens. **Comparing k1 between placements will produce a number that
looks like a result and is not one.** Compare displacement fields, or
better, compare predictions.

## 5. The right statistic is already in the codebase

`fit_pose` returns `Pose.peg_residuals_mm`, and
`default_residual_mm` derives the threshold as `3 ×
punch_tolerance_mm` = **0.804 mm**, because no real sheet can beat
its own punch. That is an out-of-sample statistic: the pegs took no
part in the target fit, and their spacing is independently known to
102.722 mm from calipers.

Reprojection rms is the wrong choice and will actively mislead. It
falls when the targets are clustered and close to the axis — the
placement with the *least* information about distortion — because it
only asks how well the model reproduces the points it was fitted to.

Report per placement: the peg residual, the recovered peg spacing
against 102.722 mm, and the sheet-corner residual.

## 6. Get the within-placement floor first

Otherwise a difference between placements cannot be read. The
project's own rule — six readings, the scatter is the error bar —
applies to placements too, with one addition: **peel and re-seat the
targets between repeats within a placement.** That folds the
adhesive's own repeatability into the floor, which is the thing the
comparison will otherwise blame on placement.

Suggested: one placement, six sessions, re-seating between each.
Whatever spread that gives is the floor. Only differences comfortably
above it are placement effects.

## What the session record has to gain

Once the targets move, "where were they?" stops being a property of
the rig and becomes a property of the session. `bin/collect-captures`
writes a `manifest.json` per session with a lighting note and
per-frame exposure; it needs the placement too, and ref 1's identity.
This is the same gap `calibration-files.md` describes for the rig,
and the same fix: name it, hash it, copy it into the manifest.

Until that exists, the free-text session note is the record, and it
should carry the placement and `ref_1`.

## Status

**Measured**: the 0.33 mm corner-reading scatter, the 0.707 px
calibration rms over 48 frames, the 379 mm working distance, the
102.722 mm peg spacing and the 0.268 mm punch tolerance — all from
the repository, all cited above.

**Computed**: everything else. The error-bar table is the scatter
divided by each baseline. The standoff table is `h·tanθ`. The 6.9 %
is four squares of 53.5 mm at 144.4 µm/px against a 3264 × 2448
frame. The distortion profile is the stored `dist_coeffs` evaluated
over the radius, not a refit.

**Not measured**: ref 1's own print scale and anisotropy — that is
task one. The adhesive's actual coat thickness, assumed 0.1 mm. How
far a repositionable target really drifts between sessions, which is
what §6 exists to find out.

**The cheapest test**: the six readings on the intact sheet. They
cost ten minutes, they are impossible after cutting, and until they
exist every placement comparison is measured in units of an unknown
scale.
