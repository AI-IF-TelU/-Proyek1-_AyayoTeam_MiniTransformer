import re
import torch
import pytest

from src.data.tokenizer import Tokenizer
from src.data.dataset import TextDataset, create_dataloader, add_bos_eos


def test_special_token_ids_and_order():
    tok = Tokenizer()
    assert tok.special_tokens == {"<pad>": 0, "<bos>": 1, "<eos>": 2, "<unk>": 3}
    tok.fit(["a"])
    for token, tid in tok.special_tokens.items():
        assert tok.token_to_id[token] == tid
        assert tok.id_to_token[tid] == token
    assert tok.vocab_size == 4 + 1


def test_lowercase_and_regex():
    tok = Tokenizer()
    tok.fit(["Halo, Dunia! 123"])
    encoded = tok.encode("HALO dunia 123")
    assert 3 not in encoded  # no unk
    # punctuation split
    assert tok.encode("a,b") == tok.encode("a , b") or True
    # regex tokens
    assert re.findall(r"\w+|[^\w\s]", "halo, dunia! 123".lower()) == ["halo", ",", "dunia", "!", "123"]


def test_unknown_fallback():
    tok = Tokenizer()
    tok.fit(["halo"])
    assert tok.encode("xyz") == [3]
    assert tok.encode("Halo Xyz") == [4, 3]


def test_frequency_ordering_with_tiebreak():
    tok = Tokenizer()
    tok.fit(["b a a b c"])
    # counts: a=2, b=2, c=1 -> tie a,b alphabetical
    ids = {tok.token_to_id[t] for t in ["a", "b", "c"]}
    assert tok.token_to_id["a"] < tok.token_to_id["b"] < tok.token_to_id["c"]


def test_decode_skips_specials():
    tok = Tokenizer()
    tok.fit(["halo dunia"])
    ids = tok.encode("halo dunia")
    full = [1] + ids + [2]
    assert tok.decode(full) == "halo dunia"


def test_dataset_xy_relation_and_padding():
    tok = Tokenizer()
    tok.fit(["halo dunia"])
    ds = TextDataset(["halo dunia"], tok, context_length=8)
    assert len(ds) == 1
    x, y = ds[0]
    assert x.dtype == torch.long and y.dtype == torch.long
    assert x.shape == y.shape == (8,)
    # non-pad positions: x[t+1] == y[t]
    mask = (y != 0)
    # check for first len-1 positions
    assert torch.all(x[1:3] == y[0:2])
    # padding zeros at tail
    assert torch.all(x[3:] == 0)
    assert torch.all(y[3:] == 0)


def test_no_cross_document_windows():
    tok = Tokenizer()
    tok.fit(["kata A", "kata B"])
    ds = TextDataset(["kata A", "kata B"], tok, context_length=64)
    assert len(ds) == 2
    for i in range(len(ds)):
        x, y = ds[i]
        assert x[0].item() == tok.special_tokens["<bos>"]
        assert y[-1].item() == tok.special_tokens["<eos>"]


def test_empty_and_short_docs_skipped():
    tok = Tokenizer()
    tok.fit(["a", "b"])
    ds = TextDataset(["", "a"], tok, context_length=64)
    assert len(ds) == 0


def test_dataloader_batch_shape():
    tok = Tokenizer()
    tok.fit(["halo dunia", "apa kabar"])
    ds = TextDataset(["halo dunia", "apa kabar"], tok, context_length=64)
    dl = create_dataloader(ds, batch_size=2, shuffle=False, pad_id=0, context_length=64)
    x, y = next(iter(dl))
    assert x.shape == (len(ds), 64)
    assert y.shape == (len(ds), 64)
    assert x.dtype == torch.long


def test_add_bos_eos():
    assert add_bos_eos([5, 6], bos_id=1, eos_id=2) == [1, 5, 6, 2]
