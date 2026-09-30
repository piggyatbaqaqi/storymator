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

---

# Revisited 2026-09-25: the bars are gone, and the diagonals only bound the skew

**Verdict.** The scale bars have been removed from
`bin/make-peg-targets` rather than relabelled, and the four boards
have been pulled together so a 152.71 mm caliper reaches every point
on the sheet. The sheet now prints its own nominals:

| span | from | to | nominal |
|---|---|---|---:|
| across | board #0's furthest corner | board #1's | **83.92 mm** |
| down | board #0's furthest corner | board #2's | **83.92 mm** |
| diagonal | board #0 | board #3 | **117.35 mm** |
| diagonal | board #1 | board #2 | **117.35 mm** |

Six readings each. The anisotropy is the ratio of the across and down
fractional errors, as before.

## Diagonals do not cross-check anisotropy

The operator asked whether they would. They do not, and the reason is
that a diagonal is symmetric in the two axes it crosses.

Under a scaling of `sx` across and `sy` down, a diagonal vector
`(W, H)` becomes `(sx·W, sy·H)`. With `W = H`, **both** diagonals
change by the same factor `sqrt((sx² + sy²)/2)`. An isotropic 1.0134
and an anisotropic 1.0127 × 1.0142 give the identical pair of
diagonals — 1.01345 either way, a difference of 5 parts per million
against a 0.4 % reading error. Only the axis-aligned spans separate
them, which is why both are advertised.

## What the diagonals do catch is shear, as a bound

A shear `x' = x + k·y` is the one distortion the axis spans miss
entirely: it leaves both `W` and `H` unchanged and moves the two
diagonals in opposite directions.

    d₁ − d₂ ≈ 2·k·W·H / hypot(W, H) = k·W·√2   (for W = H)

At `W = 82.98 mm` that is 117.35 mm of lever arm per radian. The floor
is set by the corner-reading scatter, **sd 0.33 mm** measured on 6
readings across 5 squares (`data/calibration/targets/README.md`):

| readings each | sd of the difference | 2σ floor | as an angle | inside one 37.5 mm board |
|---|---:|---:|---:|---:|
| 1 | 0.467 mm | 0.933 mm | 0.456° | 0.298 mm |
| 6 | 0.191 mm | 0.381 mm | 0.186° | 0.122 mm |

So a diagonal difference under 0.381 mm means nothing, and 0.381 mm
means 0.122 mm of corner displacement inside a cut board — **15 % of
the 0.804 mm threshold**. The diagonals can therefore *confirm* that
shear is harmless; they cannot detect one that matters. They are worth
taking because they are two more readings at the same jaw setting, not
because they are a sensitive test. Anything this instrument can see in
them is already a print fault worth investigating for other reasons.

The page-scale figure is the misleading one and is recorded here so it
does not get reused: `k = 0.00325` over the sheet's 279.4 mm height is
0.907 mm, which looks alarming and is irrelevant — the boards are cut
apart and glued down individually, so only the shear *within* one
37.5 mm board survives the scissors.

## The layout constraint, and what it cost

The binding distance is the diagonal between the two furthest printed
corners of the 2 × 2 block, `(step + 37.5) × √2`. Setting that equal
to 152.71 mm gives a centre step of **70.48 mm**, and guarantees that
every pair of points on the four boards is reachable — no reading the
operator chooses to take can fall out of range.

That guarantee is paid for in baseline:

| layout | span measured | one reading | mean of six | over the 203.232 mm peg span |
|---|---:|---:|---:|---:|
| previous | 132.40 mm | 0.249 % | 0.102 % | 0.208 mm (26 % of threshold) |
| now | 83.92 mm | 0.393 % | 0.161 % | 0.327 mm (41 %) |
| corner-capped | 108.70 mm | 0.304 % | 0.124 % | 0.252 mm (31 %) |

The middle row is what shipped. The third is the alternative — cap on
the *corner* diagonal rather than the printed edge, allowing a 95.48 mm
step — and it was not taken because it reinstates the thing that made
the previous layout awkward: some readings fit and some do not.

The previous layout bought its precision with two different rules,
corresponding corners across and innermost corners down, because
corresponding corners were 154.90 mm apart and did not fit. Two rules
for one measurement is exactly how the 0.40 % tick ambiguity got in.

## What this supersedes

The `## What should change` section above offered "either remove them,
or relabel them". Removed. `test_the_scale_bar_is_the_length_it_claims`
and five sibling tests are deleted from
`bin/make_peg_targets_test.py`, along with `scale_bar_mm`,
`scale_bar_boxes`, `SCALE_BAR_MM`, `TICK_MM` and `BAR_SPACE_MM`.

One of the deleted tests,
`test_the_bars_recover_an_anisotropy_that_was_applied`, was testing a
feature that should not exist — it proved the bars worked, which was
never the question.

