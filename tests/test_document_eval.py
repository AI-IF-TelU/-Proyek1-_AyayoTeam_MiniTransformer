"""Tests for document-level evaluation protocol (Tier 0, no retrain)."""

import math

import torch

from src.data.dataset import chunked_document_batches, iter_document_chunks
from src.train import evaluate_per_document


class _Tok:
    def __init__(self):
        self.special_tokens = {"<pad>": 0, "<bos>": 1, "<eos>": 2, "<unk>": 3}

    def encode(self, text):
        return [4 + (i % 5) for i in range(len(text.split()))]


class _ConstantModel(torch.nn.Module):
    """Uniform logits with a dummy parameter so `next(model.parameters())` works."""

    def __init__(self, vocab=10):
        super().__init__()
        self.dummy = torch.nn.Parameter(torch.zeros(1))
        self.vocab = vocab

    def forward(self, x):
        return torch.zeros(x.size(0), x.size(1), self.vocab)


def test_iter_document_chunks_is_non_overlapping_and_keeps_every_token():
    text = " ".join(["kata"] * 200)
    chunks = list(iter_document_chunks([text], _Tok(), context_length=64))
    assert chunks, "expected chunks"
    assert all(len(x) == len(y) for x, y, _ in chunks)
    assert all(len(x) <= 64 for x, _, _ in chunks)
    total_targets = sum(len(y) for _, y, _ in chunks)
    assert total_targets == 2 + 200 - 1
    assert {doc for _, _, doc in chunks} == {0}


def test_iter_document_chunks_labels_each_document():
    texts = [" ".join(["a"] * 100), " ".join(["b"] * 30)]
    docs = {doc for _, _, doc in iter_document_chunks(texts, _Tok(), 64)}
    assert docs == {0, 1}


def test_chunked_document_batches_pads_and_keeps_doc_ids():
    texts = [" ".join(["a"] * 70), " ".join(["b"] * 10)]
    batches = list(chunked_document_batches(texts, _Tok(), context_length=64,
                                            batch_size=2))
    assert batches
    for x, y, doc_ids in batches:
        assert x.shape == y.shape
        assert x.dtype == torch.long
        assert len(doc_ids) == x.size(0)
    assert {d for _, _, ids in batches for d in ids} == {0, 1}


def test_evaluate_per_document_matches_uniform_loss():
    x = torch.randint(4, 10, (4, 8))
    y = torch.randint(4, 10, (4, 8))
    model = _ConstantModel(vocab=10)
    loss, sd, n = evaluate_per_document(model, [(x, y, [0, 0, 1, 1])])
    assert n == 2
    assert abs(loss - torch.log(torch.tensor(10.0)).item()) < 1e-4
    assert sd >= 0.0


def test_evaluate_per_document_ignores_padding_rows():
    x = torch.full((2, 4), 0)
    y = torch.tensor([[4, 5, 0, 0], [4, 5, 0, 0]])
    model = _ConstantModel(vocab=10)
    padded, _, _ = evaluate_per_document(model, [(x, y, [0, 1])])
    assert abs(padded - torch.log(torch.tensor(10.0)).item()) < 1e-4


def test_ignore_ids_excludes_unk_from_loss():
    x = torch.full((1, 4), 5)
    y = torch.tensor([[3, 3, 7, 7]])   # first half is <unk>
    model = _ConstantModel(vocab=10)
    with_unk, _, _ = evaluate_per_document(model, [(x, y, [0])])
    without, _, _ = evaluate_per_document(model, [(x, y, [0])], ignore_ids=(3,))
    assert abs(with_unk - math.log(10)) < 1e-4
    assert abs(without - math.log(10)) < 1e-4, "uniform model gives same loss per token"


def test_ignore_ids_drops_documents_that_become_empty():
    x = torch.full((2, 3), 5)
    y = torch.tensor([[3, 3, 3], [7, 7, 7]])
    model = _ConstantModel(vocab=10)
    mean, _, n = evaluate_per_document(model, [(x, y, [0, 1])], ignore_ids=(3,))
    assert n == 1, "a document with no countable token carries no evidence"
    assert abs(mean - math.log(10)) < 1e-4, "all-unk document must not pull the mean to 0"


def test_ignore_ids_reports_lower_loss_when_unk_is_hard():
    class _UnkSensitive(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.dummy = torch.nn.Parameter(torch.zeros(1))

        def forward(self, x):
            logits = torch.zeros(x.size(0), x.size(1), 10)
            logits[..., 3] = -10.0     # cannot predict <unk>
            logits[..., 7] = 10.0      # always right for token 7
            return logits

    x = torch.full((1, 4), 5)
    y = torch.tensor([[3, 3, 7, 7]])
    with_unk, _, _ = evaluate_per_document(_UnkSensitive(), [(x, y, [0])])
    without, _, _ = evaluate_per_document(_UnkSensitive(), [(x, y, [0])], ignore_ids=(3,))
    assert without < with_unk
