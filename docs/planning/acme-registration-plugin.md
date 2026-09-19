# ACME registration as a ComfyUI plugin — design

*Rev 2, 2026-09-17, after operator review. Rev 1's two-transform scheme
is withdrawn: it assumed a fixed camera and a rotating disc, and the rev 0
rig is the opposite — a movable camera and no disc. The replacement is
simpler and strictly more general.*

Targets **ComfyUI 0.35.0** and the V3 schema API (`comfy_api.latest`,
`io.ComfyNode`, `define_schema`/`execute`, `ComfyExtension` +
`comfy_entrypoint`).

Implements the first milestone in
[inbetween-acceptance.md](inbetween-acceptance.md) §5.

---

## 1. The product

**The plugin's minimum output is a transformed capture that already
obeys the registration constraints** — every drawing resampled onto one
fixed canonical pixel grid in ACME field coordinates, so frame *n* and
frame *n+1* are directly comparable, differenceable and onion-skinnable
with no further work. Everything else in this document exists to make
that output trustworthy or to say when it isn't.

---

## 2. Geometry: why the pegs alone cannot do it

Rev 1 proposed a fixed desk homography plus a per-frame rigid transform
from the pegs. With a movable camera that decomposition is invalid, and
the honest replacement starts from a fact worth stating precisely:

> **Three collinear points cannot determine a homography.** Three points
> on a line fix a projective frame *on that line*, so the line is fixed
> pointwise — but the homographies fixing a line pointwise form a
> **three-parameter family** (planar homologies and elations with that
> axis). The three ACME pegs are collinear by design. Fitting them
> leaves three degrees of freedom undetermined.

Physically, the undetermined part is tilt of the paper about the peg-bar
axis, confounded with foreshortening perpendicular to it. Under a
near-perpendicular camera you can paper over this by *assuming* the sheet
is square-on. Under a deliberately keystoned camera — which is what the
rig wants, §5 — that assumption is exactly what fails.

### The paper supplies the missing degree of freedom

A sheet of ACME-punched bond is a rectangle of known size. **Its four
corners are four points in general position, which is exactly what a
homography needs.** No fiducials to buy, nothing extra in frame, and the
rig already owns it.

That gives a two-part fit with a clean division of authority:

| stage | from | supplies |
|---|---|---|
| **outline** | the four paper edges, fitted as lines and intersected | the full homography — perspective, tilt, scale |
| **datum** | the three peg centroids | a small in-plane correction, because the *pegs* are what the artist's drawings are actually aligned to |

The second stage matters because punch tolerance is real. The drawing
was made with the sheet on the pegs, so the pegs — not the paper edge —
are the registration datum. Punch position relative to the trimmed edge
carries a manufacturing tolerance, and whatever it is, the peg-derived
correction absorbs it. Fit edges first because they are long and
therefore well conditioned; correct with pegs because they are true.

**Corners come from intersecting fitted edges, never from finding a
corner pixel.** Each edge is hundreds of pixels of evidence; the corner
itself is rounded, and on a punched sheet it may be dog-eared.

---

## 3. What this buys, in pixels

Assuming 4K across a 13-inch frame — **11.6 px/mm, 1 px = 0.086 mm** —
and 0.3 px landmark localisation, which a 74-px-diameter round peg
comfortably supports.

| quantity | value |
|---|---|
| peg span, rect to rect (8″, operator-confirmed) | 2363 px |
| rotation precision | 1.8 × 10⁻⁴ rad ≈ **0.6 arcmin** |
| that, as displacement 200 mm from the bar | **0.42 px** |

So in-plane registration is comfortably sub-pixel with one camera. The
thing that is *not* sub-pixel is stack height.

### The cost of a stack, and the rule of thumb

A drawing sits one paper-thickness above the one below it, so it is
imaged at a slightly different magnification. Uncorrected, with the
camera at 400 mm and 0.1 mm bond:

> **Every sheet of stack costs about half a pixel of registration error
> at the edge of the drawing.**

| stack | camera at 400 mm | at 600 mm |
|---|---|---|
| 2 sheets | 1.2 px | 0.8 px |
| 20 sheets | 12 px | 8 px |
| 50 sheets | 29 px | 19 px |

Two sheets is fine. A flip stack is not, and no amount of software
fixes it from a single perpendicular view — the information is absent.

---

## 4. Do you need a second camera? Not yet — and here is the number

**Rev 0, at one or two sheets, is sub-pixel on one camera.** Buy nothing.

For flip-stack work there are two routes, and the second is more
interesting than rev 1 realised.

**Two cameras.** Triangulate the paper plane directly. Depth precision
δz ≈ z²·δd/(f·B):

| baseline | depth σ | in sheets | residual error, *any* stack |
|---|---|---|---|
| 100 mm | 0.10 mm | 1.0 | 0.60 px |
| 150 mm | 0.07 mm | 0.7 | **0.40 px** |
| 300 mm | 0.03 mm | 0.3 | 0.20 px |

A 150 mm baseline holds sub-pixel for a stack of any depth. Two cameras
also give paper *tilt* and *curl* for free, which a single view cannot
see at all.

**One oblique camera.** A tilted camera sees the cut edge of the stack,
and its apparent height is the stack thickness times tan(tilt):

