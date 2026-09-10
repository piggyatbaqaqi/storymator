# What makes an inbetween unusable, and how a machine could know

*Response to Dr. Daniel Boulos, 2026-09-10. Written after parsing the
three attachments in full: `WorkingDic7_AnmCOmpEss.pdf` (the compiled
manuscript, ~117 000 characters), `the7principles_ThisOne_June2015.docx`
and `THeANimatorsToolbox_Chapter 3.docx`.*

*Amends [inbetweening-scope.md](inbetweening-scope.md), whose A/B framing
Daniel's reply corrects. Governing document:
[the coarse scoping](../README.md).*

---

## 1. The correction, and why it matters

The scope note offered two answers and treated them as a fork. Daniel's
reply:

> it is much more along the lines of B but i feel the answer will lie
> within A in terms of calculating pixels not vectors

That is not a compromise between the two — it is a repair of a mistake
in how they were posed. **The note bundled two independent axes into
one choice:**

| axis | the question | the note's error |
|---|---|---|
| **Fidelity target** | plausible footage, or the drawing an assistant would have made? | assumed |
| **Representation** | pixels, or vectors? | conflated with the above |

I had assumed that wanting an assistant's drawing meant wanting stroke
correspondence, and so vectors. Daniel is asking for **B's fidelity on
A's substrate**: the drawing has to be right, and the way to get there
runs through pixels, not through interpolating control points.

The manuscript explains why that is not a preference but a consequence.
Reversal of Curves is about the *gesture line* — "the hidden line
representing the graceful connection between the forms in a figure",
which is explicitly **not a drawn line at all**. A representation whose
primitives are the strokes on the page has no place to put the most
important line in the pose. Vectors can only interpolate what was
inked. The thing that has to survive an inbetween is partly invisible.

So: pixels. And the burden that moves onto the pixel side is that the
result must satisfy criteria vector systems never even attempted.

---

## 2. The seven principles as a specification

Daniel's proposal is that "once the AI is instantiated the AI must be
trained on the local definition of all these rules," and notes that the
rule set is local — seven principles distilled over twenty years of
teaching, against Fred Moore's fourteen points as passed through Thomas
and Johnston, which "conflates drawing and scene composition principles
within other principles of motion and performance."

**Training is one use of the rules. Testing is the other, and it is
available sooner, is cheaper, and is what the project currently lacks
entirely.**

Several of the seven are *measurable on a finished drawing sequence*.
That turns "what makes an inbetween unusable" from a matter of taste
into a harness that can reject a candidate and say which principle it
violated. Going through all seven, in the manuscript's own order:

| # | Principle | Machine-checkable? | The measurement |
|---|---|---|---|
| 1 | **Arcs** | **Strongly** | Track a feature — centre of mass in a wide shot, hand or head in a medium — across key → inbetween → key. The manuscript's definition is already a geometric predicate: *"no part of the move would be on a purely straight line"* and *"sharp angles must be avoided"*. Fit an arc through the neighbouring keys; measure the inbetween's deviation from it, and the interior angle at the inbetween. A straight three-point path or a corner is a rejection. |
| 2 | **Timing** | **Exactly** | The timing chart *is* the specification. A one-half inbetween must land at 0.5 of the way along the path; Daniel's failure case — ".5 progression as a .3" — is a scalar error, reportable to two decimal places. |
| 3 | **Squash & stretch** | **Partly** | Track a form's area and aspect ratio through the sequence. *Absence* is far more detectable than correctness: a form whose proportions are rigid through an impact has failed, whatever the right amount would have been. Note the manuscript's scale rule — interior shape change matters in close-up, whole-body contour at distance — so the check is shot-size dependent. |
| 4 | **Reversal of curves** | **Partly, per scene** | The gesture line is a single dominant curve, "most often purely concave or convex". Ollie Johnston's rule as passed through Glen Keane — *"reverse this line at least once in any scene of animation"* — is a literal assertion about the sign of curvature over a scene. It is a property of the keys rather than of any one inbetween, so it audits the animator's plan, not the machine's output. |
| 5 | **Successive breaking of joints** | **Strongly — and this is the sharp one** | See below. |
| 6 | **Secondary motion** | Weakly | Requires knowing which motion is primary. The model-sheet tags Daniel proposes could supply that decomposition. Also the place where, in the manuscript's words, *"the acting is"* — so the least appropriate thing to automate. |
| 7 | **Overlapping action** | Out of scope | The manuscript is explicit that 2D animators *"apply overlapping motion after all the other elements of their scene are finished and all the inbetweens added."* It happens downstream of inbetweening and should not be the inbetweener's problem. |

### Why successive breaking of joints is the decisive test

The manuscript already contains the argument against naive inbetweening,
written a decade before this project, in Richard Williams's unfolding
box:

> Imagine for a moment animating this in 3D animation software using
> digital keyframes. If those were the only two keyframes that were set,
> your software would evenly inbetween the result. Essentially the three
> right angles would open from 90 degrees to 180 degrees simultaneously.
> The audience would perceive the box opening but would find watching it
> in motion a stiff and unnatural experience.

**Simultaneous onset is the signature of interpolation.** It is also
computable: given a joint decomposition, measure when each joint's
change begins and ends, and assert that each starts before the previous
finishes. Williams's correct version — first flap moves, second begins
before the first finishes, third before the second — is a set of
inequalities over onset times.

This gives the project a single number that separates *an inbetween*
from *an interpolation*, on the exact case Daniel raises with the
unfolding hand. It is worth building first, because every generative
approach will fail it in the same characteristic way and the failure
will be legible rather than a matter of opinion.

---

## 3. The formula problem, and the division of labour it implies

The manuscript is blunt:

> The use of formulas to determine timing is a nail in the coffin of
> character animation. […] No one does a "walk on 12's" or a "run on
> 6's" in their daily life. […] Avoid formula like the plague!

An automatic inbetweener is, by construction, a formula. That looks like
a contradiction at the heart of the project. It dissolves once you
notice **where** the manuscript locates the danger: in *timing*. And
timing is precisely the thing the artist already supplies, on the
drawing, in the chart.

That yields a hard architectural rule:

> **The system must never infer timing. It reads the chart and obeys
> it.**

And from that, a division of labour:

| | owns |
|---|---|
| **Artist** | keys, breakdowns, timing charts, the arcs implied by the keys, the performance |
| **Machine** | the drawn form at a *specified* fraction along a *specified* path |

This is not a novel arrangement. It is the historical studio hierarchy —
animator, breakdown artist, inbetweener — reproduced exactly. The
machine occupies the junior seat, which is where the formula risk was
always contained, because an inbetweener was never the one choosing the
timing.

It also reconciles the project with the manuscript's closing note, which
is worth quoting since it is the last word Daniel leaves the reader:

> Technical mastery of animation principles as a means to enter into
> meaningful emotional connections with the audience […] can never be
> effectively replaced through any digital device. Indeed, such mastery
> protects the modern animator from being automated out of their
> profession.

Nothing above contradicts that. The mastery sits with whoever draws the
keys and writes the charts, and this system is built to require both.

---

## 4. On the 3D lattice proposal

Daniel's second artery — the one they say "earns the wages" — is the
complex form undergoing change: the half-unfolded hand, whose correct
line depends on the vantage point of the audience, so that "the actual
line in formation is unique based on the proposition of the form
undergoing change."

Their proposal: the system fabricates a 3D lattice on demand, poses it
half-open in xyz, and uses it as a *guide* for the line treatment.
Supported by model sheets carrying an agreed anatomical tag — "human
hand", "bird's wing primary secondary tertiary feathers and bone
structure".

**I think this is right, and the crucial word is *guide*.** The lattice
is never rendered. It constrains where forms sit in depth and how they
occlude; the drawing is still synthesised in 2D. That is what keeps it
clear of the stiffness Daniel criticises in CG, where the deformation
*is* the output and inherits every limitation of whoever built the rig.

Three things worth knowing before the proposal is written up:

**The anatomical tags map onto existing parametric models.** "Human
hand" in particular: parametric hand models with exactly the
joint-angle parameterisation the half-unfolded case needs are mature and
widely used. Bodies likewise. So a tag vocabulary starting at
*hand / head / generic limb* has something real behind it rather than
needing to be built from nothing.

**The risk is that the lattice reintroduces the rigging dependency.** If
the lattice is generic, the guide is generic, and the result is the
stiffness the whole design is trying to avoid. The mitigation is
structural: **fit the lattice to the artist's own two keys**, not to a
canonical model. Then it inherits the artist's construction and
proportions rather than a rigger's, and the tag only supplies the
*topology* — which parts hinge on which — rather than the shape.

**The novelty claim should be checked, not asserted.** Daniel says "as
far as i know does not exist yet", and the meeting notes mention SBIR.
I have not done a prior-art search and I am not going to claim
originality on the strength of not having seen something. What I can say
is that the components exist separately and the *composition* —
on-demand lattice fabrication, tagged from a model sheet, used as a
drawing guide rather than a render target, inside a 2D inbetweening
pipeline — is not something I can point to. Before that goes in a
proposal it deserves a real search, and that is cheap to do.

---

## 5. What this changes about the immediate plan

Monte's read stands — the pencil test is the first priority, and
registered capture comes before generation. Daniel's reply adds two
reasons that were not in the earlier note:

**Capture is a prerequisite for evaluation, not just for generation.**
Every measurement in §2 — arc deviation, spacing fraction, joint onset
order — is taken in a shared coordinate system across successive
drawings. Without sub-pixel registration there is no harness, and
without a harness there is no way to know whether any generative
approach is working. Registration was already first; it is now first for
two independent reasons.

