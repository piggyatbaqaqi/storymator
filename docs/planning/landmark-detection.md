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

## Done, and it worked

Wired 2026-09-21. Peg residual went from **24.76–39.64 px** with
centroid landmarks to **7.27 px** on the best rescued frame — roughly
threefold, and consistent with the unexplained 1.7 mm having been
centroid bias all along: the rect landmarks' own bias was shifting the
midpoint the round landmark was measured against.

---

## The next obstacle: the shadow is part of the blob

Observed by the operator on the first run in earnest, and confirmed.
Every peg casts a shadow at the same angle, and it is contiguous with
the peg, so the fitted rectangle spans **peg plus shadow**.

The round peg shows it plainest. Its fitted rect came out
**120.0 × 64.6 px at +89.2°** — and +89.2° is the *shadow's* direction.
A round peg has no long axis of its own, so the fit has nothing to
latch onto but the shadow, and reports the shadow's orientation as the
landmark's.

### Thresholding alone does not separate them

The peg is darker than its shadow, which suggests simply cutting
tighter. Swept on that frame:

| `peg_contrast` | peg residual | round rect |
|---:|---:|---|
| 0.60 *(default)* | 30.29 px | 120.0 × 64.6 @ +89.2° |
| 0.42 | 31.71 | 116.0 × 60.9 @ +88.2° |
| 0.35 | 25.07 | 77.7 × 46.0 @ +70.5° |
| 0.30 | 31.67 | 40.7 × 11.7 @ +15.9° |
| 0.25 | 40.62 | 38.0 × 9.5 @ +17.1° |

The shadow does shrink away — but the rect never becomes the *peg*. By
0.30 it is 40.7 × 11.7, far too thin for a 6.44 mm dome, because a
**chrome hemisphere is not uniformly dark**: tightening the cut eats
the peg's own lit flank at the same rate as the shadow. There is no
threshold at which one is in and the other is out.

### What the operator's observation is worth

That the shadows are **parallel** says the light is effectively
collimated at this distance, so each displacement is proportional to
its peg's height — and the round peg stands 8.787 mm against the rect
pegs' 6.26, a ratio of 1.40. So the shifts are *not* common-mode: a
common-mode shift would be absorbed by the rigid stage and cost
nothing, while a differential one lands squarely in the residual.

It also means the direction is estimable from the frame itself: three
blobs, three shadows, one angle. Something that knew that angle could
trim each blob along it rather than guessing at a brightness.

Not attempted. Recorded because the observation is the useful half and
it came from looking at the picture, not the numbers.

### One thing available immediately

`peg_contrast` is a parameter of `fit_pose` and is **not exposed on
`AcmeDetectSheet`**, so an operator cannot reach it. The sweep above
spans 15.56 to 40.62 px of peg residual, which is too much leverage to
leave hardcoded at 0.6.

## Phone beside the lens: better, and the shadow is now characterised

`data/captures/2026-09-21-phone-beside-lens/`, ambient room light,
phone beside the lens rather than behind it, white monitor fill.
Subjectively much better, and measurably so — peg residual **19.99 px**
against 30.29 with the phone behind.

Fitted landmarks on frame `_009`, against a 15.75 × 3.09 mm slot and a
6.31 mm round hole:

| | fitted | angle |
|---|---|---:|
| left | 16.54 × 4.94 mm | −17.8° |
| round | 8.50 × 5.86 mm | **−90.0°** |
| right | 13.60 × 8.84 mm | −12.3° |

**The long dimension is roughly right and the short dimension is not.**
Left is +5 % on its length, right −14 %, while the short axis runs
1.6× to 2.9× oversize on all three. So the shadow is falling
**across the bar**, inflating the short axis and leaving the long one
alone.

That is a useful split: the fitted **angle and length are trustworthy;
the short extent and the across-bar position are not.**

### A prediction that failed

Last turn I predicted that if the shadow stopped dominating, the round
peg's box would swing from +89° to roughly the bar's angle. It did not
— it is **−90.0°**, still across the bar. Moving the light from behind
the lens to beside it shortened the shadow without changing which
dimension it dominates, and a round peg has no long axis of its own to
compete with it.

