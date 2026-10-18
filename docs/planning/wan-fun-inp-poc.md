# Wan2.1-Fun-InP 1.3B proof of concept — findings

*2026-10-18. Runs the experiment
[pencil-test-architecture.md](pencil-test-architecture.md) §3 reserved
for "the option that changes the middle of the range", after
[rife-poc.md](rife-poc.md) found RIFE unusable on large displacement.*

## 1. What was asked

> *"It's an SLM, so I think we can feed a description along with the
> images. What else should we say besides 'Man running.'? Do we describe
> the style and the precise breakdowns we're looking for? I'd like to
> try an 'easy' version calculating the first (1\*) and third (2) rough
> images and seeing if we get something like the 2nd (1.5). The harder
> test is to inbetween from (1\*) to (6\*) with appropriate guidance."*

Both tests were run. The prompt question was run as a **matrix**, not
answered from theory — see §6, where the answer I had formed before
running anything turned out to be wrong in the half that mattered.

## 2. The model runs on this card

| | |
|---|---|
| weights | `alibaba-pai/Wan2.1-Fun-V1.1-1.3B-InP`, 19.0 GB, **Apache-2.0** |
| pieces | DiT 3.1 GB · umt5-xxl 11.4 GB · CLIP 4.8 GB · VAE 0.5 GB |
| runner | the **already-installed** `diffsynth` `WanVideoPipeline`, `input_image=` + `end_image=` |
| VRAM | peak well under the 23.4 GiB budget; no block swap, no bare-parameter patch |

**No new inference code was needed.** `config.json` gives `in_dim: 36`
and the state dict carries `img_emb.proj.*` and `cross_attn.{k,v}_img`,
i.e. 16 noisy + 4 mask + 16 reference channels plus CLIP cross-attention
— structurally identical to Wan2.1-I2V. diffsynth's `encode_image` sets
the mask to 1 at the **first and last** frame and zero between, which is
exactly Fun-InP's start-end formulation. That is the whole reason this
spike cost hours and not days, and it is the opposite of the
ToonComposer experience in §7b.

Throughput, 720×576, one 1.3B forward per step:

| frames | latent frames | s/step | 30 steps |
|---|---|---|---|
| 5 | 2 | ~2.6 | ~77 s |
| 9 | 3 | ~4.5 | ~120 s |
| 21 | 6 | ~13.8 | ~390 s |

Fast enough for a flip loop at the small frame counts, which §5 turns
out to be the only regime that works anyway.

## 3. The style holds with no style prompt at all

This is the headline, and it is the thing ToonComposer could not do.

Fed `"Man running."` — nothing about medium, paper or pencil — every
frame came back as **blue col-erase pencil line on white paper**, with
the paper grain, the ground lines and the construction lines intact. No
drift toward photographic or cinematic rendering across any of the
twelve runs.

The reason is structural, and it is why Fun-InP is a better fit here
than ToonComposer: ToonComposer **requires a colour frame** as input
(§4.3, corrected 2026-10-13), so it is always being asked to leave the
pencil. Fun-InP's conditioning *is* the two drawings, so the style has
nowhere to drift to.

**Consequence for the suite:** style language in the prompt is not
load-bearing. Do not spend prompt budget on it.

## 4. Easy test: rough 1 → rough 2, target 1.5

The artist's drawings in this corpus are numbered 1, 1.5, 2, 3 … 10; the
manifest records that they were *captured* in the order 3, 1, 1.5, 2, …
This is the fact that two earlier passes ignored, so it was read out of
`manifest.json` before any file was opened this time.

**Result: it works, at low frame counts.** At `num_frames=5` — exactly
three inbetweens, middle frame at *t*=0.5 — frame 2 is a clean, single,
coherent drawing: top hat, ear, eye, nose, bow tie, tailcoat, cane in
the right hand, both legs in a stride, ground lines underneath. No
duplicated limbs, no doubled figure, no detached parts.

Set against what RIFE did on this corpus — *"gen_04.png has two heads
and maybe 3 feet, gen_05.png has two bodies and three arms"* — this is a
different class of output.

