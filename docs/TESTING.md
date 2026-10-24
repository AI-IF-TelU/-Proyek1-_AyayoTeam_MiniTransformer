# Dokumentasi Pengujian (pytest)

## Ringkasan

Framework pengujian resmi proyek Mini-Transformer adalah **pytest**, ditetapkan oleh koordinator pada 2026-10-19 (Issue D, subtask D2). `pytest` sudah tercantum di `requirements.txt`, tidak diperlukan dependency baru.

## Konfigurasi

File `pytest.ini` di root repository:

- `testpaths = tests` — semua tes berada di folder `tests/`.
- `python_files = test_*.py` — pola nama file tes.
- `python_classes = Test*` — pola nama kelas tes (untuk gaya `unittest`).
- `python_functions = test_*` — pola nama fungsi tes (untuk gaya `pytest` murni).
- `addopts = -ra --strict-markers` — ringkasan tes yang dilewati/gagal, penolak penanda tak terdaftar.
- Marker terdaftar:
  - `contract`: tes berbasis kontrak dari `docs/TECH_SPEC.md`.
  - `integration`: tes lintas modul (memerlukan `--run-integration`).

Marker `integration` dilewati secara default oleh `conftest.py` kecuali menjalankan dengan opsi `--run-integration`.

## Perintah Pengeksekusian

### Seluruh suite (default, tanpa integrasi)

```powershell
python -m pytest -q
```

Hasil aktual (sesuai versi yang tersedia): **117 passed** setelah D5 (103 passed sebelum D5; torch 2.14.1+cpu via `.venv`).

### Subset per modul

Contoh tes tokenizer:

```powershell
python -m pytest tests/test_tokenizer.py -q
```

Contoh tes model:

```powershell
python -m pytest tests/test_positional_encoding.py tests/test_attention.py tests/test_decoder_block.py tests/test_minigpt_logits.py -q
```

### Tes integrasi (lintas modul)

```powershell
python -m pytest -q --run-integration
```

Tes integrasi menunggu modul dari Issues A, B, dan C tersedia. Jika modul belum tersedia, collection akan gagal dengan `ImportError` — bukan kegagalan tes.

## Hasil Verifikasi Aktual

Perintah `python -m pytest -q` dijalankan dan terlihat output: `103 passed in 17.55s` (durasi dapat bervariasi antarrun; run verifikasi lain mencatat 18.35s). Semua tes kontrak lulus pada environment yang tersedia. Hasil ini mencakup tes tokenizer, positional encoding, causal attention, decoder block, MiniGPT logits, training step, checkpoint roundtrip, generation stop, sliding window, dan data pipeline.

### Subtask D4 — Tes tokenizer dan data pipeline

Perintah:

```powershell
python -m pytest tests/test_tokenizer.py tests/test_data_pipeline.py tests/test_dataloader.py tests/test_sliding_window.py tests/test_bos_eos.py -v
```

Output aktual: `29 passed in 8.13s` (Python 3.10.6, pytest 9.1.1, torch 2.14.1+cpu; durasi dapat bervariasi antarrun).

Tes baru/penambahan pada D4:

- `test_tokenizer.py::TestTokenizerOrder::test_encode_preserves_text_order` — `encode` mengikuti urutan teks, bukan urutan vocab.
- `test_tokenizer.py::TestTokenizerOrder::test_vocab_size_equals_specials_plus_unique_train_tokens` — `vocab_size = 4 + token unik train`.
- `test_data_pipeline.py::test_sliding_window_exact_count_and_stride_one` — jumlah window `L - (T+1) + 1`, pergeseran stride 1, `x=ids[:T]`, `y=ids[1:T+1]`.
- `test_data_pipeline.py::test_no_cross_document_windows_for_long_documents` — setiap sample adalah suburutan kontigu satu dokumen (bos hanya di awal, eos hanya di akhir window).
- `test_data_pipeline.py::test_dataloader_padding_is_trailing_and_correct_dtype` — padding hanya di kanan, posisi pad `x`/`y` identik, dtype `int64`.
- `test_data_pipeline.py::test_decode_specials_only_returns_empty_string` — `decode` special-only/`[]` menghasilkan string kosong.
- `test_data_pipeline.py::test_fit_with_multiple_documents_counts_across_corpus` — frekuensi dihitung lintas dokumen korpus train.

