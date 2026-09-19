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
  sheet sat on the bed and its measured pitch: **+0.06** and **−0.10**.
  Sheet placement varied by 0.77 mm sd, and none of it leaked into the
  measurement, so the spreads above are paper.
* **The axes agree.** A round hole measures 6.0165 mm across the sensor
  and 6.0363 mm along the scan, a ratio of 0.9967 — no anisotropy.

## What these scans do *not* settle

**Absolute hole size, and therefore peg clearance.** Two methods on the
same holes disagree by 0.25 mm — a thresholded area gives 6.29 mm for
the round hole, a sub-pixel chord 6.02 — and both land near or below the
6.35 mm nominal peg, which cannot be right or the paper would not go on.
The scans pin *relative* geometry beautifully and absolute size poorly.

Clearance still wants the microscope and stage micrometer, as
`docs/measuring-punch-tolerance.md` part C says. It matters because it
is the physical registration floor.

One suggestive figure, from thresholded area: the rectangular holes run
about **2.9 mm longer** than the 12.7 mm peg. That is the ACME
kinematic design working as intended — the round peg fixes position
while the elongated slots let the sheet breathe along the bar — and not
a defect.
