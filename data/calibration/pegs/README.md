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
| round peg diameter *(superseded)* | 6.477 | 0.023 | 6.350 (¼″) | +5.0 thou |
| round peg diameter, **slip test** | **6.440** | ±0.010 | 6.350 (¼″) | **+3.5 thou** |
| rect peg length, left | 12.700 | 0.010 | 12.700 (½″) | +0.0 thou |
| rect peg length, right | 12.740 | 0.010 | 12.700 | +1.6 thou |
| rect peg thickness, left | 3.197 | 0.093 | 3.175 (⅛″) | +0.9 thou |
| rect peg thickness, right | 3.087 | 0.059 | 3.175 | −3.5 thou |

**The calipers have no zero offset.** The left rect peg reads 12.700
against a ½″ nominal with sd 0.010. An offset large enough to explain
the round peg would have put that reading at 12.827.

### The slip test beats the direct reading

Calipers set to 6.48 and 6.46 slip freely to the base, **6.45 goes all
the way with detectable friction**, and 6.43 catches. So the peg's
**maximum diameter is 6.43–6.45 mm**, and the friction at 6.45 puts it
at the top of that — and the direct outside-jaw reading of 6.477 ±
0.023 sits *outside* the bracket entirely.

Note how much better this is than the direct reading: a bracket of
±0.010 against a scatter of ±0.023, from a technique that needs no
judgement about jaw seating at all.

The slip test wins, and the direction of the error says why. Calipers
tilted θ off the peg axis measure `d/cos θ`, which is **longer**: 4° of
tilt adds 0.016 mm, 6° adds 0.035. A peg standing proud of a bar is
exactly where that tilt happens, and the slip test cannot make it —
the jaws must be square to pass over.

So the round peg is **6.440 ± 0.010**, **+3.5 thou over ¼″**. The 6.5 mm
metric hypothesis is excluded, 50 µm outside the bracket.

That leaves **45 µm per side** over a nominal ¼″, which is squarely the
thickness of electroless nickel or chrome plating. Combined with the
tool marks on the rect pegs, a machined-then-plated ¼″ peg is the
natural reading — though nothing downstream depends on it.

Knock-ons are small: the dome radius becomes 3.220 and the sphere
centre 5.567 mm, and the grip fit is unchanged — the peg still exceeds
the best optical hole estimate by 0.130 mm.

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

**The round peg's top is hemispherical, not flat.** At 6.477 mm
diameter the dome radius is 3.239, so the apex reading of 8.787 puts
the *shoulder* — and the sphere's centre — at **5.549 mm** above the
paper.

That matters twice. A sphere's apparent position is the projection of
its **centre**, to first order independent of view angle, so its
effective height is 5.549 and is **unambiguous** — where a flat top's
h_eff floats somewhere between h/2 and h depending on how much lit
flank the camera sees. **A domed peg is a better fiducial than a flat
one.** And 5.549 is 63 % of the apex height, so the round peg's own
parallax at r = 20 mm drops from 0.47 mm to 0.30 mm.

*The dome is hemispherical — measured, see below.* The shoulder sits
**5.567 mm** above the paper, so that is the round peg's h_eff.

**Stop measuring shape with calipers.** A caliper measures a dimension;
this is a profile. Shoot the peg in silhouette, side-on, and the whole
shape — dome depth, taper, shoulder — comes out of one frame.

### The profile shot needs no scale reference

The question is whether **dome depth / peg radius = 1**. Both lengths
are in the same image at the same depth, so **the scale cancels
exactly**. The shoulder height then follows from the caliper apex
reading, 8.787 minus the fitted radius. Put a reference in the frame as
a cross-check if you like, but do not let it gate the measurement.

Two more constraints lift with it. **Lens distortion is a non-issue if
the peg is centred**: radial error grows as r³, so the ~70 px
correction at the frame corner (r = 2040) is **0.001 px** within 50 px
of centre. And a ratio does not need fx. So this shot is *not* locked
to `focus_absolute 134` — move closer if you want.

If a reference is wanted anyway, ranked:

1. **Calipers set to a known gap** — 0.01 mm absolute. Set a *long* gap,
   60–80 mm, so the pixel term shrinks too, and rest the beam on the bar
   so the jaws sit in the peg's own plane.
2. **The ChArUco target** — 0.11 % scale, but placed against the back of
   the peg it sits 3.22 mm behind the peg's centre plane, worth 0.85 %
   at 380 mm. Correctable, but it also patterns the background and ruins
   the silhouette. Two strikes.
3. **A plastic mat-cutter rule** — moulded graduations on a thermally
   unstable substrate, and it is a working tool, not an instrument. No.

