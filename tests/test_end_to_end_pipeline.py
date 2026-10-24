"""Cross-module integration tests: tokenizer -> dataset -> model -> loss -> generation.

These tests use the real Issue A/B/C components (no stubs) and are marked
``integration`` so the default suite stays fast; run them with
``python -m pytest -q --run-integration``.

Every assertion checks contract behaviour from ``docs/TECH_SPEC.md`` (§3-§6),
not merely "no exception".
"""

import json
from pathlib import Path

import pytest
import torch
import torch.nn.functional as F

from src.data.dataset import TextDataset, create_dataloader
from src.data.tokenizer import Tokenizer
from src.generate import generate
from src.model.minigpt import MiniGPT

pytestmark = pytest.mark.integration

PAD_ID, BOS_ID, EOS_ID = 0, 1, 2
CORPUS_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "train.jsonl"

LONG_TEXT = (
    "jakarta menteri koordinator bidang kemaritiman dan investasi menantang anak muda "
    "ahli teknologi informasi untuk membereskan ribuan aplikasi pemerintahan yang ada "
    "di seluruh kementerian dan lembaga negara indonesia pada tahun ini"
)
SHORT_TEXTS = [
    "halo dunia",
    "presiden berkunjung ke papua",
    "harga beras naik di pasar",
    "tim nasional menang",
]


def _fit_tokenizer(texts):
    tok = Tokenizer()
    tok.fit(texts)
    return tok


def _tiny_model(vocab_size, context_length=64, dropout=0.0):
    return MiniGPT(
        vocab_size=vocab_size,
        n_layers=1,
        n_heads=2,
        d_model=8,
        context_length=context_length,
        dropout=dropout,
    )


def test_tokenizer_dataset_model_shapes():
    texts = [LONG_TEXT] * 6 + SHORT_TEXTS
    tok = _fit_tokenizer(texts)
    ds = TextDataset(texts, tok, context_length=64)
    assert len(ds) > 0, "pipeline produced no training samples"

    loader = create_dataloader(ds, batch_size=4, shuffle=False, pad_id=PAD_ID, context_length=64)
    x, y = next(iter(loader))

    assert tuple(x.shape) == (4, 64), f"x shape {tuple(x.shape)} != (4, 64)"
    assert tuple(y.shape) == (4, 64), f"y shape {tuple(y.shape)} != (4, 64)"
    assert x.dtype == torch.long and y.dtype == torch.long
    assert int(x.max()) < tok.vocab_size
    assert int(y.max()) < tok.vocab_size

    # TECH_SPEC 4: x[i, t] == y[i, t-1] where both sides are non-pad.
    # Positions where a short document's x side is padding are excluded, because
    # the collate step pads x and y independently on the right.
    shift_mask = (y[:, :-1] != PAD_ID) & (x[:, 1:] != PAD_ID)
    assert shift_mask.any(), "batch has no usable non-pad shifted positions"
    assert torch.equal(x[:, 1:][shift_mask], y[:, :-1][shift_mask]), (
        "x[i, t] != y[i, t-1] for non-pad positions (TECH_SPEC 4)"
    )

    model = _tiny_model(tok.vocab_size)
    logits = model(x)
    assert tuple(logits.shape) == (4, 64, tok.vocab_size)
    assert logits.dtype == torch.float32
    assert torch.isfinite(logits).all()

    with pytest.raises(ValueError):
        model(torch.zeros(1, 65, dtype=torch.long))


