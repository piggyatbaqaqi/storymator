# "Scale: 100 %" is not the field that matters; Width and Height are

**Verdict.** The Canon dialog has been reporting the fault all along.
With Scale 100 % and Print Scaling None it still says

    Width 8.106 in    Height 10.491 in    X/Y resolution 532.672

and the artwork is 4318 × 5588 px, which is **8.500 × 11.000 in at its
own 508 dpi**. The image is being laid down at 532.672 dpi instead,
which is a scale of **0.95369** — the 4.7 % both sheets came out.

**The check before printing ref 3 is not the Scale field. It is that
Width reads 8.500 and Height 11.000.** Setting the X/Y resolution
boxes to 508 should do it.

## The arithmetic is exact

| | |
|---|---|
| artwork | 4318 × 5588 px, PNG `dpi` 508 |
| at 508 dpi | 8.5000 × 11.0000 in |
| 4318 ÷ 532.672 | **8.1063 in** — the dialog's 8.106 |
| 5588 ÷ 532.672 | **10.4905 in** — the dialog's 10.491 |

So the dialog is self-consistent and honest. 532.672 dpi is not a
setting anyone chose; it is what you get when 8.5 × 11 inches of image
is squeezed into the printable area.

| | predicted | measured on ref 1 |
|---|---:|---:|
| scale from width | 0.95365 | |
| scale from height | 0.95373 | |
| **predicted** | **0.95369** | |
| side margin left over | 5.00 mm | 5.35 mm |
| top/bottom margin | 6.46 mm | 6.73 mm |

The leftover margins are the printer's unprintable border, and they
land within a third of a millimetre of what ref 1's paper-edge
readings gave independently.

## What is left over is probably the fuser

| | |
|---|---:|
| predicted from the dialog | 0.95369 |
| measured, ref 2, 24 readings | **0.95238 ± 0.00050** |
| deficit | **−0.131 %**, 2.6σ |

That is 0.28 mm across the sheet, and it goes the awkward way: toner
spread inflates an outer-edge reading, so the true deficit is **at
least** this, not less.

A laser fuser takes the sheet to about 180 °C and drives moisture out
of it. Shrinkage of 0.1 to 0.3 % is ordinary, and this is 0.131 %. It
is the right size and the right sign, and **no print setting will
remove it** — a correctly scaled print should still come out about
0.13 % small, which is a tenth of the error that mattered on
`charuco_0001` and is simply measured rather than fixed.

## Printing at true size clips nothing

`PAGE_MARGIN_MM` insets every board and every note **15 mm** from the
page edge, against an unprintable border of 5.0 to 6.5 mm. So placing
the image at 508 dpi loses only blank paper. There is no reason to let
the driver shrink it.

## The sheet's own advice is now wrong

The foot says

    PRINT AT 100 %.  Turn off "fit to page" -- ref_1 came out 4.75 % undersize.

Scale *was* 100 % and Print Scaling *was* None, and ref 2 still came
out 4.76 % small. The line is as misleading as "MEASURE THE CORNERS"
was, and for the same reason: it names a control that is not the one
doing the damage. It should say to check Width and Height, or to set
the resolution to 508.

## What else is worth recording about a print

In rough order of how much they could move a number:

* **Paper size** — Letter or A4. It sets the printable area, which is
  what the image is being squeezed into.
* **Media type** — plain, heavy, labels. It sets the fuser
  temperature, and the fuser is what the leftover 0.131 % is.
* **The driver's own page handling**, as opposed to the application's.
  GIMP's "Scale 100 %" and the Canon driver's "Fit to Paper Size" are
  different controls and only one of them produced 532.672 dpi.
* **Paper feed orientation**, long edge or short edge first. It
  decides which axis is the process direction, which is the axis a
  laser's scale and shrinkage would differ on. Nothing has needed it
  yet because no anisotropy has been detected on either sheet, but it
  is the first thing to want if one ever is.
* **Print quality / native resolution**, 600 or 1200 dpi. It does not
  change scale — 508 dpi artwork is resampled either way — but it
  changes edge quality, and edge quality is what an outer-edge caliper
  reading is measuring.
* **Toner density or toner-save**, which moves the bleed and therefore
  the outer-edge bias.
* **Paper source / tray**, since a different path can have a different
  margin.

