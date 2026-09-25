# Flattening a bent sheet from a printed ChArUco background

Asked 2026-09-25: *can a flat sheet be extracted from a bent or even
creased sheet, if the sheet has a faint monochromatic ChArUco
background?*

**Yes** — and it is the only proposal so far that *corrects*
non-flatness rather than measuring it or arranging not to see it.
Overhead shooting reduces the projection of the error, a foam disc
reduces the error, and disc-mounted targets get a pose that does not
depend on it. None of them recover the drawing that is on a bent
sheet. A fiducial field printed on the paper does, because the
fiducials bend with the artwork.

The limits are not where intuition puts them. Faintness costs about a
tenth of a millimetre and is not the problem. The marker **pitch**,
the **interpolant's continuity class**, and the **printer's scale**
are the problem.


## Why it works, and why no surface model is needed

There is a literature on undoing paper curl from a single image —
Pilu's applicable surfaces, the developable-surface fits, later the
learned dewarpers — and all of it exists to supply information that
*is not there*: with only a text block and two page edges, the
deformation is underdetermined, so the isometry of paper has to be
imposed as a prior to pin it down.

With fiducials printed on the sheet, none of that applies. Each
detected chessboard corner is a correspondence between

* a known position in **sheet coordinates** (the print's own grid), and
* an observed position in **frame pixels**.

That is exactly the input `register_image` already consumes, except
that instead of one global homography there is a dense scattered set of
correspondences. Resampling the frame through them yields the sheet as
if flat. **No 3D reconstruction, no isometry assumption, no
developability.** The surface could be a crumpled non-developable mess
and the resampling would still be right, because the map being
inverted is image → sheet, and the sheet's embedding in space never
enters it.

This is worth stating plainly because it changes what has to be built:
the job is scattered-data interpolation in 2D, not shape recovery.


## A crease is a continuity problem, not a curvature problem

The image → sheet map is **C⁰ across a crease and not C¹**: positions
agree, the Jacobian jumps. That single fact decides the interpolant.

| interpolant | continuity | behaviour at a crease |
|---|---|---|
| global homography | C^∞ | absorbs the fold into residual — today's failure |
| thin-plate spline | C² | rounds the fold, smears a band either side |
| polynomial / Bezier patch | C^∞ | same, plus ringing |
| **per-cell homography on the fiducial mesh** | **C⁰** | **correct by construction** |
| per-triangle affine (Delaunay) | C⁰ | same, cheaper, slightly coarser |

Fit **per cell**, not globally. A crease then needs no detection, no
segmentation and no special case: it lands inside some row of cells and
those cells simply get a different Jacobian from their neighbours,
which is what the truth is. A smooth interpolant has to be *told*
about a crease; a C⁰ one never has to know.

The exception is smoothing. If corner noise is suppressed by
regularising the warp — and with a faint print it should be — the
regulariser must not smooth across the fold. Ordinary Tikhonov
smoothing on the mesh reintroduces exactly the smearing that the
piecewise fit avoided. Either leave it unregularised, or make the
smoothing anisotropic along lines where the Jacobian discontinuity is
consistent across several cells.


## The pitch sets the residual, and the numbers are comfortable

Inside one cell the true surface is approximated by a flat quad. For
curl of radius `R` and cell size `s`, the sag is `s²/8R`; for a crease
of dihedral deviation `φ` falling mid-cell, the departure from the
chord is `(s/2)·sin(φ/2)`. Either projects into the image multiplied by
`tanθ`, θ from the surface normal — the same `h·tanθ` mechanism that
made the outline residual grow with obliquity in
[landmark-detection.md](landmark-detection.md).

Threshold for comparison: **0.804 mm**, three times the punch
tolerance measured over 95 flatbed scans.

| pitch | cells on a 266.7 × 317.5 sheet | curl R=200 @1.5° | @31° | crease φ=30° @1.5° | @31° |
|---|---:|---:|---:|---:|---:|
| 12.5 mm | 21 × 25 (480 corners) | 0.003 | 0.059 | 0.042 | 0.97 |
| 25 mm | 10 × 12 (99 corners) | 0.010 | 0.235 | 0.085 | 1.94 |
| 50 mm | 5 × 6 (20 corners) | 0.041 | 0.939 | 0.169 | 3.89 |

Read against the 3 to 12 mm the free end is currently departing by,
**a 25 mm pitch removes the whole of the curl term** — two orders of
magnitude below threshold overhead, and still inside it at 31°.

Creases are the sizing constraint, not curl, and they are the reason to
go finer than the 25 mm of the CalibrX boards. At 12.5 mm a 30° crease
costs 0.042 mm overhead. The two mitigations multiply, as before: pitch
and viewing angle.


## Faintness is cheap; low contrast is the wrong way to buy it

Corner localisation scatter goes roughly as noise over local gradient,
so a print at a tenth of full contrast costs about an order of
magnitude in corner precision. At `px_per_mm = 11.63`, 1 px = 0.086 mm:

| corner scatter | in mm | against the 0.804 mm threshold |
|---|---:|---|
| 0.1 px, a crisp ChArUco corner | 0.009 | 1 % |
| 0.3 px | 0.026 | 3 % |
| 1 px, a faint print | 0.086 | 11 % |
| 2 px, very faint | 0.172 | 21 % |

So faintness is affordable. But there is a real cost hidden in it that
does not appear in that table: **a piecewise fit does not average.** A
global homography over 99 corners takes pose error down by √99; a
per-cell homography is driven by that cell's four corners and nothing
else, so the corner scatter lands in the product at full size, locally
and unsmoothed. Faintness is thus more expensive for a mesh than it
ever was for a pose.

The better trade is **chromatic separation instead of low contrast**.
Print the grid in a hue far from the ink — the trade's own non-photo
blue is exactly this idea, and the pipeline already reasons in
`(a*, b*)` after white-balancing against the paper, in `acme.ink`.
Then the grid is at *full* contrast in a channel combination chosen to
maximise it, and near-invisible in the channel the artwork is extracted
from. That buys 0.1 px corners and an unmarked drawing at the same
time, where "faint grey" buys 1 px corners and a grey drawing.

Two bonuses fall out of it. A print of known density is a **dense
photometric reference**, so the shading that a bent sheet imposes can
be flat-fielded before `acme.threshold` ever sees it. And a hue gate
is exactly the machinery already written for the peg crowns.


## Keep the pegs as the datum; let the grid carry deformation only

This is the architectural point, and getting it backwards would be
expensive.

The printed grid's absolute scale is **the printer's**, not a
metrology-grade ruler's. Roller feed error of 0.1 to 0.5 %, anisotropic
between feed and scan directions, is ordinary — and the CalibrX board
in this project's own `data/calibration/targets` prints **1.27 %
oversize**, measured. A 1 % scale error on a 266.7 mm sheet is 2.7 mm.
Make the grid the datum and that error is a systematic bias on every
coordinate, which is precisely the shape of the `centre_spacing_mm`
bug: the one number never put under the calipers setting the scale of
everything.

So:

* **pose and scale from the pegs**, unchanged — `acme.detect`,
  `acme.parallax`, `FieldSpec`, the peg frame as canonical origin;
* **the grid supplies a correction field only**, a per-cell departure
  from the homography the pegs define;
* the print's scale becomes a **per-sheet nuisance parameter** solved
  for alongside, not a bias — and solving for it per sheet also absorbs
  humidity, which moves paper by more than the printer does;
* nothing needs the print registered to the punch, which is a precision
  problem worth avoiding.

The grid's plane is the drawing's plane if it is printed on the front.
On the back, add the 0.1153 mm sheet thickness, and expect the paper's
own translucency to cost contrast.

This also settles the open question in
[pose-from-pnp.md](pose-from-pnp.md) about keeping the black
background for curl. A printed grid is a **far better curl detector
than the outline residual** — it reports curl per cell over the whole
sheet, rather than one number at the boundary — so the outline's second
job disappears and the black background becomes genuinely optional.


## Where the fiducials are absent is where the drawing is

The uncomfortable structural fact: markers are detectable on blank
paper and occluded under ink, so **the correction field is best
sampled where nothing needs correcting**. ChArUco degrades gracefully
here — any few visible markers fix the board's identity and every
visible chessboard corner is then refined — but a solid ink mass is a
hole in the field, and inside that hole the warp is interpolated from
its rim.

For curl that is fine: deformation is smooth and low-order, and
interpolating it across 30 mm of ink costs the sag of a 30 mm span. For
a crease **running under a solid ink mass** it is not fine, and nothing
recovers it from one view. Worth knowing; unlikely to bite, since a
crease crossing the sheet will be visible somewhere along its length
and its line can be continued.


## What cannot be recovered, whatever the pitch

* **Fold-over.** A crease that occludes paper against paper hides the
  drawing from the camera. One view cannot recover it. "Bent, and
  creased" is inside scope; "folded" is not.
* **Resolution lost to obliquity.** Where the sheet turns steeply away,
  the frame samples fewer pixels per millimetre and unwarping stretches
  what it has. Near a tight fold the flattened result is a blurred
  stripe, and it is blurred in the data, not in the arithmetic.
* **Tone.** Geometric flattening does not flatten shading. See the
  flat-field note above; the grid is the way to fix it.


## Recommended shape of the work

1. **Pitch 12.5 mm**, markers in a border band plus a sparse interior,
   so the interior loses as little paper to fiducials as possible.
2. **Non-photo blue, at full contrast in its own channel**, detected
   through the `acme.ink` chroma machinery, not a faint grey.
3. **Per-cell homography over a Delaunay mesh of the detected corners**,
   applied as a correction to the peg-frame homography, not as a
   replacement for it.
4. **Measure the print** the way the CalibrX board was measured —
   corner to corner across five squares with calipers, six readings,
   scatter as the error bar. One flatbed scan per batch. The printer is
   now in the error budget and has to be treated like the bar.
5. **Report the per-cell departure** as the curl map. It supersedes the
   outline residual as the flatness diagnostic.


## Status

Analysis only. Nothing here is implemented and nothing here is
measured on this rig; the error figures are the two formulas above
evaluated at this project's own `px_per_mm`, sheet size and threshold.
The claim that wants testing first is the cheapest one: print a grid,
crease a sheet deliberately, and check that a per-cell fit recovers a
straight ruled line across the fold where a thin-plate spline bows it.
