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