**It is not the artist's 1.5, and it should not be read as one.** The
artist drew 1.5 larger and further right, mouth open, with the back leg
extended much further than any blend of 1 and 2 would put it. Fun-InP's
middle is a *plausible* inbetween; the artist's is a *chosen* one. That
is the same finding as the refuted ink centroid — the artist's middle
sits at mean fraction 0.427, sd 0.202, not 0.5 — arriving from a second
direction.

Frame 1 of 5 is visibly ghosted (two poses superimposed). Frames 2 and 3
are clean. So even in the good regime, **one frame in five is unusable**
and has to be detected or discarded.

## 5. Frame count is the dominant variable, not the prompt

The spike's most useful result, and it was not on the list of questions.

| keys | gap | N=5 | N=9 | N=21 |
|---|---|---|---|---|
| 1 → 2 | one drawing | **clean** | **clean** | middle collapses |
| 1 → 6 | half a cycle | ghosts, then jumps to the end pose | mediocre; ghosting from f004 | best available, still defective |

At `num_frames=21` on the *easy* pair, frames 6–16 lose the head and
hat, the body becomes a smear and the cane detaches and floats. The
sequence only snaps back to the end key in the last two frames.

The cause is not the crop, the resolution or the step count — all were
varied, and the failure tracked the frame count alone. Fun-InP was
trained on 81-frame clips at 16 fps. Asking for 21 frames between two
drawings that are **one drawing apart** tells the model there is most of
a second of motion to invent, and it duly invents it, ignoring both
keys. Asking for 5 tells it the truth.

**Consequence for the suite:** the generator must be driven at the
frame count the chart actually implies, not at the model's native 81.
This fits the dyadic subdivision driver in architecture §2 rather than
fighting it: subdivide down to adjacent drawings, then interpolate
short spans.

### 5a. End-frame adherence is weaker than start-frame adherence

Ink IoU against the conditioning images, easy pair, N=5:

| | IoU to start | IoU to end |
|---|---|---|
| frame 0 | **0.808** | 0.104 |
| frame 4 | 0.116 | **0.612** |

Neither key is reproduced exactly — the model **re-renders** both — and
the end key is reproduced markedly worse than the start. The start frame
gets CLIP features *and* the masked latent; the end frame gets only the
latent.

**Consequence:** the artist's own drawings must be composited back over
frames 0 and N−1. Never ship the model's version of a key.

## 6. The prompt question, answered by measurement

Four prompts were defined, each adding exactly one kind of information
so the responsible kind could be isolated:

- **A** `"Man running."`
- **B** style only (blue col-erase pencil, white paper, pencil test, no colour)
- **C** B + subject (top hat, tailcoat, bow tie, cane, profile, running right)
- **D** C + action (legs through a full run cycle, arms and cane in opposition)

**B was never run.** To keep the matrix inside the day's budget the easy
pair was run at A and C and the hard pair at A and D, so the isolated
effect of style language is inferred from §3 — the style holds under A,
which leaves B nothing to add — and not measured. If §3 is ever
doubted, B against A is the run that settles it.

Same seed, same keys, same frame count, same steps throughout:

**Before running these I had formed the answer that text conditioning
would control content and style but not timing, so style would matter
and action language would not. The second half is wrong.**

| | easy pair (1→2) | hard pair (1→6), N=21 |
|---|---|---|
| A vs C | near-identical; C slightly cleaner on the one ghosted frame | — |
| A vs D | — | **decisive** |

On the easy pair the prompt barely matters: the keys are close enough
that the conditioning determines everything. On the hard pair at N=21 it
is the difference between a usable sequence and a ruined one. With
`"Man running."` frames 8, 12 and 16 are headless smears with a floating
hat. With **D**, every frame keeps an intact figure — hat on head, face,
tailcoat, legs in a readable stride — across the whole span.

**The answer to "what else should we say":** name the **character and
its props**, and name the **action**. Skip the style (§3). The
mechanism is not timing control — it is that a sparse two-key
conditioning signal under-determines the figure, and the text supplies
the missing prior about what a figure *is*. The further the frame sits
from both keys, the more it leans on that prior, which is why the effect
is invisible on the easy pair and decisive on the hard one.

