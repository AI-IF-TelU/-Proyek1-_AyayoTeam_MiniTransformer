from typing import List, Sequence
import torch
from torch.utils.data import Dataset
from .tokenizer import Tokenizer

def add_bos_eos(token_ids: List[int], bos_id: int = 1, eos_id: int = 2) -> List[int]:
    """Sisipkan BOS ID di awal dan EOS ID di akhir urutan token."""
    return [bos_id] + token_ids + [eos_id]

class TextDataset(Dataset):
    def __init__(self, texts: Sequence[str], tokenizer: Tokenizer, max_length: int = 64):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.data = []

        for text in texts:
            token_ids = self.tokenizer.encode(text)
            if not token_ids:
                continue
            token_ids = add_bos_eos(token_ids, bos_id=tokenizer.special_tokens["<bos>"], eos_id=tokenizer.special_tokens["<eos>"])
            self.data.append(token_ids)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]
