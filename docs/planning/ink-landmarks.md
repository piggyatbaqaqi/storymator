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

## What is genuinely unsettled

* **The normalisation constant.** Dividing by L\* alone blows up on
  near-black pixels; something like `chroma / (L* + k)` needs `k`
  chosen against the corpus rather than picked.
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
