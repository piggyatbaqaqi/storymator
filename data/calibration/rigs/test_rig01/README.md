# test_rig01 — N-S-E-W target layout, disc rotated

Nine frames, `ref1_nsew-1.png` … `-9.png`, 3264 × 2448. Four ref 1
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
| plane normal, one frame | 0.399° rms → 0.702 mm at the paper corner, **87 % of budget** |
| plane normal, mean of 8 | 0.141° → 0.248 mm, **31 % of budget** |
| rotation coverage | 9 bearings, largest gap 54° |

The disc plane does **not** move as the disc rotates, so it can be
measured once by averaging rather than per frame. That is what takes
it from 87 % of the budget to 31 %.

## Layout as built

| board | bearing | radius | mean out-of-plane |
|---|---:|---:|---:|
| 0 | reference | 138.5 mm | +0.31 mm |
| 1 | +90.6° | 164.9 mm | −0.45 mm |
| 2 | +183.0° | 137.9 mm | +0.81 mm |
| 3 | +269.1° | 176.6 mm | −0.75 mm |

Which board is which compass point is **not recorded** — see below.

## A second ChArUco was in the scene

Marker id **5** appears twice in frames 1–3: on the real board #1, and
on a printed pattern on the desk at bottom right, 39 px a side, half
crossed by a cable. Naively fitted it put board #1 at Z = −4 mm with
8737 px of reprojection error.

RANSAC removed it and the frames are fine — dropping 1–3 entirely
moves the answer by 0.084°. The stray has since been taken out of
frame. **The set does not need reshooting.**

## Capture conditions

Recorded from conversation, not from a manifest:

* camera `v4k_01`, standard settings, one position throughout
* lighting: hand-held phone roughly above centre, white monitor, room
  lights, diffuse sunlight (sunny)
* captured 2026-09-30
* targets: ref 1, uniform print scale 0.95251, square **11.906 mm**

## What is missing

These frames did not go through `bin/collect-captures`, so there is no
`manifest.json` and no per-frame exposure. Not recoverable after the
fact:

* **which cut piece is at which compass point** — the analysis can
  only say "board 0 is 90.6° from board 1"
* **per-frame exposure, white balance and focus** — `v4k_01`'s
  provenance says `focus_absolute` 134 and names the controls that
  must be pinned; nothing confirms they were
* **time of day**, which matters because the sunlight was a light
  source and moves
* **disc diameter**, assumed 419 mm from conversation
* **disc material and thickness**, and how the targets were seated
* **the rotation angle intended per frame** (derived as ~40°, with
  frames 3 and 9 only 2° apart, so eight distinct rotations not nine)
* **whether the paper moved on its pegs** between frames

Shoot the next set through `bin/collect-captures` so the manifest
exists, and put the compass mapping in the session note.
