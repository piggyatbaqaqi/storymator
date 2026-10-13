# Inking and inbetweening as ComfyUI plugins: an assessment of the candidates

*Assessment written 2026-10-13, in answer to a proposal to build a
ComfyUI plugin suite for rough → inked line art and then inbetweens
over successive inked pairs, using a LineArt ControlNet for the inking
and either Wan 2.1 or FrameFusion for the tweening.*

*Governing document: [the coarse scoping](../README.md). This note is
subordinate to [inbetween-acceptance.md](inbetween-acceptance.md),
whose §3 timing rule and §6 baseline argument decide most of what
follows.*

---

## 1. The short answer

| proposed | verdict | because |
|---|---|---|
| **LineArt ControlNet** for inking cleanup | **Wrong tool, right neighbourhood** | A ControlNet does not clean a drawing; it *generates a new picture* conditioned on one. Using it for cleanup means a round trip through a model that reinvents the line — the exact failure the acceptance note rejects. Keep it for the later colour/render stage, where redrawing is the point. |
| **Wan 2.1** for inbetweens | **Keep as substrate and as baseline, not as the answer** | Genuinely open (Apache-2.0) and the best open video model available, but it is arm A: no notion of "the same line, moved", and **timing is not an input**. That violates the hard rule in acceptance §3. |
| **FrameFusion** for inbetweens | **Keep as the calibration baseline — it is more valuable than it looks** | It is the only candidate here that takes *t* as a parameter, so the timing chart maps onto it exactly. It will also fail successive-breaking-of-joints *by construction*. That combination makes it the perfect instrument for acceptance §6. |
| **not proposed** | **ToonComposer (TencentARC, ICLR 2026) should be the primary candidate** | Sparse sketch injection **at selected temporal positions** — that is a slot for the timing chart. Cartoon-domain adapted, MIT weights on an Apache-2.0 base, and it unifies inbetweening with the colour stage the governing document also asks for. |

The headline: **the proposal is missing the one model that was designed
for this job**, and the two models it names are both best understood as
baselines rather than as the engine.

## 2. A hardware correction, because it changes the sums

> "an RTX 5090 with 24G of VRAM"

The desktop RTX 5090 has **32 GB** of GDDR7 on a 512-bit bus,
1,792 GB/s, 21,760 CUDA cores, 575 W. The part with **24 GB** is the
**RTX 5090 Laptop GPU**, which is a different chip: GB203 — the same
die as the *desktop 5080* — with 10,496 CUDA cores, a 256-bit bus at
896 GB/s, and at most 175 W.

So the figures imply the laptop part, and that is roughly **half the
desktop's compute and half its bandwidth**. Everything in §7 is sized
for 24 GB at 896 GB/s. If it is in fact a desktop 5090 with 32 GB, the
conclusions do not reverse but the training question in §7 gets
materially easier. **Worth confirming before anyone orders weights.**

Two Blackwell practicalities either way:

* sm_120 needs CUDA 12.8+ and PyTorch 2.7+. Older ComfyUI custom-node
  requirements pins will silently drag in a wheel with no sm_120
  kernels and fall back to something slow or fail at load.
* FP8 is native on Blackwell, which is the thing that makes §7 work at
  all. Lean on it.

---

## 3. Stage one: inking

### 3.1 "LineArt ControlNet" names two different things

This is the root of the confusion, and it is ComfyUI's fault for using
one word for both.

**The preprocessor** — `LineArtPreprocessor`,
`AnimeLineArtPreprocessor`, `Manga2Line` — is a small feed-forward net
that *extracts* line art from a picture. Licence-wise these are mostly
fine (the anime one descends from Anime2Sketch, MIT). But they are
trained to find lines in *finished* artwork. Point one at a rough with
construction lines, a ghosted first attempt and a smudge, and it
faithfully extracts **all of it**. It has no opinion about which of
those lines is the ink, because nothing in its training ever asked it
to have one.

**The ControlNet proper** — `control_v11p_sd15_lineart`,
`control_v11p_sd15s2_lineart_anime` — conditions a diffusion model on
a lineart image. Its output is a *rendered picture*, not a drawing. To
use it for "cleanup" you must generate a picture that follows your
lines and then extract lines back out of it. That round trip is a
generative pass over the artist's drawing, and acceptance §1 already
settled what is wrong with that:

> If the model re-draws the character off model, what plays back is
> the model's motion, not the motion your two poses imply — which
> makes it useless for the one job it has.

The same sentence applies one stage earlier. A pencil test is only
diagnostic if it tests *your* drawings. A cleanup stage that
regenerates the line has broken the pencil test before the tweener
ever runs.

