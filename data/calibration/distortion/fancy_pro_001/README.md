# fancy_pro_001 — CZUR Fancy S Pro

| | |
|---|---|
| manufacturer | CZUR |
| model | **Fancy S Pro** |
| device ID | `CAF1C22601008785` |
| serial | not recorded here — see below |
| max resolution | 4000 × 3000 (12.0 MP) |
| lens calibration | **none yet** |

Not yet calibrated. Seven test shots while working out static
settings.

> **The 25-character serial is deliberately not in this file.**
> `6NU89-…-8339Y` is five groups of five, which is the shape of a
> software licence key rather than a hardware serial, and CZUR ships
> these with bundled software. This repository pushes to GitHub, and
> `CLAUDE.md` says not to check credentials in. The device ID above
> identifies the unit for every purpose this project has. If the
> 25-character string turns out to be a hardware serial after all it
> can be added.

| shot | size | white balance | markers found | marker side |
|---|---|---|---:|---:|
| `test_shot-1.jpg` | 640 × 480 | **on** | 4 of 16 | 16.9 px |
| `test_shot-2.jpg` | 640 × 480 | off | 2–3 of 16 | 16.6 px |
| **`test_shot-3.jpg`** | **4000 × 3000** | off | **16 of 16** | **75.0 px** |

## The green is not raw mode, and not a white-balance cast

With auto white balance off, red and blue are **dead**, not merely
weak:

| | R mean | G mean | B mean | R ≤ 1 | B ≤ 1 | G ≥ 254 |
|---|---:|---:|---:|---:|---:|---:|
| shot-1, WB on | 158.9 | 156.1 | 151.6 | 0.07 % | 0.43 % | 0.00 % |
| shot-2, WB off | **1.0** | 207.0 | **0.4** | **91.9 %** | **97.4 %** | **65.2 %** |
| shot-3, WB off | **6.6** | 147.3 | **2.4** | **66.0 %** | **85.8 %** | **34.2 %** |

A white-balance problem shifts the ratio between channels. This zeroes
two of them. The signature says the camera is delivering a
**single-channel stream that is being packed into the green plane**,
and the green plane on its own is a perfectly ordinary greyscale
image.

## So yes, the captures are usable — at full resolution

`test_shot-3` finds **all sixteen** ref 2 markers at **75.0 px** a
side. That is better than anything `v4k_01` has produced on the disc,
where they run 22 to 78 px and only three or four pieces appear per
frame. At 4000 × 3000 it is 12.0 MP against v4k_01's 8.0, or **1.23×
the linear sampling**.

Taking the green plane and taking luma give the same answer — 75.1
against 75.0 px — because with R and B at zero, luma is just a scaled
green.

**Use maximum resolution.** At 640 × 480 the clipping costs markers:
shot-2 finds two or three where shot-1, same size with WB on, finds
four. At 4000 × 3000 it costs nothing, because the blown 34 % is
paper and disc highlight, not targets.

## What it does cost: all colour

| | pixels over the ink detector's 0.331 `min_chroma` |
|---|---:|
| shot-1, WB on | 10.68 % |
| shot-3, WB off | **99.92 %** |

Every pixel is one hue, so there is nothing to select on. **The
blue-peg detector in `acme/ink.py` cannot work on these frames at
all.** That is a design question rather than a camera fault: if the
ChArUco targets carry the geometry, the ink path may not be needed
here. If it is needed, the white balance has to work.

## Still to do

* Lower the exposure until green stops clipping; 34 % at full
  resolution is recoverable headroom.
* Decide whether this camera needs the ink path.
* Calibrate the lens — 48 frames, board at many angles. Nothing here
  is a calibration.
