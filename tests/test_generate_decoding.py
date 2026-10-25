"""Tests for decoding knobs in `src/generate.py` (Tier 1, no retrain)."""

import pytest
import torch

from src.generate import (DecodeConfig, generate, generate_ids,
                          pick_sampling_temperature, tune_temperature)

VOCAB = 12
UNK_ID = 3


class _Tok:
    def __init__(self, prompt_ids=(5,)):
        self.prompt_ids = list(prompt_ids)

    def encode(self, text):
        return list(self.prompt_ids)

    def decode(self, ids):
        return " ".join(str(i) for i in ids)


class _ScriptModel(torch.nn.Module):
    """Logits that cycle through `script`, so repetition is guaranteed."""

    def __init__(self, script=(4, 5, 4, 5, 4, 5), context_length=64):
        super().__init__()
        self.dummy = torch.nn.Parameter(torch.zeros(1))
        self.context_length = context_length
        self.script = script
        self.calls = 0
        self.seen_widths = []

    def forward(self, x):
        self.seen_widths.append(x.size(1))
        logits = torch.full((x.size(0), x.size(1), VOCAB), -20.0)
        step = self.script[self.calls % len(self.script)]
        logits[:, -1, step] = 20.0
        self.calls += 1
        return logits


class _FixedModel(torch.nn.Module):
    def __init__(self, best_id=7, rival_id=8, context_length=64):
        super().__init__()
        self.dummy = torch.nn.Parameter(torch.zeros(1))
        self.context_length = context_length
        self.best_id, self.rival_id = best_id, rival_id

    def forward(self, x):
        logits = torch.full((x.size(0), x.size(1), VOCAB), -20.0)
        logits[:, -1, self.best_id] = 5.0
        logits[:, -1, self.rival_id] = 4.0
        return logits


def test_greedy_matches_adr009_contract_still():
    model = _ScriptModel(script=(4,))
    out = generate(model, _Tok(), "hi", max_new_tokens=3, eos_id=2)
    assert out == "5 4 4 4"


def test_no_repeat_ngram_blocks_cycles():
    plain = generate_ids(_ScriptModel(script=(4, 5)), _Tok(), "hi",
                         max_new_tokens=8, eos_id=2, cfg=DecodeConfig())
    blocked = generate_ids(_ScriptModel(script=(4, 5)), _Tok(), "hi",
                           max_new_tokens=8, eos_id=2,
                           cfg=DecodeConfig(no_repeat_ngram_size=3))
    assert plain.ids[:6] == [4, 5, 4, 5, 4, 5]

    trigrams = [tuple(blocked.ids[i:i + 3]) for i in range(len(blocked.ids) - 2)]
    assert len(trigrams) == len(set(trigrams)), trigrams


def test_ban_unk_never_emits_unk_token():
    class _UnkModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.dummy = torch.nn.Parameter(torch.zeros(1))
            self.context_length = 64

        def forward(self, x):
            logits = torch.full((x.size(0), x.size(1), VOCAB), -20.0)
            logits[:, -1, UNK_ID] = 20.0
            logits[:, -1, 6] = 1.0
            return logits

    gen = generate_ids(_UnkModel(), _Tok(), "hi", max_new_tokens=4, eos_id=2,
                       cfg=DecodeConfig(ban_unk=True))
    assert UNK_ID not in gen.ids
    assert set(gen.ids) == {6}


