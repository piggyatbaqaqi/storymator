# Physical prints of the generated targets

The artwork in `../` is a file; these are the pieces of paper. They
are separate records because **a print is not its artwork**: the same
PNG through a different printer, or the same printer with "fit to
page" left on, is a different physical object with a different scale,
and every measurement taken with it inherits that scale.

`charuco_0001` learned this the expensive way — its print came out
1.27 % oversize with a 0.15 % anisotropy between the axes, and the
0.15 % turned out to be the whole of a discrepancy that had been
blamed on the sensor. See `../README.md`.

| print | artwork | measured |
|---|---|---|
| [ref_1](ref_1.json) | `peg-targets-3x3-12.5mm.png` | **not yet — take the readings before cutting** |

## Measure before you cut

The nominals are printed on the sheet because they are only
measurable while the sheet is whole. Once the four pieces are
separated the longest baseline inside one of them is 17.68 mm, and
six readings on it carry 0.76 % against a print error worth about
1.27 %. Intact, the same six readings carry 0.11 %.

Six readings on each of the four spans, furthest corner to furthest
corner, straight into the print's `measured` block. The reasoning is
in
[../../../../docs/planning/moveable-targets.md](../../../../docs/planning/moveable-targets.md)
and
[../../../../docs/planning/measuring-the-printed-target.md](../../../../docs/planning/measuring-the-printed-target.md).

Licence: as `../README.md`.
