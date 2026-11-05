"""Tests for ``bin/colour-dropout``.

The arithmetic is :mod:`acme.dropout`'s and is tested there, against
the real scan as well; what is left here is the command-line contract:
files in and out, flags and environment reaching the library, and
failures that say what went wrong without harming the input.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import types
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load() -> types.ModuleType:
    path = os.path.join(_HERE, "colour-dropout")
    loader = importlib.machinery.SourceFileLoader("colour_dropout", path)
    spec = importlib.util.spec_from_loader("colour_dropout", loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


cd = _load()

NUMERIC_VARS = ("COLOUR_DROPOUT_WHITE_PERCENTILE",
                "COLOUR_DROPOUT_WHITE_LEVEL", "COLOUR_DROPOUT_MARK_LEVEL")
ENV_VARS = NUMERIC_VARS + ("COLOUR_DROPOUT_OVERWRITE",)
PAPER = (243, 242, 246)
BLUE = (174, 209, 227)            # the "1" on the run-cycle scan
GRAPHITE = (110, 109, 111)
BLUE_BLOCK = (slice(10, 20), slice(10, 30))
GRAPHITE_BLOCK = (slice(30, 40), slice(10, 30))
PAPER_BLOCK = (slice(80, 120), slice(0, 160))


def scene() -> np.ndarray:
    img = np.empty((120, 160, 3), dtype=np.uint8)
    img[:, :] = PAPER
    img[BLUE_BLOCK] = BLUE
    img[GRAPHITE_BLOCK] = GRAPHITE
    return img


def as_float(img: np.ndarray) -> np.ndarray:
    return img.astype(float) / 255.0


def expected(img: np.ndarray, **settings: float) -> np.ndarray:
    gray = cd.dropout_colour(as_float(img), **settings).gray
    return np.round(gray * 255.0).astype(np.uint8)


def read(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path))


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """The operator's shell must not decide these tests."""
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def source(tmp_path: Path) -> Path:
    path = tmp_path / "scan.png"
    Image.fromarray(scene()).save(path)
    return path


@pytest.fixture
def target(tmp_path: Path) -> Path:
    return tmp_path / "clean.png"


def test_blue_goes_white_and_graphite_stays(source: Path,
                                            target: Path) -> None:
    assert cd.main([str(source), str(target)]) == 0
    out = read(target)
    assert np.all(out[BLUE_BLOCK] == 255)
    assert np.all(out[PAPER_BLOCK] == 255)
    assert np.all(out[GRAPHITE_BLOCK] < 200)


def test_defaults_are_the_library_defaults(source: Path,
                                           target: Path) -> None:
    """Rounded to 8 bits, and nothing else: no second set of defaults
    to drift away from the node's."""
    assert cd.main([str(source), str(target)]) == 0
    np.testing.assert_array_equal(read(target), expected(scene()))


def test_output_is_single_channel_8_bit(source: Path, target: Path) -> None:
    assert cd.main([str(source), str(target)]) == 0
    with Image.open(target) as out:
        assert out.mode == "L"
        assert out.size == (160, 120)


def test_white_level_flag_reaches_the_library(source: Path,
                                              target: Path) -> None:
    assert cd.main([str(source), str(target), "--white-level", "1.0"]) == 0
    out = read(target)
    np.testing.assert_array_equal(out, expected(scene(), white_level=1.0))
    assert np.all(out[BLUE_BLOCK] < 255)


def test_white_percentile_flag_reaches_the_library(tmp_path: Path,
                                                   target: Path) -> None:
    """Uneven paper, so the percentile picks a different white."""
    img = scene()
    img[60:] = (200, 200, 200)
    path = tmp_path / "uneven.png"
    Image.fromarray(img).save(path)
    assert cd.main([str(path), str(target),
                    "--white-percentile", "10"]) == 0
    out = read(target)
    np.testing.assert_array_equal(
        out, expected(img, white_percentile=10.0))
    assert not np.array_equal(out, expected(img))


def test_dropped_writes_the_mask(source: Path, target: Path,
                                 tmp_path: Path) -> None:
    mask_path = tmp_path / "removed.png"
    assert cd.main([str(source), str(target),
                    "--dropped", str(mask_path)]) == 0
    mask = read(mask_path)
    with Image.open(mask_path) as out:
        assert out.mode == "L"
    assert np.all(mask[BLUE_BLOCK] == 255)
    assert np.all(mask[GRAPHITE_BLOCK] == 0)
    assert np.all(mask[PAPER_BLOCK] == 0)


