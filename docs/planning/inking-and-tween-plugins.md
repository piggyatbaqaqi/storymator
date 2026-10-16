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

> **Wrong, and corrected 2026-10-16 by the spike — see §7a sixth pass
> and the specification in §7b.** Colourisation is not a second user
> story this model throws in; **it is the mechanism**. A colour
> keyframe is a *required input* and painted video is the only output.
> There is no line-in-line-out mode, so ToonComposer cannot produce a
> pencil test, which is the first milestone. The rest of this section
> stands — the sketch-injection interface is real and still unique —
> but it describes the right tool for the **colour stage**, not this
> one.

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

> **Re-read after the spike, 2026-10-16.** This table ranks candidates
> for *inbetweening* and puts ToonComposer first. It requires a colour
> keyframe and emits painted video (§7b), so for the **pencil test** it
> does not qualify at all, and the row below should be read as ranking
> it for the **colour stage**. No candidate here both accepts a chart
> and works in line only; §7b.5 states that hole plainly.

| rank | model | takes timing? | cartoon-native? | licence | role |
|---|---|---|---|---|---|
| 1 | **ToonComposer** | **yes — sketches at chosen frames** | yes (adapted Wan 2.1) | **MIT weights / Apache-2.0 base** | the engine **for the colour stage** |
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

### 7a. What the spike has measured so far — 2026-10-16

Partial, and written down as it arrives rather than held back for one
tidy amendment. The run has not yet produced a frame, so peak VRAM and
seconds per frame are still unknown. What follows is what stopped being
a guess.

**Three numbers above were wrong.**

| §7 said | measured | why it matters |
|---|---|---|
| 98 GB host RAM | **91 GiB total, ~58 available** | the block-swap argument rests on this ratio |
| ToonComposer needs ~35 GB of weights | **77 GB** for the subset it opens | disk is fine (2.7 T free); host RAM is the question |
| *(not considered)* | the Wan DiT ships **fp32** | 7 shards at ~9 GB; the bf16 assumption was never stated, only assumed |

The DiT being fp32 is the one that could bite. `WanVideoPipeline` is
constructed `torch_dtype=torch.bfloat16`, so the cast *should* happen on
load and leave ~32 GB resident rather than ~63 GB — but that is again an
inference from reading, and the spike prints the actual dtypes and peak
RSS so it stops being one.

**Two findings in the project's favour.**

**Block swap is already there.** `WanVideoPipeline.enable_vram_management(
num_persistent_param_in_dit=N)` keeps N DiT parameters resident, streams
the overflow from CPU, and holds the text encoder on CPU entirely. §7
assumed this would have to be arranged; it is a single call. `N` is the
knob to sweep.

> **Correction, same day.** An earlier version of this paragraph said
> `None` streams everything. It is the exact opposite. diffsynth's
> `enable_vram_management_recursively` reads
> `if max_num_param is not None and total + num_param > max_num_param`,
> so **`None` means no cap and the overflow config is never consulted**
> — the whole 14B DiT stays resident. Passing `None` filled the card to
> 22.80 GiB and died trying to allocate another 136 MiB. **`0` is what
> streams everything**; larger values trade host-to-device traffic for
> VRAM.

**ToonComposer's own checkpoint is 170 MB**, against Wan's 77 GB. The
adapter is a spatial low-rank adapter and sketch injection, nothing
more. That matters twice over: a cartoon-domain adapter of our own is a
far smaller training problem than the "14B LoRA" framing above implies,
and the thing worth contributing upstream is correspondingly small.

**Two practical notes.** `flash_attn` is absent, so attention takes the
slower path — any timing measured here is a ceiling, not the best this
hardware can do. And ToonComposer's pinned `torch==2.8.0` must not be
installed into the `storymator` environment: it would downgrade torch,
numpy and Pillow, and the working build here is **2.14.1+cu130**, whose
arch list includes `sm_120`. The spike runs in a throwaway
`tooncomposer-spike` environment for that reason.

#### Second pass — the model loads, and two ways to die

**The fp32 worry is dead.** The cast does happen on load: dtypes come
back `dit=bfloat16 t5=bfloat16 vae=bfloat16`, and **host RSS after build
is 36.7 GiB**, not the ~63 GB an fp32 DiT would have cost. Build takes
**38.5 s** with a warm page cache. So §7's host-RAM argument survives,
with less headroom than it claimed but enough.

**Two distinct out-of-memory failures, and they are not the same
problem.**

*CUDA OOM*, from passing `None` — see the correction above. The card
filled to 22.80 GiB of 23.42 and died on a 136 MiB onload. Self-
inflicted, and the fix is a finite cap.

*Host OOM*, from the kernel: `Killed process (python) total-vm 70.7 GB,
anon-rss 35.2 GB`. Note what else was in that log — `ZoomWebviewHost`
among the candidates. **The 91 GiB is shared with a desktop**, so the
budget is not 91 minus the model but 91 minus the model minus whatever
the operator happens to be running. A video call during a render is
enough to change the answer. Worth knowing before this lands on a
drawing desk that is also somebody's computer.

**One alarming-looking message that is benign.** Loading prints
`WanModel: 404 zero-filled, 0 not in adapter ckpt`. Those 404 are the
DeRA and sequence-condition parameters the config switches on
(`use_dera`, `dera_rank: 144`, `sequence_cond_mode: sparse`) — modules
that do not exist in the base Wan checkpoint, so they are zero-filled
and then populated from ToonComposer's own. The `0 not in adapter ckpt`
is the half that matters: nothing was left unfilled.

#### Third pass — ToonComposer and block swap do not fit together

The finding with the longest reach so far, and it is not about VRAM at
all.

With a finite cap the card no longer overflows, and the run gets into
sampling and dies there:

```
model/dit.py:761, in forward
    sequence_cond = [u.flatten(2).transpose(1, 2) + self.sequence_cond_identifier ...]
RuntimeError: Expected all tensors to be on the same device,
              but found at least two devices, cuda:0 and cpu!
```

**diffsynth's vram management replaces module *types*.** Its map covers
`torch.nn.Linear`, `Conv3d`, `LayerNorm`, `WanLayerNorm`, `WanRMSNorm` —
it walks the tree swapping those for `AutoWrapped*` versions that know
how to onload and offload themselves. **A bare `nn.Parameter` hanging
directly off a module is invisible to that mechanism** and simply stays
where it was, on the CPU.

ToonComposer adds exactly such a parameter. `model/dit.py:662`:

```python
self.sequence_cond_identifier = nn.Parameter(torch.randn(1, 1, dim) / dim**0.5)
```

So **the sketch-injection path — the one feature that made ToonComposer
the lead candidate in §4.3 — is the part that breaks under block
swap.** Upstream never meets this, because `app.py` calls
`model.to(device)` and the README says to bring 57 GB.

