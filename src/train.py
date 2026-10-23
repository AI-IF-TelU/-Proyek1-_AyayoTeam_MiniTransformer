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


def evaluate(model, data_loader, criterion) -> float:
    model.eval()
    total = 0.0
    n = 0
    with torch.no_grad():
        for x, y in data_loader:
            logits = model(x)
            b, t, v = logits.shape
            loss = criterion(logits.reshape(b * t, v), y.reshape(b * t))
            total += float(loss.item()) * x.size(0)
            n += x.size(0)
    return total / max(n, 1)


def train(
    model,
    train_loader,
    val_loader,
    epochs: int = 10,
    lr: float = 3e-4,
    weight_decay: float = 0.01,
    pad_id: int = 0,
    seed: int = 42,
):
    set_seed(seed)
    optimizer = make_optimizer(model, lr=lr, weight_decay=weight_decay)
    criterion = make_criterion(pad_id=pad_id)
    history = []
    for epoch in range(1, epochs + 1):
        model.train()
        total = 0.0
        n = 0
        for x, y in train_loader:
            loss = training_step(model, x, y, optimizer, criterion)
            total += loss * x.size(0)
            n += x.size(0)
        train_loss = total / max(n, 1)
        val_loss = evaluate(model, val_loader, criterion)
        history.append(
            {"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss}
        )
    return history