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

There was a licence objection too, and it is **withdrawn**. The SD1.5
lineage carries **CreativeML OpenRAIL-M**, and Monte settled on
2026-10-13 that OpenRAIL-M is acceptable here: the field-of-use
restrictions are neither a commercial nor an ethical concern for this
project. See [LICENSES.md](../../LICENSES.md).

**That leaves the architectural objection standing alone, which is the
one that always mattered.** The ControlNets are now ours to use; using
them to clean a drawing would still regenerate the artist's line. The
decision changes where they belong, not whether the round trip is
sound — and where they belong is the colour stage, which §8 already
said.

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
the same acceptance §3 wall as Wan.

**On the licence, traced 2026-10-13, because the first pass of this
note got it wrong.** It said the weights descended from Stable Video
Diffusion and the Stability community licence. They do not. The actual
chain is:

| link | what it says |
|---|---|
| **ToonCrafter** | HF card tagged Apache-2.0: *"Feel free to use it under the Apache-2.0 license."* Finetuned from DynamiCrafter-interpolation (512×320). |
| **DynamiCrafter** | Apache-2.0, copyright THL A29 Limited (Tencent). Finetuned from VideoCrafter1. |
| **VideoCrafter1** | *"We develop this repository for RESEARCH purposes, so it can only be used for personal/research/non-commercial purposes."* Codebase builds on Stable Diffusion. |

So the question at the root is **not** OpenRAIL and is therefore *not*
answered by the 2026-10-13 decision. It is a **non-commercial research
restriction**, which is the same class of problem as §3.3 and a
different class from the ControlNets.

Two things make it arguable rather than settled: the restriction sits
in a README disclaimer rather than in a LICENSE file, and ToonCrafter
affirmatively declares Apache-2.0 two links downstream. Whether a
disclaimer upstream survives two rounds of finetuning into a contrary
declaration is a real question and not one to answer by reading
README files.

**Still open, and still a reason not to build on it.** It is a third
baseline whose pacing we cannot control anyway, so the cost of leaving
the question unanswered is low.

Worth having as a third baseline. Not worth building the suite around,
now that ToonComposer exists.

### 4.5 Ranking

| rank | model | takes timing? | cartoon-native? | licence | role |
|---|---|---|---|---|---|
| 1 | **ToonComposer** | **yes — sketches at chosen frames** | yes (adapted Wan 2.1) | **MIT weights / Apache-2.0 base** | the engine |
| 2 | **GIMM-VFI** | yes (arbitrary *t*) | no | unverified | deterministic baseline, upper rung |
| 3 | **FrameFusion** | yes (arbitrary *t*) | no | unverified | deterministic baseline, floor; harness calibration |
| 4 | **Wan 2.2 / 2.1 FLF2V** | **no** | no | Apache-2.0 | base weights; generative baseline |
| 5 | **ToonCrafter** | **no** | yes | declares Apache-2.0 over a **non-commercial research** root (§4.4) | third baseline |

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
| SD1.5 LineArt ControlNets | Apache-2.0 | CreativeML OpenRAIL-M | **accepted 2026-10-13** — field-of-use restrictions are not a concern here |
| `sketch_simplification` | free non-commercial | **CC non-commercial** | **blocker** — a different licence from OpenRAIL; the 2026-10-13 decision does not reach it |
| ToonCrafter | Apache-2.0 | declares Apache-2.0; root is VideoCrafter1, **non-commercial research** | **open** — see §4.4; not an OpenRAIL question |
| GIMM-VFI, FrameFusion | unverified | unverified | **verify before use** |

Two patterns worth naming.

**The permissive pieces are the industrial releases** (Alibaba,
Tencent ARC), the encumbered ones academic. The intuition that research
code is freer than corporate code is backwards here.

