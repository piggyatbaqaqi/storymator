"""Put the pack root on the path once, so the tests can import
``penciltest``.

Here rather than in each test module: doing it inline forces every
import below it, which is the whole of E402's complaint.

ComfyUI is added too, when it can be found, so ``nodes/`` can be tested
at all.  That does **not** weaken the rule that ``penciltest/`` imports
without it: the guarantee comes from
``test_the_pure_half_imports_without_comfyui_or_torch``, which runs in a
subprocess with only the pack root on the path, and is unaffected by
what this file does to the parent interpreter.  Withholding the path
here would have proved nothing and only made ``nodes/`` untestable.
"""

import os
import sys
from pathlib import Path

_PACK = Path(__file__).resolve().parent
sys.path.insert(0, str(_PACK))
sys.path.insert(0, str(_PACK.parent))

_COMFY = Path(os.environ.get(
    "COMFYUI_ROOT", "/data/piggy/src/github.com/Comfy-Org/ComfyUI"))
if (_COMFY / "comfy_api").is_dir():
    sys.path.append(str(_COMFY))