def test_padding_positions_ignored_by_loss():
    texts = [LONG_TEXT] * 4 + SHORT_TEXTS
    tok = _fit_tokenizer(texts)
    ds = TextDataset(texts, tok, context_length=64)
    loader = create_dataloader(ds, batch_size=8, shuffle=False, pad_id=PAD_ID, context_length=64)
    x, y = next(iter(loader))
    padded = int((y == PAD_ID).sum())
    assert padded > 0, "batch has no padded targets; padding behaviour is untested"

    model = _tiny_model(tok.vocab_size)
    model.eval()
    with torch.no_grad():
        logits = model(x)

    criterion = torch.nn.CrossEntropyLoss(ignore_index=PAD_ID)
    loss = criterion(logits.reshape(-1, tok.vocab_size), y.reshape(-1))

    per_token = F.cross_entropy(
        logits.reshape(-1, tok.vocab_size), y.reshape(-1), reduction="none"
    )
    mask = y.reshape(-1) != PAD_ID
    expected = per_token[mask].sum() / mask.sum()

    assert torch.isfinite(loss)
    assert torch.allclose(loss, expected, atol=1e-6), (
        f"ignore_index loss {loss.item():.6f} != masked mean {expected.item():.6f}"
    )


def test_training_step_updates_parameters():
    texts = [LONG_TEXT] * 6 + SHORT_TEXTS
    tok = _fit_tokenizer(texts)
    ds = TextDataset(texts, tok, context_length=64)
    loader = create_dataloader(ds, batch_size=4, shuffle=False, pad_id=PAD_ID, context_length=64)
    x, y = next(iter(loader))

    model = _tiny_model(tok.vocab_size, dropout=0.0)
    criterion = torch.nn.CrossEntropyLoss(ignore_index=PAD_ID)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)

    before = {name: p.detach().clone() for name, p in model.named_parameters()}
    optimizer.zero_grad()
    logits = model(x)
    loss = criterion(logits.reshape(-1, tok.vocab_size), y.reshape(-1))
    assert torch.isfinite(loss)
    loss.backward()
    assert model.token_emb.weight.grad is not None
    assert torch.count_nonzero(model.token_emb.weight.grad) > 0
    assert model.lm_head.weight.grad is not None
    assert torch.count_nonzero(model.lm_head.weight.grad) > 0
    optimizer.step()

    changed = [
        name for name, p in model.named_parameters()
        if not torch.allclose(p.detach(), before[name])
    ]
    assert changed, "optimizer.step() changed no parameter"
    assert "token_emb.weight" in changed and "lm_head.weight" in changed


def _force_next_token(model, prompt_ids, token_id):
    """Bias a real MiniGPT so argmax is always ``token_id`` for ``prompt_ids``.

    The LM head has no bias, so the direction of the final hidden state decides
    the sign of every logit. Setting every row to ``-h/||h||`` and the target row
    to ``+10 h/||h||`` makes the target strictly dominant without stubbing the
    model: the forward pass, LayerNorm, PE and decoder blocks stay real.
    """
    captured = {}

    def hook(module, inputs, output):
        captured["h"] = inputs[0].detach()

    handle = model.lm_head.register_forward_hook(hook)
    with torch.no_grad():
        model(torch.tensor([prompt_ids], dtype=torch.long))
    handle.remove()

    direction = captured["h"][0, -1]
    direction = direction / direction.norm()
    with torch.no_grad():
        model.lm_head.weight.copy_(
            -direction.expand_as(model.lm_head.weight)
        )
        model.lm_head.weight[token_id] = 10.0 * direction


class _RecordingTokenizer:
    """Real Tokenizer plus a record of the ids passed to decode."""

    def __init__(self, tokenizer):
        self._tokenizer = tokenizer
        self.decoded_ids = None

    def encode(self, text):
        return self._tokenizer.encode(text)

    def decode(self, ids):
        self.decoded_ids = [int(i) for i in ids]
        return self._tokenizer.decode(ids)


