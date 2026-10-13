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
    raise NotImplementedError


def root(corpus: Corpus,
         environ: Optional[Dict[str, str]] = None) -> Optional[Path]:
    """Where the artwork actually is, or ``None`` if it is not here."""
    raise NotImplementedError


def digest(path: Path, chars: int = DIGEST_CHARS) -> str:
    """The manifest's flavour of digest: leading hex of a SHA-256."""
    raise NotImplementedError


def by_pass(corpus: Corpus, pass_name: str) -> List[Sheet]:
    """The sheets of one pass, in manifest order."""
    raise NotImplementedError


def pairing(corpus: Corpus) -> Dict[str, str]:
    """Rough drawing number to the cleanup number it became."""
    raise NotImplementedError