| stack | 30° tilt | 45° tilt |
|---|---|---|
| 2 sheets | 1.3 px | 2.3 px |
| 10 sheets | 6.7 px | 11.6 px |
| 50 sheets | 34 px | 58 px |

**The precision improves exactly as the error it corrects grows.** At
two sheets the measurement is marginal and the error is negligible; at
fifty sheets the error is 29 px and the measurement is 58 px of clean
signal. That is a fortunate shape, and it means a single oblique camera
may well handle production. It is unproven, so it is a candidate rather
than a plan — but it is cheap to test with the camera already owned, and
worth testing before buying.

**Recommendation: don't buy yet.** Test the oblique-edge measurement on
rev 0. Keep the software's per-camera pose estimation independent so a
second camera is additive rather than a rewrite. Buy when moving to flip
stacks *and* the oblique measurement has disappointed.

---

## 5. Keystone: wanted, within limits

Heavily keystoned cameras are fine — a homography is precisely the model
for a plane seen from any angle, so obliquity costs the estimator
nothing. It is also necessary: two cameras cannot both sit over the sheet
without colliding, and the desk design already calls for angles that
avoid hand obscuration.

Two real costs bound how far to push it:

| tilt | sampling on the foreshortened axis | depth range across a 317 mm sheet |
|---|---|---|
| 30° | 0.87× | 158 mm |
| 45° | 0.71× | 224 mm |
| 60° | 0.50× | 275 mm |

The second column is the binding one. A 45° view needs ~224 mm of depth
of field, which wants a small aperture — and on a small-sensor 4K camera,
stopping past roughly f/5.6 is diffraction-limited, so the resolution you
bought is lost anyway. **Keep tilt in the 30–45° band**, light it well
enough to stop down, and prefer a larger sensor if the choice arises.

---

## 6. Calibration, concretely

The rev 0 worry — *"the camera position is easily disrupted"* — stops
mattering under this design, because nothing that gets disrupted is
calibrated.

**Once per camera: lens intrinsics.** Photograph a printed checkerboard
or ArUco board lying on the desk, a dozen poses, once. This recovers
focal length, principal point and radial distortion. At 4K with a wide
lens, uncorrected radial distortion is tens of pixels at the corners, so
this is not optional for sub-pixel work. It does **not** change when the
camera is bumped. It *does* change if zoom or focus change — so fix both
and tape them.

**Every frame: pose.** Solved from the paper outline and pegs in that
frame. No stored extrinsics, nothing to invalidate. Move the camera
between shots, mid-session, on purpose. The registration does not care.

**Nothing needs to be visible outside the paper**, which answers the rev
0 space constraint: the sheet fills the frame and that is sufficient.

### The one thing a fiducial would buy — and it is your §8 point

You are right, and the reason is worth naming. With a **fixed** camera
and a **rotating disc**, the peg-bar angle measured in camera coordinates
*is* the disc angle, because the camera supplies a world reference. With
a **moving** camera and no disc, camera rotation and paper rotation are
indistinguishable — registration removes both, and absolute orientation
is not merely discarded, it is unrecoverable.

So moving the camera does *not* subsume the rotating disc. It subsumes
the registration problem, which is the larger part, and loses exactly one
scalar: absolute angle. For effects where the rotation is the point —
where the artist turns the work deliberately rather than for comfort —
that scalar is content, not nuisance.

Recovering it needs one **world-fixed** reference in frame: a small
fiducial on the desk surface, outside the paper, not on the disc. It need
not be near the sheet, only visible. Rev 0 cannot frame it and does not
need it; when there is a disc, one marker restores the datum.

---

## 7. Detection, rejection, and what the operator sees

The peg bar is a rigid body of **known** geometry, now confirmed:

```
round peg     1/4" diameter          6.35 mm    ~74 px
rect pegs     1/2" x 1/8"     12.70 x 3.18 mm   ~147 x 37 px
centres       4" apart              101.6 mm    ~1180 px
outer span    8" rect to rect       203.2 mm    ~2363 px
```

These become the *defaults* of a calibrated peg model, not constants, so
a different bar is a settings change.

Detection is **fitting, not blob-finding**: propose candidates loosely,
test triples against the known 4″/4″ spacing, keep the best fit, and
accept only under a residual threshold. The snippet's approach — Otsu
over the frame, keep contours in an area window, take leftmost and
rightmost — fails because on a sheet of artwork those contours are the
drawing.

### `residual_px`, defined

**The RMS distance, in canonical-field pixels, between where the fitted
transform says each landmark should be and where it was actually
observed.** Landmarks are the three peg centroids and the four paper
corners; the model is the known bar geometry and the known sheet
rectangle. It is the disagreement between a rigid-body model and reality.

Report RMS *and* max *and* the per-landmark breakdown — one bad corner
from a dog-ear looks completely different from a uniformly poor fit, and
only the breakdown distinguishes them. Rough reading: **under 1 px is
healthy; over 2 px means something in the scene is wrong, not merely
noisy.**

### Rejection in the widget

ComfyUI supports exactly what you asked for. `io.NodeOutput` takes a
`ui=` payload, `ui.PreviewText` renders text on the node, and core
precedent returns values *and* text together (`nodes_save_3d.py:876`:
`NodeOutput(mesh, info, ui=UI.PreviewText(info))`).

So a rejection surfaces four ways, deliberately:

