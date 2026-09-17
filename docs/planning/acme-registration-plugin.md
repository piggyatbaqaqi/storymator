# ACME registration as a ComfyUI plugin — design

*2026-09-17. Design for the capture-and-register stage identified as the
first milestone in
[inbetween-acceptance.md](inbetween-acceptance.md) §5.*

Targets **ComfyUI 0.35.0** and its V3 schema API (`comfy_api.latest`,
`io.ComfyNode`, `define_schema`/`execute`, `ComfyExtension` +
`comfy_entrypoint`). The 0.28 dict-style `INPUT_TYPES` API is not used.

---

## 1. What this has to produce

From photographs of drawings on a pegged animation disc:

* every drawing in **one coordinate system**, so frame *n* and frame
  *n+1* can be compared, onion-skinned, differenced, or fed to anything
  downstream;
* **paper removed**, line preserved;
* the **timing chart** read off the keys;
* and a **per-frame residual in pixels**, because that is the number the
  acceptance harness is built on and the number that says whether a
  frame should be thrown away.

The residual is not a nicety. Every measurement in the acceptance note —
arc deviation, spacing fraction, joint onset order — is taken across
registered frames. A silent registration error becomes a fake violation
of an animation principle. **The plugin must be able to say "I do not
trust this frame."**

---

## 2. The central decision: two transforms, calibrated at different rates

The instinct in `snippets/dtect_peg_bar_orientation.py` is to find the
pegs, compute an angle, and rotate. That cannot work, for a reason worth
stating plainly:

> **Three collinear points do not determine a homography.** A homography
> needs four points in general position. The three ACME pegs are
> deliberately, exactly collinear.

So per-frame perspective cannot be solved from the pegs. It does not
need to be. Split the problem by how fast each part changes:

| transform | what it is | solved from | changes when |
|---|---|---|---|
| **H_desk** | camera pixels → desk-plane millimetres. Full homography; removes perspective and lens scale. | a calibration target (checkerboard or ArUco board) laid on the disc | the camera or desk moves — i.e. rarely |
| **T_frame** | desk plane → canonical field coordinates. **Rigid: rotation + translation, 3 DOF.** | the three peg centroids | every capture, because the artist rotates the disc |

Composed: `canonical = T_frame ∘ H_desk ∘ pixel`.

This is what makes the per-frame problem easy instead of impossible.
Three points solving three degrees of freedom is over-determined by
design: the fit is closed-form (2-D Procrustes), needs no iteration and
no RANSAC, and **the leftover disagreement between the observed peg
triangle and the known bar is the residual** — the quality signal,
obtained free.

### Scale must not be a free parameter

Solve **rigid**, not similarity. Rotating a disc does not change scale,
and a free scale parameter would quietly absorb detection error by
shrinking the drawing — an error that looks like nothing and corrupts
every spacing measurement downstream. Scale comes from `H_desk` and is
held fixed.

That makes §3's height question load-bearing rather than pedantic.

### Register to the field, not to frame 1

The canonical target is **ACME field coordinates**, not "whatever frame
1 happened to look like". Three reasons: a scene stays comparable to
every other scene; the field guide becomes meaningful, so cropping and
the chart's expected location are defined; and it is the only thing that
makes a **camera array** tractable — the desk design calls for one,
angled to avoid hand obscuration. Each camera gets its own `H_desk` and
all of them land in the same canonical frame. Registering to a reference
*frame* would give every camera a different answer.

---

## 3. Three physical facts that change the design

### 3.1 The peg tops and the drawing surface are not the same plane

The pegs protrude *above* the paper. If you register on peg tops you
have registered a plane that is not the one being drawn on, and the
offset between them is the stack thickness — which grows as the scene
does.

The magnitude is not negligible. At a 400 mm working distance, a
100-sheet stack of about 10 mm is a **2.5 % scale error**, which on a
2000-pixel-wide field is **50 pixels**. That is catastrophic for a
process whose whole point is sub-pixel comparison.

Options, in order of preference:

1. **Shoot one sheet at a time** against the disc, so the drawing plane
   is constant. The problem disappears entirely. Whether the rig can
   work this way is a question for Daniel (§7).
2. **Model it.** Peg height is known and stack thickness is predictable
   from sheet index; correct the scale analytically.
3. **Triangulate it.** With the camera array already specified, two
   calibrated views recover the paper plane directly. This is the
   payoff of having more than one camera, and it argues for doing the
   calibration properly rather than per-camera-independently.

This must be settled before any number claims to be sub-pixel.

### 3.2 The under-glass display is in the optical path

The desk specifies a motorized disc "traditionally backed by a frosted
light" and an under-glass display for the live motion loop. Backlighting
is a gift for line extraction — paper transmits, graphite blocks, and
contrast is enormous. But a *display* under the paper is not a uniform
light source: whatever it is showing, typically the previous drawing,
will be photographed straight through the sheet.

