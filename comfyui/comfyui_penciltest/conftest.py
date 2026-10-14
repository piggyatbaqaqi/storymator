"""Put the pack root on the path once, so the tests can import
``penciltest``.

Here rather than in each test module: doing it inline forces every
import below it, which is the whole of E402's complaint.

ComfyUI is deliberately *not* added.  ``penciltest/`` must import
without it -- that is the property the firewall exists to protect --
and the node wrappers under ``nodes/`` are the only part that needs
``comfy_api``.  A test that wants them uses ``pytest.importorskip``.
"""

import sys
from pathlib import Path

_PACK = Path(__file__).resolve().parent
sys.path.insert(0, str(_PACK))
sys.path.insert(0, str(_PACK.parent))