**The repair is cheap and the lesson is not.** Walking the DiT after
`enable_vram_management` and pinning every parameter and buffer on an
unwrapped module costs a few megabytes: `modulation` is `1×6×dim` per
block and the identifier is `1×1×dim`. Trivial next to a 14B model.

But it has to be *known*, and nothing in the documentation of either
project says it. This is the first hard evidence for §4.3's claim that
integration is "the real plugin work" rather than an install: a
ComfyUI node for ToonComposer on consumer hardware must carry this
patch, must keep carrying it across upstream changes, and would fail
with a device-mismatch error a user could not act on if it did not.

**It also sharpens what to contribute upstream.** A pull request making
ToonComposer's own additions survive `enable_vram_management` is small,
self-contained, obviously correct, and useful to everyone without
57 GB — a far better first contribution than a ComfyUI node, and it
would remove the patch this project would otherwise maintain forever.

**Nothing is patched, and that is deliberate.** Both checkouts —
`TencentARC/ToonComposer` and the fork at
`piggyatbaqaqi/ToonComposer` — are clean at `53dc3df`. The workaround
lives in the spike's own throwaway script, which walks the DiT *after*
`enable_vram_management` and pins what diffsynth left behind. It
confirms the diagnosis without committing to a fix.

**The fix is deferred until a run succeeds, and it will be test-first**
(Monte, 2026-10-16). Two reasons that is the right order. A fix written
before a green run would be guessing at whether this is the only such
parameter — the spike's pin reports **330 unwrapped tensors, 3.9 M
parameters**, so `sequence_cond_identifier` is not alone and a
one-line fix aimed at it would be wrong. And the repair belongs in the
fork, as a branch that can become a pull request, not as an untracked
edit to a vendored checkout.

**The test is cheap, which is what makes TDD practical here.** It needs
no 14B model: construct a module holding a `torch.nn.Linear` *and* a
bare `nn.Parameter`, call `enable_vram_management` with
`max_num_param=0`, and assert the bare parameter ends up on the compute
device while the Linear's weight does not. That is the whole defect,
reproduced in a few lines, and it fails today.

**Where the fix belongs is itself a decision**, and worth making
deliberately rather than by whichever file is open:

| candidate | argument |
|---|---|
| ToonComposer overrides `enable_vram_management` and pins its own additions after calling diffsynth's | smallest; ToonComposer's additions are ToonComposer's problem; mergeable without waiting on a diffsynth release |
| ToonComposer re-homes the parameter inside a module type diffsynth already wraps | tidier model code, but changes checkpoint keys, which breaks every published weight |
| diffsynth learns to see bare parameters | arguably the real defect — the mechanism is incomplete, not ToonComposer's use of it — but a wider blast radius and a slower path to merge |

The first is the one to write first. The third may be worth raising
separately, since any model with a bare parameter hits this and the
failure mode is a device-mismatch error far from its cause.

**Housekeeping for whoever writes it:** the fork has only its own
`origin` and no `upstream` remote, so it cannot track TencentARC yet.

#### Fourth pass — it runs, it fits easily, and the output is unusable

The first complete run, and it answers §7's question in a way §7 did
not anticipate.

```
frames 13 | persist 0 | steps 15
build 19.9 s | generate 1264.6 s | 97.3 s/frame | peak VRAM 5.9 GiB
```

**Fits, with room to spare.** §7 asked "does it fit in 24 GB" and
treated that as the risk. Streaming the whole DiT, peak VRAM was
**5.9 GiB of 23.4** — not marginal, not tight, a quarter of the card.
The memory question is settled and it was never the hard one.

**Slow, and slower than §7's own threshold.** §7 said *"'fits but takes
six minutes' and 'fits and takes forty seconds' are different
products."* It is **21 minutes** for thirteen frames. But that figure
is from `persist 0`, which streams every parameter from host RAM for
every step, and 17 GiB of the card was sitting idle. It is a floor on
the hardware, not a measurement of the configuration anyone would ship.

**And the output is unusable.** Frame 0 follows the first key and is
recognisably the character, so the conditioning does reach the model.
It then dissolves: by the middle frame the figure is blobs, by the last
it is colour noise. Frame 0 also carries a regular dot lattice that
looks like a tiling artefact rather than a sampling one.

**A likely cause, and a correction to §7.** ToonComposer's own UI
constrains the frame count:

```python
minimum=17, maximum=max_num_frames, ... label="🎥 Number of Frames"
```

**Seventeen is the floor**, and this run asked for thirteen. §7's
central affordability argument was that *"asking for the 9–17 frames a
real key pair actually spans cuts the activation budget"* — the bottom
of that range is below what the model supports, so the argument has to
be made again at 17 and above. Since memory turned out not to bind,
that costs nothing; but the number in §7 was wrong.

`tiled=True` is the second suspect, carried from `app.py` with tile
sizes that come from the checkpoint config and may not suit this
resolution. The lattice in frame 0 is the kind of artefact tiling
produces.

**What this does to the plan.** The spike has now done its job twice
over: it retired the memory risk, and it replaced it with a different
one. "Does it fit" is answered — yes, easily. "Does it produce a
usable inbetween from pencil drawings on paper" is open, and is a
harder question than VRAM because the failure is not a resource limit
but a domain gap: ToonComposer is trained on anime production art, and
it was handed graphite on textured paper.

#### Fifth pass — seventeen frames, and the bottleneck is not memory

```
frames 17 | persist 6e9 | steps 15
build 20.8 s | generate 1489.3 s | 87.6 s/frame | peak VRAM 15.78 GiB
```

**Residency bought almost nothing, and that is the finding.** Going
from `persist 0` — every parameter streamed from host RAM on every step
— to `persist 6e9`, about 12 GiB kept resident, moved the cost from
**97.3 to 87.6 seconds per frame**. Ten percent.

So **this is compute-bound, not bandwidth-bound**, and §7 had the
mechanism wrong. §7 worried about *"block swap is bandwidth-bound, and
it is the one place the laptop part's 896 GB/s costs you relative to
the desktop's 1,792"*. The bandwidth is nearly free; the arithmetic is
not. Three consequences:

* **More VRAM would not help.** The card was three-quarters idle at
  `persist 0` and filling it changed little.
* **The desktop 5090 would help, for the other reason** — 21,760 CUDA
  cores against 10,496, so roughly half the time. Not the bandwidth.
* **`flash_attn` is absent**, and on a compute-bound workload that is
  no longer a footnote. It is the first thing to try before accepting
  ~25 minutes per key pair.

**The output is still not a drawing.** Seventeen frames is better than
thirteen — the figure persists through the middle and the pose does
shift — but the last four frames collapse into colour noise and
everything carries a pink cast. Against cleanup 2, the artist's own
inbetween:

```
ink pixels  truth 1520  generated 0
IoU 0.000
```

**Zero.** Not a poor drawing — no ink at all at any sane threshold. The
generated middle frame is a washed-out field with a ghost in it.

#### A control this spike should have run first

