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


class TestScaledDotProductAttention(unittest.TestCase):
    def setUp(self):
        self.attn = CausalMultiHeadAttention(D_MODEL, N_HEADS, dropout=0.0)
        self.attn.eval()
        self.q = torch.randn(B, N_HEADS, T, HEAD_DIM)
        self.k = torch.randn(B, N_HEADS, T, HEAD_DIM)
        self.v = torch.randn(B, N_HEADS, T, HEAD_DIM)

    def test_output_shape(self):
        out = self.attn._scaled_dot_product_attention(self.q, self.k, self.v)
        _assert_shape(out, (B, N_HEADS, T, HEAD_DIM))

    def test_matches_manual_scaled_attention(self):
        scores = self.q @ self.k.transpose(-2, -1) * (HEAD_DIM ** -0.5)
        probs = torch.softmax(scores, dim=-1)
        expected = probs @ self.v
        out = self.attn._scaled_dot_product_attention(self.q, self.k, self.v)
        torch.testing.assert_close(out, expected, atol=1e-6, rtol=1e-6)

    def test_scale_is_applied(self):
        q = torch.cat([torch.randn(B, N_HEADS, 1, HEAD_DIM)] * 2, dim=2)
        k = torch.cat(
            [
                torch.randn(B, N_HEADS, 1, HEAD_DIM) * 10.0,
                torch.randn(B, N_HEADS, 1, HEAD_DIM),
            ],
            dim=2,
        )
        v = torch.randn(B, N_HEADS, 2, HEAD_DIM)
        scaled = self.attn._scaled_dot_product_attention(q, k, v)
        scores_scaled = q @ k.transpose(-2, -1) * (HEAD_DIM ** -0.5)
        expected_scaled = torch.softmax(scores_scaled, dim=-1) @ v
        scores_unscaled = q @ k.transpose(-2, -1)
        expected_unscaled = torch.softmax(scores_unscaled, dim=-1) @ v
        torch.testing.assert_close(scaled, expected_scaled, atol=1e-6, rtol=1e-6)
        self.assertFalse(torch.allclose(scaled, expected_unscaled, atol=1e-4, rtol=1e-4))

    def test_value_error_on_wrong_shape(self):
        with self.assertRaises(ValueError):
            self.attn._scaled_dot_product_attention(
                torch.randn(B, T, HEAD_DIM), self.k, self.v
            )
        with self.assertRaises(ValueError):
            self.attn._scaled_dot_product_attention(
                torch.randn(B, N_HEADS, T, HEAD_DIM + 1), self.k, self.v
            )

    def test_gradient_flows(self):
        q = self.q.clone().requires_grad_(True)
        k = self.k.clone().requires_grad_(True)
        v = self.v.clone().requires_grad_(True)
        out = self.attn._scaled_dot_product_attention(q, k, v)
        out.sum().backward()
        for tensor in (q, k, v):
            grad = tensor.grad
            self.assertIsNotNone(grad)
            self.assertFalse(torch.allclose(grad, torch.zeros_like(grad)))

    def test_dropout_train_differs_from_eval(self):
        attn = CausalMultiHeadAttention(D_MODEL, N_HEADS, dropout=DROPOUT)
        q, k, v = self.q, self.k, self.v
        attn.train()
        out_train_a = attn._scaled_dot_product_attention(q, k, v)
        out_train_b = attn._scaled_dot_product_attention(q, k, v)
        self.assertTrue(torch.isfinite(out_train_a).all())
        self.assertTrue(torch.isfinite(out_train_b).all())
        self.assertFalse(torch.allclose(out_train_a, out_train_b))
        attn.eval()
        out_eval_a = attn._scaled_dot_product_attention(q, k, v)
        out_eval_b = attn._scaled_dot_product_attention(q, k, v)
        torch.testing.assert_close(out_eval_a, out_eval_b, atol=1e-6, rtol=1e-6)


class TestAttentionShape(unittest.TestCase):
    def test_output_shape(self):
        attn = CausalMultiHeadAttention(D_MODEL, N_HEADS)
        _assert_shape(attn(torch.randn(B, T, D_MODEL)), (B, T, D_MODEL))

    def test_output_shape_varied_batch_and_length(self):
        attn = CausalMultiHeadAttention(D_MODEL, N_HEADS)
        attn.eval()
        for batch, length in ((1, 1), (4, 16), (B, T)):
            x = torch.randn(batch, length, D_MODEL)
            _assert_shape(attn(x), (batch, length, D_MODEL))

    def test_output_is_float32(self):
        attn = CausalMultiHeadAttention(D_MODEL, N_HEADS)
        out = attn(torch.randn(B, T, D_MODEL))
        self.assertEqual(out.dtype, torch.float32)

    def test_gradient_flows_end_to_end(self):
        attn = CausalMultiHeadAttention(D_MODEL, N_HEADS, dropout=0.0)
        x = torch.randn(B, T, D_MODEL, requires_grad=True)
        out = attn(x)
        out.sum().backward()
        for name in ("w_q", "w_k", "w_v", "w_o"):
            grad = getattr(attn, name).weight.grad
            self.assertIsNotNone(grad)
            self.assertFalse(torch.allclose(grad, torch.zeros_like(grad)))


class TestAttentionValidation(unittest.TestCase):
    def test_value_error_when_heads_do_not_divide(self):
        with self.assertRaises(ValueError):
            CausalMultiHeadAttention(D_MODEL, n_heads=5)

    def test_value_error_when_zero_heads(self):
        with self.assertRaises(ValueError):
            CausalMultiHeadAttention(D_MODEL, n_heads=0)

    def test_value_error_when_more_heads_than_d_model(self):
        with self.assertRaises(ValueError):
            CausalMultiHeadAttention(D_MODEL, n_heads=D_MODEL + 1)