There is a licence objection too. The SD1.5 lineage carries
**CreativeML OpenRAIL-M**, which is not a FOSS licence — it attaches
use restrictions and carries them downstream. Against the project's
standing rule, that wants deciding before it enters the pipeline, not
after.

### 3.2 The split that the inking stage actually needs

The useful move is to stop calling it one stage:

| | what it is | who decides | how to build it |
|---|---|---|---|
| **Legibility cleanup** | paper removal, white balance, de-shadowing, contrast normalisation, optional stroke thinning | nobody — it is measurement | deterministic CV, same category as registration |
| **Inking as an artistic act** | which construction lines survive, where the line weights go, what gets a dry-brush taper | **the artist** | do not automate it yet |

Legibility cleanup is what the pencil-test pipeline actually requires,
it is estimable, it fails loudly, and **the repository already has most
of it**: `acme/ink.py` does von Kries white balance against the paper
and Lab chroma work; `acme/outline.py` and `acme/capture.py` cover
more of the ground. Extending that is
ordinary work with a known cost.

Inking-as-art is a different thing, and automating it repeats the
mistake acceptance §3 already caught in the timing domain. The rule
there was:

> **The system must never infer timing. It reads the chart and obeys
> it.**

The same logic says the system must not decide which lines are the
ink. If it does, it has taken a decision out of the artist's hands —
and unlike timing, there is no chart on the page to read it off.

**And for a pencil test you do not need ink at all.** The first
milestone wants registered, background-free line art, which is
legibility cleanup and nothing more. Inking is a stage-two problem
that the governing document's "rough sketch to fully extrapolated and
coloured" story will eventually need. It is not on the critical path.

### 3.3 The sketch-simplification trap

The honest open model for rough → clean is Simo-Serra's sketch
simplification (`bobbens/sketch_simplification`, SIGGRAPH 2016/2018) —
a fully convolutional net that does exactly this task, deterministically,
with no generative reinvention. It is the right shape of answer.

**Its pretrained weights are non-commercial.** The repository states
plainly: *"Provided models are under a non-commercial creative commons
license"*, and *"freely available for free non-commercial use."*

Against the project's licensing rule that is a blocker, not a caveat.
The architecture is published, so retraining on permissible data is
available as an option, but that is a project rather than an install.
**Recorded here so nobody discovers it after wiring it in.**

---

## 4. Stage two: inbetweening

### 4.1 Wan 2.1 / 2.2 — the right substrate, the wrong interface

Wan is the best thing in open video and the licence is clean
(Apache-2.0, Alibaba Tongyi Lab, so no OpenRAIL question). Wan 2.1
ships a dedicated **FLF2V-14B** first-last-frame checkpoint, which
looks made for this: two drawings in, motion between them out. Wan 2.2
is stronger per frame and introduced the high-noise/low-noise MoE pair,
but its first/last-frame conditioning is assembled in the workflow
rather than by a dedicated checkpoint — **verify that before planning
around it.**

Three objections, in increasing order of seriousness:

1. **Domain.** Trained on natural and photographic video. On
   black-on-white line art it reaches for shading, volume and motion
   blur, because that is what motion looked like in training.
2. **Representation.** It synthesises pixels with no notion of "the
   same line, moved". Costume seams and specific eyelashes get
   reinvented frame to frame — the off-model drift acceptance §1
   names.
3. **Timing has nowhere to go.** This is the disqualifying one. You
   ask for N frames and receive the model's pacing across them. There
   is no argument that means "land this one at 0.33". Acceptance §3
   makes reading the chart a hard architectural rule, and Wan on its
   own cannot satisfy it.

So Wan belongs in the suite — as the **base weights under ToonComposer**
and as the §6 baseline whose failure calibrates the harness. Not as
the tweener.

### 4.2 FrameFusion — the useful baseline, and better than it looks

FrameFusion is tiny: ~10 M parameters, about 37 MB in fp32, descended
from the author's DAIN work. It predicts motion, visibility and
kernel-aware warping data, then warps both inputs toward a target
timestep and blends. It ships ComfyUI packaging, runs fast, and fits
alongside anything.

**Its virtue is the one thing Wan cannot do.** One predictor pass
yields data for *multiple* intermediate timesteps, which means **t is a
parameter you supply**. The timing chart maps onto it directly. It does
not invent pacing, because it has no pacing to invent.

**Its vice is structural, not incidental.** It *warps*. Warping along
a flow field is linear transport, which means every joint in a chain
begins and ends its change together. That is precisely the signature
acceptance §2 identifies as decisive:

> **Simultaneous onset is the signature of interpolation.**

