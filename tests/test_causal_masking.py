"""Tes kontrak causal masking (Issue D, subtask D5).

Berbeda dari `tests/test_attention.py` yang menguji helper internal
(`_causal_mask`/`_scaled_dot_product_attention`), file ini membuktikan
perilaku causal lewat `forward` publik sesuai TECH_SPEC 6:

- posisi t hanya bergantung pada posisi <= t (diuji untuk setiap titik potong);
- mask aditif `-inf` benar-benar diterapkan sebelum softmax;
- probabilitas perhatian ke masa depan tepat nol dan tiap baris berjumlah 1;
- edge case T=1, dtype float64, dan skor besar tetap finite/tanpa NaN.

Dropout dinolkan dan modul di-`eval()` agar hasil deterministik; tes tidak
memakai `nn.MultiheadAttention` sebagai referensi, melainkan perhitungan
manual dari parameter modul itu sendiri.
"""
import unittest

import torch

from src.model.attention import CausalMultiHeadAttention

B, T, D_MODEL = 2, 8, 64
N_HEADS = 4
HEAD_DIM = D_MODEL // N_HEADS


def _split_heads(x: torch.Tensor) -> torch.Tensor:
    """[B, T, d_model] -> [B, H, T, head_dim]."""
    b, t, _ = x.shape
    return x.view(b, t, N_HEADS, HEAD_DIM).transpose(1, 2)


def _merge_heads(x: torch.Tensor) -> torch.Tensor:
    """[B, H, T, head_dim] -> [B, T, d_model]."""
    b, _, t, _ = x.shape
    return x.transpose(1, 2).contiguous().view(b, t, D_MODEL)


def _manual_probs_and_output(
    attn: CausalMultiHeadAttention, x: torch.Tensor
) -> tuple[torch.Tensor, torch.Tensor]:
    """Hitung ulang attention causal manual: probs [B,H,T,T], out [B,T,d]."""
    q = _split_heads(attn.w_q(x))
    k = _split_heads(attn.w_k(x))
    v = _split_heads(attn.w_v(x))
    scores = q @ k.transpose(-2, -1) * (HEAD_DIM ** -0.5)
    future = torch.triu(
        torch.ones(scores.shape[-2:], dtype=torch.bool, device=x.device), diagonal=1
    )
    scores = scores.masked_fill(future, float("-inf"))
    probs = torch.softmax(scores, dim=-1)
    return probs, attn.w_o(_merge_heads(probs @ v))


class TestCausalForwardInvariance(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(42)
        self.attn = CausalMultiHeadAttention(D_MODEL, N_HEADS, dropout=0.0).eval()
        self.x = torch.randn(B, T, D_MODEL)

    def test_every_cut_leaves_past_unchanged(self):
        with torch.no_grad():
            base = self.attn(self.x)
            for cut in range(1, T):
                x_mod = self.x.clone()
                x_mod[:, cut:, :] = torch.randn(B, T - cut, D_MODEL)
                out = self.attn(x_mod)
                torch.testing.assert_close(
                    out[:, :cut], base[:, :cut], atol=1e-6, rtol=1e-6
                )
                self.assertFalse(
                    torch.allclose(out[:, cut:], base[:, cut:]),
                    f"mengubah posisi >= {cut} seharusnya mengubah output posisi >= {cut}",
                )

    def test_past_perturbation_changes_its_own_output(self):
        with torch.no_grad():
            base = self.attn(self.x)
            x_mod = self.x.clone()
            x_mod[:, 0, :] = torch.randn(B, D_MODEL)
            out = self.attn(x_mod)
        self.assertFalse(torch.allclose(out[:, 0], base[:, 0]))

    def test_forward_matches_manual_reference(self):
        with torch.no_grad():
            out = self.attn(self.x)
            _, expected = _manual_probs_and_output(self.attn, self.x)
        torch.testing.assert_close(out, expected, atol=1e-6, rtol=1e-6)


class TestCausalProbabilityMass(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(42)
        self.attn = CausalMultiHeadAttention(D_MODEL, N_HEADS, dropout=0.0).eval()
        self.x = torch.randn(B, T, D_MODEL)

    def test_future_probability_is_exactly_zero(self):
        with torch.no_grad():
            probs, _ = _manual_probs_and_output(self.attn, self.x)
        future = torch.triu(torch.ones(T, T, dtype=torch.bool), diagonal=1)
        self.assertTrue(torch.all(probs[..., future] == 0.0))
        torch.testing.assert_close(
            probs.sum(dim=-1), torch.ones(B, N_HEADS, T), atol=1e-6, rtol=1e-6
        )

    def test_first_position_attends_only_to_itself(self):
        with torch.no_grad():
            probs, _ = _manual_probs_and_output(self.attn, self.x)
        torch.testing.assert_close(
            probs[:, :, 0, 0], torch.ones(B, N_HEADS), atol=1e-6, rtol=1e-6
        )
        self.assertTrue(torch.all(probs[:, :, 0, 1:] == 0.0))


class TestCausalEdgeCases(unittest.TestCase):
    def test_single_position_has_no_future(self):
        torch.manual_seed(42)
        attn = CausalMultiHeadAttention(D_MODEL, N_HEADS, dropout=0.0).eval()
        x = torch.randn(B, 1, D_MODEL)
        with torch.no_grad():
            out = attn(x)
            expected = attn.w_o(attn.w_v(x))
        self.assertEqual(tuple(out.shape), (B, 1, D_MODEL))
        torch.testing.assert_close(out, expected, atol=1e-6, rtol=1e-6)
        self.assertTrue(torch.isfinite(out).all())

    def test_float64_input_keeps_dtype_and_causality(self):
        torch.manual_seed(42)
        attn = CausalMultiHeadAttention(D_MODEL, N_HEADS, dropout=0.0).double().eval()
        x = torch.randn(B, T, D_MODEL, dtype=torch.float64)
        with torch.no_grad():
            base = attn(x)
            self.assertEqual(base.dtype, torch.float64)
            x_mod = x.clone()
            x_mod[:, T // 2 :, :] = torch.randn(B, T - T // 2, D_MODEL, dtype=torch.float64)
            out = attn(x_mod)
        torch.testing.assert_close(
            out[:, : T // 2], base[:, : T // 2], atol=1e-10, rtol=1e-10
        )

    def test_large_scores_remain_finite(self):
        torch.manual_seed(42)
        attn = CausalMultiHeadAttention(D_MODEL, N_HEADS, dropout=0.0).eval()
        x = torch.randn(B, T, D_MODEL) * 1e2
        with torch.no_grad():
            out = attn(x)
            probs, _ = _manual_probs_and_output(attn, x)
        self.assertTrue(torch.isfinite(out).all())
        self.assertFalse(torch.isnan(probs).any())
        torch.testing.assert_close(
            probs.sum(dim=-1), torch.ones(B, N_HEADS, T), atol=1e-5, rtol=1e-5
        )


if __name__ == "__main__":
    unittest.main()
