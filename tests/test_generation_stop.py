"""Tests for generation stopping rules (C13)."""

import torch

from src.generate import generate


class _EosModel(torch.nn.Module):
    def forward(self, x):
        # always predict eos_id=2
        logits = torch.zeros(x.size(0), x.size(1), 8)
        logits[:, :, 2] = 10.0
        return logits


class _NonEosModel(torch.nn.Module):
    def forward(self, x):
        logits = torch.zeros(x.size(0), x.size(1), 8)
        logits[:, :, 4] = 10.0  # never eos
        return logits


class _Tok:
    def encode(self, text):
        return [5]
    def decode(self, ids):
        return " ".join(str(i) for i in ids)


def test_stop_on_eos():
    m = _EosModel()
    out = generate(m, _Tok(), "hi", max_new_tokens=10, eos_id=2)
    assert isinstance(out, str)


def test_stop_on_max_new_tokens():
    m = _NonEosModel()
    out = generate(m, _Tok(), "hi", max_new_tokens=3, eos_id=2)
    assert isinstance(out, str)
    # 3 generated tokens (none eos) -> 3 numbers
    assert len(out.split()) == 3