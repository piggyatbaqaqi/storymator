"""Put the pack root on the path once, so the tests can import ``acme``.

Here rather than in each test module: doing it inline forces every
import below it, which is the whole of E402's complaint and is worth
avoiding in files people are meant to read.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
