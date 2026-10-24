"""Tes kontrak Decoder Block (Issue D, subtask D6).

Melengkapi `tests/test_decoder_block.py` milik Issue B (yang menguji shape,
FFN, dropout, dan kesetaraan pre/post-norm lewat perhitungan manual) dengan
pembuktian perilaku kontraktual `TECH_SPEC.md` 6 / ADR-007:

- struktur baseline: pre-norm, `d_ff = 4 * d_model`, `head_dim = d_model / n_heads`,
  LayerNorm epsilon `1e-5`;
- residual benar-benar aditif (parameter submodul dinolkan -> `out == x` eksak)
  dan jalur identitas tidak memblokir gradien (`d out / d x == 1`);
- causal masking berlaku untuk seluruh block (attention + residual + FFN),
  diuji per titik potong dengan kontrol sensitivitas agar bukan tes "mati";
- block tidak menyisipkan informasi posisi apa pun (bukan tanggung jawab block;
  PE ada di MiniGPT), dibuktikan lewat input yang identik di semua posisi;
- item batch saling independen;
- DecoderBlock tidak memiliki guard `context_length` (hanya MiniGPT yang
  mewajibkannya menurut kontrak), sehingga `T > 64` tetap valid.

Dropout dinolkan dan modul di-`eval()` pada tes invariance agar hasil
deterministik; invariance diuji eksak (`atol=0`) karena posisi masa depan
mendapat bobot softmax tepat nol.
"""
import unittest

import torch

from src.model.decoder_block import DecoderBlock

B, T, D_MODEL = 2, 64, 64
N_HEADS = 4
D_FF = 4 * D_MODEL
LAYER_NORM_EPS = 1e-5


def _make_block(dropout: float = 0.0) -> DecoderBlock:
    block = DecoderBlock(
        D_MODEL,
        N_HEADS,
        D_FF,
        dropout=dropout,
        layer_norm_eps=LAYER_NORM_EPS,
    )
    block.eval()
    return block


def _assert_shape(tensor: torch.Tensor, expected: tuple) -> None:
    assert tuple(tensor.shape) == expected, (
        f"shape {tuple(tensor.shape)} != expected {expected}"
    )


