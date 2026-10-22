# AI Interaction Log

> Laporan ini dihasilkan dari log otomatis dan diverifikasi terhadap raw JSONL. Jangan mengarang prompt, respons, hasil test, atau keputusan.

## Metadata

- Log ID: AI-LOG-raihanfahrifi-80017-B7-causal-mask
- Tanggal/waktu: 2026-10-22 (UTC)
- Anggota: raihanfahrifi-80017
- Agent/tool: Kilo
- Model (jika tersedia): 9router/deepseek_fahri
- Session ID: [isi session Kilo saat checkout ini]
- GitHub Issue/PR: Issue B — Implementasi Komponen Inti Transformer
- Target modul: `src/model/attention.py` (B7)
- Raw log path: `docs/ai-logs/raw/raihanfahrifi-80017/`
- Share link (jika tersedia): [Isi manual]

## Kronologi prompt dan respons

| # | Peran | Isi |
|---|---|---|
| 1 | Prompt | Instruksi subtask B7: implementasi causal mask dan uji invariance token masa depan; tunggu persetujuan sebelum coding. |
| 2 | Respons | Rencana B7: `_causal_mask` aditif `-inf` segitiga atas `[1, 1, T, T]`, broadcast dengan skor `[B, H, T, T]`; test invariance di level `_scaled_dot_product_attention`. |
| 3 | Prompt | Persetujuan rencana; lanjut implementasi. |
| 4 | Respons | Edits: `src/model/attention.py` (`_causal_mask`), `tests/test_attention.py` (test mask shape, upper-tri -inf, T=1, dtype, invariance, kontrol tanpa mask). |

## Debugging

- Pesan error aktual: tidak ada error.
- Prompt debugging aktual: tidak ada.
- Perubahan yang dilakukan: lihat kronologi 4.
- Hasil setelah perbaikan: tidak ada perbaikan yang diperlukan.

## Verifikasi

- Perintah test yang dijalankan: `python -m unittest tests.test_attention -v`
- Output aktual:
  - Ran 20 tests. OK (skipped=3), 17 passed, 0 failed (0.407s... ~1.4s).
  - B7 tests:
    - `test_causal_invariance_with_future_token_changes ... ok` (ubah q/k/v posisi `T//2:`, output posisi `:T//2` identik)
    - `test_invariance_fails_without_mask ... ok` (kontrol: tanpa mask, output past positions berubah → masklah penyebab invariance)
    - `test_mask_is_upper_triangular_negative_infinity ... ok`
    - `test_mask_shape ... ok`, `test_mask_t1_has_no_future ... ok`, `test_mask_respects_dtype_and_device ... ok`
  - skipped=3 adalah stub B2/B9 (`TestAttentionShape`, `TestAttentionValidation`, `TestDropoutBehavior`) yang dijalankan di B9.
  - Catatan: seluruh output di atas diamati pada terminal PowerShell (output aktual 20 baris `ok`/`skipped`).
- Build/test: OK — semua subtask terdahulu (B3–B6) tetap lulus bersama B7 (tidak ada regresi).
- Commit SHA: [Isi manual — commit dilakukan anggota]
- Acceptance criteria terpenuhi:
  - [x] Causal mask aditif `-inf` segitiga atas sebelum softmax (via `_scaled_dot_product_attention(mask=...)`).
  - [x] Test invariance: ubah token masa depan (q/k/v posisi ke depan) tidak mengubah output posisi sebelumnya.
  - [x] Tidak memakai `nn.Transformer`/`nn.TransformerDecoder`/`nn.MultiheadAttention`.
- Acceptance criteria yang belum terpenuhi: n/a untuk B7 (B8/B9 masih pending).

## Refleksi yang diverifikasi anggota

- Mengapa pendekatan dipilih: mask dibangun terpisah (`_causal_mask`) agar reusable di `forward` (B8) dan bisa diuji di level atomik sebelum MHA utuh. Broadcasting `[1, 1, T, T]` menjadikan mask bebas batch/head.
- Pelajaran teknis: invariance bukan milik relasi "input sama" melainkan struktur mask: posisi `i` hanya boleh melihat `j <= i`, sehingga perubahan vektor ke depan tidak menembus ke output belakang; tanpa mask, perubahan value posisi ke depan tetap mengubah output belakang (kontrol test gagal → test membuktikan penyebabnya mask).
- Keterbatasan dan langkah selanjutnya: mask belum dihubungkan ke `forward` (menunggu B8); `TestCausalInvariance` lama diganti level-mask karena `attn(x)` belum ada. Langkah berikut: B8 — pembagian/penggabungan head + output projection.