**Title:** Sample 3 does not reproduce `samples/3_out.mp4` with the released code and weights (output collapses at the sketch frame)

---

Thanks for releasing ToonComposer. We're trying to reproduce the gallery's
sample 3 before using the model, and we can't get the published output.

### What we ran

- Code: this repo at `53dc3df`, installed from `requirements.txt`
  (torch 2.8.0, diffsynth 1.1.7), Python 3.10. `flash_attn` not installed.
- Weights: `Wan-AI/Wan2.1-I2V-14B-480P` and `TencentARC/ToonComposer`
  `480p/tooncomposer.ckpt` (HF snapshot `a166c2c`). The checkpoint loads
  cleanly: 404 parameters loaded, 0 unexpected.
- GPU: A100 80GB.
- Placement: `model.to("cuda", dtype=torch.bfloat16)`, as in
  `initialize_model` in `app.py`.
- Inputs: the gallery config for sample 3 from `load_sample_data`:
  - `3_image1.png` at frame 0;
  - `3_sketch1.jpg` at frame 30, with no mask drawn;
  - 33 frames;
  - the English prompt from the gallery config.
- Sampler: the same call as `tooncomposer_inference`, with the UI
  defaults: `num_inference_steps=15`, `seed=42`, `tiled=True`,
  `cfg_scale=7.5`, `sequence_cond_residual_scale=1.0`.

We used the helper functions from `app.py` unchanged
(`process_conditions` etc.), because `app.py` can't be imported without
starting the UI.

### What we see

Frames 0 to about 24 are coherent, but the composition never moves
toward the sketch: the boy stays standing to the right. From frame 28 the
image washes out, and frames 30 to 32, where the sketch is injected,
become green noise with a regular grid texture. In `3_out.mp4` the boy
leans in by frame 16 and kneels by the basket by frame 24.

Montage attached. Rows: `3_out.mp4`, then our runs. Columns: frames 0,
8, 16, 24, 28, 30, 32.

### What we ruled out

- **Offloading and hardware.** We get the same result with diffsynth's
  `enable_vram_management` (block swap) on a 24 GB card, and with the
  whole model resident on the A100. The outputs are nearly identical.
- **Environment.** The same failure happens with torch 2.8.0 / CUDA 12
  on the A100 and with torch 2.14 / CUDA 13 locally.
- **flash-attn.** Without it, `flash_attention` falls back to SDPA.
  Every call site passes `k_lens=None` and `context_lens` is `None`, and
  the batch size is 1, so we believe the fallback computes the same
  thing. Please correct us if not.
- **The HF Space code.** We diffed the Space (`f3b0f25`) against this
  repo. The differences (LoRA defaults, temporal DeRA, visualisation
  hooks) don't apply to the 480p checkpoint's config. The Space is
  currently showing a runtime error, so we couldn't try it there.

### Something we noticed about the sample videos

`app.py` writes its output at 20 fps
(`cv2.VideoWriter(..., 20.0, ...)`), but all three `samples/N_out.mp4`
are 15 fps. Two of them have frame counts that differ from the gallery
config: `1_out.mp4` has 69 frames against a configured 61, and
`2_out.mp4` has 33 against 61. The repo also has a Chinese
`3_prompt.txt`, while the gallery uses an English prompt for sample 3.

### Questions

1. How was `samples/3_out.mp4` generated? Which script, settings,
   prompt (Chinese or English), and checkpoint?
2. Is there a setting we're missing that's required for the sketch
   conditioning to take effect? For example a sketch preprocessing
   step, or a motion mask.
3. Do you get the published result from the current `app.py` with the
   gallery's sample 3?

We're happy to share our full frames and runner script, and to test
any suggestion.
