# Coloured pegs: what to build, and what not to

Nothing prevents starting. The freshly-inked frames give the cleanest
peg detection this project has produced, and the design that survives
a change of ink is also the design that survives the things already
measured to go wrong. This is the plan before the code.

## The evidence

`data/captures/fresh_ink`, dry-erase blue reapplied to all three
crowns: `007` is blank paper, `008` is Dr. Boulos's printed hamster
art on the same pegs. Thresholding CIE L\*a\*b\* b\* at −8 over the
whole 8 Mpx frame:

| frame | 1st component | 2nd | 3rd | largest non-peg |
|---|---:|---:|---:|---:|
| `007` blank | **1781 px** (left rect) | **307** (round) | **35** (right rect) | 117 |
| `008` **art** | **1679 px** (left rect) | **238** (round) | **52** (right rect) | 50 |

The three pegs are the top three components in both frames —
**including the one with artwork on it**, where the greyscale
detector finds 44–56 candidates and cannot rank them. On blank paper
it finds 3–5 and cannot rank those either. The art costs the ink
channel almost nothing: the gap between the weakest peg and the
loudest non-peg is 35 vs 117 on blank paper and 52 vs 50 on art.

## Three things the design has to get right

### 1. The ink blob is not the peg top

Coverage is uneven and it is not going to stop being uneven. In
`fresh_ink_007` the left rect peg gives 1781 px of ink and the right
gives 35, and a crop shows both crowns looking thoroughly blue — so
the blob area is not even a proxy for how well a peg is inked.

A rectangle fitted to 35 px of ink has an angle that means nothing.
The shape of the ink is the shape of *where the pen went*; the shape
we need is the shape of the peg top.

**So chroma gates, greyscale measures.** The ink says *there is a peg
about here* — which is precisely what the greyscale detector cannot
say, because shadows and artwork look like pegs to it. Then the
existing `fit_rect` runs inside that neighbourhood on luminance, where
the full crown is visible, and produces the geometry. Both stages keep
what they are good at, and neither depends on the ink covering the
crown completely.

This also means the Dykem layout fluid arriving later cannot
invalidate the work. Better coverage makes the gate more reliable; it
changes nothing downstream.

### 2. An absolute chroma threshold is a lightness threshold in disguise

Measured on `fresh_ink_007`, ink against the local paper in the same
window:

| peg | ink L\* | displacement from paper | direction | px at b\* < −8 |
|---|---:|---:|---:|---:|
| left rect | 12.7 | 38.0 | −70.4° | 1781 |
| round | 6.8 | 24.5 | −87.2° | 307 |
| right rect | 7.2 | 16.1 | −90.7° | 35 |

The three pegs carry the same ink under the same light in one frame,
and their chroma displacement varies by **2.4×**. It tracks how dark
each peg renders, because a\* and b\* both scale with L\*. The right
peg's 35 px is not less ink; it is a dimmer peg.

**So the score is normalised and paper-relative.** Two separate
points, and both come from things already measured:

* *Paper-relative*, because white balance moves between sessions and
  the paper is the only in-frame reference for it. Paper sits at
  b\* ≈ +12 to +16 across this corpus; the ink's *absolute* b\* is not
  the signal, its displacement from paper is.
* *Normalised*, because otherwise the threshold is partly a
  brightness threshold and the dimmest peg drops out first.

### 3. The ink can be invisible without the frame looking wrong

Already measured, on the first blue session: `blue_006` and
`blue_010` have the same white balance and near-identical exposure,
and one barely registers. The crowns are mirrors, and a crown
reflecting a warm lamp swamps a thin ink layer.

Nothing in the exposure statistics predicts this. So when the ink
channel comes up empty the detector **refuses and says so** — a
`Pose(False, "ink_not_found …")` — rather than falling through to the
greyscale path, which would silently return the shadow-confused
answer we have spent a week characterising.

## Shape of it

**`InkSignature`, a dataclass in `acme/model.py`, carried on
`Calibration`.** Swapping ink is then editing a JSON file, which is
the whole point:

```python
@dataclass
class InkSignature:
    """What the peg crowns are coloured with, in chroma terms."""
    direction_deg: float        # (a*, b*) angle away from paper
    tolerance_deg: float        # how far off that direction still counts
    min_displacement: float     # per unit L*, so a dim peg still passes
    name: str = ""              # "pen+GEAR dry erase blue", for the record
```

