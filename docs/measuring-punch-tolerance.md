# Measuring ACME punch and peg geometry

*Bench procedure, 2026-09-18. Produces the numbers left open in
[planning/acme-registration-plugin.md](planning/acme-registration-plugin.md)
§12.*

No published engineering specification for Canson ACME hole-punched bond
gives these figures, so they have to be measured. They are worth
measuring early: they are cheap to get, and they set the floor for every
registration claim the project will make.

---

## What is actually being measured — three separate things

It is easy to run these together. They are different quantities, needing
different instruments, and the third matters most.

| | quantity | why it matters | instrument |
|---|---|---|---|
| **A** | **punch-to-edge** — where the holes sit relative to the trimmed sheet edges, sheet to sheet | bounds how much work the peg-correction stage of the registration fit must do, given the outline stage fits the paper | flatbed scanner |
| **B** | **punch internal geometry** — hole spacing and size, sheet to sheet | validates the peg model the detector fits | flatbed scanner |
| **C** | **peg/hole clearance** — how far a sheet can shift *on the bar* | **the physical registration floor.** No software can register better than the sheet can be placed | microscope + stage micrometer |

### Why C is the important one

The ACME bar is a deliberate kinematic design, not a loose fit. The
round centre peg fixes position. The two rectangular pegs — 1/2″ along
the bar, 1/8″ across it — fix rotation while letting the sheet breathe
along the bar as humidity changes its width. The clearances are
engineered in.

So a sheet has some freedom on the pegs, and whatever that freedom is,
it is the limit of what registration can mean. An animator's drawings
are aligned to the pegs; if the sheet can move 0.05 mm on them, then two
drawings the artist considers perfectly registered may differ by
0.05 mm, and a capture system reporting better agreement than that is
reporting noise.

At the capture rig's scale — 4K across a 13″ frame, **11.6 px/mm** —
0.05 mm is 0.6 px, which sits right in the middle of every other term in
the error budget. It needs a number, not an assumption.

---

## Part A and B — the flatbed

### Why no scanner calibration is needed

**This is a differential measurement.** A flatbed's scan axis is driven
by a belt and stepper motor, and 0.1–0.3 % error over 300 mm is normal —
several times the quantity being measured. That sounds disqualifying and
is not, because the error is *the same for every sheet placed in the
same spot*. It cancels exactly in the sheet-to-sheet spread.

So: absolute offsets from this procedure are contaminated and should not
be quoted. The **spread** is clean, and the spread is the answer.

The practical consequence is one rule: **put every sheet in roughly the
same place and orientation.** A few millimetres is close enough.

### Scanning checklist

1. **Platen only. Never the ADF.** Sheet transport introduces skew and
   scale error far larger than what is being measured.

2. **Black card behind the sheet.** White paper against a white lid
   leaves almost no contrast at the holes. Black card makes the holes
   read black *and* sharpens the sheet outline — the whole measurement
   improved in one move.

3. **Lid closed**, with a weight on top if the bond curls. Any lift
   changes local magnification.

4. **Maximum optical resolution.** Check the specification; advertised
   "interpolated" figures are meaningless. 600 dpi is ample — the round
   hole is then 150 px across and centroids to a couple of microns.

5. **Grayscale, and turn everything automatic off:** auto-deskew,
   auto-crop, descreen, sharpening, auto-levels.

   > **Auto-deskew is the dangerous one.** It silently rotates every
   > scan, destroys the skew measurement, and leaves no trace that it
   > happened.

6. **TIFF or PNG** if the scanner offers them. Scan-to-USB is perfectly
   fine — no need for network scanning or SANE. JPEG is *tolerable* at
   maximum quality, since its ringing is near-antisymmetric across an
   edge and large centroids and long line fits largely survive it, but
   it is a free loss to avoid.

7. **Sample across the ream — every tenth sheet, not twenty
   consecutive.** Punching is done in stacks, so adjacent sheets were
   punched in a single stroke and will agree with each other far better
   than the ream does. Consecutive sheets would report a flatteringly
   small tolerance that says nothing about the paper you will actually
   use.

8. **Twenty to thirty sheets.** Twenty estimates a standard deviation to
   about ±16 %, thirty to about ±13 %. Fewer than twelve is not worth
   analysing.

### Run the control — this is not optional

Scan **one** sheet ten times, lifting and replacing it between scans.

That spread is the method's own noise floor: scanner repeatability plus
placement. If it is not comfortably smaller than the sheet-to-sheet
spread, then the sheet-to-sheet number is measuring the scanner and not
the paper, and nothing should be concluded from it.

Run the same analysis over those ten scans as over the twenty sheets;
compare the sigmas.

### Analysing

