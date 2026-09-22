# Calibrating a camera for the animation desk

*Procedure, written 2026-09-18 from the first one we did end to end
(`v4k_01`, an IPEVO V4K). It took three attempts and two of the
failures were invisible in the obvious quality number, so the
validation section is the important half of this document.*

Companion to [planning/acme-registration-plugin.md](planning/acme-registration-plugin.md)
§6. Data and results live under `data/calibration/`.

---

## Why bother

Two reasons, and the second surprises people.

**Distortion.** At 4K with a wide lens the radial correction reaches
about **70 px at the frame corner** — measured on the V4K. Uncorrected
that lands in the registration residual, where it is indistinguishable
from paper curl.

**Rectangle aspect.** The proportions of a rectangle *cannot be
recovered from a single perspective view* without intrinsics. Measured
on the first rig photograph: solving for the sheet's along-bar
dimension gave 10.63 in whatever perpendicular dimension was assumed,
because the perpendicular one is simply unconstrained by the geometry.

**What calibration is not for:** pose. Pose is solved per frame from
the sheet itself, so the camera can be moved, bumped, or repositioned
mid-session without invalidating anything. Nothing positional is stored.

---

## What it is a calibration *of*

Not the camera — the camera **at one focus**. Intrinsics describe a
lens at a focus setting, and refocusing for a different working
distance voids them.

So, before anything:

```sh
v4l2-ctl -d /dev/videoN --list-ctrls        # find the controls
v4l2-ctl -d /dev/videoN --set-ctrl=white_balance_automatic=0
v4l2-ctl -d /dev/videoN --set-ctrl=auto_exposure=1            # manual
v4l2-ctl -d /dev/videoN --set-ctrl=focus_automatic_continuous=0
v4l2-ctl -d /dev/videoN --set-ctrl=focus_absolute=134         # then WRITE IT DOWN
```

Give the camera a name (`v4k_01`) and a directory. Do the same for
every physical artifact whose measured properties feed a result — here
that is the board (`charuco_0001`) and the ACME bar (`honbay_0001`),
each of which needs its own re-measurement when replaced. Put a `README.md`
beside the frames recording the model and every control value. When
the second camera arrives it gets its own name, directory and
calibration — intrinsics belong to a camera, not to a project.

---

## The target

A **ChArUco** board, not a plain checkerboard. Every corner carries an
identity, so a board pushed half out of frame still contributes — and
the half-out-of-frame views are exactly the ones that pin distortion
down. A plain checkerboard must be wholly visible or it gives nothing.

