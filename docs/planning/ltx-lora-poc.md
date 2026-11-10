# LTX-2.5 character LoRA proof of concept — findings

*2026-11-07 to 2026-11-10. A LoRA on LTX-2.5 22B distilled, trained on
the twelve cleanups of `manrun_cycle_2001_wwc`, judged by the motion
procedure of [pencil-test-architecture.md](pencil-test-architecture.md)
§3 and the earlier spikes ([rife-poc.md](rife-poc.md),
[wan-fun-inp-poc.md](wan-fun-inp-poc.md)). Day-by-day record:
[ltx-zoet-lora-todo.md](ltx-zoet-lora-todo.md).*

## 1. What was asked

The operator wanted LTX to know Dr. Boulos's run-cycle character, and
asked whether to caption each drawing or build an ffmpeg sequence. If
the result is good, Dr. Boulos is asked for more drawings of the
character. The character's working name was *Zoephan*; the stock model
draws an elephant for it, so the trigger became **Zoet**, and on
2026-11-10 the character took that name too.

Later in the run the operator added two questions: does dropping "on
white paper" from the captions remove a paper prop, and does the LoRA
work as an inbetweener when Dr. Boulos's drawings are pinned as
keyframes?

## 2. Does it run here

| | |
|---|---|
| base | LTX-2.5 22B **distilled** transformer, Gemma 4 12B text encoder, video VAE — LTX Desktop's split pack |
| licence | code Apache-2.0; weights under the **LTX-2.x Community License**, accepted 2026-11-07 ([LICENSES.md](../../LICENSES.md)) |
| trainer | `Lightricks/LTX-2` monorepo `packages/ltx-trainer` at `4f52161`, unmodified; LoRA rank 16 on `to_{q,k,v,out.0}` |
| local card | trains only at **int4**, with two launcher patches: 21.7 GB peak, **~2.4 min/step**; the final save then OOMs |
| rented | Modal H100 80 GB, bf16, no patches: **0.62 s/still step, 1.17 s/clip step**, 44 GB peak; ~$1.35 per 1000 steps |
| renderer | `ltx_pipelines.distilled`, the trainer's checkpoints loaded as `--lora` unchanged (ComfyUI key prefix); ~1.5 min per 49-frame clip on the H100 |

Gradient checkpointing must stay on even at 80 GB: without it the first
clip step OOMs. The A100 80GB is 2.6× slower per clip step, so despite
its lower hourly rate it costs more per run (~$2.10 against ~$1.35 per
1000 steps): the H100 is the better-value card. Modal spend across the proof of concept: about $17.

**Dataset.** The twelve drawings, cleaned of sheet marks by
connected-component removal (each removal checked by eye), as twelve
1184×832 stills and twelve 25-frame clips: the cycle on twos at 24 fps,
starting from each drawing in turn. Captions name the pose phase, feet,
hands, hat, cane, coat tails and cuffs, and leave identity to the
trigger. To the operator's ffmpeg-or-captions question the answer was
**both**, compared as separate training arms (§3).

## 3. Stills beat clips

Three 2000-step arms with the same recipe, seeds and prompts:
stills only, clips only, and both mixed.

| arm | wall | text only | drawing 1 as first frame |
|---|---|---|---|
| stills | 23 min | hat, coat, fists; no cane | **stays on model through 48 frames** |
| mixed | 36 min | faint ghost | faint and smeared after frame 0 |
| clips | 45 min | never learns the hat\* | faintest, smears mid-clip\* |

\* Clips was dropped on its trainer samples and never rendered in the
real pipeline; its row is the trainer's view. The other two rows are
from `ltx_pipelines.distilled`.

In the trainer's own samples mixed drew the best text-only character,
but in the real pipeline it was the faintest, so **the trainer's
validation can rank arms only roughly**. It samples like the dev model (a sigma schedule
with CFG and STG), and the checkpoint is the distilled one. Every
judgement below comes from `ltx_pipelines.distilled`, with the
stock-model baseline's settings: fp8-cast, 1088×768, 49 frames, seed 42.

**More steps did not help.** Stills checkpoints at 1000, 1750 and 2000
are hard to tell apart. The operator's pick from the trainer's samples
was stills at step 1750.

**The LoRA loads and does something.** From the same Zoet prompt the
stock model draws a bald generic man, and every stills checkpoint draws
the top-hatted character.

## 4. It learned the look, not the acting

Judged by motion: a band of every frame around the feet, set against Dr.
Boulos's drawings on twos at the same frame times.

With drawing 1 as the first frame, the stills LoRA keeps the character
coherent. The feet do pass through contact, passing and up in order,
smeared in a few frames. But:

