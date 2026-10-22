# AI Interaction Log

> Laporan manual untuk sesi perbaikan bug BUG-1 & BUG-2 (Issue B). Diverifikasi terhadap raw JSONL otomatis. Laporan auto-generate per sesi (`AI-LOG-raihanfahrifi-80017-ses_e9cc2a202ffekysJr5lFEvV40F.md`) ditulis ulang plugin setiap event, sehingga bagian manual dicatat di sini agar tidak tertimpa.

## Metadata

- Log ID: `AI-LOG-raihanfahrifi-80017-BUGFIX-b1-b2`
- Tanggal/waktu: 2026-10-22 (UTC) — 17:52–18:09 WIB
- Anggota: raihanfahrifi-80017
- Agent/tool: Kilo
- Model (jika tersedia): 9router/deepseek_fahri
- Session ID: ses_e9cc2a202ffekysJr5lFEvV40F
- GitHub Issue/PR: Issue B — Perbaikan Bug Hasil Audit (BUG-1 & BUG-2)
- Target modul: `src/model/attention.py`, `src/model/positional_encoding.py`, `tests/test_attention.py`, `tests/test_positional_encoding.py`
- Raw log path: `docs/ai-logs/raw/raihanfahrifi-80017/ses_e9cc2a202ffekysJr5lFEvV40F.jsonl`
- Share link (jika tersedia): [Isi manual]

## Kronologi prompt dan respons

| # | Peran | Isi |
|---|---|---|
| 1 | Prompt | Issue B — Perbaikan Bug Hasil Audit (BUG-1 & BUG-2): verifikasi reproduksi dulu, jelaskan akar masalah/rencana fix/dampak kontrak/test baru, TUNGGU approval. |
| 2 | Respons | Baca `AGENTS.md`, `docs/PRD.md`, `TECH_SPEC.md`, `AI_RULES.md`, `DATASET_CARD.md`, `AI_LOG_TEMPLATE.md`, `ARCHITECTURE_DECISIONS.md`; baca `src/model/attention.py`, `src/model/positional_encoding.py`, test terkait. Jalankan 3 reproduksi. |
| 3 | Respons | Reproduksi terkonfirmasi: BUG-1 forward `nonfinite 7488/8192`, skor `nan 17`; BUG-2 `max diff 1.9883061647415161`. Baseline suite `Ran 60 tests ... OK`. Present akar masalah, Opsi A untuk BUG-1 + div_term per pasangan untuk BUG-2, dampak kontrak §6/§7, 5 test baru. Berhenti menunggu approval. |
| 4 | Prompt | `fixed!` (approval). |
| 5 | Respons | Cek file masih buggy → implementasi. Edit `attention.py`: dropout skor dipindah SEBELUM penambahan mask. Tambah 3 test di `test_attention.py`; `test_dropout_train_differs_from_eval` diberi assert finite. |
| 6 | Respons | Test attention gagal 1: assert `isfinite` pada sel `-inf` (salah test). Perbaiki ke `not isnan` + `isneginf`. `Ran 28 tests ... OK`. |
| 7 | Respons | Edit `positional_encoding.py`: `div_term = exp(arange(0,d,2) * (-log(10000)/d))`, sin/cos berbagi satu frekuensi. Perbaiki referensi `_expected_pe` ke rumus standar; tambah 2 test. Test PE gagal 1 karena `rtol=1e-6` terlalu ketat untuk float32 frekuensi kecil; pakai `rtol=1e-5`. `Ran 8 tests ... OK`. |
| 8 | Respons | Full suite `Ran 65 tests in 2.230s ... OK`. Reproduksi sesudah fix: nonfinite 0, NaN 0, max diff 0.0. |

## Debugging

- Pesan error aktual:
  - `AssertionError: tensor(False) is not true` di `test_masked_future_scores_never_nan` — test memakai `torch.isfinite(...).all()`, padahal sel segitiga atas memang `-inf` dan `-inf` bukan finite. Kesalahan test, bukan implementasi.
  - `AssertionError: Tensor-likes are not close!` di `test_even_odd_pair_share_frequency` — frekuensi terkecil float32 `0.0001` vs referensi double `0.0001333`, rel diff ~3e-5; `rtol=1e-6` terlalu ketat.
