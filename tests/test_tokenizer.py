import pytest
from src.data.tokenizer import Tokenizer

def test_tokenizer_basic():
    tokenizer = Tokenizer()
    tokenizer.fit(["Halo Dunia!", "Lari... Cepat!!!"])
    
    # Test encoding/decoding
    text = "Halo Dunia!"
    encoded = tokenizer.encode(text)
    decoded = tokenizer.decode(encoded)
    assert decoded == "halo dunia !"

def test_tokenizer_special_chars():
    tokenizer = Tokenizer()
    tokenizer.fit(["Email: a@b.com"])
    
    text = "Email: a@b.com"
    encoded = tokenizer.encode(text)
    decoded = tokenizer.decode(encoded)
    assert decoded == "email : a @ b . com"

def test_tokenizer_unknown():
    tokenizer = Tokenizer()
    tokenizer.fit(["Halo"])
    
    # "Dunia" is unknown
    encoded = tokenizer.encode("Halo Dunia")
    # "halo" -> 4 (first index after special tokens), "dunia" -> <unk> -> 3
    assert encoded == [4, 3]
