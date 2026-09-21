# Canson ACME bond — punch geometry, whole ream

95 sheets scanned at 300 dpi on a legal bed against black card,
measured 2026-09-18. 94 of 95 yielded all three holes.

Procedure and rationale: [../../../docs/measuring-punch-tolerance.md](../../../docs/measuring-punch-tolerance.md).
The scans capture the punched edge and the holes but the sheet overruns
the platen, so only one perpendicular sheet edge is on the bed — enough
for position *along* the punched edge, not for distance *from* it.

## The pattern is excellent

| quantity | mean | sd | range | nominal |
|---|---:|---:|---:|---:|
| upper pitch | 101.579 mm | **0.026** | 0.149 | 101.600 |
| lower pitch | 101.653 mm | **0.028** | 0.163 | 101.600 |
| outer span | 203.232 mm | **0.039** | 0.191 | 203.200 |
| collinearity of centre hole | 0.050 mm | 0.012 | 0.072 | 0 |
| squareness to the sheet edge | 0.060° | 0.034 | 0.131 | 0 |

**Sheet-to-sheet pitch varies by 26–28 µm**, 0.026 % of a 4-inch pitch.
At the capture rig's 11.63 px/mm that is **0.3 px** — negligible, and it
means the peg model's 101.6 mm can be taken as exact.

The die has a small real asymmetry: the lower gap runs **74 µm** longer
than the upper (sd 37 µm), consistently, on every sheet.

## The punch-to-edge position is ten times looser

| quantity | mean | sd | range |
|---|---:|---:|---:|
| sheet edge to centre hole | 139.262 mm | **0.268** | 1.429 |
| sheet edge to upper hole | 240.842 mm | **0.272** | 1.479 |

**0.27 mm sd, 1.4 mm range** — about 3 px at rig scale, and ten times
the pitch variation. Which is the expected shape: the pitch is set by
one rigid die, the punch-to-edge by how each sheet was fed.

**This is the measurement that justifies the two-stage fit.** The paper
edge moves a third of a millimetre relative to the holes, so the pegs
must be the registration datum and the outline only the geometry. It
also sizes what stage two has to absorb.

## Controls

* **The scanner is not the thing varying.** Correlation between where a
  sheet sat on the bed and its measured pitch: **+0.06** and **-0.10**.
  Sheet placement varied by 0.77 mm sd, and none of it leaked into the
  measurement, so the spreads above are paper.
* **The scan axis is accurate to better than 0.1 %.** The hole line runs
  0.13 deg off the scan axis, so the 203.2 mm span is a pure measurement
  along the belt-driven axis -- the one a flatbed gets wrong. It is also
  centroid-to-centroid, so it carries no edge-definition bias at all. It
  reads **+86 ppm** against a nominal 8 inches. A belt error of the
  0.1-0.3 % a flatbed is entitled to would show as 0.2-0.6 mm here.
* **The sensor axis is *not* checked.** Nothing in these scans spans a
  long distance across the sensor; its longest feature is a 6 mm hole.
  See "verifying the scanner" below.

## Round punch size across the ream

94 of 95 sheets, three independent estimators:

| method | mean | **sd** | min | max | range |
|---|---:|---:|---:|---:|---:|
| 50 % edge crossing, 720 rays | 6.312 | **0.0394** | 6.271 | 6.423 | 0.153 |
| thresholded area | 6.292 | 0.0349 | 6.247 | 6.403 | 0.156 |
| extent + 1 px | 6.341 | 0.0527 | 6.265 | 6.435 | 0.169 |

**Sheet to sheet, the round punch varies by sd 39 µm — 0.62 % of the
hole.** 95 % of sheets fall in a 0.132 mm band; the full range over 94
sheets is 0.153 mm. The three methods differ by 49 µm on the *mean* and
agree on the *spread* within 18 µm, so the spread is the robust number.

### Reading it for a paper review

The honest headline is **consistency, not size**. Put beside the pitch:

| | sd | as % |
|---|---:|---:|
| hole pitch (101.6 mm) | 26 µm | **0.026 %** |
| round hole diameter (6.44 mm) | 39 µm | **0.62 %** |