### And a fix that does not apply

The operator's reading was that the right box encloses only the shadow,
ignoring the peg beside it — which would mean peg and shadow are
separate candidates and the wrong one won, fixable by filtering on
shape with the already-written `Rect.matches`.

They are not separate. There are four candidates in that frame and only
one anywhere near the right peg, at 13.30 × 8.65 mm: peg and shadow are
a single merged blob, and the fitted rectangle spans both. The box
*looks* like it is on the shadow because the shadow is the larger part
of the union.

`Rect.matches` would reject all four, since none is within half of
3.09 mm on the short axis. It is the right idea and the wrong stage —
useful once something separates the two, useless while they are one
blob.

## The specular base line: real, one-sided, and the grazing shot backfired

The operator noticed a light-coloured line at the base of each peg and
shot a frame with the phone held low to enhance it.
`data/captures/2026-09-21-low-grazing/`.

**Why it is worth wanting.** The base of a peg is where it enters the
hole, so a landmark there sits at the paper plane — `h ≈ 0`, and the
parallax term that has cost us 2 mm simply does not arise. And it is
*bright*, where the shadow is dark, so a threshold separates them with
no cleverness at all. Every problem this evening has come from peg and
shadow sharing a polarity.

**What it actually looks like.** Present on all three, and clearly, but
**one-sided rather than a closed ring**:

* the round peg shows a bright crescent on its lit flank, not a circle;
* both rect pegs show a bright line along the base of the *near* long
  edge only.

So it does not give a centre directly — a one-sided feature's centroid
sits about a peg-radius off the axis. What it does give, precisely, is
the **near edge's across-bar position**, which is exactly the
coordinate the dark blob gets wrong: the shadow falls across the bar
and inflates the short extent 1.6× to 2.9×, while leaving the long axis
and the angle alone.

That suggests combining them rather than choosing — long axis and
length from the dark blob, across-bar position from the bright base
line. Not attempted, and stated as a direction rather than a plan.

**The grazing shot clips the paper — but not where it matters.**
Holding the light low does enhance the specular, and it also blows out
a quarter of the sheet:

| | paper p5 | median | p95 | at full white |
|---|---:|---:|---:|---:|
| phone beside the lens | 0.600 | 0.839 | 0.953 | 0.0 % |
| phone low, grazing | 0.741 | 0.969 | 1.000 | **25.9 %** |

> **Corrected, same session.** I first read this as the grazing shot
> having backfired. It has not. The clipping is in the hotspot, which
> is in the upper-left of the frame, while the pegs sit along the
> bottom edge where the paper reads **0.72–0.85 and is not clipped at
> all**. Searching for bright features against the sheet's *global*
> median found nothing, and that was my threshold being wrong, not the
> feature being absent.
>
> Against a **high-pass** — subtract a 41 px blur, so a lighting
> gradient vanishes and crisp structure survives — the specular is
> present at **all three pegs in both frames**: 4 600 to 8 100 pixels
> above threshold, peak excess 0.30 to 0.66. It is real, it is crisp,
> and it is there under both lightings.
>
> The earlier text also said it was not reliably present at all three.
> That was the same mistake: a *local* paper level estimated from a
> window's border is itself tilted by the gradient, so the comparison
> was against the wrong baseline.

### Answered: it does not stay put

Tested 2026-09-21 with `stability-light-A` and `-B` — the operator
shot two lightings with **the sheet and camera untouched**, which was
confirmed independently below. So the specular's position could be
compared in raw image pixels, with no homography to go wrong.

| peg | spread within A | within B | **A → B** |
|---|---:|---:|---:|
| left | 0.78 px | 0.49 px | **4.94 mm** |
| round | 0.48 px | 0.62 px | **8.24 mm** |
| right | 12.0 px | 0.46 px | **6.31 mm** |

**Sub-pixel repeatable within one lighting, and 5 to 8 mm adrift
between two.** The detected area collapses too — 755 px to 390 on the
round peg, 1589 to 174 on the right — so it is not even the same
feature, let alone the same place.

