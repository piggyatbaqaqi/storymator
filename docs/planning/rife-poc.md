# RIFE proof of concept — design

*2026-10-16. Follows
[pencil-test-architecture.md](pencil-test-architecture.md), which makes
the proxy generator an instrument whose only obligations are
legibility, speed and faithful spacing.*

## 1. What it must answer

Five questions, in the order that would kill the idea soonest.

| # | question | why it could kill the idea |
|---|---|---|
| 1 | Does RIFE expose an **arbitrary timestep**? | the CLI documents only `--multi` and `--exp`, i.e. powers of two. If the model API has no `timestep`, §2's dyadic driver stops being optional |
| 2 | Is the output **legible enough to judge a pose**? | §4.2 predicts flow methods *ghost and double* lines on sparse black-on-white. That is the failure that matters, not joint onset |
| 3 | Does it **honour position along the path**? | §1's spacing contract. A proxy that puts a drawing somewhere the chart did not ask for voids the animator's approval |
| 4 | How does it degrade with **gap width**? | acceptance §7's unanswered question, promoted to load-bearing by §7c |
| 5 | Is it **fast enough for a flip loop**? | the whole reason we are not using ToonComposer |

**What it must not try to answer.** Whether the drawings are any good,
whether they obey the seven principles, or whether the final synthesis
stage works. The frames are disposable by design; see §1 of the
architecture.

## 2. Prerequisite, already checked

Interpolation accuracy cannot mean more than the registration under it.
Peg centroids across the twelve cleanups:

| | |
|---|---|
| typical disagreement with drawing 1 | **1–3 px** |
| worst | **6.4 px**, drawing 5 |
| at 200 px/inch | **0.82 mm** |

Good enough that a global shift will not dominate — but **6.4 px is a
floor on what any accuracy number here can mean**, and it is not
nothing for a flow estimator working on two-pixel lines. Report it
beside every result.

*(Two drawings returned four peg blobs rather than five. That is my
detector missing an edge dot, not a registration fault — the five-blob
cases bracket them.)*

## 3. The data

The corpus is better than a single example, which matters because one
triple proves nothing.

| | |
|---|---|
| cleanup triples | drawings *n*, *n+g*, *n+2g* — **10 at g=1** |
| rough triples | same, in blue pencil — **10 at g=1** |
| ground truth | the middle drawing, which the artist made |
| gap sweep | **g = 1, 2, 3** — predict 1, 3, 5 frames across a widening span |

The gap sweep is the point. §7c argues that the joint-onset objection
scales with gap width; this measures whether *interpolation quality*
does too, on the same axis.

## 4. Measurement, chosen in light of a mistake

**Mean absolute error is not used.** It misled twice during the
ToonComposer spike — it passed a run with a third arm, then ranked a
washed-out run above a better one — and an operator's eye caught both.
See §7b's retraction.

| what | measures | why this one |
|---|---|---|
| **contact sheets** | everything | **primary.** A human looks. This is the arbiter |
| **ink ratio** (generated ÷ truth ink pixels) | ghosting and washout | **directly tests §4.2's prediction.** Doubling pushes it above 1; washout below |
| **Chamfer distance** between ink masks | how far lines land from true lines | IoU is brutal on two-pixel lines, where a sub-pixel shift reads as total failure. Chamfer degrades gracefully and is interpretable: *"the line is 3 px from where it should be"* |
| **spacing fraction** via `penciltest.arcs` | §1's contract | the harness, used for its actual purpose for the first time |

## 5. Preprocessing sweep

§4a left open what RIFE wants as input, and flagged that the 1990s
threshold evidence may not transfer because **optical flow wants
gradients and a threshold destroys them**.

Three conditions, same triples: **raw capture**, **contrast-normalised
greyscale**, **thresholded**. If raw wins, §4a's conclusion — that
legibility processing is for registration and display, not for the
interpolator — is confirmed by measurement rather than argument.

## 6. Environment

A separate conda env, for a reason the ToonComposer spike already met:
**Practical-RIFE states python ≤ 3.11 and `storymator` is 3.14.** Same
pattern as `tooncomposer-spike` — do not disturb the documented
environment.

