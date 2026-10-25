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
| Dataset | Indonesian News Datasets (kolom `content`); subset awal 1.000 artikel, C15 memakai 1.800 | ADR-003, ADR-012, ADR-015 |
| Split | Per dokumen; split bawaan train/test dipertahankan; validation 10% dari train (seed 42); fallback 80/10/10 tidak dipakai | ADR-010, ADR-012 |
| Objektif | Next-token prediction | ADR-001 |
| Loss | Cross-Entropy, token pad di target diabaikan (`ignore_index=pad_id`) | TECH_SPEC §5 |
| Optimizer | AdamW; awal `lr=3e-4`, `weight_decay=0.01` | TECH_SPEC §6 |
| Konfigurasi awal | `n_layers=2`, `n_heads=4`, `d_model=64`, `context_length=64`, `d_ff=256`; C15 memakai `n_layers=4`, `context_length=128`, weight tying aktif | ADR-004, ADR-014, ADR-015 |
| Seed | 42 (split data dan random seed) | ADR-010 |

Semua angka hiperparameter adalah titik awal yang boleh disesuaikan melalui eksperimen terdokumentasi, tanpa mengubah arsitektur inti.

## 2. Batas library

Dilarang menggunakan `nn.Transformer`, `nn.TransformerDecoder`, atau `nn.MultiheadAttention` untuk menggantikan inti implementasi manual. Operasi tensor dasar, `nn.Linear`, `nn.Embedding`, autograd, loss, optimizer, dan utilitas dasar PyTorch diizinkan. Tidak boleh memakai pretrained model atau external GPT API sebagai model proyek.

## 3. Kontrak tokenizer

File target: `src/data/tokenizer.py`.

- `fit(texts: Sequence[str], min_freq: int = 1) -> None` — bangun vocabulary **hanya dari data train**. Urutan id: `<pad>=0`, `<bos>=1`, `<eos>=2`, `<unk>=3`, lalu token hasil regex diurutkan berdasarkan frekuensi. `min_freq` adalah batas frekuensi minimum; default `1` berarti tanpa batas (perilaku baseline), `min_freq=2` membuang hapax (ADR-013).
- `encode(text: str) -> list[int]` — normalisasi lowercase, tokenisasi `re.findall(r"\w+|[^\w\s]", text)`, karakter/token di luar vocab → `<unk>`.
- `decode(ids: Sequence[int]) -> str` — gabung token kata/tanda baca dengan spasi, lalu `strip`; `bos/eos/pad/unk` tidak dirender (atau dirender sebagai spasi kosong). Roundtrip `decode(encode(t)) == t` tidak dijamin; ini perilaku yang didokumentasikan, bukan bug.
- Properti `vocab_size: int` tersedia setelah `fit`.

Perilaku token khusus: `<bos>` dan `<eos>` **tidak** dikirim sebagai string literal ke regex; keduanya disisipkan sebagai token id langsung pada tahap dataset (lihat §4).

## 3b. Catatan C15 untuk tokenizer (aditif)

Berlaku hanya untuk C15; kontrak §3 tidak berubah.

- Signature menjadi `fit(texts: Sequence[str], min_freq: int = 1) -> None`. Default `1` = perilaku baseline persis.
- `min_freq=2` pada C15 → vocab 16.278 (vs 27.648 bila `min_freq=1` pada korpus yang sama).
- Properti `min_freq` disimpan pada instance untuk reproduksibilitas.
- Pruning **tidak** menomori ulang token yang dipertahankan: id token yang lolos filter tetap sama dengan `min_freq=1`. Ini menjaga agar vocabulary checkpoint lama masih bisa dipetakan.

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
- `T > max_len` → `ValueError`. `max_len = context_length` (64 pada baseline, 128 pada C15 — ADR-015).

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

- `MiniGPT(vocab_size: int, n_layers: int = 2, n_heads: int = 4, d_model: int = 64, context_length: int = 64, dropout: float = 0.1, layer_norm_eps: float = 1e-5, tie_embeddings: bool = False)`.
- `forward(idx: [B, T] int64) -> logits: [B, T, vocab_size] float32`.
- Komposisi: `Embedding(V, d)` → + PE → `n_layers` × DecoderBlock → LayerNorm akhir → `Linear(d, V)`. Bobot LM head tidak di-tie pada baseline (`tie_embeddings=False`); C15 memakai `tie_embeddings=True` (ADR-014).
- `T > context_length` → `ValueError`.
- `MiniGPT.from_config(config: dict) -> MiniGPT` — membangun model dari dict `config["model"]` apa adanya, dengan menyaring kunci yang bukan parameter konstruktor (`d_ff` diturunkan sebagai `4 * d_model`; `min_freq` milik tokenizer). Gunakan ini saat memuat checkpoint; jangan menyaring manual, karena config C15 memuat `min_freq` yang membuat `MiniGPT(**config)` gagal dengan `TypeError`.

### Training (`src/train.py`)

