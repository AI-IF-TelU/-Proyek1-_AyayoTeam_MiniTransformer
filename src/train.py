"""Training utilities for MiniGPT (contract: TECH_SPEC 6, ADR-011)."""

import random

import numpy as np
import torch
import torch.nn as nn


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def make_criterion(pad_id: int = 0) -> nn.CrossEntropyLoss:
    return nn.CrossEntropyLoss(ignore_index=pad_id)


def make_optimizer(model, lr: float = 3e-4, weight_decay: float = 0.01):
    return torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)


def training_step(model, x, y, optimizer, criterion) -> float:
    model.train()
    optimizer.zero_grad()
    logits = model(x)
    b, t, v = logits.shape
    loss = criterion(logits.reshape(b * t, v), y.reshape(b * t))
    loss.backward()
    optimizer.step()
    return float(loss.item())