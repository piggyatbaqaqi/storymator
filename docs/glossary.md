# Glossary

The project's vocabulary, in one place so the code can cite it.

The rule comes from [planning/inbetween-acceptance.md](planning/inbetween-acceptance.md):
**the code should use these words and no others.** That rule has been
breached twice by writing this documentation, both times caught by a
human reading carefully, which is why it is worth having a register
rather than a habit.

**Every entry names its source**, because the difference matters. A term
Daniel's manuscript fixes is binding on this project in a way that a
general industry usage is not, and a convention this repository invented
is binding on nobody but us.

| source | means |
|---|---|
| **manuscript** | Boulos, *The Animator's Toolbox* (`boulos2015toolbox`) — the project's authority |
| **Wikipedia** | quoted, CC-BY-SA-4.0, attributed in place |
| **this repo** | measured or decided here; the entry says where |
| **in conversation** | stated by Daniel or Monte, dated |
| **general usage** | current in the craft, but not fixed by any of the above — treat as weaker |

---

## 1. The drawings

**cel** — *Wikipedia.*

> A cel, short for celluloid, is a transparent sheet on which objects are
> drawn or painted for traditional, classical, hand-drawn animation.
>
> — [Cel](https://en.wikipedia.org/wiki/Cel), Wikipedia, CC-BY-SA-4.0,
> retrieved 2026-10-14.

Characters are painted on cels and laid over a static background, so a
frame is a *stack* of cels and the stacking order matters. Digital ink
and paint made physical cels obsolete — Disney's CAPS replaced them in
1990 — but the exposure sheet still numbers its layers in cels, so the
word survives the material.

**It is never "cell".** Monte, *in conversation*, 2026-10-13: *"There is
no such thing as a 'cell' in animation."* See §5.

**rough** — *general usage.* The first drawing of a pose, carrying
construction and search lines. In this project's corpus the roughs are in
blue pencil; see [planning/inking-and-tween-plugins.md](planning/inking-and-tween-plugins.md) §12.

**cleanup** — *general usage, and the governing document's own word*
(*"cleanup, paint and compositing"*). The drawing redrawn as a single
confident line, on model. In the corpus the cleanups are graphite, traced
in register over the roughs.

**tie-down** — *general usage.* A rough already tightened most of the way
to cleanup. Noted because the corpus's roughs read as tie-downs rather
than as construction-line roughs, which makes them an *easier* cleanup
problem than the general case — an observation of this project's, not a
label the artist applied.

**key pose** — *manuscript.* The storytelling anchor; rarely more than
two per second.

**extreme** — *manuscript.* Contains the outer motion of an element.

**breakdown** — *manuscript.* A frame between keys containing an extreme.

**inbetween** — *manuscript.* Everything remaining between breakdowns and
keys.

**pencil test** — *governing document.* The drawings shot and played at
speed to judge whether the movement reads. Diagnostic, not deliverable —
which is what sets this project's fidelity bar: rough is fine, wrong is
not.

---

## 2. Timing

**timing chart** — *manuscript.* Marks between two bars, usually in the
upper right of the drawing, giving **where a drawing sits along the
path** between its neighbours. Spatial. The chart *is* the specification:
the system reads it and obeys it, and never infers it.

**exposure sheet** (*X-sheet*, *dope sheet*) — *general usage; structure
fixed by Monte in conversation, 2026-10-13.* The production document
giving **which drawing is exposed on which frame**, per layer, with
dialogue, sound and camera. Temporal.

**The chart and the sheet are different documents** and neither derives
from the other — see [planning/inking-and-tween-plugins.md](planning/inking-and-tween-plugins.md)
§13. A drawing's *number* is a name, not a position: "1.5" says it was
inserted between 1 and 2, not that it sits halfway.

**frame** — one exposure, 1/24 s at this project's rate. **Not a
synonym for *drawing*:** a drawing held for three frames is one drawing
and three frames. The exposure sheet exists precisely to map one onto the
other.

**slow-in**, **slow-out** — *manuscript.* Two of timing's four basic
choices, the others being stopped and constant.

**feet** — *manuscript.* 16 frames of 35 mm; 3 feet = 2 seconds.

**hold** — a drawing exposed on successive frames. A **moving hold**
keeps a slight drift so the image does not die on screen.

**traceback** — *manuscript.* A held drawing traced three or four times
rather than exposed twice, so line variation keeps the pose alive.
Digital paint lost this, *"there is no variation as one might find from
one painted cel to the next."*

**cycle** — a run of drawings that repeats. The corpus is a run cycle.

Other tricks the manuscript enumerates, distinct from the seven
principles: drag, go-beyond-and-settle-back, anticipation, blurs and
distortions, multiple images, vibrations, pure illusion.

---

## 3. The page and the camera

**pegs** — *manuscript.* *"The two oblong and one round pegs that
protrude upward from an animator's peg-bar."* Two oblong plus one round
at fixed spacing is a known rigid geometry, which is what makes fitting
them robust rather than blob-detecting them.

**ACME** — the peg standard this project uses. Nominal centre spacing
4.0000 in; **the bar this project measured is 4.0624 in**
([data/calibration/pegs/honbay_0001](../data/calibration/pegs/honbay_0001/README.md),
*this repo*), manufacturer's spacing rather than a bend. Do not trust the
nominal on a real rig.

**field**, **field size** — *general usage.* The camera's shooting area.
**A field size is a width** in field units: "12 field" names a rectangle
12 units wide. It does **not** name a height.

**aspect ratio** — *general usage; raised by Monte in conversation,
2026-10-13.* What supplies the height a field size does not. 12F at 4:3,
at Academy and at 16:9 are three different rectangles sharing a width.
**Record the number, not the nickname:** the standard chart is Academy
**1.37:1**, universally called 4:3, but 4:3 is 1.3333 and the difference
is 2.7 % of the height.

**field centre** — fixed relative to the **peg bar**, not to the sheet
edges, which is why a sheet trimmed off-square still shoots true and why
cropping a true field requires locating the pegs first.

**`12F/`, `10F/`** — *this repo, and a caution.* The two directories of
the ManRunCycle corpus. They are field *names*, not frame counts. But
`10F/` is produced by keeping the central 10/12 of **both** dimensions,
so it inherits the paper's aspect (1.4232 — not 4:3, not Academy, not
16:9) and is 13.7–13.9 inches wide. **It is a paper crop, not a camera
field**, and the name over-promises. See
[planning/inking-and-tween-plugins.md](planning/inking-and-tween-plugins.md)
§13.4.

**registration** — bringing successive drawings into one coordinate
system. Everything downstream assumes it.

---

## 4. The seven principles

Enumerated with the manuscript's own definitions, and their attributions,
in [planning/inbetween-acceptance.md](planning/inbetween-acceptance.md) —
appendix. Named here only so the glossary is a complete index: arcs,
timing, squash and stretch, reversal of curves, successive breaking of
joints, secondary motion, overlapping action.

Two attributions the manuscript is careful about, and so should we be:
**reversal of curves** reached Daniel from Glen Keane, who had it from
Ollie Johnston; **successive breaking of joints** from Richard Williams,
who credited Art Babbit.

---

## 5. Words we do not use

| not this | but this | why |
|---|---|---|
| cell | **cel** | *"There is no such thing as a 'cell' in animation"* — Monte, 2026-10-13. The repository's other uses of "cell" are correct and stay: *cell phone* in the capture lighting notes, and grid or mesh cells in the calibration and sheet-flattening maths. Those are not animation terms. |
| frame (for a drawing) | **drawing** | A hold is one drawing on several frames. |
| field size alone (for a rectangle) | **field size + aspect ratio** | A width is not a shape. |
