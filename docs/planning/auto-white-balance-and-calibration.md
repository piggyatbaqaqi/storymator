# Auto white balance costs 0.02 px; the auto exposure is the problem

**Verdict.** Calibrating a camera with only automatic colour balance
is a **precision question, and barely that** — provided the work is
done on a single channel. The serious issue on `fancy_pro_001` is a
different control: it auto-exposes to **34 % clipped** with about
**10 % of headroom** before targets start disappearing, and there is
no exposure control to back it off.

## Why white balance hardly touches geometry

Calibration uses feature *positions* from a greyscale image. White
balance is a per-channel gain, and a ChArUco target is **achromatic** —
black squares and white squares. A per-channel gain maps achromatic to
achromatic: the greys change, the edges do not move.

The one coupling is **lateral chromatic aberration**. The lens focuses
red, green and blue at slightly different magnifications, so a
greyscale image is a weighted sum of three slightly different images,
and changing the weights moves the sum. Measured on the WB-on frame
with sub-pixel corner refinement:

| | mean | worst |
|---|---:|---:|
| R vs G | **0.022 px** | 0.111 px |
| B vs G | 0.018 px | 0.055 px |
| luma vs G | 0.009 px | 0.024 px |

Against the 0.707 px rms of this project's existing lens calibration,
that is noise. Measured on one target piece in a 640 × 480 frame,
though, and lateral chromatic aberration grows toward the frame
corners, so treat 0.1 px as a floor rather than a bound.

## And it goes to exactly zero on a single channel

A white-balance gain applied to **one** channel is a scalar multiply
of the whole plane. It cannot move an edge, and it cannot mix in
chromatic aberration either, because there is nothing to mix.

**So calibrate and capture on the green plane.** Green also carries
twice the Bayer sites of red or blue, and on this camera it carries
the entire image anyway.

Taking luma instead is actively worse here, because it drags in two
dead, noisy channels:

| | mean | worst |
|---|---:|---:|
| luma vs green plane, full-res frames | **0.333 px** | 4.412 px |

## The serious issue is clipping, and it is the other control

34 % of the green channel is saturated, and it stays at 34.3 % whether
the lamp is at its lowest or highest setting — the auto-exposure holds
the mean at about 147 and the clipping comes with it.

The targets survive that. They do not survive much more:

| extra gain | clipped | markers found | mean corner shift |
|---:|---:|---:|---:|
| ×1.00, as shot | 34.2 % | **16** | — |
| ×1.10 | 40.3 % | 15 | 0.424 px |
| ×1.25 | 44.0 % | 14 | 0.949 px |
| ×1.50 | 46.5 % | **6** | 1.835 px |
| ×2.00 | 49.3 % | **0** | — |

**Ten per cent brighter loses a marker; twice as bright detects
nothing.** That is not a precision loss that averages away — it is a
cliff, and the camera is auto-exposing close to its edge.

It is also the one error here that is **systematic**. A partially
clipped edge biases its sub-pixel corner the same way in every frame,
so averaging over frames does not remove it. Everything else in this
document averages out; this does not.

## What would actually help, given no exposure control

The scene's dynamic range is the problem: white paper against a black
disc. The auto-exposure holds the mean, so the black disc drags the
exposure long and the paper blows.

**Lightening the disc should fix it without any camera control.** At
present the dark decile sits near 28 and the paper is clipped. Lifting
the disc from near-black to mid-grey raises the frame mean, the
auto-exposure shortens in response, and the paper comes down out of
saturation. A rough estimate on this frame's histogram puts a mid-grey
disc right at the edge of unclipped.

That is a trade against the original reason the disc is black — it was
the contrast background for sensing the paper's corners. The ChArUco
targets were introduced to take that job over, so the black may no
longer be earning its keep. **Worth deciding deliberately rather than
by inheritance.**

Using the lamp at its lowest setting is marginally the best of the
three, with slightly more shadow detail and identical targets.

## What is genuinely lost, and it is not calibration

`acme/ink.py`'s blue-peg detector needs chroma, and with this camera's
colour pipeline there is none to have — 99.92 % of pixels exceed its
`min_chroma`, so it would select the entire frame. That is a
capability gone, not a calibration defect, and it is a design question:
if the ChArUco targets carry the geometry, the ink path may not be
needed on this camera.

## Status

**Measured**: the chromatic aberration between planes and the luma-vs-
green shift, both with sub-pixel corner refinement; the clipping
response, by re-detecting the same frame at progressively higher gain;
the lamp invariance, across shots 5, 6 and 7.

**Computed**: nothing beyond those.

**Not measured**: lateral chromatic aberration at the frame corners —
the only frame with real colour is 640 × 480 and its markers sit near
the middle. And whether a grey disc actually lands the exposure where
the histogram says it would.

**The cheapest test**: put something mid-grey over the disc, shoot one
frame, and look at the clipped fraction. If it drops below a few per
cent the headroom problem is solved without any camera control.