Ours is **`charuco_0001`**, generated with
[CalibrX](https://calibrx.io) — 7 × 9 squares, `DICT_6X6_250`,
nominally 25/18 mm. CalibrX also served as the independent
cross-check on our own fit, agreeing to 0.36 px
([../data/calibration/distortion/v4k_01/calibrx/README.md](../data/calibration/distortion/v4k_01/calibrx/README.md)),
and gave permission to redistribute the boards as generated. Name the board, not just the
camera: its measured square size and print anisotropy are properties of
*that printed sheet*, and a reprint is a different target. **Read the parameters off the board's own printed legend at
full resolution** — reading them off a downscaled preview cost an
afternoon here, because a wrong dictionary means zero detections and
looks exactly like a broken detector.

### Mount it rigidly

This is not optional and it was our largest single error source. Loose
paper on a desk gave per-frame homography residuals up to **5.25 px
with individual corners 12–14 px out**. No lens does that. Mounted on
foam board the same measurement gives **0.63–0.69 px**.

* Spray-mount or tape across the **whole area**, not just the edges —
  edge-only tape lets the middle bow.
* Repositionable adhesive fights you and can stretch the paper. A
  locally stretched region has the wrong square spacing, which is a
  real error rather than a cosmetic one. Better to place it once.
* Clips at the corners, outside the board area, work too and undo
  cleanly.
* **Where the paper sits on the board does not matter at all.** The
  board is a stiffener, not a datum; only the ChArUco corners and their
  spacing are inputs. A 2 mm overhang is irrelevant.
* **Do not put glass over the calibration target.** A flat plate
  displaces what is under it by an amount that grows with viewing
  angle, so it varies smoothly across the frame and is absorbed into
  the distortion coefficients. A 3 mm plate spans 0.59 px at 5° and
  4.71 px at 35° — a 4.1 px spread, larger than the flatness error the
  glass was brought in to remove. Glass is for flattening *drawings*.

### Measure the print, then stop worrying about it

Ours came out **1.27 % oversize**: five squares corner to corner
measure **126.582 mm** on digital calipers (six readings, sd 0.33),
putting the square at **25.3163 mm**, se 0.027.

### Do not measure the short reference bar

The board's printed "50 mm" bar reads 51.037 outside-line to
outside-line — but the serifs are 0.53 and 0.58 mm wide, and nobody
says which convention the 50 is:

| reading of "50 mm" | true | square |
|---|---:|---:|
| outside to outside | 51.037 | 25.518 |
| centre to centre | 50.482 | 25.241 |
| inside to inside | 49.927 | 24.963 |

**A spread of 2.22 %**, on a quantity worth 1.27 %. The serifs *are*
the error bar and they swallow the measurement whole. An earlier pass
here quoted 2.07 % from this bar; it was the outside-to-outside branch
of a three-way ambiguity, and 3.9σ from the real value.

Measure **corner to corner across five squares** instead. A checker
corner is a point where four quadrants meet, with no line width to
argue about, and five squares is 126.6 mm — inside a 150 mm caliper.

The cross-checks line up:

| method | square | |
|---|---:|---|
| 5 squares, calipers | 25.316 ± 0.027 | — |
| 9 squares at 228 mm, ruler | 25.333 ± 0.111 | +0.1σ |
| 7 squares at 178 mm, ruler | 25.429 ± 0.143 | +0.8σ |
| 50 mm bar, outside-to-outside | 25.518 ± 0.044 | **+3.9σ** |

The 9-square ruler reading agrees to 0.02 mm. Only the bar is out.

**What limits this is technique, not the caliper.** Six readings gave
sd 0.33 mm on 126.6 mm — 0.26 %, twenty-five times the caliper's own
0.01 mm. A checker corner is a *virtual* point and a jaw cannot seat on
it; you are eyeballing the jaw against a corner. Take six readings, not
three, and treat the scatter as the error.

**It does not affect the intrinsics.** Scaling a board uniformly scales
the recovered extrinsic translations and leaves focal length, principal
point and distortion untouched. Verified on the real set: 25.00 mm and
25.40 mm give rms 2.0821 both ways and fx agreeing to six significant
figures; what moved was the mean board distance, 375.5 → 381.5 mm,
a ratio of exactly 1.0160. The correction from 25.400 to 25.3163 likewise
moves only the working distance, 380 → 378.8 mm.

So measure it for absolute work and for mixing boards — not because
the calibration needs it.

---

## Shooting the set

Twelve to fifteen frames minimum; we ended with 55 and used 50. Three
requirements, and they are independent:

### 1. Tilt must vary — this is the one that is easy to miss

Our first set had beautiful frame coverage and **every frame tilted
27–31°**, a spread of 3.8°, because the board lay flat on a desk and
that 29° was just the camera's own obliquity. Position varied;
orientation did not.

Fronto-parallel views are **degenerate**: with the board plane parallel
to the sensor, focal length and board distance trade off against each
other and cannot be separated. Measured on synthetic views with known
intrinsics:

| poses | fx error | k1 (true −0.200) | rms |
|---|---|---|---|
| camera moved, orientation fixed | **42.8 %** | −0.065 | 0.472 |
| same, and distance varied too | **329.9 %** | −3.655 | 0.480 |
| tilted, always central | 0.1 % | −0.254 | 0.462 |
| tilted **and** spread | 0.9 % | −0.191 | 0.422 |

Varying the *distance* makes it worse, not better — distance is
precisely what focal length is confounded with.

Aim for ±20–30° in both axes plus some roll, **visibly different frame
to frame**. A mounted board can be held; a board on a desk cannot tilt.

### 2. Cover the frame

Grid the image and count corners per cell. Our first set left the
entire left third empty — 11 of 48 cells with nothing.

### 3. Cover the *radius* — the one that stayed broken longest

Distortion is pinned by the outermost samples, and this is not the same
as covering the frame. After three rounds we still have **nothing
beyond 90 % of maximum radius**, with the nearest samples 245–598 px
from the four frame corners.

What that costs, asking four lens models fitted to the same data for
the radial correction:

| radius | data | spread between models |
|---|---|---|
| 60 % | yes | 3.4 px |
| 80 % | yes | 4.2 px |
| 90 % | none | 10.9 px |
| 100 % | none | **18–29 px** |

Inside 80 % the models agree within ~4 px. At the corner they disagree
by 18–29 px on a correction of ~70 px. That is not a calibration, it is
four opinions.

**To fix it a board *corner* must land within about 200 px of a *frame*
corner** — the board hanging out of frame on two sides. Getting near
the edge is not enough; the radius maximum is at the corners.

### What does *not* need fixing: exposure

We spent effort on this and it was misplaced. Grouping frames by how
bright the board's whites came out:

```
whites p95 100-125   8 frames   mean error 0.728 px
whites p95 125-145  17 frames   mean error 0.691 px
whites p95 145-165  16 frames   mean error 0.666 px
correlation(brightness, error) = -0.00
```

A black-on-white target has ample contrast even at p95 = 139. This says
nothing about capturing pencil on paper, which has a fraction of the
contrast — do not carry the conclusion across.

---

## Running it

```
AcmeCalibrateLens
    board_type        charuco
    columns 7   rows 9
    square_mm 25.3163 marker_mm 18.228    # measured, not nominal
    aruco_dictionary  DICT_6X6_250
```

Then `AcmeCalibrationSave` to a file named for the camera.

---

## Validating — the important part

**The reprojection error does not tell you whether the calibration is
good.** In the synthetic test above, the run that was 330 % wrong
reported rms 0.480 and the correct one 0.422. A low rms says the model
fits the points it was given; it says nothing about whether those
points constrained the model.

Four checks that do work, in order of usefulness:

### 1. Stability across lens models — the decisive one

Refit the same data with several models. If the answers move, the data
does not constrain them.

```
              bad set (13 frames)        good set (50 frames)
free            fx 2520                    fx 2625.1
fx=fy           fx 2542                    fx 2626.4
no k3           fx 3511                    fx 2630.1
no tangential   fx 4497                    fx 2629.5
rational        fx 17857  cx 3743          fx 2633.8
```

The bad set put the principal point at cx = 3743 in a 3264-px-wide
frame. The good set spans 0.3 %. **That spread is the honest
uncertainty.**

### 2. fx ≈ fy, and the principal point near centre — with a caveat

Square pixels are near-universal, so fx and fy should agree closely.
Ours: **0.11 %** (the bad set: 3.9 %).

**But fx/fy partly measures the target, not the camera.** A board whose
print is anisotropic maps that anisotropy straight into fx/fy. Ours is:
refitting with the board's x and y scaled independently,

| board anisotropy | rms | fx/fy − 1 |
|---:|---:|---:|
| −0.380 % (reversed, control) | 0.8644 | −0.320 % |
| 0 % (isotropic) | 0.7215 | −0.097 % |
| +0.100 % | 0.7089 | −0.035 % |
| **+0.150 %** | **0.7070** | **−0.003 %** |
| +0.200 % | 0.7082 | +0.029 % |
| +0.380 % (what the calipers said) | 0.7366 | +0.149 % |

Two independent criteria — minimum rms and fx = fy — agree at the same
point, **+0.15 %**. So the whole of our 0.11 % fx/fy discrepancy was the
print, and the camera's pixels are square to 0.003 %.

Three things follow. **fx ≈ fy is a weaker check than it looks**, and a
fx/fy discrepancy under a few tenths of a percent should be blamed on
the target before the sensor. **The data measures the board better than
calipers do** — the calipers said +0.38 % ± 0.26, and the calibration
pins it at +0.15 %. And **the reversed control is much worse**
(rms 0.8644), which is what makes this a measurement rather than a
free parameter absorbing noise.

Uniform scale still does not matter: 25.3163 and 25.400 give rms 0.7215
and fx 2624.44 both, identical to six figures. Only the *ratio* does. cx/cy should sit within a few
tens of pixels of the frame centre — ours are 1644.8 and 1203.7 against
1632 and 1224.

### 3. Straight lines must straighten

On a **rigid board**, rows of corners should bow less after correction.
Ours: 4.3, 3.8, 4.2 px → 1.8, 0.8, 1.1 px.

**Do not run this test on paper.** A curled sheet's edges are not
straight to begin with, so removing a correct lens model can leave
*more* bow. We got a false "does not apply" from exactly this mistake,
twice.

### 4. rms, last

Useful as a floor, not a verdict. Under ~0.8 px is healthy; 2 px says
something is wrong but not what.

---

## Result for v4k_01

```
48 of 55 frames, 1590 corners
isotropic board:   rms 0.7215   fx 2624.44  fy 2627.00  (0.097 %)
board +0.15 % aniso: rms 0.7070   fx 2625.44  fy 2625.52  (0.003 %)   <- adopt
cx 1645.1   cy 1204.2   (frame centre 1632, 1224)
focus_absolute 134
working distance ~380 mm, 6.55 px/mm on the target, 1 px = 153 um
```

Known gap: nothing beyond 90 % radius, so the correction at the extreme
corners carries ~18 px of uncertainty. It does not currently matter —
an ACME sheet at this framing puts its corners at 43–75 % of maximum
radius, where the models agree within 4–6 px — and it would matter at
wider framing.

---

## Next time: the tool this wants

Doing it by hand cost three rounds, and each failure was a *coverage*
failure invisible in the output numbers. The diagnostics that actually
found them are all cheap, and all belong in one place — ideally running
**during** capture, because the expensive part was shooting 33 frames
and learning afterwards that the set was degenerate.

Proposed as `AcmeCalibrationCoverage`, taking an `IMAGE` batch and
board parameters and emitting a diagnostic image plus a text verdict:

| panel | shows | why it earned its place |
|---|---|---|
| **frame coverage** | corner counts on a grid, empty cells flagged | found the empty left third |
| **radius histogram** | counts per 10 % band of max radius, with the ≥90 % band called out | the failure that survived three rounds; invisible in the coverage grid |
| **tilt histogram** | out-of-plane angle per view | found the 27–31° degeneracy, which frame coverage cannot show |
| **roll** | in-plane rotation per view | cheap, and diversity here helps the principal point |
| **per-frame residual** | homography rms per frame, worst flagged | separates a bent target or a blurred frame from a bad lens |
| **model stability** | fx and cx across 4–5 model variants | the single best trustworthiness test, and nobody runs it by hand |
| **verdict** | what is missing, in words | "no samples beyond 80 % radius — put a board corner in a frame corner" |

Two design notes from the experience:

* **The verdict must be prescriptive.** "Coverage is weak at high
  radius" is not actionable; "a board corner must land within 200 px of
  a frame corner" is.
* **Show tilt and radius side by side.** They fail independently and
  each looks fine while the other is broken — our set two had excellent
  tilt and no outer radius, set one the reverse.

A live view with these updating as frames are added would turn a
three-round process into one.
