# Pencil test: system architecture

*Written 2026-10-16, after the ToonComposer spike. Governing document:
[the coarse scoping](../README.md). Supersedes §8's generator ordering
in [inking-and-tween-plugins.md](inking-and-tween-plugins.md).*

Monte, 2026-10-16, setting the objective:

> *"let's assume that inbetweening rough sketches to a timing chart is
> the core objective, and that we're willing to give up fidelity to get
> something fast and close enough"*

and the keystone:

> *"I don't think the interpolated frames need to be used in the final
> production pipeline — it may be enough to validate a timing chart
> which can be fed to a later stage."*

## 1. The keystone, and what falls out of it

**The deliverable of the pencil-test stage is an approved timing chart,
not drawings.** The frames are scaffolding that exists to let an
animator judge, and are thrown away.

Four consequences, and they simplify more than they constrain.

**The generator becomes an instrument, not a pipeline component.**
Nothing downstream consumes its output, so it can be replaced without
touching anything else. That lowers the stakes of choosing one
considerably, and argues against spending much deciding.

**The harness splits along the same seam.**

| stage | what must be checked | why |
|---|---|---|
| **proxy** | `HarnessSpacingError` only | if the proxy puts a drawing somewhere the chart did not ask for, the animator judges a timing they will not get, and the approval is void |
| **final synthesis** | arcs, joint onset, squash and stretch | these are properties of *drawings that ship*. A disposable frame owes them nothing |

This gives [§7c](inking-and-tween-plugins.md)'s speculation a precise
form. Joint onset is not relaxed — it is **relocated**, to the stage
that produces drawings somebody keeps.

**[§13](inking-and-tween-plugins.md)'s exposure-sheet schema stops being
data interchange and becomes the deliverable.** It is the artefact that
crosses the boundary. That raises its priority and vindicates the care
spent on it.

**The proxy's quality bar is now statable.** It must be *legible enough
to judge a pose*, *fast enough not to break the flip loop*, and
*faithful in spacing*. It owes nothing to line quality, model fidelity
or the seven principles.

## 2. One selection criterion dominates: arbitrary *t*

A timing chart is **non-uniform by construction** — slow-in, slow-out,
holds. An interpolator that only doubles (2×, 4×, 8×) can produce only
*even* spacing, which is precisely the formula the manuscript calls
*"a nail in the coffin of character animation"*.

**So the proxy generator must accept an arbitrary position along the
path, not a power-of-two subdivision.** This is a harder filter than
speed or quality and it eliminates candidates quietly.

## 3. Candidates, with licences actually checked this time

**FrameFusion is dead, and recommending it was my error.** I put it in
§8's build order and §7c's experiment while its licence sat marked
*unverified* in §5. Checked now:

> *"The packaged model weight … is licensed under CC BY-NC 4.0."* —
> code is Apache-2.0, **weights are NonCommercial**, and it is the same
> model sold as the FrameFusion Motion Interpolation Steam product.

Same class of blocker as `sketch_simplification`, and the project's own
rule — *trace a checkpoint's lineage, not its card* — would have caught
it had I applied it.

| candidate | code | weights | arbitrary *t*? | verdict |
|---|---|---|---|---|
| **RIFE** (Practical-RIFE) | MIT | MIT | **yes**, v4.x takes a timestep | **lead candidate** |
| FILM (Google) | Apache-2.0 | **unstated** — Google Drive, no terms | yes | verify first; also TensorFlow 2 against our torch stack, and *"not an officially supported Google product"* |
| **Wan2.x-Fun-InP 1.3B** | Apache-2.0 | Apache-2.0 | no — emits N frames evenly | **fits this card**; see §4 |
| Wan2.1 FLF2V 14B | Apache-2.0 | Apache-2.0 | no | too large, too slow |
| ToonComposer | MIT | MIT | yes (frame indices) | colour stage only; needs ~42 GiB |
| ~~FrameFusion~~ | Apache-2.0 | **CC BY-NC 4.0** | yes | **blocked** |

One caveat on RIFE, recorded rather than buried: a third-party
derivative (RIFE-for-Nuke) warns that the *training data* may carry
non-commercial terms. That is a downstream claim, not the author's, and
the upstream repository states MIT for code and weights. **Worth one
question to the author before anything ships**, on the same principle
that caught VideoCrafter.

## 4. The option that changes the middle of the range

**`Wan2.x-Fun-InP` at 1.3B is Apache-2.0 throughout, does start-and-end
frame conditioning, and is about 2.6 GiB in bf16.** It fits this card
with room to spare — unlike the 14B models, which is the whole reason
ToonComposer failed here.

It does not take arbitrary *t*, so it cannot honour a chart directly;
it emits N frames evenly and would need `TweenResampleToChart`
([§6.3](inking-and-tween-plugins.md)) to be re-timed, with the spacing
error reported rather than hidden.

So it is **not** a proxy generator. It is the first candidate found
that could plausibly do *final* synthesis on hardware Monte owns, which
is a different and currently unfilled role.

## 5. The architecture

```
   drawings on paper
          │
          ▼
   comfyui_acme ─────────── registration, legibility cleanup
          │
          ▼
   ┌──────────────────────────────────────────────┐
   │  THE INSTRUMENT (local, fast, not ComfyUI)   │
   │                                              │
   │   exposure sheet (§13)  ←── animator edits   │
   │          │                                   │
   │          ▼                                   │
   │   proxy inbetweens at arbitrary t  ── RIFE   │
   │          │                                   │
   │          ▼                                   │
   │   flip / scrub ──► animator judges timing    │
   │          │                                   │
   │   HarnessSpacingError: does the proxy sit    │
   │   where the chart said?                      │
   └──────────────────────────────────────────────┘
          │
          ▼
   APPROVED TIMING CHART  ◄── the deliverable; frames discarded
          │
          ▼
   ┌──────────────────────────────────────────────┐
   │  SYNTHESIS (ComfyUI, slow, asynchronous)     │
   │   Wan-Fun-InP 1.3B locally, or ToonComposer  │
   │   on rented hardware for the colour stage    │
   │                                              │
   │   full harness: arcs, joint onset, spacing   │
   └──────────────────────────────────────────────┘
```

Two boundaries matter. **The instrument does not run through ComfyUI** —
a batch graph executor cannot answer inside a flip. And **the only
thing crossing from instrument to synthesis is the exposure sheet**,
which is why its schema is the deliverable.

## 6. What this means for the budget

The project runs on **$25/day**. Two consequences.

**The 80 GB ToonComposer test is affordable now.** An 80 GB A100 or
H100 rents for roughly $2–3/hour; the decisive experiment — sample 3
with `model.to(device)` and no block swap — is one hour. It does not
need saving up for; it needs scheduling.

**The proxy path costs nothing.** RIFE is small enough to run on the
CPU and the corpus is already on disk. The next experiment — cleanups 1
and 3 in, compare the middle against cleanup 2 — has no hardware cost
at all.

## 7. What to do next

1. **RIFE on the corpus.** Cleanup 1 → cleanup 3, compare the middle
   against cleanup 2. Answers two questions at once: whether flow
   interpolation on pencil line art is legible enough to judge a pose,
   and whether it ghosts the way §4.2 predicts. No GPU, no budget.
2. **The exposure-sheet schema**, which the keystone promotes to the
   deliverable. Still blocked on the one open question in §13.1.
3. **The 80 GB ToonComposer control**, when scheduled — it decides
   whether ToonComposer is usable at all, on anyone's hardware, for
   this project.
4. **Ask the RIFE author about training-data terms**, before it is
   anywhere near shipping.
