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

Give the camera a name (`v4k_01`) and a directory. Put a `README.md`
beside the frames recording the model and every control value. When
the second camera arrives it gets its own name, directory and
calibration — intrinsics belong to a camera, not to a project.

---

## The target

A **ChArUco** board, not a plain checkerboard. Every corner carries an
identity, so a board pushed half out of frame still contributes — and
the half-out-of-frame views are exactly the ones that pin distortion
down. A plain checkerboard must be wholly visible or it gives nothing.

Ours is `calibrx.io`, 7 × 9 squares, `DICT_6X6_250`, nominally
25/18 mm. **Read the parameters off the board's own printed legend at
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

Ours came out **2.07 % oversize**: the printed 50 mm bar reads
**51.037 mm** on digital calipers (sd 0.153, n=3), putting the square
at **25.518 mm**, se 0.044.

An earlier ruler pass read the bar at 50.8 and the square at 25.4,
"one inch exactly" — a tidy story, and 2.7σ from the caliper value.
It was an artifact of reading a printed line with a ruler.

**Do not measure the short reference bar.** A printed line has width,
so where you put the jaws is ambiguous by a line width — 0.3 mm here is
0.6 %, larger than the effect. Measure **corner to corner across
several squares** instead: a ChArUco corner is a point where four
quadrants meet, with no width to argue about. Five squares is 127.6 mm,
inside a 150 mm caliper, and reads to **0.008 %**.

**It does not affect the intrinsics.** Scaling a board uniformly scales
the recovered extrinsic translations and leaves focal length, principal
point and distortion untouched. Verified on the real set: 25.00 mm and
25.40 mm give rms 2.0821 both ways and fx agreeing to six significant
figures; what moved was the mean board distance, 375.5 → 381.5 mm,
a ratio of exactly 1.0160. The correction from 25.400 to 25.518 likewise
moves only the working distance, 380 → 381.8 mm.

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
    square_mm 25.518  marker_mm 18.37     # measured, not nominal
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

### 2. fx ≈ fy, and the principal point near centre

Square pixels are near-universal, so fx and fy should agree closely.
Ours: **0.11 %** (the bad set: 3.9 %). cx/cy should sit within a few
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
50 of 55 frames, 1606 corners, rms 0.717 px
fx 2624.2   fy 2626.9   (0.11 %)
cx 1644.8   cy 1203.7   (frame centre 1632, 1224)
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
