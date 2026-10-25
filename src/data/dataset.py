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
            # Dokumen 1 token menghasilkan len(full_ids) == 3 ([bos, token, eos])
            # TECH_SPEC.md §4: dokumen 1 token TIDAK menghasilkan pasangan.
            if len(full_ids) < 4:
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


def iter_document_chunks(texts: Sequence[str], tokenizer: Tokenizer,
                         context_length: int = 64):
    """Yield (x, y, doc_index) over NON-overlapping windows of each document.

    `TextDataset` slides with stride 1, which inflates a 80-document validation
    split into 28k highly redundant rows. For measurement, each token must be
    counted once: chunking keeps every token but yields one row per
    `context_length` tokens, so per-document losses are independent samples.
    """
    chunk = context_length + 1
    bos_id = tokenizer.special_tokens["<bos>"]
    eos_id = tokenizer.special_tokens["<eos>"]

    for doc_index, text in enumerate(texts):
        full_ids = add_bos_eos(tokenizer.encode(text), bos_id=bos_id, eos_id=eos_id)
        if len(full_ids) < 4:
            continue
        for start in range(0, len(full_ids) - 1, context_length):
            window = full_ids[start:start + chunk]
            if len(window) < 2:
                break
            yield window[:-1], window[1:], doc_index


def chunked_document_batches(texts: Sequence[str], tokenizer: Tokenizer,
                             context_length: int = 64, batch_size: int = 32,
                             pad_id: int = 0):
    """Batch `iter_document_chunks` output into padded (x, y, doc_ids) tensors."""
    xs, ys, docs = [], [], []

    def flush():
        width = max(len(x) for x in xs)
        bx = torch.full((len(xs), width), pad_id, dtype=torch.long)
        by = torch.full((len(ys), width), pad_id, dtype=torch.long)
        for row, (x, y) in enumerate(zip(xs, ys)):
            bx[row, :len(x)] = torch.tensor(x, dtype=torch.long)
            by[row, :len(y)] = torch.tensor(y, dtype=torch.long)
        return bx, by, list(docs)

    for x, y, doc in iter_document_chunks(texts, tokenizer, context_length):
        xs.append(x)
        ys.append(y)
        docs.append(doc)
        if len(xs) == batch_size:
            yield flush()
            xs, ys, docs = [], [], []
    if xs:
        yield flush()

