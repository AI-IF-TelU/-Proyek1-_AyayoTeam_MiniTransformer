import torch
import torch.nn as nn


class SinCosPositionalEncoding(nn.Module):
    """Sinusoidal positional encoding per TECH_SPEC 6.

    - Kontrak:
    - buffer `pe: [max_len, d_model]` non-trainable;
    - `forward(x: [B, T, d_model]) -> [B, T, d_model]`, menambahkan `pe[:T]`;
    - `T > max_len` -> `ValueError`.
    """

    def __init__(self, d_model: int, max_len: int) -> None:
        super().__init__()
        self.d_model = d_model
        self.max_len = max_len

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        raise NotImplementedError("implemented in subtask B3")