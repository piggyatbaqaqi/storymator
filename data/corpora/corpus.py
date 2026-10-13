# SPDX-License-Identifier: GPL-3.0-or-later
# Code, not data: the surrounding directory is CC-BY-SA-4.0.
"""Reading a corpus manifest, and checking it still describes the corpus.

A corpus manifest is the in-tree half of an out-of-tree corpus.  The
artwork is not ours to publish, so what this repository carries is a
description of it: what each sheet is, and a digest per file so a test
can tell whether it is pointed at the corpus it thinks it is.  See
LICENSES.md, "Reference artwork".

The artwork is located at run time, never by a path baked into a test:

    STORYMATOR_CORPORA   a directory holding corpora by name
    or the manifest's own ``location.default_path``

``root()`` returns ``None`` when neither resolves, and the tests that
need pixels skip rather than fail.  A checkout without the artwork is a
normal state, not a broken one.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

DIGEST_CHARS: int = 16


@dataclass(frozen=True)
class Sheet:
    """One photographed sheet, as the manifest describes it."""

    file: str
    pass_name: str
    medium: str
    drawing: str
    marks: Sequence[str]
    pairs_with_cleanup: Optional[str]
    sha256_16: str
    stored_px: Sequence[int]
    oriented_px: Sequence[int]


@dataclass(frozen=True)
class Corpus:
    """A manifest, parsed."""

    name: str
    title: str
    sheets: List[Sheet]
    raw: Dict[str, object]


def load(manifest_path: Path) -> Corpus:
    """Parse a manifest into a :class:`Corpus`."""
    raw = json.loads(Path(manifest_path).read_text())
    sheets = [
        Sheet(
            file=s["file"],
            pass_name=s["pass"],
            medium=s["medium"],
            drawing=s["drawing"],
            marks=tuple(s["marks"]),
            pairs_with_cleanup=s["pairs_with_cleanup"],
            sha256_16=s["sha256_16"],
            stored_px=tuple(s["stored_px"]),
            oriented_px=tuple(s["oriented_px"]),
        )
        for s in raw["sheets"]
    ]
    return Corpus(name=raw["name"], title=raw["title"],
                  sheets=sheets, raw=raw)


def root(corpus: Corpus,
         environ: Optional[Dict[str, str]] = None) -> Optional[Path]:
    """Where the artwork actually is, or ``None`` if it is not here.

    ``STORYMATOR_CORPORA`` wins outright when it is set, and names a
    directory holding corpora by name.  It does **not** fall back to the
    manifest's default on a miss: someone who sets the variable has said
    where the corpora are, and silently reading a different copy is how
    you end up measuring the wrong one.
    """
    env = os.environ if environ is None else environ
    override = env.get("STORYMATOR_CORPORA")
    if override:
        candidate = Path(override).expanduser() / corpus.name
    else:
        location = corpus.raw.get("location")
        if not isinstance(location, dict):
            return None
        default = location.get("default_path")
        if not isinstance(default, str):
            return None
        candidate = Path(default).expanduser()
    return candidate if candidate.is_dir() else None


def digest(path: Path, chars: int = DIGEST_CHARS) -> str:
    """The manifest's flavour of digest: leading hex of a SHA-256."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()[:chars]


def by_pass(corpus: Corpus, pass_name: str) -> List[Sheet]:
    """The sheets of one pass, in manifest order."""
    return [s for s in corpus.sheets if s.pass_name == pass_name]


def pairing(corpus: Corpus) -> Dict[str, str]:
    """Rough drawing number to the cleanup number it became."""
    return {s.drawing: s.pairs_with_cleanup
            for s in corpus.sheets
            if s.pairs_with_cleanup is not None}
