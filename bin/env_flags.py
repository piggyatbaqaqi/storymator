"""Let the environment supply argparse defaults: CLI, then environment.

Every optional flag on a parser reads ``<PREFIX>_<DEST>`` when it is not
given on the command line, so a flag added later is covered without
anyone remembering to.  See docs/bin-argparse-strict.md.

    parser = build_parser()
    apply_env(parser, "MEASURE_INK", exempt={"peg"})

Whatever can't sensibly take one value from a shell must be named in
``exempt``.  A repeatable flag is the usual case: argparse appends to its
default, so a value from the environment would be added to by the command
line rather than replaced by it.  ``apply_env`` raises on those instead
of skipping them, so that leaving one out is a decision somebody made.
"""

from __future__ import annotations

import argparse
from typing import Collection


def apply_env(parser: argparse.ArgumentParser, prefix: str,
              exempt: Collection[str] = ()) -> None:
    """Point each optional flag's default at its environment variable."""
    raise NotImplementedError("apply_env is not written yet")
