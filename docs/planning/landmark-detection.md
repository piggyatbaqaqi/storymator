# The centroid throws away most of what a peg landmark tells you

*Operator's observation, 2026-09-21, at the end of a long session.
Recorded rather than acted on.*

## The observation

Reducing each rectangular landmark to one blob centroid discards
structure that is plainly there: the peg body, the two gaps at the ends
of the slot, and the bar visible through them. Those are not noise.

## Why it matters, measured

The blob **extent** on both rect landmarks is hole-sized — 16.95 and
16.53 mm against a 15.75 mm hole and a 12.70 mm peg. So the blob does
span the slot.

But the **centroid is not the slot's centre.** On one frame the right
landmark sat on the peg's left shoulder; on another the left landmark
sat dead centre on the side of the peg. A dark region made of a peg
body plus an end gap is not symmetric, and its centroid lands wherever
the mass happens to fall — which moves with the lighting, with where
the peg sits in its slot, and with which end is shadowed.

An earlier note in `data/calibration/pegs/honbay_0001/README.md` said
these landmarks "are holes". That is true of their extent and
misleading about their centroid, which is the quantity actually used.

## What to fit instead

**The slot's own rectangle.** The hole is a crisp paper edge, 15.75 ×
3.09 mm, lying in the paper plane. Fitting its outline rather than
taking a blob centroid would give:

* **a position** that is the rectangle's centre, robust to whatever the
  interior looks like — peg, gap, highlight or shadow;
* **an orientation**, which the bar constrains and which is currently
  thrown away entirely;
* **a size**, which is a free consistency check: anything not close to
  15.75 × 3.09 is not a slot and should be refused rather than fitted.

Three landmarks currently give six numbers. Three fitted rectangles
would give twelve, over-determining a fit that has three degrees of
freedom — so the residual would start meaning something.

And it is in the paper plane, so `rect_landmark_height_mm` stays 0 and
the parallax question does not arise for these two at all.

## The round one stays awkward

The round peg grips its hole, so there is no visible ring to fit. The
only thing to detect is the dome, which carries parallax and whose
apparent centroid moves with specular highlights — currently the
largest single error, with ~1.7 mm along the bar unexplained after the
parallax correction.

Options, none measured: fit a circle to the dome's silhouette rather
than take its centroid; weight the round landmark down relative to two
well-fitted slots; or find the hole's rim where the dome does not quite
fill it.

## Not started

This is a design direction, not a plan. It wants its own tests, and it
should wait until the current fit is understood — there is still that
unexplained 1.7 mm, and changing the detector before explaining it
would make the explanation harder, not easier.