- Prompt debugging aktual: jalankan test tunggal dengan `-v` untuk traceback, lalu cek manual 224 sel segitiga atas = `-inf`.
- Perubahan yang dilakukan:
  - `tests/test_attention.py`: ganti assert `isfinite` → `not isnan` (assert `isneginf` dipertahankan).
  - `tests/test_positional_encoding.py`: `div_term` float32 dari `torch.exp`; `rtol` pasangan frekuensi `1e-5`.
- Hasil setelah perbaikan: attention `Ran 28 tests OK`; PE `Ran 8 tests OK`; full suite `Ran 65 tests OK`.

## Verifikasi

- Perintah test yang dijalankan dan output aktual:
  - Reproduksi BUG-1 model: sebelum `nonfinite: 7488 / 8192` → sesudah `nonfinite: 0 / 8192`.
  - Reproduksi BUG-1 skor: sebelum `nan in dropped scores: 17` → sesudah `nan in dropped scores: 0`.
  - Reproduksi BUG-2: sebelum `max diff vs standard: 1.9883061647415161` → sesudah `max diff vs standard: 0.0`.
  - `python -m unittest tests.test_attention` → `Ran 28 tests in 1.591s OK`.
  - `python -m unittest tests.test_positional_encoding` → `Ran 8 tests in 1.423s OK`.
  - `python -m unittest discover -s tests` → `Ran 65 tests in 2.230s OK` (60 lama + 5 baru).
- Commit SHA: [Isi manual — commit oleh anggota, bukan AI]
- Acceptance criteria yang terpenuhi:
  - [x] Train mode finite: output attention dropout 0.1 finite di beberapa seed.
  - [x] Causal invariance di train mode: output posisi `< T//2` identik saat input masa depan diubah (seed sama).
  - [x] Sel future `j>i` pasca dropout+mask = `-inf` eksak, bukan NaN.
  - [x] PE cocok rumus sinusoid standar (diff 0.0, atol 1e-6).
  - [x] Pasangan (2k, 2k+1) berbagi frekuensi sama.
  - [x] Tidak ada perubahan kontrak publik; shape `[B,T,d]`, `pe [max_len,d]`, mask `[1,1,T,T]` tetap; kompleksitas §7 tetap.
  - [x] `TECH_SPEC.md` dan `ARCHITECTURE_DECISIONS.md` tidak diubah.
- Acceptance criteria yang belum terpenuhi: n/a untuk perbaikan bug ini.

## Refleksi yang diverifikasi anggota

- Mengapa pendekatan dipilih: Opsi A (dropout skor sebelum mask) mempertahankan kontrak §6 harfiah — dropout tetap pada skor sebelum softmax, mask tetap `-inf` sebelum softmax — dan menjadikan posisi future selalu `-inf` eksak → probabilitas 0 eksak, invariance causal terjamin di train mode. Opsi B (dropout setelah softmax) mengubah semantik menjadi dropout probabilitas dan butuh keputusan koordinator; tidak dipilih.
- Pelajaran teknis: (1) `nn.Dropout` = `input * mask_bernoulli * 1/(1-p)`, sehingga `-inf * 0 = NaN`; mask `-inf` wajib ditambahkan SETELAH dropout. (2) `-inf` bukan finite — assert "tidak NaN" harus `not isnan`. (3) Rumus sinusoid standar memakai satu frekuensi `10000^(-2k/d)` untuk pasangan (2k, 2k+1); implementasi per-kolom lama memberi kolom cos frekuensi salah. (4) Membandingkan float32 vs referensi double pada frekuensi sangat kecil butuh toleransi relatif lebih longgar (`1e-5`).
- Keterbatasan dan langkah selanjutnya: 65/65 test hijau; sesi raw log otomatis terekam (13k+ baris). Berhenti sesuai aturan Issue, tunggu review anggota sebelum push. Operasi Git dilakukan anggota, bukan AI.
