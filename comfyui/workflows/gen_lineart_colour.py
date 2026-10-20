"""Generate the lineart-colour ComfyUI workflow (UI format) and an API twin.

usage: python gen_lineart_colour.py UI_OUT.json API_OUT.json
"""
from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

CKPT: str = "v1-5-pruned-emaonly-fp16.safetensors"
CN_LINEART: str = "control_v11p_sd15_lineart_fp16.safetensors"
CN_CANNY: str = "control_v11p_sd15_canny_fp16.safetensors"

CHARACTER = ("a cartoon character, full body, clean cel shading, flat colours, "
             "red jacket, blue trousers, brown hair, crisp black outlines")
BACKGROUND = ("background: a sunny city street, brick buildings, blue sky, "
              "soft afternoon light, painted animation background")
NEGATIVE = ("lowres, blurry, extra limbs, deformed hands, sketch, monochrome, "
            "greyscale, text, watermark, signature")

NOTE = """# Clean line drawing -> coloured character + background

1. Put the cleaned drawing in ComfyUI's `input/` and pick it in **Load drawing**.
   Dark lines on a **white, opaque** background. A transparent PNG loads as
   black and the ControlNet sees the whole frame as ink.
2. Describe the character and the background in their own boxes.
3. **Lineart** is on. **Canny** is bypassed (Ctrl+B to toggle). Canny on clean
   line art traces both edges of every stroke, so it doubles the lines.
4. The ControlNet reads empty paper as "nothing here", which pushes toward a
   plain background. `end_percent` 0.8 hands the last steps back to the prompt
   so the background can fill in. Raise it if the lines drift.

Models: `controlnet/control_v11p_sd15_lineart_fp16.safetensors` (and `_canny_`)
from comfyanonymous/ControlNet-v1-1_fp16_safetensors. CreativeML OpenRAIL-M,
accepted in storymator LICENSES.md (2026-10-13).
"""

# id: (type, title, pos, size, widgets, inputs{name: (type, src)}, outputs[(name,type)], mode)
# src is (node_id, out_slot) or None; widget-inputs are flagged with "widget".
# An input spec is (name, type, src) or (name, type, src, "widget"), so the
# tuples are deliberately ragged; see the comment above.
InputSpec = Tuple[Any, ...]
OutputSpec = Tuple[str, str]
Source = Optional[Tuple[int, int]]

N: Dict[int, Dict[str, Any]] = {}


def node(nid: int, typ: str, title: str, pos: List[int], size: List[int],
         widgets: List[Any], inputs: Sequence[InputSpec] = (),
         outputs: Sequence[OutputSpec] = (), mode: int = 0) -> None:
    N[nid] = dict(type=typ, title=title, pos=pos, size=size, widgets=widgets,
                  inputs=list(inputs), outputs=list(outputs), mode=mode)


node(1, "CheckpointLoaderSimple", "Checkpoint (SD1.5)", [0, 0], [315, 98], [CKPT],
     outputs=[("MODEL", "MODEL"), ("CLIP", "CLIP"), ("VAE", "VAE")])
node(2, "CLIPTextEncode", "Character prompt", [360, 0], [400, 140], [CHARACTER],
     inputs=[("clip", "CLIP", (1, 1))], outputs=[("CONDITIONING", "CONDITIONING")])
node(3, "CLIPTextEncode", "Background prompt", [360, 180], [400, 140], [BACKGROUND],
     inputs=[("clip", "CLIP", (1, 1))], outputs=[("CONDITIONING", "CONDITIONING")])
node(4, "ConditioningConcat", "Character + background", [800, 60], [260, 50], [],
     inputs=[("conditioning_to", "CONDITIONING", (2, 0)),
             ("conditioning_from", "CONDITIONING", (3, 0))],
     outputs=[("CONDITIONING", "CONDITIONING")])
node(5, "CLIPTextEncode", "Negative prompt", [360, 360], [400, 120], [NEGATIVE],
     inputs=[("clip", "CLIP", (1, 1))], outputs=[("CONDITIONING", "CONDITIONING")])
node(6, "LoadImage", "Load drawing", [0, 520], [315, 320], ["character_clean.png", "image"],
     outputs=[("IMAGE", "IMAGE"), ("MASK", "MASK")])
node(7, "ImageScaleToTotalPixels", "Scale to SD1.5 size", [360, 520], [300, 106],
     ["lanczos", 0.4, 8],
     inputs=[("image", "IMAGE", (6, 0))], outputs=[("IMAGE", "IMAGE")])
