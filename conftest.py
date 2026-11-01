"""pytest options for the whole repo. Fixtures are in gengo/test/conftest.py;
command-line options have to be declared here, at the root, for a bare
`pytest` to accept them."""
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--browser-tests", action="store_true",
        help="also run the browser tests (needs playwright and its browsers)")


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "browser: drives a real browser; run with --browser-tests")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--browser-tests"):
        return
    skip = pytest.mark.skip(reason="browser test; run with --browser-tests")
    for item in items:
        if "browser" in item.keywords:
            item.add_marker(skip)
