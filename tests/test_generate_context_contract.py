"""Tes regresi `generate` mengikuti `model.context_length` (F-D9-02, D14).

`<eos>` selalu dinetralkan (`eos_id=-1`) agar hasil tidak bergantung pada bobot
acak: pada D10 terbukti 7/10 inisialisasi berhenti lebih dulu di `<eos>`.
"""

import torch

from src.generate import generate
from src.model.minigpt import MiniGPT


class _Tok:
    def encode(self, text):
        return [5]

    def decode(self, ids):
        return " ".join(str(i) for i in ids)


class _RecordingModel(torch.nn.Module):
    """Model stub yang mencatat panjang konteks tiap panggilan forward."""

    def __init__(self, context_length: int):
        super().__init__()
        self.context_length = context_length
        self.dummy = torch.nn.Parameter(torch.zeros(1))
        self.seen = []

    def forward(self, x):
        self.seen.append(x.size(1))
        logits = torch.zeros(x.size(0), x.size(1), 8)
        logits[..., 4] = 1.0  # tidak pernah <eos>
        return logits


def test_default_context_length_follows_model_context_length():
    model = MiniGPT(vocab_size=8, n_layers=1, n_heads=2, d_model=8,
                    context_length=8, dropout=0.0)
    out = generate(model, _Tok(), "hi", max_new_tokens=10, eos_id=-1)
    assert isinstance(out, str)
    assert out.strip() != ""


def test_default_window_is_model_context_length_not_64():
    model = _RecordingModel(context_length=6)
    generate(model, _Tok(), "hi", max_new_tokens=8, eos_id=-1)
    assert max(model.seen) == 6


def test_explicit_context_length_still_honoured():
    model = _RecordingModel(context_length=64)
    generate(model, _Tok(), "hi", max_new_tokens=10, context_length=8, eos_id=-1)
    assert max(model.seen) == 8


def test_model_without_context_length_attribute_falls_back_to_64():
    model = _RecordingModel(context_length=64)
    del model.context_length
    generate(model, _Tok(), "hi", max_new_tokens=5, eos_id=-1)
    # prompt [1, 5] + 5 token baru, 5 panggilan forward: panjang 2..6 (tidak terpotong)
    assert max(model.seen) == 6
