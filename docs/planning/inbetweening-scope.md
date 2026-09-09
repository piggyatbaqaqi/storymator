# Two kinds of inbetween

*Scoping note for the automatic-inbetweening project. Drafted
2026-09-09 for discussion with Dr. Daniel Boulos.*

> **Revised the same day, after reading the coarse-scoping document**
> ([docs/README.md](../README.md)). It answers more of this than the
> first draft assumed — see *What the coarse scoping already settles*
> below. The A/B fork still frames the decision, but the governing
> document has already ruled out one arm of it.

## The question that decides the architecture

Everything downstream — which models, which training data, what
"working" means, how long it takes — turns on one question that has
not been settled:

> **When the machine produces an inbetween, what has to be true of it
> for the studio to use it?**

There are two coherent answers. They are not points on a spectrum;
they are different products with different engineering.

### A — a plausible moving shot

Two drawings go in, motion comes out. The output is judged as
*footage*: does the movement read, does it hold up at speed.

* **Exists today.** ToonCrafter, via `ComfyUI-ToonCrafter` or Kijai's
  DynamiCrafterWrapper. Weeks, not months, to a working demo.
* **It re-draws rather than tweens.** The model synthesises pixels; it
  has no notion of "the same line, moved". Characters drift off model,
  and detail that matters (a specific eyelash, a costume seam) is
  reinvented frame to frame.
* **Timing is not an input.** An animator's chart — the spacing that
  makes a movement ease in, snap, or float — has nowhere to go. You
  get the model's idea of pacing.

### B — the drawing an assistant would have made

The output is judged as *artwork*: is it on model, is it on the
chart, could it go in the stack without anyone noticing.

* **No off-the-shelf solution.** This needs stroke correspondence —
  knowing that *this* line in drawing 1 becomes *that* line in
  drawing 2 — which is a research problem, not an install.
* **It respects the craft.** Timing charts become a real control.
  Line identity is preserved because lines, not pixels, are the unit.
* **It breaks where animation is hardest.** Occlusion, and any change
  in topology — a hand closing, a head turning through three-quarter —
  are exactly the cases correspondence methods fail, and exactly the
  drawings an assistant earns their wage on.

**The honest summary:** A is buildable now and may not be useful. B is
useful and may not be buildable. Which one is worth doing depends on
what the studio would actually accept.

## What the coarse scoping already settles

Two user stories in the governing document answer more than the first
draft of this note assumed.

> *"Artist draws two successive poses on paper. AI automatically
> inbetweens a **pencil test**."*

A pencil test is diagnostic, not deliverable — you shoot the drawings,
play them at speed, and judge whether the movement reads. So the output
is **disposable**, which sounds like it favours A.

It does not, because of the second story:

> *"Interpret timing information from **thumbnails**."*

Timing is meant to be an **input**, taken from the artist's own
thumbnails. That is precisely what A cannot accept: a generative
image-to-video model has nowhere to put a chart, and supplies its own
pacing.

And the diagnostic purpose imposes a fidelity floor that A also fails.
A pencil test is only useful if it tests *your* drawings. If the model
re-draws the character off model, what plays back is the model's
motion, not the motion your two poses imply — which makes it useless
for the one job it has.

**So the target is neither A nor B as drawn above.** It is B's fidelity
requirement — the artist's own lines, the artist's own timing — at A's
disposability: rough is fine, wrong is not. That is a *lower* bar than
final art and a *higher* one than plausible footage, and it is the bar
the desk document actually asks for.

The remaining question for Dr. Boulos is therefore not "final or
rough" but **how much line degradation still leaves a pencil test
readable** — which is an empirical question an animator can answer by
looking at examples, and probably faster than any amount of discussion.

## What is worth building either way

**The capture pipeline.** Camera → deskew → registration → paper
removal → clean line art, frame to frame.

Both answers need it. It is ordinary computer vision rather than
research, so it can be estimated honestly. And it is worth something
on its own even if the inbetweening never ships: it turns a stack of
paper into a registered digital sequence, which is a drawing-desk
digitiser.

**Registration is the whole problem.** Everything downstream — onion
skinning, correspondence, any model — assumes frame *n* and frame
*n+1* are in the same coordinate system. Paper on pegs under a
hand-held or desk-mounted camera is not. Get sub-pixel registration
and the rest is tractable; skip it and every later stage inherits the
drift.

Work started on peg-bar detection on 2026-09-09.

## Questions for Dr. Boulos

1. **The acceptance test.** Show an assistant animator a machine
   inbetween. What makes them reject it? That answer *is* the success
   criterion, and it decides A or B.
2. **How rough can a pencil test be and still do its job?** The desk
   document settles that the output is a pencil test, not final art.
   What it does not settle is the fidelity floor: how much line
   degradation still lets you judge the movement honestly? Best
   answered by showing examples rather than by discussion.
3. **The physical rig.** Acme pegs? Camera fixed above a disc, or
   hand-held? Backlit on a light table, or top-lit? Each answer
   changes the capture code substantially.
4. **Volume and spacing.** How many drawings per second of finished
   animation, and how wide are the gaps an assistant normally fills —
   one inbetween, or a run of five?
5. **What this is meant to relieve.** Is there a real production
   behind this with a real bottleneck, or is it exploratory? That sets
   how much roughness is tolerable.

## Recommended first milestone

**Registered capture, measured on Wiki Wiki's own drawings.**

*Deliverable:* given photographs of a pegged stack, produce clean,
background-free line art in a common coordinate system.

*How it is judged:* registration residual in pixels, on real drawings
from a real scene — not on synthetic tests.

*Why first:* it is required by both A and B, it is estimable, it fails
loudly rather than subtly, and it is the one piece that keeps its
value whichever way the question above is answered.

**What not to do first:** pick a model. Both branches demo well on a
cherry-picked pair of drawings, and neither demo tells you which one
the studio can use.
