from typing import List, Sequence, Tuple
import torch
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pad_sequence
from .tokenizer import Tokenizer

def pad_collate_fn(batch: List[Tuple[torch.Tensor, torch.Tensor]], pad_id: int = 0, max_len: int = 64) -> Tuple[torch.Tensor, torch.Tensor]:
    x_list, y_list = zip(*batch)
    x_padded = pad_sequence(x_list, batch_first=True, padding_value=pad_id)
    y_padded = pad_sequence(y_list, batch_first=True, padding_value=pad_id)
    
    if x_padded.size(1) < max_len:
        pad_size = max_len - x_padded.size(1)
        x_padded = torch.nn.functional.pad(x_padded, (0, pad_size), value=pad_id)
        y_padded = torch.nn.functional.pad(y_padded, (0, pad_size), value=pad_id)
    elif x_padded.size(1) > max_len:
        x_padded = x_padded[:, :max_len]
        y_padded = y_padded[:, :max_len]
        
    return x_padded, y_padded

def create_dataloader(dataset: Dataset, batch_size: int = 32, shuffle: bool = True, pad_id: int = 0, context_length: int = 64) -> DataLoader:
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        collate_fn=lambda b: pad_collate_fn(b, pad_id=pad_id, max_len=context_length)
    )

def add_bos_eos(token_ids: List[int], bos_id: int = 1, eos_id: int = 2) -> List[int]:
    """Sisipkan BOS ID di awal dan EOS ID di akhir urutan token."""
    return [bos_id] + token_ids + [eos_id]

class TextDataset(Dataset):
    def __init__(self, texts: Sequence[str], tokenizer: Tokenizer, context_length: int = 64):
        self.tokenizer = tokenizer
        self.context_length = context_length
        self.samples: List[Tuple[List[int], List[int]]] = []

        window_size = context_length + 1
        bos_id = tokenizer.special_tokens["<bos>"]
        eos_id = tokenizer.special_tokens["<eos>"]

        for text in texts:
            token_ids = self.tokenizer.encode(text)
            if not token_ids:
                continue
            full_ids = add_bos_eos(token_ids, bos_id=bos_id, eos_id=eos_id)
            if len(full_ids) < 2:
                continue

            if len(full_ids) >= window_size:
                for i in range(len(full_ids) - window_size + 1):
                    window = full_ids[i : i + window_size]
                    self.samples.append((window[:context_length], window[1:window_size]))
            else:
                self.samples.append((full_ids[:-1], full_ids[1:]))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        x, y = self.samples[idx]
        return torch.tensor(x, dtype=torch.long), torch.tensor(y, dtype=torch.long)