So FrameFusion will fail the successive-breaking-of-joints test on
every chain, every time, for a reason you can state in advance. On
line art it will also show the classic VFI failure mode: lines **ghost
and double** rather than move, because a flow estimator has nothing to
latch onto in a sparse black-on-white drawing with large displacement
and no texture.

**Which is exactly why it is worth installing first.** Acceptance §6
asked for a baseline *in order to fail it*, so the harness has
something to measure before it can be trusted. FrameFusion is the
cheapest possible such instrument: timing-exact, hallucination-free,
and guaranteed to fail one specific named test. If the harness does not
reject it, the harness is broken.

**GIMM-VFI** (NeurIPS 2024) is the stronger member of the same family —
continuous implicit motion modelling, arbitrary-timestep, open code and
checkpoints, and it also takes *t*. Same structural limitation, better
flow. Worth having as the second rung. *Licence unverified — check
before it goes in.*

### 4.3 ToonComposer — the candidate that should lead

`TencentARC/ToonComposer`, ICLR 2026, *Streamlining Cartoon Production
with Generative Post-Keyframing*. Four reasons it fits this project
better than anything else on the list:

**It has a slot for the timing chart.** Its sparse sketch injection
takes *"one or more keyframe sketches at selected frames"* — sketches
placed at chosen temporal positions, with optional region masks. Frame
indices are exactly what a timing chart specifies. No other candidate
accepts the specification at all; this one accepts it as a native
input. That alone moves it past the acceptance §3 objection that
disqualifies Wan.

**It is cartoon-adapted rather than cartoon-prompted.** A spatial
low-rank adapter tailors the video foundation model to the cartoon
domain, which is the difference between a model that knows line art
and a model being asked nicely about it.

**The licence is the cleanest on the list.** MIT for ToonComposer's own
code *and* weights, over an Apache-2.0 Wan 2.1 base. For a project with
a standing licensing rule, that is worth a great deal — compare §3.3
and §4.4.

**It covers the stage after this one too.** It unifies inbetweening
*and* colourisation in one post-keyframing pass, which is the
governing document's "rough sketch to fully extrapolated and coloured"
story. One integration, two user stories.

Two honest costs:

* **No ComfyUI support exists.** The upstream repo ships a Gradio app.
  Building those nodes *is* the plugin work — which is the right answer
  to "what should this suite be", but it should be budgeted as
  integration rather than installation.
* **It is the heaviest thing here.** Upstream reports *"Generating a
  480p video with 61 frames requires ~57GB of VRAM."* See §7 — the
  shape of this project makes that much less frightening than it
  reads.

### 4.4 ToonCrafter — the obvious one, and why it slipped

ToonCrafter (SIGGRAPH Asia 2024) is cartoon-specific, has working
ComfyUI nodes today, and runs comfortably in 24 GB at 512×320. It is
the fastest route to a moving picture.

But: 2 frames in, ~16 out, **pacing fixed by the model** — so it hits
the same acceptance §3 wall as Wan. And its code being Apache-2.0 does
not settle the weights, whose lineage runs through DynamiCrafter to
Stable Video Diffusion and the Stability community licence.
**Needs verification before use; do not assume the code licence covers
the checkpoint.**

Worth having as a third baseline. Not worth building the suite around,
now that ToonComposer exists.

### 4.5 Ranking

| rank | model | takes timing? | cartoon-native? | licence | role |
|---|---|---|---|---|---|
| 1 | **ToonComposer** | **yes — sketches at chosen frames** | yes (adapted Wan 2.1) | **MIT weights / Apache-2.0 base** | the engine |
| 2 | **GIMM-VFI** | yes (arbitrary *t*) | no | unverified | deterministic baseline, upper rung |
| 3 | **FrameFusion** | yes (arbitrary *t*) | no | unverified | deterministic baseline, floor; harness calibration |
| 4 | **Wan 2.2 / 2.1 FLF2V** | **no** | no | Apache-2.0 | base weights; generative baseline |
| 5 | **ToonCrafter** | **no** | yes | code Apache-2.0, **weights unclear** | third baseline |

Also worth a look later, not now: **AniDoc** (sketch colourisation with
line propagation) and **LVCD** for the colour stage; **MangaNinja** for
reference-guided line work.

---

## 5. Licence audit

Collected because the project's rule is to ask before licensing
anything new, and three of these would have failed quietly.