**And a licence declaration is not a licence audit.** ToonCrafter says
Apache-2.0 and means it; the restriction is two links upstream, where
nobody looking at the model card would see it. The first pass of this
note named the wrong upstream, which is the same mistake in the other
direction. **Trace the chain to a root that states its own terms, and
record the chain rather than the conclusion** — that is what §4.4 now
does, so the next reader can check it instead of trusting it.

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
3. ~~**Whether OpenRAIL-M is acceptable anywhere in this pipeline.**~~
   **Answered 2026-10-13: yes**, the field-of-use restrictions are
   neither a commercial nor an ethical concern for this project. This
   clears the SD-lineage ControlNets and preprocessors, which matters
   most for the colour stage. It does **not** clear
   `sketch_simplification` (CC non-commercial, §3.3) or ToonCrafter
   (non-commercial research root, §4.4) — both are a different class of
   restriction. Those two remain open, and neither is on the critical
   path.
4. **Still open from acceptance §7: is there paired data?** Keys with
   the inbetweens an assistant actually drew. It is the gate on
   fine-tuning any of this, and nothing substitutes for it.

---

## 10. A correction: the arc check is degenerate for a single inbetween

Found 2026-10-13 while working out what the first tests assert.
Acceptance §2's Arcs row says:

> Track a feature […] across key → inbetween → key. […] Fit an arc
> through the neighbouring keys; measure the inbetween's deviation from
> it, and the interior angle at the inbetween.

**Three distinct non-collinear points determine exactly one circle.** So
the deviation of inbetween *I* from the circle through (key *A*, *I*,
key *B*) is **identically zero for every *I***, including deliberately
awful ones. Measured over 20,000 random inbetweens scattered ±20 units
around a 10-unit key separation, the worst deviation found was
**3.6 × 10⁻¹²** — floating-point noise.

That sentence bundles two checks, and only one of them survives on a
single inbetween:

| check | needs | measured behaviour |
|---|---|---|
| **interior angle at the inbetween** | 3 points — **one inbetween is enough** | discriminates cleanly: **180.0°** dead centre (the straight line the principle forbids), 146.6° gentle arc, 58.1° sharp corner, 43.2° off-path spike |
| **deviation from an arc** | the arc determined *independently* of the candidate: **≥3 keys**, or ≥2 inbetweens, or the artist's own drawn guide | with three keys: **0.000** for a drawing on the key arc, **1.960** for one taking the chord shortcut |

Consequences for the plugin suite:

* `HarnessArcDeviation` (§6.4) **splits into two nodes** with different
  fixture requirements — `HarnessInteriorAngle` and
  `HarnessArcDeviation`.
* **Build the interior angle first.** It works on the narrowest case —
  two keys and one inbetween — which acceptance §7 Q4 suggests is the
  common one, and it catches the straight-line failure the manuscript
  names in so many words: *"no part of the move would be on a purely
  straight line"*.
* `HarnessArcDeviation` needs a fixture with **three keys or two
  inbetweens**, so whether it is in the first slice depends on the
  answer to §11.1.

**This sharpens the harness rather than weakening it.** As written, the
deviation check would have returned zero on every candidate and been
believed — a passing measurement that measured nothing. Worth catching
before it was a number in a funding document.

Verification script kept out of the repository: it is six lines of
circle-fitting and reproduces from the table above. If it should live
in `acme/` as a test instead, say so.

---

## 11. Decisions needed before the first test

Per the project's TDD rule the tests get written and confirmed before
any implementation, so these are the answers the test bodies depend on.
Split by whether they actually block.

### 11.1 Blocking — a test cannot be written without these

**1. Fixtures — mostly answered by the ManRunCycle corpus, with one gap
left and one correction.** The corpus is read in detail in §12. What it
settles:

| test | needs | status |
|---|---|---|
| rough → clean cleanup | aligned rough/clean pairs | **12 pairs, already in register** (§12) |
| `HarnessArcDeviation` | three keys, or two inbetweens (§10) | **real material now** — a 12-drawing sequence on one peg bar |
| `HarnessSpacingError` | a sequence with known spacing | **partly** — drawing numbers, including 1.5 and 6.5, but no chart |
| `HarnessJointOnset` | a joint chain, plus a known-bad variant | **real half**; the bad half must still be authored |
| `InkReadTimingChart` | a page with a real chart, and Daniel's reading | **still nothing** |

