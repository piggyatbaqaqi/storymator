"""What keeps this pack publishable, checked rather than hoped for.

Several lines below carry ``# vocabulary-ok``.  They have to name the
word the glossary rules out, because that is what they are testing, and
the marker is how a legitimate use is allowed in place and stays visible
to a reader rather than being special-cased inside the checker.  A test
for a rule is the one piece of code guaranteed to break it.

Three groups.  The **helpers** are tested on constructed input, because
a checker nobody checks is worth nothing -- a firewall that silently
fails to parse relative imports would pass forever and protect nothing.
The **applied** tests run those helpers over this pack's real sources,
and are the ones that will one day fail on somebody's convenient
shortcut.  The **packaging** tests fix the property that the pure half
imports without ComfyUI.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


from . import hygiene

PACK: Path = Path(__file__).resolve().parent.parent


# ----------------------------------------------------------- the helpers


def test_pack_files_finds_sources_and_sorts_them(tmp_path: Path) -> None:
    (tmp_path / "b.py").write_text("")
    (tmp_path / "a.py").write_text("")
    (tmp_path / "notes.md").write_text("")
    got = hygiene.pack_files(tmp_path, (".py",))
    assert [p.name for p in got] == ["a.py", "b.py"]


def test_pack_files_skips_build_artefacts(tmp_path: Path) -> None:
    (tmp_path / "real.py").write_text("")
    for junk in hygiene.SKIP_DIRS:
        (tmp_path / junk).mkdir()
        (tmp_path / junk / "stale.py").write_text("")
    got = hygiene.pack_files(tmp_path, (".py",))
    assert [p.name for p in got] == ["real.py"]


def test_pack_files_takes_several_suffixes(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("")
    (tmp_path / "b.md").write_text("")
    (tmp_path / "c.txt").write_text("")
    got = hygiene.pack_files(tmp_path, (".py", ".md"))
    assert sorted(p.name for p in got) == ["a.py", "b.md"]


def test_module_imports_plain_and_dotted() -> None:
    assert hygiene.module_imports("import x") == {"x"}
    assert hygiene.module_imports("import x.y") == {"x.y"}


def test_module_imports_sees_through_an_alias() -> None:
    """``import acme as a`` must not slip past."""
    assert hygiene.module_imports("import x as z") == {"x"}


def test_module_imports_from_form() -> None:
    assert hygiene.module_imports("from x import y") == {"x"}
    assert hygiene.module_imports("from x.y import z") == {"x.y"}


def test_module_imports_keeps_relative_dots() -> None:
    """The dots are the difference between our module and the rig's."""
    assert hygiene.module_imports("from . import y") == {"."}
    assert hygiene.module_imports("from .a import b") == {".a"}
    assert hygiene.module_imports("from ..a.b import c") == {"..a.b"}


def test_module_imports_collects_every_statement() -> None:
    src = "import a\nfrom b import c\n\ndef f():\n    import d\n"
    assert hygiene.module_imports(src) == {"a", "b", "d"}


def test_forbidden_imports_flags_an_absolute_reach(tmp_path: Path) -> None:
    (tmp_path / "bad.py").write_text("from acme.lens import calibrate\n")
    got = hygiene.forbidden_imports(tmp_path)
    assert {p.name for p in got} == {"bad.py"}


def test_forbidden_imports_flags_a_relative_reach(tmp_path: Path) -> None:
    """``from ..acme.x import y`` is the shortcut someone will try."""
    (tmp_path / "bad.py").write_text("from ..acme.rect import fit_rect\n")
    assert {p.name for p in hygiene.forbidden_imports(tmp_path)} == {"bad.py"}


def test_forbidden_imports_allows_our_own_relatives(tmp_path: Path) -> None:
    (tmp_path / "fine.py").write_text(
        "from .arcs import interior_angle\nimport numpy as np\n")
    assert hygiene.forbidden_imports(tmp_path) == {}


def test_forbidden_imports_does_not_match_a_prefix(tmp_path: Path) -> None:
    """``acmetools`` is not ``acme``."""
    (tmp_path / "fine.py").write_text("import acmetools\n")
    assert hygiene.forbidden_imports(tmp_path) == {}


