"""Mock-flow shape test for MiniGPT (C4).

This verifies the [B, T] -> [B, T, V] pipeline using shape-preserving stubs
for PE and DecoderBlock. It is NOT final integration (see C5/C6).
"""

import torch
import torch.nn as nn

from src.model import minigpt as minigpt_mod


class _ShapePE(nn.Module):
    def forward(self, x):
        return x


class _ShapeBlock(nn.Module):
    def forward(self, x):
        return x


def test_mock_flow_shape():
    minigpt_mod.SinCosPositionalEncoding = _ShapePE
    minigpt_mod.DecoderBlock = _ShapeBlock
    m = minigpt_mod.MiniGPT(vocab_size=10, n_layers=2, n_heads=2, d_model=4, context_length=8)
    x = torch.randint(0, 10, (3, 5), dtype=torch.long)
    out = m(x)
    assert tuple(out.shape) == (3, 5, 10)
    assert out.dtype == torch.float32


def test_valueerror_on_long_sequence():
    minigpt_mod.SinCosPositionalEncoding = _ShapePE
    minigpt_mod.DecoderBlock = _ShapeBlock
    m = minigpt_mod.MiniGPT(vocab_size=10, n_layers=1, n_heads=2, d_model=4, context_length=4)
    x = torch.randint(0, 10, (2, 5), dtype=torch.long)
    try:
        m(x)
        raised = False
    except ValueError:
        raised = True
    assert raised