node(8, "GetImageSize", "Drawing size", [360, 680], [220, 70], [],
     inputs=[("image", "IMAGE", (7, 0))],
     outputs=[("width", "INT"), ("height", "INT"), ("batch_size", "INT")])
node(9, "EmptyLatentImage", "Latent (drawing size)", [620, 680], [260, 106], [512, 512, 1],
     inputs=[("width", "INT", (8, 0), "widget"), ("height", "INT", (8, 1), "widget")],
     outputs=[("LATENT", "LATENT")])
node(10, "ImageInvert", "Invert (lines -> white on black)", [700, 520], [260, 30], [],
     inputs=[("image", "IMAGE", (7, 0))], outputs=[("IMAGE", "IMAGE")])
node(11, "ControlNetLoader", "ControlNet lineart", [1000, 360], [340, 60], [CN_LINEART],
     outputs=[("CONTROL_NET", "CONTROL_NET")])
node(12, "ControlNetApplyAdvanced", "Apply lineart", [1100, 60], [300, 186], [1.0, 0.0, 0.8],
     inputs=[("positive", "CONDITIONING", (4, 0)), ("negative", "CONDITIONING", (5, 0)),
             ("control_net", "CONTROL_NET", (11, 0)), ("image", "IMAGE", (10, 0)),
             ("vae", "VAE", None)],
     outputs=[("positive", "CONDITIONING"), ("negative", "CONDITIONING")])
node(13, "Canny", "Canny edges", [700, 860], [260, 82], [0.4, 0.8],
     inputs=[("image", "IMAGE", (7, 0))], outputs=[("IMAGE", "IMAGE")])
node(14, "ControlNetLoader", "ControlNet canny", [1000, 860], [340, 60], [CN_CANNY],
     outputs=[("CONTROL_NET", "CONTROL_NET")])
node(15, "ControlNetApplyAdvanced", "Apply canny (bypassed)", [1440, 60], [300, 186],
     [0.6, 0.0, 0.8],
     inputs=[("positive", "CONDITIONING", (12, 0)), ("negative", "CONDITIONING", (12, 1)),
             ("control_net", "CONTROL_NET", (14, 0)), ("image", "IMAGE", (13, 0)),
             ("vae", "VAE", None)],
     outputs=[("positive", "CONDITIONING"), ("negative", "CONDITIONING")], mode=4)
node(16, "KSampler", "Sampler", [1780, 60], [315, 262],
     [20261019, "fixed", 25, 7.0, "dpmpp_2m", "karras", 1.0],
     inputs=[("model", "MODEL", (1, 0)), ("positive", "CONDITIONING", (15, 0)),
             ("negative", "CONDITIONING", (15, 1)), ("latent_image", "LATENT", (9, 0))],
     outputs=[("LATENT", "LATENT")])
node(17, "VAEDecode", "Decode", [2130, 60], [210, 46], [],
     inputs=[("samples", "LATENT", (16, 0)), ("vae", "VAE", (1, 2))],
     outputs=[("IMAGE", "IMAGE")])
node(18, "SaveImage", "Save", [2130, 160], [400, 450], ["lineart_colour/char"],
     inputs=[("images", "IMAGE", (17, 0))])
node(19, "PreviewImage", "What lineart sees", [1000, 480], [300, 300], [],
     inputs=[("images", "IMAGE", (10, 0))])
node(20, "PreviewImage", "What canny sees", [1380, 860], [300, 300], [],
     inputs=[("images", "IMAGE", (13, 0))])
node(21, "MarkdownNote", "Read me", [0, 900], [620, 420], [NOTE])

OPTIONAL: Set[str] = {"vae"}