1. **On the node** — `ui.PreviewText` with the reason, visible without
   wiring anything up.
2. **As a `STRING` output** — composable, so a report node can collect a
   whole batch.
3. **Burned into the overlay image** — so an ordinary `PreviewImage`
   shows it, with the failed fit drawn on the frame.
4. **As a per-frame flag inside `ACME_POSE`** — so downstream nodes can
   filter programmatically.

**Never by raising**, and never via `block_execution`: one bad frame in a
batch of two hundred must not kill the run. Rejection is data.

Reasons are specific and carry their numbers:

```
accepted            residual 0.41 px (max 0.62, corner NE)
no_candidates       found 1 peg-like region, need 3
no_consistent_triple 7 candidates, none matching 4.00"/4.00" +/- 2 mm
residual_too_high   3.2 px > 1.5 px threshold — check for paper curl
paper_not_found     no closed quadrilateral; outline supplies the 4th DOF
ambiguous_orientation paper mass 51/49 either side of the bar line
out_of_plane        corners inconsistent with a plane by 2.8 mm
exposure            17% of frame clipped; peg segmentation unreliable
```

The last four are the useful ones: each names a physical cause the
operator can act on.

### Bar above or below

An explicit `bar_position` control — `below` (Disney) / `above` / `auto`
— because the two studio conventions both exist and the bar is
180°-symmetric, so geometry alone cannot tell them apart. `auto` compares
paper mass either side of the peg line and is right whenever the sheet is
visible; the explicit setting exists for when it isn't, and because a
silent wrong guess flips every drawing in a scene.

---

## 8. Capture hygiene

**Lock everything.** Auto white balance, auto exposure and autofocus must
all be off. This is not only about consistent colour — §9's pencil
separation is a linear solve against measured ink colours, and it is
simply invalid if the white point moves between frames.

**Avoid chroma subsampling.** A 4:2:0 stream samples colour at half
resolution, which is precisely the wrong trade for thin carmine lines.
Shoot RAW, or 4:4:4 if RAW is unavailable.

**Flash: yes, and it solves the display problem.** A display under the
paper contributes only what transmits through the sheet; a flash from
above can exceed that by one to two orders of magnitude, so its
contribution becomes a small fixed offset. Subtracting a
display-showing-black reference frame removes even that.

But flash on graphite has a trap: **graphite is specular.** A direct
flash puts highlights on exactly the dark strokes you are trying to
measure, locally inverting contrast. The standard fix for photographing
pencil artwork is **cross-polarisation** — a polarising filter on the
light, an analyser on the lens, crossed — which extinguishes the specular
component and leaves the diffuse. Cheap, and worth doing from the start
rather than discovering later.

**Blanking interlock**: designed for, not required. The capture node
takes an optional "display reference" frame and subtracts it when
present. With no light table this input is simply unused, and the hook
costs nothing now.

---

## 9. Colour: separate the pencils, don't threshold them

Rev 1's grayscale line extraction is withdrawn. Undercolour for blocking
and instruction is part of the working method, the colour is the artist's
choice — non-photo blue historically, then carmine, and Dr. Boulos
prefers carmine — so **nothing may be hardcoded**.

Thresholding on hue is the wrong instrument. The right one is **linear
unmixing**. Under fixed illumination and locked white balance, each pixel
is a mixture of a small number of materials with measured colours:

```
observed_linear_RGB  =  a·paper + b·graphite + c·undercolour
```

Three channels, three materials — **exactly determined**, solvable per
pixel with a non-negative least-squares fit, yielding a *density map* per
material rather than a mask. Density maps preserve pencil pressure, which
matters: the acceptance note records that traceback liveliness comes
precisely from line variation, and binarising at capture throws that away
before anyone can choose.

The undercolour is not assumed, it is **measured**: the artist scribbles
a swatch of each pencil on a sheet of the same stock, once, and that
calibrates a `PENCIL_PALETTE`. Any colour, any artist, no code change.

Prerequisites, all of which are cheap and none of which are optional:
undo the sRGB transfer curve so the mixing is linear; flat-field to
remove illumination gradient; keep white balance locked.

### The honest limit

**Three RGB channels cleanly separate paper plus graphite plus *one*
colour.** Blocking in carmine *and* instructions in a second colour is
four unknowns from three measurements — solvable only with a sparsity or
smoothness prior, and less reliably. Two ways out if it becomes real:
keep blocking and instructions in the same pencil, or capture two frames
under different illuminants (white and amber flash), which gives six
channels and restores headroom. Worth knowing before the working method
hardens around two undercolours.

---

## 10. Node set

```
ACME_CALIBRATION   lens intrinsics per camera, peg model, sheet size,
                   field definition, bar_position
ACME_POSE          per-frame homography + residual + accepted + reason
PENCIL_PALETTE     measured linear RGB per pencil, from a swatch sheet
```

**Phase 1 — registration**