class TestDecoderBlockStructure(unittest.TestCase):
    """Konfigurasi baseline harus sesuai ADR-007, bukan sekadar bisa forward."""

    def test_baseline_hyperparameters(self):
        block = DecoderBlock(D_MODEL, N_HEADS, D_FF)
        self.assertTrue(block.pre_norm, "baseline wajib pre-norm (ADR-007)")
        self.assertEqual(block.d_model, D_MODEL)
        self.assertEqual(block.n_heads, N_HEADS)
        self.assertEqual(block.d_ff, D_FF)
        self.assertEqual(block.attn.head_dim, D_MODEL // N_HEADS)
        self.assertEqual(block.attn.n_heads, N_HEADS)
        self.assertAlmostEqual(block.norm1.eps, LAYER_NORM_EPS)
        self.assertAlmostEqual(block.norm2.eps, LAYER_NORM_EPS)

    def test_ffn_projection_sizes_follow_d_ff(self):
        block = DecoderBlock(D_MODEL, N_HEADS, D_FF)
        self.assertEqual(block.ffn.fc1.weight.shape, (D_FF, D_MODEL))
        self.assertEqual(block.ffn.fc2.weight.shape, (D_MODEL, D_FF))

    def test_block_registers_no_positional_buffers(self):
        block = DecoderBlock(D_MODEL, N_HEADS, D_FF)
        self.assertEqual(list(block.named_buffers()), [])
        param_names = " ".join(name for name, _ in block.named_parameters())
        self.assertNotIn("pe", param_names)


class TestDecoderBlockForwardShape(unittest.TestCase):
    def test_baseline_shape_and_finite(self):
        block = _make_block()
        x = torch.randn(B, T, D_MODEL)
        out = block(x)
        _assert_shape(out, (B, T, D_MODEL))
        self.assertTrue(torch.isfinite(out).all())

    def test_single_position(self):
        block = _make_block()
        out = block(torch.randn(B, 1, D_MODEL))
        _assert_shape(out, (B, 1, D_MODEL))
        self.assertTrue(torch.isfinite(out).all())


class TestResidualConnectionContract(unittest.TestCase):
    def test_zeroed_parameters_make_block_identity(self):
        """Residual aditif: bila attention dan FFN menghasilkan nol, `out == x`."""
        block = _make_block()
        with torch.no_grad():
            for param in block.parameters():
                param.zero_()
        x = torch.randn(B, T, D_MODEL)
        out = block(x)
        torch.testing.assert_close(out, x, atol=0.0, rtol=0.0)

    def test_identity_path_keeps_gradient_one(self):
        """Jalur residual tidak memblokir gradien: `d out / d x == 1`."""
        block = _make_block()
        with torch.no_grad():
            for param in block.parameters():
                param.zero_()
        x = torch.randn(B, T, D_MODEL, requires_grad=True)
        block(x).sum().backward()
        self.assertIsNotNone(x.grad)
        torch.testing.assert_close(x.grad, torch.ones_like(x), atol=0.0, rtol=0.0)


class TestCausalMaskingThroughBlock(unittest.TestCase):
    def test_every_cut_leaves_past_unchanged(self):
        """Mengubah x[:, k:] tidak boleh mengubah out[:, :k] untuk setiap k."""
        block = _make_block()
        x = torch.randn(B, T, D_MODEL)
        base = block(x)
        for cut in (1, 8, T // 2, T - 1):
            perturbed = x.clone()
            perturbed[:, cut:] = perturbed[:, cut:] + 1.0
            out = block(perturbed)
            torch.testing.assert_close(
                out[:, :cut], base[:, :cut], atol=0.0, rtol=0.0
            )

    def test_past_perturbation_changes_its_own_output(self):
        """Kontrol sensitivitas: block tidak boleh mengabaikan input sepenuhnya."""
        block = _make_block()
        x = torch.randn(B, T, D_MODEL)
        base = block(x)
        perturbed = x.clone()
        perturbed[:, 0] = perturbed[:, 0] + 1.0
        out = block(perturbed)
        self.assertFalse(torch.allclose(out[:, 0], base[:, 0], atol=1e-6, rtol=1e-6))

    def test_future_perturbation_changes_future_output(self):
        """Perubahan posisi terakhir harus terlihat pada output posisi terakhir."""
        block = _make_block()
        x = torch.randn(B, T, D_MODEL)
        base = block(x)
        perturbed = x.clone()
        perturbed[:, -1] = perturbed[:, -1] + 1.0
        out = block(perturbed)
        self.assertFalse(torch.allclose(out[:, -1], base[:, -1], atol=1e-6, rtol=1e-6))


class TestPositionIndependence(unittest.TestCase):
    def test_identical_positions_produce_identical_outputs(self):
        """Block sendiri tidak menambahkan posisi: input identik -> output identik.

        Informasi posisi hanya datang dari `SinCosPositionalEncoding` di MiniGPT
        (TECH_SPEC 6). Bila block diam-diam menambahkan posisi, sifat ini gagal.
        """
        block = _make_block()
        row = torch.randn(1, 1, D_MODEL)
        x = row.repeat(B, T, 1)
        out = block(x)
        for b in range(B):
            for t in range(1, T):
                # Bukan eksak: jumlah suku softmax bertambah dengan t sehingga
                # urutan penjumlahan float32 menghasilkan galat ~1e-7
                # (toleransi setara temuan pembulatan float32 pada D5).
                torch.testing.assert_close(
                    out[b, t], out[b, 0], atol=1e-6, rtol=1e-5
                )


class TestBatchIndependence(unittest.TestCase):
    def test_perturbing_one_item_does_not_change_other_items(self):
        block = _make_block()
        x = torch.randn(B, T, D_MODEL)
        base = block(x)
        perturbed = x.clone()
        perturbed[0] = perturbed[0] + 1.0
        out = block(perturbed)
        self.assertFalse(torch.allclose(out[0], base[0], atol=1e-6, rtol=1e-6))
        torch.testing.assert_close(out[1], base[1], atol=0.0, rtol=0.0)


class TestNoContextLengthGuard(unittest.TestCase):
    def test_longer_sequences_still_forward(self):
        """DecoderBlock tidak memiliki `context_length`; guard ada di MiniGPT."""
        block = _make_block()
        for length in (T + 1, 2 * T):
            x = torch.randn(B, length, D_MODEL)
            out = block(x)
            _assert_shape(out, (B, length, D_MODEL))
            self.assertTrue(torch.isfinite(out).all())


if __name__ == "__main__":
    unittest.main()
