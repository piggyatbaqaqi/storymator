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