- the stride is **the stock model's rhythm**, a step every ~9.6 frames
  against the drawings' 12;
- there is **no crouch** on the down poses (drawings 5 and 11);
- the **hat never lifts**, and the **cane stays upright**.

Those three are what make this cycle Dr. Boulos's rather than a generic
run, and none of them came through. Twelve drawings taught the
character's appearance and nothing of his acting. The operator saw the
same from the trainer's samples: *"The floating hat and the mid-step
crouch are both lost."*

## 5. The paper prop is not in the captions

In the trainer's validation, the stills LoRA's text-only samples put a
sheet of paper in the figure's hands. The obvious source was the style
sentence's "on white paper", so stills was retrained without it.

**Refuted.** The retrained LoRA's validation samples still hold the
sheet from step 750, and in the real pipeline the prop never appeared,
with or without the phrase. The only change was a cost: text-only
renders lost the top hat at steps 1000 and 1750.

A hypothesis, untested: the validation prompt's "each drawing **held**
for two frames" comes only from the clip captions, so the stills LoRA
never saw it there. Mixed did see it, and never drew the prop. This
only matters for the trainer's samples, not for real use.

## 6. As an inbetweener: keys are hit, not reached

Drawings 1, 5 and 11 were pinned as keyframes at their on-twos frames:
0, 8 and 20. This set is *k3*; *k6* repeats it one cycle later, at 24,
32 and 44. Each set was rendered with the stills step-1750 LoRA and
with the stock model. Frame 0 replaces the first latent; the later keys
guide at strength 1.0.

- **The keys appear on time**, the crouch and the floating hat
  included. That was not possible without them.
- **They are reached through a burst of scribble and left by a
  dissolve**, not by travel: k3 frames 6–7 and 17–18 in, 9–11 and
  22–23 out. Between keys the figure goes back to a pose like drawing 1
  instead of running on through drawings 6–10.
- **With a key every cycle, both models jump and hold** — the failure
  that has sunk every candidate so far. The stock model holds each pose
  for three frames. The LoRA holds drawing 11 for seven frames (15–21)
  and brings the second crouch in eight frames before its key.
- **The LoRA does not help.** It hits the keys no better than stock,
  and stock's approach into drawing 5 (frames 4–8) is the cleaner one.

Not varied: guide strength, the seed, and the prompt's "each drawing
held for two frames", which may itself invite holds.

## 7. What is refuted

- *The trainer's validation samples judge the arms.* They rank them
  only roughly: mixed's text-only lead there became last place in the
  real pipeline.
- *"On white paper" causes the prop* (§5).
- *A character LoRA makes LTX a better inbetweener of that character's
  drawings* (§6).
- *More steps would bring the acting in.* Steps 1000 to 2000 look alike.
- *The plan's recipe, mixed stills and clips, is the one to train.* It
  was planned because clips carry the motion. Neither clip arm learned
  any motion, and both drew more faintly than stills.

## 8. Standing against the architecture

| claim | standing |
|---|---|
| A rented 80 GB GPU makes LTX LoRA training cheap | **confirmed** — minutes and single-digit dollars per run |
| LTX can learn the character from twelve drawings | **confirmed for appearance**, from stills |
| LTX can learn the character's motion from twelve drawings | **refuted** at this dataset size |
| LTX keyframes inbetween Dr. Boulos's drawings | **refuted** for k3 and k6 at one seed: jump and hold, or a dissolve through scribble |
| More drawings from Dr. Boulos would close the acting gap | **unsettled**; a model sheet teaches appearance, which is already learned, so what would help is more *actions* |

## 9. Open

- **Load check in LTX Desktop.** Desktop is said to skip a mismatched
  LoRA silently. The renders prove the LoRA loads in
  `ltx_pipelines.distilled`, not in Desktop. The step-1750 LoRA is
  installed at Desktop's `models/loras/zoet/` and needs one with/without
  pair from the UI.
- Guide strength below 1.0, and the prompt without "held", for keyframe
  inbetweening.
- Whether stills-only plus a handful of *other actions* from Dr. Boulos
  teaches acting, or whether acting needs a model built to inbetween.

## 10. Artefacts

Out of tree, unpublished (the art is Wiki Wiki Cartoons'):
`~/lab/storymator/spikes/ltx-lora-2026-11-07/`:

- `baseline/`: the stock model.
- `compare/`: trainer validation sheets for the three arms and no-paper.
- `renders/`: real-pipeline mp4s, plus per-render figure, feet and hat
  montages from `montage_render.sh`, and the overviews.
- `runs/`: every log and the Modal bills.
- `modal/bench.py`: the throwaway runner.

The LoRA checkpoints are on the Modal volume `zoet-runs`.
