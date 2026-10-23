"""Shared pytest configuration and fixtures for Mini-Transformer tests."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers import (
    BASE_CONFIG,
    PAD_ID,
    BOS_ID,
    EOS_ID,
    UNK_ID,
    make_batch,
)


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run integration-marked tests",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-integration"):
        return
    skip_integration = pytest.mark.skip(
        reason="integration tests require --run-integration"
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


@pytest.fixture
def base_config():
    return dict(BASE_CONFIG)


@pytest.fixture
def batch():
    return make_batch(4, 64)


@pytest.fixture
def special_ids():
    return {"pad": PAD_ID, "bos": BOS_ID, "eos": EOS_ID, "unk": UNK_ID}
"""Shared pytest configuration and fixtures for Mini-Transformer tests."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers import (
    BASE_CONFIG,
    PAD_ID,
    BOS_ID,
    EOS_ID,
    UNK_ID,
    make_batch,
)


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run integration-marked tests",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-integration"):
        return
    skip_integration = pytest.mark.skip(
        reason="integration tests require --run-integration"
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


@pytest.fixture
def base_config():
    return dict(BASE_CONFIG)


@pytest.fixture
def batch():
    return make_batch(4, 64)


@pytest.fixture
def special_ids():
    return {"pad": PAD_ID, "bos": BOS_ID, "eos": EOS_ID, "unk": UNK_ID}