Licence is clean: MIT for code, and the model links are *"under the
same MIT license as this project"*. The one open item from
[pencil-test-architecture.md](pencil-test-architecture.md) §3 stands —
a third-party derivative warns the *training data* may carry
non-commercial terms. **Ask the author before anything ships**; it does
not block a proof of concept.

## 6a. No GPU required — and CPU is the default, not the fallback

Monte asked for confirmation. **Confirmed**, and it is now a design
constraint rather than an expectation.

**The evidence.**

| | |
|---|---|
| device selection | upstream's is the standard `torch.device("cuda" if torch.cuda.is_available() else "cpu")`, with cuDNN touched only when CUDA is present. **CPU works unmodified** |
| precision | no fp16 path in upstream `inference_img.py`. A community fork has an fp16 flag, but it sits inside a CUDA check and does nothing on CPU |
| model size | **~23 MB, fp32**. Against ToonComposer's 77 GB |
| fp16 | not wanted anyway — RIFE's coarse-to-fine flow is reported fp16-sensitive, so **fp32 on CPU is the accurate path**, not a compromise |
| this machine | 24-core Intel Core Ultra 9 275HX |

**The workload is small.** Ten triples × three preprocessing
conditions × three gaps × two media = **180 interpolations**. At 1–5
seconds each that is **3 to 15 minutes**, once, on the CPU.

**So the constraint:** the POC **runs on CPU by default and must be
written that way**. The GPU is used only for an explicit timing
comparison, never silently.

Two reasons that matters beyond convenience.

**An honest answer to question 5.** The machine has a GPU, so letting
torch pick a device would quietly measure the GPU and tell us nothing
about whether a drawing desk needs one. Architecture §5 puts the
instrument outside ComfyUI precisely so it can be light; if the proxy
path runs on a CPU, the desk's hardware story gets much simpler.

**Nothing else in the POC wants a GPU either.** Chamfer, ink ratio,
contact sheets and `penciltest.arcs` are numpy, Pillow and pure Python.

**One thing to check in step 1**, while reading the model file for the
timestep API: that the chosen 4.25 weights carry no CUDA-only
operation. Nothing in RIFE's architecture suggests one — it is
convolutions and `grid_sample` — but it is a free check while that file
is already open.

**Pin the thread count when timing.** Twenty-four cores will otherwise
make the numbers depend on what else the machine is doing, and this
session has already lost a run to a desktop competing for memory.

## 7. Order of work

1. **Verify the timestep API by reading the code**, not the README.
   The model file in `train_log/` is what matters, not
   `inference_video.py`. This is a gate: it decides whether §2's
   dyadic driver is needed.
2. Build the env, fetch a 4.25 model, interpolate one pair, look at it.
3. The g=1 cleanup sweep, three preprocessing conditions.
4. The gap sweep.
5. Roughs, which is the real input — the cleanups are a kinder test.
6. Timing, **CPU first** with a pinned thread count, GPU only as an
   explicit comparison. See §6a — the CPU number is the one that
   decides whether a drawing desk needs a graphics card.

## 8. Success criteria — provisional, Daniel's to set

Stated so the POC can fail rather than merely produce output. The
numbers are placeholders, in the same spirit as `arcs.py`'s thresholds.

| | provisional bar |
|---|---|
| legibility | an animator identifies the pose. **Binary, judged by eye** |
| ghosting | ink ratio within **0.7–1.4** of truth |
| spacing | fraction within **0.05** of the chart. Acceptance §2's named failure is 0.2 |
| speed | **under 200 ms/frame**, so a flip loop survives |

## 9. Scope and lifecycle

**Throwaway, like the ToonComposer spike.** Research code in the
scratchpad, no TDD, downloads kept. Its product is a **recorded
finding** in this directory, not a module.

If RIFE passes, the proxy generator is then built properly — tests
first, confirmed, committed — inside the instrument described in
architecture §5, which does **not** run through ComfyUI.

If it fails, the finding says which of the five questions killed it,
and the next candidate is chosen against the same five.


---

# Findings

## Gate: the timestep API exists — and the README does not say so

