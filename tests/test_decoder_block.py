import unittest

import torch
import torch.nn.functional as F

from src.model.decoder_block import DecoderBlock, FeedForward

B, T, D_MODEL = 2, 8, 64
N_HEADS = 4
D_FF = 4 * D_MODEL
DROPOUT = 0.1
LAYER_NORM_EPS = 1e-5


def _assert_shape(tensor: torch.Tensor, expected: tuple) -> None:
    assert tuple(tensor.shape) == expected, (
        f"shape {tuple(tensor.shape)} != expected {expected}"
    )


class TestFeedForward(unittest.TestCase):
    def test_output_shape(self):
        ffn = FeedForward(D_MODEL, D_FF)
        _assert_shape(ffn(torch.randn(B, T, D_MODEL)), (B, T, D_MODEL))

    def test_linear_layer_shapes(self):
        ffn = FeedForward(D_MODEL, D_FF)
        self.assertEqual(ffn.fc1.weight.shape, (D_FF, D_MODEL))
        self.assertEqual(ffn.fc1.bias.shape, (D_FF,))
        self.assertEqual(ffn.fc2.weight.shape, (D_MODEL, D_FF))
        self.assertEqual(ffn.fc2.bias.shape, (D_MODEL,))

    def test_matches_manual_gelu_computation(self):
        ffn = FeedForward(D_MODEL, D_FF, dropout=0.0)
        ffn.eval()
        x = torch.randn(B, T, D_MODEL)
        expected = ffn.fc2(F.gelu(ffn.fc1(x)))
        torch.testing.assert_close(ffn(x), expected, atol=1e-6, rtol=1e-6)

    def test_dropout_train_differs_from_eval(self):
        ffn = FeedForward(D_MODEL, D_FF, dropout=DROPOUT)
        x = torch.randn(B, T, D_MODEL)
        ffn.train()
        out_train_a = ffn(x)
        out_train_b = ffn(x)
        ffn.eval()
        out_eval_a = ffn(x)
        out_eval_b = ffn(x)
        self.assertFalse(torch.allclose(out_train_a, out_train_b))
        torch.testing.assert_close(out_eval_a, out_eval_b, atol=1e-6, rtol=1e-6)

    def test_gradient_flows_to_all_parameters(self):
        ffn = FeedForward(D_MODEL, D_FF)
        x = torch.randn(B, T, D_MODEL)
        ffn(x).sum().backward()
        for name, param in ffn.named_parameters():
            self.assertIsNotNone(param.grad, f"param {name} has None gradient")
            self.assertTrue(
                torch.count_nonzero(param.grad) > 0, f"param {name} grad zero"
            )

    def test_value_error_on_nonpositive_dims(self):
        with self.assertRaises(ValueError):
            FeedForward(0, D_FF)
        with self.assertRaises(ValueError):
            FeedForward(D_MODEL, 0)

    def test_value_error_on_wrong_input(self):
        ffn = FeedForward(D_MODEL, D_FF)
        with self.assertRaises(ValueError):
            ffn(torch.randn(B, D_MODEL))
        with self.assertRaises(ValueError):
            ffn(torch.randn(B, T, D_MODEL - 1))


class TestDecoderBlockShape(unittest.TestCase):
    def test_output_shape(self):
        block = DecoderBlock(D_MODEL, N_HEADS, D_FF)
        _assert_shape(block(torch.randn(B, T, D_MODEL)), (B, T, D_MODEL))

    def test_output_shape_varied_batch_and_length(self):
        block = DecoderBlock(D_MODEL, N_HEADS, D_FF)
        block.eval()
        for batch, length in ((1, 1), (4, 16), (B, T)):
            x = torch.randn(batch, length, D_MODEL)
            _assert_shape(block(x), (batch, length, D_MODEL))

    def test_value_error_on_wrong_input(self):
        block = DecoderBlock(D_MODEL, N_HEADS, D_FF)
        with self.assertRaises(ValueError):
            block(torch.randn(B, D_MODEL))
        with self.assertRaises(ValueError):
            block(torch.randn(B, T, D_MODEL - 1))


class TestResidualConnection(unittest.TestCase):
    def test_output_differs_from_input(self):
        block = DecoderBlock(D_MODEL, N_HEADS, D_FF, dropout=DROPOUT)
        block.eval()
        x = torch.randn(B, T, D_MODEL)
        out = block(x)
        self.assertFalse(torch.allclose(out, x, atol=1e-6, rtol=1e-6))

    def test_pre_norm_matches_manual_residual_computation(self):
        block = DecoderBlock(D_MODEL, N_HEADS, D_FF, dropout=0.0)
        block.eval()
        x = torch.randn(B, T, D_MODEL)
        a = block.attn(block.norm1(x))
        expected = x + a + block.ffn(block.norm2(x + a))
        torch.testing.assert_close(block(x), expected, atol=1e-6, rtol=1e-6)

    def test_post_norm_matches_manual_computation(self):
        block = DecoderBlock(
            D_MODEL, N_HEADS, D_FF, dropout=0.0, pre_norm=False
        )
        block.eval()
        x = torch.randn(B, T, D_MODEL)
        a = block.attn(x)
        h = block.norm1(x + a)
        expected = block.norm2(h + block.ffn(h))
        torch.testing.assert_close(block(x), expected, atol=1e-6, rtol=1e-6)


class TestDropoutBehavior(unittest.TestCase):
    def test_train_differs_from_eval(self):
        block = DecoderBlock(D_MODEL, N_HEADS, D_FF, dropout=DROPOUT)
        x = torch.randn(B, T, D_MODEL)
        block.train()
        out_train_a = block(x)
        out_train_b = block(x)
        block.eval()
        out_eval_a = block(x)
        out_eval_b = block(x)
        self.assertFalse(torch.allclose(out_train_a, out_train_b))
        torch.testing.assert_close(out_eval_a, out_eval_b, atol=1e-6, rtol=1e-6)


@unittest.skip("skeleton B2; prediction dijalankan di B12")
class TestGradients(unittest.TestCase):
    def test_gradients_flow_to_all_parameters(self):
        block = DecoderBlock(D_MODEL, N_HEADS, D_FF)
        x = torch.randn(B, T, D_MODEL)
        loss = block(x).sum()
        loss.backward()
        for name, param in block.named_parameters():
            self.assertIsNotNone(param.grad, f"param {name} has None gradient")
            self.assertTrue(torch.count_nonzero(param.grad) > 0, f"param {name} grad zero")


if __name__ == "__main__":
    unittest.main()