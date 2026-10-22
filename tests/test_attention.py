import unittest

import torch
import torch.nn as nn

from src.model.attention import CausalMultiHeadAttention

B, T, D_MODEL = 2, 8, 64
N_HEADS = 4
HEAD_DIM = D_MODEL // N_HEADS
DROPOUT = 0.1


def _assert_shape(tensor: torch.Tensor, expected: tuple) -> None:
    assert tuple(tensor.shape) == expected, (
        f"shape {tuple(tensor.shape)} != expected {expected}"
    )


class TestProjectionQKV(unittest.TestCase):
    def setUp(self):
        self.attn = CausalMultiHeadAttention(D_MODEL, N_HEADS)
        self.x = torch.randn(B, T, D_MODEL)

    def test_projections_are_linear(self):
        for name in ("w_q", "w_k", "w_v", "w_o"):
            mod = getattr(self.attn, name)
            self.assertIsInstance(mod, nn.Linear)
            self.assertEqual(mod.weight.shape, (D_MODEL, D_MODEL))
            self.assertEqual(mod.bias.shape, (D_MODEL,))

    def test_qkv_output_shape(self):
        q, k, v = self.attn._project_qkv(self.x)
        for tensor in (q, k, v):
            _assert_shape(tensor, (B, T, D_MODEL))

    def test_w_o_is_separate(self):
        self.assertIsNot(self.attn.w_o, self.attn.w_q)
        self.assertIsNot(self.attn.w_o, self.attn.w_k)
        self.assertIsNot(self.attn.w_o, self.attn.w_v)

    def test_gradient_flows_through_projections(self):
        q, k, v = self.attn._project_qkv(self.x)
        loss = q.sum() + k.sum() + v.sum()
        loss.backward()
        for name in ("w_q", "w_k", "w_v"):
            grad = getattr(self.attn, name).weight.grad
            self.assertIsNotNone(grad)
            self.assertFalse(torch.allclose(grad, torch.zeros_like(grad)))

    def test_value_error_when_heads_dont_divide(self):
        with self.assertRaises(ValueError):
            CausalMultiHeadAttention(D_MODEL, n_heads=5)
        with self.assertRaises(ValueError):
            CausalMultiHeadAttention(D_MODEL, n_heads=0)


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