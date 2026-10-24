"""Training utilities for MiniGPT (contract: TECH_SPEC 6, ADR-011)."""

import json
import os
import random

import numpy as np
import torch
import torch.nn as nn


def write_metrics_jsonl(history, path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for rec in history:
            f.write(json.dumps(rec) + "\n")


def save_checkpoint(path: str, model, vocab=None, config=None) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    torch.save(
        {"state_dict": model.state_dict(), "vocab": vocab, "config": config},
        path,
    )

def load_checkpoint(path: str):
    return torch.load(path, map_location="cpu")


def get_device() -> torch.device:
    """Pick CUDA when available, otherwise CPU."""
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


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


def _model_device(model) -> torch.device:
    if hasattr(model, 'parameters'):
        param = next(model.parameters(), None)
        if param is not None:
            return param.device
    return torch.device("cpu")


def training_step(model, x, y, optimizer, criterion) -> float:
    model.train()
    device = _model_device(model)
    x, y = x.to(device), y.to(device)
    optimizer.zero_grad()
    logits = model(x)
    b, t, v = logits.shape
    loss = criterion(logits.reshape(b * t, v), y.reshape(b * t))
    loss.backward()
    optimizer.step()
    return float(loss.item())


def evaluate(model, data_loader, criterion) -> float:
    model.eval()
    param = next(model.parameters(), None)
    total = 0.0
    n = 0
    with torch.no_grad():
        for x, y in data_loader:
            device = _model_device(model)
            x, y = x.to(device), y.to(device)
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
    metrics_path: str = None,
    checkpoint_path: str = None,
    vocab=None,
    config=None,
    on_epoch=None,
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
        rec = {"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss}
        history.append(rec)
        if on_epoch is not None:
            on_epoch(rec)
    if metrics_path is not None:
        write_metrics_jsonl(history, metrics_path)
    if checkpoint_path is not None:
        save_checkpoint(checkpoint_path, model, vocab=vocab, config=config)
    return history