**Question 1 is answered affirmatively, by reading the code.** The 4.25
model ships its own `RIFE_HDv3.py`, and:

```python
def inference(self, img0, img1, timestep=0.5, scale=1.0):
```

`inference_img.py` exposes it as `--ratio`, documented *"inference
ratio between two images with 0 - 1 range"*, and calls
`model.inference(img0, img1, args.ratio)` directly.

So **arbitrary *t* is available** and §2's dyadic driver is confirmed
unnecessary. The README's model list mentions only `--multi` and
`--exp`, which is what made this a gate; the design was right to say
*read the model file, not the README*.

## CPU-only by construction

`torch 2.14.1+cpu`, `torch.cuda.is_available() == False`. Not the GPU
hidden behind an environment variable — a build with no CUDA in it, so
§6a holds whatever anyone passes later. The PoC asserts it on startup.

Two environment notes worth keeping:

* `conda run -n <env>` silently resolved to a **different environment**
  more than once. Every command here uses the interpreter path
  directly. Same lesson as the ToonComposer spike.
* A user-level `pip.conf` carries
  `extra-index-url = …/whl/cu129`, which quietly pulls a **CUDA build**
  even when `--index-url …/whl/cpu` is given. `PIP_CONFIG_FILE=/dev/null`
  is what forces the CPU wheel.

## Speed: question 5 answered

| | |
|---|---|
| 1024 × 775, 8 threads | **0.40 s/frame** |
| model | 22.9 MB, from the official Drive link |
| load | about a second |

Against the provisional 200 ms bar, this is **twice too slow at full
width** — but it is CPU, at a resolution chosen for inspection rather
than for flipping, and the thread count was a third of the machine. It
is the right order of magnitude, which is what the question asked.
Compare ToonComposer at **69.9 s/frame on a GPU**: RIFE is **175×
faster on a CPU**.

## No ghosting. The §4.2 prediction was wrong

§4.2 predicted that flow methods *"ghost and double lines rather than
move them"* on sparse black-on-white, and treated that as the likely
killer.

**It did not happen.** Ink ratio against the artist's own drawing is
**0.75** — the lines are *fainter*, not doubled. Doubling would have
pushed the ratio above 1; this is the opposite failure, and a milder
one.

Looking at the frames: the generated drawings are **coherent, single-
line figures** — hat, cane, coat tail, both legs — legible enough to
read the pose at a glance. They are lighter than the artist's, and the
fastest-moving parts smear, but they are *drawings*, not smears.

**Question 2 is answered affirmatively**, on the cleanups at gap 1.

## The finding that reaches furthest: the ink centroid is the wrong feature

The PoC measured where the generated drawing sits along the chord
between its neighbours. It also measured where **the artist's own
drawing** sits — and that is what matters:

| | mean | sd | range |
|---|---|---|---|
| RIFE's middle | 0.412 | 0.339 | −0.29 … 0.96 |
| **the artist's middle** | **0.427** | **0.202** | **0.11 … 0.81** |

**The artist's own inbetween does not sit at 0.5 either.** On this
material the ink centroid is not a measure of position along the path:
in a run cycle the pose changes shape — a leg extends, a coat swings —
so the centroid moves for reasons that have nothing to do with travel.

Three consequences.

**§11.2's decision 7 is refuted by measurement.** That decision was
*"the tracked feature starts as the ink centroid… deterministic and
testable today"*. It is deterministic and it is testable, and the test
says it does not measure what it was chosen to measure.

**The first spacing number this PoC produced was meaningless.** Mean
error against *t*=0.5 came out at 0.277 — worse than acceptance §2's
named failure of 0.2 — and it was comparing RIFE against a reference
the artist does not meet. The honest number is **RIFE against the
artist: 0.189 mean absolute difference in fraction.** Still large, but
it is a number about RIFE rather than about the centroid.

