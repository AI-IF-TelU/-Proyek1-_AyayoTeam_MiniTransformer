"""Test that one training step updates parameters and yields finite loss (C8)."""

import torch

from src.model.minigpt import MiniGPT
from src.train import make_criterion, make_optimizer, training_step


def test_parameter_update():
    torch.manual_seed(0)
    m = MiniGPT(vocab_size=8, n_layers=1, n_heads=2, d_model=4, context_length=8)
    opt = make_optimizer(m, lr=1e-2)
    crit = make_criterion(pad_id=0)
    x = torch.randint(0, 8, (2, 6), dtype=torch.long)
    y = torch.randint(0, 8, (2, 6), dtype=torch.long)
    y[:, 0] = 0  # pad positions
    before = m.lm_head.weight.detach().clone()
    loss = training_step(m, x, y, opt, crit)
    after = m.lm_head.weight.detach()
    assert torch.isfinite(torch.tensor(loss))
    assert not torch.allclose(before, after)