**The capture pipeline must read the timing chart.** The chart lives on
the drawing, usually in the upper right corner, as horizontal marks
between two bars. If the chart is the specification — and §3 says it is
— then capturing the chart *is* capturing the specification, and it is
not an optional extra. This is a concrete addition to the capture scope:
detect the chart region, read the marks, recover the fractions.

**One useful confirmation from the manuscript** for the registration
work already underway: the lingo section defines pegs as *"the two
oblong and one round pegs that protrude upward from an animators
peg-bar."* Two oblong plus one round, at fixed spacing, is a known rigid
geometry — which is what makes fitting it (rather than blob-detecting
it) the robust approach.

### Suggested first milestone, restated

Unchanged in shape, sharper in content:

*Deliverable* — from photographs of a pegged stack: clean
background-free line art in a common coordinate system, **plus the
timing chart read off each key**.

*Judged by* — registration residual in pixels on real drawings, and
chart-reading accuracy against the animator's own reading.

*Then, and only then* — the rejection harness of §2, measured against
whatever generates candidates, including deliberately bad candidates.

---

## 6. Where I would push back, gently

Daniel expects off-the-shelf solutions to have little to offer beyond
existing vector interpolation. I mostly agree, with one caveat about
sequencing rather than about the conclusion.

**Run the off-the-shelf baseline anyway, in order to fail it.** The
harness of §2 needs something to measure before it can be trusted, and a
measured failure — *"the generative baseline reproduces the specified
spacing to ±0.18, and opens all joints simultaneously in 9 of 10
cases"* — is worth considerably more than the same claim asserted. It
calibrates the instrument, it costs very little, and in a funding
context a number beats a conviction.

If it turns out to do better than expected on some class of shot, that
is worth knowing too, and it is cheaper to find out now than after a
year of building.

---

## 7. Questions back

1. **Is there paired data?** Keys and breakdowns together with the
   inbetweens an assistant actually drew, from any past production. This
   is the single highest-value asset for both training and evaluation,
   and nothing else substitutes for it. Even a few scenes.

2. **Per principle, what is the pencil-test floor?** A pencil test is
   diagnostic, so some degradation is fine. Which of the seven must be
   *right* for the test to be readable, and which can be approximate?
   My guess is that arcs and spacing must be right, squash and stretch
   can be crude, and reversal of curves does not apply at inbetween
   level at all — but that is a guess, and it sets the whole quality
   bar.

3. **How large is the tag vocabulary at the start?** Beginning with
   hand, head and generic limb is tractable. Bird's-wing feather groups
   are considerably harder. Where is the useful floor?

4. **A trick that may become a feature.** The manuscript describes
   *tracebacks*: a held drawing traced three or four times, where "the
   line variation from one drawing to another keeps a certain amount of
   life in the pose" — and notes that digital paint lost this, since
   "there is no variation as one might find from one painted cel to the
   next." A generative model that redraws with slight variation
   reproduces exactly that quality for free. It is a defect for
   inbetweens and arguably a virtue for holds. Is that worth anything,
   or has the moving hold made tracebacks obsolete?

---

## Appendix: the seven principles, as this project will use them

Recorded so the "local definition" is written down in one place and can
be cited by the code.

**The Big 3**
1. **Arcs** — everything in nature moves on a curved path. Straight
   lines and sharp direction changes read as mechanical. Wide shot: the
   arc of the centre of mass. Medium: arms and hands, more subtly the
   head.
2. **Timing** — timing is spacing. Four basic choices: stopped,
   constant, slowing (slow-in), speeding up (slow-out). Notated by the
   timing chart. Formula is fatal.
3. **Squash and stretch** — "animation is shape change". Internal at
   close range, whole-body contour at distance. Key word: contrast.
   Applied even where life does not exhibit it.

**The Lesser Known Gems**
4. **Reversal of curves** — the gesture line, the hidden connecting
   curve, should reverse at least once in a scene. *(Glen Keane, from
   Ollie Johnston.)*
5. **Successive breaking of joints** — a force ripples outward through a
   chain of joints; each begins before the previous finishes. Never all
   at once. *(Richard Williams, from Art Babbit.)*

**An Important Distinction**
6. **Secondary motion** — a non-primary motion with the power to move
   itself. Where the acting is.
7. **Overlapping action** — motion generated by a force other than
   itself; added after the inbetweens are done.

**Animation tricks** (novelties of a stack of drawings played in rapid
succession, distinct from the principles): cycles, drag, go-beyond-and-
settle-back, anticipation, blurs and distortions, multiple images,
vibrations, held cels, tracebacks, moving holds, pure illusion.

**Vocabulary**, as the manuscript fixes it — the code should use these
words and no others: *key pose* (storytelling anchor; rarely more than
two per second), *extreme* (contains the outer motion of an element),
*breakdown* (a frame between keys containing an extreme), *inbetween*
(everything remaining between breakdowns and keys), *slow-in*,
*slow-out*, *feet* (16 frames of 35 mm; 3 feet = 2 seconds), *pegs*.
