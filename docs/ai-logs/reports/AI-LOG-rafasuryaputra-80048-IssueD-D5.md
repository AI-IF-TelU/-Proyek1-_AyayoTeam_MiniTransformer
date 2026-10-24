# AI Log Report - Issue D (Subtask D5)

## Metadata
- Log ID: AI-LOG-rafasuryaputra-80048-IssueD-D5
- Tanggal/waktu: 2026-10-24 19:05 WIB (UTC+07:00)
- Anggota: Rafa Suryaputra (rafasuryaputra-80048)
- Agent/tool: Kilo (VS Code extension)
- Model (jika tersedia): aibebas/deepseek-v4-pro
- Session ID: ses_e923ef3d0ffeKCEcA6vj357GGb
- GitHub Issue/PR: [STEP 3] Issue D — Unit Test, Integrasi & Dokumentasi Teknis
- Target modul: `tests/test_positional_encoding.py`, `tests/test_causal_masking.py`, `docs/TESTING.md`
- Raw log path: `docs/ai-logs/raw/rafasuryaputra-80048/ses_e923ef3d0ffeKCEcA6vj357GGb.jsonl`
- Share link: N/A
- Laporan otomatis sesi: `docs/ai-logs/reports/AI-LOG-rafasuryaputra-80048-ses_e923ef3d0ffeKCEcA6vj357GGb.md` (dibuat ulang otomatis oleh plugin; laporan ini adalah ringkasan manual yang tidak ditimpa)

## Kronologi prompt dan respons

| Waktu | Prompt (ringkas) | Respons AI (ringkas) | File terdampak | Keputusan anggota |
|---|---|---|---|---|
| 2026-10-24 18:52 | Verifikasi repo/branch/Git/logging, baca Issue D + AC + dependensi, jelaskan tujuan/algoritma/shapes/kompleksitas/edge cases/unit test, sebutkan file dan rencana; jangan coding; tunggu persetujuan | Verifikasi `master` (ahead/behind 0/0), baca Issue D, TECH_SPEC, AI_RULES, ADR, dan tes yang sudah ada milik Issue B; laporkan gap (PE/attention sudah teruji pada level helper, belum lewat `forward`) dan temuan bahwa `docs/D1_Acceptance_Criteria_Matrix.md` dkk. tidak ada di repo; usulkan 6 tes PE + 6 tes causal | tidak ada (rencana) | Menyetujui rencana D5 |
| 2026-10-24 18:56 | Instruksi implementasi D5: implementasi hanya subtask ini, jelaskan kode/algoritma, jalankan tes, tampilkan file berubah, pastikan logging, tanpa operasi Git | Menambah `TestPositionalEncodingContract` (6 tes), membuat `tests/test_causal_masking.py` (8 tes; 6 skenario rencana dipecah menjadi 8 kasus), memperbarui `docs/TESTING.md`, menjalankan tes, dan membuat laporan manual ini | `tests/test_positional_encoding.py`, `tests/test_causal_masking.py` (baru), `docs/TESTING.md`, laporan ini | Menunggu review |

## Debugging

- Pesan error aktual (run pertama `python -m pytest tests/test_positional_encoding.py tests/test_causal_masking.py -q`):
  ```
  ____ TestPositionalEncodingContract.test_same_offset_for_every_batch_item _____
  E  AssertionError: Tensor-likes are not close!
  E  Mismatched elements: 2 / 512 (0.4%)
  E  Greatest absolute difference: 1.103617250919342e-07 at index (3, 42) (up to 1e-07 allowed)
  E  Greatest relative difference: 1.55131801875541e-05 at index (3, 42) (up to 1e-07 allowed)
  1 failed, 23 passed in 11.61s
  ```
- Prompt debugging aktual: tidak ada prompt baru dari anggota; analisis dilakukan pada run yang sama.
- Perubahan yang dilakukan: toleransi `test_same_offset_for_every_batch_item` diubah dari `atol=1e-7, rtol=1e-7` menjadi `atol=1e-6, rtol=1e-5`.
- Diagnosis: selisih berasal dari pembulatan `float32` pada operasi `(x + pe) - x`; buffer PE dan modul tidak diubah karena bukan bug implementasi. Toleransi baru setara dengan yang dipakai tes pemilik modul (`test_even_odd_pair_share_frequency`).
- Hasil setelah perbaikan: `24 passed in 12.55s`.

## Verifikasi

- Perintah test yang dijalankan:
  1. `python -m pytest tests/test_positional_encoding.py tests/test_causal_masking.py -q` → `24 passed in 12.11s` (setelah perbaikan; run verbose mencatat `24 passed in 12.55s`).
  2. `python -m pytest tests/test_positional_encoding.py tests/test_causal_masking.py -v` → 24 item, semuanya `PASSED`.
  3. `python -m pytest -q` → `117 passed in 18.06s`.
  4. Baseline sebelum implementasi: `python -m pytest tests/test_positional_encoding.py tests/test_attention.py -q` → `38 passed in 12.38s`.
- Environment: Python 3.10.6, pytest 9.1.1, torch 2.14.1+cpu (`.venv`).
- Commit SHA: belum ada (operasi Git dilakukan anggota; atas instruksi, agent tidak melakukan commit).
- Acceptance criteria yang terpenuhi:
  - D5 checklist: tes kontrak PE (shape, buffer non-trainable, `ValueError T > max_len`) dan causal masking (invariance) tersedia dan lulus.
  - Issue D §10: test case memeriksa perilaku yang diharapkan (invariance per titik potong, probabilitas masa depan nol eksak, kesesuaian dengan referensi manual), bukan sekadar "tidak error".
  - Hasil tes dicatat dari output aktual.
  - Tidak ada perubahan kontrak publik, `src/`, dependency, atau operasi Git.
- Acceptance criteria yang belum terpenuhi:
  - Review koordinator/anggota dan commit oleh anggota.
  - Penandaan checkbox D5 di `issues/`.
  - D6–D13 belum dikerjakan (di luar scope).

## Refleksi yang diverifikasi anggota
- Mengapa pendekatan dipilih: tes diletakkan di level `forward` publik agar yang dibuktikan adalah perilaku modul sesuai TECH_SPEC §6, bukan detail helper internal. File causal masking dipisah agar tes pemilik Issue B tidak diubah. Rujukan manual dihitung dari parameter modul sendiri sehingga tidak bergantung pada library terlarang.
- Pelajaran teknis: membandingkan kembali hasil penjumlahan `float32` memerlukan toleransi yang sesuai skala; `assert_close` dengan toleransi 1e-7 absolut gagal pada nilai PE kecil. Nilai probabilitas masa depan dapat diuji eksak (`== 0.0`) karena `-inf` menghasilkan bobot nol setelah softmax.
- Keterbatasan dan langkah selanjutnya: tes berjalan di CPU (build torch CPU-only); `T = 0` tidak diuji karena tidak ada dalam kontrak; `docs/D1_Acceptance_Criteria_Matrix.md`, `docs/D2_Testing_Framework.md`, `docs/D3_Test_Structure.md` yang dirujuk laporan D1 tidak ada di repo sehingga matriks kontrak→test perlu dilengkapi sebelum D11–D13.