**`HarnessSpacingError` needs a feature before it can do its job**, and
it is the instrument the whole fast-proxy architecture depends on
(architecture §1's timing contract). Candidates: global translation by
phase correlation, which measures travel and ignores shape change; a
tagged landmark such as the hat; or the bounding-box centre. This wants
settling before the instrument is built.

## The matrix

Two media × three preprocessing conditions × three gaps, ten triples at
gap 1 falling to six at gap 3.

### Thresholding wins, and §4a's speculation was wrong

§4a guessed that *"optical flow wants gradients and a threshold
destroys them"*, and that RIFE *"may well prefer an unprocessed
greyscale capture to a clean threshold"*.

**The opposite is true**, on equal masks and by eye:

| preprocessing | chamfer | by eye |
|---|---|---|
| raw | 12.3 px | faint but legible |
| contrast-normalised | 12.2 px | paper grain amplified into visible noise |
| **thresholded** | **6.0 px** | **crisp black on white, no texture, fully legible** |

Thresholding **halves** the error and produces the cleanest frame. The
gradient argument assumed paper texture was neutral; it is not, it is a
distractor the flow estimator latches onto. Remove it and only the
lines remain.

**This vindicates Daniel's 1990s memory more strongly than it was
offered.** The claim was that crude threshold captures were *enough*
for judging timing. On this evidence crude threshold captures are
*better input*, not merely tolerable.

### The gap sweep: quality degrades, measurably

Within `raw` on cleanups, so the comparison is like with like:

| gap | chamfer | fraction error vs the artist |
|---|---|---|
| 1 | 9.7 px | 0.19 |
| 2 | 17.6 px | 0.74 |
| 3 | 21.9 px | 1.35 |

**§7c's gap-width thesis holds for interpolation quality too.** The
argument there was about joint onset; this is the same axis measured on
a different property. One inbetween between adjacent drawings is a
different proposition from filling a wide span, and now there is a
number for it.

### Roughs work at least as well as cleanups

At raw, gap 1: chamfer **7.7 px** on roughs against **9.7 px** on
cleanups. The blue-pencil roughs — the actual input a pencil test would
have — are not the harder case. That removes a worry §4a raised.

## Two measurement bugs of my own, and a pattern

**The ink mask was not invariant across preprocessing.** It used
`g < percentile(g, 92) - 0.12`: a fixed *offset*. Contrast-normalising
stretches the histogram, so that offset selected **7.4 % of the frame
instead of 1.8 %** — four times as much ink. Chamfer then collapses for
free, because with that much ink everything is near something.
`norm` appeared to beat `raw` **eightfold** (1.7 px against 13.8) on
that basis alone. Replaced with a fixed *fraction*; verified that all
three conditions then select 1.80–1.87 %, which is what makes the table
above fair.

**Twenty-four threads is ten times slower than sixteen.**

| threads | s/frame |
|---|---|
| 4 | 0.44 |
| 8 | 0.39 |
| **16** | **0.35** |
| 24 | **3.50** |

The whole matrix ran at 24 and its timings are therefore worthless.
The quality numbers are unaffected — thread count does not change
output. This machine's 24 cores are not alike (Intel Ultra 9 275HX,
performance and efficiency cores), and saturating them collapses
throughput. **§6a said to pin the thread count; it did not say to find
the right one first.**

**The pattern, now three for three.** Mean absolute error ranked a
washed-out ToonComposer run above a better one; it then ranked CFG 3.0
above CFG 7.5; and now a fixed-offset ink mask ranked `norm` eightfold
above `raw`. Every time, **a threshold I chose was not invariant to the
thing I was comparing**, and every time the frames said otherwise at a
glance. The design named contact sheets as the arbiter for this reason.
It is worth promoting from a habit to a rule: **look first, and treat
any metric as a hypothesis until a picture agrees with it.**

## Verdict against the five questions

| # | question | answer |
|---|---|---|
| 1 | arbitrary timestep? | **yes** — `inference(img0, img1, timestep, scale)` |
| 2 | legible enough? | **yes**, and thresholded input is best |
| 3 | honours position? | **cannot yet be measured** — the tracked feature is broken, not RIFE |
| 4 | gap degradation? | **measured**: 9.7 → 17.6 → 21.9 px over gaps 1–3 |
| 5 | fast enough? | **0.35 s/frame** at 1024 px, 16 threads, on CPU. 175× faster than ToonComposer on a GPU |