| node | in | out |
|---|---|---|
| `AcmeCalibrateLens` | `IMAGE` batch of a checkerboard | `ACME_CALIBRATION` |
| `AcmeCalibrationLoad` / `Save` | file | `ACME_CALIBRATION` |
| `AcmeDetectSheet` | `IMAGE`, `ACME_CALIBRATION` | `ACME_POSE`, `IMAGE` overlay, `STRING` report |
| `AcmeRegister` | `IMAGE`, `ACME_POSE`, `ACME_CALIBRATION` | `IMAGE` canonical, `MASK` valid |
| `AcmeRegistrationReport` | `ACME_POSE` | `STRING`, `IMAGE` residual plot |
| `AcmeFilterByResidual` | `IMAGE`, `ACME_POSE` | accepted / rejected batches |

**Phase 2 — pencils**

| node | purpose |
|---|---|
| `AcmePencilPaletteCalibrate` | swatch sheet → `PENCIL_PALETTE` |
| `AcmeFlatField` | divide by a blank-paper reference |
| `AcmeUnmixPencils` | registered `IMAGE` + palette → one density `IMAGE` per material |

**Phase 3 — identification and QA**

| node | purpose |
|---|---|
| `AcmeReadSheetId` | the identifiers written in the control colour, off the control-colour density map, linking sheets to the externally authored timing chart |
| `AcmeFieldGuideOverlay` | see below |

`AcmeReadTimingChart` is **withdrawn**. The timing chart is a separate,
digitally-born artifact — a table, not something read off paper. What
must be read off paper is only the sheet identifier, and unmixing hands
that over on a clean channel.

### What `AcmeFieldGuideOverlay` is for

Two things, one of them a production need rather than debug decoration.

*Production:* the field guide is the framing chart. Drawn over a
registered capture it shows whether the artwork actually falls inside the
shot — a drawing that strays outside the field will be cropped in the
final, and the artist wants to know at the desk, not in the edit.

*QA:* it is what you look at when `residual_px` says everything is fine
and something still feels wrong. A number cannot show you that the fit
locked onto the wrong three blobs; a picture with the model drawn over
the observation shows it instantly.

If it earns its place only as a debug aid it can be deferred. I think the
field-boundary use makes it worth phase 3.

---

## 11. Packaging

OpenCV is **declared** in the pack's own `requirements.txt` —
`opencv-contrib-python`, since ArUco remains available for the
world-reference fiducial of §6 even though rev 0 does not use it. It is
not a ComfyUI dependency and is not currently in the `storymator` env.

```
storymator/comfyui/comfyui-acme/
    __init__.py            exports comfy_entrypoint()
    nodes/                 thin adapters: tensors in, tensors out
    acme/                  the arithmetic, importable and tested
                           without ComfyUI running
    requirements.txt
```

Installed by symlink into `ComfyUI/custom_nodes/`. The arithmetic stays
out of the node classes so the acceptance harness can call it directly —
and, as noted, so it can be tested without standing up a graph.

---

## 11a. What is implemented — 2026-09-18

Phase 1 is in `comfyui/comfyui-acme/`. Seven nodes load and their
schemas validate against ComfyUI 0.35.0; 24 tests pass against
synthetic captures with exact ground truth, covering rotation to ±25°,
keystone, sensor noise, camera moves between frames, and every refusal
path. End to end on a four-frame batch including a deliberately bad
frame: **0.38 px mean residual, 0.42 px max**, the bad frame refused
with a reason, batch alignment preserved.

**Four things the implementation changed about the design.**

**The outline must be found to sub-pixel, and that is not optional.** A
thresholded mask's boundary sits half a pixel inside the true edge on
every side, shrinking the detected sheet by about a pixel in each
dimension — a 0.13 % scale error, which put 1.8 px of residual on the
pegs. Stage two cannot absorb it, because that fit is rigid and has no
scale freedom *by design*. Edges are now located as the centroid of the
intensity gradient along the surface normal, which is unbiased whatever
the threshold was.

**Sides must be assigned in the sheet's frame, not the image's.** The
obvious assignment — nearest image axis — mis-sorts points near the
corners as soon as the sheet is rotated and collapses entirely past
about 20°, which is an ordinary camera placement. The mask's principal
axes fix it.

**Otsu is the wrong threshold here, twice over.** For the sheet against
its ground, a bimodal histogram with a wide empty gap gives *identical*
between-class variance for every threshold in that gap, so `argmax` is
arbitrary. For the pegs, which are ~0.2 % of the sheet's area, there is
no second mode to find at all — any split-the-modes method is really
choosing where to cut the paper, and it fails the moment there is
sensor noise. Replaced by a percentile midpoint and a paper-relative
threshold respectively. (A genuine bug hid inside this: dividing by a
zero class weight gives infinity, and `np.nan_to_num` turns infinity
into a very large finite number, so the implementation returned the
last bin for every image. Invisible on clean frames.)

**Search pairs, not triples.** The two rectangular pegs are 2 × spacing
apart with the round peg at their midpoint, so each qualifying pair
determines where the third must be. That turns an O(n³) scan into
O(n²), which on a noisy frame is the difference between seconds and
four minutes — and noisy frames are the ones that generate the most
candidates.

Also worth knowing operationally: `px_per_mm` sets the output raster,
and the default 11.63 over a 10.5 × 12.5 in sheet is a 3149 × 3740
frame, about 12 Mpx. Batch size costs memory accordingly.

## 11b. First real capture — 2026-09-18

`AcmeCalibrateLens` is built (OpenCV 5.0.0 installed; the suite passes
against 4.11 and 5.0). Synthetic checkerboards recover fx to 0.3 %,
principal point to 4 px and k1 to 0.011, at 0.22 px reprojection rms.
Landmarks are undistorted rather than the frame — exact, free, and it
leaves the pixels the warp still has to sample untouched.

