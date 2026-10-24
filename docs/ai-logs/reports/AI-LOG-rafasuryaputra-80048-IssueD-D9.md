# AI Log Report - Issue D (Subtask D9)

## Metadata
- Log ID: AI-LOG-rafasuryaputra-80048-IssueD-D9
- Tanggal/waktu: 2026-10-24 19:56–20:16 WIB (UTC+07:00)
- Anggota: Rafa Suryaputra (rafasuryaputra-80048)
- Agent/tool: Kilo (VS Code extension)
- Model (jika tersedia): aibebas/deepseek-v4-pro
- Session ID: ses_e9206a204ffe2zhFcZPLV8NwQJ
- GitHub Issue/PR: [STEP 3] Issue D — Unit Test, Integrasi & Dokumentasi Teknis
- Target modul: `docs/D9_FAILURE_LOG.md` (baru), `docs/TESTING.md` (bagian D9), laporan ini; eksekusi reproduksi di luar repo
- Raw log path: `docs/ai-logs/raw/rafasuryaputra-80048/ses_e9206a204ffe2zhFcZPLV8NwQJ.jsonl`
- Share link: N/A
- Laporan otomatis sesi: `docs/ai-logs/reports/AI-LOG-rafasuryaputra-80048-ses_e9206a204ffe2zhFcZPLV8NwQJ.md` (dibuat plugin; laporan manual ini tidak menimpanya)

## Kronologi prompt dan respons

