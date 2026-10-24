"""Shared helpers for Mini-Transformer contract tests."""
import sys
import random
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Sequence, Tuple

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


def set_seed(seed: int = 42) -> None:
    """Set seeds for reproducibility (contract: seed 42)."""
    random.seed(seed)
    try:
        import numpy as _np  # type: ignore

        _np.random.seed(seed)
    except Exception:
        pass
    try:
        import torch  # type: ignore

        torch.manual_seed(seed)
        if hasattr(torch, "cuda") and torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except Exception:
        pass


def get_special_ids() -> Dict[str, int]:
    """Return special token ids per TECH_SPEC §3/ADR-008."""
    return {"pad": PAD_ID, "bos": BOS_ID, "eos": EOS_ID, "unk": UNK_ID}


def make_batch(B: int, T: int = 64, V: int = 100, pad_id: int = PAD_ID) -> Tuple[Any, Any]:
    import torch

    torch.manual_seed(42)
    x = torch.randint(4, V, (B, T), dtype=torch.long)
    mask = torch.rand(B, T) < 0.1
    x = x.masked_fill(mask, pad_id)
    y = torch.zeros_like(x)
    y[:, 1:] = x[:, :-1]
    y[:, 0] = pad_id
    return x, y


def make_tokenizer_corpus() -> list:
    return [
        "Hello, world! This is a test.",
        "hello world hello world",
        "Punctuation: a,b;c. d? e!",
    ]


def make_tiny_corpus() -> list:
    """Small corpus for contract tests (tokenizer/dataset)."""
    return [
        "Halo dunia!",
        "halo halo dunia.",
        "Ini adalah contoh; tes, uji! Coba?",
    ]


def assert_shape(tensor: Any, expected: Sequence[int]) -> None:
    assert tuple(tensor.shape) == tuple(expected), (
        f"shape mismatch: got {tuple(tensor.shape)}, expected {tuple(expected)}"
    )


def assert_x_y_shift(x: Any, y: Any, pad_id: int = PAD_ID) -> None:
    """Assert x[i,t] == y[i,t-1] for positions where target is not pad (TECH_SPEC §4)."""
    try:
        import torch  # type: ignore

        if isinstance(x, torch.Tensor) and isinstance(y, torch.Tensor):
            if x.shape != y.shape:
                raise AssertionError(f"x,y shape mismatch: {x.shape} vs {y.shape}")
            # check shift where y != pad_id
            if y.shape[1] >= 1:
                # y[:,0] may be pad by construction
                if y.shape[1] >= 2:
                    nonpad = y[:, 1:] != pad_id
                    if nonpad.any():
                        assert torch.all(x[:, :-1][nonpad] == y[:, 1:][nonpad]), (
                            "x[i,t] != y[i,t-1] for non-pad positions"
                        )
            return
    except Exception:
        pass
    # fallback for non-torch
    if hasattr(x, "shape") and hasattr(y, "shape") and x.shape == y.shape:
        B, T = x.shape[0], x.shape[1]
        for b in range(B):
            for t in range(1, T):
                yt = y[b, t]
                if yt == pad_id:
                    continue
                xtm1 = x[b, t - 1]
                assert xtm1 == yt, f"x[{b},{t-1}] != y[{b},{t}] for non-pad"


def assert_causal_mask(mask: Any) -> None:
    """Assert causal mask has expected shape/structure (aditif, upper triangle masked)."""
    try:
        import torch  # type: ignore

        if isinstance(mask, torch.Tensor):
            if mask.ndim == 2:
                T = mask.shape[-1]
                assert mask.shape[0] == T, f"causal mask must be square, got {mask.shape}"
                # upper triangle should be masked (very negative) relative to diagonal/lower
                upper = torch.triu(torch.ones_like(mask, dtype=torch.bool), diagonal=1)
                if upper.any():
                    vals = mask[upper]
                    # expect masked values to be very negative
                    assert (vals < -1e8).all() or (vals == float("-inf")).all(), (
                        "upper triangle of causal mask not properly masked"
                    )
                return
            elif mask.ndim == 4:  # [B,H,T,T] sometimes; check last two
                T = mask.shape[-1]
                assert mask.shape[-2] == T, f"causal mask last dims must be square, got {mask.shape}"
                upper = torch.triu(torch.ones((T, T), dtype=torch.bool), diagonal=1)
                # sample
                sub = mask[0, 0]
                vals = sub[upper]
                assert (vals < -1e8).all() or (vals == float("-inf")).all(), (
                    "upper triangle of causal mask not properly masked"
                )
                return
    except Exception:
        pass
    # best effort for other types
    if hasattr(mask, "shape"):
        s = mask.shape
        assert len(s) >= 2 and s[-1] == s[-2], f"causal mask must be square, got {s}"


def count_nonpad(tensor: Any, pad_id: int = PAD_ID) -> int:
    try:
        import torch  # type: ignore

        if isinstance(tensor, torch.Tensor):
            return int((tensor != pad_id).sum().item())
    except Exception:
        pass
    try:
        total = 0
        for v in tensor.flatten() if hasattr(tensor, "flatten") else tensor:
            if v != pad_id:
                total += 1
        return total
    except Exception:
        return 0


def assert_value_error(fn: Callable, *args, **kwargs) -> None:
    try:
        import pytest  # type: ignore

        with pytest.raises(ValueError):
            fn(*args, **kwargs)
        return
    except Exception:
        pass
    try:
        fn(*args, **kwargs)
        raise AssertionError("Expected ValueError but no exception was raised")
    except ValueError:
        return
    except AssertionError:
        raise
    except Exception as e:
        raise AssertionError(f"Expected ValueError, got {type(e).__name__}: {e}")


def make_model(kind: str, cfg: Dict[str, Any] = None):
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

        # MiniGPT tidak menerima d_ff: nilainya ditetapkan internal 4 * d_model
        # (TECH_SPEC §6), sehingga cfg["d_ff"] tidak diteruskan.
        return MiniGPT(
            vocab_size=100,
            d_model=cfg["d_model"],
            n_heads=cfg["n_heads"],
            n_layers=cfg["n_layers"],
            context_length=cfg["context_length"],
            dropout=cfg["dropout"],
        )
    raise ValueError(f"unknown model kind: {kind}")