So the split still stands, but it has moved:

* **The harness still wants synthetic for the *failing* half, and
  should.** You cannot photograph a drawing that opens three joints at
  exactly the same instant; you author one and assert rejection.
  Acceptance §6 wants *"deliberately bad candidates"* and those have to
  be constructed. `acme/synth.py` is the precedent. What the corpus adds
  is the *passing* half — real drawings an assistant actually made, so
  the harness can be shown not to reject good work.
* **The chart reader is still blocked and is now the only thing that
  is.** No sheet in the corpus carries a chart. The ask is unchanged and
  small: **one photographed page with a chart on it, plus Daniel's
  reading of it.** Worth making this week, because it is the only
  input the §8 build order cannot start without.

**The correction: use `12F/`, not `10F/`.** The 10F crop removes the
outer 1/12 of each dimension, which is exactly where the peg holes are.
Measured: the bottom band of a 10F frame is blank paper. No pegs means
no registration landmarks, which makes every `comfyui_acme` node
inapplicable to it. **10F is a viewing crop, not a working set.**

**2. What is in a `TIMING_CHART`?** This is the specification, so its
shape propagates into every test downstream. The sub-questions:

* **Frame numbers, fractions, or both?** I think both and they are not
  redundant: the chart's *marks* give fractions along the path, its
  *numbers* give frame positions, and the mapping between them is the
  whole content. ToonComposer's interface wants indices; acceptance §2's
  *"must land at 0.5 of the way along the path"* wants fractions.
* **Is the fraction read off the chart's geometry, or derived from the
  frame numbers?** It must be **read**. Deriving it is a formula, and
  the manuscript calls formula *"a nail in the coffin"*. This is the
  single most consequential line in the data model and it means the
  reader must locate mark positions sub-pixel, not just count marks.
* **How is a hold represented?** Two marks at the same position with
  different frame numbers — so the model must permit duplicate
  fractions, and `HarnessSpacingError` must not divide by a zero gap.
* **Does `provenance` allow `defaulted` at all?** §6.1 proposed
  `read / asserted / defaulted`. Given acceptance §3's rule, a defaulted
  chart is a rule violation. I would make it representable but
  **poisoning** — it appears in the `HARNESS_REPORT` and nothing can
  launder it. The alternative is a hard error. Your call.

**3. The pack layout, and a name collision worth fixing now.**
§6 proposed four packs. Two sub-decisions:

* **`comfyui_acme` or a new pack for cleanup?** Cleanup is downstream of
  registration and uses the same `ACME_CALIBRATION` and the same von
  Kries white balance, which argues for keeping it in `comfyui_acme`.
  That gives **three packs, not four**: `comfyui_acme` (capture,
  register, clean), `comfyui_tween`, `comfyui_harness`.
* **Do not call it `ink`.** `acme/ink.py` already means *the marker ink
  on the peg crowns*, documented at length in
  [ink-landmarks.md](ink-landmarks.md). A drawing-cleanup module also
  called ink would make every future reference ambiguous. I recommend
  **`acme/clean.py`** with nodes `AcmeClean*` — which is also the
  governing document's own word (*"cleanup, paint and compositing"*),
  and it leaves the name "ink" free for the actual inking stage in §3.2,
  which is the thing we are deliberately not building yet.

### 11.2 Proceeding on these defaults unless you say otherwise

Stated so they are visible rather than buried in a test body. None of
them need an answer to start.

**4. The joint decomposition is an input, not an inference.**
`HarnessJointOnset` takes the chain as a parameter and the first
fixtures hand-author it. Deriving it from the drawing is the research
problem acceptance §4 discusses; the harness does not need to wait for
it. Daniel's tag-vocabulary floor (acceptance §7 Q3) can land later
without changing the node signature.

