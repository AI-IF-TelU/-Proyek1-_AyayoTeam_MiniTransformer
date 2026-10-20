import pytest
from src.data.tokenizer import Tokenizer
from src.data.dataset import add_bos_eos

def test_add_bos_eos():
    tokenizer = Tokenizer()
    tokenizer.fit(["halo dunia"])
    
    raw_ids = tokenizer.encode("halo dunia")
    processed_ids = add_bos_eos(raw_ids, bos_id=tokenizer.special_tokens["<bos>"], eos_id=tokenizer.special_tokens["<eos>"])
    
    assert processed_ids[0] == tokenizer.special_tokens["<bos>"]  # 1
    assert processed_ids[-1] == tokenizer.special_tokens["<eos>"] # 2
    assert processed_ids[1:-1] == raw_ids
    print("\nTest BOS/EOS Passed Successfully!")

if __name__ == "__main__":
    test_add_bos_eos()
