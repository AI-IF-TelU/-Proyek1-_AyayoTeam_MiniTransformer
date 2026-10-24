# AI Log Report - Issue D (Subtask D7)

## Metadata
- Log ID: AI-LOG-rafasuryaputra-80048-IssueD-D7
- Tanggal/waktu: 2026-10-24 19:15–19:26 WIB (UTC+07:00)
- Anggota: Rafa Suryaputra (rafasuryaputra-80048)
- Agent/tool: Kilo (VS Code extension)
- Model (jika tersedia): aibebas/deepseek-v4-pro
- Session ID: ses_e9229499fffe5VbxECRcmoeNHI
- GitHub Issue/PR: [STEP 3] Issue D — Unit Test, Integrasi & Dokumentasi Teknis
- Target modul: `tests/test_training_contract.py` (baru), `docs/TESTING.md`
- Raw log path: `docs/ai-logs/raw/rafasuryaputra-80048/ses_e9229499fffe5VbxECRcmoeNHI.jsonl`
- Share link: N/A
- Laporan otomatis sesi: `docs/ai-logs/reports/AI-LOG-rafasuryaputra-80048-ses_e9229499fffe5VbxECRcmoeNHI.md` (dibuat plugin; laporan manual ini tidak ditimpa)

## Kronologi prompt dan respons

| Waktu | Prompt (ringkas) | Respons AI (ringkas) | File terdampak | Keputusan anggota |
|---|---|---|---|---|
| 2026-10-24 19:15 | Verifikasi repo/branch/Git/logging, baca Issue D + AC + dependensi, jelaskan tujuan/algoritma/shapes/kompleksitas/edge cases/unit test, sebutkan file dan rencana; jangan coding; tunggu persetujuan | Verifikasi `master` in-sync dengan `origin/master`, tidak ada perubahan staged/unstaged, satu file untracked laporan otomatis. Baseline `tests/test_training_step.py tests/test_train_integration.py` → `2 passed in 16.15s`. Temuan: `tests/test_training_step.py` sudah ada milik Issue C/C8 (commit `69af6e0`) dan hanya memeriksa loss finite + `lm_head` berubah. Usul `tests/test_training_contract.py` baru (10–11 tes) + dokumentasi | tidak ada (rencana) | Menyetujui rencana D7 |
| 2026-10-24 19:18 | Instruksi implementasi D7: implementasikan hanya subtask ini, jelaskan kode/algoritma, buat unit test, jalankan, tampilkan file berubah, pastikan logging, laporkan AC/kegagalan/keterbatasan, tanpa operasi Git, berhenti untuk review | Probe perilaku aktual (target all-pad → `nan`; `lr=0` → parameter identik), menulis 18 tes di `tests/test_training_contract.py`, 2 kegagalan awal dianalisis dan diperbaiki di sisi tes, menjalankan kontrol negatif `ignore_index`, memperbarui `docs/TESTING.md`, membuat laporan manual ini | `tests/test_training_contract.py`, `docs/TESTING.md` | Menunggu review |

## Debugging

- Probe awal (skrip di `%TEMP%\kilo\d7_probe.py`, di luar repo): `all-pad target loss: nan`, `lr=0 unchanged: True`. Dipakai untuk memastikan asumsi sebelum menulis tes, bukan diklaim sebagai hasil tes.

- Run pertama `python -m pytest tests/test_training_contract.py -v` → `2 failed, 16 passed in 16.68s`:
```
E  AssertionError: tensor(True) is not false
E  tests\test_training_contract.py:173
```
  Diagnosis: `test_perturbing_nonpad_row_logits_changes_loss` menambahkan `+100.0` ke seluruh kelas, yang merupakan pergeseran seragam; softmax invarian terhadap pergeseran seragam sehingga loss tidak berubah. Asersi pasangannya (baris pad) berisiko lolos palsu dengan alasan yang sama. Perbaikan: perturbasi diarahkan ke satu kelas (kelas target pad untuk baris pad, kelas non-target untuk baris non-pad) dan ditambahkan kontrol anti-vakum dengan `ignore_index=-100`.
```
E  AssertionError: 7 != 9
E  tests\test_training_contract.py:355
```
  Diagnosis: `test_context_length_guard_applies_and_keeps_parameters` memakai batch `T=6` lalu ditambah satu kolom menjadi `T=7`, belum melewati `context_length=8` sehingga `ValueError` tidak muncul. Perbaikan: batch guard dibuat eksplisit `T = context_length + 1 = 9`.

