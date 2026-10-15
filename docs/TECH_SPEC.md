# Technical Specification

**Status:** Final untuk baseline Issue #1 (Step 2). Keputusan yang tercantum dicatat pada `ARCHITECTURE_DECISIONS.md`. Perubahan arsitektur atau kontrak publik wajib melalui ADR baru dan persetujuan tim.

## 1. Keputusan arsitektur

| Komponen | Keputusan | ADR |
|---|---|---|
| Framework | Python + PyTorch | ADR-001 |
| Arsitektur | Decoder-only transformer, next-token prediction | ADR-001 |
| Attention | Causal Multi-Head Self-Attention manual (tanpa `nn.MultiheadAttention`/`nn.Transformer`) | ADR-002 |
| Positional encoding | Sinusoidal, implementasi mandiri | ADR-002 |
| Decoder Block | Pre-LayerNorm; residual; FFN `d_ff = 4 * d_model`; GELU; dropout `0.1`; LayerNorm epsilon `1e-5` | ADR-007 |
| Tokenizer | Regex `r"\w+|[^\w\s]"`; lowercase sebelum tokenisasi | ADR-008 |
| Special tokens | `<pad>=0`, `<bos>=1`, `<eos>=2`, `<unk>=3` | ADR-008 |
| Dataset | Indonesian News Datasets (kolom `content`); subset awal 500–2.000 artikel | ADR-003 |
| Split | Per dokumen; 80/10/10 seed 42 hanya jika split bawaan tidak tersedia/tidak layak | ADR-010 |
| Objektif | Next-token prediction | ADR-001 |
| Loss | Cross-Entropy, token pad di target diabaikan (`ignore_index=pad_id`) | TECH_SPEC §5 |
| Optimizer | AdamW; awal `lr=3e-4`, `weight_decay=0.01` | TECH_SPEC §6 |
| Konfigurasi awal | `n_layers=2`, `n_heads=4`, `d_model=64`, `context_length=64`, `ff_dim=256` | ADR-004 |
| Seed | 42 (split data dan random seed) | ADR-010 |

Semua angka hiperparameter adalah titik awal yang boleh disesuaikan melalui eksperimen terdokumentasi, tanpa mengubah arsitektur inti.

## 2. Batas library

Dilarang menggunakan `nn.Transformer`, `nn.TransformerDecoder`, atau `nn.MultiheadAttention` untuk menggantikan inti implementasi manual. Operasi tensor dasar, `nn.Linear`, `nn.Embedding`, autograd, loss, optimizer, dan utilitas dasar PyTorch diizinkan. Tidak boleh memakai pretrained model atau external GPT API sebagai model proyek.

## 3. Kontrak tokenizer

File target: `src/data/tokenizer.py`.

- `fit(texts: Sequence[str]) -> None` — bangun vocabulary **hanya dari data train**. Urutan id: `<pad>=0`, `<bos>=1`, `<eos>=2`, `<unk>=3`, lalu token hasil regex diurutkan berdasarkan frekuensi (tidak ada batas vocab tetap; dicatat saat eksperimen).
- `encode(text: str) -> list[int]` — normalisasi lowercase, tokenisasi `re.findall(r"\w+|[^\w\s]", text)`, karakter/token di luar vocab → `<unk>`.
- `decode(ids: Sequence[int]) -> str` — gabung token kata/tanda baca dengan spasi, lalu `strip`; `bos/eos/pad/unk` tidak dirender (atau dirender sebagai spasi kosong). Roundtrip `decode(encode(t)) == t` tidak dijamin; ini perilaku yang didokumentasikan, bukan bug.
- Properti `vocab_size: int` tersedia setelah `fit`.

Perilaku token khusus: `<bos>` dan `<eos>` **tidak** dikirim sebagai string literal ke regex; keduanya disisipkan sebagai token id langsung pada tahap dataset (lihat §4).

## 4. Kontrak dataset

File target: `src/data/dataset.py`.

Urutan pemrosesan dokumen (wajib):
1. Deduplikasi berdasarkan konten ternormalisasi.
2. Split per dokumen: 80/10/10, seed 42 — **hanya jika** split bawaan dataset tidak tersedia atau tidak layak. Jika split bawaan ada dan terverifikasi, pertahankan tanpa resplit.
3. Tokenisasi tiap dokumen (mengikuti tokenizer).
4. Sisipkan `bos_id` di awal dan `eos_id` di akhir urutan token tiap dokumen.
5. Bangun window:
   - Dokumen dengan ≥ 65 token: sliding window panjang 65, stride 1.
   - Setiap window → `x = ids[:64]`, `y = ids[1:65]`.
   - Dokumen pendek: buat satu pasangan pendek (`x = ids[:-1]`, `y = ids[1:]`) saat tersedia; padding ke panjang penuh dilakukan pada tahap batching.
   - Dilarang membuat window melintasi batas dokumen.