def test_no_mask_is_written_unless_asked_for(source: Path, target: Path,
                                             tmp_path: Path) -> None:
    assert cd.main([str(source), str(target)]) == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == ["clean.png",
                                                          "scan.png"]


def test_mark_level_flag_shapes_the_mask_and_not_the_picture(
        source: Path, target: Path, tmp_path: Path) -> None:
    """This blue's luminance is about 0.84 of paper."""
    mask_path = tmp_path / "removed.png"
    assert cd.main([str(source), str(target), "--dropped", str(mask_path),
                    "--mark-level", "0.8"]) == 0
    assert np.all(read(mask_path)[BLUE_BLOCK] == 0)
    np.testing.assert_array_equal(read(target), expected(scene()))


def test_environment_supplies_a_setting(
        source: Path, target: Path,
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COLOUR_DROPOUT_WHITE_LEVEL", "1.0")
    assert cd.main([str(source), str(target)]) == 0
    np.testing.assert_array_equal(read(target),
                                  expected(scene(), white_level=1.0))


def test_each_setting_has_its_environment_variable(
        source: Path, target: Path,
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Out of range from the environment is refused by name, which
    shows each variable was read."""
    for name in NUMERIC_VARS:
        monkeypatch.setenv(name, "200")
        assert cd.main([str(source), str(target)]) == 2
        monkeypatch.delenv(name)


def test_cli_beats_environment(source: Path, target: Path,
                               monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COLOUR_DROPOUT_WHITE_LEVEL", "not a number")
    assert cd.main([str(source), str(target), "--white-level", "1.0"]) == 0
    np.testing.assert_array_equal(read(target),
                                  expected(scene(), white_level=1.0))


def test_bad_environment_value_names_the_variable(
        source: Path, target: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("COLOUR_DROPOUT_WHITE_LEVEL", "not a number")
    with pytest.raises(SystemExit) as caught:
        cd.main([str(source), str(target)])
    assert caught.value.code == 2
    assert "COLOUR_DROPOUT_WHITE_LEVEL" in capsys.readouterr().err
    assert not target.exists()


def test_a_mistyped_flag_is_rejected(source: Path, target: Path) -> None:
    with pytest.raises(SystemExit) as caught:
        cd.main([str(source), str(target), "--white-levle", "0.9"])
    assert caught.value.code == 2


def test_both_file_names_are_required(source: Path) -> None:
    with pytest.raises(SystemExit) as caught:
        cd.main([str(source)])
    assert caught.value.code == 2


@pytest.mark.parametrize("flags, named", [
    (["--white-level", "0"], "white_level"),
    (["--mark-level", "1.5"], "mark_level"),
    (["--white-percentile", "100"], "white_percentile"),
])
def test_out_of_range_setting_is_refused_and_writes_nothing(
        source: Path, target: Path, flags: list[str], named: str,
        capsys: pytest.CaptureFixture[str]) -> None:
    assert cd.main([str(source), str(target)] + flags) == 2
    assert named in capsys.readouterr().err
    assert not target.exists()


def test_missing_input_is_named(tmp_path: Path, target: Path,
                                capsys: pytest.CaptureFixture[str]) -> None:
    absent = tmp_path / "absent.png"
    assert cd.main([str(absent), str(target)]) == 1
    assert "absent.png" in capsys.readouterr().err


def test_input_that_is_not_an_image_is_named(
        tmp_path: Path, target: Path,
        capsys: pytest.CaptureFixture[str]) -> None:
    junk = tmp_path / "notes.png"
    junk.write_text("not an image")
    assert cd.main([str(junk), str(target)]) == 1
    assert "notes.png" in capsys.readouterr().err


def test_unwritable_output_is_named(
        source: Path, tmp_path: Path,
        capsys: pytest.CaptureFixture[str]) -> None:
    nowhere = tmp_path / "no" / "such" / "dir" / "clean.png"
    assert cd.main([str(source), str(nowhere)]) == 1
    assert "clean.png" in capsys.readouterr().err


def test_existing_output_is_refused_and_left_alone(
        source: Path, target: Path,
        capsys: pytest.CaptureFixture[str]) -> None:
    target.write_bytes(b"precious")
    assert cd.main([str(source), str(target)]) == 2
    assert target.read_bytes() == b"precious"
    assert "clean.png" in capsys.readouterr().err


def test_existing_mask_is_refused_before_anything_is_written(
        source: Path, target: Path, tmp_path: Path,
        capsys: pytest.CaptureFixture[str]) -> None:
    mask_path = tmp_path / "removed.png"
    mask_path.write_bytes(b"precious")
    assert cd.main([str(source), str(target),
                    "--dropped", str(mask_path)]) == 2
    assert mask_path.read_bytes() == b"precious"
    assert not target.exists()
    assert "removed.png" in capsys.readouterr().err


def test_a_link_at_the_output_path_counts_as_existing(
        source: Path, target: Path, tmp_path: Path) -> None:
    """Even a dangling one: writing would create the file it names."""
    aimed_at = tmp_path / "elsewhere.png"
    target.symlink_to(aimed_at)
    assert cd.main([str(source), str(target)]) == 2
    assert not aimed_at.exists()


def test_input_named_as_output_is_an_ordinary_existing_file(
        source: Path) -> None:
    before = source.read_bytes()
    assert cd.main([str(source), str(source)]) == 2
    assert source.read_bytes() == before


def test_overwrite_replaces_the_output_and_the_mask(
        source: Path, target: Path, tmp_path: Path) -> None:
    mask_path = tmp_path / "removed.png"
    target.write_bytes(b"old")
    mask_path.write_bytes(b"old")
    assert cd.main([str(source), str(target), "--dropped", str(mask_path),
                    "--overwrite"]) == 0
    np.testing.assert_array_equal(read(target), expected(scene()))
    assert np.all(read(mask_path)[BLUE_BLOCK] == 255)


def test_environment_can_allow_overwriting(
        source: Path, target: Path,
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COLOUR_DROPOUT_OVERWRITE", "1")
    target.write_bytes(b"old")
    assert cd.main([str(source), str(target)]) == 0
    np.testing.assert_array_equal(read(target), expected(scene()))


def test_a_false_environment_value_still_refuses(
        source: Path, target: Path,
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COLOUR_DROPOUT_OVERWRITE", "0")
    target.write_bytes(b"precious")
    assert cd.main([str(source), str(target)]) == 2
    assert target.read_bytes() == b"precious"


def test_overwrite_treats_the_input_like_any_other_file(
        source: Path) -> None:
    assert cd.main([str(source), str(source), "--overwrite"]) == 0
    np.testing.assert_array_equal(read(source), expected(scene()))


@pytest.mark.parametrize("flags", [[], ["--overwrite"]])
def test_mask_and_output_must_be_different_files(
        source: Path, target: Path, flags: list[str],
        capsys: pytest.CaptureFixture[str]) -> None:
    """One would silently replace the other, flag or no flag."""
    assert cd.main([str(source), str(target),
                    "--dropped", str(target)] + flags) == 2
    assert not target.exists()
    assert "clean.png" in capsys.readouterr().err


def test_alpha_in_the_input_is_ignored(tmp_path: Path, target: Path) -> None:
    rgba = np.dstack([scene(), np.full((120, 160), 40, dtype=np.uint8)])
    path = tmp_path / "alpha.png"
    Image.fromarray(rgba).save(path)
    assert cd.main([str(path), str(target)]) == 0
    np.testing.assert_array_equal(read(target), expected(scene()))


def test_exif_orientation_is_honoured_as_loadimage_does(
        tmp_path: Path, target: Path) -> None:
    """ComfyUI's LoadImage transposes, so the node sees it upright."""
    exif = Image.Exif()
    exif[0x0112] = 6                 # rotate 90 clockwise to display
    path = tmp_path / "tagged.png"
    Image.fromarray(scene()).save(path, exif=exif)
    assert cd.main([str(path), str(target)]) == 0
    with Image.open(target) as out:
        assert out.size == (120, 160)


def test_high_bit_depth_input_is_refused_rather_than_clipped(
        tmp_path: Path, target: Path,
        capsys: pytest.CaptureFixture[str]) -> None:
    """Pillow's conversion to RGB clips 16-bit values to white, which
    would be a blank page and exit status 0."""
    deep = np.full((40, 40), 30000, dtype=np.uint16)
    path = tmp_path / "deep.png"
    Image.fromarray(deep).save(path)
    assert cd.main([str(path), str(target)]) == 1
    assert "deep.png" in capsys.readouterr().err
    assert not target.exists()
