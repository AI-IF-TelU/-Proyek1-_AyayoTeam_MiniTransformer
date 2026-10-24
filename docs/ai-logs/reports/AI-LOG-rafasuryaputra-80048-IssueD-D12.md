# AI Log — Issue D Subtask D12 (Dokumentasi Pengujian dan Hasil Eksperimen)

> Laporan ini disusun dari sesi yang direkam otomatis. Semua angka berasal dari output run yang
> tercantum; tidak ada prompt, hasil test, atau keputusan yang dikarang.

## Metadata

- **Log ID:** AI-LOG-rafasuryaputra-80048-IssueD-D12
- **Tanggal/waktu:** 2026-10-24 21:30–21:41 WIB (UTC+07:00)
- **Anggota:** Rafa Suryaputra — `rafasuryaputra-80048`
- **Agent/tool:** Assistant Vengentic (Kilo Code CLI), tools: shell (PowerShell), file read/write/edit
- **Model:** Assistant Vengentic
- **Session ID:** `ses_e91adee40ffeoHOZn0i0sHn6Pt`
- **GitHub Issue/PR:** [STEP 3] Issue D — Unit Test, Integrasi & Dokumentasi Teknis, subtask D12
- **Target modul:** `docs/` (dokumentasi pengujian), `README.md`
- **Raw log path:** `docs/ai-logs/raw/rafasuryaputra-80048/ses_e91adee40ffeoHOZn0i0sHn6Pt.jsonl`
- **Share link:** tidak tersedia (lokal)

## Kronologi prompt dan respons