Four runs in, every one of them varied *our* inputs, and not one
established that this installation produces good output on inputs the
model likes. That is the wrong order and it is worth naming: **a
negative result on unfamiliar data means nothing until the rig is shown
to work on familiar data.** The block-swap patch, the dtype handling,
`tiled=True`, the conditioning layout — any of those could produce
exactly what was seen, and the domain-gap explanation would be an
assumption dressed as a conclusion.

`samples/` ships three complete cases with reference outputs. Their
configuration is already informative:

| | sample 1 | sample 2 | sample 3 |
|---|---|---|---|
| frames | 61 | 61 | 33 |
| colour image at | 0 | 0 | 0 |
| sketches at | 20, 40, 60 | 30, 60 | 30 |

**None of them puts a sketch at frame 0**, where the colour image goes,
and sample 3's only sketch is at frame 30 of 33 — *not* the last frame.
This spike put sketches at frame 0 **and** at the last frame, which is
a layout none of the shipped examples uses. That alone could explain
the ends collapsing.

Sample 3 is running now as the control.

#### Sixth pass — the colour frame is required, and §4.3 missed it

Monte, 2026-10-16, pointing at `samples/ToonComposer-TLDR.jpg`: *"seems
to suggest that we need a color frame as input to the process. Is this
not universally true?"*

**It is universally true, and this is the most consequential finding of
the spike.** The figure is unambiguous — **Color Frame** plus **Sketch
Frame(s) (Any Temporal Position)** in, fully painted video out. The
README agrees in step 2: *"Provide at least one keyframe color image
(usually placed at frame index 0)."* The config allows up to four
(`max_num_cond_images: 4`). It is an input, not an option.

**§4.3 got this wrong by treating colourisation as a bonus.** That
section recommended ToonComposer partly because *"it covers the stage
after this one too… One integration, two user stories."* The
colourisation is not a second user story the model happens to throw in.
**It is the mechanism.** ToonComposer is a *post-keyframing* model:
colour reference plus sketches to painted video. Line in, line out is
not a mode it has.

**Which is a problem for the milestone we are actually on.** The first
deliverable is a **pencil test** — graphite in, graphite out, no colour
anywhere, and acceptance §1 is emphatic that it must be *the artist's
own lines*. There is no colour frame on a drawing desk at that stage
because nobody has painted one yet.

**And it explains the washout, precisely.** This spike handed
ToonComposer a near-white graphite drawing as its colour reference. The
model's job is to paint, and it was given nothing to paint with — so it
produced a pale field with a ghost in it and a pink cast. That is not a
vague "domain gap"; it is the specific consequence of supplying a
colour condition that contains no colour.

**A second number, from the same file.** The checkpoint config carries
`num_frames: 33` — the **length it was trained at**. The UI's
`minimum=17` is a floor on the widget, not on the model's competence.
Both this spike's runs, at 13 and 17, were below the trained length;
the control at 33 is the first run at it.

**What this does to §4.5's ranking.** It does not demote ToonComposer —
it relocates it. For the **colour stage** the governing document
eventually wants (*"rough sketch to fully extrapolated and coloured"*)
it remains the best open candidate, and sparse sketch injection is
still the only interface found with a slot for a timing chart. For the
**pencil test**, it is the wrong tool, and §8's step 3 is therefore
aimed at the wrong milestone.

That reopens a question §4 thought it had settled: **what generates a
line drawing from two line drawings?** ToonCrafter interpolates
cartoon frames and does not require colour. FrameFusion and GIMM-VFI
are frame interpolators and are indifferent to it. None of them accepts
a chart. The candidate that accepted the specification turns out not to
accept the medium.

---

## 7b. Specification: how this project uses ToonComposer

Written 2026-10-16, after the spike. Supersedes the loose treatment in
§4.3, which recommended ToonComposer for the wrong stage.

### 7b.1 What it is

**A post-keyframing model: colour in, colour out.** It takes a painted
keyframe and one or more sketches at chosen temporal positions, and
produces painted video. It has no line-in-line-out mode. §7a's sixth
pass has the evidence.

### 7b.2 Where it sits

| stage | tool |
|---|---|
| capture and register | `comfyui_acme` |
| legibility cleanup | `comfyui_acme` (deterministic CV) |
| **pencil test** — line in, line out | **not ToonComposer.** Open; see §7b.5 |
| **colour / paint** — one painted key plus approved drawings, out comes painted footage | **ToonComposer** |
| acceptance harness | `comfyui_penciltest` |

So it enters **after** a pencil test has been approved and the artist
has painted **one** key. That is a real workflow and the governing
document already asks for it — *"rough sketch to fully extrapolated and
coloured"* — it is simply not the first milestone.

### 7b.3 The interface, as measured

**Inputs**

| | |
|---|---|
| colour keyframes | 1 to 4 (`max_num_cond_images: 4`), conventionally at frame 0. **Required.** |
| sketches | 1 to 4, at any frame indices. This is the slot the timing chart maps onto, and it is still the only one found in any candidate. |
| prompt | the shipped samples all end *"Anime. High quality."* |
| frames | **33 is the trained length** (`num_frames: 33` in the checkpoint config). The UI's `minimum=17` is a widget floor, not the model's. |

**Measured costs, RTX 5090 Laptop, 480p, 15 steps**

| | |
|---|---|
| peak VRAM | **5.9 GiB** streaming everything, **16.7 GiB** with ~12 GiB resident |
| speed | **70–97 s/frame**; a 33-frame generation is **~38 minutes** |
| build | ~20 s with a warm page cache |
| host RAM | 36.7 GiB resident; the machine has 91 GiB *shared with a desktop* |

**Two defects that must be carried**

1. **Bare parameters break under block swap.** diffsynth wraps module
   *types*; ToonComposer's `sequence_cond_identifier` and ~330 other
   tensors are bare and stay on the CPU. Any integration must pin them
   after `enable_vram_management` or fail with a device mismatch. §7a,
   third pass.
2. **Output quality is not yet established, and an earlier version of
   this line claimed it was.** See the retraction below.

#### Retraction: the control was run at the wrong CFG

**Withdrawn 2026-10-16.** This section first reported that the control
reproduced ToonComposer's sample 3 to within tolerance for *28 of 33
frames*, and concluded the installation was sound with an isolated tail
defect. **Both halves were wrong.**

Monte looked at the frames and said what the number had missed: in our
output *"the adult grows a third arm"*, where in theirs *"the child
kneels down before the adult to offer apples"*. The degradation is not
confined to the tail. It is **progressive and semantic** — anatomy
breaks by frame 8, the image washes out through the middle, and by
frame 24 ours is pale mush while the reference is still crisp.

**The cause is a parameter this spike guessed and never checked.**
ToonComposer's CFG slider defaults to **7.5**:

```python
cfg_scale = gr.Slider(minimum=1.0, maximum=15.0, value=7.5, ...)
```

Every run in §7a used **3.0**, a default invented in the spike's own
argument parser. Low CFG produces exactly what was observed: weak
adherence to the conditioning, anatomical incoherence, and washout.
`sequence_cond_residual_scale` was right at 1.0; CFG was not.

