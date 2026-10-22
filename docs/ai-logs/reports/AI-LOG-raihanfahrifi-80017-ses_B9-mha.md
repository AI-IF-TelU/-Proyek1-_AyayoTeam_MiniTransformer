# AI Interaction Log

> Laporan ini dihasilkan dari log otomatis dan diverifikasi terhadap raw JSONL.

## Metadata

- Log ID: AI-LOG-raihanfahrifi-80017-B9-mha
- Tanggal/waktu: 2026-10-22 (UTC)
- Anggota: raihanfahrifi-80017
- Agent/tool: Kilo
- Model (jika tersedia): 9router/deepseek_fahri
- Session ID: [isi session Kilo saat checkout ini]
- GitHub Issue/PR: Issue B — Implementasi Komponen Inti Transformer
- Target modul: `tests/test_attention.py` (B9)
- Raw log path: `docs/ai-logs/raw/raihanfahrifi-80017/`
- Share link (jika tersedia): [Isi manual]

## Kronologi prompt dan respons

| # | Peran | Isi |
|---|---|---|
| 1 | Prompt | Subtask B9: uji Multi-Head Self-Attention utuh. Jelaskan rencana, tensor shapes, edge cases. |
| 2 | Respons | Rencana: hapus `@unittest.skip` di 3 kelas stub (TestAttentionShape, TestAttentionValidation, TestDropoutBehavior); tambah variasi shape, gradient end-to-end, `ValueError` n_heads=0 dan n_heads>d_model. |
| 3 | Prompt | Persetujuan rencana; lanjut implementasi. |
| 4 | Respons | Edits: `tests/test_attention.py` — unskip 3 kelas, tambah `test_output_shape_varied_batch_and_length`, `test_output_is_float32`, `test_gradient_flows_end_to_end` pada TestAttentionShape; tambah `test_value_error_when_zero_heads`, `test_value_error_when_more_heads_than_d_model` pada TestAttentionValidation. |
| 5 | Respons | **25 passed, 0 skipped, 0 failed** (pytest dan unittest). |

## Debugging

- Pesan error aktual: tidak ada error.
- Prompt debugging aktual: tidak ada.
- Perubahan yang dilakukan: lihat kronologi 4.
- Hasil setelah perbaikan: tidak ada perbaikan yang diperlukan.

## Verifikasi

- Perintah test yang dijalankan: `python -m pytest tests/test_attention.py -v` dan `python -m unittest tests.test_attention -v`
- Output aktual:
  - Ran 25 tests. OK (pytest: 5.35s, unittest: 1.51s).
  - B9 tests yang sebelumnya skipped kini lulus:
    - `TestAttentionShape::test_output_shape ... ok`
    - `TestAttentionShape::test_output_shape_varied_batch_and_length ... ok`
    - `TestAttentionShape::test_output_is_float32 ... ok`
    - `TestAttentionShape::test_gradient_flows_end_to_end ... ok`
    - `TestAttentionValidation::test_value_error_when_heads_do_not_divide ... ok`
    - `TestAttentionValidation::test_value_error_when_zero_heads ... ok`
    - `TestAttentionValidation::test_value_error_when_more_heads_than_d_model ... ok`
    - `TestDropoutBehavior::test_train_differs_from_eval ... ok`
  - Seluruh test B5–B8 tetap lulus (tidak ada regresi).
- Build/test: OK.
- Acceptance criteria yang terpenuhi:
  - [x] Shape output `[B, T, d_model]` diverifikasi pada B=2,T=8,d=64 dan variasi B=1,T=1 serta B=4,T=16.
  - [x] Dropout train vs eval: train dua panggilan berbeda, eval dua panggilan identik.
  - [x] `ValueError` saat `d_model % n_heads != 0` (n_heads=5, n_heads=0, n_heads>d_model).
  - [x] Gradient end-to-end mengalir: `w_q`, `w_k`, `w_v`, `w_o` weight.grad non-None, non-zero.
  - [x] Tidak memakai `nn.Transformer`/`nn.TransformerDecoder`/`nn.MultiheadAttention`.
- Acceptance criteria yang belum terpenuhi: n/a untuk B9.

## Refleksi yang diverifikasi anggota

- Mengapa pendekatan dipilih: menandai stub `@unittest.skip` adalah cara aman untuk me-reserve test slot di B2 tanpa gagal di CI sampai komponen siap; B9 adalah titik aman untuk "mematikan" skip karena `CausalMultiHeadAttention.forward` sudah lengkap (B8 selesai). Penambahan variasi shape (B=1,T=1 dan B=4,T=16) dan cek gradient end-to-end memperkuat coverage acceptance criteria §10.
- Pelajaran teknis: `requires_grad=True` pada input x tidak diperlukan untuk gradient param — cukup `out.sum().backward()` setelah forward, autograd mengalir ke parameter modul. `test_gradient_flows_end_to_end` membuktikan semua 4 bobot proyeksi menerima gradien.
- Keterbatasan dan langkah selanjutnya: B9 selesai. Langkah berikut: B10 — FFN dengan GELU (`decoder_block.py` sudah punya stub?), B11 — DecoderBlock, B12 — gradient DecoderBlock, B13 — integrasi, B14 — dokumentasi. Tunggu instruksi.