Output batch (via `DataLoader`, collate pad → `pad_id`):
- `x`: `[B, T]` int64, `T = context_length = 64`
- `y`: `[B, T]` int64
- `x[i, t] == y[i, t-1]` untuk semua posisi non-pad.

Edge cases: dokumen hasil tokenisasi kosong dibuang; dokumen 1 token tidak menghasilkan pasangan input-target; vocab tidak pernah di-fit dari test.

## 5. Kontrak perhitungan loss

- `CrossEntropyLoss(ignore_index=pad_id)` pada logits `[B, T, V]` vs target `[B, T]` (flat `[B*T, V]` vs `[B*T]`).
- Posisi target berisi `pad_id` tidak berkontribusi ke loss.

## 6. Kontrak model dan training

### Positional Encoding (`src/model/positional_encoding.py`)

- `SinCosPositionalEncoding(d_model: int, max_len: int)`, buffer `pe: [max_len, d_model]` non-trainable.
- `forward(x: [B, T, d_model]) -> [B, T, d_model]` — tambahkan `pe[:T]`.
- `T > max_len` → `ValueError`. `max_len = context_length = 64`.

### Causal Multi-Head Self-Attention (`src/model/attention.py`)

- `CausalMultiHeadAttention(d_model: int, n_heads: int, dropout: float = 0.1)`.
- `forward(x: [B, T, d_model]) -> [B, T, d_model]`.
- `d_model % n_heads == 0`, `head_dim = d_model // n_heads` (16 untuk baseline); pelanggaran → `ValueError`.
- Urutan: proyeksi `W_q, W_k, W_v, W_o` (`Linear(d_model, d_model)`); reshape ke `[B, H, T, head_dim]`; skala `1/sqrt(head_dim)`; causal mask aditif (`-inf`) di segitiga atas sebelum softmax; gabung head; `W_o`; dropout pada skor sebelum softmax dan pada output attention.

### Decoder Block (`src/model/decoder_block.py`)

- `DecoderBlock(d_model: int, n_heads: int, d_ff: int, dropout: float = 0.1, layer_norm_eps: float = 1e-5, pre_norm: bool = True)`.
- `forward(x: [B, T, d_model]) -> [B, T, d_model]`.
- Pre-norm (baseline): `x = x + CausalMHA(LayerNorm(x))`; `x = x + FFN(LayerNorm(x))`.
- FFN: `Linear(d_model, d_ff)` → GELU → `Linear(d_ff, d_model)` → dropout. `d_ff = 4 * d_model = 256`.

### MiniGPT (`src/model/minigpt.py`)

- `MiniGPT(vocab_size: int, n_layers: int = 2, n_heads: int = 4, d_model: int = 64, context_length: int = 64, dropout: float = 0.1, layer_norm_eps: float = 1e-5)`.
- `forward(idx: [B, T] int64) -> logits: [B, T, vocab_size] float32`.
- Komposisi: `Embedding(V, d)` → + PE → `n_layers` × DecoderBlock → LayerNorm akhir → `Linear(d, V)` (bobot LM head tidak di-tie ke embedding pada baseline).
- `T > context_length` → `ValueError`.

### Training (`src/train.py`)

- Batch size 32; epochs 10 (awal); AdamW `lr=3e-4`, `weight_decay=0.01`; seed 42 (Python, NumPy, PyTorch).
- Tiap epoch: hitung train loss dan validation loss; catat ke `outputs/metrics/` (CSV/JSONL) dan laporkan di laporan akhir.

### Generation (`src/generate.py`)

- Versi pertama: **greedy decoding** (argmax tiap langkah; `temperature` sampling opsional, tidak wajib).
- `generate(prompt: str, max_new_tokens: int = 64) -> str`.
- Alur: lowercase → `encode` → prepend `bos_id` → loop; berhenti saat menghasilkan `eos_id` atau mencapai `max_new_tokens`; konteks dibatasi ke `context_length` terakhir (window geser) jika melebihi.

## 7. Kompleksitas dan memori

Dengan batch `B`, urutan `T`, dimensi `d`, head `H`:
- Attention: waktu `O(B * T^2 * d)`.
- Matriks attention: memori `O(B * H * T^2)`.
- FFN: waktu `O(B * T * d^2)` bila `d_ff` seorde dengan `d` (baseline `d_ff = 4d` tetap `O(d^2)`).

Contoh baseline (`B=32, T=64, d=64, H=4`): attention time ≈ 32·4096·64 ≈ 8,4M operasi per blok; matriks attention ≈ 32·4·4096 = 524.288 elemen (≈2 MiB fp32). Gunakan parameter aktual dan cantumkan asumsi pada laporan.

## 8. Data split

- Jangan pegang test split bawaan jika tersedia dan kualitasnya terverifikasi; jika tidak, fallback 80/10/10 seed 42.
- Split dilakukan per dokumen sebelum tokenisasi dan pembuatan window (mencegah kebocoran antarartikel).
- Strategi aktual (jumlah artikel per split, jumlah token, ukuran vocab) dicatat di `DATASET_CARD.md` pada langkah dataset.