Direction and tolerance carry the colour; nothing else in the pipeline
names a hue. Blue is −70° to −91° here; Dykem Steel Blue will be some
other pair of numbers in the same field, and a red ink would be near
0° without a line of code changing.

**`acme/ink.py`** holds the arithmetic: sRGB to L\*a\*b\*, the
paper reference measured in-frame, the normalised score, and the mask.
No ComfyUI, no torch, testable on arrays — like the rest of `acme/`.

**`acme/detect.py`** gains the gate: when the calibration carries an
`InkSignature`, propose candidate windows from the ink mask and fit
each with the existing `fit_rect` on luminance. When it does not,
behave exactly as now. The existing corpus has no ink in it and must
keep passing.

**A way to measure a new ink.** `bin/measure-ink`, given a frame and
rough peg locations, reports the direction, the spread and the
displacement — so onboarding the Dykem is shooting one frame and
pasting three numbers, not guessing at a colour name.

## How stable is the signature? Measured

The direction is the only colour parameter, so its stability is the
question that decides whether this is a one-off calibration or a
per-session chore. Measured across every inked frame in the corpus —
`blue_008`, `blue_010`, `blue_hamster_003`, `blue_hamster_002`,
`fresh_ink_007`, `fresh_ink_008`: two days, four lighting setups, blank
paper and artwork, a bar move, and a re-inking in the middle.

| | mean | sd | range |
|---|---:|---:|---:|
| left rect peg | −75.0° | 6.0° | 15.7° |
| round peg | −89.1° | 3.1° | 8.0° |
| right rect peg | −92.5° | **1.5°** | 3.5° |
| all eighteen | −85.5° | 8.6° | 26.8° |

**Lighting is not the dominant variable; peg geometry is.** Each peg
holds to 1.5–6.0° across everything the corpus throws at it, while the
three pegs sit 17.5° apart from each other. Splitting the same numbers
by session instead of by peg gives −87.8° against −84.4° — a 3.4°
shift, a fifth of the between-peg spread.

That the pegs differ is not a defect. Each crown is a mirror at its
own angle, reflecting a different part of the room, so the ink-tinted
reflection mixes with a different background on each. It is geometry,
and it is why the signature wants one generous tolerance rather than
per-peg tuning: per-peg numbers would encode *this* bar at *this*
camera position, and moving the camera between captures is a supported
operating mode.

**−82° ± 13° covers every peg in every frame**, with no misses. A
stored ±25° leaves comfortable margin without admitting anything else
in the corpus, where the nearest competitor — paper — sits about 100°
away.

### Referencing to the paper is doing half the work

The same eighteen measurements, taken as absolute (a\*, b\*) angles
rather than relative to the paper in the same window:

| | sd | range |
|---|---:|---:|
| paper-relative | **8.6°** | 26.8° |
| absolute | 15.6° | 46.1° |

Paper b\* runs +12.0 to +19.7 across these sessions — the white
balance moving — and referencing to it absorbs that. It is not a
neutral reference (Canson cream sits at a\* +0.5 to +7.4), but it is
an *in-frame* one, which is what matters when the illuminant is
whatever was on the desk that evening.

### Will it change with the camera?

Almost certainly, and the corpus cannot say by how much, because every
frame in it is `v4k_01`. Paper-referencing removes the illuminant, not
the sensor: a different colour filter array and a different ISP put
the same ink at a different (a\*, b\*). Treat the signature as a
property of *camera plus ink*, re-measured with `bin/measure-ink` when
either changes. That is one frame, which is the right cost.

### Where a colour calibration card helps, and where it does not

It **does not** tighten anything on this rig. The dominant residual is
the 17.5° between pegs, which is mirror geometry; no colour transform
changes what a mirror reflects. And the in-frame paper already handles
the illuminant.

It **does** earn its place for three other things:

1. **Portability.** A card gives camera RGB → device-independent
   colour, so a signature measured on one camera transfers to the next
   without reshooting pegs. That matters directly to selling
   calibrated cameras.
2. **A reference that does not depend on paper stock.** The white
   reference is currently a sheet of Canson cream. A different stock
   moves it, and nothing would announce that.
