"""Tests for MiniGPT logits shape/dtype and context-length guard (C6)."""

import torch

from src.model.minigpt import MiniGPT


def test_logits_shape_and_dtype():
    m = MiniGPT(vocab_size=12, n_layers=2, n_heads=2, d_model=8, context_length=64)
    x = torch.randint(0, 12, (4, 16), dtype=torch.long)
    out = m(x)
    assert tuple(out.shape) == (4, 16, 12)
    assert out.dtype == torch.float32
    assert torch.isfinite(out).all()


def test_valueerror_when_t_exceeds_context():
    m = MiniGPT(vocab_size=12, n_layers=1, n_heads=2, d_model=8, context_length=8)
    x = torch.randint(0, 12, (2, 9), dtype=torch.long)
    try:
        m(x)
        raised = False
    except ValueError:
        raised = True
    assert raised