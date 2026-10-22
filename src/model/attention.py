import math

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
        self.attn_dropout = nn.Dropout(dropout)
        self.out_dropout = nn.Dropout(dropout)
        self.w_q = nn.Linear(d_model, d_model)
        self.w_k = nn.Linear(d_model, d_model)
        self.w_v = nn.Linear(d_model, d_model)
        self.w_o = nn.Linear(d_model, d_model)

    def _project_qkv(
        self, x: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """x: [B, T, d_model] -> q, k, v: [B, T, d_model]."""
        return self.w_q(x), self.w_k(x), self.w_v(x)

    def _causal_mask(
        self,
        t: int,
        device: torch.device | None = None,
        dtype: torch.dtype | None = None,
    ) -> torch.Tensor:
        """Additive causal mask: `-inf` strictly above the diagonal.

        Returns `[1, 1, T, T]`, broadcast-compatible with scores
        `[B, H, T, T]`. Position `i` may attend to `j <= i` only;
        `T = 1` yields a single zero (no future positions).
        """
        idx = torch.arange(t, device=device)
        mask = torch.where(idx[None, :] > idx[:, None], float("-inf"), 0.0)
        if dtype is not None:
            mask = mask.to(dtype)
        return mask.view(1, 1, t, t)

    def _scaled_dot_product_attention(
        self,
        q: torch.Tensor,
        k: torch.Tensor,
        v: torch.Tensor,
        mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Scaled dot-product attention per head (subtask B6).

        - q, k, v: [B, H, T, head_dim] -> out: [B, H, T, head_dim];
        - skor QK^T / sqrt(head_dim), dropout skor pre-softmax,
          softmax, lalu @ V;
        - `mask` tambahan aditif [B, H, T, T]-compatible dijumlahkan
          ke skor sebelum softmax (dipakai causal mask di B7).
        """
        for name, tensor in (("q", q), ("k", k), ("v", v)):
            if tensor.dim() != 4:
                raise ValueError(
                    f"{name}: expected 4D [B, H, T, head_dim], got {tensor.dim()}D"
                )
            if tensor.size(-1) != self.head_dim:
                raise ValueError(
                    f"{name}: expected last dim {self.head_dim}, "
                    f"got {tensor.size(-1)}"
                )
        scale = 1.0 / math.sqrt(self.head_dim)
        scores = q @ k.transpose(-2, -1) * scale  # [B, H, T, T]
        scores = self.attn_dropout(scores)
        if mask is not None:
            scores = scores + mask
        probs = torch.softmax(scores, dim=-1)  # [B, H, T, T]
        return probs @ v  # [B, H, T, head_dim]

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: [B, T, d_model] -> [B, T, d_model] (subtasks B5-B8).

        Alur: proyeksi Q/K/V -> split [B, H, T, head_dim] ->
        scaled dot-product attention dgn causal mask -> gabung head ->
        output projection `W_o` -> dropout output attention.
        """
        if x.dim() != 3:
            raise ValueError(
                f"expected 3D input [B, T, d_model], got {x.dim()}D"
            )
        if x.size(-1) != self.d_model:
            raise ValueError(
                f"expected last dim {self.d_model}, got {x.size(-1)}"
            )
        b, t, d = x.size()
        q, k, v = self._project_qkv(x)  # masing-masing [B, T, d_model]
        q = q.view(b, t, self.n_heads, self.head_dim).transpose(1, 2)
        k = k.view(b, t, self.n_heads, self.head_dim).transpose(1, 2)
        v = v.view(b, t, self.n_heads, self.head_dim).transpose(1, 2)
        mask = self._causal_mask(t, device=x.device, dtype=x.dtype)
        attn_out = self._scaled_dot_product_attention(q, k, v, mask)  # [B, H, T, d/H]
        attn_out = attn_out.transpose(1, 2).contiguous().view(b, t, d)
        out = self.w_o(attn_out)  # output projection [B, T, d_model]
        return self.out_dropout(out)