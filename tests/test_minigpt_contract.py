"""Tes kontrak MiniGPT (Issue D, subtask D6).

Melengkapi `tests/test_minigpt_logits.py` dan `tests/test_minigpt_mock.py`
milik Issue C (shape/dtype + guard) dengan pembuktian perilaku kontraktual
`TECH_SPEC.md` 6:

- komposisi: `Embedding -> + PE -> n_layers x DecoderBlock -> LayerNorm -> Linear`
  dengan `d_ff = 4 * d_model` dan LM head tidak di-tie ke embedding (baseline);
- `forward(idx: [B, T] int64) -> logits [B, T, V] float32` pada konfigurasi
  baseline penuh (`B=2, T=context_length=64, V=100`);
- guard `T > context_length` memakai nilai `context_length` yang dikonfigurasi
  (bukan hardcode 64) -> `ValueError`, sedangkan `T == context_length` lolos;
- causal masking tetap berlaku setelah Embedding + PE + seluruh block + head;
- positional encoding benar-benar diterapkan (token identik pada posisi berbeda
  menghasilkan logits berbeda);
- gradien mengalir ke seluruh parameter model (embedding, semua block, LayerNorm
  akhir, LM head) dan ke input token-embedding;
- `eval()` deterministik, `train()` (dropout 0.1) berbeda;
- `d_model % n_heads != 0` -> `ValueError`.

Dropout dinolkan dan model di-`eval()` pada tes invariance agar hasil
deterministik; invariance causal diuji eksak (`atol=0`) karena posisi masa depan
mendapat bobot softmax tepat nol.
"""
import unittest

import torch

from src.model.decoder_block import DecoderBlock
from src.model.minigpt import MiniGPT
from src.model.positional_encoding import SinCosPositionalEncoding

B, T, D_MODEL = 2, 64, 64
N_HEADS = 4
N_LAYERS = 2
CONTEXT_LENGTH = 64
VOCAB_SIZE = 100
D_FF = 4 * D_MODEL
LAYER_NORM_EPS = 1e-5


def _make_model(context_length: int = CONTEXT_LENGTH, dropout: float = 0.0) -> MiniGPT:
    model = MiniGPT(
        vocab_size=VOCAB_SIZE,
        n_layers=N_LAYERS,
        n_heads=N_HEADS,
        d_model=D_MODEL,
        context_length=context_length,
        dropout=dropout,
        layer_norm_eps=LAYER_NORM_EPS,
    )
    model.eval()
    return model


def _token_batch(batch: int = B, length: int = T) -> torch.Tensor:
    return torch.randint(4, VOCAB_SIZE, (batch, length), dtype=torch.long)


def _assert_shape(tensor: torch.Tensor, expected: tuple) -> None:
    assert tuple(tensor.shape) == expected, (
        f"shape {tuple(tensor.shape)} != expected {expected}"
    )


class TestMiniGPTStructure(unittest.TestCase):
    """Komposisi model harus sesuai TECH_SPEC 6, bukan sekadar bisa forward."""

    def test_component_types_and_baseline_hyperparameters(self):
        model = _make_model()
        self.assertEqual(model.vocab_size, VOCAB_SIZE)
        self.assertEqual(len(model.blocks), N_LAYERS)
        self.assertIsInstance(model.pos_enc, SinCosPositionalEncoding)
        for block in model.blocks:
            self.assertIsInstance(block, DecoderBlock)
            self.assertEqual(block.d_ff, D_FF)
            self.assertTrue(block.pre_norm)
        self.assertAlmostEqual(model.ln_f.eps, LAYER_NORM_EPS)
        self.assertEqual(model.token_emb.embedding_dim, D_MODEL)

    def test_lm_head_is_not_tied_to_embedding(self):
        """Baseline: bobot LM head terpisah dari embedding (TECH_SPEC 6)."""
        model = _make_model()
        self.assertEqual(model.lm_head.weight.shape, (VOCAB_SIZE, D_MODEL))
        self.assertIsNone(model.lm_head.bias)
        self.assertIsNot(model.lm_head.weight, model.token_emb.weight)
        self.assertNotEqual(
            model.lm_head.weight.data_ptr(), model.token_emb.weight.data_ptr()
        )

    def test_positional_encoding_buffer_shape(self):
        model = _make_model()
        buffers = dict(model.named_buffers())
        self.assertIn("pos_enc.pe", buffers)
        pe = buffers["pos_enc.pe"]
        self.assertEqual(tuple(pe.shape), (CONTEXT_LENGTH, D_MODEL))
        self.assertFalse(pe.requires_grad)


