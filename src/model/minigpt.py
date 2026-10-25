"""MiniGPT decoder-only model (contract: TECH_SPEC 6).

Composition: Embedding -> +SinCosPE -> n_layers x DecoderBlock -> LayerNorm -> Linear head.
"""

import torch
import torch.nn as nn

from src.model.decoder_block import DecoderBlock
from src.model.positional_encoding import SinCosPositionalEncoding


class MiniGPT(nn.Module):
    def __init__(
        self,
        vocab_size: int,
        n_layers: int = 2,
        n_heads: int = 4,
        d_model: int = 64,
        context_length: int = 64,
        dropout: float = 0.1,
        layer_norm_eps: float = 1e-5,
        tie_embeddings: bool = False,
    ) -> None:
        super().__init__()
        if vocab_size <= 0:
            raise ValueError(f"vocab_size must be positive, got {vocab_size}")
        if n_layers <= 0:
            raise ValueError(f"n_layers must be positive, got {n_layers}")
        if n_heads <= 0 or d_model % n_heads != 0:
            raise ValueError(
                f"d_model ({d_model}) must be divisible by n_heads ({n_heads})"
            )
        if context_length <= 0:
            raise ValueError(f"context_length must be positive, got {context_length}")
        if not (0.0 <= dropout < 1.0):
            raise ValueError(f"dropout must be in [0,1), got {dropout}")
        if layer_norm_eps <= 0:
            raise ValueError(f"layer_norm_eps must be positive, got {layer_norm_eps}")

        self.vocab_size = vocab_size
        self.n_layers = n_layers
        self.n_heads = n_heads
        self.d_model = d_model
        self.context_length = context_length
        self.dropout = dropout
        self.layer_norm_eps = layer_norm_eps
        self.tie_embeddings = bool(tie_embeddings)
        self.d_ff = 4 * d_model

        self.token_emb = nn.Embedding(vocab_size, d_model)
        self.pos_enc = SinCosPositionalEncoding(d_model, context_length)
        self.blocks = nn.ModuleList(
            [
                DecoderBlock(
                    d_model=d_model,
                    n_heads=n_heads,
                    d_ff=self.d_ff,
                    dropout=dropout,
                    layer_norm_eps=layer_norm_eps,
                )
                for _ in range(n_layers)
            ]
        )
        self.ln_f = nn.LayerNorm(d_model, eps=layer_norm_eps)
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)
        if self.tie_embeddings:
            # ADR-014: LM head memakai matriks embedding yang sama (transpose).
            self.lm_head.weight = self.token_emb.weight

    @classmethod
    def from_config(cls, config: dict) -> "MiniGPT":
        """Bangun model dari dict config apa adanya.

        `src/config.py::ModelConfig` menyimpan `d_ff` dan `min_freq`, yang bukan
        parameter konstruktor `MiniGPT` (d_ff = 4 * d_model; min_freq milik
        tokenizer). Tanpa penyaringan ini, memuat checkpoint C15 gagal dengan
        `TypeError: unexpected keyword argument 'min_freq'`.
        """
        import inspect

        allowed = set(inspect.signature(cls.__init__).parameters) - {"self"}
        return cls(**{k: v for k, v in config.items() if k in allowed})

    def forward(self, idx: torch.Tensor) -> torch.Tensor:
        if not torch.is_tensor(idx):
            raise ValueError("idx must be a torch.Tensor")
        if idx.dim() != 2:
            raise ValueError(
                f"expected idx shape [B, T], got {tuple(idx.shape)}"
            )
        if idx.dtype != torch.long:
            raise ValueError(f"expected idx dtype int64 (long), got {idx.dtype}")
        T = idx.size(1)
        if T > self.context_length:
            raise ValueError(
                f"sequence length T={T} exceeds context_length={self.context_length}"
            )

        x = self.token_emb(idx)  # [B, T, d_model]
        x = self.pos_enc(x)  # [B, T, d_model]
        for block in self.blocks:
            x = block(x)  # [B, T, d_model]
        x = self.ln_f(x)  # [B, T, d_model]
        if self.tie_embeddings:
            logits = x @ self.token_emb.weight.t()  # [B, T, vocab_size]
        else:
            logits = self.lm_head(x)  # [B, T, vocab_size]
        return logits.to(torch.float32)