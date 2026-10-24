"""Tes penulisan metrics JSONL oleh `train()` (gap Issue C #3, D14).

`TECH_SPEC.md` §6 dan ADR-011 menetapkan metrik per-epoch ditulis ke
`outputs/metrics/` sebagai JSONL: satu objek JSON per baris. Sebelum tes ini
tidak ada tes yang menyentuh `write_metrics_jsonl`/`metrics_path` sama sekali,
sehingga acceptance criterion Issue #4 nomor 3 tidak terverifikasi.
"""

import json
import os

import torch
from torch.utils.data import DataLoader, TensorDataset

from src.model.minigpt import MiniGPT
from src.train import train, write_metrics_jsonl

VOCAB_SIZE = 16
PAD_ID = 0
CONTEXT_LENGTH = 8


def _loader(batch_size: int = 2) -> DataLoader:
    x = torch.tensor(
        [[4, 5, 6, 7, PAD_ID, PAD_ID, PAD_ID, PAD_ID],
         [8, 9, 10, 11, PAD_ID, PAD_ID, PAD_ID, PAD_ID],
         [4, 5, 6, 7, PAD_ID, PAD_ID, PAD_ID, PAD_ID],
         [8, 9, 10, 11, PAD_ID, PAD_ID, PAD_ID, PAD_ID]],
        dtype=torch.long,
    )
    y = torch.tensor(
        [[5, 6, 7, PAD_ID, PAD_ID, PAD_ID, PAD_ID, PAD_ID],
         [9, 10, 11, PAD_ID, PAD_ID, PAD_ID, PAD_ID, PAD_ID],
         [5, 6, 7, PAD_ID, PAD_ID, PAD_ID, PAD_ID, PAD_ID],
         [9, 10, 11, PAD_ID, PAD_ID, PAD_ID, PAD_ID, PAD_ID]],
        dtype=torch.long,
    )
    return DataLoader(TensorDataset(x, y), batch_size=batch_size)


def _model() -> MiniGPT:
    return MiniGPT(vocab_size=VOCAB_SIZE, n_layers=1, n_heads=2, d_model=8,
                   context_length=CONTEXT_LENGTH, dropout=0.0)


def test_train_writes_one_jsonl_line_per_epoch(tmp_path):
    metrics_path = os.path.join(str(tmp_path), "metrics", "run.jsonl")
    loader = _loader()
    history = train(_model(), loader, loader, epochs=3, lr=1e-3,
                    pad_id=PAD_ID, seed=42, metrics_path=metrics_path)

    assert os.path.exists(metrics_path)
    with open(metrics_path, encoding="utf-8") as f:
        lines = [line for line in f.read().splitlines() if line.strip()]

    assert len(lines) == 3
    assert len(history) == 3

    records = [json.loads(line) for line in lines]
    assert [r["epoch"] for r in records] == [1, 2, 3]
    for rec, hist in zip(records, history):
        assert set(rec) == {"epoch", "train_loss", "val_loss"}
        assert rec["train_loss"] == hist["train_loss"]
        assert rec["val_loss"] == hist["val_loss"]
        assert isinstance(rec["train_loss"], float)
        assert isinstance(rec["val_loss"], float)
        assert torch.isfinite(torch.tensor(rec["train_loss"]))
        assert torch.isfinite(torch.tensor(rec["val_loss"]))


def test_train_without_metrics_path_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    train(_model(), _loader(), _loader(), epochs=1, lr=1e-3,
          pad_id=PAD_ID, seed=42, metrics_path=None)
    assert list(tmp_path.iterdir()) == []


def test_write_metrics_jsonl_overwrites_not_appends(tmp_path):
    path = os.path.join(str(tmp_path), "metrics.jsonl")
    write_metrics_jsonl([{"epoch": 1, "train_loss": 1.0, "val_loss": 2.0}], path)
    write_metrics_jsonl([{"epoch": 1, "train_loss": 3.0, "val_loss": 4.0}], path)
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["train_loss"] == 3.0
