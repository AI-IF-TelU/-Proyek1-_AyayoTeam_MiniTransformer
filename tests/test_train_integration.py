"""Integration smoke test using real Issue A data components (C11)."""

import torch
from torch.utils.data import DataLoader

from src.data.dataset import TextDataset, create_dataloader
from src.data.tokenizer import Tokenizer
from src.model.minigpt import MiniGPT
from src.train import train


def test_integration_one_epoch():
    texts = ["ini berita satu dua tiga"] * 50 + ["berita lain empat lima"] * 50
    tok = Tokenizer()
    tok.fit(texts)
    ds = TextDataset(texts, tok, context_length=8)
    loader = create_dataloader(ds, batch_size=4, shuffle=True, pad_id=0, context_length=8)
    val_loader = create_dataloader(ds, batch_size=4, shuffle=False, pad_id=0, context_length=8)
    m = MiniGPT(vocab_size=tok.vocab_size, n_layers=1, n_heads=2, d_model=8, context_length=8)
    hist = train(m, loader, val_loader, epochs=1, lr=1e-3, pad_id=0, seed=42)
    assert len(hist) == 1
    assert torch.isfinite(torch.tensor(hist[0]["train_loss"]))
    assert torch.isfinite(torch.tensor(hist[0]["val_loss"]))
    # batch shape check
    xb, yb = next(iter(loader))
    assert tuple(xb.shape[1:]) == (8,)
    assert xb.dtype == torch.long