import math
import unittest

import torch

from src.model.positional_encoding import SinCosPositionalEncoding

B, T, D_MODEL = 2, 8, 64
MAX_LEN = 64


def _assert_shape(tensor: torch.Tensor, expected: tuple) -> None:
    assert tuple(tensor.shape) == expected, (
        f"shape {tuple(tensor.shape)} != expected {expected}"
    )


def _expected_pe(d_model: int, max_len: int) -> torch.Tensor:
    positions = torch.arange(max_len, dtype=torch.float32).unsqueeze(1)
    div_term = torch.exp(
        torch.arange(0, d_model, 2, dtype=torch.float32)
        * (-math.log(10000.0) / d_model)
    )
    angles = positions * div_term
    pe = torch.zeros(max_len, d_model)
    pe[:, 0::2] = torch.sin(angles)
    pe[:, 1::2] = torch.cos(angles)
    return pe


class TestPositionalEncoding(unittest.TestCase):
    def setUp(self):
        self.pe = SinCosPositionalEncoding(D_MODEL, MAX_LEN)

    def test_output_shape(self):
        x = torch.randn(B, T, D_MODEL)
        _assert_shape(self.pe(x), (B, T, D_MODEL))

    def test_buffer_non_trainable(self):
        buffer = self.pe.get_buffer("pe")
        self.assertFalse(buffer.requires_grad)
        _assert_shape(buffer, (MAX_LEN, D_MODEL))

    def test_sin_cos_pattern(self):
        buffer = self.pe.get_buffer("pe")
        expected = _expected_pe(D_MODEL, MAX_LEN)
        torch.testing.assert_close(buffer, expected, atol=1e-6, rtol=1e-6)

    def test_matches_standard_sinusoid_formula(self):
        buffer = self.pe.get_buffer("pe")
        positions = torch.arange(MAX_LEN, dtype=torch.float32).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, D_MODEL, 2, dtype=torch.float32)
            * (-math.log(10000.0) / D_MODEL)
        )
        reference = torch.zeros(MAX_LEN, D_MODEL)
        reference[:, 0::2] = torch.sin(positions * div_term)
        reference[:, 1::2] = torch.cos(positions * div_term)
        torch.testing.assert_close(buffer, reference, atol=1e-6, rtol=1e-6)

    def test_even_odd_pair_share_frequency(self):
        buffer = self.pe.get_buffer("pe")
        positions = torch.arange(MAX_LEN, dtype=torch.float32)
        div_term = torch.exp(
            torch.arange(0, D_MODEL, 2, dtype=torch.float32)
            * (-math.log(10000.0) / D_MODEL)
        )
        for i, k in enumerate(range(0, D_MODEL, 2)):
            angle = positions * div_term[i]
            torch.testing.assert_close(
                buffer[:, k], torch.sin(angle), atol=1e-6, rtol=1e-5
            )
            torch.testing.assert_close(
                buffer[:, k + 1], torch.cos(angle), atol=1e-6, rtol=1e-5
            )

    def test_value_error_when_T_exceeds_max_len(self):
        pe = SinCosPositionalEncoding(D_MODEL, max_len=4)
        x = torch.randn(B, 8, D_MODEL)
        with self.assertRaises(ValueError):
            pe(x)

    def test_value_error_when_d_model_odd(self):
        with self.assertRaises(ValueError):
            SinCosPositionalEncoding(63, 4)
        with self.assertRaises(ValueError):
            SinCosPositionalEncoding(65, 4)

    def test_even_d_model_still_works(self):
        pe = SinCosPositionalEncoding(64, 4)
        _assert_shape(pe.get_buffer("pe"), (4, 64))

    def test_t_equals_max_len(self):
        pe = SinCosPositionalEncoding(D_MODEL, max_len=4)
        x = torch.randn(B, 4, D_MODEL)
        _assert_shape(pe(x), (B, 4, D_MODEL))

    def test_additive_semantics(self):
        x = torch.randn(B, T, D_MODEL)
        out = self.pe(x)
        expected = x + self.pe.get_buffer("pe")[:T]
        torch.testing.assert_close(out, expected, atol=1e-7, rtol=1e-7)


class TestPositionalEncodingContract(unittest.TestCase):
    """Kontrak PE (Issue D, subtask D5) yang diuji lewat perilaku, bukan hanya "tidak error".

    Melengkapi tes pemilik modul: offset yang sama untuk setiap item batch,
    ketiadaan mutasi input, gradien identitas, determinisme train/eval, dan
    batas `max_len` tepat pada nilai baseline (T=64 lolos, T=65 ValueError).
    """

    def setUp(self):
        self.pe = SinCosPositionalEncoding(D_MODEL, MAX_LEN)

    def test_buffer_is_registered_and_not_trainable(self):
        self.assertEqual(list(self.pe.named_parameters()), [])
        buffers = dict(self.pe.named_buffers())
        self.assertIn("pe", buffers)
        self.assertFalse(buffers["pe"].requires_grad)

    def test_same_offset_for_every_batch_item(self):
        x = torch.randn(B, T, D_MODEL)
        out = self.pe(x)
        buffer = self.pe.get_buffer("pe")[:T]
        for b in range(B):
            torch.testing.assert_close(out[b] - x[b], buffer, atol=1e-6, rtol=1e-5)

    def test_forward_does_not_mutate_input(self):
        x = torch.randn(B, T, D_MODEL)
        before = x.clone()
        self.pe(x)
        torch.testing.assert_close(x, before, atol=0.0, rtol=0.0)

    def test_gradient_is_identity(self):
        x = torch.randn(B, T, D_MODEL, requires_grad=True)
        self.pe(x).sum().backward()
        self.assertIsNotNone(x.grad)
        torch.testing.assert_close(x.grad, torch.ones_like(x), atol=0.0, rtol=0.0)

    def test_deterministic_in_train_and_eval(self):
        x = torch.randn(B, T, D_MODEL)
        self.pe.train()
        train_out = self.pe(x)
        self.pe.eval()
        eval_out = self.pe(x)
        torch.testing.assert_close(train_out, eval_out, atol=0.0, rtol=0.0)

    def test_max_len_boundary_at_baseline(self):
        pe = SinCosPositionalEncoding(D_MODEL, MAX_LEN)
        at_limit = torch.randn(1, MAX_LEN, D_MODEL)
        _assert_shape(pe(at_limit), (1, MAX_LEN, D_MODEL))
        over_limit = torch.randn(1, MAX_LEN + 1, D_MODEL)
        with self.assertRaises(ValueError):
            pe(over_limit)


if __name__ == "__main__":
    unittest.main()