That is worse than the dark blob it was meant to improve on, whose
centroid moved 2.8–4.4 mm across the same kind of change.

**So the specular is eliminated as a landmark, standalone or
combined.** A feature that moves with the light is a reflection, and no
amount of combining rescues it. It looks convincing precisely because
it is rock-steady in any single frame — which is the trap.

Worth keeping the negative result: the reasoning that made it
attractive was sound. It *is* at the paper plane, it *is* the opposite
polarity to the shadow. Those were the right things to want. It simply
is not attached to the peg.

### Superseded: the earlier open question

The question was whether it stays put when the light moves, which
could not be answered from the first two frames because the sheet had
been moved between them. It has now been answered above: it does not.

Worth noting separately: the paper level varies by **42 %** across the
sheet under the better of these two lightings. `find_peg_candidates`
thresholds at a fraction of *one* paper median, which is a reasonable
design on an evenly lit sheet and is being asked for more than that
here. A local threshold would be a smaller change than a new landmark
and might be worth trying first.

## A separate finding: clipping wrecks the outline

Falling out of the same two sessions. The sheet did not move, so every
change in the fitted corners is the detector, not the world:

| frame | sheet clipped | worst corner error |
|---|---:|---:|
| B_029 | 5.5 % | 0 px |
| B_030 | 9.1 % | 10 px |
| B_031 | 20.3 % | 64 px |
| B_032 | 20.4 % | 69 px |
| B_033 | 26.6 % | 84 px |
| B_034 | 0 % but median 0.078 | 214 px |

Session A, unclipped throughout, holds to **1–5 px across six frames**.

So outline error tracks clipping almost monotonically, and the one
badly-*dark* frame is worse still. Both ends of the exposure range
destroy the corner fit, and neither announces itself — the fit returns
a confident quadrilateral either way.

This is cheap to guard: the fraction of the sheet at full white, and
its median, are both one line to compute and would have caught every
bad frame here. `AcmeCapture` already refuses a capture that disagrees
with its calibration; refusing one that cannot be measured is the same
idea.

It also explains an earlier mistake of mine. I concluded from these
frames that "the sheet MOVED", having averaged corner positions over a
session that included the badly clipped ones. The operator said they
had not touched it, and they were right.

## The blue marker works, and I said it did not

A pen+GEAR dry-erase marker on the unprepped chrome crowns. Session
`blue`, five full-size frames.

**I reported it had not taken. That was wrong**, and the operator
disputed it twice before I looked at the right thing. The measurement
that produced the wrong answer sampled the *darkest 55 %* of the peg
and averaged its hue. The crown is a mirror: its body is near-black
and its hue there is noise, so the average says nothing. The operator
had already described where the colour actually is — "you can see the
blue around the two reflections" — which is exactly the annulus that
sampling excludes.

`blue_006_round_peg_closeup.png` is a byte-exact crop of `blue_006.png`
at (1909, 1763); the colour is in the captured data, not in the crop.

### What it looks like measured

CIE L\*a\*b\* b\* is the channel: negative is blue, and every other
surface in the frame — paper, desk, shadow — is strongly positive
(paper b\* ≈ +16).

Thresholding the whole 8 Mpx frame at **b\* < −8**, opened 3×3 and
closed 7×7:

| frame | components | pixels | are they pegs? |
|---|---:|---:|---|
| `blue_008` | 3 | 364 | **all three, and nothing else** |
| `blue_010` | 8 | 653 | six peg fragments, two specks on the desk edge |
| `blue_009` | 1 | 81 | the round peg only — frame is near-black |
| `blue_006` | 2 | 21 | one peg, marginal |
| `blue_007` | 0 | 0 | near-black frame |

Against the greyscale detector's 3–5 candidates on blank paper and
44–56 on artwork, three components for three pegs is a different kind
of result.

**The shadow is not blue.** In the b\* map the shadows read as *dark
yellow* — the same hue as the paper they fall on, which is what a
shadow is. The confuser that has cost the most work this far simply is
not in this channel.

