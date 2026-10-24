# D2 — Keputusan Framework dan Runner Pengujian

**Issue:** [STEP 3] Issue D — Unit Test, Integrasi & Dokumentasi Teknis
**Subtask:** D2 (artefak yang sebelumnya diklaim ada tetapi belum dibuat — F-D9-05)
**Tanggal:** 2026-10-24 (WIB, UTC+07:00)
**Anggota:** Rafa Suryaputra (rafasuryaputra-80048)

Dokumen ini mencatat keputusan runner pengujian proyek beserta konsekuensinya. Isinya
mengonsolidasikan keputusan yang sudah dipakai sejak D4–D13; tidak ada keputusan baru yang
diambil di sini.

## 1. Keputusan

| Item | Keputusan | Dasar |
|---|---|---|
| Framework | **pytest** | Ditetapkan koordinator 2026-10-19 (Issue D §7 butir D2); sudah ada di `requirements.txt` |
| Dependency baru | **tidak ada** | `pytest` sudah terdaftar; torch/numpy sudah dipakai proyek |
| Lokasi tes | `tests/` | `pytest.ini`: `testpaths = tests` |
| Gaya tes | campuran `unittest.TestCase` dan fungsi pytest murni | Tes pemilik modul A/B/C memakai `unittest`; tes Issue D memakai fungsi pytest |
| Marker | `contract`, `integration` | `pytest.ini`; `--strict-markers` menolak marker tak terdaftar |
| Tes integrasi | dilewati default, dijalankan dengan `--run-integration` | `tests/conftest.py::pytest_collection_modifyitems` |
| Seed | 42 sebelum setiap tes | fixture autouse `seed_everything` di `tests/conftest.py` |

## 2. Konfigurasi aktual (`pytest.ini`)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -ra --strict-markers
markers =
    contract: contract-based tests from TECH_SPEC
    integration: cross-module integration tests
```

Konsekuensi `--strict-markers`: menambahkan marker baru tanpa mendaftarkannya di `pytest.ini`
membuat koleksi gagal. Ini disengaja agar penanda tidak menjadi dekorasi tanpa arti.

## 3. Peta perintah runner

| Tujuan | Perintah | Cakupan (D14) |
|---|---|---|
| Suite default (cepat) | `python -m pytest -q` | `175 passed, 15 skipped` |
| Suite penuh | `python -m pytest -q --run-integration` | `190 passed` |
| Hanya integrasi | `python -m pytest -q -m integration --run-integration` | 15 tes `integration` |
| Koleksi saja | `python -m pytest --collect-only -q --run-integration` | `190 tests collected` |
| Satu berkas | `python -m pytest tests/test_tokenizer.py -q` | per berkas |
| Subset modul | lihat `docs/D3_Test_Structure.md` §4 | per modul A/B/C |

Catatan environment: `python` global (Laragon 3.10) tidak memiliki pytest; perintah pada dokumen
proyek memakai `.\.venv\Scripts\python.exe` atau `python -m pytest` setelah venv aktif.

## 4. Mengapa pytest, bukan unittest murni atau framework lain

| Alternatif | Alasan tidak dipilih |
|---|---|
| `unittest` murni | Tidak punya fixture parametrik/marker/skip kondisional; `unittest discover` tidak bisa mengekspresikan "tes integrasi dilewati default" tanpa kode tambahan |
| `nose`/`nose2` | Tidak dirawat aktif; tidak ada di `requirements.txt`; menambah dependency baru |
| `tox` | Menambah dependency dan lapisan konfigurasi; proyek hanya punya satu environment (CPU, Python 3.10.6) |
| Framework baru (mis. `hypothesis`) | Tidak diperlukan untuk kontrak deterministik; menambah dependency tanpa persetujuan |

pytest tetap menjalankan kelas `unittest.TestCase` yang sudah ditulis pemilik modul, sehingga
integrasi tidak menuntut penulisan ulang tes A/B/C.

## 5. Perilaku skip dan bukti aktual

Tes ber-marker `integration` **tidak hilang** pada suite default: `conftest.py` menambahkan marker
`skip` sehingga tes tersebut muncul sebagai `skipped` dan ikut dihitung. Output D14:

```text
SKIPPED [7] tests\test_end_to_end_pipeline.py: integration tests require --run-integration
SKIPPED [7] tests\test_integration_components.py: integration tests require --run-integration
SKIPPED [1] tests\test_train_integration.py: integration tests require --run-integration
175 passed, 15 skipped in 37.04s
```

## 6. Batasan

1. Runner hanya diverifikasi pada Windows + PowerShell 5.1, Python 3.10.6, pytest 9.1.1,
   torch 2.14.1+cpu. Reproduksi di OS/versi lain belum diuji.
2. `--strict-markers` berarti berkas tes baru wajib memakai marker terdaftar; ini membatasi
   fleksibilitas penandaan.
3. Tidak ada pengukuran coverage (`pytest-cov` bukan dependency), sehingga "190 passed" tidak
   menyatakan persentase baris yang tercakup.
