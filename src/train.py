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


def evaluate_per_document(model, doc_batches, pad_id: int = 0, ignore_ids=()):
    """Loss aggregated per document, so each held-out article counts once.

    `doc_batches` yields `(x, y, doc_ids)` where `doc_ids[i]` names the document
    row `i` came from. Sliding-window evaluation repeats one article ~54x; that
    inflates the token count without adding evidence. Here chunk losses are
    averaged per document first, then every document contributes one sample.

    `ignore_ids` excludes target tokens from the average (e.g. `<unk>`), which
    ADR-013 requires because an OOV token is impossible to predict: including it
    mixes tokenizer coverage into a model-quality number. A document whose every
    target token is ignored carries no evidence and is dropped, not counted as
    zero loss.

    Returns (mean_loss, stddev, n_documents).
    """
    model.eval()
    ignored = tuple(int(i) for i in ignore_ids if int(i) != pad_id)
    per_doc_sum = {}
    per_doc_count = {}
    with torch.no_grad():
        for x, y, doc_ids in doc_batches:
            x, y = x.to(_model_device(model)), y.to(_model_device(model))
            logits = model(x)
            flat_logits = logits.reshape(-1, logits.size(-1))
            flat_target = y.reshape(-1)
            tok_loss = torch.nn.functional.cross_entropy(
                flat_logits, flat_target, ignore_index=pad_id, reduction="none"
            )
            keep = (flat_target != pad_id).reshape(y.shape)
            for value in ignored:
                keep &= y != value
            row_sum = (tok_loss.reshape(y.shape) * keep).sum(dim=1)
            row_count = keep.sum(dim=1)
            for row, doc in enumerate(doc_ids):
                doc = int(doc)
                per_doc_sum[doc] = per_doc_sum.get(doc, 0.0) + float(row_sum[row])
                per_doc_count[doc] = per_doc_count.get(doc, 0) + int(row_count[row])

    losses = [per_doc_sum[d] / per_doc_count[d]
              for d in sorted(per_doc_sum) if per_doc_count[d] > 0]
    if not losses:
        return float("nan"), float("nan"), 0
    mean = sum(losses) / len(losses)
    if len(losses) < 2:
        return mean, 0.0, 1
    var = sum((v - mean) ** 2 for v in losses) / (len(losses) - 1)
    return mean, var ** 0.5, len(losses)


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