3. **Checking an assumption.** Every number above decodes the camera's
   output as sRGB. That is an assumption about the ISP, not a
   measurement, and a card is how it gets checked.

Worth shooting once and keeping in the corpus. Not worth blocking on:
the paper-relative design works today on the camera we have.

## Built, and what it does on real frames

Implemented in `acme/ink.py`, with the gate in
`acme/detect.find_peg_candidates_by_ink` and the tool in
`bin/measure-ink`. Against every inked frame in the corpus, with the
shipped default signature:

| frame | luminance candidates | ink candidates | on a real peg |
|---|---:|---:|---:|
| `fresh_ink_007` blank | 4 | **3** | 3/3 |
| `fresh_ink_008` **art** | 36 | **3** | 3/3 |
| `blue_010` blank | 3 | **3** | 3/3 |
| `blue_008` blank | 3 | **3** | 3/3 |
| `blue_hamster_003` **art, worn** | 34 | **3** | 3/3 |
| `blue_hamster_002` **art, worn** | 36 | **3** | 3/3 |

Six frames, three candidates each, every one on a peg — including the
two with artwork, where the luminance path returns 34 to 36 and cannot
rank them, and the two whose ink had worn for a day.

### The default signature is measured, not chosen

−59.6° ± 32°, minimum relative chroma 0.23, pooled over all six frames.
Run `bin/measure-ink` on a single frame and it lands within a few
degrees: −63.7, −64.2, −61.2, −67.8 on four of them.

The tolerance is far wider than that 7° spread deliberately. The
nearest competitor in any real frame is the paper, about 100° away, so
tightness buys nothing and costs pegs: at ±25° the worn right-hand peg
drops out, at ±32° it is found.

### Two things the synthetic tests could not have caught

Both were found by running the corpus and neither by the unit tests,
which is the argument for keeping both.

**A sweep must not start from the ink's brightest pixel.** The crown is
chrome, so the ink sits next to a specular highlight and the mask
occasionally catches one. A single such pixel put the threshold sweep's
floor at paper level, above its own ceiling, and the peg vanished. It
starts from the 25th percentile of the ink's luminance now.

**Selecting the ink by saturation and darkness together is worse than
by saturation alone.** Darkness needs a percentile of luminance, and on
a frame with only two distinct levels that selects everything. More
importantly it was unnecessary: the noise it was meant to exclude is
near-black pixels whose hues point every which way, and taking the
hue *mode* rather than the mean discards them anyway. The mean was
measurably wrong — pooled over the corpus it reported 53.5° of scatter
for an ink that holds to about 9.

### Where it can be fooled, honestly

On four uninked frames the gate still proposes candidates — and every
one of them lands within 27 px of a real peg. They are bare chrome
crowns reflecting the white monitor, which reads as blue. So
`ink_not_found` means *this channel is empty*, and an unmarked chrome
crown is not reliably empty. That is a mirror being a mirror, and it
is not a mis-registration risk: it proposes pegs where pegs are.

### The swap works on real imagery, not only in tests

Checked by spinning the whole chroma plane of `fresh_ink_007` about
the neutral axis, which leaves the near-neutral paper where it is and
moves the ink a long way. Nothing was recoloured by hand, so the
detector was not handed a mask it had drawn itself.

| simulated ink | measured direction | found | its own signature | the *blue* signature |
|---|---:|---:|---|---|
| as shot | −63.4° | 3/3 | — | 3 |
| rotated +100° | −3.4° | 3/3 | works | **refuses** |
| rotated −120° | +142.6° | 3/3 | works | 4, none reliable |
| rotated 180° | +115.6° | 3/3 | works | 2 |

Each colour is measured correctly and finds all three pegs, and the
blue signature stops working on every one of them — so the selection
is by colour rather than by the pegs being findable regardless. The
imperfect refusals in the last two rows are an artefact of rotating
*everything*, which drags unrelated dark pixels into the blue
direction; a real ink change moves only the crowns.

## What is genuinely unsettled

* ~~The normalisation constant.~~ Settled: `k = 16`, which is not a
  constant to choose at all. `L* + 16` is `116 f(Y/Yn)`, carrying the
  same cube root as a\* and b\*, so `C*/(L* + 16)` is exactly
  scale-invariant wherever Lab is a cube root. Crowns are dark enough
  to reach the linear segment, where it is not — halving the light
  costs the angle 3.2° and the relative chroma 16.5 % — so the angle
  discriminates and the magnitude is only a floor.
