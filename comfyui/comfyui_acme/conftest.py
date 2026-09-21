"""Put the pack root on the path once, so the tests can import ``acme``.

Here rather than in each test module: doing it inline forces every
import below it, which is the whole of E402's complaint and is worth
avoiding in files people are meant to read.

At the pack root rather than in ``tests/`` because unit tests now live
beside the module they exercise, as ``acme/foo_test.py`` -- see
``pytest.ini``.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def pytest_addoption(parser):
    parser.addoption(
        "--integration", action="store_true", default=False,
        help="also run tests that need the real camera on the bench")


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: needs real hardware; opt in with "
                   "--integration")


def pytest_collection_modifyitems(config, items):
    """Skip hardware tests unless asked for.

    They open the camera, so they fail whenever ComfyUI or anything
    else holds it -- which is most of the time during development.
    Opt-in keeps a red suite meaning something.
    """
    if config.getoption("--integration"):
        return
    import pytest
    skip = pytest.mark.skip(reason="needs --integration and the bench rig")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)