class TestMiniGPTForwardShape(unittest.TestCase):
    def test_baseline_shape_dtype_finite(self):
        model = _make_model()
        idx = _token_batch()
        logits = model(idx)
        _assert_shape(logits, (B, T, VOCAB_SIZE))
        self.assertEqual(logits.dtype, torch.float32)
        self.assertTrue(torch.isfinite(logits).all())

    def test_single_token_sequence(self):
        model = _make_model()
        logits = model(_token_batch(B, 1))
        _assert_shape(logits, (B, 1, VOCAB_SIZE))
        self.assertTrue(torch.isfinite(logits).all())


class TestMiniGPTContextGuard(unittest.TestCase):
    def test_boundary_at_baseline_context_length(self):
        model = _make_model()
        logits = model(_token_batch(B, CONTEXT_LENGTH))
        _assert_shape(logits, (B, CONTEXT_LENGTH, VOCAB_SIZE))
        with self.assertRaises(ValueError):
            model(_token_batch(B, CONTEXT_LENGTH + 1))

    def test_guard_uses_configured_context_length(self):
        """Batas mengikuti `context_length` yang dikonfigurasi, bukan hardcode 64."""
        short = _make_model(context_length=8)
        logits = short(_token_batch(B, 8))
        _assert_shape(logits, (B, 8, VOCAB_SIZE))
        with self.assertRaises(ValueError):
            short(_token_batch(B, 9))

        long = _make_model(context_length=128)
        _assert_shape(long(_token_batch(B, 128)), (B, 128, VOCAB_SIZE))