* **Whether the round peg needs its own treatment.** It has been the
  awkward one throughout — a dome, so its ink sits on a curved mirror
  and its landmark height is 5.567 mm rather than zero.
* **Durability, still.** Dry erase lost the round peg in a day. The
  Dykem options are the answer to that and neither has arrived, so
  nothing here should assume even coverage or a long-lived mark.

## Tests to write first

1. A synthetic scene with inked pegs is detected; the same scene with
   the ink removed is not (the gate is doing the work).
2. Ink at half brightness on one peg still passes — the normalisation
   claim, which is the one the right peg falsifies today.
3. Paper-relative: shifting the whole frame's white balance does not
   change which pixels are found.
4. A red `InkSignature` finds red pegs and ignores blue ones, and
   vice versa, with no code difference — the swap claim.
5. A frame with no ink anywhere refuses with `ink_not_found`, rather
   than returning the greyscale answer.
6. A calibration with no `InkSignature` detects exactly as it does
   today, on a real frame from the existing corpus.
7. The gate proposes, the greyscale fit measures: a peg whose ink
   covers a corner of the crown still yields the *crown's* rectangle,
   not the ink patch's.

## Sampling window: the percentile was the fault, not the border

Prompted by "does it make sense to calibrate ink on art images?", and
by the discovery that a predicted 160 px window already reaches past
the punched edge -- the pegs sit 12 mm in, which is 87 px on this rig.

Direction measured from the same predicted windows at growing radii:

| radius | unclipped | clipped to the sheet | clipped, fixed count |
|---|---:|---:|---:|
| 70 px | −66.4° | −66.3° | −63.6° |
| 120 px | −62.5° | −75.1° | −61.8° |
| 160 px | −57.1° | −73.2° | −61.5° |
| 300 px | **+56.2°** | −60.9° | −61.9° |
| 450 px | **+51.4°** | **+155.8°** | −59.6° |

Three separate things were going wrong and only the third is the real
one.

**The desk.** Unclipped, a window past 300 px reaches the wooden desk,
which is strongly saturated brown and wins the chroma selection
outright. Clipping to the sheet fixes that, and yes it leans on the
black mat -- but only through `find_sheet`, and the fitted outline
already in hand is the more precise boundary.

**The percentile.** Clipping alone is not enough: at 450 px it still
fails, and the measured `min_chroma` falls from 0.216 to 0.036 as the
window grows. `measure_signature` took the **top decile** of relative
chroma, which is a *fraction* -- so a larger window is a larger
population of paper and the decile fills up with paper texture. Taking
a fixed **count** instead, sized to the peg's own area through the
homography (about 1500 px here), makes window size stop mattering:
−63.6° at 70 px and −59.6° at 450.

**The art, which is what is left.** With both fixed, blank sheets are
stable across the whole range and art sheets are stable only to
160 px, flipping to +73° and +79° at 300 -- exactly where the window
reaches the drawing, whose nearest mark is 200 px from a peg.

So the answer to the question is: measure on a **blank** sheet. Not as
a precaution against a hazard that might exist, but because it is the
one remaining limit on how wide the window may be, and the window has
to be wide because the prediction carries the paper's bow.

### Built, and the radius now costs nothing

`measure_signature` takes `inside` and `count`; `bin/measure-ink`
passes the eroded sheet and a count from `ink_pixel_count`. The same
sweep as above, through the tool:

| radius | direction | tolerance | min_chroma |
|---|---:|---:|---:|
| 70 px | −63.8° | 30.9 | 0.292 |
| 160 px | −61.8° | 31.7 | 0.331 |
| 300 px | −62.3° | 33.0 | 0.327 |
| 450 px | −59.6° | 31.0 | 0.355 |

Against −66.4° drifting to **+51.4°** before, with the chroma floor
collapsing from 0.216 to 0.107. A predicted window is now as good as a
hand-typed one, so the manual step is gone with nothing given up.

Three things the tests found that reading would not have.