**Two lessons, and the second is the expensive one.**

*A metric I chose and then trusted.* The 28-of-33 figure came from a
mean-absolute-error threshold I picked myself, with no reason behind
the number 40. It passed frames that a person looking at them rejects
immediately. **An eye caught what the statistic was built to miss**,
which is the argument for looking at output rather than measuring it,
and it is the project's own standing rule — *look before computing*.

*A guessed parameter presented as a measurement.* Everything §7a says
about output quality was produced at less than half the intended
guidance scale, so **none of it is evidence about ToonComposer**. The
timings and memory figures survive — CFG does not change the cost of a
step — but every judgement about whether the output is usable is
withdrawn, including the inference that our pencil-drawing failure was
*demonstrated* to be the colour-frame problem.

**What survives, and why.** §7b.1's conclusion — that a colour frame is
required and the output is painted video — **does not rest on these
runs at all.** It rests on the TLDR figure, README step 2, and
`max_num_cond_images` in the checkpoint config. Documentary evidence,
unaffected by a sampler setting. The specification below therefore
stands; only the quality measurements are retracted.

A control at CFG 7.5 is running.

### 7b.4 What to build, when we build it

A `ComfyUI-ToonComposer` wrapper pack, per §14: the model wrapper and
nothing else, so it can go upstream. Its nodes take a colour image, a
list of (sketch, frame index) pairs, and the usual sampler controls.
**The frame indices come from the exposure sheet** (§13), which is what
makes this project's version worth building rather than a reimplemented
Gradio app.

Budget it as integration, not installation. The spike needed a
transitive-closure extractor to reuse six helper functions, because
`app.py` parses CLI arguments and builds the model at module scope.

### 7b.4a Too slow for a pencil test, on this hardware

**Monte's conclusion from the spike, 2026-10-16, and the arithmetic
agrees.** At the measured 69.9 s/frame:

| | |
|---|---|
| one 33-frame generation | **38 minutes** |
| a 5-second shot at 24 fps (120 frames) | ~3.6 generations, **~2 hours 20 minutes** |

Against an artist who drew the keys in minutes and wants to know
*now* whether the movement reads. A pencil test that arrives after
lunch is not a pencil test; it is a render.

**This survives the CFG retraction.** Guidance scale does not change
the cost of a denoising step, so the timings stand while the quality
judgements do not.

**So ToonComposer is disqualified from the pencil test twice over, for
independent reasons.** It needs a colour frame that does not exist at
that stage (§7b.1), and it is two orders of magnitude too slow for the
loop it would sit in. Either alone would be decisive. The second is
the one that cannot be designed around: the first might be met by
inventing a colour surrogate, but nothing makes 140 minutes into
seconds on this machine.

Note what this does **not** say. For the **colour stage** — where the
artist has painted a key, the drawings are approved, and the output is
footage rather than a diagnostic — 38 minutes a shot is entirely
reasonable. The spec in §7b stands for that stage. It is the *loop
latency* of a pencil test that it fails, not the job.

### 7b.5 The hole this leaves

**Nothing yet generates a line drawing from two line drawings.** That
is the first milestone and §4.5's ranking was built around a candidate
that cannot do it. The remaining candidates do not require colour but
none accepts a chart:

| | colour required? | accepts a chart? |
|---|---|---|
| ToonCrafter | no | no |
| FrameFusion | no | yes — takes *t* |
| GIMM-VFI | no | yes — arbitrary *t* |

The two that accept a chart are flow-based interpolators that §4.2
predicts will fail joint onset by construction. That prediction is now
more useful than it was: it is the measurement the harness exists to
make, and the harness is built.

---

## 7c. What is a pencil test *for*? — open, with Daniel

Monte, 2026-10-16: he has asked Daniel to identify the core purpose of
the pencil test, and speculates that **it is to confirm timing and
performance, not to settle technical qualities such as joint onset** —
and therefore that flow interpolation may be adequate for it.

**Daniel has not answered. Nothing below is settled**, and it is
recorded now because it changes which experiment is worth running
next, not because it is a conclusion.

> **Related, 2026-10-16.** Daniel's
> [realtime-ui-construction note](../ideas/realtime-ui-construction.md)
> argues for the same split from craft rather than measurement, and
> supplies the best evidence the project has on this question: the
> 1990s digital animation stands judged timing from *"crude black/white
> threshold-style captures"* where *"the image quality wasn't the
> point"*. An existence proof from production practice.
> [Assessment](../ideas/realtime-ui-construction-response.md).

### Why the speculation is plausible

The acceptance note already half-says it. *"A pencil test is
diagnostic, not deliverable — you shoot the drawings, play them at
speed, and judge whether the movement reads."* If what is being judged
is whether the movement reads, then the inbetweens are scaffolding:
they have to avoid distracting, not to be right.

And traditionally the pencil test does not wait for inbetweens at all.
Animators shoot keys and breakdowns on 2s precisely to check timing
before the inbetweens exist.

### The sharpening worth adding

**The joint-onset objection scales with the width of the gap, and that
has been treated as if it did not.**

Acceptance §2's decisive argument is Williams's unfolding box: two
keyframes, eleven frames between them, and software that opens three
right angles simultaneously. That is a **wide-gap, two-key** case, and
the objection is fatal there.

A single inbetween between two *adjacent* drawings is a different
proposition. Successive breaking of joints is a property the artist
puts into the **spacing of the keys and breakdowns**. If those
drawings already encode it, a machine filling one frame between
adjacent ones cannot destroy it — there is no room in the gap for the
joints to go wrong.

So the severity of §4.2's prediction — that flow interpolators *"will
fail joint onset on every chain, by construction"* — depends entirely
on a question acceptance §7 asked and never had answered:

> **How wide are the gaps an assistant normally fills — one inbetween,
> or a run of five?**

That has been sitting in the open-questions list as a scoping detail.
It is not. **It decides whether the project's most-quoted objection
applies to the first milestone at all.**

### Where I would push back

The joint-onset argument is not the only objection to flow
interpolation on drawings, and the other one is untouched by this
reframing. §4.2 also predicts that flow methods **ghost and double
lines rather than move them**, because a flow estimator has nothing to
latch onto in sparse black-on-white with large displacement. That is a
*legibility* failure, not a *principle* failure, and a pencil test
whose lines smear may fail at exactly the job Monte's speculation says
it has.

Whether a doubled line reads as a blur at 24 fps or as a mistake is an
empirical question, and an animator can answer it by looking.

### The experiment this makes cheap and obvious

**The corpus already contains the answer.** Cleanups 1 and 3 are
adjacent drawings; cleanup 2 is the inbetween the artist actually drew.
Interpolate 1→3 and compare the middle against 2.