Against the provisional bars: legibility **passes**, ghosting
**passes** (0.75–1.03, no doubling anywhere), speed **misses 200 ms at
1024 px** but was not tuned for it, and spacing **cannot be assessed**
until the feature question is settled.

**RIFE passes everything that was in doubt about RIFE.** What is left
open is ours: `HarnessSpacingError` needs a feature that measures
travel rather than shape change, and that blocks architecture §1's
timing contract rather than this candidate.


---

# Retraction: the verdict was wrong, and so was the method

**2026-10-17.** Monte opened the generated frames and read all ten:

> *"gen_04.png has two heads and maybe 3 feet? gen_05.png has two
> bodies and three arms… gen_06.png and gen_07.png are the only images
> without major distortions."*

He is right. **The verdict above is withdrawn.**

## What I actually did

I looked at **three frames out of 180** — triples 1, 4 and 7 of one
condition — and generalised to *"legible enough to read the pose…
question 2 answered affirmatively"*. Two paragraphs after writing
*"look first, and treat any metric as a hypothesis until a picture
agrees with it."*

## The metric could not see the thing it was used to refute

I declared §4.2's ghosting prediction wrong because **ink ratio was
0.75**, below 1, where doubling should push it above.

**Ink ratio cannot detect duplicated structure.** A limb doubled at
reduced intensity leaves total darkness unchanged or lower. The metric
measures how much ink there is, not whether the anatomy is coherent —
so a frame with two heads and three arms can score *better* than a
faithful one.

**§4.2 appears to have been right.** *"Lines ghost and double rather
than move"* is precisely what two heads and three arms are. The
prediction was not refuted; it was measured with an instrument blind to
it.

## And the rough half of the matrix was invalid

The corpus manifest records that the roughs are stored in **capture
order** — `3, 1, 1.5, 2, 4, …` — not drawing order. §12.2 of the
planning note says so explicitly. **The PoC indexed by file position
anyway**, so its first rough triple interpolated drawing **3** and
drawing **1.5** to predict drawing **1**, which is not an inbetween of
anything. Every rough number in the matrix above is void.

This is the third time a corpus fact was written down and then ignored
by code written afterwards — the sheet sizes in §12.1 did the same
thing an hour earlier.

## Fixed, and re-measured

Sorting by drawing number, and asking for the *t* the artist's drawing
actually sits at — the roughs carry 1.5 and 6.5, so consecutive
drawings are not evenly spaced and the midpoint is often **0.333** or
**0.667**, which exercises the arbitrary timestep properly:

| | before (invalid) | after |
|---|---|---|
| chamfer | 7.5 px | **5.68 px** |
| spacing error | 0.273 | **0.12** |

Real improvements. **The structural failures persist.** Of ten frames,
roughly five are usable and four are grossly broken — doubled heads,
tangled limbs — with one marginal. **Thresholding fixes line crispness
and not anatomy:** the same triples fail under `raw` and `thresh`, so
it is the *motion* in those triples that defeats RIFE, not the input
preprocessing.

## Revised verdict

| # | question | revised answer |
|---|---|---|
| 1 | arbitrary timestep? | **yes**, unchanged, and now actually exercised at *t* = 0.333 and 0.667 |
| 2 | legible enough? | **qualified failure.** Works where displacement is small; fails grossly where it is not. About half the frames |
| 3 | honours position? | spacing error **0.12** against the artist — but the centroid feature is still suspect |
| 4 | gap degradation? | measured, and the within-triple variation is larger than the gap effect |
| 5 | fast enough? | **0.34 s/frame**, unchanged |

**RIFE is not yet a usable proxy generator.** It is fast, correctly
licensed, and takes a chart — but it produces an unusable drawing
roughly half the time on this material, and those failures are the kind
an animator would reject instantly.

## What this changes

**A failure detector may matter more than a better interpolator.** If
the broken frames can be flagged automatically, a proxy that works half
the time is still useful — the instrument shows what it has and marks
the rest. Duplicated structure should be detectable: a doubled figure
has more connected components, or ink where the two source drawings
disagree. That is cheap to test and has not been tried.

