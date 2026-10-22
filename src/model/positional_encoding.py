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

        positions = torch.arange(max_len, dtype=torch.float32).unsqueeze(1)
        div_term = 10000.0 ** (torch.arange(d_model, dtype=torch.float32) / d_model)
        angles = positions / div_term
        pe = torch.empty(max_len, d_model, dtype=torch.float32)
        pe[:, 0::2] = torch.sin(angles[:, 0::2])
        pe[:, 1::2] = torch.cos(angles[:, 1::2])
        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.dim() != 3:
            raise ValueError(f"expected 3D input [B, T, d_model], got {x.dim()}D")
        if x.size(-1) != self.d_model:
            raise ValueError(f"expected last dim {self.d_model}, got {x.size(-1)}")
        t = x.size(1)
        if t > self.max_len:
            raise ValueError(f"sequence length {t} > max_len {self.max_len}")
        return x + self.pe[:t]