### Standoff

| Z | px/mm | 9 mm peg | dome r | depth of field |
|---:|---:|---:|---:|---:|
| 380 | 6.9 | 62 px | 22 px | 320–469 (149) |
| 250 | 10.5 | 94 px | 34 px | 222–286 (63) |
| 200 | 13.1 | 118 px | 42 px | 182–222 (40) |
| **150** | **17.5** | **158 px** | **56 px** | **140–162 (23)** |
| 120 | 21.9 | 197 px | 70 px | 113–128 (14) |

**Depth of field never binds** — hyperfocal is about 2 m at f/2.4, and
the peg is only 6.4 mm deep.

Resolution binds less than it looks, because you **fit a circle to the
dome arc** rather than measuring two points: the radius error goes as
edge error / √N. At 380 mm that is ~35 arc points and 0.2 % on the
radius; at 150 mm, ~89 points and 0.06 %. Both far better than needed
to tell a hemisphere from a shallow crown — so **150–200 mm is
comfortable and 380 mm would do**. Systematics (silhouette threshold,
the peg not exactly in profile, the tool marks) will dominate either
way, which is the real reason not to chase pixels.

### Shoot level

Tilting up by α puts the peg top nearer than its base and scales the
two ends differently: 0.21 % at 5°, 0.41 % at 10°, 0.81 % at 20° — all
straight into the ratio being measured. Since nothing in frame needs to
be legible, there is nothing to elevate *for*. Get the camera down to
bar height; the bar sitting at the desk edge makes that easy.

For the silhouette, a sheet of white paper a few cm behind the bar, lit
from the front with the peg itself shaded, gives dark-on-bright without
a proper backlight.

### The rect pegs are flat-topped

The rounding completes within 1 mm of each end, so **10.7 of 12.7 mm
(84 %) of the top is flat**. There are visible tool marks on the ends
and along the flank facing the sheet, near-identical on both pegs. Not
precision parts.

So the rect pegs are **not** domes and do not get a sphere's clean
view-independent centre. Their h_eff stays ambiguous across
**[h/2, h] = [3.13, 6.26] mm**, because an oblique camera sees the flat
top *and* one lit flank:

| h_eff | shift | apparent span | rigid rms |
|---:|---:|---:|---:|
| 3.130 | 0.84 | 204.89 | 0.69 |
| 4.695 | 1.27 | 205.74 | 1.04 |
| 6.260 | 1.70 | 206.60 | 1.39 |

The tool marks are the practical argument for **solving h_eff from
data rather than modelling it from geometry**: these pegs are not made
to a spec worth modelling to.

### Parallax alone does not account for the residual

The observed 1.6–2.3 mm **exceeds even the h_eff = h case (1.39)**, so
something else is present. Sheet drape supplies it:

| obliquity | drape | parallax + drape |
|---:|---:|---:|
| 10° | 0.85 | 2.24 |
| 20° | 1.76 | 3.15 |
| 30° | 2.80 | 4.19 |

Both are correctable, and they are the two leading terms in the budget
below.

### The correction is per-peg, not one plane

Round peg h_eff 5.57 (sphere centre); rect pegs 3.13–6.26 and flat. The
three sit at **different** effective heights, so this is three plane
offsets rather than a single peg-top-plane homography. Still exact,
just slightly more bookkeeping.

## What the heights explain

A peg top at height *h*, seen by a camera at distance *Z*, at lateral
offset *r* from the optical axis, appears displaced **outward** by
`r·h/(Z−h)`. The two rect pegs sit at r ≈ ±101.6 mm, so they move
outward in *opposite* directions: not a translation, a **pure apparent
scale increase of the peg triple**.

The **rect** pegs drive this, not the round one: they sit at r = ±101.6
while the round peg is central, so the dome correction above barely
touches the span. Assuming flat or across-the-bar-rounded rect tops:

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

## First profile attempt: refocus, do not retreat

`data/calibration/distortion/v4k_01/peg_profile-*.raw`, 2026-09-19.
Frame 4 is the usable one — white card behind, peg silhouetted, peg
near frame centre. It is out of focus, and the cause is not distance.

Measuring the shaft against its known 6.440 mm diameter:

| | |
|---|---|
| shaft width | 89.0 px → **13.8 px/mm** |
| implied standoff | Z = 2625/13.8 = **190 mm** |
| edge 10–90 rise | **19 px** (a sharp edge is 1–2) |
| predicted blur, shooting 190 mm focused at 380 | **10.7 px** |