def test_banned_words_matches_whole_words_only() -> None:
    assert hygiene.banned_words("a cell here") == [(1, "cell")]  # vocabulary-ok
    assert hygiene.banned_words("cellular automata") == []  # vocabulary-ok
    assert hygiene.banned_words("the cel is fine") == []


def test_banned_words_ignores_case() -> None:
    assert hygiene.banned_words("Cells and CELL") == [  # vocabulary-ok
        (1, "Cells"), (1, "CELL")]  # vocabulary-ok


def test_banned_words_reports_line_numbers() -> None:
    assert hygiene.banned_words("ok\nok\na cell\n") == [(3, "cell")]  # vocabulary-ok


def test_banned_words_respects_the_allow_marker() -> None:
    text = f"a cell  # {hygiene.ALLOW_MARKER}\na cell\n"  # vocabulary-ok
    assert hygiene.banned_words(text) == [(2, "cell")]  # vocabulary-ok


def test_forbidden_words_scans_prose_too(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("stack of cells\n")  # vocabulary-ok
    got = hygiene.forbidden_words(tmp_path)
    assert {p.name for p in got} == {"README.md"}


# ------------------------------------------------------------- applied

def test_this_pack_never_imports_the_rig() -> None:
    """§14.2. The pack must stay publishable on its own."""
    offenders = hygiene.forbidden_imports(PACK)
    assert not offenders, "\n".join(
        f"{p.relative_to(PACK)} imports {sorted(names)}"
        for p, names in sorted(offenders.items()))


def test_this_pack_uses_the_project_vocabulary() -> None:
    """§14.4. The glossary fixes the words; this is the mechanism."""
    offenders = hygiene.forbidden_words(PACK)
    assert not offenders, "\n".join(
        f"{p.relative_to(PACK)}:{line} {word!r} -- write "
        f"{hygiene.BANNED_WORDS[word.lower()]!r}"
        for p, hits in sorted(offenders.items()) for line, word in hits)


def test_the_pack_has_sources_to_check() -> None:
    """Guards against a checker that passes by finding nothing."""
    assert len(hygiene.pack_files(PACK, (".py",))) >= 4


# ----------------------------------------------------------- packaging

_FORBIDDEN_AT_IMPORT = ("comfy", "comfy_api", "comfy_extras", "torch")


def test_the_pure_half_imports_without_comfyui_or_torch() -> None:
    """``penciltest/`` must import with neither present.

    In a subprocess, because the claim is about what a *fresh*
    interpreter ends up holding, and this one has already imported the
    world -- including, under pytest, the pack itself.  An earlier
    version of this test asked ``sys.modules`` directly and matched our
    own ``comfyui_penciltest`` on the prefix, which is the kind of
    green-for-the-wrong-reason a packaging test exists to avoid.
    """
    probe = (
        "import sys; sys.path.insert(0, {root!r});"
        "import penciltest, penciltest.hygiene;"
        "roots = {{m.split('.')[0] for m in sys.modules}};"
        "print(','.join(sorted(roots & set({forbidden!r}))))"
    ).format(root=str(PACK), forbidden=list(_FORBIDDEN_AT_IMPORT))
    done = subprocess.run([sys.executable, "-c", probe],
                          capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == "", f"pulled in {done.stdout.strip()}"


def test_the_entrypoint_refuses_outside_comfyui() -> None:
    """Loudly, and saying what is missing.

    The pack root imports cleanly without ComfyUI on purpose, so the
    failure has to come at the point of use rather than at import, or
    it does not come at all.

    In a subprocess for the same reason as the test above, and for a
    sharper one: conftest.py now puts ComfyUI on the path so ``nodes/``
    can be tested, and ``nodes`` imports ``comfy_api``.  An in-process
    version of this test would therefore skip itself every single run
    and look like it was passing.
    """
    probe = (
        "import asyncio, sys; sys.path.insert(0, {parent!r});"
        "import comfyui_penciltest as p;"
        "\ntry:\n"
        "    asyncio.run(p.comfy_entrypoint())\n"
        "except RuntimeError as e:\n"
        "    print('refused:', e)\n"
        "else:\n"
        "    print('NOT REFUSED')\n"
    ).format(parent=str(PACK.parent))
    done = subprocess.run([sys.executable, "-c", probe],
                          capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stderr
    assert done.stdout.startswith("refused:"), done.stdout
    assert "ComfyUI 0.35" in done.stdout
