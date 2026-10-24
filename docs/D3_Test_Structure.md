# D3 — Struktur Unit Test

**Issue:** [STEP 3] Issue D — Unit Test, Integrasi & Dokumentasi Teknis
**Subtask:** D3 (artefak yang sebelumnya diklaim ada tetapi belum dibuat — F-D9-05)
**Tanggal:** 2026-10-24 (WIB, UTC+07:00)
**Anggota:** Rafa Suryaputra (rafasuryaputra-80048)

Dokumen ini menjelaskan susunan direktori `tests/`, tanggung jawab tiap berkas, dan cara
menjalankan subset per modul. Seluruh angka berasal dari koleksi aktual D14
(`pytest --collect-only -q --run-integration` → `190 tests collected`).

## 1. Prinsip penyusunan

1. **Satu berkas = satu kontrak atau satu modul.** Nama berkas menunjuk modul/ kontrak yang diuji
   sehingga kegagalan langsung menunjuk pemilik modul.
2. **Kontrak dari `docs/TECH_SPEC.md` §3–§6.** Setiap berkas kontrak menyebut bagian spesifikasi
   yang diuji pada docstring.
3. **Tes Issue D tidak menggantikan tes pemilik modul.** Tes A/B/C tetap dipertahankan; Issue D
   menambahkan tes lintas modul, tes kontrak yang belum tercakup, dan kontrol negatif.
4. **Tes integrasi dipisahkan dengan marker**, bukan dengan direktori berbeda, agar satu perintah
   dapat menjalankan seluruh suite (`--run-integration`).
5. **Helper bersama di `tests/helpers.py`**, bukan duplikasi di tiap berkas; helper yang dipakai
   lintas modul wajib punya tes sendiri (`test_helpers_contract.py`).

## 2. Berkas pendukung

| Berkas | Tanggung jawab |
|---|---|
| `tests/__init__.py` | Menjadikan `tests` paket agar `from tests.helpers import ...` bekerja |
| `tests/conftest.py` | Menambahkan root repo ke `sys.path`; opsi `--run-integration`; skip tes `integration` secara default; fixture `seed_everything` (autouse, seed 42), `base_config`, `batch`, `special_ids`, `tiny_corpus`, `tokenizer_cls`, `make_tokenizer`, `device` |
| `tests/helpers.py` | `BASE_CONFIG`, id special, `set_seed`, `make_batch` (arah kontrak §4), `make_tokenizer_corpus`, `make_tiny_corpus`, `assert_shape`, `assert_x_y_shift`, `assert_causal_mask`, `count_nonpad`, `assert_value_error`, `make_model` |
| `pytest.ini` | `testpaths`, pola nama, marker `contract`/`integration` (lihat `docs/D2_Testing_Framework.md`) |

Fixture `batch` memakai `make_batch(4, 64)`; sejak D14 helper itu membangun relasi kontrak
`x[i,t] == y[i,t-1]`, sehingga fixture aman dipakai tes baru.

## 3. Inventaris berkas tes (25 berkas, 190 tes)

### 3.1 Data pipeline & tokenizer (6 berkas, 36 tes)

| Berkas | Tes | Cakupan |
|---|---:|---|
| `test_tokenizer.py` | 11 | regex+lowercase, `<unk>`, special id, urutan frekuensi, tanpa leakage, `from_vocab` (D14) |
| `test_data_pipeline.py` | 17 | `TextDataset`, window 65/stride 1, relasi `x`/`y`, padding, dokumen pendek/kosong, no-window-crossing |
| `test_dataloader.py` | 2 | shape/padding batch |
| `test_sliding_window.py` | 3 | jumlah window, pasangan dokumen pendek, no-leak |
| `test_bos_eos.py` | 1 | `add_bos_eos` |
| `test_data_split.py` | 2 | split per dokumen, seed 42, tanpa irisan |

### 3.2 Komponen inti (6 berkas, 90 tes)

| Berkas | Tes | Cakupan |
|---|---:|---|
| `test_attention.py` | 28 | proyeksi QKV, skala, mask, dropout, gradien, validasi `n_heads` |
| `test_positional_encoding.py` | 16 | rumus sinusoidal, buffer non-trainable, guard `T > max_len`, gradien identitas |
| `test_decoder_block.py` | 18 | pre-norm, FFN/GELU, residual, dropout, gradien |
| `test_decoder_block_contract.py` | 13 | struktur baseline, tanpa guard konteks, tanpa buffer posisi |
| `test_causal_masking.py` | 8 | invariance per titik potong, probs masa depan nol, float64, skor besar |
| `test_integration_components.py` | 7 | PE→MHA→Block, gradien, modul terlarang (7 tes `integration`) |

