# ACME peg bar — caliper measurements

Digital calipers, three readings per feature, 2026-09-19. Part C of
[../../../docs/measuring-punch-tolerance.md](../../../docs/measuring-punch-tolerance.md),
partly done: the pegs are measured, the holes and clearance are not.

Heights are depth-gauge readings; the outside jaws are only for the peg
dimensions. The bar's surface is wavy with bumps that cannot be read
accurately.
**Every height below is referenced to one of the higher bumps** and so
is a lower bound on the local variation.

## Pegs

| feature | mean | sd | nominal | error |
|---|---:|---:|---:|---:|
| round peg diameter | 6.477 | 0.023 | 6.350 (¼″) | **+5.0 thou** |
| rect peg length, left | 12.700 | 0.010 | 12.700 (½″) | +0.0 thou |
| rect peg length, right | 12.740 | 0.010 | 12.700 | +1.6 thou |
| rect peg thickness, left | 3.197 | 0.093 | 3.175 (⅛″) | +0.9 thou |
| rect peg thickness, right | 3.087 | 0.059 | 3.175 | −3.5 thou |

**The calipers have no zero offset.** The left rect peg reads 12.700
against a ½″ nominal with sd 0.010. An offset large enough to explain
the round peg would have put that reading at 12.827.

So the round peg really is **0.127 mm over ¼″**, which is 5 thou
exactly — or, just as consistent with the data, it is a **6.5 mm metric
peg** (mean is within one sd of 6.5).

The rect thicknesses have sd 0.09, four times the round peg's, and the
left/right means differ by 0.11 mm at 1.5σ — not significant. A ⅛″
dimension on a ½″-long peg is easy to catch off-square. Re-measure
across the middle with the jaws seated flat before believing any
left/right difference.

## Heights — the parallax lever arms

| feature | mean | sd |
|---|---:|---:|
| round peg above paper | **8.787** | 0.159 |
| round peg above bar | 9.040 | 0.280 |
| rect peg above paper | **6.260** | 0.145 |
| bar above desk | 4.843 | 0.465 |
| paper above desk | 0.555 | 0.153 |

These are the numbers the registration fit needs, and they are large.

## What the heights explain

A peg top at height *h*, seen by a camera at distance *Z*, at lateral
offset *r* from the optical axis, appears displaced **outward** by
`r·h/(Z−h)`. The two rect pegs sit at r ≈ ±101.6 mm, so they move
outward in *opposite* directions: not a translation, a **pure apparent
scale increase of the peg triple**.

| Z | rect peg shift | apparent span | rigid-fit rms |
|---:|---:|---:|---:|
| 300 | 2.17 mm | 207.53 | 1.77 |
| 380 | 1.70 mm | 206.60 | **1.39** |
| 450 | 1.43 mm | 206.07 | 1.17 |

**The observed peg residual is 1.6–2.3 mm.** The rigid correction stage
deliberately does not let scale float, so a uniformly inflated triple
cannot be absorbed and lands wholly in the residual. That is the
signature, and the magnitude matches.

This was predicted in `docs/planning/acme-registration-plugin.md` §3.1
and is now measured. It is also 10× the peg detector's own 1.5 px
(0.22 mm) repeatability, so it is the dominant term.

### The fix is exact, not a fudge

The peg tops lie in a plane parallel to the paper, offset by *h*. Given
the camera pose from the outline homography plus the intrinsics, the
homography for the *peg-top* plane follows directly — same rotation,
translation shifted by *h* along the plane normal. Map peg detections
through that instead of the paper homography. No approximation.

The one unknown is **effective height**: an oblique camera sees the top
face *and* the lit flank, so the detected centroid sits somewhere
between *h*/2 and *h*. Solve it from data rather than assuming — the
apparent span gives it directly, `h = Z(1 − 203.2/apparent)`:

| apparent span at Z=380 | implied h_eff |
|---:|---:|
| 204.0 | 1.49 mm |
| 205.0 | 3.34 mm |
| 206.0 | 5.17 mm |
| 207.0 | 6.98 mm |

Measure the apparent span on the existing captures and read h_eff off.

## The sheet is not flat, either

Ten sheets measure 1.1533 mm (sd 0.081), so bond is **0.1153 mm**
thick, se 0.005.

Measured with the **depth gauge, not the outside jaws** — the jaws
visibly compress a paper stack and leave marks, and read distinctly
smaller. So this is free thickness with no compression bias, and it is
the right technique for every soft or stacked material here. The bar
stands **4.84 mm** above the desk, so paper over the bar sits at 4.96
and paper lying flat at 0.12: the sheet drapes through **4.84 mm**.
Against the outline homography's planar assumption that is 0.85 mm at
10° obliquity, 1.76 at 20°, **2.80 at 30°** — all near the bar, where
the pegs are.

(The earlier 4.29 mm used the 0.555 mm paper-above-desk reading as the
far datum. With the real thickness known, that reading is not thickness
at all — the sheet sits 0.44 mm off the desk there, which is curl.)

A light table or a sheet of glass removes this. Until then it is a
second systematic term of the same order as the parallax, and the two
are not independent, since both grow with obliquity.

## Still open

* **Bar waviness.** Currently only a lower bound, from the sd on
  bar-above-desk (0.465 mm) which mixes real waviness with reading
  error. It matters because it tilts each peg.

## Clearance: there isn't any

A mounted sheet shows **no measurable lateral motion at the round peg**,
and none at the rect pegs either. Pressing between the round peg and a
rect peg makes the sheet **bow upward** rather than slide — in-plane
compression with nowhere to go, which is what zero clearance looks
like. The round peg at 6.477 mm is a grip fit in the punched hole.

Generously bounding caliper resolution on a mounted sheet at 0.05 mm
diametral, that caps the physical registration floor at:

| | |
|---|---|
| lateral shift | ≤ 0.025 mm = **0.29 px** at rig scale |
| rotation | ≤ 0.014°, i.e. 0.05 mm at 200 mm out |

**So the floor is not the limiting term — it is the smallest term.**
The budget now reads:

| term | mm | px at 11.63 px/mm |
|---|---:|---:|
| sheet drape at 20° | 1.76 | 20.5 |
| peg-top parallax (Z=380) | 1.39 | 16.2 |
| punch-to-edge spread (sd) | 0.27 | 3.1 |
| peg detector repeatability | 0.22 | 2.6 |
| hole clearance | ≤0.025 | **≤0.3** |

Both leaders are **geometric and correctable** — parallax exactly, drape
by flattening the sheet — and neither is physical. That is the good
outcome: nothing in the paper or the bar limits this rig.

To tighten the clearance bound further, use the rig itself rather than
the calipers: at 11.63 px/mm it resolves 0.05 mm as 0.6 px. Capture a
mounted sheet, push it hard one way and capture, push the other way and
capture, register all three. It measures the quantity that actually
matters — how far the *drawing* moves — with the pipeline already built.