### False positives across the rest of the corpus

Every unmarked full-size capture, same threshold: 24 of 29 frames give
under 40 px total, and 13 give nothing at all. The worst three are
`2026-09-21_007/008/050` at 678–1033 px, and all of that sits at
x ≈ 3080–3140 — the dark desk at the right frame edge, nowhere near
the pegs and outside the sheet the outline stage has already found.

Both **hamster-crowbar** artwork frames give 3 px and 0 px. Printed
artwork does not fire this channel.

### The catch: the crown is a mirror, so the tint is not always visible

`blue_006` and `blue_010` have the same white balance (paper B/G 0.852
vs 0.848) and near-identical exposure (median 0.243 vs 0.220), yet 006
barely registers and 010 is unmistakable. The difference is what the
dome reflects. In 006 it is throwing back the warm room lamp and the
amber swamps a thin ink layer; in 008 and 010 — after the note "phone
next to lens, bar moved" — it reflects the phone and the white monitor,
and the tint shows.

So the marker's signal strength is a property of the *lighting
geometry*, not of the exposure, and nothing in the exposure statistics
predicts it. Any detector built on this needs to say so when the
channel comes up empty rather than fall through to a silent
mis-registration.

Untested: how long dry-erase ink survives on chrome that gets sheets
pushed onto it all day.

## Artwork plus blue pegs: the corpus exists, the marking does not hold

Session `blue_hamster`, the day after the marker went on. Dr. Boulos's
printed hamster art on the pegs, three full-size frames: `003` and
`004` are one setup, `002` is the same with the bar moved right so
more of the black mat shows.

**The artwork is still not the problem.** The blue channel does not
see printed ink — that part of yesterday's result holds.

**The marking is the problem.** A day of sheets going on and off the
bar has taken the ink off unevenly:

| peg | `blue_010` (day 1, blank) | `blue_hamster_003` | `blue_hamster_002` |
|---|---:|---:|---:|
| left rect | 343 px | 871 px | 665 px |
| round | **299 px** | **52 px** | **20 px** |
| right rect | 31 px | 21 px | 11 px |

Pixels with b\* < −8 in a 110×110 window on each peg. The round peg
has lost the ink almost entirely, and a crop shows why: it is bare
chrome again, a grey mirror with two highlights and no tint. It is
the peg the paper actually grips — 6.44 mm of peg in a 6.35 mm hole —
so it is the one that gets scrubbed every time a sheet is mounted.

The right rect peg was never strongly marked; it has been the weakest
of the three since the first blue frame.

The left rect peg *gained*, which is the mirror effect again rather
than more ink: the bar moved between sessions and that crown now
throws back something cooler.

So at present **one peg in three carries a usable mark**, and a fit
needs all three. Dry erase on unprepped chrome is not durable enough
to be the answer; the corpus is still worth having, because it is the
first material with art and colour together.

Whole-frame, `b* < −8` now yields 26–35 components rather than 3, and
the largest are background: the cable coil and desk at x ≈ 2850–3040
and the hole punch at x ≈ 60–230, all of it outside the sheet the
outline stage has already found. Restricting the search to the fitted
sheet interior disposes of every one of them, which is what a detector
should do anyway.

## The paper bows, and it is one edge by a lot

The operator's observation, measured. Segment the sheet, fit a quad to
its outline, rectify that quad onto the nominal 279.4 × 215.9 mm
rectangle, and measure how far the traced boundary departs from the
straight chord between each pair of corners:

| frame | punched long edge | far long edge | left short edge | **right short edge** |
|---|---:|---:|---:|---:|
| `003` | −0.84 mm | +1.01 mm | −1.49 mm | **+9.04 mm** |
| `004` | +0.98 mm | +1.01 mm | −1.74 mm | **+10.57 mm** |
| `002` | +1.04 mm | −1.03 mm | −1.35 mm | **+8.20 mm** |

Three edges hold within ±1.8 mm peak and ≤1.25 mm rms. The right short
edge — the free end, furthest from the pegs — departs by 8–11 mm, rms
5.4–7.1 mm. It survives moving the bar, so it is the sheet and not the
setup.