**Three things only a real photograph could have taught us.**

*The peg spacing test had to move into millimetres.* On `training-1`
the two halves of the bar project to **778 px and 564 px** — a 38 %
difference for two spacings equal to a thousandth of an inch on the
bar. Any equal-spacing test in image space is testing the camera
angle. The test now runs after the outline homography, where the
spacings really are equal. This also broke a circularity: the punched
edge was identified from the pegs, and the pegs needed the edge. Now
four orientation hypotheses are enumerated and the bar's own geometry
picks the winner.

*Registration could mirror the sheet.* The orientation search
enumerated corner *swaps* — reflections — alongside rotations, and
`eigh`'s arbitrary eigenvector signs let the corner winding flip
between frames. Two captures of the same sheet registered to |y|
agreeing within 0.03 mm and the sign disagreeing. Rotations only now,
plus an explicit refusal of any fit with negative determinant.

*The pegs are specular metal.* The dark blob is whichever part of each
peg happens to be shaded, and at a loose threshold it merges with the
cast shadow; at a tight one the peg fragments. Neither gives the peg's
centre. Detection nonetheless finds all three correctly — verified
against the overlay — so this is a centroid-accuracy problem, not a
detection one.

**Where the error actually is.** With the outline residual now measured
against sampled edge points rather than the four corners — a homography
from four corners fits those corners *exactly*, so their residual was
measuring the peg correction and nothing else:

| term | on `training-1` |
|---|---|
| outline, i.e. curl + lens distortion | **2.28 mm** |
| peg triangle against the bar | 2.00 mm (23.4 px) |
| punch correction applied | 2.47 mm |

The frame is refused, correctly, against a 1.5 px threshold. 2.3 mm of
non-planarity on a 267 mm sheet is about 0.9 %, which is the right
order for an uncalibrated wide webcam lens plus the curl visible in the
photograph. **Lens calibration is the one term we can remove today**,
and it is now buildable: shoot a checkerboard with this camera.

Also settled from the photograph: the sheet is **10.5 in along the
bar**. Solving for the along-bar dimension that makes the peg spacing
come to 101.6 mm gives 10.63 in — and gives the *same* 10.63
whatever perpendicular dimension is assumed, because a rectangle's
aspect cannot be recovered from one perspective view without
intrinsics. That is a second, independent reason to calibrate the lens.


## 11c. The calibration boards — 2026-09-18

`AcmeCalibrateLens` now offers **ChArUco** as well as a plain
checkerboard, and ChArUco is the one to use: every corner carries an
identity, so a board pushed half out of frame still contributes — and
those are exactly the views that pin distortion down. Synthetic views
recover fx to 0.2 %, principal point to 4 px and k1 to 0.002 at 0.43 px
reprojection rms.

**The boards are 7×9 and 7×5, DICT_6X6_250, 25/18 mm**, exactly as
their printed legends state. (An earlier note here claimed the legend
was wrong about both the dictionary and the square count; that was a
misreading of a third-scale preview, and is withdrawn.)

**One of the two prints is 6.9 % off, and it is measurable from the
photographs.** Normalising each board's square size against the *sheet
of paper it is pegged to* — the same paper in both captures, so it
calibrates out camera distance — gives 97.51 against 91.20 px of square
per unit of paper. The paper edges themselves agree to within 1 %
(1838/1841/1863 against 1843/1853/1854 px), so the camera did not move
between the two shots and the difference is in the printing. The larger
board is the one that came out small, which is the signature of
fit-to-page scaling.

**It does not matter for calibrating the lens.** Scaling a board
uniformly scales the recovered extrinsic translations and leaves focal
length, principal point and distortion untouched — pinned by a test
that calibrates the same synthetic views against a board declared
6.9 % too large and asserts the intrinsics do not move. It matters only
for absolute measurement, and if two differently-scaled boards are
mixed in one run while being declared the same size.

## 11d. How to shoot the calibration set — measured, 2026-09-18

The operator asked whether the camera could be moved instead of the
board, keeping the same height and angle, because the peg bar sits at
the edge of the desk. Moving the camera is fine — calibration sees only
the *relative* pose, so moving camera or board is identical. Keeping
the same height and angle is not fine, and the cost was measured on
synthetic views with known intrinsics:

| poses | fx error | k1 (true −0.200) | rms |
|---|---|---|---|
| camera moved, orientation never changed | **42.8 %** | −0.065 | 0.472 |
| same, and height varied too | **329.9 %** | −3.655 | 0.480 |
| tilted, but always central | 0.1 % | −0.254 | 0.462 |
| tilted **and** spread to the corners | 0.9 % | −0.191 | 0.422 |

**Fronto-parallel views are degenerate**: with the board plane always
parallel to the sensor, focal length and board distance trade off
against each other and cannot be separated. Varying the height makes it
*worse*, not better, because distance is precisely the quantity focal
length is confounded with.

**And the reprojection error does not warn you.** All four runs report
an rms between 0.42 and 0.48 px. The one that is 330 % wrong looks
exactly as healthy as the one that is right. A low rms means the model
fits the points it was given; it says nothing about whether those
points constrained the model. Tilt diversity has to be assured by how
the set is shot, because no number in the output will reveal its
absence.

