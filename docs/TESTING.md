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

Hasil aktual (sesuai versi yang tersedia): **103 passed** (torch 2.14.1+cpu via `.venv`).

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


## Catatan Teknis

- Tidak ada penambahan dependency baru (pytest sudah terdaftar di `requirements.txt`).
- Koleksi tes memerlukan PyTorch terpasang. Jika modul A/B/C belum tersedia, tes yang mengimpor modul tersebut akan gagal dengan `ImportError` saat koleksi — bukan kegagalan tes.
- Tes menggunakan giga campuran `unittest.TestCase` dan fungsi `pytest` murni; keduanya dijalankan oleh pytest secara bersamaan.
- File `tests/conftest.py` menambahkan root repo ke `sys.path`, menambahkan opsi `--run-integration`, dan menyediakan fixture `base_config`, `batch`, dan `special_ids`.
