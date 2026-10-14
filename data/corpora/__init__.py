# SPDX-License-Identifier: GPL-3.0-or-later
# Code, not data: the surrounding directory is CC-BY-SA-4.0.
"""Corpora held outside this repository, described inside it.

A package rather than two loose modules so that ``corpus_test.py`` can
say ``from . import corpus`` -- which is the same question
``comfyui/mypy.ini`` poses of every test file: where does it sit
relative to the thing it tests?  Beside it, in a package, so the import
is relative.
"""