| Waktu | Prompt (ringkas) | Respons AI (ringkas) | File terdampak | Keputusan anggota |
|---|---|---|---|---|
| 2026-10-24 19:53 | Prompt A (perencanaan D9): verifikasi repo/branch/Git/logging, baca Issue D + AC + dependensi, jelaskan tujuan/algoritma/shapes/kompleksitas/edge cases/unit test, sebutkan file dan rencana; tanpa kode; tanpa operasi Git; tunggu persetujuan | Verifikasi `master` @ `266c611`, satu file untracked (laporan otomatis), logger aktif (prompt tercatat sebagai entri #15). Baseline D8 dirujuk. Ditemukan `python` global tanpa pytest sehingga semua run harus lewat `.venv`. Usul rencana R1–R3 + verifikasi dokumentasi, tanpa menyentuh `src/`/tes. Usul file: `docs/D9_FAILURE_LOG.md`, `docs/TESTING.md`, laporan AI | tidak ada (rencana) | Menyetujui rencana D9 |
| 2026-10-24 20:00 | Instruksi implementasi D9: implementasikan hanya subtask ini, jelaskan kode/algoritma, buat/perbarui unit test, jalankan tes, tampilkan output aktual dan file berubah, pastikan logging, laporkan AC/kegagalan/keterbatasan, tanpa operasi Git, berhenti untuk review | Menjalankan baseline 5 run (162/162/31/90/41 semua PASS), lalu R1 (restore ala README), R2 + R2b (guard `context_length`), R3 (end-to-end `run_training.py` 1 epoch di `%TEMP%`), R3b (restore pada checkpoint nyata), verifikasi dokumentasi ADR-014 dan file D1–D3. Menulis `docs/D9_FAILURE_LOG.md`, bagian D9 di `docs/TESTING.md`, dan laporan ini | `docs/D9_FAILURE_LOG.md`, `docs/TESTING.md`, `docs/ai-logs/reports/AI-LOG-rafasuryaputra-80048-IssueD-D9.md` | Menunggu review |

## Debugging

- **Baseline:** tidak ada kegagalan; kelima run lulus pada percobaan pertama (lihat Verifikasi).
- **Pesan error aktual #1 (R2, defect proyek):**
  `ValueError: sequence length T=9 exceeds context_length=8`, dilempar dari `src/model/minigpt.py:77`
  lewat `src/generate.py:17`. Prompt 3 token + 6 token hasil generasi = konteks 9 melewati batas
  model; `generate` memakai `context_length=64` hardcode sehingga window tidak pernah menyusut ke 8.
- **Pesan error aktual #2 (defect proyek, silent):** tidak ada exception. `generate()` mengembalikan
  `''` karena `README.md:283-284` hanya mengisi `tok.token_to_id`; `id_to_token` tetap `{}` sehingga
  `Tokenizer.decode` (`src/data/tokenizer.py:44-47`) merender setiap id sebagai string kosong.
- **Pesan error aktual #3 (artefak skrip D9, bukan defect repo):**
  `json.decoder.JSONDecodeError: Unexpected UTF-8 BOM (decode using utf-8-sig): line 1 column 1 (char 0)`
  saat `run_training.py` membaca salinan data di `%TEMP%`. Penyebab: `Set-Content -Encoding UTF8`
  pada PowerShell 5.1 menulis BOM. Perubahan: salinan dibuat ulang dengan Python (`encoding="utf-8"`,
  tanpa BOM). Hasil setelah perbaikan: `run_training.py` berjalan sampai selesai
  (`train=6.5652 val=7.1810`, 265.2 s). Berkas `data/processed/*.jsonl` di repo tidak ber-BOM,
  sehingga hal ini tidak dilaporkan sebagai temuan.
- **Kesalahan skrip sendiri:** percobaan pertama R2b memakai `python -c` dengan definisi `class`
  inline → `SyntaxError`. Diperbaiki dengan menulis skrip ke `%TEMP%\kilo\d9\`.
- **Perubahan yang dilakukan:** hanya dokumentasi (`docs/D9_FAILURE_LOG.md` baru, bagian D9 di
  `docs/TESTING.md`, laporan ini). Tidak ada perubahan `src/`, `tests/`, `README.md`, `issues/`,
  `TECH_SPEC.md`, ADR, `pytest.ini`, atau dependency.

## Verifikasi

- Perintah dan output aktual (2026-10-24 19:58–20:11 WIB, `master` @ `266c611`, `.venv`):
  1. `.\.venv\Scripts\python.exe -m pytest -q` → `162 passed in 24.32s`
  2. `.\.venv\Scripts\python.exe -m pytest -q --run-integration` → `162 passed in 27.59s`
  3. Modul A (6 file, `-q`) → `31 passed in 12.74s`
  4. Modul B (6 file, `-q`) → `90 passed in 19.49s`
  5. Modul C (8 file, `-q`) → `41 passed in 21.76s`
  6. R1 `r1_restore.py` → `id_to_token size 0`, `vocab_size 0`, `decode('presiden indonesia' encoded) == ''`,
     `generate(...) == ''`, kontrol (id_to_token diisi) → `'presiden indonesia'` dan generate non-kosong,
     `MiniGPT(vocab_size=tok.vocab_size)` → `ValueError: vocab_size must be positive, got 0`
  7. R2 `r2_context_guard.py` → `ValueError: sequence length T=9 exceeds context_length=8`; kontrol
     `context_length=8` → `'5 6 7 7 7 5 5 5 5 5 5 5'` (10 token baru); `max_new_tokens=0` → `'5 6'`
  8. R2b `r2b_baseline_long_prompt.py` → model `context_length=64` + prompt 100 token → 105 token,
     tanpa exception (sliding window baseline bekerja)
  9. R3 `run_training.py --epochs 1 --max-epochs 1 --data-dir %TEMP%\kilo\d9\data --metrics-dir %TEMP%\kilo\d9\out`
     → `Articles: train=50, val=10`, `Vocab size: 3981`, `Segments: train=16637, val=3182`,
     `Model params: 609,664`, `Epoch 01/1 | train=6.5652 val=7.1810 (265.2s)`,
     checkpoint + metrics tertulis, `Generated: 'presiden indonesia . " kata dia . " kata dia ...'`
  10. R3b `r3b_real_checkpoint.py <ckpt>` → checkpoint nyata: `vocab entries 3981`,
      `id_to_token size 0`, `vocab_size 0`, `generate(...) == ''`
  11. Verifikasi statis: `ADR-014` tidak ada (ADR hanya 001–012, hanya `src/train.py:31` merujuk);
      `docs/D1_Acceptance_Criteria_Matrix.md` / `D2_Testing_Framework.md` / `D3_Test_Structure.md`
      → `False`; `Test-Path outputs` → `False`, `git ls-files outputs` kosong
- `git status --short` setelah seluruh kerja: hanya file `docs/` yang ditambahkan/diubah pada D9
  dan laporan otomatis sesi (untracked). Tidak ada perubahan `src/`, `tests/`, atau `data/`.
- Logging: raw `ses_e9206a204ffe2zhFcZPLV8NwQJ.jsonl` aktif dan memuat prompt perencanaan (entri #15)
  maupun prompt implementasi D9; laporan otomatis `AI-LOG-rafasuryaputra-80048-ses_e9206a204ffe2zhFcZPLV8NwQJ.md`
  ikut diperbarui.
- Environment: Python 3.10.6, pytest 9.1.1, torch 2.14.1+cpu, numpy 2.2.6, CPU-only.
- Commit SHA: belum ada (operasi Git dilakukan anggota; agent tidak melakukan commit/push/staging).
- Acceptance criteria yang terpenuhi:
  - D9 checklist: setiap kegagalan dicatat dengan traceback/error aktual dan langkah reproduksi;
    laporan ke pemilik modul disiapkan sebagai draft siap kirim di `docs/D9_FAILURE_LOG.md` §11.
  - Issue D §10: "Hasil tes dan error dicatat berdasarkan output aktual; tidak dikarang" —
    seluruh angka berasal dari output run yang tercatat; temuan yang belum direproduksi diberi label
    `statis` dan tidak dihitung sebagai kegagalan.
  - Tidak ada perubahan kontrak publik, `src/`, dependency, atau file tes.
- Acceptance criteria yang belum terpenuhi:
  - Perbaikan F-D9-01/02 dan tes regresinya (menunggu pemilik Issue C; verifikasi ulang di D10).
  - Keputusan koordinator untuk F-D9-03 (signature `generate`) dan F-D9-05 (matriks D1).
  - Review koordinator/anggota dan commit oleh anggota; checkbox D9 di `issues/` belum dicentang.
  - D10–D13 di luar scope.

## Refleksi yang diverifikasi anggota
- Mengapa pendekatan dipilih: D9 bukan penulisan fitur, melainkan pembuktian. Baseline dijalankan
  lebih dulu agar klaim "suite hijau" punya angka aktual, lalu defect dicari di jalur yang **tidak**
  dicakup suite (restore checkpoint, model non-baseline). Setiap temuan dipasangkan kontrol negatif
  supaya tidak berhenti pada "kelihatannya bug": F-D9-01 dikontrol dengan tokenizer yang
  `id_to_token`-nya diisi, F-D9-02 dikontrol dengan `context_length` eksplisit dan dengan R2b yang
  membuktikan sliding window baseline tetap benar.
- Pelajaran teknis: status hijau suite tidak membuktikan jalur pemakaian terdokumentasi berfungsi.
  Dua defect terpenting justru berada di persimpangan modul — README (dokumentasi) mengasumsikan
  tokenizer dapat dipulihkan dari `vocab`, sementara `Tokenizer` tidak menyediakan jalur itu dan
  `decode` gagal secara senyap. Kegagalan senyap (string kosong) lebih berbahaya daripada exception
  karena tidak meninggalkan jejak di log mana pun. Pelajaran kedua: `generate` yang lulus tes karena
  semua tes memakai `context_length=64` menyembunyikan konstanta yang salah; tes stub cenderung
  mewarisi asumsi implementasi, bukan kontrak.
- Keterbatasan dan langkah selanjutnya: (1) hasil CPU-only; (2) checkpoint C14 asli tidak tersedia
  sehingga R3 membuat checkpoint struktural setara (1 epoch, 50 artikel, vocab 3.981) dan R3 belum
  mencakup `data/processed/` penuh — kebutuhan D11; (3) akses volume Modal tidak dapat diverifikasi
  sehingga F-D9-06 hanya sampai tingkat "berkas tidak ada di repo"; (4) severity bersifat penilaian
  dampak karena proyek belum punya definisi severity; (5) D9 sengaja tidak menambah file tes —
  usulan tes regresi sudah tertulis di log kegagalan agar dapat dipakai pada D10.