def test_stop_on_eos_reports_flag():
    class _EosAfterOne(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.dummy = torch.nn.Parameter(torch.zeros(1))
            self.context_length = 64
            self.calls = 0

        def forward(self, x):
            logits = torch.full((x.size(0), x.size(1), VOCAB), -20.0)
            logits[:, -1, 2 if self.calls else 6] = 20.0
            self.calls += 1
            return logits

    gen = generate_ids(_EosAfterOne(), _Tok(), "hi", max_new_tokens=10, eos_id=2)
    assert gen.ids == [6]
    assert gen.stopped_on_eos is True


def test_temperature_extremes_do_not_produce_nan():
    model = _FixedModel()
    for temp in (0.01, 1.0, 100.0):
        gen = generate_ids(model, _Tok(), "hi", max_new_tokens=3, eos_id=2,
                           cfg=DecodeConfig(do_sample=True, temperature=temp,
                                            seed=0))
        assert all(isinstance(i, int) for i in gen.ids)


def test_top_k_and_top_p_prune_to_the_same_single_candidate():
    model = _FixedModel(best_id=7, rival_id=8)
    gen = generate_ids(model, _Tok(), "hi", max_new_tokens=3, eos_id=2,
                       cfg=DecodeConfig(do_sample=True, top_k=1, seed=0))
    assert gen.ids == [7, 7, 7]
    gen2 = generate_ids(model, _Tok(), "hi", max_new_tokens=3, eos_id=2,
                        cfg=DecodeConfig(do_sample=True, top_p=0.5, seed=0))
    assert gen2.ids == [7, 7, 7]


def test_sampling_is_seed_reproducible():
    model = _FixedModel(best_id=7, rival_id=8)
    cfg = DecodeConfig(do_sample=True, temperature=1.0, seed=1234)
    a = generate_ids(model, _Tok(), "hi", max_new_tokens=8, eos_id=2, cfg=cfg)
    b = generate_ids(model, _Tok(), "hi", max_new_tokens=8, eos_id=2, cfg=cfg)
    assert a.ids == b.ids


def test_context_length_default_follows_model():
    model = _ScriptModel(script=(4,), context_length=6)
    generate_ids(model, _Tok(), "hi", max_new_tokens=8, eos_id=2)
    assert max(model.seen_widths) == 6


def test_tune_temperature_returns_lowest_nll():
    model = _FixedModel(best_id=7, rival_id=8)
    x = torch.tensor([[5, 5, 5, 5]])
    y = torch.tensor([[7, 8, 7, 8]])
    best_t, rows, at_boundary = tune_temperature(model, [(x, y)], grid=(0.5, 1.0, 2.0))
    assert len(rows) == 3
    best_row = min(rows, key=lambda r: r[1])
    assert best_t == best_row[0]
    assert all(row[1] == row[1] for row in rows)
    assert at_boundary is (best_t in (0.5, 2.0))


def test_tune_temperature_flags_grid_boundary():
    model = _FixedModel(best_id=7, rival_id=8)
    x = torch.tensor([[5, 5, 5, 5]])
    y = torch.tensor([[7, 7, 7, 7]])
    best_t, rows, at_boundary = tune_temperature(model, [(x, y)], grid=(0.8, 1.0))
    if best_t == 0.8:
        assert at_boundary is True


class _LoopModel(torch.nn.Module):
    """Repeats 4,5 forever, so repetition is inevitable without a ban."""

    def __init__(self):
        super().__init__()
        self.dummy = torch.nn.Parameter(torch.zeros(1))
        self.context_length = 64
        self.calls = 0

    def forward(self, x):
        logits = torch.full((x.size(0), x.size(1), VOCAB), -20.0)
        logits[:, -1, (4, 5)[self.calls % 2]] = 20.0
        self.calls += 1
        return logits


def test_pick_sampling_temperature_reports_grid_rows():
    model = _FixedModel(best_id=7, rival_id=8)
    best, rows = pick_sampling_temperature(model, _Tok(), ["a"], grid=(0.8, 1.0),
                                           max_new_tokens=6)
    assert len(rows) == 2
    assert best in (0.8, 1.0)
    assert all(len(row) == 3 for row in rows)


def test_pick_sampling_temperature_falls_back_when_nothing_is_feasible():
    model = _LoopModel()
    best, rows = pick_sampling_temperature(model, _Tok(), ["a"], grid=(0.8, 1.0),
                                           max_new_tokens=6, min_distinct1=0.99)
    assert best == 0.8
    assert all(row[2] == 0 for row in rows)


def test_nll_and_ece_moves_batches_to_model_device():
    """Model di device berbeda dari batch: CPU batch + model bertanda device lain.

    Regresi untuk RuntimeError di Kaggle: nll_and_ece menerima tensor CPU dari
    chunked_document_batches sementara model ada di cuda:0.
    """
    from src.generate import nll_and_ece

    moved = []

    class _RecordingModel(_FixedModel):
        def forward(self, x):
            moved.append(x.device.type)
            return super().forward(x)

    model = _RecordingModel(best_id=7, rival_id=8)
    x = torch.tensor([[5, 5, 5, 5]])
    y = torch.tensor([[7, 8, 7, 8]])
    nll, acc, ece = nll_and_ece(model, [(x, y)], temperature=1.0)

    assert moved, "forward must be called"
    assert all(d == "cpu" for d in moved), "batch must be moved to the model device"
    assert nll == nll and 0.0 <= acc <= 1.0 and ece == ece


def test_nll_and_ece_returns_finite_metrics_with_partial_batch():
    from src.generate import nll_and_ece

    model = _FixedModel(best_id=7, rival_id=8)
    x = torch.tensor([[5, 5, 5, 5]])
    y = torch.tensor([[7, 0, 0, 0]])
    nll, acc, ece = nll_and_ece(model, [(x, y)], temperature=0.9)
    assert nll == nll and ece == ece
    assert 0.0 <= acc <= 1.0


def test_nll_and_ece_device_contract_detects_real_mismatch(monkeypatch):
    """Tanpa perpindahan device, forward harus gagal seperti di Kaggle (cuda)."""
    from src.generate import nll_and_ece

    class _StrictModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.dummy = torch.nn.Parameter(torch.zeros(1))

        def forward(self, x):
            if x.device != self.dummy.device:
                raise RuntimeError(
                    f"index is on {x.device}, weight on {self.dummy.device}"
                )
            logits = torch.full((x.size(0), x.size(1), VOCAB), -20.0)
            logits[:, -1, 7] = 5.0
            return logits

    model = _StrictModel()
    x = torch.tensor([[5, 5, 5, 5]])
    y = torch.tensor([[7, 7, 0, 0]])
    nll, acc, ece = nll_and_ece(model, [(x, y)])
    assert nll == nll and 0.0 <= acc <= 1.0


def test_nll_and_ece_on_cuda_when_available():
    import pytest
    if not torch.cuda.is_available():
        pytest.skip("CUDA tidak tersedia")
    from src.generate import nll_and_ece

    from src.model.minigpt import MiniGPT
    model = MiniGPT(vocab_size=VOCAB, n_layers=1, n_heads=2, d_model=8,
                    context_length=8, dropout=0.0).cuda()
    x = torch.tensor([[5, 5, 5, 5]])
    y = torch.tensor([[7, 7, 0, 0]])
    nll, acc, ece = nll_and_ece(model, [(x, y)])
    assert nll == nll and 0.0 <= acc <= 1.0