The nominals in the verdict at the top of this document — 132.40 mm
across and 129.90 mm down — describe the **old** layout and no longer
apply. **Superseded reading above.** Use the table at the head of this
section.

## Status

**Measured**: the 0.33 mm corner-reading scatter, six readings across
five squares, from `data/calibration/targets/README.md`. The 0.20 mm
tick width and the three bar readings, off the rendered PNG at a known
20 px/mm.

**Computed**: every figure in this section — the diagonal identity,
the shear lever arm, the detection floors, the layout cap and the
precision table are formulae evaluated at this sheet's geometry and at
the rig's 203.232 mm peg span and 0.804 mm threshold.

**Not measured**: this print's actual anisotropy and skew. The sheet
has not been printed yet.

**The cheapest test**: print it and take six readings on each of the
four advertised spans. If the two diagonals agree within 0.381 mm,
shear is settled and can be ignored from then on.

---

# Revisited 2026-09-30: measure all four spans, and spread them over sittings

**Verdict.** Yes, take `#2–#3` across and `#1–#3` down on ref 2 — but
not because ref 1's rows disagreed. They did not, emphatically. Take
them because they are half the sample and the only guard against a
scale that differs between pieces, which is unrecoverable once the
sheet is cut.

And arrange the readings as **3 + 3 across two sittings on each of the
four spans**, rather than 6 in one. That is the same twenty-four
readings and a far more honest error bar.

## The rows and columns agreed, and it was not close

| span | n | mean | sd | sem |
|---|---:|---:|---:|---:|
| across #0–#1 | 6 | 102.877 | 0.210 | 0.086 |
| across #2–#3 | 6 | 102.890 | 0.184 | 0.075 |
| down #0–#2 | 6 | 102.827 | 0.389 | 0.159 |
| down #1–#3 | 6 | 102.822 | 0.217 | 0.088 |

| | difference | | |
|---|---:|---:|---|
| across, top row vs bottom | **+0.013 mm** ± 0.114 | 0.12σ | +0.012 % |
| down, left column vs right | **−0.005 mm** ± 0.182 | 0.03σ | −0.005 % |

The Canon's scale is uniform over a letter sheet to five thousandths
of a millimetre. That is a property of the transport and the scanner
optics, and it is not going to be different on the next sheet out of
the same machine.

## Why take them anyway: they are half the data

The second pair is not an extra check bolted onto the measurement. It
*is* half of the measurement.

| | one pair (n=6) | both pairs (n=12) | |
|---|---:|---:|---:|
| across, scale uncertainty | 0.080 % | **0.050 %** | 1.58× |
| down, scale uncertainty | 0.147 % | **0.080 %** | 1.83× |
| anisotropy uncertainty | ±0.167 % | **±0.095 %** | 1.76× |

Dropping the second pair costs about √2 on everything, and the
anisotropy — the one quantity a lens calibration actually cares about
— is already only marginally resolvable at ±0.095 %.

## And the drift they would catch is budget-sized

This is the argument that settles it. With 6 + 6 readings the smallest
row-to-row drift detectable at 2σ is **0.212 %**. If a drift that size
went unseen, pieces from different rows would carry scales differing
by 0.212 %, and one average scale applied to all four would put each
piece's depth out by half that — at Z ≈ 380 mm, **0.804 mm of
differential depth between a top-row piece and a bottom-row one**.

That is the entire error budget, spent on a fault nobody looked for.
And it is worse than a random error, because two targets would be
pushed one way and two the other, which a plane fit turns directly
into a spurious tilt.

Measuring one pair does not make this smaller. It makes it invisible.

## What matters more than any of it: sittings

ref 1's `down #0–#2` span, measured twice:

| | n | mean |
|---|---:|---:|
| first sitting | 3 | 102.473 |
| second sitting | 3 | **103.180** |

**A gap of +0.707 mm, thirteen times the 0.055 mm scatter within a
sitting.** That single systematic is what produced — and then
destroyed — the +0.273 % anisotropy first reported for ref 1.

Six readings taken back to back are not six independent readings. They
share a jaw seating, a grip, a viewing angle and a minute of the
operator's attention, and their agreement measures none of those. The
error bar has to come from repeats separated by putting the calipers
down.

So for ref 2: four spans, **3 readings in one sitting and 3 in
another**. Same total effort as before, and the scatter between
sittings becomes part of the answer instead of an ambush.

## Status

**Measured**: all four spans of ref 1, 24 readings, 2026-09-30.

**Computed**: the row and column differences and their uncertainties,
the precision lost by dropping a pair, the 2σ drift floor and its
projection to differential depth at Z = 380 mm.

**Not measured**: whether a second sheet from the same printer is as
uniform as ref 1 was. It is assumed, on the grounds that page-scale
uniformity is a property of the machine rather than of the sheet —
which is precisely why the check is cheap to keep and expensive to
skip.