Relatively, hole *size* is about twenty-five times less consistent than
hole *spacing* — which is what you would expect and is not a criticism.
Spacing is set by rigid steel; size is set by where paper fibres tear.
It also does not matter for registration, because the peg grips: a hole
40 µm larger does not let the sheet move 40 µm, it just grips slightly
less.

Two caveats to quote with the numbers.

**The mean is a lower bound, the spread is not.** All three methods
read *smaller* than the 6.440 mm peg, by 0.128 mm on the principled
one, which cannot be true of the mechanical hole since the sheet
mounts. The cause is the punched rim — see below. A constant bias
cancels out of a standard deviation entirely, so the sd stands as
measured while the mean does not.

**The sd is itself an upper bound on true hole variation**, because it
includes any sheet-to-sheet variation in the rim itself. The real
punch is at least this consistent and possibly more.

## Hole size: the holes are peg-sized

The first pass reported the holes *undersize*, which is impossible. Two
biases, both mine:

* A `ptp` over pixel indices measures centre-to-centre, so an N-pixel
  run reads N-1: **exactly one pixel short**, 0.0847 mm at 300 dpi.
* A chord-width estimator that read 6.02 mm was simply broken.

The off-by-one is provably a constant offset rather than a scale error,
because the two features differ 2:1 in size and the shortfall does not:

| feature | peg | raw | shortfall | as % |
|---|---:|---:|---:|---:|
| round hole | 6.350 | 6.2632 | -0.0868 | -1.37 % |
| rect hole, short | 3.175 | 3.0719 | -0.1031 | -3.25 % |

Same millimetres, different percentages, and the millimetres are one
pixel. Corrected, three independent estimators of the round hole agree:

| method | diameter | vs the 6.350 mm peg |
|---|---:|---:|
| 50 % edge crossing, 720 rays (the principled one) | 6.3105 | -0.040 |
| thresholded area | 6.2925 | -0.058 |
| extent + 1 px | 6.3478 | -0.002 |
| rect short, extent + 1 px | 3.1565 | -0.019 |

So the holes are **line-to-line with the pegs, within about 0.04 mm**,
sd 0.034-0.039 sheet to sheet. The residual few hundredths runs the way
a punched rim biases an optical edge: the punch turns fibres down into
the aperture, and a lit lip hanging over a black hole reads as hole.

**It is a grip fit after all.** Calipers put the round peg at
**6.477 mm**, larger than every optical hole estimate, and a mounted
sheet shows **no measurable lateral motion at the round peg** -- press
between the round and a rect peg and the sheet **bows upward** instead
of sliding. That is in-plane compression with nowhere to go: a
zero-clearance hole.

The earlier argument here -- that bond at 0.1 mm thick is too flimsy to
grip -- confused bending stiffness with in-plane stiffness. Out of
plane a sheet is floppy; *in* plane it is a hoop in tension at a few
GPa, which is ample. The paper grips the post.

Which means the optical hole reads small by roughly **0.15 mm**, about
1.6 px at 300 dpi. That is credible for a punched rim: the sheet is
0.115 mm thick, 1.4 px, and the punch tears fibres down into the
aperture, so a lit burr over a black hole reads as hole. Optical
measurement is simply the wrong instrument for this feature.

The rect holes run about **2.9 mm longer** than the 12.7 mm peg -- the
kinematic freedom along the bar, working as designed.

## Verifying the scanner

Not needed for anything above: every number here is either a spread
(where scanner error cancels) or a length along the axis the span check
validates. It is worth doing anyway, because the sensor axis is
unverified and because a trustworthy scanner becomes ground truth for
the camera rig.

Two artifacts, already on hand:

* **The ChArUco board on foam board.** Rigid, planar, every corner
  identified, ~63 corners over 178 x 228 mm. Scanned flat it gives the
  **x/y scale ratio, linearity and orthogonality** over both axes at
  once -- all differential, so its own print scale does not enter.
  That is precisely the gap.
* **The steel rule**, scanned once along each axis, for **absolute
  scale**. The board's print is measured only to ~0.4 %, so it cannot
  certify absolute scale itself.

Board for the field, rule for the ruler.
