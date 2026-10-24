# AI Log Report - Issue D (Subtask D6)

## Metadata
- Log ID: AI-LOG-rafasuryaputra-80048-IssueD-D6
- Tanggal/waktu: 2026-10-24 19:07–19:12 WIB (UTC+07:00)
- Anggota: Rafa Suryaputra (rafasuryaputra-80048)
- Agent/tool: Kilo (VS Code extension)
- Model (jika tersedia): aibebas/deepseek-v4-pro
- Session ID: ses_e9234b35cffeikhYNamMVvN3pV
- GitHub Issue/PR: [STEP 3] Issue D — Unit Test, Integrasi & Dokumentasi Teknis
- Target modul: `tests/test_decoder_block_contract.py`, `tests/test_minigpt_contract.py`, `tests/helpers.py`, `docs/TESTING.md`
- Raw log path: `docs/ai-logs/raw/rafasuryaputra-80048/ses_e9234b35cffeikhYNamMVvN3pV.jsonl` (aktif, 1,4 MB → 9,9 MB selama sesi)
- Share link: N/A
- Laporan otomatis sesi: `docs/ai-logs/reports/AI-LOG-rafasuryaputra-80048-ses_e9234b35cffeikhYNamMVvN3pV.md` (dibuat plugin; laporan manual ini tidak ditimpa)

## Kronologi prompt dan respons

| Waktu | Prompt (ringkas) | Respons AI (ringkas) | File terdampak | Keputusan anggota |
|---|---|---|---|---|
| 2026-10-24 19:03 | Verifikasi repo/branch/Git/logging, baca Issue D + AC + dependensi, jelaskan tujuan/algoritma/shapes/kompleksitas/edge cases/unit test, sebutkan file dan rencana; jangan coding; tunggu persetujuan | Verifikasi `master` in-sync (`0 0`), baca Issue D, TECH_SPEC §6, AI_RULES, ADR-007/008, dan tes milik Issue B/C. Baseline 22 tes model lulus. Laporkan gap kontrak (residual aditif, causality lintas block, PE aktif, LM head tied, guard `context_length` terkonfigurasi, gradien seluruh parameter) dan usulkan 20 tes baru (9 block + 11 MiniGPT) + perbaikan `helpers.make_model('minigpt')` | tidak ada (rencana) | Menyetujui rencana D6 |
| 2026-10-24 19:07 | Instruksi implementasi D6: implementasikan hanya subtask ini, jelaskan kode/algoritma, jalankan tes, tampilkan file berubah, pastikan logging, tanpa operasi Git, berhenti untuk review | Memperbaiki `helpers.make_model`, menulis 2 file tes baru (13 + 14 tes), menjalankan tes, 3 kegagalan awal dianalisis dan diperbaiki di sisi tes, menjalankan kontrol negatif mask, memperbarui `docs/TESTING.md`, membuat laporan manual ini | lihat daftar di atas | Menunggu review |

## Debugging

- Run pertama `python -m pytest tests/test_decoder_block_contract.py tests/test_minigpt_contract.py -v` → `3 failed, 24 passed in 10.34s`:
```
E  Mismatched elements: 28 / 64 (43.8%)
E  Greatest absolute difference: 2.384185791015625e-07 at index (41,)
```
  Diagnosis: `test_identical_positions_produce_identical_outputs` memakai `atol=0`; jumlah suku softmax bertambah dengan posisi sehingga penjumlahan `float32` menghasilkan galat ~1e-7. Bukan pelanggaran kontrak (nilai eksak secara matematis). Perbaikan: `atol=1e-6, rtol=1e-5`, selaras preseden D5.
```
E  Mismatched elements: 4096 / 4096 (100.0%)
E  Greatest absolute difference: 1.0000004768371582 at index (5, 34)
```
  Diagnosis: `test_perturbing_one_item_does_not_change_other_items` salah asersi — item batch 0 sengaja diubah tetapi diperiksa "tidak berubah". Perbaikan: item 0 harus berubah (`assertFalse(allclose)`), item 1 identik eksak.
```
E  KeyError: 'pe'
E  tests\test_minigpt_contract.py:93
```
  Diagnosis: buffer milik submodul sehingga nama terdaftar `pos_enc.pe`. Perbaikan: kunci `pos_enc.pe`.