- Perubahan yang dilakukan: hanya pada file tes baru dan `docs/TESTING.md`. Tidak ada perubahan `src/`, kontrak publik, atau dependency.
- Hasil setelah perbaikan: `18 passed in 14.66s`.

## Verifikasi

- Perintah dan output aktual:
  1. `python -m pytest tests/test_training_contract.py -v` → `18 passed in 14.66s`.
  2. `python -m pytest tests/test_training_step.py tests/test_training_contract.py tests/test_train_integration.py tests/test_checkpoint.py -q` → `21 passed in 16.02s`.
  3. `python -m pytest -q` → `162 passed in 22.63s` (baseline sebelum D7: 144 passed).
  4. `python -m pytest -q --run-integration` → `162 passed in 20.96s`.
  5. Kontrol negatif `%TEMP%\kilo\d7_mutation_check.py`:
```
ignore_index=pad(0)    pad affects loss: False  pad grad zero: True
ignore_index=-100      pad affects loss: True   pad grad zero: False
```
- Environment: Python 3.10.6, pytest 9.1.1, torch 2.14.1+cpu (`.venv`), CPU-only.
- Commit SHA: belum ada (operasi Git dilakukan anggota; agent tidak melakukan commit/push/staging).
- Acceptance criteria yang terpenuhi:
  - D7 checklist: tes training step, loss, dan pembaruan parameter tersedia dan lulus (`loss` finite; bobot berubah setelah step; posisi pad diabaikan di loss, dibuktikan pada nilai loss dan gradien).
  - Issue D §10: tes memeriksa perilaku, bukan "tidak error" — loss dicocokkan dengan CE manual atas logits step itu, baris pad diperturbasi ekstrem tanpa mengubah loss, gradien pad tepat nol, dan kontrol negatif (`lr=0`, `ignore_index=-100`, seed berbeda) membuktikan tes tidak vakum.
  - Hasil tes dicatat dari output aktual; tidak ada klaim yang belum dijalankan.
  - Tidak ada perubahan kontrak publik, `src/`, dependency, atau operasi Git.
- Acceptance criteria yang belum terpenuhi:
  - Review koordinator/anggota dan commit oleh anggota.
  - Penandaan checkbox D7 di `issues/`.
  - D8–D13 belum dikerjakan (di luar scope).

## Refleksi yang diverifikasi anggota
- Mengapa pendekatan dipilih: tes diletakkan pada `training_step`/`make_criterion`/`make_optimizer` publik agar membuktikan kontrak `TECH_SPEC.md` §5–§6. File `tests/test_training_step.py` milik Issue C tidak diubah; D7 melengkapi dengan bukti kausal: forward hook menangkap logits step tersebut sehingga loss dapat dibandingkan dengan CE manual, dan `retain_grad()` dipakai untuk membuktikan gradien pad tepat nol.
- Pelajaran teknis: perturbasi logits harus asimetris antarkelas; pergeseran seragam seluruh kelas tidak mengubah softmax sehingga tes semacam itu lolos palsu (ini justru ditemukan dari kegagalan run pertama). Menambahkan kontrol anti-vakum (`ignore_index=-100`) membuat asersi "pad diabaikan" benar-benar bermakna.
- Keterbatasan dan langkah selanjutnya: (1) `training_step` tidak memiliki guard untuk target yang seluruhnya `pad_id`; `nn.CrossEntropyLoss(ignore_index=pad_id)` mengembalikan `nan` dan perilaku ini hanya dicatat sebagai keterbatasan, bukan kontrak. (2) Hanya loss yang memakai `ignore_index`; attention tidak memakai key-padding mask, sesuai `TECH_SPEC.md` §5 (di luar scope D7). (3) Semua tes berjalan di CPU; tidak ada uji mixed precision atau akumulasi gradien. (4) Reproduktibilitas diuji pada satu environment (torch 2.14.1+cpu, CPU); perilaku lintas perangkat/backend tidak dijamin. (5) `test_overfitting_one_batch_reduces_loss` bergantung pada seed tetap dan lr `1e-2`; nilainya deterministik di environment ini tetapi bukan jaminan konvergensi umum.