**So the board should not be pegged.** It never needed to be: lens
calibration wants a rigid planar target seen from many poses, and
nothing about the peg bar helps. Un-pegging removes the desk-space
constraint entirely. The reason to peg it was presumably flatness — so
mount the print on stiff card or a clipboard instead, and then it can
be held anywhere at any angle, which supplies the tilt for free.

**Fixed focus is part of the calibration.** The V4K's controls are
already set correctly — auto white balance off, exposure manual, and
`focus_automatic_continuous` off with `focus_absolute` pinned at 134.
That number is part of the calibration: intrinsics describe the lens
*at that focus*, and refocusing for a different working distance
invalidates them. Record it beside the calibration file.

## 11e. The first real calibration set — do not use it, 2026-09-18

Thirteen ChArUco captures, `data/calibration/distortion/`, board found
in all thirteen with good frame coverage (left 13 %, right 96 %, top
10 %, bottom 94 %). The calibration is nonetheless **not usable**, for
two compounding reasons that are both now fixable.

### It is under-determined, and the instability proves it

Same data, reasonable variations of the lens model:

| model | fx | cx | k1 | rms |
|---|---|---|---|---|
| all 13 frames | 2520 | 1507 | +0.157 | 2.08 |
| 8 flattest, unconstrained | **17857** (fy 1361968) | 3743 | −685.7 | 1.83 |
| 8 flattest, fx = fy | 2542 | 1663 | +0.126 | 1.06 |
| + no k3 | 3511 | 2512 | +0.067 | 1.36 |
| + no tangential | 4497 | **3182** | −0.090 | 1.80 |

Focal length swinging from 2542 to 17857 and a principal point landing
at cx = 3182 in a 3264-pixel-wide frame are not imprecision. They are
the signature of data that does not constrain the parameters: several
very different lenses explain these observations about equally well.

For scale, fx ≈ 2500 is at least *plausible* — the 10.5 in sheet spans
about 1840 px at a working distance of roughly 350 mm — so the rig is
fine and the capture set is what is wrong.

### Cause one: the board is not flat, and this dominates the residual

Fitting a homography per frame absorbs the entire pose, leaving lens
distortion (smooth, shared between frames, radial) plus the board not
being planar (per-frame, arbitrary):

```
distortion-9  (with glass)   0.88 px      distortion-2   4.52 px, max 14.4
distortion-13                0.97 px      distortion-6   5.25 px, max 12.4
distortion-5                 1.34 px      distortion-12  2.73 px, max  9.9
```

Single corners displaced by 12–14 px. No lens does that. And **the
frame shot with glass over the target is the best in the set** — which
is the experiment answering itself.

Print anisotropy was checked and ruled out: sweeping the assumed y/x
square ratio from 0.94 to 1.06 minimises rms at exactly 1.00.

### Cause two: out-of-plane tilt never varies

Recovered board tilt, every frame: **27.0° to 30.8°**, a spread of
3.8°. The board lay flat on the desk in all thirteen, so its
orientation relative to the camera is just the camera's own fixed
obliquity. Position varied beautifully; orientation did not.

Measured in isolation on synthetic views, constant tilt alone costs
about 3.6 % on fx and is survivable. It is not survivable *combined*
with a non-planar target: the degenerate direction has nothing pinning
it, so corner noise and paper curl run away along it. That is why the
unconstrained fit on the flattest eight frames diverged to fx = 17857
rather than merely being a few percent off.

### What to change

Both causes have the same fix, and the materials are now to hand.
**Mount the print on the foam board** — that removes the dominant
residual — and then *hold* it, which supplies the out-of-plane tilt
that lying on a desk cannot. Twelve to fifteen frames, tilt varied
±20–30° in both axes and genuinely different frame to frame, spread
across the frame including half off the corners.

The glass stays useful for the other job: flattening a *drawing* for a
capture, which is how the curl contribution to `training-1`'s 2.28 mm
outline residual gets separated from the lens contribution.

## 11f. Flatness budget, and why glass must not go on the target

With the rig's geometry now measured — 380 mm working distance,
fx ≈ 2500, so **6.55 px/mm on the board and 1 px = 153 µm** — the
flatness requirement can be stated as a number instead of an
exhortation. At the rig's ~30° obliquity a point lifted *h* above the
plane appears displaced by *h*·tan θ:

| lift | displacement | in pixels |
|---|---|---|
| 50 µm | 29 µm | 0.19 px |
| 100 µm | 58 µm | 0.38 px |
| 200 µm | 115 µm | 0.76 px |
| 500 µm | 289 µm | 1.89 px |

So the 0.88 px of the best frame in the distortion set corresponds to
about **134 µm** of non-flatness, and a paper wrinkle of a few hundred
microns — which is an ordinary wrinkle — costs a pixel. That is the
standard a mounted target has to meet, and it is checkable from a
single photograph with the per-frame homography residual.

**What does *not* matter is where the paper sits on the board.** The
foam board is a stiffener, not a datum. Calibration consumes only the
ChArUco corners and their assumed grid spacing; the paper's edges, the
board's edges, and the offset between them are not inputs to anything.
A 2 mm overhang is irrelevant. Stress from repositioning is not: a
locally stretched region has the wrong square spacing, and that is a
real error rather than a cosmetic one.