- Batch size 32; epochs 10 (awal; C15 memakai 20 — ADR-016); AdamW `lr=3e-4`, `weight_decay=0.01`; seed 42 (Python, NumPy, PyTorch).
- Tiap epoch: hitung train loss dan validation loss; catat ke `outputs/metrics/` (format JSONL; ADR-011) dan laporkan di laporan akhir.
- **Evaluasi per dokumen (wajib untuk pelaporan).** `evaluate_per_document(model, doc_batches, pad_id=0, ignore_ids=())` mengagregasi loss per dokumen dari window non-overlap (`chunked_document_batches`), lalu melaporkan `mean ± 1.96 * sd / sqrt(n_dokumen)`.
  - Window stride-1 (ADR-010) tetap dipakai untuk *training* karena memaksimalkan data, tetapi **tidak boleh** dipakai untuk mengukur val/test: satu artikel menjadi ratusan baris sehingga loss terlihat jauh lebih pasti daripada buktinya.
  - `ignore_ids=(3,)` mengecualikan target `<unk>` sesuai ADR-013. Dokumen yang seluruh targetnya di-ignore dibuang dari sampel, bukan dihitung loss 0.
- **Seluruh artefak teks berformat JSONL** (satu objek JSON per baris): metrik per epoch, evaluasi akhir, generasi, konfigurasi, dan vocabulary.

### Generation (`src/generate.py`)

- Versi pertama: **greedy decoding** (argmax tiap langkah; `temperature` sampling opsional, tidak wajib).
- Signature aktual (7 parameter; F-D9-03 masih terbuka karena dokumen ini dulu menulis 2 parameter):

  ```python
  generate(model, tokenizer, prompt: str, max_new_tokens: int = 64,
           context_length: int | None = None, bos_id: int = 1, eos_id: int = 2) -> str
  ```

- `context_length=None` berarti memakai `model.context_length` (bukan hardcode 64); perilaku ini menutup F-D9-02.
- Alur: lowercase → `encode` → prepend `bos_id` → loop; berhenti saat menghasilkan `eos_id` atau mencapai `max_new_tokens`; konteks dibatasi ke `context_length` terakhir (window geser) jika melebihi.
- `generate_ids(...)` mengembalikan `Generation(ids, stopped_on_eos)` dan menerima `DecodeConfig` opsional:

  ```python
  @dataclass
  class DecodeConfig:
      do_sample: bool = False        # False = greedy (default, ADR-009)
      temperature: float = 1.0
      top_k: int = 0                 # 0 = nonaktif
      top_p: float = 1.0             # 1.0 = nonaktif
      repetition_penalty: float = 1.0
      no_repeat_ngram_size: int = 0  # 0 = nonaktif
      ban_unk: bool = True           # logits[<unk>] = -inf saat inference
      seed: int | None = None
      stop_on_eos: bool = True
  ```

  `DecodeConfig` hanya mengubah pemilihan token berikutnya; bobot model dan `Tokenizer.decode` tidak tersentuh.
- Teks untuk ditampilkan dirapikan `src/postprocess.py` (`detokenize`, `restore_case`, `trim_to_sentence`). `decode` tetap menggabung token dengan spasi sesuai §3.

## 6b. Catatan C15 (aditif, tidak menggantikan §6)

Bagian ini hanya berlaku untuk eksperimen C15 dan **tidak** mengubah §6 di atas:

- Shape batch menjadi `x, y: [B, 128]` (`context_length=128`, ADR-015). Aturan window §4 tetap sama bentuknya, hanya `T` berubah: dokumen ≥ 129 token → sliding window 129, stride 1, `x = ids[:128]`, `y = ids[1:129]`.
- Model `n_layers=4`, `tie_embeddings=True` (ADR-014). `d_model`, `n_heads`, `d_ff` tidak berubah.
- `Tokenizer.fit(texts, min_freq=2)` (ADR-013).
- Pelaporan loss memakai protokol per dokumen + CI 95% yang dijelaskan di §6, bukan loss per window.
- Token train C15: 567.989; val 71.188; test 77.330 (vocab 16.278).
- Restore checkpoint: `MiniGPT.from_config(ck["config"]["model"])`.

## 7. Kompleksitas dan memori

Dengan batch `B`, urutan `T`, dimensi `d`, head `H`:
- Attention: waktu `O(B * T^2 * d)`.
- Matriks attention: memori `O(B * H * T^2)`.
- FFN: waktu `O(B * T * d^2)` bila `d_ff` seorde dengan `d` (baseline `d_ff = 4d` tetap `O(d^2)`).

Contoh baseline (`B=32, T=64, d=64, H=4`): attention time ≈ 32·4096·64 ≈ 8,4M operasi per blok; matriks attention ≈ 32·4·4096 = 524.288 elemen (≈2 MiB fp32). Gunakan parameter aktual dan cantumkan asumsi pada laporan.

## 8. Data split

- Split bawaan dataset (train 25.8k / test 6.46k) dipertahankan tanpa resplit (ADR-010). Tidak ada split validation bawaan, sehingga validation diambil 10% dari split train (seed 42) — ADR-012. Fallback 80/10/10 tidak digunakan pada proyek ini.
- Jangan pegang test split bawaan jika tersedia dan kualitasnya terverifikasi; jika tidak, fallback 80/10/10 seed 42.
- Split dilakukan per dokumen sebelum tokenisasi dan pembuatan window (mencegah kebocoran antarartikel).
- Strategi aktual (jumlah artikel per split, jumlah token, ukuran vocab) dicatat di `DATASET_CARD.md` pada langkah dataset.