"""Put the repo root on the path so ``big_green_button`` imports as a package.

The modules use relative imports (``from . import input_devices``), so
they can only be imported as part of the package -- which means the
PARENT of this directory has to be importable, not this directory.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