class TestMiniGPTCausality(unittest.TestCase):
    def test_every_cut_leaves_past_unchanged(self):
        """Mengubah token idx[:, k:] tidak boleh mengubah logits[:, :k]."""
        model = _make_model()
        idx = _token_batch()
        base = model(idx)
        for cut in (1, 8, T // 2, T - 1):
            perturbed = idx.clone()
            perturbed[:, cut:] = (perturbed[:, cut:] + 1) % VOCAB_SIZE
            perturbed[:, cut:] = perturbed[:, cut:].clamp(min=4)
            logits = model(perturbed)
            torch.testing.assert_close(
                logits[:, :cut], base[:, :cut], atol=0.0, rtol=0.0
            )

    def test_last_position_reacts_to_last_token(self):
        """Kontrol sensitivitas: logits posisi terakhir bergantung token terakhir."""
        model = _make_model()
        idx = _token_batch()
        base = model(idx)
        perturbed = idx.clone()
        perturbed[:, -1] = (perturbed[:, -1] + 1) % VOCAB_SIZE
        perturbed[:, -1] = perturbed[:, -1].clamp(min=4)
        logits = model(perturbed)
        self.assertFalse(
            torch.allclose(logits[:, -1], base[:, -1], atol=1e-6, rtol=1e-6)
        )


class TestPositionalEncodingIsApplied(unittest.TestCase):
    def test_identical_tokens_at_different_positions_give_different_logits(self):
        """Tanpa PE, urutan token identik menghasilkan logits identik per posisi."""
        model = _make_model()
        idx = torch.full((1, 8), 7, dtype=torch.long)
        logits = model(idx)
        self.assertFalse(
            torch.allclose(logits[0, 0], logits[0, 1], atol=1e-6, rtol=1e-6)
        )
        self.assertFalse(
            torch.allclose(logits[0, 1], logits[0, 2], atol=1e-6, rtol=1e-6)
        )


class TestMiniGPTGradients(unittest.TestCase):
    def test_all_parameters_receive_finite_nonzero_gradient(self):
        model = _make_model(dropout=0.0)
        logits = model(_token_batch())
        logits.sum().backward()
        params = list(model.named_parameters())
        self.assertTrue(params, "model tidak memiliki parameter")
        for name, param in params:
            self.assertIsNotNone(param.grad, f"param {name} grad is None")
            self.assertTrue(torch.isfinite(param.grad).all(), f"{name} grad not finite")
            self.assertTrue(
                torch.count_nonzero(param.grad) > 0, f"param {name} grad all zero"
            )

    def test_embedding_gradient_reaches_used_token_ids_only(self):
        model = _make_model(dropout=0.0)
        idx = torch.full((1, 4), 7, dtype=torch.long)
        model(idx).sum().backward()
        grad = model.token_emb.weight.grad
        self.assertIsNotNone(grad)
        self.assertTrue(torch.count_nonzero(grad[7]) > 0)
        unused = torch.ones(VOCAB_SIZE, dtype=torch.bool)
        unused[7] = False
        self.assertTrue(torch.count_nonzero(grad[unused]) == 0)


class TestDropoutBehavior(unittest.TestCase):
    def test_eval_is_deterministic_and_train_differs(self):
        model = _make_model(dropout=0.1)
        idx = _token_batch()
        model.eval()
        eval_a = model(idx)
        eval_b = model(idx)
        torch.testing.assert_close(eval_a, eval_b, atol=0.0, rtol=0.0)
        model.train()
        train_a = model(idx)
        train_b = model(idx)
        self.assertFalse(torch.allclose(train_a, train_b, atol=1e-6, rtol=1e-6))


class TestMiniGPTInitValidation(unittest.TestCase):
    def test_value_error_when_d_model_not_divisible_by_n_heads(self):
        with self.assertRaises(ValueError):
            MiniGPT(vocab_size=VOCAB_SIZE, n_heads=3, d_model=D_MODEL)


if __name__ == "__main__":
    unittest.main()


def test_tie_embeddings_defaults_to_false_and_keeps_separate_head():
    from src.model.minigpt import MiniGPT
    model = MiniGPT(vocab_size=32, n_layers=1, n_heads=2, d_model=8, context_length=8)
    assert model.tie_embeddings is False
    assert model.lm_head.weight is not model.token_emb.weight


def test_tie_embeddings_shares_one_matrix():
    from src.model.minigpt import MiniGPT
    model = MiniGPT(vocab_size=32, n_layers=1, n_heads=2, d_model=8, context_length=8,
                    tie_embeddings=True)
    assert model.lm_head.weight is model.token_emb.weight


def test_tie_embeddings_saves_exactly_vocab_times_d_model_parameters():
    from src.model.minigpt import MiniGPT
    kwargs = dict(vocab_size=50, n_layers=2, n_heads=2, d_model=8, context_length=8)
    untied = MiniGPT(**kwargs, tie_embeddings=False)
    tied = MiniGPT(**kwargs, tie_embeddings=True)
    saved = sum(p.numel() for p in untied.parameters()) - sum(p.numel() for p in tied.parameters())
    assert saved == 50 * 8


def test_tied_model_forward_shape_and_gradients():
    import torch
    from src.model.minigpt import MiniGPT
    model = MiniGPT(vocab_size=20, n_layers=1, n_heads=2, d_model=8,
                    context_length=8, dropout=0.0, tie_embeddings=True)
    idx = torch.randint(1, 20, (2, 8))
    logits = model(idx)
    assert tuple(logits.shape) == (2, 8, 20)
    logits.sum().backward()
    assert model.token_emb.weight.grad is not None
    assert float(model.token_emb.weight.grad.abs().sum()) > 0


def test_tied_and_untied_are_different_models():
    import torch
    from src.model.minigpt import MiniGPT
    torch.manual_seed(0)
    kwargs = dict(vocab_size=20, n_layers=1, n_heads=2, d_model=8, context_length=8)
    tied = MiniGPT(**kwargs, tie_embeddings=True)
    assert sum(p.numel() for p in tied.parameters()) < \
        sum(p.numel() for p in MiniGPT(**kwargs, tie_embeddings=False).parameters())
