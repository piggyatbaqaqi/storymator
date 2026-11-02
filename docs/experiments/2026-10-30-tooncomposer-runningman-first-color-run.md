# ToonComposer on RunningMan with a colour guide, 2026-10-30

ToonComposer was run locally on our own drawings for the first time: the
ManRunCycle cleanups plus the colour guide `char_00031_.png`, at 17 and
33 frames. Neither run is usable as an inbetween. But the 33-frame run
pinned down where the failure lives, which earlier runs had not:

> **Every 4-frame VAE latent that holds a sketch turns into lattice
> noise. Every latent without a sketch renders a coherent coloured
> figure.** The upstream sample 3 shows the same signature on the
> 80 GB resident run (no block swap). The defect sits in the
> sketch-injection path, not in our offload rig and not in our
> drawings.

Background: §7a.8 and §7b.3 of
[inking-and-tween-plugins.md](../planning/inking-and-tween-plugins.md),
and upstream issue
[TencentARC/ToonComposer#19](https://github.com/TencentARC/ToonComposer/issues/19).

**Not for publication.** The inputs and every generated frame derive
from the Wiki Wiki Cartoons ManRunCycle corpus. Its manifest says the
images are owned outright and not published. No images are committed
here, and none should go to #19 unless Monte and Daniel decide so. The
latent-pattern finding can be stated in words without them.

## Setup

| | |
|---|---|
| Model | ToonComposer adapter on Wan2.1-I2V-14B-480P, weights cast to bf16 on load (`lowmem.py`) |
| Card | RTX 5090 Laptop, 24 GB; driver 595.99.02 |
| Offload | diffsynth block swap, `num_persistent_param_in_dit=6e9`, bare parameters pinned to CUDA |
| Host cap | `systemd-run --user --scope -p MemoryMax=54G -p MemorySwapMax=0` |
| Sampling | 15 steps, CFG 7.5, 832×480 |
| Prompt | "A startled cartoon man in a top hat and long tailcoat runs to the right in a fast, bouncing run, gripping a crook-handled cane that swings forward and back with his arm. Anime. High quality." |

**Inputs**, prepared by `runner/prep_runman.py`:

- **Sketches.** Cleanups of drawings 1, 3, 5, 7 from `10F/`, chosen by
  the manifest's drawing number, not capture order:
  `20260920-001539.png`, `-001823`, `-002042`, `-002247`.
  - Each was EXIF-transposed and had the NE 340×360 metadata corner
    blanked.
  - Levels were stretched so paper reads white and graphite near black
    (paper = 60th percentile, ink = 0.2th percentile).
  - They were not moved: they are peg-registered, so their relative
    positions are the motion.
- **Colour key at frame 0.** `colored/char_00031_.png` is drawing 1's
  pose at another scale.
  - It was scaled ×3.512 and offset (−6, 3) so the figure's bounding box
    matches drawing 1's.
  - It sits on a 10F-sized canvas filled with its own sky-blue
    background, so the app's short-edge resize and centre crop treat it
    exactly like the sketches.
  - `montages/inputs_check.png` shows the cropped inputs overlaid.

**Arms:**

| Arm | Frames | Sketch slots (drawings 1/3/5/7) | Latents holding a sketch |
|---|---|---|---|
| `runman17` | 17 | 0, 5, 11, 16 | 0, 2, 3, 4 (of 0–4) |
| `runman33` | 33 | 0, 11, 21, 32 | 0, 3, 6, 8 (of 0–8) |

The Wan VAE compresses time 4×: frame 0 is latent 0 on its own, and
after that frames 4k−3 … 4k form latent k.

## Cost

| Arm | Build | Generate | s/frame | Peak VRAM | Host RSS |
|---|---|---|---|---|---|
| `runman17` | 19.8 s | 2019.7 s (34 min) | 118.8 | 16.58 GiB | 38.2 GiB |
| `runman33` | 17.5 s | 3245.3 s (54 min) | 98.3 | 17.94 GiB | 38.2 GiB |

There were no OOM events. Both arms ran in sequence, 13:31–14:59.

## Results

### By eye (`montages/*_all.png`, `*_slots.png`)

**`runman17`:**
- **f00:** the colour key, recognisable, but covered in a regular
  lattice texture.
- **f01–f04:** washed out to a pale figure ghost.
- **f05–f16:** coloured noise with lattice texture throughout.
- **Sketch slots:** none of the drawings appear at any of them.

**`runman33`:**
- **f00:** as in `runman17`: the key with lattice texture.
- **f01–f08, f13–f20, f25–f28:**
  - A coherent, flat-coloured figure. The top hat, the cane with its
    crook, the tailcoat, blue trousers and dark shoes are all present.
  - The pose changes from latent to latent.
  - The sky-blue background and the door frame are gone: the figure
    stands on white.
  - The hat shifts from brown to orange.
  - The face is mostly blank.
- **f09–f12, f21–f24, f29–f32:** dark lattice noise. At most a faint
  figure-shaped shadow shows through.
- **Sketch slots 11, 21, 32:** noise. **None of drawings 3, 5, 7 are
  reproduced at its slot.**

### Measured (`montages/texture_by_latent.txt`)

The texture measure is the mean |Laplacian| of luma; brightness is mean
luma. Frame ranges are inclusive.

| `runman33` latent | Frames | Sketch? | Texture | Mean luma |
|---|---|---|---|---|
| 0 | 0 | drawing 1 + colour key | 4.9 | 140 |
| 1 | 1–4 | | 1.2–1.7 | 234–249 |
| 2 | 5–8 | | 1.4–1.9 | 241–248 |
| **3** | **9–12** | **drawing 3 @ 11** | **4.4–14.5** | **17–71** |
| 4 | 13–16 | | 1.5–2.0 | 236–245 |
| 5 | 17–20 | | 1.1–2.1 | 239–246 |
| **6** | **21–24** | **drawing 5 @ 21** | **5.7–14.5** | **54–112** |
| 7 | 25–28 | | 1.0–2.6 | 224–251 |
| **8** | **29–32** | **drawing 7 @ 32** | **2.8–11.5** | **53–139** |

- **The split is total.** Every non-sketch latent has texture ≤ 2.6 and
  mean luma ≥ 224. Every sketch latent is dark and textured.
- **The boundaries match exactly.** They fall on the latent edges, not
  on the sketch frames: the whole 4-frame group goes, whichever frame in
  it carries the sketch.
- **`runman17` agrees.**
  - Latent 1 (f01–f04, no sketch) is clean: texture 2.7–3.9, luma
    210–224.
  - Latents 2, 3 and 4 each hold a sketch (slots 5, 11, 16), so
    f05–f16 are all noise.
  - That is why the 17-frame arm looked like total collapse: at that
    length nearly every latent carries a sketch.

### The same signature on upstream's own sample

The same measure was run on the 2026-10-19 sample-3 outputs in
`~/lab/storymator/spikes/tooncomposer-modal-2026-10-19/frames/`. Sample
3 has one sketch, at frame 30, which falls in latent 8.

| Run | f00–f28 texture | f29–f32 (latent 8) texture | f29–f32 luma |
|---|---|---|---|
| `out_modal_resident` (A100-80GB, no block swap) | 2.0–3.0 | 16.7, 6.8, 14.8, 9.8 | 132, 53, 58, 77 |
| `out_modal_swap` (A100-80GB, block swap) | identical to resident | identical | identical |
| `ref3` (upstream's published reference) | 2.7–3.2 | 2.8–2.9 | 164–165 |

The run without block swap fails in exactly the sketch's latent and
nowhere else. Upstream's published output does not fail. This confirms
§7b.3's exoneration of block swap, now on the metric that localises the
fault.

## What this means

1. **The #19 defect is in the sketch-conditioning path, and it is
   latent-local.**
   - When a sketch is injected into a latent, that latent's denoising
     goes wrong.
   - Neighbouring latents are unharmed, so the corruption does not leak
     through temporal attention to any visible degree.
   - The likely suspects are in the per-latent sketch injection itself:
     `sequence_cond_identifier`, the sparse-sketch embedding, or its
     scaling or dtype. This is inference, not yet tested.
2. **The colour key does carry.**
   - Clean latents up to 28 frames away hold the guide's palette and
     costume.
   - The changes are the background lost to white, the hue shift on the
     hat and the blank face.
   - Colour propagation is therefore not what's blocking us; sketch
     adherence is.
3. **No verdict on inbetweening RunningMan is possible yet.**
   - The latents where the drawings should appear are exactly the ones
     destroyed, so whether the model hits the drawn poses was never
     tested.
   - Whether the clean latents move *toward* the next drawing (travel
     of the cane or trailing foot) has not been assessed. A band crop
     is the next look, but the result is moot until sketch latents
     render.
4. **Caveat on the measure.** Mean |Laplacian| and brightness are
   hypotheses. The by-eye read of all three montages agrees with them
   frame for frame. The latent mapping assumes Wan's 1 + 4k temporal
   compression, which 17 → 5 and 33 → 9 latents are consistent with.

## Suggested next tests

- **Sample 3 with its sketch removed** (colour key only, everything else
  identical). If latent 8 comes out clean, the defect is confirmed in
  the sketch path. This uses only upstream's material, so it can be
  posted to #19. About 40 min locally, no cost.
- **Move the sketch by one latent.** Run sample 3 with its sketch at
  frame 28 instead of 30. The noise should follow it into latent 7.
- **Report to #19 in words.** The latent-local observation is the most
  useful thing we can tell upstream, and it needs neither our images
  nor our corpus.

## Where everything is

Run directory:
`/home/piggy/lab/storymator/training_data/ManRunCycle_Rough_CleanUp_2001_WWC/first_color_run/`

| Path (relative to the run directory) | Contents |
|---|---|
| `inputs/sketch_{1,3,5,7}.png` | Prepared sketches, 2734×1921 |
| `inputs/colour_registered.png` | Colour key registered to drawing 1 |
| `runman17/frame_00.png` … `frame_16.png`, `runman17/result.json` | 17-frame arm, with settings and timings |
| `runman33/frame_00.png` … `frame_32.png`, `runman33/result.json` | 33-frame arm |
| `runman17.log`, `runman33.log` | Full run logs |
| `launch.status` | Start, exit codes and finish times |
| `montages/runman{17,33}_all.png` | Every frame, 6 across |
| `montages/runman{17,33}_slots.png` | Inputs (top row) against the generated frame at each slot |
| `montages/inputs_check.png` | Inputs after the app's resize and crop, overlaid |
| `montages/texture_by_latent.txt` | Per-frame texture and luma for both arms |
| `runner/run.py`, `lowmem.py`, `tc_helpers.py` | Spike runner (`--colour`, `--sketch PATH@FRAME`) |
| `runner/prep_runman.py` | Input preparation |
| `runner/check_inputs.py`, `montage.py`, `latent_texture.py` | Checks and measures |
| `runner/launch.sh` | Exact launch. It copies inputs from the original scratchpad's `in/`, so to rerun, point it at `inputs/`. |

Other paths:

- Source corpus:
  `/home/piggy/lab/storymator/training_data/ManRunCycle_Rough_CleanUp_2001_WWC/10F/`
  and `.../colored/char_00031_.png`. The manifest is in-tree at
  `data/corpora/manrun_cycle_2001_wwc/manifest.json`.
- Sample-3 comparison frames:
  `/home/piggy/lab/storymator/spikes/tooncomposer-modal-2026-10-19/frames/{out_modal_resident,out_modal_swap,ref3}/`.
- Conda env for the runner: `tooncomposer-spike`. The measures ran under
  `storymator`.