```sh
bin/measure-punch-tolerance --dpi 600 scans/*.png
bin/measure-punch-tolerance --dpi 600 --csv punch.csv scans/*.png
bin/measure-punch-tolerance --self-test      # needs no scanner
```

Pure numpy / scipy / Pillow — no OpenCV, so it runs in the `storymator`
environment as it stands.

Five quantities per sheet, all expressed in a frame built from the
sheet's **own** punched edge, which is what makes scanner placement
irrelevant:

| | |
|---|---|
| `offset_along` | centre-hole displacement along the punched edge |
| `offset_normal` | centre-hole distance from the punched edge |
| `skew` | angle between the hole line and the punched edge |
| `span` | rect hole to rect hole (nominal 8″ = 203.2 mm) |
| `centring` | centre hole against the midpoint of the two rect holes |

Hole sizes are reported too, and feed into part C.

### What the tool can and cannot deliver

From the synthetic self-test, recovery of sheet-to-sheet *differences*:

| quantity | accuracy |
|---|---|
| `offset_along` | 0.001 mm |
| `offset_normal` | 0.001 mm |
| `skew` | 0.007° (0.4 arcmin) |
| `span` | 0.04 mm — **the weak one** |

`span` is noisiest because it differences two centroids across a 203 mm
baseline, so both centroid errors land on it undiluted. Treat a small
measured `span` variation with suspicion.

Absolute values carry a fixed bias of about −1.2 px, because a
thresholded mask's boundary pixels sit just inside the true edge. It is
identical for every sheet and cancels in every spread. The tool prints
it rather than hiding it.

### Reading the result

The report converts the sigmas into rig pixels for you. The decision it
informs:

* **Well under a pixel** — fitting the sheet outline alone would
  register adequately, and the peg stage is a refinement.
* **A pixel or more** — the pegs are doing real work and must remain the
  registration datum, exactly as the design assumes.

Either answer is useful. The second confirms the two-stage design; the
first would simplify it.

---

## Part C — clearance, with the microscope

The stage micrometer is the right instrument here and the wrong one for
the scanner. At 600 dpi a 1 mm scale is only 24 px across, so its length
reads to about ±1 % — useless for calibrating a 300 mm axis, and its
precision entirely wasted. Against a 6 mm hole under a microscope it is
exactly what is wanted.

**Measure, calibrating the eyepiece or camera against the micrometer
first:**

| feature | nominal | notes |
|---|---|---|
| round hole diameter | — | against a 1/4″ = 6.350 mm peg |
| rect hole, short dimension | — | against a 1/8″ = 3.175 mm peg |
| rect hole, long dimension | — | against a 1/2″ = 12.700 mm peg |
| the pegs themselves | as above | calipers are fine, or the same scope |

Measure several holes on several sheets; punched paper edges are fibrous
and a single reading is not representative.

**Then:**

```
diametral clearance   = round hole diameter − round peg diameter
max lateral shift     = diametral clearance / 2

rotational clearance  = rect hole short − rect peg short
max rotation          ≈ rotational clearance / 203.2 mm   (radians)
```

Convert to rig pixels at 11.6 px/mm, and to a displacement at the far
corner of the drawing — 200 mm out is a fair reference.

**That result is the floor.** Every later registration claim should be
quoted against it, and any claim of accuracy better than it is measuring
something other than the artist's intent.

---

## Optional: making the scanner an absolute instrument

Not needed for anything above. Worth knowing because of what it would
unlock.

The cheap route is a **300 mm steel rule**, accurate to ±0.1–0.2 mm over
its length — about 0.05 %, better than the scanner, and enough to check
it. Scan it, measure it, compare.

A fuller route is **self-calibration**: scan one punched sheet at
fifteen or twenty positions and orientations across the platen. The
sheet is rigid, so any variation in its measured geometry is scanner
distortion, and the distortion field and the sheet's true geometry are
jointly recoverable up to a single global scale — which the steel rule
then pins. No special artifact required; the sheet you already have is
the artifact.

**The payoff is not this study.** It is that a geometrically trustworthy
scanner becomes **ground truth for validating the camera rig**: scan a
drawing, capture the same drawing with the V4K, register both, and
compare. That is a far stronger acceptance measurement than the camera
pipeline agreeing with itself, and it is the natural way to earn the
residual figures the acceptance harness wants.

---

## Summary

| step | instrument | output |
|---|---|---|
| 20–30 sheets, black card, autos off | flatbed | punch-to-edge spread |
| 1 sheet × 10, lift and replace | flatbed | the method's noise floor |
| holes and pegs | microscope + stage micrometer | clearance, the physical floor |
| *(optional)* steel rule or self-calibration | flatbed | scanner as ground truth |

The first three are an afternoon, and they convert three assumptions in
the registration design into three numbers.
