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


---

# Revisited 2026-09-25: the premise has failed

The conclusion above — *desk targets are not needed* — was drawn from
a Monte Carlo that modelled landmark error as **Gaussian noise on
points that are where the model says they are**. Four sheet corners at
`z = 0`, three pegs at their heights, 0.5 to 2 px of scatter.

That premise no longer holds. What has been measured since:

* the sheet is **not flat** — the free end departs from a plane by 3 to
  12 mm, and three edges hold to 1 mm while one does not;
* the corners are therefore not *noisy*, they are **biased**, and a
  simulation that adds symmetric noise cannot represent a bias;
* the outline residual is 1.33 mm at near-normal incidence and 3.9 mm
  at 31°, which is now the **dominant** error in the pipeline;
* and the dependence on viewing angle is itself the proof of
  non-planarity, since a homography is exact for a plane at any angle.

So the question is no longer whether targets improve the pose against
noise. It is that **the sheet corners are systematically wrong and a
target fixed to the disc is not.** That is a different argument and it
points the other way.

## What targets on the disc would change

The disc carries the bar. Fix targets to the disc and they are rigid
with respect to the pegs, so a pose from targets is a pose of the
pegs, and it depends on nothing that bends.

**The black background could go, for pose.** It exists so
`find_sheet` can threshold paper against surroundings; if pose comes
from targets, the paper never has to be segmented to be registered.

**But it should stay, for curl — and the reason is sharper than it
looks.** Right now the outline is doing two jobs at once: it *defines*
the plane and it is the *only evidence* about the sheet's shape. A
thing cannot report on itself. Every millimetre of curl is absorbed
into the fitted homography and re-emerges as a residual that cannot be
attributed to anything in particular.

Decouple them — pose from the targets, outline measured against it —
and the outline residual stops being a mixture and becomes a **direct
measurement of how far the paper departs from the disc**. That is a
better curl detector than anything available today, and it costs only
keeping some contrast at the paper's edge.

Which suggests making the **disc itself dark** rather than laying a
separate mat on it. White paper on white foam has no edge to find, and
the mat is the thing that is bowing by a centimetre.

## Two 2 x 2 boards is not enough

A ChArUco board of `c x r` squares has `(c-1) x (r-1)` interior
chessboard corners — the precise ones:

| board | chessboard corners | marker corners |
|---|---:|---:|
| 2 x 2 | **1** | 8 |
| 3 x 3 | 4 | 16 |
| 4 x 4 | 9 | 32 |
| 5 x 5 | 16 | 48 |

**Two 2 x 2 boards give two chessboard corners between them.** A
homography needs four in general position and a pose wants many more.
The ArUco marker corners are also usable — 8 per board — but they are
located less precisely than an interpolated chessboard corner, which
is the whole reason ChArUco exists.

Two further geometric points:

* **Spread matters more than count.** Points in two clusters at
  opposite corners give a long baseline along the diagonal and very
  little leverage across it. Targets at three or four places around
  the paper condition the fit far better than two larger ones.
* **The paper must not cover them.** The disc has to be enough larger
  than a 279 x 216 mm sheet to leave the targets visible with a sheet
  mounted.

## The offset nobody should discover later

Targets live on the disc; the drawing lives on the paper, one sheet
higher. Canson measures **0.1153 mm** thick. At normal incidence that
projects to nothing; at 31° it is 0.069 mm. Negligible either way —
but it is a known constant and belongs in the calibration rather than
in someone's memory.

## The prize, if the targets are fixed to the disc

The pegs' positions in the target frame become **constant**, because
both are bolted to the same disc. Measure that once and peg detection
becomes a *check* rather than a requirement — which would make
registration survive a sheet whose pegs are hidden under artwork, a
failure mode the corpus already contains.


## Four corners cut from one board: what to watch

The plan — scale `calibrx-charuco-175x225mm.svg` to 50 %, cut the four
3 x 3 corners out, glue them at N, S, E and W — is sound in its
essentials and has one serious problem.

**What works.** The four corner blocks carry disjoint marker ids —
NW `{0,3,4,7}`, NE `{2,5,6,9}`, SW `{21,24,25,28}`, SE
`{23,26,27,30}` — so a detector can always tell which piece it is
looking at, and a piece is never mistaken for another. Each 3 x 3
block has four chessboard corners, so the set gives **16 precise
points** spread to the compass. At 50 % the square is 12.5 mm, which
at the rig's 9.8 px/mm is 123 px, with about **11 px per marker
module** — workable, though it would get tight if the camera ever
moved further back.

**The serious problem: cutting the board destroys its geometry.** The
reason a printed target is a calibration target is that the relative
positions of its features are manufactured to the print's accuracy.
Cut it into four and glue them down separately and that is gone: what
remains is four pieces whose *internal* geometry is known and whose
*relative* geometry is whatever the glue did.

Three ways out, in increasing order of appeal.

*Measure the placement.* Four pieces, each needing two coordinates and
a rotation, to a tenth of a millimetre, by hand. Possible; tedious;
easy to get subtly wrong.

*Print the whole layout on one sheet.* Removes the problem entirely,
because the geometry is printed rather than glued — but the disc has
to hold a 279 x 216 mm sheet plus targets outside it, which is bigger
than the printer.

*Bootstrap from the pegs.* The peg spacing is now known to about
0.05 mm. Shoot a set of frames in which pegs and targets are both
visible, solve once for each piece's placement in the peg frame, and
store it in the rig. After that the targets carry the pose on their
own — including on frames where artwork hides a peg, which is the
failure this whole line of work is trying to survive.

The third is the one that needs no new hardware and no careful
handwork, and it reuses the multi-view machinery already in
`acme/lens.py`.

**Three smaller things.**

`cv2.aruco.CharucoBoard` describes a **regular grid**. Four pieces at
the compass points are not one, so `find_charuco` as written will not
see them. Either detect each piece as its own small board and combine
the results, or build a generic `cv2.aruco.Board` with explicit object
points — which is the tool for exactly this and is what the bootstrap
above would produce.

**The print must be re-measured.** The existing board came out 1.27 %
oversize with a +0.15 % anisotropy between its axes. A 50 % rescale
and a fresh print has its own scale error, and it will not be the same
one.

**The pieces have to be coplanar to about 0.1 mm** — glued flat, no
trapped bubble, no ridge of adhesive. Non-coplanar targets reintroduce
precisely the error the disc is being built to remove.

And one placement note: the bar occupies one edge of the disc, so one
of the four compass points is already spoken for. Three targets plus
the bar may be the real layout.
