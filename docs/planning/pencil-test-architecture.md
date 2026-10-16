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

## 2. Arbitrary *t* is a convenience, not a requirement

> **Rewritten 2026-10-16.** This section first claimed that an
> interpolator which only doubles *"can produce only even spacing,
> which is precisely the formula the manuscript calls fatal"*, and that
> arbitrary *t* was therefore the dominant selection criterion.
> **That was wrong**, and Monte caught it:
>
> *"the traditional way to use a timesheet involves creating uniformly
> spaced inbetweens at a coarse timeslice, and then subdividing at a
> finer slice. The only timing I can't see doing that way is
> favors."*
>
> Halving does not produce *even* spacing. It produces **any dyadic
> position** — and dyadic positions are what charts are made of,
> because repeated halving is how an inbetweener produces them.

### The traditional chart is exactly what halving serves

| wanted | served | error | depth |
|---|---|---|---|
| 1/2 — a half | 1/2 | **0** | 1 |
| 1/4, 3/4 — quarters | exact | **0** | 2 |
| 1/8, 7/8 — a slow-in | exact | **0** | 3 |
| **1/3 — a favor** | 3/8 | 0.042 | 3 |
| **1/3 — a favor** | 85/256 | 0.0013 | 8 |
| **2/5 — a favor** | 51/128 | 0.0016 | 7 |

The error bound at depth *n* is 1/2ⁿ⁺¹. For scale: acceptance §2's
stated failure is *"a .5 progression as a .3"* — an error of **0.2**.
**Depth 3 beats that by a factor of three**, and depth 3 is where the
exact chart positions already live.

### Favors are the exception, and the cost is not what it looks like

Monte is right that favors are the one case halving cannot hit exactly.
But the cost of approximating them is **not time** — a depth-*n*
position takes *n* interpolations, not 2ⁿ, because only the interval
containing the target is ever subdivided.

**The cost is compounding synthesis error.** Each level interpolates an
*interpolation*: at depth 5 the frame is five generations removed from
any drawing the artist made, inheriting every artefact of its
ancestors. On line art, where flow methods already ghost and double
(§4.2), that is the thing to watch.

So the cost structure mirrors the craft. **A half is exact and costs
one generation. A favor is a deliberate extra decision and costs
depth** — which is roughly how it feels to an inbetweener.

### Two consequences for the driver

**The approximation is known before anything is generated.** A chart
position maps to its dyadic server by arithmetic, so a driver can tell
the animator *"this favor will be served at 0.375 rather than 0.333"*
without running a model. That is `HarnessSpacingError` computed
statically — the spacing contract of §1 checked ahead of time rather
than after.

**Much apparent non-uniformity never reaches the interpolator at all.**
Timing is achieved two ways: by crowding drawings *spatially* along the
path, and by *exposure* — holding a drawing for more frames. Shooting
on 2s or 3s is exposure, not position. Those are exposure-sheet rows
and cost nothing.

### What this does to candidate selection

It widens the field rather than narrowing it. A 0.5-only interpolator
is usable with a chart-aware driver, so arbitrary *t* becomes a
convenience that saves depth — and therefore saves accumulated
artefacts — rather than a gate.

RIFE v4.x accepts a timestep, so it needs none of this. The analysis
matters because it means **the proxy generator can be chosen on
legibility and speed**, which are the properties §1 says actually
matter, instead of on an interface detail.

### One question for Daniel

Is a favor served at 3/8 distinguishable from one at 1/3, when the
drawing is a disposable proxy being flipped to judge timing? An
inbetweener asked to favour a key is eyeballing *"closer to A"*, not
computing thirds. If the answer is no, depth 3 suffices for everything
and favors cost nothing either.

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
