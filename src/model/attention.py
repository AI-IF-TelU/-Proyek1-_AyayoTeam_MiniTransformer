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
        if n_heads <= 0 or d_model % n_heads != 0:
            raise ValueError(
                f"d_model ({d_model}) must be divisible by n_heads ({n_heads})"
            )
        self.d_model = d_model
        self.n_heads = n_heads
        self.head_dim = d_model // n_heads
        self.dropout = dropout
        self.w_q = nn.Linear(d_model, d_model)
        self.w_k = nn.Linear(d_model, d_model)
        self.w_v = nn.Linear(d_model, d_model)
        self.w_o = nn.Linear(d_model, d_model)

    def _project_qkv(
        self, x: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """x: [B, T, d_model] -> q, k, v: [B, T, d_model]."""
        return self.w_q(x), self.w_k(x), self.w_v(x)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        raise NotImplementedError("implemented in subtasks B6-B8")