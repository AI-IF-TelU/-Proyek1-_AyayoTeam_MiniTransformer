import torch
import torch.nn as nn

from src.model.attention import CausalMultiHeadAttention


class FeedForward(nn.Module):
    """Position-wise Feed-Forward Network dengan GELU per TECH_SPEC 6 / ADR-007.

    - Kontrak:
    - `Linear(d_model, d_ff)` -> GELU -> `Linear(d_ff, d_model)` -> dropout;
    - baseline `d_ff = 4 * d_model = 256`, dropout `0.1`;
    - `forward(x: [B, T, d_model]) -> [B, T, d_model]`, identik per posisi;
    - `d_model <= 0` atau `d_ff <= 0` -> `ValueError` saat inisialisasi.
    """

    def __init__(self, d_model: int, d_ff: int, dropout: float = 0.1) -> None:
        super().__init__()
        if d_model <= 0 or d_ff <= 0:
            raise ValueError(
                f"d_model ({d_model}) and d_ff ({d_ff}) must be positive"
            )
        self.d_model = d_model
        self.d_ff = d_ff
        self.dropout = dropout
        self.fc1 = nn.Linear(d_model, d_ff)
        self.activation = nn.GELU()
        self.fc2 = nn.Linear(d_ff, d_model)
        self.drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: [B, T, d_model] -> [B, T, d_model]."""
        if x.dim() != 3:
            raise ValueError(
                f"expected 3D input [B, T, d_model], got {x.dim()}D"
            )
        if x.size(-1) != self.d_model:
            raise ValueError(
                f"expected last dim {self.d_model}, got {x.size(-1)}"
            )
        return self.drop(self.fc2(self.activation(self.fc1(x))))


class DecoderBlock(nn.Module):
    """Pre-LayerNorm decoder block per TECH_SPEC 6 / ADR-007.

    - Kontrak:
    - `forward(x: [B, T, d_model]) -> [B, T, d_model]`;
    - pre-norm (baseline): `x = x + CausalMHA(LayerNorm(x))`,
      `x = x + FFN(LayerNorm(x))`;
    - FFN: `Linear(d_model, d_ff)` -> GELU -> `Linear(d_ff, d_model)`
      -> dropout; baseline `d_ff = 4 * d_model = 256`;
    - LayerNorm epsilon `1e-5`.
    """

    def __init__(
        self,
        d_model: int,
        n_heads: int,
        d_ff: int,
        dropout: float = 0.1,
        layer_norm_eps: float = 1e-5,
        pre_norm: bool = True,
    ) -> None:
        super().__init__()
        if d_model <= 0 or d_ff <= 0:
            raise ValueError(
                f"d_model ({d_model}) and d_ff ({d_ff}) must be positive"
            )
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_ff = d_ff
        self.dropout = dropout
        self.layer_norm_eps = layer_norm_eps
        self.pre_norm = pre_norm
        self.norm1 = nn.LayerNorm(d_model, eps=layer_norm_eps)
        self.attn = CausalMultiHeadAttention(d_model, n_heads, dropout)
        self.norm2 = nn.LayerNorm(d_model, eps=layer_norm_eps)
        self.ffn = FeedForward(d_model, d_ff, dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: [B, T, d_model] -> [B, T, d_model].

        - pre-norm: `x + CausalMHA(LayerNorm(x))`, `x + FFN(LayerNorm(x))`;
        - post-norm: `LayerNorm(x + CausalMHA(x))`, `LayerNorm(x + FFN(x))`.
        """
        if x.dim() != 3:
            raise ValueError(
                f"expected 3D input [B, T, d_model], got {x.dim()}D"
            )
        if x.size(-1) != self.d_model:
            raise ValueError(
                f"expected last dim {self.d_model}, got {x.size(-1)}"
            )
        if self.pre_norm:
            x = x + self.attn(self.norm1(x))
            x = x + self.ffn(self.norm2(x))
        else:
            x = self.norm1(x + self.attn(x))
            x = self.norm2(x + self.ffn(x))
        return x