class TestCausalMask(unittest.TestCase):
    def setUp(self):
        self.attn = CausalMultiHeadAttention(D_MODEL, N_HEADS, dropout=0.0)

    def test_mask_shape(self):
        mask = self.attn._causal_mask(T)
        _assert_shape(mask, (1, 1, T, T))

    def test_mask_is_upper_triangular_negative_infinity(self):
        mask = self.attn._causal_mask(T)[0, 0]
        for i in range(T):
            for j in range(T):
                if j > i:
                    self.assertEqual(mask[i, j], float("-inf"))
                else:
                    self.assertEqual(mask[i, j], 0.0)

    def test_mask_t1_has_no_future(self):
        mask = self.attn._causal_mask(1)
        _assert_shape(mask, (1, 1, 1, 1))
        self.assertEqual(mask[0, 0, 0, 0], 0.0)

    def test_mask_respects_dtype_and_device(self):
        mask = self.attn._causal_mask(T, dtype=torch.float64)
        self.assertEqual(mask.dtype, torch.float64)

    def test_causal_invariance_with_future_token_changes(self):
        q = torch.randn(B, N_HEADS, T, HEAD_DIM)
        k = torch.randn(B, N_HEADS, T, HEAD_DIM)
        v = torch.randn(B, N_HEADS, T, HEAD_DIM)
        mask = self.attn._causal_mask(T)
        out_a = self.attn._scaled_dot_product_attention(q, k, v, mask)

        q_future = q.clone()
        k_future = k.clone()
        v_future = v.clone()
        q_future[:, :, T // 2 :, :] = torch.randn_like(q_future[:, :, T // 2 :, :])
        k_future[:, :, T // 2 :, :] = torch.randn_like(k_future[:, :, T // 2 :, :])
        v_future[:, :, T // 2 :, :] = torch.randn_like(v_future[:, :, T // 2 :, :])
        out_b = self.attn._scaled_dot_product_attention(
            q_future, k_future, v_future, mask
        )

        torch.testing.assert_close(
            out_a[:, :, : T // 2, :], out_b[:, :, : T // 2, :], atol=1e-6, rtol=1e-6
        )
        self.assertFalse(
            torch.allclose(out_a[:, :, T // 2 :, :], out_b[:, :, T // 2 :, :])
        )

    def test_invariance_fails_without_mask(self):
        q = torch.randn(B, N_HEADS, T, HEAD_DIM)
        k = torch.randn(B, N_HEADS, T, HEAD_DIM)
        v = torch.randn(B, N_HEADS, T, HEAD_DIM)
        out_a = self.attn._scaled_dot_product_attention(q, k, v)

        v_future = v.clone()
        v_future[:, :, T // 2 :, :] = torch.randn_like(v_future[:, :, T // 2 :, :])
        out_b = self.attn._scaled_dot_product_attention(q, k, v_future)

        self.assertFalse(
            torch.allclose(out_a[:, :, : T // 2, :], out_b[:, :, : T // 2, :])
        )


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


class TestTrainModeDropoutSafety(unittest.TestCase):
    def setUp(self):
        self.attn = CausalMultiHeadAttention(D_MODEL, N_HEADS, dropout=DROPOUT)
        self.attn.train()

    def test_train_mode_output_is_finite(self):
        for seed in range(5):
            torch.manual_seed(seed)
            x = torch.randn(B, T, D_MODEL)
            out = self.attn(x)
            self.assertTrue(
                torch.isfinite(out).all(), f"non-finite output under seed {seed}"
            )

    def test_causal_invariance_holds_in_train_mode(self):
        q = torch.randn(B, N_HEADS, T, HEAD_DIM)
        k = torch.randn(B, N_HEADS, T, HEAD_DIM)
        v = torch.randn(B, N_HEADS, T, HEAD_DIM)
        mask = self.attn._causal_mask(T)

        torch.manual_seed(0)
        out_a = self.attn._scaled_dot_product_attention(q, k, v, mask)

        q_future = q.clone()
        k_future = k.clone()
        v_future = v.clone()
        q_future[:, :, T // 2 :, :] = torch.randn_like(q_future[:, :, T // 2 :, :])
        k_future[:, :, T // 2 :, :] = torch.randn_like(k_future[:, :, T // 2 :, :])
        v_future[:, :, T // 2 :, :] = torch.randn_like(v_future[:, :, T // 2 :, :])

        torch.manual_seed(0)
        out_b = self.attn._scaled_dot_product_attention(q_future, k_future, v_future, mask)

        self.assertTrue(torch.isfinite(out_a).all())
        self.assertTrue(torch.isfinite(out_b).all())
        torch.testing.assert_close(
            out_a[:, :, : T // 2, :], out_b[:, :, : T // 2, :], atol=1e-6, rtol=1e-6
        )
        self.assertFalse(
            torch.allclose(out_a[:, :, T // 2 :, :], out_b[:, :, T // 2 :, :])
        )

    def test_masked_future_scores_never_nan(self):
        q = torch.randn(B, N_HEADS, T, HEAD_DIM)
        k = torch.randn(B, N_HEADS, T, HEAD_DIM)
        scale = HEAD_DIM ** -0.5
        scores = q @ k.transpose(-2, -1) * scale
        mask = self.attn._causal_mask(T)
        torch.manual_seed(0)
        scores = self.attn.attn_dropout(scores)
        scores = scores + mask
        upper = torch.triu(torch.ones(T, T, dtype=torch.bool), diagonal=1)
        future_scores = scores[:, :, upper]
        self.assertFalse(torch.isnan(future_scores).any())
        self.assertTrue(torch.isneginf(future_scores).all())


if __name__ == "__main__":
    unittest.main()