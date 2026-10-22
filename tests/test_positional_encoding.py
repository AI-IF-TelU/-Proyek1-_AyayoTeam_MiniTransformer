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
    dims = torch.arange(d_model, dtype=torch.float32).unsqueeze(0)
    angles = positions / (10000.0 ** (dims / d_model))
    pe = torch.zeros(max_len, d_model)
    pe[:, 0::2] = torch.sin(angles[:, 0::2])
    pe[:, 1::2] = torch.cos(angles[:, 1::2])
    return pe


@unittest.skip("skeleton B2; prediction dijalankan di B4")
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

    def test_value_error_when_T_exceeds_max_len(self):
        pe = SinCosPositionalEncoding(D_MODEL, max_len=4)
        x = torch.randn(B, 8, D_MODEL)
        with self.assertRaises(ValueError):
            pe(x)


if __name__ == "__main__":
    unittest.main()