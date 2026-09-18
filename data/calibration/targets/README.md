# Calibration targets

## calibrx-charuco-175x225mm — the 7×9 board

ChArUco, 7×9 squares, `DICT_6X6_250`. Nominal 25 mm squares with 18 mm
markers, so a nominal 175 × 225 mm board on a 191 × 265 mm page.

### Measured 2026-09-18 — the print is 1.6 % oversize

| feature | nominal | measured | scale |
|---|---:|---:|---:|
| the printed 50 mm calibration line | 50 mm | **50.8 mm** | 1.0160 |
| 7 squares across the width | 175 mm | **178 mm** | 1.0171 |
| 9 squares along the length | 225 mm | **228 mm** | 1.0133 |

Three independent measurements agreeing on **1.016**, which is
`25.4 / 25` exactly — so each 25 mm square printed at **25.4 mm, one
inch**, and the 50 mm line came out at 50.8 mm, two inches. A 1.6 %
error that lands on exactly an inch is unlikely to be a coincidence;
something in the print path applied an inch-for-millimetre scaling
rather than fitting to the page. Check the print dialog is set to
*Actual size* / 100 % before reprinting.

**Use these values** with `AcmeCalibrateLens` for this physical print:

```
columns 7    rows 9    square_mm 25.4    marker_mm 18.29
aruco_dictionary DICT_6X6_250
```

### It does not affect the lens calibration

Scaling a board uniformly scales the recovered extrinsic translations
and leaves focal length, principal point and distortion untouched.
Verified on the 13-frame set in `../distortion/`:

```
25.00 / 18.00 mm   rms 2.0821   fx 2519.731   cx 1507.433   k1 +0.15730
25.40 / 18.29 mm   rms 2.0821   fx 2519.734   cx 1507.433   k1 +0.15730
```

Identical to six significant figures, the last-digit difference being
solver noise. What moved was the mean board distance, 375.5 → 381.5 mm
— a ratio of 1.0160, which is the scale factor and nothing else.

So the measurement matters for absolute work and for mixing boards, not
for calibrating the lens. Incidentally it also tells us the working
distance of the rig: **about 380 mm.**

## calibrx-charuco-175x125mm — the 7×5 board

**Not measured, and it is not the same scale.** Normalising each
board's square size against the sheet of paper it was pegged to — the
same paper in both captures, so camera distance divides out — the 7×5
print's squares are **6.9 % larger** than the 7×9's. If the 7×9 is at
25.4 mm then the 7×5 is near 27.1 mm, which is not a round number in
either unit and so is worth measuring rather than inferring.

**Do not mix the two boards in one calibration run** unless each is
given its own true square size. The two were produced from different
sources — the 7×9 has a PDF and PNG beside its SVG, the 7×5 only an
SVG — which is the likely origin of the difference.