| artefact | code | weights | verdict |
|---|---|---|---|
| Wan 2.1 / 2.2 | Apache-2.0 | Apache-2.0 | **clean** |
| ToonComposer | MIT | MIT | **clean** |
| Anime2Sketch-derived preprocessors | MIT | MIT | **clean** |
| `acme/*` legibility cleanup | GPLv3 (ours) | n/a | **clean** |
| SD1.5 LineArt ControlNets | Apache-2.0 | **CreativeML OpenRAIL-M** | **not FOSS — use restrictions, decide first** |
| `sketch_simplification` | free non-commercial | **CC non-commercial** | **blocker** |
| ToonCrafter | Apache-2.0 | **unclear (DynamiCrafter → SVD)** | **verify before use** |
| GIMM-VFI, FrameFusion | unverified | unverified | **verify before use** |

The pattern is worth naming: **the permissive pieces are the ones that
were released as products of industrial labs with legal review (Alibaba,
Tencent ARC); the encumbered ones are academic releases.** The
intuition that research code is freer than corporate code is backwards
here.

---

## 6. The plugin suite

Four packs, siblings of the existing `comfyui_acme`, same conventions:
ComfyUI V3 node API (`io.ComfyNode`, `io.Schema`, `comfy_entrypoint`),
`storymator/<pack>` categories, PEP 484/526 annotations, a `foo_test.py`
beside every `foo.py`.

```
comfyui/
  comfyui_acme/      exists — capture, lens, registration
  comfyui_ink/       legibility cleanup + chart reading
  comfyui_tween/     the generator interface, backend-agnostic
  comfyui_harness/   the acceptance §2 rejection harness
```

### 6.1 Types

| type | carries |
|---|---|
| `ACME_CALIBRATION` | exists |
| `DRAWING_PAIR` | two registered drawings, their residuals, their frame numbers |
| `TIMING_CHART` | the fractions read off the page, plus provenance (read / asserted / defaulted) |
| `TWEEN_SEQUENCE` | candidate frames, each tagged with the fraction it *claims* to sit at |
| `HARNESS_REPORT` | per-principle measurements and the reject/accept with reasons |

### 6.2 `comfyui_ink`

`InkFlattenPaper` · `InkDeshadow` · `InkBinarise` · `InkThin` ·
`InkOnionSkin` · `InkReadTimingChart`

`InkReadTimingChart` is the one that is easy to leave out and must not
be. Acceptance §5:

> **The capture pipeline must read the timing chart.** […] If the chart
> is the specification — and §3 says it is — then capturing the chart
> *is* capturing the specification.

Upper right corner, horizontal marks between two bars, output a
`TIMING_CHART`. Judged against the animator's own reading of the same
page.

No `InkSimplify` node yet, per §3.2 and §3.3: there is no licensable
model to put behind it, and it is not on the critical path.

### 6.3 `comfyui_tween`, and the one design decision that matters

`TweenPair` · `TweenGenerate` · `TweenResampleToChart` ·
`TweenContactSheet`

**`TIMING_CHART` is a required input on `TweenGenerate`.** Not
optional, not defaulted. The chart is the specification, so a node that
produces drawings without one is producing drawings to no
specification.

Most backends cannot honour it. That is the interesting part, and the
answer is **not** to relax the input — it is to make the deficiency
measurable:

```
            ┌──────────────────────────────────────────┐
            │ backend honours the chart natively       │
  chart ───►│  ToonComposer, FrameFusion, GIMM-VFI     │───► TWEEN_SEQUENCE
            └──────────────────────────────────────────┘      (fractions as specified)

            ┌──────────────────┐   ┌─────────────────────────┐
            │ backend supplies │   │ TweenResampleToChart    │
  chart ───►│ its own pacing   │──►│ resample N uniform      │───► TWEEN_SEQUENCE
            │  Wan, ToonCrafter│   │ frames onto the chart,  │     + measured
            └──────────────────┘   │ EMIT THE SPACING ERROR  │       spacing error
                                   └─────────────────────────┘
```

`TweenResampleToChart` exists to produce a number, not to paper over a
gap. It is how acceptance §6's calibration gets built into the graph
rather than done once by hand:

> *"the generative baseline reproduces the specified spacing to ±0.18,
> and opens all joints simultaneously in 9 of 10 cases"* — is worth
> considerably more than the same claim asserted.

Every run of every backend then reports its own spacing fidelity as a
side effect of running. That is the cheapest possible way to keep the
instrument honest.

### 6.4 `comfyui_harness`

`HarnessArcDeviation` · `HarnessSpacingError` · `HarnessJointOnset` ·
`HarnessReport` · `HarnessReject`

Straight out of acceptance §2 — arc deviation and interior angle,
spacing fraction to two decimals, joint onset ordering as a set of
inequalities. `HarnessJointOnset` is the sharp one and the one to build
first, because every generative approach fails it in the same legible
way.

