import unittest

import torch

from src.model.attention import CausalMultiHeadAttention

B, T, D_MODEL = 2, 8, 64
N_HEADS = 4
HEAD_DIM = D_MODEL // N_HEADS
DROPOUT = 0.1


def _assert_shape(tensor: torch.Tensor, expected: tuple) -> None:
    assert tuple(tensor.shape) == expected, (
        f"shape {tuple(tensor.shape)} != expected {expected}"
    )


@unittest.skip("skeleton B2; prediction dijalankan di B9")
class TestAttentionShape(unittest.TestCase):
    def test_output_shape(self):
        attn = CausalMultiHeadAttention(D_MODEL, N_HEADS)
        _assert_shape(attn(torch.randn(B, T, D_MODEL)), (B, T, D_MODEL))


@unittest.skip("skeleton B2; prediction dijalankan di B9")
class TestAttentionValidation(unittest.TestCase):
    def test_value_error_when_heads_do_not_divide(self):
        with self.assertRaises(ValueError):
            CausalMultiHeadAttention(D_MODEL, n_heads=5)


@unittest.skip("skeleton B2; prediction dijalankan di B9")
class TestCausalInvariance(unittest.TestCase):
    def test_future_positions_do_not_change_past_output(self):
        attn = CausalMultiHeadAttention(D_MODEL, N_HEADS, dropout=DROPOUT)
        attn.eval()
        x = torch.randn(B, T, D_MODEL)
        out_a = attn(x)
        x_future = x.clone()
        x_future[:, T // 2 :, :] = torch.randn_like(x_future[:, T // 2 :, :])
        out_b = attn(x_future)
        torch.testing.assert_close(
            out_a[:, : T // 2, :], out_b[:, : T // 2, :], atol=1e-6, rtol=1e-6
        )


@unittest.skip("skeleton B2; prediction dijalankan di B9")
class TestDropoutBehavior(unittest.TestCase):
    def test_train_differs_from_eval(self):
        attn = CausalMultiHeadAttention(D_MODEL, N_HEADS, dropout=DROPOUT)
        x = torch.randn(B, T, D_MODEL)
        attn.train()
        out_train_a = attn(x)
        out_train_b = attn(x)
        attn.eval()
        out_eval_a = attn(x)
        out_eval_b = attn(x)
        self.assertFalse(torch.allclose(out_train_a, out_train_b))
        torch.testing.assert_close(out_eval_a, out_eval_b, atol=1e-6, rtol=1e-6)


if __name__ == "__main__":
    unittest.main()