### 3.3 MiniGPT, training, generation (10 berkas, 49 tes)

| Berkas | Tes | Cakupan |
|---|---:|---|
| `test_minigpt_contract.py` | 14 | komposisi, PE diterapkan, guard konteks, causality, gradien, validasi |
| `test_training_contract.py` | 18 | loss = CE logits step, pad diabaikan (kontrol), `lr=0`, state optimizer, seed 42 |
| `test_minigpt_logits.py` | 2 | shape/dtype logits, guard `T` |
| `test_minigpt_mock.py` | 2 | shape alur mock |
| `test_training_step.py` | 1 | satu step memperbarui parameter |
| `test_checkpoint.py` | 1 | roundtrip `state_dict`/`vocab`/`config` |
| `test_checkpoint_restore_contract.py` | 2 | restore → `generate` non-kosong; `vocab_size` hasil restore membangun MiniGPT (D14) |
| `test_generation_stop.py` | 2 | berhenti di `<eos>` dan `max_new_tokens` |
| `test_generate_context_contract.py` | 4 | default `context_length` mengikuti model; parameter eksplisit dihormati; fallback 64 (D14) |
| `test_metrics_jsonl_contract.py` | 3 | satu baris JSONL per epoch; tanpa `metrics_path` tidak menulis; overwrite bukan append (D14) |

### 3.4 Helper dan integrasi lintas modul (3 berkas, 15 tes)

| Berkas | Tes | Cakupan |
|---|---:|---|
| `test_helpers_contract.py` | 7 | arah shift `make_batch`, penolakan arah terbalik, `assert_x_y_shift` tidak menelan `AssertionError` (D14) |
| `test_end_to_end_pipeline.py` | 7 | tokenizer→dataset→model→loss→backward→step→generate (7 tes `integration`) |
| `test_train_integration.py` | 1 | `train()` satu epoch dengan komponen Issue A (1 tes `integration`) |

## 4. Menjalankan subset per modul

```powershell
# Modul A — data pipeline & tokenizer
python -m pytest tests/test_tokenizer.py tests/test_data_pipeline.py tests/test_dataloader.py `
  tests/test_sliding_window.py tests/test_bos_eos.py tests/test_data_split.py -q

# Modul B — komponen inti
python -m pytest tests/test_positional_encoding.py tests/test_attention.py `
  tests/test_causal_masking.py tests/test_decoder_block.py `
  tests/test_decoder_block_contract.py tests/test_integration_components.py -q --run-integration

# Modul C — MiniGPT/training/generation/checkpoint
python -m pytest tests/test_minigpt_logits.py tests/test_minigpt_mock.py `
  tests/test_minigpt_contract.py tests/test_training_step.py `
  tests/test_training_contract.py tests/test_checkpoint.py `
  tests/test_checkpoint_restore_contract.py tests/test_generation_stop.py `
  tests/test_generate_context_contract.py tests/test_metrics_jsonl_contract.py -q

# Helper bersama
python -m pytest tests/test_helpers_contract.py -q

# Integrasi lintas modul
python -m pytest tests/test_end_to_end_pipeline.py tests/test_train_integration.py -q --run-integration
```

Output aktual D14:

```text
Modul A : 36 passed
Modul B : 90 passed
Modul C : 49 passed
Helper  : 7 passed
Integrasi: 8 passed
Suite penuh: 190 passed; default: 175 passed, 15 skipped
```

## 5. Konvensi penamaan dan penambahan tes baru

1. Berkas: `test_<modul>_contract.py` untuk tes kontrak baru; `test_<topik>.py` untuk tes pemilik
   modul yang sudah ada (nama dipertahankan agar rujukan dokumen lama tetap valid).
2. Nama tes: `test_<perilaku yang diharapkan>`, bukan `test_<fungsi>_works`.
3. Setiap tes perilaku wajib disertai kontrol negatif bila memungkinkan (mis. `lr=0`,
   `eos_id=-1`, arah shift terbalik) agar asersi tidak vakum.
4. Tes yang membutuhkan korpus nyata memakai subset kecil (`data/processed/train.jsonl` 60 dokumen)
   dan gagal eksplisit bila berkas tidak ada.
5. Tes lintas modul diberi `pytestmark = pytest.mark.integration`.

## 6. Batasan

1. `tests/` tidak memiliki tes untuk signature `generate` terhadap `TECH_SPEC.md` §6 karena
   kontrak itu masih OPEN (F-D9-03) dan menunggu keputusan koordinator.
2. Tidak ada pengukuran coverage; jumlah tes bukan ukuran kelengkapan cakupan.
3. Tes korpus nyata bergantung pada keberadaan `data/processed/*.jsonl` di repo.
