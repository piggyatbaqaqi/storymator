# Solving the pose in 3-D, with `cv2.solvePnP`

*Feasibility, 2026-09-21. Short version: **PnP is worth doing, and the
desk targets are not needed** — measured, not argued.*

---

## First, the principal point is not the thing PnP finds

The principal point is an **intrinsic**. It belongs to the lens at one
focus and is recovered by lens calibration, which we have already done:
`cx 1640.2, cy 1204.2` from 48 ChArUco frames, cross-checked against
CalibrX to within 0.36 px
([../../data/calibration/distortion/v4k_01/calibrx/README.md](../data/calibration/distortion/v4k_01/calibrx/README.md)).

`solvePnP` **consumes** the camera matrix; it does not refine it. It
answers a different question — where the camera is relative to a known
3-D object, six degrees of freedom — and a ChArUco target on the desk
would feed that, not the intrinsics.

So the two halves of the proposal separate cleanly, and they have
different answers.

---

## What PnP would buy

The fit today is a planar homography plus a rigid correction. A
homography maps plane to plane and **knows nothing about height**,
which is exactly why parallax on a raised landmark had to be corrected
by hand with `r·h/Z` in [../../comfyui/comfyui_acme/acme/parallax.py](../comfyui/comfyui_acme/acme/parallax.py).

With a 3-D pose the correction stops being a correction. Each landmark
has a known height, gets projected through the pose, and is compared
where it actually is. Any height, any camera angle, no approximation —
and the same machinery would handle a fourth landmark at a fourth
height without new code.

It also over-determines the fit. Seven landmarks give fourteen
observations against six unknowns, so eight are redundant and the
residual starts meaning something.

---

## The desk targets are not needed — measured

The seven points already detected — four sheet corners at `z = 0` and
three peg landmarks at their heights — are **non-coplanar, but only
just**: singular values 314, 250 and **5.01 mm**, so the out-of-plane
spread is 1.6 % of the in-plane one. That looked far too thin to
condition a pose, which is the reason to test rather than assume.

Monte Carlo, 200 trials per row, a 25° view at 306 mm, median error:

| point set | noise | rotation | translation |
|---|---:|---:|---:|
| **the seven we detect now** | 0.5 px | 0.03° | 0.1 mm |
| **the seven we detect now** | 2.0 px | **0.13°** | **0.3 mm** |
| + ChArUco flat on the desk | 2.0 px | 0.07° | 0.2 mm |
| + ChArUco on 60 mm risers | 2.0 px | 0.08° | 0.2 mm |

**0.13° and 0.3 mm at 2 px of landmark noise, with nothing added to the
desk.** Desk targets roughly halve that, and standing them on 60 mm
risers buys nothing over laying them flat — so the depth that was
feared to be too thin is in fact sufficient, and adding depth does not
help.

Against a 1.5 px (0.18 mm) acceptance threshold, a 0.2 mm improvement
in the pose is not what is standing in the way.

### What desk targets would still be good for

Not pose accuracy. Two other things, if either turns out to matter:

* **A camera pose that does not depend on the sheet.** Useful if sheet
  detection fails, or to check the camera has not been bumped between
  frames.
* **An independent scale**, rather than inferring the working distance
  from `fx / scale`.

Against which: more bright objects in frame, on a rig where a plastic
bag touching the paper already cost an evening
([../rig-setup.md](rig-setup.md)).

---

## What PnP would *not* fix

The current dominant error is **detection bias, not geometry**. About
1.7 mm of along-bar offset on the round landmark is unexplained after
the parallax correction, and a better pose fitted to a biased landmark
is a biased pose. PnP would make the geometry exact and leave that
untouched.

It also assumes a **rigid** object. The sheet is not: the bar stands
4.84 mm above the desk, so the paper drapes rather than lying flat, and
the four corners are not really at `z = 0` together. PnP would absorb
that into pose error rather than reporting it — the same way the rigid
stage absorbed the 180° flip.

---

## Recommendation

**Do PnP, skip the desk targets, and do neither first.**

Order matters. Fit the landmarks properly before improving the geometry
that consumes them — see
[landmark-detection.md](landmark-detection.md), which would replace
three centroids with three fitted rectangles and twelve numbers instead
of six. PnP on good landmarks is a clear win; PnP on biased centroids
just relocates the bias.

If the desk targets are wanted anyway, lay them flat. The risers are
measurably pointless.
