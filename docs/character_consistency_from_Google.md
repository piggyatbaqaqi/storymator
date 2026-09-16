# Local 2D AI Animation Pipeline Summary

This document outlines the workflow and architectural strategy discussed for creating consistent 2D anime animations locally via **ComfyUI** using a structural character sheet and open-weights frameworks.

---

## 1. Core Workflow Pipeline Architecture

The local node configuration maps multi-angle concept art onto dynamic motion tracks by breaking processing into four interconnected stages:

```
[Character Sheet] ➔ [Image Crop / Prep] ➔ [IP-Adapter Advanced] ┐
                                                                ├─➔ [KSampler + AnimateDiff/Wan] ➔ [VAE Decode] ➔ [Video]
[Driving Video]   ➔ [DWPreprocessor]     ➔ [ControlNet OpenPose] ┘
```

1. **Preprocessing & Isolation:** Splitting the character sheet via `ImageCrop` nodes into localized 3/4 and front-facing references, followed by background elimination nodes (e.g., `RMBG-1.4`).
2. **Identity Locking:** Feeding isolated crops through `IP-Adapter Advanced (Plus-V2)` and `ControlNet Reference/Tile` systems to tightly preserve aesthetic features, lines, and costumes across runtime generations.
3. **Motion Extraction:** Processing raw driving video footage via `DWPreprocessor` to capture skeleton telemetry using `OpenPose` mapping.
4. **Diffusion Execution:** Sampling data using open-weights diffusion engines parameterized specifically for local computational limitations.

---

## 2. Open-Weights Engine Trade-Offs

When selecting the foundational animation engine inside ComfyUI, users must balance local computational capacity against the desired visual complexity:

| Model Strategy | VRAM Usage | Strengths | Limitations |
| :--- | :--- | :--- | :--- |
| **AnimateDiff + 2D Checkpoint** (e.g., *Neta Lumina*, *ToonYou*) | **Low-Mid** (~8-12 GB) | Renders flawless flat 2D cel-shaded aesthetics; flexible frame interpolation loops. | Prone to feature drift over extended context lengths (60+ frames). |
| **Wan 2.2 Animate (14B FP8)** | **High** (~22-24 GB) | Highly fluid anatomical physics and extreme cinematic capabilities. | Tends to introduce unwanted 3D dimensionality; requires rigorous negative prompting. |

---

## 3. Advanced Optimization Protocols

* **Temporal Face Correction:** To stabilize hand-drawn line styles during intense movements, final frame batches should feed into a post-processing `FaceDetailer` loop equipped with an anime-trained `bbox` detector.
* **Sprite Production:** For production-level application, localized outputs can be piped into pixel-aligned programmatic frameworks to generate modular game assets from the raw video matrix.

---

## References

* **MiniMax H3:** Open-weights platform for video asset reference rendering. [MiniMax Instagram Update](https://www.instagram.com/p/DdJni3fC_tM/).
* **Wan 2.2 Animate Workflow:** ComfyUI community integration models for custom workflow templates. [ComfyUI Use Cases Guide](https://comfy.org/workflows/use-cases/ai-character-replacement/).
* **ComfyUI Ecosystem:** Core node processing framework. [ComfyUI Official Home](https://comfy.org).
* **Automated Sprite Frameworks:** Repository tooling for programmatic 2D engine asset compiling. [GitHub Repository: comfyui-2d-character-pipeline](https://github.com/mor-o/comfyui-2d-character-pipeline).