- Perubahan yang dilakukan: hanya pada file tes baru dan `tests/helpers.py`. Tidak ada perubahan `src/`, kontrak, atau dependency.
- Hasil setelah perbaikan: `27 passed in 11.02s`.

## Verifikasi

- Perintah dan output aktual:
  1. `python -m pytest tests/test_decoder_block_contract.py tests/test_minigpt_contract.py -v` → `27 passed in 11.02s`.
  2. `python -m pytest tests/test_decoder_block.py tests/test_decoder_block_contract.py tests/test_causal_masking.py tests/test_minigpt_logits.py tests/test_minigpt_contract.py tests/test_minigpt_mock.py -q` → `57 passed in 10.66s`.
  3. `python -m pytest -q` → `144 passed in 16.26s` (baseline sebelum D6: 117 passed).
  4. `python -c "... make_model('minigpt') ..."` → `MiniGPT 2 256 torch.Size([100, 64])`.
  5. Kontrol negatif `%TEMP%\kilo\mutation_check.py`:
```
causal intact   -> block fails: False model fails: False
mask removed    -> block fails: True model fails: True
```
- Environment: Python 3.10.6, pytest 9.1.1, torch 2.14.1+cpu (`.venv`).
- Commit SHA: belum ada (operasi Git dilakukan anggota; agent tidak melakukan commit/push/staging).
- Acceptance criteria yang terpenuhi:
  - D6 checklist: tes kontrak Decoder Block dan MiniGPT (shape, residual/pre-norm, gradien, `ValueError T > context_length` hanya MiniGPT) tersedia dan lulus.
  - Issue D §10: tes memeriksa perilaku (invariance causal per titik potong, residual identitas eksak, PE aktif, LM head tidak di-tie, guard terkonfigurasi), bukan sekadar "tidak error"; kontrol negatif membuktikan tes tidak lolos palsu.
  - Hasil tes dicatat dari output aktual; tidak ada klaim yang belum dijalankan.
  - Tidak ada perubahan kontrak publik, `src/`, dependency, atau operasi Git.
- Acceptance criteria yang belum terpenuhi:
  - Review koordinator/anggota dan commit oleh anggota.
  - Penandaan checkbox D6 di `issues/`.
  - D7–D13 belum dikerjakan (di luar scope).

## Refleksi yang diverifikasi anggota
- Mengapa pendekatan dipilih: semua tes diletakkan di level `forward` publik agar membuktikan perilaku kontrak `TECH_SPEC.md` §6, bukan detail internal. Sifat kontraktual dipilih yang tidak bisa "lolos kebetulan": residual dibuktikan dengan menolkan parameter (`out == x` eksak, gradien identitas 1), causality dibuktikan per titik potong plus kontrol sensitivitas, dan PE dibuktikan lewat token identik yang menghasilkan logits berbeda.
- Pelajaran teknis: invariance causal bisa diuji eksak (`atol=0`) walaupun penskalaan/softmax ada, karena bobot masa depan tepat nol; sebaliknya kesamaan antarposisi dengan panjang softmax berbeda tetap terkena galat pembulatan `float32` sehingga butuh toleransi. Kontrol negatif (mematikan mask secara in-memory) layak dijalankan untuk memastikan tes invariance tidak vakum.
- Keterbatasan dan langkah selanjutnya: tes berjalan di CPU (torch CPU-only); tidak menguji `T=0` (di luar kontrak) maupun padding key-mask pada attention (TECH_SPEC §5 hanya menetapkan `ignore_index` pada loss, bukan mask padding). Rencana awal menyebut uji permutation equivariance untuk membuktikan FFN position-wise, tetapi sifat itu tidak berlaku pada attention causal (urutan posisi memengaruhi mask), sehingga diganti dengan kombinasi "tidak ada buffer posisi" + "input identik → output identik"; kebutuhan sejenis sudah dipenuhi `tests/test_decoder_block.py::test_input_gradient_not_none` dan tes D5. Model MiniGPT diuji dengan `vocab_size=100` dan `context_length` 8/64/128 agar guard terbukti tidak di-hardcode.
