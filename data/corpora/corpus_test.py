# SPDX-License-Identifier: GPL-3.0-or-later
# Code, not data: the surrounding directory is CC-BY-SA-4.0.
"""The manifest is a contract; these tests are what it promises.

Two halves, deliberately separable:

*Structure* needs no artwork.  It checks the manifest is internally
coherent -- that the pairing is a bijection, that the numbering is what
section 12.2 of the planning note read off the sheets, that the marks
are where they were verified to be.  These run everywhere, always.

*Correspondence* needs the artwork and skips without it.  It checks the
manifest still describes the files on disk: nothing added, nothing
removed, nothing silently re-captured.  That is the half that catches a
corpus quietly changing underneath the tests that depend on it.

The expected values here are not copied from the manifest.  They are the
readings recorded in docs/planning/inking-and-tween-plugins.md section
12, so if someone edits the manifest to match a changed corpus these
tests still object, which is the point of writing them down twice.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import pytest

import corpus as C

_HERE: Path = Path(__file__).resolve().parent
MANIFEST: Path = _HERE / "manrun_cycle_2001_wwc" / "manifest.json"

# Read off the sheets 2026-10-13; see planning note section 12.2.
CLEANUP_NUMBERS: List[str] = [str(n) for n in range(1, 13)]
ROUGH_NUMBERS: List[str] = ["3", "1", "1.5", "2", "4", "5",
                            "6", "6.5", "7", "8", "9", "10"]
ASTERISKED: set = {"1", "6", "10"}
EXPECTED_PAIRING: Dict[str, str] = {
    "1": "1", "1.5": "2", "2": "3", "3": "4", "4": "5", "5": "6",
    "6": "7", "6.5": "8", "7": "9", "8": "10", "9": "11", "10": "12",
}


@pytest.fixture(scope="module")
def manrun() -> C.Corpus:
    return C.load(MANIFEST)


@pytest.fixture(scope="module")
def artwork(manrun: C.Corpus) -> Path:
    where = C.root(manrun)
    if where is None or not (where / "12F").is_dir():
        pytest.skip("corpus artwork not present; set STORYMATOR_CORPORA")
    return where


# --------------------------------------------------------------- structure

def test_manifest_is_valid_json() -> None:
    json.loads(MANIFEST.read_text())


def test_loads(manrun: C.Corpus) -> None:
    assert manrun.name == "manrun_cycle_2001_wwc"
    assert len(manrun.sheets) == 24


def test_twelve_of_each_pass(manrun: C.Corpus) -> None:
    assert len(C.by_pass(manrun, "cleanup")) == 12
    assert len(C.by_pass(manrun, "rough")) == 12


def test_cleanups_are_numbered_one_to_twelve(manrun: C.Corpus) -> None:
    assert [s.drawing for s in C.by_pass(manrun, "cleanup")] == CLEANUP_NUMBERS


def test_roughs_carry_the_inserted_inbetweens(manrun: C.Corpus) -> None:
    """1.5 and 6.5 are the artist's own inbetweens, and must survive."""
    assert [s.drawing for s in C.by_pass(manrun, "rough")] == ROUGH_NUMBERS


def test_pairing_is_a_bijection(manrun: C.Corpus) -> None:
    got = C.pairing(manrun)
    assert got == EXPECTED_PAIRING
    assert sorted(got.values(), key=int) == CLEANUP_NUMBERS


def test_only_cleanups_lack_a_pair(manrun: C.Corpus) -> None:
    for s in manrun.sheets:
        if s.pass_name == "cleanup":
            assert s.pairs_with_cleanup is None, s.file
        else:
            assert s.pairs_with_cleanup is not None, s.file


def test_asterisks_are_on_roughs_one_six_and_ten(manrun: C.Corpus) -> None:
    """Verified across all 24 corners at native resolution."""
    marked = {s.drawing for s in manrun.sheets if "asterisk" in s.marks}
    assert marked == ASTERISKED
    assert not any(s.marks for s in C.by_pass(manrun, "cleanup"))


def test_media_match_the_pass(manrun: C.Corpus) -> None:
    for s in manrun.sheets:
        expected = "graphite" if s.pass_name == "cleanup" else "blue pencil"
        assert s.medium == expected, s.file


def test_digests_are_well_formed(manrun: C.Corpus) -> None:
    for s in manrun.sheets:
        assert len(s.sha256_16) == C.DIGEST_CHARS, s.file
        int(s.sha256_16, 16)


def test_oriented_size_is_the_stored_size_transposed(manrun: C.Corpus) -> None:
    """Every sheet carries EXIF orientation 6, so the axes swap."""
    for s in manrun.sheets:
        assert list(s.oriented_px) == list(reversed(list(s.stored_px))), s.file


def test_sheets_are_not_all_the_same_size(manrun: C.Corpus) -> None:
    """The finding that forces edge-anchored geometry. Do not 'fix'."""
    sizes = {tuple(s.stored_px) for s in manrun.sheets}
    assert len(sizes) == 4
    widths = {w for w, _ in sizes}
    assert min(widths) == 2305 and max(widths) == 2313
    assert (2305, 3217) in sizes       # the 64 px narrower sheet


# ---------------------------------------------------------- correspondence

def test_every_described_sheet_is_on_disk(manrun: C.Corpus,
                                          artwork: Path) -> None:
    missing = [s.file for s in manrun.sheets
               if not (artwork / "12F" / s.file).is_file()]
    assert not missing, f"described but absent: {missing}"


def test_no_sheet_on_disk_is_undescribed(manrun: C.Corpus,
                                         artwork: Path) -> None:
    described = {s.file for s in manrun.sheets}
    found = {p.name for p in (artwork / "12F").glob("*.png")}
    assert found == described, f"undescribed: {sorted(found - described)}"


def test_digests_still_match(manrun: C.Corpus,
                             artwork: Path) -> None:
    changed = [s.file for s in manrun.sheets
               if C.digest(artwork / "12F" / s.file) != s.sha256_16]
    assert not changed, f"content changed since the manifest: {changed}"


def test_stored_sizes_still_match(manrun: C.Corpus,
                                  artwork: Path) -> None:
    from PIL import Image
    wrong = []
    for s in manrun.sheets:
        with Image.open(artwork / "12F" / s.file) as im:
            if list(im.size) != list(s.stored_px):
                wrong.append((s.file, im.size, tuple(s.stored_px)))
    assert not wrong, wrong


# ------------------------------------------------------------- the helpers

def test_digest_matches_hashlib(tmp_path: Path) -> None:
    import hashlib
    p = tmp_path / "x.bin"
    p.write_bytes(b"storymator")
    assert C.digest(p) == hashlib.sha256(b"storymator").hexdigest()[:16]


def test_root_is_none_when_nothing_resolves(manrun: C.Corpus) -> None:
    nowhere = {"STORYMATOR_CORPORA": "/nonexistent"}
    assert C.root(manrun, environ=nowhere) is None


def test_root_prefers_the_environment(manrun: C.Corpus,
                                      tmp_path: Path) -> None:
    (tmp_path / manrun.name / "12F").mkdir(parents=True)
    got = C.root(manrun, environ={"STORYMATOR_CORPORA": str(tmp_path)})
    assert got == tmp_path / manrun.name