| # | Waktu (WIB) | Jenis | Isi ringkas | File terdampak |
|---|---|---|---|---|
| 1 | 21:30 | Prompt anggota | `SUBTASK PLANNING` D12: verifikasi repo/branch/Git/logging, baca Issue + AC + dependensi, jelaskan tujuan/algoritma/shapes/kompleksitas/edge cases/unit test, sebutkan file yang akan diubah, jangan menulis kode, jangan operasi Git | — |
| 2 | 21:30–21:33 | Respons asisten | Verifikasi: `master` saja, HEAD `4dbe3a2`, hanya 1 laporan logger untracked, raw log aktif, `.venv` Python 3.10.6/pytest 9.1.1/torch 2.14.1+cpu, `169 tests collected`, `154 passed, 15 skipped`. Membaca Issue D §7 D12, `TECH_SPEC.md` §3–§7, `AI_RULES.md`, `TESTING.md`, `D9_FAILURE_LOG.md`, `D10_FIX_VERIFICATION.md`, laporan C14, `helpers.py`, `conftest.py`, `src/generate.py`, `src/data/tokenizer.py`, `src/data/dataset.py`, `src/train.py`, `src/model/minigpt.py`, `tests/test_end_to_end_pipeline.py`, AC Issues #2–#6. Rencana: `docs/D12_TESTING_REPORT.md` baru + pembaruan `docs/TESTING.md` + `README.md` §12 + laporan ini; tanpa menyentuh `src/`/`tests/` | tidak ada |
| 3 | 21:33 | Prompt anggota | `SUBTASK IMPLEMENTATION` D12: implementasikan rencana, jelaskan kode/algoritma, buat/perbarui tes, jalankan dan tampilkan output aktual, tampilkan file berubah, pastikan logging, laporkan AC/kegagalan/keterbatasan, tanpa operasi Git | — |
| 4 | 21:33–21:41 | Respons asisten | Menjalankan seluruh varian perintah pytest dan mencatat output aktual; menyusun `docs/D12_TESTING_REPORT.md` (10 bagian: runner, matriks kontrak §3–§7, matriks AC #2–#6, integrasi, riwayat debugging, arti suite hijau, eksperimen, keterbatasan, aturan pemeliharaan, daftar file); menambah bagian D12 di `docs/TESTING.md`; memperluas `README.md` §12; menulis laporan ini | `docs/D12_TESTING_REPORT.md`, `docs/TESTING.md`, `README.md`, laporan ini |

## Debugging

Tidak ada kegagalan pytest pada sesi D12: seluruh run berakhir `passed` tanpa `failed`/`error`.
Dua koreksi yang dilakukan bersifat dokumentasi, bukan perbaikan kode.

### Koreksi 1 — rujukan status yang basi di `docs/TESTING.md`

Teks lama pada bagian "Perintah Pengeksekusian" menyatakan status terbaru ada di bagian D8,
padahal D8 sudah digantikan D11/D12. Perubahan: rujukan diarahkan ke bagian D12 dan
`docs/D12_TESTING_REPORT.md` §1.3. Tidak ada angka historis yang diubah.

### Koreksi 2 — penajaman F-D11-01

D11 mencatat `helpers.make_batch` membangun `x[i,t] == y[i,t+1]`. Pemeriksaan D12 menunjukkan
`tests/helpers.py::assert_x_y_shift` juga mengodekan arah yang sama (`x[:, :-1] == y[:, 1:]`),
sehingga helper dan pemakaiannya konsisten satu sama lain tetapi keduanya berbeda dari
`TECH_SPEC.md` §4. Dampak tetap nol: `Select-String` atas `tests/*.py` menunjukkan fixture `batch`
(satu-satunya pemakai `make_batch`) tidak dipakai tes mana pun, dan `assert_x_y_shift` tidak
dipanggil. Tidak diubah pada D12 karena berada di luar scope dokumentasi.

### Catatan lingkungan

Output `Get-Content` di konsol PowerShell menampilkan karakter non-ASCII (mis. `—`, `→`) sebagai
mojibake karena codepage konsol; pembacaan ulang dengan editor UTF-8 menunjukkan isi file benar.
Berkas ditulis sebagai UTF-8 oleh tool file.

## Verifikasi

- **Perintah test yang dijalankan (semua pada `master @ 4dbe3a2`, `.venv`):**

```powershell
.\.venv\Scripts\python.exe -m pytest --collect-only -q --run-integration
.\.venv\Scripts\python.exe -m pytest --collect-only -q
.\.venv\Scripts\python.exe -m pytest --collect-only -q -m integration --run-integration
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest -q --run-integration
.\.venv\Scripts\python.exe -m pytest -q -m integration --run-integration
.\.venv\Scripts\python.exe -m pytest tests/test_tokenizer.py tests/test_data_pipeline.py tests/test_dataloader.py tests/test_sliding_window.py tests/test_bos_eos.py tests/test_data_split.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_positional_encoding.py tests/test_attention.py tests/test_causal_masking.py tests/test_decoder_block.py tests/test_decoder_block_contract.py tests/test_integration_components.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_positional_encoding.py tests/test_attention.py tests/test_causal_masking.py tests/test_decoder_block.py tests/test_decoder_block_contract.py tests/test_integration_components.py -q --run-integration
.\.venv\Scripts\python.exe -m pytest tests/test_minigpt_logits.py tests/test_minigpt_mock.py tests/test_minigpt_contract.py tests/test_training_step.py tests/test_training_contract.py tests/test_checkpoint.py tests/test_generation_stop.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_data_split.py -q
```

- **Output aktual:**

```text
169 tests collected in 10.33s
169 tests collected in 7.90s
15/169 tests collected (154 deselected) in 8.14s
154 passed, 15 skipped in 21.54s
169 passed in 22.67s
15 passed, 154 deselected in 16.48s
31 passed in 9.44s
83 passed, 7 skipped in 15.68s
90 passed in 15.42s
40 passed in 15.26s
2 passed in 9.60s
```

- **Commit SHA:** `4dbe3a2` (`feat(Issue D): Substask D11`), branch `master`, tanpa operasi Git.
- **Acceptance criteria yang terpenuhi (D12):**
  - Perintah runner terdokumentasi lengkap dengan output aktual untuk suite default, suite penuh,
    mode integrasi, dan per modul (`docs/D12_TESTING_REPORT.md` §1.2–§1.3).
  - Matriks kontrak→test→status tersedia untuk `TECH_SPEC.md` §3–§7 dengan nama tes yang
    benar-benar ada di koleksi (§2), melengkapi deliverable D1 yang artefaknya tidak pernah ada
    (F-D9-05).
  - Matriks acceptance criteria Issues #2–#6 → bukti → status tersedia (§3).
  - Hasil integrasi lintas modul terdokumentasi (§4) dan konsisten dengan angka run.
  - Riwayat debugging D4–D11 terdokumentasi dengan penyebab dan perbaikan (§5), termasuk kontrol
    negatif.
  - Hasil eksperimen C14 diringkas dengan sumber eksplisit dan batas klaim (§7).
  - Temuan terbuka dinyatakan eksplisit sehingga "suite hijau" tidak dibaca sebagai "semua
    kontrak tertutup" (§6).
  - `README.md` memuat instruksi menjalankan seluruh tes beserta tautan dokumentasi.
  - Tidak ada perubahan `src/`, `tests/`, `pytest.ini`, `requirements.txt`, atau kontrak publik.
- **Acceptance criteria yang belum terpenuhi (D12):**
  - Seluruh temuan F-D9-01…F-D9-06 dan F-D11-01 masih `OPEN`; penutupannya memerlukan perbaikan
    pemilik modul (Issue A/C) dan keputusan koordinator (F-D9-03). D12 hanya mendokumentasikan.
  - D12 tidak memverifikasi bukti per subtask A1–A13/B1–B14/C1–C14 maupun validasi logging
    Issue E; keduanya berada di luar scope substask ini.

## Refleksi yang diverifikasi anggota

- **Mengapa pendekatan dipilih:** D12 meminta "rangkum perintah runner, matriks kontrak→test,
  hasil integrasi, dan riwayat debugging di `docs/` serta README". Sebelumnya informasi itu
  tersebar di `TESTING.md` (per subtask), `D9_FAILURE_LOG.md`, `D10_FIX_VERIFICATION.md`, dan
  laporan C14, sehingga pembaca tidak punya satu tempat untuk menjawab "kontrak mana yang sudah
  terbukti, dengan tes apa". Satu dokumen konsolidasi + tautan dari README memberi jalur baca
  tunggal tanpa menghapus riwayat.
- **Pelajaran teknis:** (1) Status "169 passed" hanya bermakna bila dipasangkan dengan gap
  cakupan; tiga temuan D9 muncul justru pada jalur yang tidak diuji, bukan pada tes yang gagal.
  (2) Matriks harus memakai nama tes dari `--collect-only`, bukan nama yang diingat — beberapa
  nama kelas (`TestPositionalEncodingContract`) tidak akan tertebak. (3) Rekonsiliasi jumlah
  (31 + 90 + 40 + 1 + 7 = 169; 169 − 15 = 154) adalah pemeriksaan murah yang menangkap
  ketidakkonsistenan dokumentasi.
- **Keterbatasan dan langkah selanjutnya:** CPU-only; tidak ada pengukuran kompleksitas empiris;
  angka eksperimen dikutip, bukan dijalankan ulang; artefak `outputs/` tidak ada di repo. Langkah
  selanjutnya adalah D13 (laporan akhir berbasis bukti) dengan syarat keputusan koordinator untuk
  F-D9-03 dan perbaikan Issue C untuk F-D9-01/F-D9-02 agar klaim penutupan temuan memiliki bukti
  tes yang lulus.
