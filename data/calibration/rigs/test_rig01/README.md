# test_rig01 — N-S-E-W target layout, disc rotated

Two sets of nine frames, 3264 × 2448: `ref1_nsew-1.png` … `-9.png`
with the disc rotated ~45° between frames, and
`ref1_nsew_noise_detection-1.png` … `-9.png` with **nothing moved at
all** — the control that separates measurement noise from movement. Four ref 1
targets glued at N, S, E and W of the animation disc with
repositionable adhesive; the disc is rotated between frames and the
camera does not move. First of a planned pair — the second will try
NNE-NNW-SSE-SSW.

**Question**: can four small ChArUco patches find the plane of the
disc in every orientation?

**Answer**: yes, and N-S-E-W is the layout to keep. Full analysis in
[../../../../docs/planning/nsew-disc-plane.md](../../../../docs/planning/nsew-disc-plane.md).

## Results

| | |
|---|---|
| board poses recovered | 35 / 36 (frame 7 lost one target) |
| reprojection | 0.78 – 1.35 px |
| disc flatness | ±0.8 mm over 419 mm — **flat** |
| plane normal, rotated set | 0.399° ± 0.107 |
| plane normal, **static** set | **0.379° ± 0.095** |
| rotation coverage | 9 bearings, largest gap 54° |

**Rotation contributes nothing measurable.** The two scatters agree, so
the plane really is stable as the disc turns — and the 0.914 mm of
standoff scatter under the putty does *not* reach the working surface.

**One target is doing almost all the damage.** Dropping W improves the
plane normal 2.7×, to 0.139°; dropping any other board makes it worse.

| | Z | marker | angle to line of sight | σ_z |
|---|---:|---:|---:|---:|
| N | 397 mm | 46.9 px | 41.0° | 1.017 mm |
| E | 314 mm | 74.5 px | 12.0° | 0.274 mm |
| S | 397 mm | 46.8 px | 39.3° | 0.907 mm |
| **W** | **482 mm** | **31.3 px** | **51.9°** | **6.744 mm** |

W is far, oblique and out of focus, and one `focus_absolute` cannot
serve a 168 mm depth range. **The fix is to centre the camera over the
disc**, which puts every rim point at 28.9° instead of spreading them
from 0.8° to 58.6°.

| | normal error | at the paper corner | of budget |
|---|---:|---:|---:|
| per frame, as shot | 0.399° | 0.701 mm | 87 % |
| **per frame, without W** | **0.139°** | **0.244 mm** | **30 %** |
| mean of 9, as shot | 0.126° | 0.222 mm | 28 % |

## Layout as built

| compass | piece | marker ids | bearing | radius | mean out-of-plane |
|---|---:|---|---:|---:|---:|
| N | #0 | 0–3 | reference | 138.5 mm | +0.31 mm |
| E | #1 | 4–7 | +90.6° | 164.9 mm | −0.45 mm |
| S | #2 | 8–11 | +183.0° | 137.9 mm | +0.81 mm |
| W | #3 | 12–15 | +269.1° | 176.6 mm | −0.75 mm |

East and west sit furthest out because the paper is **landscape** —
279.4 mm east-west against 215.9 north-south — so it reaches 139.70 mm
that way and only 107.95 mm north-south, and a 50.96 mm piece has to
clear it.

## A second ChArUco was in the scene

Marker id **5** appears twice in frames 1–3: on the real board #1, and
on a printed pattern on the desk at bottom right, 39 px a side, half
crossed by a cable. Naively fitted it put board #1 at Z = −4 mm with
8737 px of reprojection error.

RANSAC removed it and the frames are fine — dropping 1–3 entirely
moves the answer by 0.084°. The stray has since been taken out of
frame. **The set does not need reshooting.**

## Capture conditions

See [manifest.json](manifest.json). In short: `v4k_01` with
`camera_settings.gpfl` loaded immediately before shooting, which pins
`focus_absolute` 134, `auto_exposure` 1, `exposure_time_absolute` 950
and white balance at 4590 K — exactly the controls `v4k_01`'s own
provenance requires. 12:50:31 to 12:51:34 EDT on 2026-09-30, nine
frames in 63 s. Lighting was a hand-held phone above the centre, the
white monitor, room lights and diffuse sunlight.

The rotation was meant to be 45° CCW per frame; recovered from the
poses it is **−45.3° ± 6.3°**, and the nine frames span a full turn,
so frame 9 repeats frame 1 to within 2° and there are eight distinct
rotations.

## The disc

| | |
|---|---:|
| diameter | 419.1 mm (16.5 in nominal, not measured) |
| foam board | 4.993 ± 0.015 mm |
| with paperboard facing | 5.553 ± 0.060 mm |
| standoff above the desk | 17.156 ± **0.914** mm, range 2.14 |
| working surface above the desk | 22.71 mm |
| foam vs facing alignment | −2 to +5 mm at the extremes |

The foam is uniform to 15 µm, so the 0.914 mm of standoff scatter
belongs to the adhesive putty — but the static control shows it does
**not** reach the disc's plane. Leave the mount alone. Five height
readings at one point say nothing about the plane through the whole
disc, and the plane was what was wanted.

## What is still missing

These frames did not go through `bin/collect-captures`:

* **shutter times and per-frame exposure** — the manifest's times are
  file mtimes, and the exposure is the one from the settings file, not
  a per-frame record
* **the camera's position and height**, only its recovered poses
* **disc diameter**, assumed rather than measured
* **how hard each target was pressed**, and its standoff
* **whether the paper shifted on its pegs** between frames

Shoot the next set through `bin/collect-captures`.