Perbaikan asersi lemah: `test_lowercase_and_regex` sebelumnya memakai `assert ... or True` (selalu lolos) dan kini memeriksa bahwa `encode("a,b") == encode("a , b")`.

### Subtask D5 — Tes Positional Encoding dan causal masking

Perintah:

```powershell
python -m pytest tests/test_positional_encoding.py tests/test_causal_masking.py -v
```

Output aktual: `24 passed in 12.55s` (Python 3.10.6, pytest 9.1.1, torch 2.14.1+cpu).

Tes baru pada D5 (`tests/test_positional_encoding.py::TestPositionalEncodingContract`, 6 tes):

- `test_buffer_is_registered_and_not_trainable` — `named_parameters()` kosong dan `pe` terdaftar sebagai buffer non-trainable.
- `test_same_offset_for_every_batch_item` — `out[b] - x[b] == pe[:T]` untuk setiap item batch (offset posisi tidak tercampur antarbatch).
- `test_forward_does_not_mutate_input` — `forward` tidak mengubah tensor input.
- `test_gradient_is_identity` — gradien `d out / d x` bernilai 1 (PE tidak memblokir aliran gradien residual).
- `test_deterministic_in_train_and_eval` — keluaran identik pada `train()` dan `eval()`.
- `test_max_len_boundary_at_baseline` — `T = max_len = 64` lolos; `T = 65` melempar `ValueError`.

Tes baru pada `tests/test_causal_masking.py` (8 tes, diuji lewat `forward` publik, dropout 0 + `eval()`):

- `test_every_cut_leaves_past_unchanged` — untuk setiap titik potong `k`, mengubah `x[:, k:]` tidak mengubah `out[:, :k]`, sementara `out[:, k:]` berubah.
- `test_past_perturbation_changes_its_own_output` — kontrol sensitivitas: mengubah posisi 0 mengubah output posisi 0.
- `test_forward_matches_manual_reference` — keluaran `forward` sama dengan perhitungan manual (proyeksi → skala → mask → softmax → `@V` → `W_o`).
- `test_future_probability_is_exactly_zero` — `probs[..., j > i] == 0.0` eksak dan tiap baris berjumlah 1.
- `test_first_position_attends_only_to_itself` — posisi 0 hanya memberi bobot 1 ke dirinya sendiri.
- `test_single_position_has_no_future` — `T = 1`: output = `W_o(W_v(x))`, finite, tanpa NaN.
- `test_float64_input_keeps_dtype_and_causality` — model/input `float64` menghasilkan output `float64` dan invariance tetap berlaku.
- `test_large_scores_remain_finite` — input magnitudo `1e2` menghasilkan output finite dan probs tanpa NaN dengan baris berjumlah 1.

Catatan debugging aktual: run pertama D5 gagal pada `test_same_offset_for_every_batch_item` dengan `Greatest absolute difference: 1.103617250919342e-07` (2/512 elemen). Penyebab: pembulatan `float32` pada `(x + pe) - x`, bukan bug modul. Perbaikan: toleransi uji disamakan ke `atol=1e-6, rtol=1e-5` (setara toleransi yang dipakai tes pemilik modul). Setelah perbaikan: lulus.

Seluruh suite setelah D5:

```powershell
python -m pytest -q
```

Output aktual: `117 passed in 18.06s` (103 tes sebelum D5 + 14 tes baru).


## Catatan Teknis

- Tidak ada penambahan dependency baru (pytest sudah terdaftar di `requirements.txt`).
- Koleksi tes memerlukan PyTorch terpasang. Jika modul A/B/C belum tersedia, tes yang mengimpor modul tersebut akan gagal dengan `ImportError` saat koleksi — bukan kegagalan tes.
- Tes menggunakan giga campuran `unittest.TestCase` dan fungsi `pytest` murni; keduanya dijalankan oleh pytest secara bersamaan.
- File `tests/conftest.py` menambahkan root repo ke `sys.path`, menambahkan opsi `--run-integration`, dan menyediakan fixture `base_config`, `batch`, dan `special_ids`.
