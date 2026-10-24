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

Hasil aktual (sesuai versi yang tersedia): **96 passed** (torch 2.14.1+cpu via `.venv`).

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

Perintah `python -m pytest -q` dijalankan dan terlihat output: `96 passed in 18.83s`. Semua tes kontrak lulus pada environment yang tersedia. Hasil ini mencakup tes tokenizer, positional encoding, causal attention, decoder block, MiniGPT logits, training step, checkpoint roundtrip, generation stop, sliding window, dan data pipeline.

## Catatan Teknis

- Tidak ada penambahan dependency baru (pytest sudah terdaftar di `requirements.txt`).
- Koleksi tes memerlukan PyTorch terpasang. Jika modul A/B/C belum tersedia, tes yang mengimpor modul tersebut akan gagal dengan `ImportError` saat koleksi — bukan kegagalan tes.
- Tes menggunakan giga campuran `unittest.TestCase` dan fungsi `pytest` murni; keduanya dijalankan oleh pytest secara bersamaan.
- File `tests/conftest.py` menambahkan root repo ke `sys.path`, menambahkan opsi `--run-integration`, dan menyediakan fixture `base_config`, `batch`, dan `special_ids`.