That is the §4.2 prediction and Monte's speculation tested in the same
run, against ground truth, on the real medium. FrameFusion is **37 MB
and runs on a CPU**. It costs nothing next to the 38 minutes a single
ToonComposer generation takes, and unlike this spike it needs no
weights, no block swap and no guessed sampler settings.

It is now the obvious next thing to do, and §8 has already been
reordered to put FrameFusion first.

---

## 8. What to build first

> **Reordered 2026-10-14, and the reason is worth more than the order.**
> The list below used to run cleanup → harness → FrameFusion →
> ToonComposer, which sequenced the work by dependency. Monte: *"At what
> point do we start using the ToonComposer APIs? It feels like we're
> rebuilding from scratch."*
>
> The duplication half of that is answerable — ToonComposer ships a
> generator and nothing else, no harness, no exposure sheet, no arcs
> check, so none of the harness work repeats it. **The sequencing half
> is not.** Ordering by dependency put the project's largest unretired
> risk fourth, and that risk is not "is the integration fiddly" but
> **"does a 14B model run usefully on this machine at all"**.
>
> §7 argues it does: 61 frames is not what a key pair needs, fp8 is
> native on Blackwell, and 98 GB of host RAM is a good ratio for block
> swap. **That is an argument, not a measurement**, and everything
> downstream is costed against it. A harness built to judge a generator
> that cannot run here would be a well-tested waste.
>
> So the spike goes first. Not the integration — the one question.

0. **Spike: does ToonComposer run here?** One key pair from the corpus,
   driven from a script, 9–17 frames at 480p. Measure peak VRAM, wall
   clock, and whether the output is worth looking at. **Throwaway code,
   kept downloads.** It either validates §7 or rewrites the plan, and
   nothing after this point is honestly estimable until it is known.
1. **Finish legibility cleanup and chart reading** (`comfyui_ink`).
   Judged on registration residual and chart-reading accuracy against
   the animator's own reading. No models, no licences, known cost.
2. **`HarnessJointOnset` plus `HarnessSpacingError`.** Before any
   generator. They are what makes the generative steps mean something.
3. ~~**ToonComposer integration**~~ — **moved, 2026-10-16.** The spike
   (§7a) established that it is a colour-stage tool, so integrating it
   before a pencil test exists would be building the second stage
   first. It is specified in §7b and waits for a painted key to exist.
   **FrameFusion moves up in its place**, because the open question is
   now *what makes a line drawing from two line drawings* and the
   flow interpolators are the only candidates left that work in line.
4. **FrameFusion as the calibration baseline** — now the first
   generator rather than the third. Hours of work. It will be
   timing-exact and will fail joint onset on every chain. If the
   harness does not catch that, fix the harness. It is also, after
   §7b.5, one of only two candidates that work in line *and* accept a
   chart, so it is no longer only a baseline.
5. **Wan FLF2V and ToonCrafter as generative baselines**, through
   `TweenResampleToChart`, so their pacing error is a number in the
   report.

**The general lesson, since this project keeps meeting it:** a build
order that follows dependencies retires risk in whatever order the
dependencies happen to fall, which is not the order that matters. Ask of
each step *what would we most hate to learn late*, and do that first
even when nothing depends on it yet.

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
  is.** No sheet in the corpus carries a chart. **Requested 2026-10-13:**
  Monte has asked Daniel for a hand-written exposure sheet and a prose
  description of it. Note that an exposure sheet is *not* a timing chart
  — see §13 — so this unblocks `XSheetLoad` and leaves `ChartRead`
  waiting on a photographed page with a chart on it.

**The correction: use `12F/`, not `10F/`.** The 10F crop removes the
outer 1/12 of each dimension, which is exactly where the peg holes are.
Measured: the bottom band of a 10F frame is blank paper. No pegs means
no registration landmarks, which makes every `comfyui_acme` node
inapplicable to it. **10F is a viewing crop, not a working set.**

**2. What is in a `TIMING_CHART`?** **Reframed 2026-10-13 — see §13**,
which separates the exposure sheet from the timing chart and proposes a
schema for the first. The sub-questions below apply to the *chart*, the
smaller and later of the two:

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

**3. ~~The pack layout~~ — answered 2026-10-13, and differently from
the suggestion here.** I had proposed folding cleanup into
`comfyui_acme` because it shares the calibration. Monte's constraint
overrides that: the plugins are meant to be contributed upstream to
ToonComposer, which does not want ACME infrastructure. **§14 has the
split by upstreamability, the name `comfyui_penciltest`, and the
import-firewall test.** The `ink` name collision stands and is avoided
there too.

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
| `12Fto10F` | **a bash script, not a directory** |

The crop keeps exactly the central **10/12** of each dimension —
2734/3281 = 1921/2305 = 0.8333 — which is what establishes that
**12F and 10F are field sizes, not frame counts.**

**The sheets are not all the same size.** Four distinct stored sizes:

| stored | count | note |
|---|---|---|
| 2305×3281 | 20 | the common case |
| 2305×3217 | **1** | **64 px narrower in the rotated frame** |
| 2309×3281 | 1 | |
| 2313×3281 | 2 | |

This matters more than it looks: **absolute pixel coordinates do not
transfer between sheets.** Anything keyed to a position must anchor to
an edge. An absolute crop near the right-hand edge runs off the narrow
sheet, and ImageMagick returns a short tile rather than an error.

**An EXIF trap, and a bug it was hiding.** The files carry
`orientation=6`, so `identify` reports 2305×3281 (portrait) while every
viewer shows 3281×2305 (landscape). A loader that does not call
`exif_transpose` silently works on a sideways page. That deserves its
own test.

Worse, the conversion script rotated the raster and left the tag alone,
so **every 10F output claimed it still needed rotating** — `identify`
said 2734×1921 while PIL's `exif_transpose` returned 1921×2734. Fixed
2026-10-13 by setting the tag to match the raster; see §12.6.

**Three sheets carry a thin dark scan-edge strip** along one edge, and
one has a strip at the right. Harmless to the eye, but an ink detector
finds them, so anything measuring ink near an edge should inset.

### 12.6 Keeping the drawing number in the 10F crop

The 10F field is the central 10/12, and **the drawing number is written
outside it** — upper right corner of the sheet, past the field edge. So
the original crop threw away the only identity each drawing carries,
which is why §12.2's reading had to be reconstructed by overlay rather
than read off the file.

`12Fto10F` now lifts that corner and composites it into the top right of
the 10F output. Three things about the geometry, each measured:

**The box is 340 × 360, anchored to the corner rather than given
absolute coordinates.** Across all 24 sheets the left-most metadata ink
sits **254 px** from the right edge (rough 6.5) and the lowest sits
**267 px** below the top (cleanup 1), so the box clears the worst case by
86 px across and 93 px down. Anchoring is not a stylistic preference:
with four different sheet widths, an absolute *x* slides across the
sheet, and on the narrow one it runs past the edge and yields a short
tile that then composites in the wrong place.

**It lands on blank paper.** Ink in the destination corner totals 94
pixels across all 24 frames, which is dust.