So capture and display need an interlock: **blank the under-glass
display, or show a known flat field, for the exposure.** This is a
hardware/software boundary that neither side will discover on its own,
and it is much cheaper to design in now than to subtract out later.

### 3.3 The bar is 180°-symmetric

Round centre peg, two oblong side pegs, evenly spaced: rotating the bar
by 180° maps it onto itself. Peg geometry alone therefore cannot tell
upright from upside-down, and an artist working on a rotating disc will
absolutely hand you an upside-down capture.

The disambiguator is the **paper**, which lies entirely on one side of
the bar. Take the paper mask centroid, compare which side of the peg
line it falls on, flip if needed. Cheap and reliable.

---

## 4. Detection: fit a known object, do not find blobs

The peg bar is a rigid body with known landmark geometry. That makes
this a **fitting** problem, not a detection problem, and the difference
is what separates a demo from something that can run unattended.

The snippet's approach — Otsu over the whole frame, `RETR_EXTERNAL`,
keep contours between 100 and 50 000 px, take leftmost and rightmost —
fails because on a sheet of *artwork* those contours are the drawing.
A character's eyes, knuckles and hatching all land in that area window,
and leftmost/rightmost of a contaminated list is noise by construction.

Instead:

1. **Propose.** Blob detection is fine *as a proposal stage*. Over-
   generate; precision does not matter yet.
2. **Fit.** For each candidate triple, solve the rigid transform that
   best maps the known peg model onto it, and score by residual.
3. **Accept or refuse.** Keep the best fit only if its residual is under
   threshold. Otherwise emit no pose and flag the frame. A registration
   tool that refuses is worth more than one that always answers.

The peg model itself is **calibrated, not hardcoded**. Nominal ACME
geometry — a round centre peg with oblong pegs either side, on the order
of four inches centre-to-centre — should be a *default that the operator
confirms against their own bar*, because the bar in the room is the
ground truth and bars vary. `AcmePegModelCalibrate` measures it once
from a reference capture.

### The cheaper alternative, if the rig allows it

If a fiducial can be fixed to the bar or the disc, ArUco markers give
sub-pixel corners, unique IDs, and — being four non-collinear corners
each — a **full homography from a single marker**, which collapses §2's
two-transform scheme into one and sidesteps the collinearity problem
altogether. Roughly twenty lines against a detector that needs tuning.

This is a rig question, not a software one, and worth asking before
detector work is paid for. Note it requires `opencv-contrib-python`,
which matters for §6.

---

## 5. Node design

ComfyUI style is small composable nodes plus typed edges. Custom types
carry the structured data that is not a tensor:

```
ACME_CALIBRATION   H_desk per camera, peg model, field definition, units
ACME_POSE          per-frame (θ, tx, ty) + residual + accepted flag
TIMING_CHART       parsed chart: ordered fractions, frame numbers
```

Declared with `io.Custom("ACME_CALIBRATION")` and friends.

Batches map naturally: a stack of drawings **is** a ComfyUI `IMAGE`
batch of shape `(B, H, W, C)`, float 0..1. `ACME_POSE` therefore carries
a list of length B, and every node must preserve batch alignment —
including the refusal case, which is why refusal is a *flag* rather than
a dropped element.

### Phase 1 — registration core

| node | in | out |
|---|---|---|
| `AcmeCalibrationLoad` / `Save` | file | `ACME_CALIBRATION` |
| `AcmeCalibrateDeskPlane` | `IMAGE` of a calibration target, camera id | `ACME_CALIBRATION` (H_desk) |
| `AcmePegModelCalibrate` | `IMAGE`, `ACME_CALIBRATION` | `ACME_CALIBRATION` (+ peg model) |
| `AcmeDetectPegBar` | `IMAGE`, `ACME_CALIBRATION` | `ACME_POSE`, `IMAGE` (debug overlay), `FLOAT` (residual) |
| `AcmeRegister` | `IMAGE`, `ACME_POSE`, `ACME_CALIBRATION` | `IMAGE` (canonical field), `MASK` (valid area) |
| `AcmeRegistrationReport` | `ACME_POSE` | `STRING`, `IMAGE` (residual plot) |

`AcmeRegistrationReport` is not a convenience. It is where the
milestone's success criterion — *registration residual in pixels on real
drawings* — actually gets measured, so it ships in phase 1, not later.

### Phase 2 — line art

| node | in | out |
|---|---|---|
| `AcmeFlatField` | `IMAGE`, flat-field `IMAGE` | `IMAGE` |
| `AcmeExtractLineArt` | `IMAGE`, `MASK` | `IMAGE` (line, paper removed), `MASK` (paper) |

Flat-fielding — divide by a once-captured frame of blank paper under the
same light — handles light-box non-uniformity and lens vignetting
together, and is far more robust than any adaptive threshold.

