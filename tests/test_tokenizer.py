import pytest
from src.data.tokenizer import Tokenizer

def test_tokenizer_fit_and_encode():
    texts = ["Halo dunia!", "Halo mini transformer."]
    tokenizer = Tokenizer()
    tokenizer.fit(texts)
    
    assert tokenizer.vocab_size > 4
    assert tokenizer.token_to_id["<pad>"] == 0
    assert tokenizer.token_to_id["<bos>"] == 1
    assert tokenizer.token_to_id["<eos>"] == 2
    assert tokenizer.token_to_id["<unk>"] == 3

    encoded = tokenizer.encode("Halo dunia baru")
    assert isinstance(encoded, list)
    # "baru" harusnya <unk> karena tidak ada di fit
    assert encoded[-1] == 3

def test_tokenizer_decode():
    tokenizer = Tokenizer()
    tokenizer.fit(["tes tokenizer"])
    ids = [tokenizer.token_to_id["tes"]]
    decoded = tokenizer.decode(ids)
    assert decoded == "tes"