The application turned out **not** to matter: ref 1 came from gthumb
and ref 2 from GIMP, and they agree to 0.013 %. The driver's treatment
of the printable area is the whole effect.

## Status

**Measured**: the artwork's pixel size and stored dpi; ref 2's scale,
0.95238 ± 0.00050 from 24 readings across two sittings; ref 1's
paper-edge margins.

**Reported**: the dialog's Width, Height, resolution and settings, by
the operator.

**Computed**: the predicted 0.95369 and the margins it implies, and
the −0.131 % deficit against it.

**Assumed**: that the deficit is fuser shrinkage. It is the right size
and sign and nothing else obvious fits, but it has not been tested.

**The cheapest test**: set the resolution boxes to 508, confirm Width
and Height read 8.500 and 11.000, print ref 3, and measure it. If it
comes back near 0.9987 rather than 1.0000, the fuser hypothesis is
confirmed and the residue is a constant this rig can simply carry.

---

# Resolved 2026-09-30: the control is "Ignore Page Margins"

The resolution boxes will not come down to 508 until **Ignore Page
Margins** is checked. With it checked they do, Width and Height read
8.500 × 11.000, and the sheet prints at full size.

That is the whole fix, and it is safe here: `PAGE_MARGIN_MM` insets
every board and every note **15 mm** from the page edge, against an
unprintable border of 5.0–6.5 mm. Ignoring the margins clips only
blank paper. On a sheet whose content ran closer to the edge it would
not be.

So the foot's `PRINT AT 100 %` line names the wrong control twice
over — 100 % was already set, and the control that mattered was three
fields away. It should say:

    Check "Ignore Page Margins", then set the resolution to 508 dpi
    so Width and Height read 8.5 x 11 in.

## The full-size sheet's diagonal will not fit the calipers

This is the consequence nobody has had to face until now, because
every sheet so far was 4.7 % small.

| | across / down | diagonal | of 152.71 mm jaw travel |
|---|---:|---:|---:|
| as printed so far (0.95238) | 102.84 mm | 145.44 mm | 95.2 % |
| full size, no shrinkage | 107.98 mm | **152.71 mm** | **100.0 %** |
| full size, less 0.131 % fuser | 107.84 mm | **152.51 mm** | **99.9 %** |

The layout was capped so the outer diagonal came to *exactly* the
caliper's reach, and at the time that looked like using the budget
fully. It means a correct print has no measurable diagonal.

The axis spans are comfortable at 107.84 mm, **71 % of travel**. So
for the full-size sheet: **take the four axis spans and skip the
diagonals.** Nothing is lost that matters — the diagonals only ever
bounded shear, no shear has been detected on either sheet, and both
read 0.35 to 0.50 % short at 95 % travel because the jaws splay.

This is the second time that cap has cost something, and it is now
worth fixing: target about 95 % of travel rather than 100 %, which
would put the diagonal at 145 mm and cost 5 % of baseline.

## The feed direction now has a prediction attached

US Letter, **short edge first**, so the 215.9 mm edge leads: the
**process axis is "down"** on the sheet and the **laser scan axis is
"across"**.

Fuser shrinkage is usually worse along the process axis, so if the
0.131 % residue is the fuser, the prediction is **`sy` < `sx`**.
ref 2 measured `sy` 0.95250 against `sx` 0.95226 — the wrong way by
+0.025 % ± 0.105, which is to say not significant either way.

The full-size print is the first sheet where this could be seen at
all, because it is the first without a 4.7 % scaling sitting on top
of it.

## Recorded settings

| | |
|---|---|
| paper size | US Letter |
| media type | Stationery |
| feed | short edge first |
| print quality | Normal (not Draft) |
| colour | Monochrome |
| scale / print scaling | 100 % / None |
| **ignore page margins** | **unchecked on ref 1 and ref 2; checked for full size** |

## Status

**Measured**: nothing new. The spans above are ref 2's measured scale
and the dialog's own arithmetic projected to a full-size print.

**Reported**: the settings, by the operator, including that the
resolution field is locked until Ignore Page Margins is checked.

**Computed**: the projected spans and their fraction of jaw travel,
and which axis the feed makes the process direction.

**Not measured**: the full-size print itself.

**The cheapest test**: measure the full-size sheet's four axis spans,
3 + 3 across two sittings. If the scale comes back near 0.9987 the
fuser hypothesis holds; if it comes back at 1.0000 the 0.131 % was
something else and worth chasing.
