import pytest
import torch
from src.data.tokenizer import Tokenizer
from src.data.dataset import TextDataset

def test_sliding_window_and_pairs():
    tokenizer = Tokenizer()
    tokenizer.fit(["satu dua tiga empat lima enam tujuh delapan sembilan sepuluh"])

    doc1 = "satu dua tiga"
    doc2 = "empat lima"
    doc3 = ""
    texts = [doc1, doc2, doc3]

    dataset = TextDataset(texts, tokenizer, context_length=4)
    assert len(dataset) > 0

    for i in range(len(dataset)):
        x, y = dataset[i]
        assert x.shape == y.shape
        assert torch.equal(x[1:], y[:-1])

def test_no_cross_document_leak():
    tokenizer = Tokenizer()
    tokenizer.fit(["kata A", "kata B"])

    doc1 = "kata A"
    doc2 = "kata B"

    dataset = TextDataset([doc1, doc2], tokenizer, context_length=64)
    bos_id = tokenizer.special_tokens["<bos>"]
    eos_id = tokenizer.special_tokens["<eos>"]

    doc1_x, doc1_y = dataset[0]
    assert doc1_x[0].item() == bos_id
    assert doc1_y[-1].item() == eos_id

    doc2_x, doc2_y = dataset[1]
    assert doc2_x[0].item() == bos_id
    assert doc2_y[-1].item() == eos_id

    assert len(dataset) == 2

def test_empty_and_short_docs():
    tokenizer = Tokenizer()
    tokenizer.fit(["a"])

    dataset = TextDataset(["", "a"], tokenizer, context_length=64)
    assert len(dataset) == 1
    x, y = dataset[0]
    bos_id = tokenizer.special_tokens["<bos>"]
    eos_id = tokenizer.special_tokens["<eos>"]
    a_id = tokenizer.encode("a")[0]

    assert x.tolist() == [bos_id, a_id]
    assert y.tolist() == [a_id, eos_id]