Two things this measurement cannot tell apart: a sheet curved in its
own plane, and a flat sheet lifting out of plane near that edge. Both
project as a curved boundary. The number is still the one registration
cares about — how far the edge sits from where a flat sheet's edge
would be — but it is not yet a diagnosis.

Not yet known: what this costs. The outline homography is fitted from
the four corners, and a mid-edge bulge moves no corner, so the direct
cost may be small; the risk is that corner *location* degrades when
the edges meeting there are curved. Worth measuring against the peg
residual before anyone builds a correction.

## Reinked: the three pegs are the three largest blue things in the frame

`fresh_ink`, dry erase reapplied to all three crowns. `007` is blank
paper, `008` is the printed hamster art on the same pegs.
Thresholding b\* < −8 over the whole frame:

| frame | 1st | 2nd | 3rd | largest non-peg |
|---|---:|---:|---:|---:|
| `007` blank | 1781 px left rect | 307 round | 35 right rect | 117 |
| `008` **art** | 1679 px left rect | 238 round | 52 right rect | 50 |

Top three components in both frames, artwork included. Worth reading
against the greyscale detector's 44–56 candidates on artwork and its
3–5 unrankable ones on blank paper.

**The 50× spread between pegs is not coverage.** Crops show all three
crowns thoroughly blue. Measured against the local paper:

| peg | ink L\* | chroma displacement | direction |
|---|---:|---:|---:|
| left rect | 12.7 | 38.0 | −70.4° |
| round | 6.8 | 24.5 | −87.2° |
| right rect | 7.2 | 16.1 | −90.7° |

Same ink, same light, same frame, and 2.4× between the ends. a\* and
b\* scale with L\*, so an absolute chroma threshold is partly a
brightness threshold and the dimmest peg drops out first. The
*direction* is the stable quantity; the magnitude needs normalising.

What to build on this is in
[ink-landmarks.md](ink-landmarks.md).

## The outline is the blocker now, and it fails on rotation

Found chasing an empty `AcmeDetectSheet.overlay`. The overlay was
blank because the fit was refused, and a refused `Pose` carries no
corners and no peg rectangles to draw.

**The pegs are not the problem any more.** With the colour gate
running, `fresh_ink_007` yields exactly three candidates and all three
sit on the pegs. What fails is `sheet_corners`.

Its four corners on that frame are (1057, −13), (3106, 623),
(2100, 2326), (718, 1701). The sheet's own bounding box is
x 899–2693, y 73–2083. **Every corner is outside it.** Drawn on the
frame, the quad is visibly skewed off the paper onto the mat.

Across the corpus, sorted by how far the sheet is rotated in frame:

| principal angle | frames | corners outside the sheet bbox |
|---|---|---|
| ≤ 3° | `2026-09-21_*`, `rect-first_*` | **0 of 4** |
| 11–17° | `stability-light-*`, `hamster-crowbar-*` | 1 of 4 |
| 26–45° | `blue_*`, `blue_hamster_*`, `fresh_ink_*` | **3–4 of 4** |

Every recent frame is in the bottom row. The bar was turned between
sessions and the outline stage stopped working; the earlier frames
that registered are all in the top row.

The cause is `_principal_angle`, which takes the sheet's orientation
from the second moments of its *area*. Under a strong keystone the
area's principal axis is not the edge direction — 32.1° against a
sheet rotated nearer 18° on `fresh_ink_007` — and `sheet_corners`
sorts boundary points into four sides by sign in that frame. Get the
frame wrong by 14° on a quadrilateral this irregular and whole
stretches of one edge are filed under another, so each line is fitted
through a mixed set of points and the intersections land anywhere.

The docstring anticipates rotation and says the image-axis assignment
"collapses entirely past about 20 degrees". It is right about the
failure and wrong about the remedy: the principal axis of the area
does not survive perspective either.

