# The fast-proxy / slow-synthesis split — assessment

*Response to [realtime-ui-construction.md](realtime-ui-construction.md),
2026-10-16. Monte asked whether the concept maps onto what we are
already doing, and whether there is an obvious technical reason the
split would or would not work.*

**Short answer: it maps, more closely than the note's author could have
known, and the one real danger is not latency.**

## 1. It arrives at the same decomposition the spike did, from the other end

The note separates *"two problems that don't actually need to be solved
at the same speed"* — temporal decision-making, which must be
instantaneous, and drawing synthesis, which can lag.

Three days of measurement reached the same place by a different route.
[planning/inking-and-tween-plugins.md](../planning/inking-and-tween-plugins.md)
§7b.4a has ToonComposer at **38 minutes per 33-frame generation**, about
**2 h 20 m** for a five-second shot. §7c then records Monte's
speculation that a pencil test exists to confirm timing and
performance rather than to settle every technical quality.

Daniel's note is the same claim, made from craft rather than from a
stopwatch. **Independent arrival is worth more than either argument
alone.**

## 2. The historical evidence is the strongest the project has on this question

> *"those crude black/white threshold-style captures where you adjusted
> controls until enough of the drawing appeared to judge the motion. The
> image quality wasn't the point — the point was that it was fast enough
> to let the animator judge timing and change exposures interactively."*

§7c asks whether a low-fidelity inbetween is sufficient for a pencil
test. **This is an existence proof from a decade of production
practice**, from someone who used those stands. It is better evidence
than anything the harness can produce, because it is about what
animators actually accepted, not about what a metric scores.

It does not settle the question — a threshold capture of a *drawing the
artist made* is not the same as a *synthesised* drawing, and the
failure modes differ. But it moves the burden: the question is no
longer "can crude be enough" but "crude in which specific ways".

## 3. The tie-in Monte was looking for: the control surface is the exposure sheet

The note describes the animator wanting to *"change spacing, alter
holds, move a breakdown, or adjust the timing chart"*.

**That is the exposure sheet, exactly**, and this project already has a
schema for it —
[§13](../planning/inking-and-tween-plugins.md) — with rows in frame
order, cels ordered within a row, holds as a repeated drawing, and the
timing chart kept separate because it answers a different question.
§13 was written as a data-interchange problem. It turns out to be the
**state model of the instrument Daniel is describing**.

So the desk's dedicated exposure-sheet touchscreen, already in the
governing document's hardware list, is where this lands. Nothing new
has to be invented for the control surface; it has to be *built*.

## 4. The arbitrary-*t* property makes the interactive loop almost free

The note worries about regeneration latency. Most of it can be avoided.

**Changing the chart does not require regenerating anything**, if the
proxy inbetweens are parameterised by position along the path rather
than baked at fixed frames. FrameFusion and GIMM-VFI both take
arbitrary *t*
([§4.2](../planning/inking-and-tween-plugins.md)) — that was noted as
the property that lets them honour a timing chart. It has a second
consequence nobody had drawn: **moving a breakdown or changing a hold
re-times existing drawings rather than demanding new ones.** Scrubbing
is playback. Re-spacing is a handful of fresh *t* values, not a shot.

The expensive operation — the one the note is right to route around —
is only triggered by *new drawings*, not by new timing.

## 5. The real danger: the two speeds must agree about timing

This is the thing I would raise before anything is built.

The animator approves spacing on the proxy. The slow pass then
synthesises the final. **If the two disagree about where a drawing sits
along the path, the approval was meaningless** — the animator signed
off on a performance they will not receive.

And they can disagree, for a concrete reason. A warp or flow
interpolator places a drawing at *t* along **its own estimated motion
field**. ToonComposer places sketches at **integer frame indices** and
synthesises the rest to taste. Those are different notions of "a third
of the way", and nothing currently forces them to coincide.

**So the split needs a timing contract**: the proxy and the final must
be measured against the same chart, and the difference reported.
`HarnessSpacingError` is exactly that instrument, and it was built for
a different purpose — calibrating generative baselines. It becomes the
thing that keeps the two halves of this architecture honest.

That is a cheap requirement to state now and an expensive one to
retrofit.

## 6. Where I would push back: do not let the model build the instrument

The Google demo's novelty is *"the model building the artist's tool
dynamically, rather than merely generating the artist's output"*. That
is genuinely interesting where the tool is unknown.

**Here it is not unknown.** The exposure sheet has been the same
document for ninety years. This project has already written down its
vocabulary ([glossary](../glossary.md)) specifically so the code and the
craft use the same words. A tool generated fresh each session is harder
to trust, harder to test, and will drift from that vocabulary — and an
animator who cannot predict where the hold column is will stop using
it.

Build the x-sheet instrument once, properly, against the §13 schema.
Reserve dynamic generation for the places where the right control
genuinely is not known in advance.

## 7. Where the fast loop should not live: ComfyUI

ComfyUI is a batch graph executor. Submitting a graph, waiting for
scheduling, and collecting outputs is a poor fit for something that has
to answer inside a flip.

The architecture the note implies is therefore: **a local instrument
holding the x-sheet and the proxy frames, and ComfyUI behind it for the
slow synthesis.** That matches the split the note is arguing for, and
it means the fast path has no dependency on the ComfyUI packs at all —
only on registration, which must happen first either way.

## 8. What would test this cheaply

The corpus already contains the experiment, and it is the same one §7c
proposes.

Cleanups 1 and 3 are adjacent drawings; cleanup 2 is the inbetween the
artist drew. Generate a proxy between 1 and 3 and ask an animator to
judge the timing from the proxy alone. Two questions fall out
immediately:

* **Is the proxy legible enough to judge spacing?** — Daniel's
  threshold-capture memory predicts yes; §4.2 predicts flow methods
  ghost and double lines, which is a different failure from a coarse
  threshold and may read worse.
* **Does the proxy's spacing survive into the final?** — §5's timing
  contract, measured rather than assumed.

FrameFusion is 37 MB and runs on a CPU. This costs an afternoon and no
GPU time.

## Summary

| | |
|---|---|
| maps onto current work? | **yes** — the control surface is §13's exposure sheet, and the desk already lists the touchscreen for it |
| solves the latency finding? | **routes around it**, which is better than fixing it |
| biggest risk | not latency — **the proxy and the final disagreeing about spacing**, which makes approval meaningless |
| what already exists | the x-sheet schema, the spacing harness, the arbitrary-*t* interpolators |
| what does not | the instrument, registration at speed, and any evidence about proxy legibility |
| where I disagree | the instrument should be built once against a fixed schema, not generated per session |