### Glass belongs on drawings, not on the target

A flat plate displaces whatever is under it, by an amount that grows
with viewing angle — so across a frame it varies, and it varies
*smoothly*, which is to say it looks exactly like lens distortion and
will be absorbed into the distortion coefficients.

| plate | at 5° | at 35° | spread across the field |
|---|---|---|---|
| 2 mm | 0.39 px | 3.14 px | **2.8 px** |
| 3 mm | 0.59 px | 4.71 px | **4.1 px** |
| 4 mm | 0.78 px | 6.29 px | **5.5 px** |

Several pixels of smoothly varying displacement is larger than the
flatness error glass was brought in to remove. This also qualifies the
earlier reading of `distortion-9`: its 0.88 px homography residual was
the best in the set, but a homography absorbs a uniform shift and most
of a linear gradient, and that frame covered only part of the field —
so the test that made glass look good is precisely the test that would
hide refraction. Glass genuinely fixed the flatness there. It should
still not be on the calibration target.

It remains the right tool for flattening a *drawing* — but the same
arithmetic says a glass platen in the production rig would introduce
its own few-pixel systematic, which has to be calibrated out or
designed around rather than assumed away.

## 11g. The mounted target passes — 2026-09-18

Two frames of the print mounted on foam board,
`data/calibration/distortion/v4k_01/check_mount-{1,2}.raw`. (The camera
now has a name, which is right: intrinsics belong to a camera, and a
second one is on the cards.)

Whole-board homography residuals are 1.78 and 1.48 px, against 0.88 px
for the glass reference — which reads like a fail and is not one. **The
residual is flatness plus lens distortion, and a homography absorbs
less distortion over a larger patch.** The glass frame covers 20
corners over 76 × 152 mm; the mounted frames cover all 48 over roughly
twice the area, so they are being asked to swallow far more of the lens.

Comparing patches of the same size cut from the mounted board:

| | patch | residual |
|---|---|---|
| glass reference | 76 × 152 mm, 20 corners | 0.88 px |
| check_mount-1 | median of 9 same-size patches | **0.69 px** (0.53–1.04) |
| check_mount-2 | median of 9 same-size patches | **0.63 px** (0.48–0.80) |

That flatters the mount slightly, because distortion grows with
distance from the frame centre and the glass patch sits further out
(r = 825 px) than any mount patch reaches (outermost r = 661 and 629,
giving 0.97 and 0.80 px). Matching radius properly is not possible with
these two frames.

**So the honest reading is that the mount and the glass are
indistinguishable at this precision** — both sit at roughly 0.8–1.0 px
on comparable patches, which is the lens-distortion floor plus noise,
and the two mount frames of the same physical board disagree by 0.17 px
between themselves, which sets the measurement's own repeatability.

What is not in doubt is the comparison that matters: loose paper ran to
5.25 px with single corners 12–14 px out. The mount is nowhere near
that. **It passes; do not reprint.**

Nor does the 2 mm overhang matter, for the reason in §11f: the board is
a stiffener, not a datum.

The remaining gap in the calibration set is unchanged and is not about
flatness — it is tilt diversity. A mounted board can now be held at
genuinely different angles, which is the thing lying on a desk could
never supply.

## 11h. v4k_01 calibration set two — usable, with one real gap

33 frames, board found in 28. **rms 0.647 px** against 2.08 for the
first set, fx and fy now agreeing to 0.51 % where they differed by
3.9 %, and tilt spanning 5–54° where it had spanned 3.8°. Mounting the
target and holding it fixed both problems at once.

**The calibration is stable, which is what makes it trustworthy.** fx
across five lens models: 2637.6, 2640.8, 2646.5, 2629.5, 2640.2 — a
spread of 0.6 %. The first set swung from 2542 to 17857 on the same
test. So: `fx ≈ 2640, cx ≈ 1660, cy ≈ 1199` for v4k_01 at
`focus_absolute 134`.

### Where coverage is still weak

Corner counts over an 8 × 6 grid of the frame:

```
              0    408    816   1224   1632   2040   2448   2856
  y    0      0      1      2      3     12     19     13      7
  y  408      0      1      5      9     28     60     46     15
  y  816      0      0      7     11     34     74     42     20
  y 1224      0      0      4     12     33     76     62     21
  y 1632      0      0      2      8     35     78     55     19
  y 2040      0      0      0      2     21     31     25     13
```

**The left third of the frame is empty** — 11 of 48 cells have no
corners at all and every one of them is on the left. Density peaks
right of centre.

By radius from the principal point, which is what actually pins
distortion: 80–90 % of maximum radius holds 12 corners, and **90–100 %
holds none**.

### What the outer gap costs, in pixels

Fitting four lens models to the same data and asking each for the
radial correction at a given radius. Where they agree the data
constrains the answer; where they diverge they are extrapolating:

| radius | data | free | fx=fy | no k3 | rational | spread |
|---|---|---|---|---|---|---|
| 20 % | yes | −3.53 | −3.11 | −2.98 | −2.87 | 0.66 |
| 60 % | yes | −41.37 | −38.64 | −37.95 | −38.55 | 3.42 |
| 80 % | yes | −62.19 | −58.97 | −58.40 | −58.02 | 4.18 |
| 90 % | none | −68.31 | −64.11 | −59.53 | −70.45 | **10.93** |
| 100 % | none | −72.64 | −64.73 | −44.07 | −66.49 | **28.56** |