def test_generate_with_real_tokenizer_and_model():
    texts = [LONG_TEXT] * 6 + SHORT_TEXTS
    tok = _fit_tokenizer(texts)
    model = _tiny_model(tok.vocab_size)

    prompt = "menteri"
    prompt_ids = [BOS_ID] + tok.encode(prompt)
    _force_next_token(model, prompt_ids, tok.token_to_id["jakarta"])

    for max_new_tokens in (0, 3, 8):
        recording = _RecordingTokenizer(tok)
        out = generate(model, recording, prompt, max_new_tokens=max_new_tokens, eos_id=-1)
        assert isinstance(out, str)
        assert out.split()[0] == "menteri"
        assert recording.decoded_ids[: len(prompt_ids) - 1] == prompt_ids[1:]
        assert len(recording.decoded_ids) == len(prompt_ids) - 1 + max_new_tokens, (
            f"max_new_tokens={max_new_tokens} produced "
            f"{len(recording.decoded_ids) - (len(prompt_ids) - 1)} tokens"
        )


def test_generate_stops_at_eos_on_real_model():
    texts = [LONG_TEXT] * 6 + SHORT_TEXTS
    tok = _fit_tokenizer(texts)
    model = _tiny_model(tok.vocab_size)

    prompt = "menteri"
    prompt_ids = [BOS_ID] + tok.encode(prompt)
    _force_next_token(model, prompt_ids, EOS_ID)

    recording = _RecordingTokenizer(tok)
    out = generate(model, recording, prompt, max_new_tokens=8)

    assert out == tok.decode(prompt_ids)
    assert recording.decoded_ids == prompt_ids[1:], (
        f"generation appended tokens after <eos>: {recording.decoded_ids}"
    )


def test_generate_sliding_window_on_long_prompt():
    texts = [LONG_TEXT] * 6 + SHORT_TEXTS
    tok = _fit_tokenizer(texts)
    model = _tiny_model(tok.vocab_size, context_length=64)

    prompt_ids = tok.encode(" ".join([LONG_TEXT] * 3))
    assert len(prompt_ids) > model.context_length
    prompt = " ".join(tok.decode([i]) for i in prompt_ids)

    out = generate(model, tok, prompt, max_new_tokens=2, eos_id=-1)
    assert isinstance(out, str) and out.strip()


def test_real_corpus_windows_and_forward():
    if not CORPUS_PATH.exists():
        pytest.fail(f"real corpus not available: {CORPUS_PATH}")

    texts = []
    with CORPUS_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            if len(texts) == 60:
                break
            content = json.loads(line).get("content", "").strip()
            if content:
                texts.append(content)
    assert len(texts) == 60, f"expected 60 documents, read {len(texts)}"

    tok = _fit_tokenizer(texts)
    ds = TextDataset(texts, tok, context_length=64)

    expected_windows = 0
    for text in texts:
        full_ids = [BOS_ID] + tok.encode(text) + [EOS_ID]
        if len(full_ids) >= 65:
            expected_windows += len(full_ids) - 64
        elif len(full_ids) >= 4:
            expected_windows += 1
    assert len(ds) == expected_windows, (
        f"dataset windows {len(ds)} != per-document sum {expected_windows} "
        "(cross-document windowing detected)"
    )
    assert len(ds) > 0

    for x_ids, _ in ds.samples:
        assert len(x_ids) <= 64
        assert all(0 <= i < tok.vocab_size for i in x_ids)
        if BOS_ID in x_ids:
            assert x_ids[0] == BOS_ID, "<bos> inside a window but not at position 0"

    loader = create_dataloader(ds, batch_size=4, shuffle=False, pad_id=PAD_ID, context_length=64)
    x, y = next(iter(loader))
    assert tuple(x.shape) == (4, 64)

    model = _tiny_model(tok.vocab_size, dropout=0.0)
    criterion = torch.nn.CrossEntropyLoss(ignore_index=PAD_ID)
    logits = model(x)
    assert tuple(logits.shape) == (4, 64, tok.vocab_size)
    loss = criterion(logits.reshape(-1, tok.vocab_size), y.reshape(-1))
    assert torch.isfinite(loss)
    loss.backward()
    assert model.lm_head.weight.grad is not None
    assert torch.count_nonzero(model.lm_head.weight.grad) > 0