**Do not describe the precise breakdowns.** There is no mechanism by
which "favour the first key" or "the third inbetween should be at 3/8"
reaches the sampler; placement comes from the frame count and the
start/end conditioning, and nothing in the text path can move it. The
prompt is a description of *what is being drawn*, never of *when*.

## 7. Hard test: rough 1 → rough 6 — no configuration passes

Rough 1 and rough 6 are the two asterisked drawings and sit half a cycle
apart. The intervening drawings 1, 1.5, 2, 3, 4, 5, 6 fall at fractions
0, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0, so **N=21 is the smallest valid frame
count (N ≡ 1 mod 4) that puts all seven on exact integer frames**: 0, 2,
4, 8, 12, 16, 20. That is a real argument for N=21 here, and it collides
head-on with §5's finding that N=21 is where the middle collapses.

Best available result — prompt D, N=21 — keeps the figure intact
throughout, which the bare prompt does not. It still fails on two
counts:

1. **A spurious second cane.** The model gives the man a stick in each
   hand through the middle of the span. It has no concept that the one
   cane swings across; my own prompt phrase *"arms and cane swing in
   opposition"* probably encouraged the duplicate.
2. **It never finds the crouch.** The artist's 4 and 5 are deep,
   low, weight-bearing poses. Nothing in the generated span goes there.
   The model travels between the two keys along the shortest plausible
   path; the artist went somewhere else on purpose.

Point 2 is the one that matters, and it is not a tuning problem. **The
artist's half-cycle is not an interpolation of its endpoints.** No
two-key method recovers drawings 4 and 5 from 1 and 6, because the
information is not in 1 and 6.

**Consequence for the architecture:** a two-key inbetweener is an
instrument for *short* spans. Asking one to cross a half cycle is asking
it to animate, not to inbetween, and §1 of the architecture does not
want it to animate.

## 8. No failure detector yet — two more candidates refuted

The pencil test needs to flag its own bad frames, since one in five is
unusable even in the good regime. Two cheap candidates were tested
against frames already judged by eye:

| candidate | result |
|---|---|
| **ink fraction** ≈ 2× a key | catches **ghosting** (frames 1 and 19 of the bad N=21 run, 4.9–5.9% against a 3% key) but is **blind to hallucination** — the headless-smear frames sit at 2.4–3.1%, indistinguishable from a good key |
| **low IoU to both keys** | **refuted.** It flags the bad N=21 middle, but it equally flags the *good* N=9 middle, because a genuine inbetween is a new pose that resembles neither key. It measures novelty, not wrongness |

So the count stands at three refuted features — ink centroid, ink
fraction, IoU-to-keys — and no detector. Ink-density statistics cannot
see structure; this is the third time that has been demonstrated on this
corpus and it should now be treated as settled. The next candidate has
to be structural: connected-component topology, or a skeleton with a
limb count.

## 9. Standing against the architecture

| architecture §3 claim | status |
|---|---|
| Fun-InP "fits this card" | **confirmed** — runs, Apache-2.0, no patch needed |
| "no — emits N frames evenly" | **confirmed**, and N is now known to be load-bearing, not incidental |
| RIFE is lead candidate | **unsettled.** Fun-InP is markedly more legible at small gaps; RIFE is far faster and takes an arbitrary *t*. They are not yet compared head to head at matched gap |

## 10. Open

- Head-to-head Fun-InP vs RIFE on the same small gaps, same metrics.
- A structural failure detector (§8).
- Whether compositing the artist's keys over frames 0 and N−1 (§5a) is
  enough, or whether the re-rendered interior drifts in line weight too.
- Whether the spurious second cane survives dropping *"and cane"* from
  prompt D.
- Daniel's reading of the generated 1.5 against his own: is a plausible
  inbetween useful for approving a chart, or does only the chosen one
  count? This is §7c's question, now with a concrete pair to look at.

## 11. Artefacts

Out of tree, because WWC owns the originals and these derive from them:
`~/lab/storymator/spikes/wan-fun-inp-2026-10-18/` — montages, every
generated frame, the throwaway runner and the three run logs.