**The EXIF tag is now set to match the raster** (`-orient TopLeft`), so
the outputs stop claiming they need rotating.

Verified by regenerating all 24 into a scratch directory and checking
that every number and asterisk is complete, and that outside the pasted
corner the new outputs are **bit-identical** to the old ones.

### 12.7 Capturing the printed roughs on the rig

Monte, 2026-10-13: the 10F crops are *"printed landscape at the top of a
prepunched 10F sheet, so the printed images get real punch holes"*, and
the motive for capturing them is *"realistic images to feed into my live
ComfyUI pipeline"*.

**That reverses the recommendation in §14.3, which answered a question
nobody asked.** §14.3 weighed a re-capture as *training* data, where a
reprint is strictly worse than the original. As *pipeline input* it is
strictly better, because the 12F scans contain none of what the pipeline
exists to cope with.

**Two corpora, two jobs, and the error is using either for the other's:**

| | good for | useless for |
|---|---|---|
| **12F originals** | cleanup and inbetween supervision; pose and line fidelity; the pairing | anything about capture — no perspective, no rig lighting, no lens |
| **rig captures of the printouts** | `AcmeDetectSheet`, `AcmeRegister`, lens distortion, exposure, shadow, end-to-end smoke tests | line fidelity, and anything colorimetric (see below) |

**The win worth naming: these come with ground truth.** The twelve
originals are already mutually registered to ~3.5 px (§12.3). Print them,
capture them, and the registration pipeline has a known answer to be
scored against **on real drawings** — which is the one thing a ChArUco
board cannot provide, because a board is not a drawing and does not fail
the way a drawing fails.

With one honest caveat: what a capture recovers is *print placement
error* compounded with *capture and registration error*, and the residual
does not say which. They separate cheaply — **print one sheet twice and
capture both**; the difference isolates print placement repeatability.
That is an afternoon, and it is a number this project wants anyway, since
the desk concept involves printing.

#### Do not composite the pegs into the digital 10F

Monte has considered moving the peg holes up into the cropped 10F so it
matches the printout. **Recommend against**, on three grounds:

* **A composited hole is not a hole.** It has no shadow, no torn fibre,
  no deformation of the sheet around it. `acme` finds pegs by the chroma
  of inked crowns and by fitting rectangles in luminance — cues a paste
  does not have. It would teach a detector the wrong thing and the
  detector would then fail on real paper.
* **It would be geometrically false.** The original's punch-to-artwork
  relationship is not the printout's, because print placement intervenes.
  The composite would assert a registration that the physical sheet does
  not have.
* **The better version is already planned.** Real punches, in real paper,
  under the real rig. The composite is a worse substitute for the thing
  the capture gives you directly.

Its one honest use is a synthetic stand-in for pipeline smoke tests
*before* any rig captures exist — low value, given the captures are a
session's work.

#### Two things to settle before printing

**Scale.** The 10F crop is **13.7–13.9 inches wide** (§13.4), which is
wider than a 10-field sheet. So the print is being scaled, and the
capture's px/mm is not the original's. Anything that compares a capture
back to an original needs that factor, and it is one caliper measurement
on one printout. Worth recording in the manifest next to the 197–200 ppi
of the scans.

**Medium — and this one is easy to miss.** The roughs are blue pencil;
the printout is toner or inkjet. Pencil pigment sits in the tooth of the
paper and graphite is partly specular; toner is a fused film. They are
not the same stimulus. `acme/ink.py` separates pencils by the **angle of
(a\*, b\*) in CIE Lab**, measured over the inked corpus, and
[acme-registration-plugin.md](acme-registration-plugin.md) §9 makes
*separate the pencils, don't threshold them* a design rule.

So these captures are realistic for **geometry** and actively misleading
for **colour**. Use them for registration, detection, exposure and
end-to-end flow. **Do not tune the pencil separation on them** — that
wants real pencil on real paper, which is a different and much easier
capture to stage, because it needs no printer at all: a few scrap
drawings in the right media under the rig.

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

**The asterisks.** A small **asterisk** — not a cross — sits under 1, 6
and 10, and under no other drawing: not under 1.5 or 6.5, and under none
of the twelve cleanups. Verified across all 24 corners at native
resolution. In a ten-drawing run, 1 and 6 are half
a cycle apart, which is where the two contacts fall, so the obvious
reading is that ✗ marks a key or extreme. **That is a guess. Monte put it to Daniel on 2026-10-13; the answer is
outstanding.** If it is right, the corpus carries its own key/inbetween
labelling and `HarnessJointOnset` has its chain endpoints for free.

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
different line widths, and the rough carries construction marks and the
**ground lines, with perhaps a hint of shadow** (Monte, 2026-10-13), at
lower left that the clean does not. The overlay is
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

**Settled 2026-10-13.** Monte: *"WikiWikiCartoons owns these images
outright and we don't plan to publish the original art at this time."*
So the corpus stays **out of tree**, and an in-tree `manifest.json`
describes it: `data/corpora/manrun_cycle_2001_wwc/manifest.json`.

That resolves both problems at once. The provenance problem — this
repository publishes, so committing the artwork would publish artwork
that is not ours to publish. And the size problem — 327 MB for `12F/`
against a repository already carrying 948 MB in `data/` and a 672 MB
`.git`, with no LFS configured.

**The manifest is the contract.** It records what each sheet is, so the
reading in §12.2 is not lost, and it carries `sha256_16` per file so a
test can verify it is pointed at the corpus it thinks it is. Tests
locate the corpus by a configured path and **skip when it is absent** —
the pattern `acme/ink_test.py` already uses — so a checkout without the
artwork still runs green.

---

## 13. The exposure sheet and the timing chart are two instruments

Monte, 2026-10-13: *"Are you asking for a data model for an exposure
sheet? By 'read off the chart geometry' do you mean that the order of
the frames is the order on the exposure sheet?"*

No, and the question exposes a conflation in §11.1 worth fixing
properly. **An exposure sheet and a timing chart are different
documents carrying different information, and this project needs
both.**

| | answers | lives on | consumed by |
|---|---|---|---|
| **exposure sheet** | *which drawing is exposed on which frame* — holds, layering, cycles, and later track, EFX and camera | a production document, one per scene | **ToonComposer's frame indices**, directly |
| **timing chart** | *where a drawing sits along the path* between its neighbours | the drawing itself, upper right corner | the harness's spacing test (acceptance §2) |

The exposure sheet is **temporal**: drawing 3 is held for two frames, so
it occupies frames 7 and 8. The timing chart is **spatial**: drawing 1.5
sits a third of the way from 1 to 2, not halfway. Neither derives from
the other.

### Why "read off the chart geometry" matters, and the corpus proves it

The number on a drawing is a **name**, not a position. Drawing "1.5"
is called that because it was inserted between 1 and 2 — it says nothing
about where it sits in space. A slow-in puts it at 0.3; a slow-out puts
it at 0.7.