def build_ui() -> Dict[str, Any]:
    links: List[List[Any]] = []
    link_id: int = 0
    out_links: Dict[Tuple[int, int], List[int]] = {
        (nid, s): [] for nid, n in N.items() for s in range(len(n["outputs"]))}
    ui_nodes: List[Dict[str, Any]] = []
    for order, (nid, n) in enumerate(sorted(N.items())):
        ins: List[Dict[str, Any]] = []
        for spec in n["inputs"]:
            name, typ, src = spec[0], spec[1], spec[2]
            entry: Dict[str, Any] = {"name": name, "type": typ, "link": None}
            if name in OPTIONAL:
                entry["shape"] = 7
            if len(spec) > 3:
                entry["widget"] = {"name": name}
            if src is not None:
                link_id += 1
                sn, ss = src
                assert N[sn]["outputs"][ss][1] == typ, (nid, name)
                links.append([link_id, sn, ss, nid, len(ins), typ])
                out_links[(sn, ss)].append(link_id)
                entry["link"] = link_id
            ins.append(entry)
        ui_nodes.append(dict(
            id=nid, type=n["type"], pos=n["pos"], size=n["size"], flags={},
            order=order, mode=n["mode"], inputs=ins,
            outputs=[{"name": o, "type": t, "slot_index": i, "links": out_links[(nid, i)]}
                     for i, (o, t) in enumerate(n["outputs"])],
            title=n["title"], properties={"Node name for S&R": n["type"]},
            widgets_values=n["widgets"]))
    return {
        "id": "5b1f2c7e-6d0a-4c1e-9a43-4e7f3a9b1c2d",
        "revision": 0, "last_node_id": max(N), "last_link_id": link_id,
        "nodes": ui_nodes, "links": links,
        "groups": [
            {"id": 1, "title": "Lineart (on)", "bounding": [690, 330, 660, 470],
             "color": "#3f789e", "font_size": 24, "flags": {}},
            {"id": 2, "title": "Canny (bypassed)", "bounding": [690, 820, 1000, 360],
             "color": "#a1309b", "font_size": 24, "flags": {}},
        ],
        "config": {}, "extra": {"ds": {"scale": 0.6, "offset": [40, 40]}}, "version": 0.4,
    }


# widget names in widgets_values order (UI-only "control_after_generate" and the
# LoadImage "upload" entry are skipped when building API inputs)
WIDGETS: Dict[str, List[Optional[str]]] = {
    "CheckpointLoaderSimple": ["ckpt_name"],
    "CLIPTextEncode": ["text"],
    "LoadImage": ["image", None],
    "ImageScaleToTotalPixels": ["upscale_method", "megapixels", "resolution_steps"],
    "EmptyLatentImage": ["width", "height", "batch_size"],
    "ControlNetLoader": ["control_net_name"],
    "ControlNetApplyAdvanced": ["strength", "start_percent", "end_percent"],
    "Canny": ["low_threshold", "high_threshold"],
    "KSampler": ["seed", None, "steps", "cfg", "sampler_name", "scheduler", "denoise"],
    "SaveImage": ["filename_prefix"],
}


def build_api() -> Dict[str, Dict[str, Any]]:
    """API prompt as the frontend would submit it: notes dropped, bypass spliced."""
    def resolve(src: Tuple[int, int]) -> List[Any]:
        sn, ss = src
        if N[sn]["mode"] == 4:  # bypass: pass the first same-typed input through
            typ = N[sn]["outputs"][ss][1]
            same = [s for s in N[sn]["inputs"] if s[1] == typ and s[2] is not None]
            return resolve(same[ss][2] if len(same) > ss else same[0][2])
        return [str(sn), ss]

    api: Dict[str, Dict[str, Any]] = {}
    for nid, n in N.items():
        if n["type"] == "MarkdownNote" or n["mode"] == 4:
            continue
        inputs: Dict[str, Any] = {}
        for name, val in zip(WIDGETS.get(n["type"], []), n["widgets"]):
            if name:
                inputs[name] = val
        for spec in n["inputs"]:
            if spec[2] is not None:
                inputs[spec[0]] = resolve(spec[2])
        api[str(nid)] = {"class_type": n["type"], "inputs": inputs,
                         "_meta": {"title": n["title"]}}
    # prune nodes not reachable from an output node
    outputs: Set[str] = {"SaveImage", "PreviewImage"}
    keep: Set[str] = set()
    stack: List[str] = [k for k, v in api.items() if v["class_type"] in outputs]
    while stack:
        k = stack.pop()
        if k in keep:
            continue
        keep.add(k)
        stack += [v[0] for v in api[k]["inputs"].values() if isinstance(v, list)]
    return {k: v for k, v in api.items() if k in keep}


def main(argv: Sequence[str]) -> int:
    ui_path, api_path = argv[1], argv[2]
    with open(ui_path, "w") as f:
        json.dump(build_ui(), f, indent=2)
        f.write("\n")
    with open(api_path, "w") as f:
        json.dump(build_api(), f, indent=2)
        f.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