Inside 80 % the models agree within about 4 px. At the frame corner
they disagree by **28.6 px** on a correction of roughly 70 px. The
corners are pure extrapolation — and the corners of an ACME sheet are
exactly what lands there in production.

### Lighting: underexposed, not glare

Measured on the board region rather than the whole frame, the white
squares peak at **p95 = 151–158 of 255**, and highlight clipping is
**0.0 %** in every frame. The whites should be reaching 220–240. About
40 % of the available range is going unused, and contrast is what
corner localisation is made of.

So the fix is more light, not longer exposure: the five frames where
the board was not found average a blur metric of 27 against 35 for the
frames that worked, and lengthening exposure on a hand-held board makes
that worse. Diffuse it, to avoid trading underexposure for specular
glare on the print.

### What to add

Roughly ten more frames, pooled with the existing 28 rather than
replacing them — calibration uses all views together:

* the **left third** of the frame, which has nothing at all;
* all four **frame corners**, board deliberately half out of frame;
* more light, whites reading 220–240 without clipping.

Tilt is now good and does not need changing.

## 11i. v4k_01 calibrated — usable now, 2026-09-18

48 frames (32 dropped for motion artefact), board found in 43, 1452
corners. **rms 0.730 px, fx 2625.1, fy 2627.2 — agreeing to 0.08 %** —
cx 1644.3, cy 1200.7. Stable across lens models: fx spans 2625–2634,
0.3 %, and cx spans 1641–1645.

**Validated directly rather than by rms.** A straight line must come
back straight: on calibration frame `distortion-13`, rows of board
corners bow 4.3, 3.8 and 4.2 px, and after removing the lens model they
bow 1.8, 0.8 and 1.1. The model is doing real work.

### Coverage, answered

Empty grid cells fell from 11 to 3 and the left side is now sampled.
What remains:

* **the bottom-left**, still nearly empty — the bottom row reads
  1, 0, 1, 6 across its left half;
* **nothing beyond 90 % of maximum radius**, still. The nearest corner
  samples sit 452, 245, 531 and 294 px from the four frame corners,
  and the 90 % ring runs 204 px inside each one.

Model disagreement on the radial correction at the extreme corner fell
from 28.6 px to 18.8 px, but it is still extrapolation.

**It does not currently matter.** An ACME sheet framed as in
`training-1` puts its corners at **43–75 % of maximum radius**, where
the four models agree within 4–6 px. The corner gap bites only if the
sheet is framed larger than the present rig frames it.

### A correction: the lighting is not the problem

Earlier guidance here said to add light before reshooting. Measured,
that was wrong. Grouping frames by how bright the board's whites came
out and comparing per-frame reprojection error:

```
whites p95 100-125   8 frames   mean error 0.728 px
whites p95 125-145  17 frames   mean error 0.691 px
whites p95 145-165  16 frames   mean error 0.666 px
correlation(brightness, error) = -0.00
```

The target is black-on-white and the detector has ample contrast even
at p95 = 139. Underexposure costs nothing measurable *here*. It may
still matter for capturing pencil on paper, which has a fraction of the
contrast — but that is a different measurement and should not be
inferred from this one.

### A bug this exposed

`fit_pose` undistorted the sheet corners and the peg centroids but left
the edge samples alone — and the edge samples are what the outline
residual is measured from. So a fit computed in corrected coordinates
was being compared against uncorrected observations, and applying a
*good* calibration appeared to make the outline residual worse
(26.6 → 40.0 px). Fixed; the samples are now corrected with everything
else.

### The old test captures cannot validate it

After the fix, the intrinsics still do not improve `training-1` or
`training-4`, and the straight-edge test says why: on calibration
frames undistortion straightens lines, on those two it does not, and
some edges get worse. They were shot five hours earlier, before
`focus_absolute` was pinned at 134 and recorded. Intrinsics describe a
lens at a focus; those captures are from a different one.

**So the next capture is a pegged sheet shot now, with focus untouched
since the calibration set** — after which the outline residual finally
decomposes into lens and curl.

## 12. Rev 0 plan, and what remains open

**Rev 0 scope**: one camera, one or two sheets, no disc, no light table,
30–45° tilt, locked exposure and white balance, cross-polarised if a
flash is used.

**First slice**: `AcmeCalibrateLens` → `AcmeDetectSheet` →
`AcmeRegister` → `AcmeRegistrationReport`, over real drawings, with the
camera **deliberately moved between captures** — which is now a supported
operating mode rather than a failure to survive.

Success is a residual distribution and a demonstration that bad frames —
curled paper, occluded pegs, inverted sheet, blown exposure — are refused
with a reason rather than silently mis-registered.

**Open:**

* Canson ACME bond punch tolerance relative to the trimmed edge. No
  published spec found. It bounds how much correction stage two has to
  make, and can be *measured* — register twenty sheets, look at the
  spread of the peg-versus-outline correction. Worth doing early; it is
  free and it validates the two-stage split.
* Whether the oblique stack-edge measurement (§4) works in practice.
* Whether blocking and instruction share one pencil (§9).
