# Do not measure the scale bars; measure between chessboard corners

**Verdict.** Ignore the printed bars on
`data/calibration/targets/peg-targets-3x3-12.5mm.png`. Measure
**corner to corner between two boards, before cutting**:

| axis | from | to | nominal |
|---|---|---|---:|
| across | a corner on board #0 | the same corner on board #1 | **132.40 mm** |
| down | board #0's lower corners | board #2's upper corners | **129.90 mm** |

Six readings each, and treat the scatter as the error bar. The
anisotropy is the ratio of the two fractional errors.

If the bars get used anyway, the **solid bar, outside to outside**, is
the only exact reading on the sheet: 100.000 mm. Every way of reading
the *ticks* is wrong.

## The project already decided this, about a different bar

`data/calibration/targets/README.md` records it: the CalibrX board's
printed 50 mm bar read **+3.9σ** away from the ruler measurements,
because its serifs are 0.53 and 0.58 mm wide and "50 mm" could mean
outside-, centre- or inside-to-inside — a **2.22 % spread on a
quantity worth 1.27 %**. *"The serifs are the error bar."*

I put scale bars on the new target sheet anyway. They have the same
disease in a milder form.

## Measured off the rendered sheet

The bar is a filled rectangle of exactly 2000 px at 20 px/mm. Its
ticks are 4 px — 0.20 mm — wide, the first starting at column 1159 and
the last at 3159:

| what is measured | reading |
|---|---:|
| the solid bar, outside to outside | **100.000 mm** |
| ticks, outside to outside | 100.200 mm |
| ticks, centre to centre | 100.000 mm |
| ticks, inside to inside | 99.800 mm |

Two of those are right and two are wrong, and nothing on the sheet
says which. The tick ambiguity is **0.400 mm on 100**, or 0.40 %.

## Which matters, because 0.40 % spends the whole budget

A scale error in the target geometry propagates straight into the pose
scale, so it lands on the peg span:

| scale error | over the 203.232 mm peg span | of the 0.804 mm threshold |
|---|---:|---:|
| 0.40 %, the tick ambiguity | 0.813 mm | **101 %** |
| 0.26 %, one corner reading | 0.528 mm | 66 % |
| 0.13 %, the mean of six | 0.264 mm | 33 % |

Reading the ticks the wrong way costs more than the entire error
budget. That is not a rounding concern.

## Corners beat the bar because the error is a different kind

A checker corner is a point where four quadrants meet. It has **no
width to argue about**, so there is no outside/centre/inside question
to get wrong.

The project measured the technique limit directly: six readings across
five squares gave **sd 0.33 mm on 126.6 mm**, twenty-five times the
caliper's resolution, because a checker corner is a *virtual* point a
jaw cannot seat on.

That is 0.26 % for one reading — worse than the bar's 0.40 %? No, and
the difference is the whole argument:

* the corner scatter is **random**, so the mean of six is 0.11 %;
* the bar's ambiguity is **systematic**, so six readings of the wrong
  interpretation give the wrong answer six times.

## The sheet cannot quite do the vertical measurement as laid out

Corresponding corners on vertically adjacent boards are **154.90 mm**
apart, which does not fit a 150 mm caliper — and the vertical axis is
the entire reason the operator asked.

The innermost corners do fit, at **129.90 mm**, which is why the
verdict names those. It works, but it is a narrower baseline for no
reason other than where the boards landed, and a layout with the rows
about 25 mm closer would let the same corner pair serve both axes.

## What should change

**The bars should stop claiming to be measuring instruments.** Either
remove them, or relabel them for counting and print the two
corner-to-corner nominals on the sheet so the operator has something
to compare a reading against.

This supersedes what `bin/make_peg_targets_test.py::
test_the_scale_bar_is_the_length_it_claims` is *for* — not its
assertion, which is true and should stay true while a bar exists, but
its premise that the bar is how the print gets measured.

## Status

**Measured**: the bar and tick geometry, read off the rendered PNG in
pixels at a known 20 px/mm. The 0.33 mm corner-reading scatter and the
CalibrX bar's 2.22 % spread, both from
`data/calibration/targets/README.md`, six readings each. The board
placement, from `bin/make-peg-targets`'s own layout.

**Computed**: the corner-to-corner nominals, from that layout. The
budget table, which is a scale error carried through the peg span and
divided by the derived threshold.

**Not measured**: this print's actual anisotropy — the sheet has not
been printed yet. And whether a 12.5 mm square's corners can be read as
precisely as a 25 mm square's; the 0.33 mm scatter was measured on the
larger board, and a corner's localisation depends on the print's edge
quality rather than on the square size, so it should carry over, but
that is an assumption.

**The cheapest test**: print the sheet, take six readings on each axis
between the corners named above, and six on the solid bar outside to
outside. If the bar agrees with the corners, it is usable after all
and only needs labelling. If it does not, it should go.
