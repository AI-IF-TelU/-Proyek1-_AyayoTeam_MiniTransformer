"""Checkpoint roundtrip test (C10)."""

import os
import tempfile

import torch

from src.model.minigpt import MiniGPT
from src.train import load_checkpoint, save_checkpoint


def test_checkpoint_roundtrip():
    m = MiniGPT(vocab_size=6, n_layers=1, n_heads=2, d_model=4, context_length=8)
    vocab = {"a": 4}
    cfg = {"d_model": 4}
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "ckpt.pt")
        save_checkpoint(path, m, vocab=vocab, config=cfg)
        loaded = load_checkpoint(path)
        assert set(loaded["state_dict"].keys()) == set(m.state_dict().keys())
        for k in m.state_dict():
            assert torch.allclose(loaded["state_dict"][k], m.state_dict()[k])
        assert loaded["vocab"] == vocab
        assert loaded["config"] == cfg