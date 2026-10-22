import torch
import torch.nn as nn


class CausalMultiHeadAttention(nn.Module):
    """Causal multi-head self-attention manual per TECH_SPEC 6 / ADR-002.

    - Kontrak:
    - `forward(x: [B, T, d_model]) -> [B, T, d_model]`;
    - `d_model % n_heads == 0` (head_dim = d_model // n_heads), pelanggaran
      -> `ValueError`;
    - proyeksi `W_q, W_k, W_v, W_o = Linear(d_model, d_model)`;
    - reshape `[B, T, d] -> [B, H, T, d/H]`, skala `1/sqrt(head_dim)`;
    - causal mask aditif `-inf` segitiga atas sebelum softmax;
    - dropout pada skor sebelum softmax dan pada output attention.
    """

    def __init__(self, d_model: int, n_heads: int, dropout: float = 0.1) -> None:
        super().__init__()
        self.d_model = d_model
        self.n_heads = n_heads
        self.dropout = dropout

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        raise NotImplementedError("implemented in subtasks B5-B8")