**5. Thresholds live in configuration; tests assert measurements.** What
spacing error constitutes a reject is a studio judgment, not an
engineering one — acceptance §2 gives 0.5-read-as-0.3 as a clear
failure, but says nothing about 0.05. So tests assert *measured values*
on known fixtures, and the reject thresholds sit in a config file where
they are Daniel's to tune, under the project's CLI/env/config precedence
rule. This unblocks the tests without needing the numbers.

**6. Harness measurements are in millimetres on the page.** Registration
already produces a common coordinate system and the codebase works in mm
(`default_residual_mm`). Millimetres make measurements comparable across
captures at different camera distances; pixels do not.

**7. The tracked feature starts as the ink centroid.** Acceptance §2
wants *"centre of mass in a wide shot, hand or head in a medium"*. The
first is the first moment of the binarised drawing — deterministic and
testable today. "Hand or head" needs the tag vocabulary, so it waits
with decision 4. Means the arc checks are honest for wide shots and
approximate for medium ones at the start, which should be recorded in
the report rather than hidden.

### 11.3 Can wait

**8. Desktop or laptop 5090** (§2). Blocks model work, not tests.

**9. Non-integer chart positions** (§9 Q2). Needs a real chart to
know whether it ever happens.

---

## 12. The ManRunCycle corpus, read 2026-10-13

`~/lab/storymator/training_data/ManRunCycle_Rough_CleanUp_2001_WWC`.
Opened and measured rather than taken on the folder name, because what
is in it changes §11.

### 12.1 Shape

| entry | what |
|---|---|
| `12F/` | 24 PNGs, 8.8 MB each, **327 MB** — the full sheet, pegs included |
| `10F/` | the same 24, rotated and cropped, 2734×1921, **201 MB** |
| `12Fto10F` | **a bash script, not a directory**: `magick $a -rotate 90 -crop 2734x1921+273+192` |

The crop keeps exactly the central **10/12** of each dimension —
2734/3281 = 1921/2305 = 0.8333 — which is what establishes that
**12F and 10F are field sizes, not frame counts.**

**An EXIF trap.** The files carry `orientation=6`, so `identify` reports
2305×3281 (portrait) while every viewer shows 3281×2305 (landscape).
A loader that does not call `exif_transpose` silently works on a
sideways page. That deserves its own test.

### 12.2 What the 24 sheets are

Two passes of one run cycle:

* **files 1–12 — graphite cleanups**, numbered 1 … 12.
* **files 13–24 — blue-pencil roughs**, numbered (in file order)
  3, 1, **1.5**, 2, 4, 5, 6, **6.5**, 7, 8, 9, 10.

The roughs run 1 … 10 with **1.5 and 6.5** inserted. Ten drawings plus
two inbetweens is twelve, and the cleanups are 1 … 12 — so the cleanup
pass **renumbered**. Confirmed by overlay rather than by arithmetic:
rough 1 ↔ clean 1, rough 1.5 ↔ clean 2, rough 2 ↔ clean 3,
rough 3 ↔ clean 4, same poses in the same place on the page.

**So the fractional numbers are the artist's own inbetweens**, and the
corpus is a partial answer to acceptance §7 Q1 — paired keys and the
inbetweens an assistant actually drew — without the chart that would
have made it a complete one.

**The ✗ marks.** A small ✗ sits under 1, 6 and 10, and under no other
drawing — not under 1.5 or 6.5. In a ten-drawing run, 1 and 6 are half
a cycle apart, which is where the two contacts fall, so the obvious
reading is that ✗ marks a key or extreme. **That is a guess and should
be put to Daniel, not assumed.** If it is right, the corpus carries its
own key/inbetween labelling and `HarnessJointOnset` has its chain
endpoints for free.

### 12.3 Measurements

* **Peg geometry**: two oblong slots flanking one round hole, the round
  one carrying a **white reinforcement patch**. Detection must not
  assume bare paper around a hole — this one is repaired.