**And the gap thesis gets sharper.** The failures cluster on triples
with large displacement, not uniformly. §7c argued the joint-onset
objection scales with gap width; this says *interpolation itself* has a
displacement budget, and the useful question is not "how wide a gap"
but "how far does the drawing move".


---

# The media question: does cleaning up the roughs buy anything?

**2026-10-17**, Monte's question. Full matrix rerun with the drawing
order fixed, matched *t*, and two metrics chosen to see what ink ratio
could not.

## Making the comparison fair

After sorting, **index *i* is the same drawing in both media** — rough
1.5 is clean 2, rough 6.5 is clean 8. So clean-versus-rough can be a
genuine like-for-like test.

One trap had to be avoided. **The cleanup renumbering destroyed the
spacing information.** The roughs say 2 sits a *third* of the way from
1.5 to 3; the cleanups, renumbered 1…12, say 3 sits *halfway* between 2
and 4. Those are the same three drawings and the two numberings
disagree. The matrix therefore uses index-based *t* for both media, so
the comparison is about the drawings and not about the numbering.

*(That the renumbering discarded the artist's spacing is itself worth
noticing. §13's exposure sheet is where that information belongs, and
this is a concrete case of it being lost when it had nowhere to live.)*

## The answer: no, and it may cost you

| prep | gap | chamfer, clean | chamfer, rough |
|---|---|---|---|
| raw | 1 | 12.3 | **7.7** |
| raw | 2 | 19.5 | **14.9** |
| raw | 3 | 23.2 | **22.1** |
| norm | 1 | 12.2 | **8.4** |
| thresh | 1 | 6.0 | **5.8** |

**The roughs interpolate at least as well as the cleanups, and often
better.** By eye, on matched columns: the first two are equally good in
both media; the third and fourth are **clearly better from the
roughs**, where the cleanup version tangles the arm and cane; the fifth
fails in both.

**I suspected a confound and tested it.** Scattered ink could lower
chamfer for free, since every point would be near something. Measured:
the rough's mean distance from an arbitrary pixel to the nearest ink is
**139.9 px against the cleanup's 108.4** — *sparser*, not denser. The
hypothesis was refuted, and the chamfer difference survives it. For
once the numbers and the pictures agree, which is the standard this
document set after three failures to meet it.

**A plausible reason, offered as one.** Flow estimation wants texture.
A cleanup is sparse, confident single lines — the aperture problem at
its worst. A rough carries construction lines, broken strokes and tone,
which is more for an estimator to hold on to. §4.2 reasoned that line
art is hard for flow *because* it is sparse; the corollary nobody drew
is that **the sparser of two line drawings should be harder**, and the
cleanup is the sparser one.

## What it does not fix

**Both media fail on the same drawings.** The columns that tangle,
tangle in both. Cleaning changes how well the easy cases render; it
does not change which cases are hard. That remains displacement, as the
retraction above found.

## The one clean monotone result

The gap sweep, pooled across media and preprocessing:

| gap | chamfer | fraction error |
|---|---|---|
| 1 | 8.7 px | 0.31 |
| 2 | 15.1 px | 0.50 |
| 3 | 19.9 px | **1.60** |

Degradation is steady and the fraction error explodes at gap 3.

## Fragmentation: the structural signal

RIFE **roughly doubles the number of connected ink fragments** on
cleanups — 5.6 in the artist's drawing against 9.9 generated. On
thresholded roughs it is far worse: 7 becomes 33.

This is the metric ink ratio could not supply, and it points the right
way. It is **not yet validated against the eye** on a frame-by-frame
basis, so it is a candidate failure detector rather than a working one
— which is exactly the status ink ratio should have had.

## Consequence for the architecture

[§4a](pencil-test-architecture.md) recommended dropping line
simplification from the pencil-test path on architectural grounds: the
frames are discarded, so simplifying them is work on a thrown-away
artefact.

**That recommendation now has evidence behind it, and a stronger
form.** Cleaning up a rough before interpolating it does not help the
interpolation and appears to hurt it. The pencil test should run on the
roughs as captured.
