# Calibration targets

> **Licence: CC-BY-SA-4.0.** Generated with CalibrX under a lifetime
> commercial licence, whose terms grant ownership of generated output
> (§4, reaffirmed in §5). See
> [../../../LICENSES.md](../../../LICENSES.md).
>
> **"calibrx.io" is a trademark of CalibrX and is not licensed here.**
> *(The rule below is our conservative default; CalibrX was asked
> directly on 2026-09-21 and their answer supersedes it.)*
> Each board's printed legend carries that mark. If you redistribute a
> **modified** board, remove it — a changed target must not imply
> endorsement CalibrX never gave. Unmodified copies may keep it.

## calibrx-charuco-175x225mm — `charuco_0001`, the 7×9 board

ChArUco, 7×9 squares, `DICT_6X6_250`. Nominal 25 mm squares with 18 mm
markers, so a nominal 175 × 225 mm board on a 191 × 265 mm page.

### Measured — the print is 1.27 % oversize

**Superseded reading below.** An early ruler pass gave 1.6 % and a
square of 25.4 mm "one inch exactly", which was a tidy story and wrong.

| method | square | |
|---|---:|---|
| **5 squares corner to corner, calipers** | **25.3163 ± 0.027** | current |
| 9 squares at 228 mm, ruler | 25.333 ± 0.111 | +0.1σ |
| 7 squares at 178 mm, ruler | 25.429 ± 0.143 | +0.8σ |
| the printed 50 mm bar, calipers | 25.518 ± 0.044 | **+3.9σ — do not use** |

**Never measure the printed 50 mm bar.** Its serifs are 0.53 and
0.58 mm wide, and "50 mm" could mean outside-, centre- or
inside-to-inside, giving 25.518, 25.241 or 24.963 — a **2.22 % spread**
on a quantity worth 1.27 %. The serifs are the error bar. Measure
corner to corner across five squares instead: a checker corner is a
point where four quadrants meet, with no width to argue about, and
126.6 mm fits a 150 mm caliper.

Technique limits this, not the caliper: six readings gave sd 0.33 mm on
126.6, twenty-five times the caliper's own resolution, because a
checker corner is a *virtual* point a jaw cannot seat on. Take six
readings and treat the scatter as the error.

### Marker size, and why it is not measured

The SVG's viewBox is 1:1 with millimetres, so the design geometry is
exact: **25.0 mm squares** and marker bits of 2.25 mm. DICT_6X6_250 is
6×6 data plus a one-bit quiet border, so the marker is 8 × 2.25 =
**18.0 mm exactly**, matching the printed legend's "25/18 mm".

At the measured print scale of 1.012652:

| | design | as printed |
|---|---:|---:|
| square | 25.0 | **25.3163** |
| marker | 18.0 | **18.2277** |
| board | 175 × 225 | 177.21 × 227.85 |

The marker figure is **derived, not measured** — design ratio times the
measured square scale — and that is sufficient, because
**`markerLength` is not a measurement input.** The markers identify
which chessboard corner is which; the calibration geometry uses only
the chessboard corners, whose spacing is `squareLength`. Varying it
across the real set:

| marker_mm | frames | corners | rms | fx |
|---:|---:|---:|---:|---:|
| 18.2277 | 48 | 1590 | 0.7070 | 2625.44 |
| 18.0 | 48 | 1590 | 0.7072 | 2625.44 |
| 17.0 | 48 | 1590 | 0.7073 | 2625.39 |
| 20.0 | 48 | 1590 | 0.7070 | 2625.40 |

**±11 % on the marker moves fx by 0.002 % and detects the same 1590
corners.** Record it for board identity — reprinting, or telling two
boards apart — not for accuracy.

### The print is also anisotropic by +0.15 %

Refitting the 48-frame set with x and y scaled independently, minimum
rms (0.7070) and fx = fy (−0.003 %) land at the same point, and a
reversed control is much worse (0.8644). Calipers said +0.38 ± 0.26 %;
the calibration data measures the board better than the calipers do.

The whole of the recorded 0.11 % fx/fy discrepancy was the print, not
the sensor. See `../distortion/v4k_01/anisotropy_scan.py`.

**Use these values** with `AcmeCalibrateLens` for this physical print:

```
columns 7    rows 9    square_mm 25.3163    marker_mm 18.228
aruco_dictionary DICT_6X6_250
```

### It does not affect the lens calibration

Scaling a board uniformly scales the recovered extrinsic translations
and leaves focal length, principal point and distortion untouched. Only
the *ratio* of the two axes matters, which is why the anisotropy above
does and the 1.27 % does not. Verified twice — on the superseded
13-frame set:

```
25.00 / 18.00 mm   rms 2.0821   fx 2519.731   cx 1507.433   k1 +0.15730
25.40 / 18.29 mm   rms 2.0821   fx 2519.734   cx 1507.433   k1 +0.15730
```

Identical to six significant figures, the last-digit difference being
solver noise. What moved was the mean board distance, 375.5 → 381.5 mm
— a ratio of 1.0160, which is the scale factor and nothing else.

and again on the final 48-frame set, where 25.3163 and 25.400 give rms
0.7215 and fx 2624.44 identically to six figures.

So the measurement matters for absolute work and for mixing boards, not
for calibrating the lens. Incidentally it also tells us the working
distance of the rig: **about 379 mm.**

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