**The count wants half the *smaller* peg's area, not the larger's.**
The pen reaches only part of a crown, and what it misses is bare
chrome -- dark but not coloured, so it only dilutes the hue. The full
area of the larger peg gives −73.7° at radius 70 and −66.3° at 450:
biased, and still biased as the window grows. Half the round peg's
gives −63.8° and −59.6°. Flat was the property being bought, so the
smaller count is the right one. That judgement lives in
`ink_pixel_count` rather than in the test fixture where it started.

**Select by index, not by thresholding at the count-th value.** They
differ when values tie, and a flat rendered scene has thousands of
pixels at one chroma: asked for 1600 of them, `>= cut` returned 4944
-- the whole window, paper included.

**The scale is 9.71 px/mm, not the 7.25 assumed earlier.** So 12 mm of
punch offset is 117 px, and a 70 px window does not reach the punched
edge while a 160 px one does. `sheet_scale_px_per_mm` measures it from
the fitted outline rather than anyone assuming it.

## Dykem Steel Blue measures the same hue as the dry erase

First of the two Dykem products, `data/captures/dykem_steel_blue`,
blank sheet, phone over the centre of the page.

| ink | direction | tolerance | min_chroma |
|---|---:|---:|---:|
| pen+GEAR dry erase | −61.8° | 31.7 | 0.331 |
| **Dykem Steel Blue** | **−61.2°** | **28.6** | **0.280** |

Six tenths of a degree apart, and the signatures are interchangeable:
each finds 3 of 3 pegs on the other's frame. So the colour is not what
a second calibration would be buying. What the layout fluid is for is
durability — the dry erase lost the round peg in a day — and that
cannot be read off one frame.

Worth keeping `v4k_01_steel_blue.json` separate anyway, since the two
will diverge if the fluid ages differently, but on today's evidence
the existing calibration would detect this ink perfectly well.

The frame still refuses at the fit, `residual_too_high` at 40.06 px
against a 1.5 px threshold. That is the outstanding problem and it is
not about ink: the dry-erase frames refuse the same way at 32.88 px.

## Three media compared: Brite-Mark 84001 wins

| ink | direction | tolerance | min_chroma | ink px per peg | total |
|---|---:|---:|---:|---|---:|
| pen+GEAR dry erase | −61.8° | 31.7 | 0.331 | 1885 / 557 / 286 | 2728 |
| Dykem Steel Blue fluid | −61.2° | 28.6 | 0.280 | 1566 / 567 / 197 | 2336 |
| **Dykem Brite-Mark 84001** | **−68.0°** | **20.0** | **0.649** | **1948 / 1234 / 609** | **3794** |

The paint marker is better on every axis that matters.

**Twice the saturation.** A chroma floor of 0.649 against 0.28 and
0.331. It is opaque paint rather than a thin tint over a mirror, so
what the camera sees is the paint instead of the paint plus whatever
the chrome is reflecting.

**A hue that holds.** Tolerance 20.0 comes from a 5 degree scatter,
against 8 to 9 for the other two. Same reason: no mirror underneath to
mix in the room.

**Coverage where it has always been missing.** The right-hand peg has
been the weak one since the first blue frame — 286 px with dry erase,
197 with the fluid, **609** with the paint. The middle peg doubles too.

And by eye the crowns are matte, with the specular reduced from broad
reflections to pinpoints. That is the mirror problem retired, which
was the cause of `blue_006` showing almost no ink at the same exposure
and white balance as `blue_010`.

### Withdrawn: the tight signature is not too specific

This section said the Brite-Mark signature's 0.649 chroma floor was
above what a thin layout fluid puts down, so it found two of three
pegs on the Steel Blue frame and the calibration therefore had to
match the ink on the bar. That was wrong.

The limit was never the chroma floor. It was a **pixel-count** floor:
`min_area_px` is sized for a whole peg, five per cent of the smaller
one, and once the landmark became a patch of paint *on* a peg that
floor was measuring the wrong thing. The weakest crowns give 159 to
172 px against a 200 px peg floor. The window stage proposed them at
its own 12 px floor and the area check then threw them away.

With one floor used throughout the ink path, all nine combinations of
three signatures and three frames find all three pegs. The inks are
interchangeable after all, which is the simpler and happier result.

Durability is still unmeasured for both Dykem products, and it is the
reason they were bought. Paint on unprepped chrome may or may not
survive sheets being pushed on and off; the dry erase lost the round
peg in a day.
