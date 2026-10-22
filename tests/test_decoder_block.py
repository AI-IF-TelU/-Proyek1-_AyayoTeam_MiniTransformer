import unittest

import torch

from src.model.decoder_block import DecoderBlock

B, T, D_MODEL = 2, 8, 64
N_HEADS = 4
D_FF = 4 * D_MODEL
DROPOUT = 0.1
LAYER_NORM_EPS = 1e-5


def _assert_shape(tensor: torch.Tensor, expected: tuple) -> None:
    assert tuple(tensor.shape) == expected, (
        f"shape {tuple(tensor.shape)} != expected {expected}"
    )


@unittest.skip("skeleton B2; prediction dijalankan di B12")
class TestDecoderBlockShape(unittest.TestCase):
    def test_output_shape(self):
        block = DecoderBlock(D_MODEL, N_HEADS, D_FF)
        _assert_shape(block(torch.randn(B, T, D_MODEL)), (B, T, D_MODEL))


@unittest.skip("skeleton B2; prediction dijalankan di B12")
class TestResidualConnection(unittest.TestCase):
    def test_output_differs_from_input(self):
        block = DecoderBlock(D_MODEL, N_HEADS, D_FF, dropout=DROPOUT)
        block.eval()
        x = torch.randn(B, T, D_MODEL)
        out = block(x)
        self.assertFalse(torch.allclose(out, x, atol=1e-6, rtol=1e-6))


@unittest.skip("skeleton B2; prediction dijalankan di B12")
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