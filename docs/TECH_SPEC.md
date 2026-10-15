# Technical Specification

**Status:** Draft awal untuk ditinjau sebelum coding. Jangan mengubah keputusan yang sudah disetujui tanpa mencatatnya di `ARCHITECTURE_DECISIONS.md`.

## 1. Keputusan awal

| Komponen | Keputusan |
|---|---|
| Framework | Python + PyTorch |
| Tokenizer | Regex berbasis kata dan tanda baca |
| Special tokens | `<unk>`, `<bos>`, `<eos>`; tambahan hanya jika diperlukan dan disetujui |
| Positional encoding | Sinusoidal, implementasi mandiri |
| Attention | Causal Multi-Head Self-Attention, implementasi mandiri |
| Decoder block | Attention + Feed-Forward Network, residual connections, LayerNorm |
| Objective | Next-token prediction |
| Loss | Cross-Entropy |
| Optimizer | AdamW |
| Initial configuration | `n_layers=2`, `n_heads=4`, `d_model=64`, `context_length=64` |
| Evaluation | Train/validation loss, causal-mask tests, generation samples |

Semua angka adalah konfigurasi awal yang dapat disesuaikan berdasarkan eksperimen yang terdokumentasi.

## 2. Batas library

Dilarang memakai `nn.Transformer`, `nn.TransformerDecoder`, atau `nn.MultiheadAttention` untuk menggantikan inti implementasi manual. Penggunaan operasi tensor, `nn.Linear`, `nn.Embedding`, autograd, loss, optimizer, dan utilitas dasar PyTorch diizinkan.

## 3. Kontrak modul yang direncanakan

### Tokenizer
- `fit(texts: Sequence[str]) -> None`
- `encode(text: str) -> list[int]`
- `decode(token_ids: Sequence[int]) -> str`
- Vocabulary hanya dipelajari dari data train, bukan test.

### Dataset
- Menghasilkan pasangan `x` dan `y` dengan bentuk `[sequence_length]`.
- `y` harus merupakan pergeseran satu token dari `x`.
- Pembentukan split dilakukan berdasarkan dokumen sebelum window token dibangun.

### Positional Encoding
- Input/output berbentuk `[batch, sequence, d_model]`.
- Panjang urutan tidak boleh melampaui panjang posisi yang dialokasikan.

### Causal Multi-Head Self-Attention
- Input: `[batch, sequence, d_model]`.
- Output: `[batch, sequence, d_model]`.
- `d_model % n_heads == 0`.
- Mask harus mencegah setiap posisi memperhatikan posisi masa depan.

### Decoder Block
- Input/output: `[batch, sequence, d_model]`.
- Menggunakan pre-norm atau post-norm secara konsisten; keputusan final harus dicatat sebelum integrasi.

### MiniGPT
- Input token ID: `[batch, sequence]`.
- Output logits: `[batch, sequence, vocab_size]`.
- Tidak menggunakan model pretrained.

## 4. Kompleksitas yang harus dilaporkan

Dengan batch size `B`, panjang urutan `T`, model dimension `d`, dan jumlah head `H`:
- Attention: waktu sekitar `O(B*T^2*d)`.
- Attention matrix: memori sekitar `O(B*H*T^2)`.
- Feed-forward: waktu sekitar `O(B*T*d^2)` jika hidden dimension seorde dengan `d`.

Gunakan parameter aktual dan jelaskan asumsi analisis pada laporan.

## 5. Data split

Pertahankan test split bawaan dataset jika split tersebut tersedia dan kualitasnya sudah diperiksa. Pisahkan validation dari train. Cegah kebocoran antarartikel dan dokumentasikan strategi split yang sebenarnya dipakai.