Not yet fixed, and it needs tests first. Two candidates worth
measuring against each other: take the orientation from
`cv2.minAreaRect` on the mask, which fits the *boundary* rather than
the area; or drop the four-way sort entirely and fit the quadrilateral
with `cv2.approxPolyDP`, which is what the bow measurement in
[ink-landmarks.md](ink-landmarks.md) already does successfully on
these very frames — including `fresh_ink_007`.

### Correction: it is not rotation, it is degeneracy

The workaround first recorded here — square the bar to the frame — was
wrong, and the operator acted on it. The `square` session is that
attempt: the sheet is visibly square in `square_013` and `square_014`,
and `_principal_angle` still reports −31.5° and −44.4°.

Sorting the corpus by the mask's **aspect ratio** — the square root of
the ratio of its covariance eigenvalues — explains why:

| corners outside the bbox | aspect ratio |
|---|---|
| 3–4 of 4 | 1.00 – 1.29 |
| 0 of 4 | 1.02 – 1.58 |

The two populations overlap almost entirely, so rotation was never the
variable. What the corpus does show is that **43 of 46 frames have a
mask between 1.00 and 1.06** — essentially square. The sheet is 1.29,
but from this camera angle the long axis foreshortens until the
projection is square.

The covariance of a square is isotropic, so its principal axis is
*arbitrary*. That is why the reported angle wanders between 1° and 45°
with no relation to where the sheet actually is: it is not measuring
anything. The frames that work are the ones where the arbitrary axis
happened to land near zero — 1.2°, 2.9°, 1.3°, 3.7° — and that luck
has been carrying the outline stage all along.

So there is **no operating workaround**. The finder has to be
replaced. Both candidates take the orientation from the boundary,
where the corners are, rather than from the area; they sit side by
side in `acme/outline.py` under one battery of tests in
`acme/outline_test.py`, so the choice is read off a table rather than
argued.

### Resolved: `approxPolyDP` wins, by 60x on the case that mattered

Both candidates were implemented and run through one battery. On
synthetic scenes with exact ground truth they are indistinguishable
everywhere except the degenerate one:

| scene | `minAreaRect` | `approxPolyDP` |
|---|---:|---:|
| mild keystone, any rotation | 0.00 px | 0.00 px |
| **near-square mask (aspect 1.14)** | **4.97 px** | **0.08 px** |
| worst IoU over six real frames | 0.982 | 0.986 |

`minAreaRect` fits its box to the convex hull, and a keystoned
quadrilateral is not a rotated rectangle, so the box's angle is a
compromise between the two pairs of opposite edges and the side
assignment leaks points across the corners. `approxPolyDP` assumes
nothing about the shape.

`sheet_corners` now delegates to `acme.outline.corners_approx_poly`.
The old implementation survives as `_sheet_corners_by_area`, called by
nothing but the test that guards the diagnosis.

**One approved threshold had to be relaxed, and it was wrong rather
than strict.** The tests asserted a fitted corner sits within 25 px of
the mask boundary. A corner is the intersection of two straight-line
fits and this paper does not have straight edges: measured on these
frames, three sides of each sheet hold to 3-10 px while the free end
bows 23 to 90 px, matching the 8-11 mm measured independently.
`BOW_PX = 100` still catches what the tests exist for -- the old
finder put corners more than 500 px outside the sheet.

### What is behind it

With the outline fixed the pipeline reaches the residual on every
frame, so the next two problems are now visible:

| frame | verdict |
|---|---|
| `fresh_ink_007` / `_008` | peg residual 32.9 / 27.6 px against a 1.5 px threshold |
| `blue_010`, `blue_hamster_003` | 47.0 / 32.8 px |
| `square_013` / `_014` | only **2** peg candidates, need 3 |

The `square` pair miss the right-hand peg, and it is not the ink
signature -- re-measuring from those frames' own pegs gives
essentially the stored one and still finds two. The room light was off
for that session and the right of the frame is very dark. Lighting,
not colour.

The residual is a separate question and the larger one. It is no
longer the outline: these are three real pegs fitted against a bar,
and 30 px at 7.25 px/mm is 4 mm, which is far too much for punch
tolerance. Worth its own measurement before anything is changed.
