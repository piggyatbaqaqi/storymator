# Splitting the calibration, and where the pieces join

A proposal. Nothing here is built.

## What is wrong now

`data/calibration/distortion/v4k_01/v4k_01_blue_84001.json` is a
directory named after a **camera**, holding a file named after a
camera and an **ink**, containing the geometry of a **peg bar** and a
**paper stock**. There are three such files and each carries its own
copy of all four.

The cost is not hypothetical. Measuring `honbay_0001`'s peg spacing on
2026-09-25 — one number, one bar — meant editing three files that have
nothing to do with the bar, and the directory actually named after the
bar still holds no machine-readable record at all.

It also cannot answer the question that matters when reading an old
capture back: *which bar was this shot with?*

## Five things, five lifetimes

| thing | changes when | currently lives in |
|---|---|---|
| camera intrinsics | the camera or its focus changes | every calibration file |
| peg bar geometry | the bar is replaced or re-measured | every calibration file |
| paper stock | a different ream or size is used | every calibration file |
| ink signature | the marking medium changes, **or the camera does** | one file each, by name |
| output raster | someone wants a different output size | every calibration file |

Only the ink is stored anywhere near correctly, and even that is
misfiled: it is a property of *camera plus ink*, so its name should
say both.

The raster is the odd one out — it is not a measurement of anything.
It is a choice about the output, and it belongs to whoever is asking
for output rather than to the hardware.

## The files

Each named after its subject, each holding what was measured and how.

**`data/calibration/pegs/honbay_0001/honbay_0001.json`**

```json
{
  "kind": "pegs",
  "name": "honbay_0001",
  "round_diameter_mm": 6.44,
  "rect_long_mm": 12.72,
  "rect_short_mm": 3.142,
  "centre_spacing_mm": 103.185,
  "round_landmark_height_mm": 8.674,
  "rect_landmark_height_mm": 6.404,
  "provenance": {
    "centre_spacing_mm": "Calipers 2026-09-25, clear gaps 93.60 and 93.61 mm plus half of each peg along the bar. The halves agree to 0.010 mm.",
    "round_landmark_height_mm": "Dome apex, 5 readings, mean 8.674 sd 0.312.",
    "rect_landmark_height_mm": "13 readings across both rect pegs, mean 6.404 sd 0.163."
  }
}
```

**`data/calibration/paper/canson_ream_0001/canson_ream_0001.json`** —
`width_mm`, `height_mm`, `punch_offset_mm`, `punch_tolerance_mm`,
`bar_position`, and the barcode already recorded in that directory's
README. The punch tolerance came from 95 flatbed scans and is the only
one of these that is currently measured rather than nominal; the
sheet's own dimensions are still 8.5 × 11 inches taken on faith, and
the 0.57 % scale discrepancy left after the peg spacing was corrected
may well live here.

**`data/calibration/distortion/v4k_01/v4k_01.json`** — `camera_matrix`
and `dist_coeffs` only, plus the provenance block it already has
(frame size, `focus_absolute` 134, which board). Everything else moves
out.

**`data/calibration/ink/v4k_01-brite_mark_84001.json`** — the
`InkSignature`, named for the camera *and* the ink, because the
measurement is of both together. Paper-referencing removes the
illuminant but not the sensor.

## Where they join: two different jobs

**To run a graph: a rig file.** One place that says which hardware is
on the desk, so `AcmeCalibrationLoad` takes one path and not four.

`data/calibration/rigs/desk.json`:

```json
{
  "kind": "rig",
  "name": "desk",
  "camera": "../distortion/v4k_01/v4k_01.json",
  "pegs":   "../pegs/honbay_0001/honbay_0001.json",
  "paper":  "../paper/canson_ream_0001/canson_ream_0001.json",
  "ink":    "../ink/v4k_01-brite_mark_84001.json",
  "raster": { "px_per_mm": 11.63 }
}
```

Paths relative to the rig file, so the tree can be moved or copied
whole. The raster is inline because it is a choice, not a part — and
`FieldSpec.for_sheet` derives the rest of it from the paper.

**To describe an experiment: the session manifest.** This is the
operator's suggestion and it is the right one, but for the other half
of the job. `bin/collect-captures` already writes a `manifest.json`
per session carrying the lighting note and per-frame exposure. It
should also record what the frames were shot *through*:

```json
{
  "session": "hamster_centered",
  "rig": {
    "name": "desk",
    "camera": { "name": "v4k_01", "sha256_16": "…" },
    "pegs":   { "name": "honbay_0001", "sha256_16": "…" },
    "paper":  { "name": "canson_ream_0001", "sha256_16": "…" },
    "ink":    { "name": "v4k_01-brite_mark_84001", "sha256_16": "…" }
  },
  "notes": [ … ],
  "frames": [ … ]
}
```

The hashes are the point. A rig file is a live thing that gets
corrected — `centre_spacing_mm` moved by 1.5 % on 2026-09-25 — and
without a hash there is no way to tell whether a capture from
2026-09-23 was measured before or after. With one, a frame that
disagrees with its own manifest is a fact rather than a mystery.

This also fixes something already visible: every measurement in
`docs/planning/landmark-detection.md` before 2026-09-25 was taken
through a peg spacing 1.5 % too small, and the only record of that is
prose.

## Migration, in shippable steps

Each step leaves the tree working.

1. **Read references without writing them.** `Calibration.from_dict`
   learns that a value may be `{"$from": "relative/path.json"}` and
   resolves it against the file it is reading. Inline blocks keep
   working, so nothing changes yet and the old files still load.
2. **Emit the part files** for `honbay_0001`, the Canson stock, the
   camera and the three inks, from the values currently inline. A
   `fixes/` script, since it runs once.
3. **Rewrite the three calibrations as rig files** pointing at the
   parts. At this moment the duplication ends: there is one copy of
   the peg spacing.
4. **Teach `collect-captures` to record the rig** and its hashes.
   Sessions shot before this simply lack the block, which is honest —
   they were shot without the information being captured.
5. **Retire `Calibration.to_dict`'s inline form** for writing, keeping
   it for reading. `bin/measure-ink --into` then writes to the ink
   file rather than to a whole calibration.

Steps 1 and 2 are independent of the rest and could land first.

## What this does not change

`Calibration` stays one object in memory. The split is about storage
and provenance, not about the fitter, which should go on receiving a
single assembled thing. Nothing in `acme/fit.py` or `acme/detect.py`
should need to know that the peg geometry arrived from a different
file than the lens model.

## Open questions

* **Does the rig file belong in the repository or beside the graph?**
  A rig is a statement about one physical desk. Two people with
  different hardware want different rigs, and neither wants the
  other's in their tree.
* **Should a session record the rig, or a copy of it?** The hash makes
  a reference sufficient *if the referenced file is still there*.
  Copying the resolved values into the manifest makes an old session
  readable even after a rig file is deleted, at the cost of a much
  larger manifest.
* **What names the paper?** `canson_ream_0001` names a *ream*, which
  is right for punch statistics — a different ream is a different
  punch. It may be wrong for sheet dimensions, which are a property of
  the product.
