"""Keeping the pack portable, as a test rather than an intention.

Two rules, both from ``docs/planning/inking-and-tween-plugins.md`` in
the storymator repository.

**Nothing here imports the rig.**  This pack takes drawings that are
already registered; how they got that way is ``comfyui_acme``'s problem
and nobody else's.  The moment one module reaches across for a
convenience, the pack stops being publishable on its own, and that
happens gradually and is expensive to undo.

**The vocabulary is the project's, not the author's.**  The glossary
fixes the words and says the code should use those and no others.  That
rule has already been breached twice by people writing prose, both times
caught by a human reading carefully -- which is not a mechanism.

Neither check resists a determined author: a module could reach the rig
through ``importlib.import_module`` with a computed name, and no static
check will see it.  They are meant to catch **accident**, which is how
this kind of coupling actually arrives.

A line carrying the marker ``vocabulary-ok`` is exempt from the word
check, so a legitimate use can be allowed in place and stays visible to
a reader rather than silently special-cased in the checker.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Dict, List, Sequence, Set, Tuple

ALLOW_MARKER: str = "vocabulary-ok"

#: Packages this pack must never reach for.
FORBIDDEN_IMPORTS: Tuple[str, ...] = ("acme", "comfyui_acme")

#: Words the glossary rules out, with what to write instead.
BANNED_WORDS: Dict[str, str] = {
    "cell": "cel",            # vocabulary-ok
    "cells": "cels",          # vocabulary-ok
}

#: Directories that are build artefacts rather than sources.
SKIP_DIRS: Tuple[str, ...] = (
    "__pycache__", ".mypy_cache", ".pytest_cache", ".git",
)


def pack_files(root: Path, suffixes: Sequence[str]) -> List[Path]:
    """Every source file under ``root`` with one of ``suffixes``.

    Sorted, so a failure names files in a stable order.
    """
    wanted = set(suffixes)
    skip = set(SKIP_DIRS)
    return sorted(
        p for p in root.rglob("*")
        if p.is_file()
        and p.suffix in wanted
        and not skip.intersection(p.parts)
    )


def module_imports(source: str) -> Set[str]:
    """Every module name ``source`` imports.

    Relative imports keep their leading dots, so ``from ..acme.lens
    import x`` comes back as ``"..acme.lens"`` and can be told apart
    from the absolute ``acme.lens``.
    """
    found: Set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            # `import x as z` must not hide x behind its alias.
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            found.add("." * node.level + (node.module or ""))
    return found


def forbidden_imports(
    root: Path,
    forbidden: Sequence[str] = FORBIDDEN_IMPORTS,
) -> Dict[Path, Set[str]]:
    """Which files import something they must not, and what."""
    banned = set(forbidden)
    offenders: Dict[Path, Set[str]] = {}
    for path in pack_files(root, (".py",)):
        hits = {name for name in module_imports(path.read_text())
                if _top_level(name) in banned}
        if hits:
            offenders[path] = hits
    return offenders


def banned_words(
    text: str,
    banned: Sequence[str] = tuple(BANNED_WORDS),
) -> List[Tuple[int, str]]:
    """``(line number, word)`` for each banned word used as a word.

    Whole words only and case-insensitive: a longer word that merely
    contains a banned one is fine, and capitalising does not help.
    Lines carrying :data:`ALLOW_MARKER` are skipped.

    Worded without examples on purpose -- a docstring naming the banned
    word would need the marker, and the marker would then be visible in
    the rendered help.
    """
    if not banned:
        return []
    # Longest first, so the alternation cannot match a short word and
    # then fail the trailing boundary where a longer one would have fit.
    alternatives = "|".join(
        re.escape(w) for w in sorted(banned, key=len, reverse=True))
    pattern = re.compile(rf"\b(?:{alternatives})\b", re.IGNORECASE)
    hits: List[Tuple[int, str]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if ALLOW_MARKER in line:
            continue
        hits.extend((number, m.group(0)) for m in pattern.finditer(line))
    return hits


def forbidden_words(
    root: Path,
    banned: Sequence[str] = tuple(BANNED_WORDS),
    suffixes: Sequence[str] = (".py", ".md"),
) -> Dict[Path, List[Tuple[int, str]]]:
    """Which files use a banned word, where."""
    offenders: Dict[Path, List[Tuple[int, str]]] = {}
    for path in pack_files(root, suffixes):
        hits = banned_words(path.read_text(), banned)
        if hits:
            offenders[path] = hits
    return offenders


def _top_level(module: str) -> str:
    """``"..acme.lens"`` -> ``"acme"``, so a prefix cannot match.

    ``acmetools`` is not ``acme``, and comparing on the whole dotted
    name would miss ``acme.lens`` while comparing on a prefix would
    catch ``acmetools``.  The first component is the thing to compare.
    """
    return module.lstrip(".").split(".")[0]
