import unittest

import pytest
import torch

from src.model.attention import CausalMultiHeadAttention
from src.model.decoder_block import DecoderBlock
from src.model.positional_encoding import SinCosPositionalEncoding

pytestmark = pytest.mark.integration

B, T, D_MODEL = 2, 16, 64
N_HEADS = 4
N_LAYERS = 2
D_FF = 4 * D_MODEL
MAX_LEN = 64
DROPOUT = 0.1
LAYER_NORM_EPS = 1e-5


def _assert_shape(tensor: torch.Tensor, expected: tuple) -> None:
    assert tuple(tensor.shape) == expected, (
        f"shape {tuple(tensor.shape)} != expected {expected}"
    )


class TestComponentIntegration(unittest.TestCase):
    def _build_stack(self):
        pe = SinCosPositionalEncoding(D_MODEL, MAX_LEN)
        attn = CausalMultiHeadAttention(D_MODEL, N_HEADS, DROPOUT)
        blocks = torch.nn.ModuleList(
            [
                DecoderBlock(
                    D_MODEL,
                    N_HEADS,
                    D_FF,
                    dropout=DROPOUT,
                    layer_norm_eps=LAYER_NORM_EPS,
                )
                for _ in range(N_LAYERS)
            ]
        )
        return pe, attn, blocks

    def _forward(self, pe, attn, blocks, x):
        h = pe(x)
        h = attn(h)
        for block in blocks:
            h = block(h)
        return h

    def test_pipeline_shapes_all_layers(self):
        pe, attn, blocks = self._build_stack()
        for mod in (pe, attn, *blocks):
            mod.eval()
        x = torch.randn(B, T, D_MODEL)
        h = pe(x)
        _assert_shape(h, (B, T, D_MODEL))
        h = attn(h)
        _assert_shape(h, (B, T, D_MODEL))
        for i, block in enumerate(blocks):
            h = block(h)
            _assert_shape(h, (B, T, D_MODEL))
        self.assertTrue(torch.isfinite(h).all())

    def test_pipeline_shapes_varied_batch_and_length(self):
        pe, attn, blocks = self._build_stack()
        for mod in (pe, attn, *blocks):
            mod.eval()
        for batch, length in ((1, 1), (4, 32), (2, 64)):
            x = torch.randn(batch, length, D_MODEL)
            h = self._forward(pe, attn, blocks, x)
            _assert_shape(h, (batch, length, D_MODEL))

    def test_forward_backward_and_gradients(self):
        pe, attn, blocks = self._build_stack()
        for mod in (pe, attn, *blocks):
            mod.eval()
        x = torch.randn(B, T, D_MODEL)
        out = self._forward(pe, attn, blocks, x)
        _assert_shape(out, (B, T, D_MODEL))
        loss = out.sum()
        loss.backward()
        for name, param in attn.named_parameters():
            self.assertIsNotNone(param.grad, f"attn.{name} has None gradient")
            self.assertTrue(
                torch.count_nonzero(param.grad) > 0,
                f"attn.{name} grad zero",
            )
        for i, block in enumerate(blocks):
            for name, param in block.named_parameters():
                self.assertIsNotNone(
                    param.grad, f"block{i}.{name} has None gradient"
                )
                self.assertTrue(
                    torch.count_nonzero(param.grad) > 0,
                    f"block{i}.{name} grad zero",
                )
        self.assertIsNone(
            pe.get_buffer("pe").grad,
            "PE buffer must stay non-trainable (grad must be None)",
        )

    def test_gradient_flows_grouped_by_submodule(self):
        pe, attn, blocks = self._build_stack()
        for mod in (pe, attn, *blocks):
            mod.eval()
        x = torch.randn(B, T, D_MODEL, requires_grad=True)
        out = self._forward(pe, attn, blocks, x)
        out.sum().backward()
        self.assertIsNotNone(x.grad)
        self.assertTrue(torch.count_nonzero(x.grad) > 0)
        for i, block in enumerate(blocks):
            for submodule_name in ("norm1", "attn", "norm2", "ffn"):
                submodule = getattr(block, submodule_name)
                params = list(submodule.named_parameters())
                self.assertTrue(params, f"block{i} {submodule_name} has no params")
                for name, param in params:
                    self.assertIsNotNone(
                        param.grad,
                        f"block{i}.{submodule_name}.{name} has None gradient",
                    )
                    self.assertTrue(
                        torch.count_nonzero(param.grad) > 0,
                        f"block{i}.{submodule_name}.{name} grad zero",
                    )

    def test_no_forbidden_transformer_module(self):
        pe, attn, blocks = self._build_stack()
        for mod in (pe, attn, *blocks):
            for sub in mod.modules():
                self.assertNotIsInstance(
                    sub,
                    (
                        torch.nn.Transformer,
                        torch.nn.TransformerDecoder,
                        torch.nn.MultiheadAttention,
                    ),
                )


class TestPipelineValidation(unittest.TestCase):
    def test_value_error_when_T_exceeds_max_len(self):
        pe = SinCosPositionalEncoding(D_MODEL, MAX_LEN)
        x = torch.randn(B, T + MAX_LEN, D_MODEL)
        with self.assertRaises(ValueError):
            pe(x)

    def test_value_error_when_heads_do_not_divide(self):
        with self.assertRaises(ValueError):
            CausalMultiHeadAttention(D_MODEL, n_heads=5)


if __name__ == "__main__":
    unittest.main()