**Deriving the fraction from the number is a formula**, and the
manuscript is explicit that formula is *"a nail in the coffin of
character animation"*. Acceptance §3 turned that into the hard rule:
*the system must never infer timing; it reads the chart and obeys it.*

§12 shows the concern is live rather than theoretical: this corpus's
roughs are numbered **1, 1.5, 2 … 6, 6.5, 7**. Nothing in those names
says where 1.5 and 6.5 sit, and assuming halfway is exactly the
inference the rule forbids. **That is what "read off the geometry"
meant** — measure the mark positions on the chart; do not compute the
fraction from the numbering or from the row order.

### Where each attaches

The chart does **not** belong in the exposure sheet. It is a property of
a *drawing*, or of the *segment between two keys*, so it is keyed by
level and drawing and carried alongside:

```
exposure sheet  ──(frame → level → drawing)──►  ToonComposer sketch slots
timing chart    ──(drawing → fraction)──────►  HarnessSpacingError
```

A drawing can appear on many frames (a hold) and still have one position
on the path. Putting the fraction in a row would duplicate it per frame
and invite the two copies to disagree.

### 13.1 A proposed exposure-sheet schema

Following Monte's outline. Metadata outermost, rows in frame order, each
row an **ordered list of cels, outermost to innermost**.

> **Vocabulary, corrected 2026-10-13.** The unit is a **cel**, from
> celluloid — *"there is no such thing as a 'cell' in animation"*
> (Monte). Earlier drafts of this section wrote `cells`; it is `cels`
> throughout now. Definition, sources and the words this project does
> not use are in **[glossary.md](../glossary.md)**, which became a
> document of its own on 2026-10-14. Worth enforcing mechanically
> rather than by vigilance; see §14.4.

```json
{
  "schema": "storymator.xsheet/1",
  "production": {
    "studio": "Wiki Wiki Cartoons",
    "show": null, "act": null, "scene": null, "sequence": null,
    "animator": null,
    "description": "man run cycle, cane and top hat",
    "frame_rate": 24,
    "field_size": "12F"
  },
  "levels": [
    {"id": "A", "name": "man", "note": "the only level in this scene"}
  ],
  "rows": [
    {
      "frame": 1,
      "cels": [
        {"level": "A", "drawing": "1"}
      ]
    },
    {
      "frame": 2,
      "cels": [
        {"level": "A", "drawing": "1"}
      ]
    }
  ]
}
```

Four design notes, each of which is a decision rather than an obvious
choice:

**Cels are ordered *and* carry a level id.** Monte's outline says
ordered outermost to innermost, which is more general than a traditional
sheet's fixed columns — a cel can change depth mid-scene. But the fixed
columns bought an invariant worth keeping: that level A is *normally*
the same thing throughout. Carrying `level` as well as position means a
reader can detect an accidental re-ordering between frames rather than
silently compositing in the wrong order. Cheap, and it makes a good
test.

**Holds need no special case.** The same `drawing` repeated on
successive rows *is* a hold. Cycles likewise, until someone wants them
expressed compactly — at which point that is a notation on top, not a
change to the rows.

**`drawing` is a string, not a number.** Because `"1.5"` and `"6.5"`
exist, and because sheets carry things like `"X"` for a blank. Sorting
is by the sheet, never by parsing the name.

**Room for the later fields is in the cel *and* the row.** Track, EFX
and camera are not all the same shape: dialogue and sound belong to the
**frame**, as does a camera instruction such as field size, pan, zoom or
tracking — they are not per-layer. So I would add them to the **row**,
beside `cels`, rather than into the cel record. If Monte's "how
record" meant something that holds all of them, that is the one place
this schema departs from the outline and it should be said out loud.

### 13.3 Field size is a width; aspect ratio is the shape

Monte, 2026-10-13: *"Do we need an aspect ratio in addition to a field
size? … it is possible to use a 16:9 ratio with a 12F sheet, though it's
usually 4:3."*

**Yes, and they are independent.** A field size is the *width* of the
camera field in field units. The aspect ratio supplies the height. 12F at
4:3, 12F at Academy and 12F at 16:9 are three different rectangles that
happen to share a width, so **a field size alone does not name a
rectangle** and the schema cannot omit the ratio.

One refinement worth building in from the start: **record the number, not
the nickname.** The standard field chart is Academy **1.37:1**, which
everyone calls 4:3. But 4:3 is 1.3333, and 1.37 vs 1.3333 is **2.7 % of
the height** — about a quarter inch on a 12-field chart, which is the
kind of discrepancy that surfaces at composite time and gets blamed on
something else.

### 13.4 And a finding: our `10F/` is not a 10 field

Checking the question against the corpus turned up a mismatch.

`12Fto10F` keeps the central **10/12 of both dimensions**, so the output
inherits the scan's aspect exactly:

| | px | aspect |
|---|---|---|
| 12F scan | 3281 × 2305 | 1.4234 |
| `10F/` crop | 2734 × 1921 | **1.4232** |

1.4232 is **not** 4:3 (1.3333), not Academy (1.3700) and not 16:9
(1.7778). It is the *paper's* proportion, because a proportional crop
cannot change the shape it started with. **This argument needs no scale
at all**, which is what makes it solid.

The scale makes it starker. Peg centres measure 800.4 px apart in these
scans; against ACME's nominal 4.0000 in that is 200.1 ppi, and against
the bar this project actually measured —
[honbay_0001](../../data/calibration/pegs/honbay_0001/README.md), 4.0624
in — it is 197.0 ppi. Either way **the `10F` crop is 13.7–13.9 inches
wide, not 10.** (Which punch made the 2001 holes is unknown, so both are
quoted rather than one chosen.)

So **`10F` names a paper crop — the sheet less a 1/12 border — not a
camera field.** The name asserts a field; the geometry does not deliver
one. Nothing downstream is broken by this yet, because nothing has used
it as a field. It wants deciding before something does: rename the
directory, or change the crop.

**And a true field crop needs the pegs.** The field centre is fixed
relative to the *peg bar*, not to the sheet edges — a sheet trimmed
slightly off-square still shoots true, because the camera is registered
to the pegs. So cropping a real field means locating the pegs first,
which is `comfyui_acme`'s job and is exactly what the present `10F` crop
destroys (§12.1). The two findings are the same finding seen twice.

### 13.5 Where each belongs in the schema

Aspect is a property of the **production**; field size and centre are
properties of a **camera instruction on a row**:

```json
{
  "format": {
    "aspect_ratio": "1.37:1",
    "aspect_decimal": 1.37,
    "name": "Academy",
    "note": "not 4:3 -- 1.37 vs 1.3333 is 2.7% of height"
  },
  "rows": [
    {
      "frame": 1,
      "cels": [{"level": "A", "drawing": "1"}],
      "camera": {"field": {"size": 10.0, "north": 0.0, "east": 0.0}}
    }
  ]
}
```

Three notes:

**Both the ratio string and its decimal.** The string is what an animator
writes; the decimal is what code compares. Storing only the string means
every consumer parses `"16:9"`, and one of them will do it wrong.

**Field size carries a centre offset.** Field instructions are notated
`10F N2 E3` — size *and* position. A size-only field is only the centred
case, and a pan is a sequence of centres, so the offsets have to exist
before pans can be expressed at all.

**Aspect sits at production level, overridable per row.** It is the
delivery format and effectively constant, so repeating it on every row
invites two rows to disagree. A per-row override costs nothing and covers
the rare format change.

### 13.2 What this changes in the build order

**The exposure sheet is the better first target, and it is also easier.**
It is a hand-written document that a human can transcribe, so it does
not require the sub-pixel mark measurement the chart does, and it maps
straight onto ToonComposer's interface. Monte has requested one from
Daniel together with a prose description (2026-10-13).

So §8's step 1 splits:

1a. **`XSheetLoad` / `XSheetValidate`** over the JSON above — pure data,
    no models, no rig, fully testable the day the schema is agreed.
1b. **`ChartRead`** — still blocked on a photographed page with a chart,
    and still the only blocked thing.

---

## 14. Packaging, and keeping the rig out of it

Monte, 2026-10-13: *"This set of tools is not part of the acme
subpackage… I'm concerned about ACME-specific parameters slipping into
this new code base. The goal is to contribute the ComfyUI plugins back
to the ToonComposer project, and they don't necessarily need or want the
ACME infrastructure."*

Right, and that goal should drive the split. **Divide by how far each
piece can travel, not by pipeline stage.**

| pack | contents | travels to |
|---|---|---|
| `ComfyUI-ToonComposer` | the model wrapper and nothing else — load, sketch injection at frame indices, sampling, offload | **upstream.** Zero project opinions, so it is contributable |
| `comfyui_penciltest` | x-sheet types and I/O, cleanup, the harness, tween orchestration across backends | publishable on its own; useful to any 2D shop, rig-agnostic |
| `comfyui_acme` | pegs, sheet detection, registration, lens, capture | **stays here.** It is our bench |

The thing ToonComposer's maintainers would want is the first pack only.
Our x-sheet and our harness are opinionated — they encode Daniel's seven
principles and this studio's vocabulary — and that is a feature for us
and a liability upstream. Keeping them in a separate pack means the
contribution is small, reviewable, and free of anything they would have
to argue about.

### 14.1 The name

**`comfyui_penciltest`** for the middle pack. It is the product name
the governing document already uses, it is traditional-animation
vocabulary any 2D animator reads instantly, it names the *output*
rather than a mechanism so it survives swapping FrameFusion for
ToonComposer, and it contains no rig, no vendor and no ACME.

Alternatives considered: `comfyui_xsheet` names the central data type
but undersells the cleanup and harness halves; `comfyui_inbetween`
excludes cleanup; `comfyui_assistant` is evocative of the studio role
acceptance §3 puts the machine in, but collides badly with "AI
assistant" in every search.

Node prefix `PencilTest*`, category `penciltest/`. Note the category
should *not* be `storymator/…` — the pack is meant to leave.

### 14.2 The firewall, as a test rather than a rule

"ACME-specific parameters slipping in" is exactly the kind of thing that
happens gradually and is expensive to undo, so it should fail the build
rather than rely on vigilance. Two rules, both testable:

**No import of the rig.** `comfyui_penciltest` may not import `acme` or
`comfyui_acme`, directly or transitively. That is an `ast`-walk over
every module in the pack, asserting no `Import`/`ImportFrom` names the
rig — a dozen lines, and it fails loudly the first time someone reaches
for a convenience.

**No physical constants.** The subtler leak is not an import but a
default: peg spacing, 200 px/inch, a field size, an ACME hole diameter.
The rule is that the pack **takes scale as an explicit input and
hardcodes no physical quantity.** Its public surface should speak in
pixels and in fractions, with a `px_per_mm` passed in where real units
are needed. Harder to test mechanically than the import rule, so it
belongs in the pack's README as a stated contract and in review.

The direction is one-way: **`comfyui_acme` may depend on
`comfyui_penciltest`, never the reverse.** The rig knows about pencil
tests; pencil tests do not know they came off a peg bar.

### 14.4 A vocabulary test, for the same reason

[glossary.md](../glossary.md) fixes the project's vocabulary and carries
the rule that **the code should use these words and no others**. That has
now been breached twice in this document — the marks on the roughs were
called crosses when they are asterisks, and the exposure sheet's unit was
called a cell when it is a **cel**. Both were caught by Monte reading
carefully, which is not a mechanism.

It is the same argument as §14.2's import firewall: a rule that matters
should fail the build rather than depend on vigilance. A test over
`comfyui_penciltest`'s own sources rejecting a short banned list —
`cell`/`cells` first — is a dozen lines.

It works **in the new pack specifically** because the pack has no grids,
no meshes and no phones, so there is no legitimate "cell" to allow for.
Running the same check over the whole repository would false-positive on
the calibration maths and the lighting notes, so the check stays scoped
to the pack rather than being made clever.

### 14.3 Should the printed roughs be re-scanned with pegs visible?

Monte asks, given the stage's inputs are already registered.

> **Answered differently once the purpose was stated — see §12.7.**
> Monte's reason for wanting the capture is realistic input for the live
> ComfyUI pipeline, which is a different goal from training fidelity.
> For *that* purpose the answer is yes. What follows is still right
> about what the capture is **not** good for, and wrong only in
> treating training fidelity as the only reason to capture.

**No, for the purpose of feeding this pack** — and the reason is the
same concern that prompted the question.

* **The originals already have pegs and are already registered.** §12
  measured the two passes agreeing within 3.5 px, with peg spacing at
  200 px/inch. A fresh scan of a reprint cannot beat that.
* **A reprint is second-generation.** You would be measuring the printer
  and the scanner, not the drawings — line weight, dot gain and paper
  all change. For a cleanup model that learns what a pencil line looks
  like, that is the wrong signal.
* **Pegs in frame are a liability for this pack, not an asset.**
  `comfyui_penciltest` is supposed to accept registered images and know
  nothing about how they got registered. Training or testing it on
  frames with peg holes in them teaches it to expect holes, which is
  precisely the ACME contamination the pack is meant to avoid.

**What is worth capturing instead**, in priority order: the exposure
sheet and chart pages Daniel has been asked for; and, separately and for
`comfyui_acme`'s own validation rather than this pack's, the **original**
artwork through the real rig — the 12F scans are a reference set the
registration code can be measured against, which is better than another
calibration board.

---

## Sources

BibTeX for the published work below is in
[bibliography.bib](../bibliography.bib): `li2025tooncomposer`,
`xing2024tooncrafter`, `wan2025`, `xing2023dynamicrafter`,
`chen2023videocrafter1`, `guo2024gimmvfi`, `framefusion`,
`simoserra2016learning`, `zhang2023controlnet`, `meng2024anidoc`.


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