**The harness is the part of this suite with no substitute anywhere.**
Four models can generate candidates; nothing but this can say whether a
candidate is usable, in this studio's own terms.

---

## 7. Does it fit in 24 GB?

| model | inference footprint | fits 24 GB? |
|---|---|---|
| FrameFusion | ~37 MB, CPU-capable | trivially |
| GIMM-VFI | a few GB | yes |
| ToonCrafter 512×320 | ~10–12 GB | yes |
| Wan 14B, fp8 | ~16–18 GB weights + block swap | yes |
| ToonComposer 480p, 61 frames | **~57 GB naive** | **not as published** |
| Wan 14B LoRA training | — | **marginal; rent instead** |

The ToonComposer number has an answer, and it is the project's own
shape rather than a trick:

**A pencil test between two keys needs three inbetweens, not
sixty-one.** The governing document's timing vocabulary puts key poses
at *"rarely more than two per second"* — so a key pair spans on the
order of 12 frames, and the chart usually asks for one to five
inbetweens. The 57 GB figure is for a 61-frame clip. Latent cost in a
DiT scales with the temporal extent, so asking for the 9–17 frames a
real key pair actually spans cuts the activation budget by roughly the
same factor, before any of the ordinary tricks.

Then: **fp8** (native on Blackwell), **block swap** against the 98 GB
of host RAM, and sequential offload of the text encoder and VAE. 98 GB
of host RAM against 24 GB of VRAM is a good ratio for exactly this —
block swap is bandwidth-bound, and it is the one place the laptop
part's 896 GB/s costs you relative to the desktop's 1,792.

**Expect it to fit, and expect it to be slow.** Minutes per key pair,
not seconds. For a diagnostic pencil test produced at a drawing desk
while the artist goes on drawing, minutes is survivable. Confirm it
early, though, because "fits but takes six minutes" and "fits and takes
forty seconds" are different products.

**Training is the real hardware question.** A cartoon-domain LoRA on a
14B base at 24 GB and 896 GB/s is marginal at best. The sane split is
**rent for training, run locally for inference** — and the project
already has `comfy-build` and `comfy-deploy` for exactly that.

---

## 8. What to build first

Unchanged in shape from acceptance §5, with the model work sequenced
behind it:

1. **Finish legibility cleanup and chart reading** (`comfyui_ink`).
   Judged on registration residual and chart-reading accuracy against
   the animator's own reading. No models, no licences, known cost.
2. **`HarnessJointOnset` plus `HarnessSpacingError`.** Before any
   generator. They are what makes everything after step 3 mean
   something.
3. **FrameFusion as the calibration baseline.** Hours of work. It will
   be timing-exact and will fail joint onset on every chain. If the
   harness does not catch that, fix the harness.
4. **ToonComposer integration** — the real plugin work, and the only
   candidate that accepts the specification.
5. **Wan FLF2V and ToonCrafter as generative baselines**, through
   `TweenResampleToChart`, so their pacing error is a number in the
   report.

**What not to do first:** the inking stage. It is not on the pencil-test
path (§3.2), its best open model is unlicensable (§3.3), and the
ControlNet route would regenerate the artist's line (§3.1). It belongs
with the colour stage, which ToonComposer may well absorb anyway.

---

## 9. Questions this raises

1. **Desktop or laptop 5090?** §2. Changes the training answer, not the
   model choice.
2. **Does the chart ever ask for non-integer frame positions?** The
   sparse-sketch interface takes frame *indices*. If a chart can
   specify a fraction that falls between frames, the mapping needs a
   rule.
3. **The licence decisions in §5**, particularly whether OpenRAIL-M is
   acceptable anywhere in this pipeline. Standing rule says ask.
4. **Still open from acceptance §7: is there paired data?** Keys with
   the inbetweens an assistant actually drew. It is the gate on
   fine-tuning any of this, and nothing substitutes for it.

---

## Sources

* ToonComposer — <https://github.com/TencentARC/ToonComposer>,
  <https://arxiv.org/abs/2508.10881>,
  <https://huggingface.co/TencentARC/ToonComposer>
* Wan 2.1 FLF2V in ComfyUI — <https://docs.comfy.org/tutorials/video/wan/wan-flf>
* FrameFusion — <https://github.com/BurguerJohn/FrameFusion-Model>
* GIMM-VFI — <https://github.com/GSeanCDAT/GIMM-VFI>
* ToonCrafter — <https://github.com/Doubiiu/ToonCrafter>
* sketch simplification — <https://github.com/bobbens/sketch_simplification>
* VFI survey — <https://github.com/CMLab-Korea/Awesome-Video-Frame-Interpolation>
