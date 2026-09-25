# Where the rig's numbers live

**This file is a map, not a copy.** It deliberately quotes almost no
values, because the values move — the peg spacing went through three
values on 2026-09-25 alone — and a stale number copied into a skill is
worse than no number, since it looks authoritative. Read the sources.

## The quantity you want, and where it is

| quantity | source of truth | provenance to cite |
|---|---|---|
| peg bar geometry, peg heights | `data/calibration/pegs/<bar>/README.md` | digital calipers, three readings per feature |
| peg bar, machine-readable | `data/calibration/distortion/<cam>/*.json` | in the *wrong* place on purpose-for-now; see `docs/planning/calibration-files.md` |
| punch geometry, punch tolerance | `data/calibration/acme_paper/README.md` | 95 flatbed scans of a ream |
| paper size, punch offset, raster scale | `comfyui/comfyui_acme/acme/model.py` (`SheetModel`, `FieldSpec`) | **defaults, some nominal** — read the docstrings, they say which |
| camera intrinsics, distortion | `data/calibration/distortion/<cam>/README.md` and its JSONs | ChArUco multi-frame calibration, cross-checked against CalibrX |
| printed target scale and anisotropy | `data/calibration/targets/README.md` | calipers across five squares, six readings, scatter as the error bar |
| ink / crown chroma | `InkSignature` in `model.py`, `acme/ink.py` | pooled over the inked corpus, two days and four lighting setups |
| the corpus of captures | `data/calibration/distortion/<cam>/`, `bin/collect-captures` | |

## The procedures, when a number has to be made rather than looked up

* `docs/measuring-punch-tolerance.md` — the punch and bar measurement
  procedure, of which the peg part is done and the holes are not.
* `docs/calibrating-a-camera.md` — lens calibration, including its
  hard-won prohibitions (no glass over the target; do not run the
  flatness test on paper).
* `data/calibration/targets/README.md` — how to measure a print without
  fooling yourself. Corner to corner across five squares; **never the
  printed millimetre bar**, whose serifs are worth more than the error
  being measured.

## Error-budget furniture

Look these up rather than reciting them, but know they exist:

* **The residual threshold is derived** — a small multiple of the
  measured punch tolerance, because no real sheet can beat its own
  punch. A threshold below it is unmeetable by construction.
* **`px_per_mm`** in `FieldSpec` converts every pixel-domain error into
  millimetres, which is the only unit the operator judges in.
* **The peg frame** is the canonical coordinate system: origin at the
  round peg's centre, +x along the bar, +y into the sheet, millimetres.
  Its definition and the reasoning for it are in `model.py`'s docstring.

## Established mechanisms, with the modules that implement them

Most rig questions turn out to be one of these in a new costume. Using
the established form keeps the new result comparable with the numbers
already in the docs.

| mechanism | form | where |
|---|---|---|
| out-of-plane error projected into the image | `h·tan θ` | `docs/planning/landmark-detection.md`, "why this is proof the surface is not flat" |
| landmark standing above the paper plane | `r·h/Z`, r observed | `acme/parallax.py`, whose docstring derives it and gives the measured check |
| chord across a curved span | sag `s²/8R` | `docs/planning/sheet-flattening.md` |
| a homography is exact for a plane at any angle | — | which makes *any* angle-dependent residual evidence of non-planarity |
| corner localisation scatter | ≈ noise / local gradient | why faint print costs precision, and why a piecewise fit cannot average it away |

## The reading list for context

`docs/planning/landmark-detection.md` is the long session record and the
densest source of measured numbers. `docs/planning/pose-from-pnp.md`
holds the pose and desk-target reasoning including its own retraction.
`docs/planning/calibration-files.md` holds the decided file layout.
`docs/planning/sheet-flattening.md` holds the fiducial-field analysis.