* **Scale**: adjacent peg features sit 800.1 and 800.7 px apart. Against
  ACME's 4-inch spacing that is **200 px/inch**, consistent across both
  passes.
* **Capture repeatability**: the same three features land within
  **3.5 px** between the rough capture and the clean capture, as a
  consistent translation.
* **Registration**: overlaying clean 1 on rough 1 on the raw pixel grid
  puts the lines on top of each other. **The cleanup was traced in
  register, on the same pegs.** The visible differences are editorial —
  the coat tail, the cane, a shoulder correction — which is the signal
  an inking model would have to learn.

**A number from this session not to reuse.** A first pass compared the
rough's blue-ink centroid with the clean's grey-ink centroid and got an
offset of (+148, +311) px. That is confounded: different masks, very
different line widths, and the rough carries construction marks and two
faint guide lines at lower left that the clean does not. The overlay is
the honest instrument and it says registered. Recorded because the
confounded number is the kind that gets quoted later.

### 12.4 What it does and does not buy

**Buys:** twelve aligned rough→clean pairs, so the inking stage has real
supervision and real fixtures; a twelve-drawing sequence in one
coordinate system, so §10's arc-deviation check is testable on real
drawings and not only synthetic ones; and a blue-rough / graphite-clean
split that is exactly the chroma separation `acme/ink.py` already
performs and that
[acme-registration-plugin.md](acme-registration-plugin.md) §9 argued for
— *separate the pencils, don't threshold them*.

**Does not buy:** a timing chart, on any sheet. It is also one scene,
one character, one action, and a **cycle** rather than a key pair with a
chart. And the roughs are **tie-downs, not construction-line roughs** —
considerably cleaner than the general rough-cleanup case, so a model
that does well here has not yet been tested on the hard one.

### 12.5 Before any of it is committed

**Provenance.** This is Wiki Wiki Cartoons production artwork from 2001.
It is not ours, and this repository publishes under GPL-3.0-or-later
with CC-BY-SA-4.0 documentation. **Committing it as test fixtures
publishes it.** The standing rule is to ask, and this wants Daniel's
explicit permission with the terms written down the way the CalibrX
reply is kept in `docs/licensing/` — not an assumption from the fact
that he supplied the files.

**Size.** 327 MB for `12F/` against a repository already carrying 948 MB
in `data/` and a 672 MB `.git`, with no LFS configured. Three options,
in the order I would consider them: keep the corpus out of tree and
commit a `manifest.json` describing it, in the style
`data/captures/*/manifest.json` already uses; commit a small derived
subset, say two pairs, at reduced resolution; or configure LFS. The
first costs nothing and keeps the tests pointed at a path that can be
checked for presence and skipped, which `acme/ink_test.py` already does
with `skipif`.

---

## Sources

* ToonComposer — <https://github.com/TencentARC/ToonComposer>,
  <https://arxiv.org/abs/2508.10881>,
  <https://huggingface.co/TencentARC/ToonComposer>
* Wan 2.1 FLF2V in ComfyUI — <https://docs.comfy.org/tutorials/video/wan/wan-flf>
* FrameFusion — <https://github.com/BurguerJohn/FrameFusion-Model>
* GIMM-VFI — <https://github.com/GSeanCDAT/GIMM-VFI>
* ToonCrafter — <https://github.com/Doubiiu/ToonCrafter>,
  <https://huggingface.co/Doubiiu/ToonCrafter> (licence tag and parent model)
* ToonCrafter's weight lineage — <https://github.com/Doubiiu/DynamiCrafter>,
  <https://github.com/AILab-CVC/VideoCrafter> (the non-commercial research root)
* sketch simplification — <https://github.com/bobbens/sketch_simplification>
* VFI survey — <https://github.com/CMLab-Korea/Awesome-Video-Frame-Interpolation>
* ManRunCycle corpus (§12) — `~/lab/storymator/training_data/ManRunCycle_Rough_CleanUp_2001_WWC`,
  supplied by Dr. Daniel Boulos; Wiki Wiki Cartoons, 2001