**Output grayscale, not binary.** Pencil pressure carries information
and the pencil test is judged on the artist's own line. The acceptance
note records that a *traceback* — the same drawing traced three or four
times — stays alive on screen precisely because of line variation, and
that digital paint lost that quality. Binarising at capture throws it
away before anyone can decide whether they wanted it. Binarisation is a
separate optional node for consumers that need it.

### Phase 3 — chart and QA

| node | purpose |
|---|---|
| `AcmeReadTimingChart` | the chart is the specification; reading it is part of capture |
| `AcmeFieldGuideOverlay` | draw field grid and fitted peg positions over a registered frame |
| `AcmeFilterByResidual` | split a batch into trusted and rejected |

Registration is what makes chart reading tractable at all: in canonical
field coordinates the chart lands in a predictable place, so the
recogniser gets a small fixed region instead of a search.

---

## 6. Packaging, dependencies, and one real constraint

**OpenCV is not present.** The ComfyUI runtime here is the `storymator`
conda env — torch 2.13.0+cu130, numpy 2.5.1, scipy 1.18.0, Pillow 12.3.0
— and OpenCV is not a ComfyUI dependency and is not installed. Two
honest options:

* **Declare it.** A custom-node pack ships its own `requirements.txt`,
  which is the normal ComfyUI arrangement. `opencv-contrib-python` if
  ArUco is wanted, plain `opencv-python` otherwise.
* **Avoid it.** Blob proposals via `scipy.ndimage.label`, the rigid fit
  in closed form with numpy, the warp with `torch.nn.functional.
  grid_sample` on the GPU. Homography *estimation* for calibration is
  the only genuinely awkward piece, and it runs rarely.

Recommendation: **declare OpenCV.** Re-deriving `findHomography` to
avoid a dependency is not a good trade, and ArUco is a live option that
needs it. But note the avoidance path exists, because it is short.

Layout — develop in this repository, install by symlink, which is the
standard ComfyUI dev pattern and keeps the code under version control
here rather than inside the ComfyUI checkout:

```
storymator/comfyui/comfyui-acme/
    __init__.py            exports comfy_entrypoint()
    nodes/…                one module per phase
    acme/…                 the actual maths, importable and testable
                           without ComfyUI running
    requirements.txt
```

```sh
ln -s …/storymator/comfyui/comfyui-acme \
      …/Comfy-Org/ComfyUI/custom_nodes/comfyui-acme
```

**Keep the maths out of the node classes.** `acme/` should be plain
functions over numpy arrays with their own tests; the node classes are a
thin adapter that converts tensors, calls them, and wraps results in
`io.NodeOutput`. Otherwise nothing is testable without standing up a
whole graph, and the acceptance harness needs to call this code
directly.

Shape of a node, for the record:

```python
class AcmeDetectPegBar(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="AcmeDetectPegBar",
            display_name="ACME Detect Peg Bar",
            category="storymator/acme",
            inputs=[
                io.Image.Input("image"),
                io.Custom("ACME_CALIBRATION").Input("calibration"),
                io.Float.Input("max_residual_px", default=1.5,
                               min=0.1, max=50.0, step=0.1),
            ],
            outputs=[
                io.Custom("ACME_POSE").Output("pose"),
                io.Image.Output("overlay"),
                io.Float.Output("residual_px"),
            ],
        )

    @classmethod
    def execute(cls, image, calibration, max_residual_px) -> io.NodeOutput:
        ...
```

---

## 7. Open questions — rig, not software

These change the design rather than the implementation, so they are
worth asking before code is written.

1. **One sheet, or the top of a stack?** §3.1. If capture is of a single
   sheet against the disc, the drawing plane is constant and scale is
   fixed. If it is the top of a growing stack, scale varies by a few
   percent and must be modelled or triangulated. This is the single most
   consequential answer.

2. **How many cameras, and are they fixed?** The desk specifies an
   array angled to avoid hand obscuration. Fixed cameras make `H_desk` a
   one-time calibration; a movable or handheld camera makes it per-shot
   and much harder.

3. **Can a fiducial go on the bar or the disc?** §4. If yes, ArUco
   collapses the whole transform problem and the peg detector becomes
   optional.

4. **Is the under-glass display on during capture?** §3.2. If yes, we
   need a blanking interlock or a subtraction step.

5. **What is the actual bar?** Measured peg spacing and diameters from
   the bar in the room, and the paper and field sizes in use. The
   nominal values become defaults; the measured ones become the
   calibration.

---

## 8. Suggested first slice

Narrow, and it produces the milestone number:

`AcmeCalibrateDeskPlane` → `AcmeDetectPegBar` → `AcmeRegister` →
`AcmeRegistrationReport`, over a stack of real drawings shot on the
actual rig, with the disc **deliberately rotated between captures**.

Success is not a pretty picture. It is a residual distribution, and a
demonstration that deliberately bad frames — out of plane, occluded
pegs, upside down — are refused rather than silently mis-registered.

Everything after that has somewhere to stand.
