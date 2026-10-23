"""Shared helpers for Mini-Transformer contract tests."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BASE_CONFIG = {
    "n_layers": 2,
    "n_heads": 4,
    "d_model": 64,
    "context_length": 64,
    "d_ff": 256,
    "dropout": 0.1,
}

PAD_ID, BOS_ID, EOS_ID, UNK_ID = 0, 1, 2, 3


def make_batch(B, T=64, V=100, pad_id=PAD_ID):
    import torch

    torch.manual_seed(42)
    x = torch.randint(4, V, (B, T), dtype=torch.long)
    mask = torch.rand(B, T) < 0.1
    x = x.masked_fill(mask, pad_id)
    y = torch.zeros_like(x)
    y[:, 1:] = x[:, :-1]
    y[:, 0] = pad_id
    return x, y


def make_tokenizer_corpus():
    return [
        "Hello, world! This is a test.",
        "hello world hello world",
        "Punctuation: a,b;c. d? e!",
    ]


def assert_shape(tensor, expected):
    assert tuple(tensor.shape) == tuple(expected), (
        f"shape mismatch: got {tuple(tensor.shape)}, expected {tuple(expected)}"
    )


def make_model(kind, cfg=None):
    cfg = cfg or BASE_CONFIG
    if kind == "pe":
        from src.model.positional_encoding import SinCosPositionalEncoding

        return SinCosPositionalEncoding(cfg["d_model"], cfg["context_length"])
    if kind == "attn":
        from src.model.attention import CausalMultiHeadAttention

        return CausalMultiHeadAttention(cfg["d_model"], cfg["n_heads"], dropout=cfg["dropout"])
    if kind == "decoder":
        from src.model.decoder_block import DecoderBlock

        return DecoderBlock(cfg["d_model"], cfg["n_heads"], cfg["d_ff"], cfg["dropout"])
    if kind == "minigpt":
        from src.model.minigpt import MiniGPT

        return MiniGPT(
            vocab_size=100,
            d_model=cfg["d_model"],
            n_heads=cfg["n_heads"],
            n_layers=cfg["n_layers"],
            d_ff=cfg["d_ff"],
            context_length=cfg["context_length"],
            dropout=cfg["dropout"],
        )
    raise ValueError(f"unknown model kind: {kind}")