So the camera moved in to 190 mm and **`focus_absolute` is still 134,
which is focus for 380 mm**. Moving further away would fix it by
accident — and throw away half the resolution. Refocus instead:

```sh
v4l2-ctl -d /dev/videoN --set-ctrl=focus_automatic_continuous=0
for n in $(seq 0 10 250); do
    v4l2-ctl -d /dev/videoN --set-ctrl=focus_absolute=$n
    sleep 0.6
    <capture> focus-$n.raw
done
bin/score-focus focus-*.raw
```

**Set `focus_absolute` back to 134 afterwards.** The lens calibration
is for that focus and nothing else. This shot does not need the
calibration — it is a ratio — so refocusing is free, but leaving it
moved would silently void every registration capture after it.

### The peg is its own scale reference

Its diameter is known to ±0.010 mm from the slip test, and it is in the
image, in the plane of interest, by construction. Nothing else needs to
be in frame. It doubles as an **edge-bias check**: if the measured
shaft width does not come back to 6.440 mm, the difference is the
silhouette threshold's bias and applies to the dome radius too.

### Watch the specular edges

The peg is shiny — the highlight in frame 4 confirms the plating
reading. A polished cylinder against a bright background reflects that
background near its silhouette edges, where the surface normal turns
away from the camera, so the edge reads **bright** and the peg measures
**narrow**. Put something dark on the camera side so there is nothing
bright for the flanks to reflect, and keep the bright card strictly
behind.

### What frame 4 says so far

Apex to shoulder is 33 px against a 44.5 px radius, so **dome depth /
radius = 0.74**. Do not trust that yet: with a 19 px edge rise on a
33 px dome, blur washes the apex down and biases the depth **low**, so
0.74 is a lower bound. What is clear from the silhouette is that the
top is a rounded nose of roughly the right order — not a shallow
chamfer, and not obviously a clean hemisphere either. A focused frame
will settle it.

## The dome is hemispherical

`peg_profile-5.raw`, shot at **57 mm with `focus_absolute 635`**. Edge
10–90 rise **11 px**, down from 19. Scale from the known 6.440 mm
shaft: **63.35 px/mm**, 1 px = 15.8 µm.

Fitting the whole arc — semi-axis *a* across, *b* up — against the
shaft half-width:

| | |
|---|---|
| best fit | a = 203.5 px, b = 199.5 px, rms 3.92 px |
| **b/a** | **0.980** |
| a true hemisphere | rms **4.03 px** |

The hemisphere fits as well as the free fit does. Profile against the
two candidates, as a fraction of full width:

| height above apex | measured | hemisphere | ellipse b/a = 0.75 |
|---:|---:|---:|---:|
| 10 px | 0.295 | **0.310** | 0.356 |
| 20 | 0.413 | **0.432** | 0.495 |
| 40 | 0.597 | **0.595** | 0.675 |
| 60 | 0.725 | **0.709** | 0.795 |
| 80 | 0.813 | **0.795** | 0.880 |
| 120 | 0.914 | **0.912** | 0.977 |

It tracks the hemisphere column and is nowhere near the oblate one.

**So h_eff for the round peg is 8.787 − 3.220 = 5.567 mm**, and the
sphere-centre rule applies cleanly: apparent position is the projection
of the centre, independent of view angle.

### A bad estimator, recorded so it is not repeated

The first pass called the shoulder "the first row reaching full width"
and got dome depth / radius = 0.750, which looked like a decidedly
oblate cap. It is an artifact. A hemisphere approaches full width
**tangentially** — the profile is at 0.95 of full width a fifth of the
way down from the shoulder — so that criterion fires early and noise
moves it a long way. Fit the whole profile; never key off the point
where a curve goes flat.

### Two residual caveats, neither changing the answer

**The peg sits at 53 % of maximum frame radius**, not centred, and at
`focus_absolute 635` the stored distortion model does not apply — it
was measured at 134. Radial and tangential magnification differ by
roughly 1–2 % out there, the same order as the b/a uncertainty.
Recentring would tighten it; it will not overturn a hemisphere.

**11 px of edge rise is 0.17 mm** at this scale. Blur is symmetric so
it largely cancels in a symmetric fit, but a finer sweep around 635
would still help. Depth of field at 57 mm is only about 3 mm against a
6.44 mm peg, so focus wants to sit on the peg's mid-depth, where the
silhouette tangent lies.

### What handled the chrome

The specular flanks read *brighter* than the background in places, so a
brightness threshold cuts into the peg. The measurement models the
background per row instead and calls "peg" anything departing from it
by more than 6× the background noise. It works: shaft width came out
sd **1.10 px over 230 rows**.
