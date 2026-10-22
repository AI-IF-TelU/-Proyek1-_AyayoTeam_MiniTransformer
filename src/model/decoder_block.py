import torch
import torch.nn as nn


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

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        raise NotImplementedError("implemented in subtasks B10-B11")