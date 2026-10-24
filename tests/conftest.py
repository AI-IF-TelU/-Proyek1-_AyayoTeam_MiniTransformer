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
    make_tiny_corpus,
    set_seed,
    get_special_ids,
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


@pytest.fixture(autouse=True)
def seed_everything():
    set_seed(42)
    yield


@pytest.fixture
def base_config():
    return dict(BASE_CONFIG)


@pytest.fixture
def batch():
    return make_batch(4, 64)


@pytest.fixture
def special_ids():
    return {"pad": PAD_ID, "bos": BOS_ID, "eos": EOS_ID, "unk": UNK_ID}


@pytest.fixture
def special_ids_dict():
    return get_special_ids()


@pytest.fixture
def tiny_corpus():
    return make_tiny_corpus()


@pytest.fixture
def tokenizer_cls():
    from src.data.tokenizer import Tokenizer

    return Tokenizer


@pytest.fixture
def make_tokenizer(tokenizer_cls):
    def _make():
        return tokenizer_cls()

    return _make


@pytest.fixture
def device():
    try:
        import torch  # type: ignore

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"
