import torch
import pytest
from src.data.dataset import TextDataset, create_dataloader
from src.data.tokenizer import Tokenizer

def test_dataloader_padding():
    tokenizer = Tokenizer()
    # Mock vocab for testing
    texts = ["halo dunia", "apa kabar"]
    tokenizer.fit(texts) # Minimal fit to set special tokens
    
    # context_length 64 sesuai TECH_SPEC
    context_length = 64
    dataset = TextDataset(texts, tokenizer, context_length=context_length)
    
    # batch_size 2 agar bisa cek padding jika panjang berbeda (walau di sini mungkin sama)
    # Gunakan text sangat pendek agar pasti dipad ke 64
    dataloader = create_dataloader(dataset, batch_size=2, shuffle=False, pad_id=0, context_length=context_length)
    
    x, y = next(iter(dataloader))
    
    # Verifikasi shape [B, T]
    assert x.shape == (len(dataset), context_length)
    assert y.shape == (len(dataset), context_length)
    
    # Verifikasi tipe data LongTensor
    assert x.dtype == torch.long
    assert y.dtype == torch.long
    
    # Verifikasi padding (posisi kanan)
    # Dokumen pendek "halo dunia" -> tokens: [bos, halo, dunia, eos] -> len 4
    # x = tokens[:-1] -> [bos, halo, dunia] (len 3)
    # y = tokens[1:]  -> [halo, dunia, eos] (len 3)
    # Setelah pad ke 64, index 3 s/d 63 harus 0
    assert torch.all(x[:, 3:] == 0)
    assert torch.all(y[:, 3:] == 0)
    
    # Verifikasi x[i, t] == y[i, t-1] untuk non-pad
    # x[0, 0] = bos, y[0, 0] = halo
    # x[0, 1] = halo, y[0, 0] = halo -> x[0, 1] == y[0, 0]
    assert torch.all(x[:, 1:3] == y[:, 0:2])

def test_dataloader_longer_text():
    tokenizer = Tokenizer()
    # Buat text yang menghasilkan window > 64 tokens (jika digabung bos/eos)
    # Regex: r"\w+|[^\w\s]"
    # Kita buat text panjang 70 kata
    long_text = " ".join(["kata"] * 70)
    tokenizer.fit([long_text])
    
    context_length = 64
    dataset = TextDataset([long_text], tokenizer, context_length=context_length)
    
    dataloader = create_dataloader(dataset, batch_size=32, shuffle=False, pad_id=0, context_length=context_length)
    
    x, y = next(iter(dataloader))
    
    # Verifikasi shape tetap [B, 64]
    assert x.shape[1] == 64
    assert y.shape[1] == 64
    assert x.shape[0] > 0
