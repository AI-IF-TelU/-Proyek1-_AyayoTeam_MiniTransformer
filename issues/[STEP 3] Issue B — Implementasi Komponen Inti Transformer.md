## 0. Pemilik tugas

- **Pemilik (rekomendasi):** Muhammad Raihan Fahrifi — Prompt Engineer & LLM Navigator.

## 1. Tujuan

Implementasi inti Transformer secara manual sesuai kontrak: Sinusoidal Positional Encoding, Causal Multi-Head Self-Attention, Decoder Block (Pre-LayerNorm), dan Feed-Forward Network GELU. Tanpa `nn.Transformer`, `nn.TransformerDecoder`, atau `nn.MultiheadAttention` sebagai pengganti komponen inti.

## 2. Konteks teknis dan file terkait

- `docs/TECH_SPEC.md` §2 (batas library), §6 (kontrak model), §7 (kompleksitas); `docs/ARCHITECTURE_DECISIONS.md` ADR-002, ADR-004, ADR-007.
- File target: `src/model/positional_encoding.py`, `src/model/attention.py`, `src/model/decoder_block.py` (susunan final dikonfirmasi koordinator 2026-10-19 — Opsi 1, tetap per kontrak TECH_SPEC §6).
- Konfigurasi baseline: `n_layers=2`, `n_heads=4`, `d_model=64`, `context_length=64`, `d_ff=256`, dropout `0.1`, LayerNorm epsilon `1e-5`.

## 3. Ruang lingkup

1. `SinCosPositionalEncoding(d_model, max_len)` — buffer `pe [max_len, d_model]` non-trainable; `forward` menambahkan `pe[:T]`; `T > max_len` → `ValueError`.
2. `CausalMultiHeadAttention(d_model, n_heads, dropout=0.1)` — proyeksi `W_q, W_k, W_v, W_o` (`Linear(d_model, d_model)`); reshape `[B, H, T, head_dim]`; skala `1/sqrt(head_dim)`; causal mask aditif `-inf` di segitiga atas sebelum softmax; gabung head; dropout pada skor dan output attention; validasi `d_model % n_heads == 0` (head_dim 16 untuk baseline).
3. `DecoderBlock(d_model, n_heads, d_ff, dropout=0.1, layer_norm_eps=1e-5, pre_norm=True)` — pre-norm: `x + CausalMHA(LayerNorm(x))`, lalu `x + FFN(LayerNorm(x))`; FFN: `Linear(d_model, d_ff)` → GELU → `Linear(d_ff, d_model)` → dropout; `d_ff = 4 * d_model = 256`.
4. Validasi input, penanganan edge cases, dokumentasi kompleksitas.
5. Unit test setiap komponen (bagian 8).

## 4. Di luar scope

- MiniGPT, training loop, checkpoint, dan generation (Issue C).
- Dataset/tokenizer (Issue A), integrasi tes (Issue D).
- Sampling generation (opsional v2, bukan baseline).
- Tie bobot LM head ke embedding (bukan baseline).

## 5. Dependensi

- Kontrak sudah dikunci final di `docs/TECH_SPEC.md` (Issue #1) — tidak menunggu Issue lain.
- Paralel penuh dengan Issue A.
- Issue C membutuhkan modul ini lulus tes untuk integrasi final; Issue D membutuhkannya untuk integrasi tes.

## 6. Interface dan kontrak (dari TECH_SPEC)

- `SinCosPositionalEncoding(d_model: int, max_len: int)`; `forward(x: [B, T, d_model]) -> [B, T, d_model]`; `T > max_len` → `ValueError`; `max_len = context_length = 64`.
- `CausalMultiHeadAttention(d_model: int, n_heads: int, dropout: float = 0.1)`; `forward(x: [B, T, d_model]) -> [B, T, d_model]`; pelanggaran `d_model % n_heads != 0` → `ValueError`.
- `DecoderBlock(d_model: int, n_heads: int, d_ff: int, dropout: float = 0.1, layer_norm_eps: float = 1e-5, pre_norm: bool = True)`; `forward(x: [B, T, d_model]) -> [B, T, d_model]`.
- Layout komposisi MiniGPT (diimplementasikan Issue C): `Embedding` → `+ PE` → `n_layers` × `DecoderBlock` → LayerNorm akhir → `Linear(d_model, vocab_size)`.
- Kompleksitas: attention waktu `O(B·T²·d)`, matriks attention memori `O(B·H·T²)`, FFN waktu `O(B·T·d²)`.

## 7. Task checklist berurutan

Kerjakan **satu subtask pada satu waktu**, dari atas ke bawah. Jangan menggabungkan beberapa komponen sekaligus; setiap komponen diuji dulu sebelum menjadi fondasi komponen berikutnya.

- [ ] **B1. Periksa kontrak tensor dan parameter pada `TECH_SPEC.md`.** Baca §2, §6, §7 dan ADR-002/004/007; catat seluruh nama kelas, parameter, tensor shapes, dan edge case. *Hasil:* ringkasan kontrak tertulis di laporan AI.
- [ ] **B2. Siapkan struktur file dan unit test komponen model.** Buat file target model + kerangka test (shape helper) sesuai kontrak. *Hasil:* struktur file + stub test siap.
- [ ] **B3. Implementasikan Sinusoidal Positional Encoding.** Buffer `pe [max_len, d_model]` non-trainable; `forward` menambah `pe[:T]`; `T > max_len` → `ValueError`. *Hasil:* `src/model/positional_encoding.py`.
- [ ] **B4. Uji bentuk tensor dan batas `max_len` PE.** Verifikasi shape output `[B, T, d_model]`, buffer non-trainable (`requires_grad=False`), pola sin/cos, `ValueError` saat `T > max_len`. *Hasil:* test PE lulus dengan output aktual.
- [ ] **B5. Implementasikan proyeksi Query, Key, dan Value.** `Linear(d_model, d_model)` untuk `W_q, W_k, W_v` (dan `W_o`), jalur `x -> Q/K/V`. *Hasil:* sub-komponen proyeksi teruji shape-nya.
- [ ] **B6. Implementasikan scaled dot-product attention.** Skor `QK^T / sqrt(head_dim)`, softmax, `@ V`; dropout pada skor (masking) sebelum softmax. *Hasil:* attention tunggal head berjalan, shape `[B, H, T, head_dim]`.
- [ ] **B7. Implementasikan causal mask dan uji dengan perubahan token masa depan.** Mask aditif `-inf` di segitiga atas sebelum softmax; buktikan invariance (ubah logit posisi masa depan tidak mengubah output posisi sebelumnya). *Hasil:* test causal mask lulus.
- [ ] **B8. Implementasikan pembagian head, penggabungan head, dan output projection.** Reshape `[B, T, d_model]` → `[B, H, T, head_dim]`, proses attention per head, gabung `[B, T, d_model]`, `W_o`. *Hasil:* multi-head terangkai.
- [ ] **B9. Uji Multi-Head Self-Attention.** `CausalMultiHeadAttention` utuh: shape output, perilaku dropout train vs eval, `ValueError` saat `d_model % n_heads != 0`. *Hasil:* test MHA lulus.
- [ ] **B10. Implementasikan FFN dengan GELU.** `Linear(d, d_ff)` → GELU → `Linear(d_ff, d)` → dropout; `d_ff = 4 * d_model = 256`. *Hasil:* FFN siap dipasang di DecoderBlock.
- [ ] **B11. Implementasikan Decoder Block dengan Pre-LayerNorm, residual connection, dan dropout.** Pre-norm: `x + CausalMHA(LayerNorm(x))`, `x + FFN(LayerNorm(x))`; epsilon `1e-5`. *Hasil:* `src/model/decoder_block.py`.
- [ ] **B12. Uji forward pass, backward pass, dan gradient.** Pastikan shape output `[B, T, d]`, forward+backward berjalan, gradien MHA/FFN/LayerNorm/reparam bukan `None`. *Hasil:* tes gradient lulus.
- [ ] **B13. Lakukan pengujian integrasi seluruh komponen.** PE → attention → DecoderBlock dijalankan sebagai satu alur bertingkat; verifikasi shape konsisten di tiap lapisan. *Hasil:* integrasi komponen inti lulus.
- [ ] **B14. Dokumentasikan kompleksitas dan trade-off algoritma.** Tuliskan kompleksitas waktu/memori (§7), edge cases, dan hasil tes di laporan eksperimen. *Hasil:* laporan lengkap tanpa klaim yang dikarang.

## 8. Instruksi pengerjaan setiap subtask

1. Baca kembali bagian spesifikasi yang relevan (`TECH_SPEC.md` §6–§7, ADR-002/004/007).
2. Minta AI menjelaskan tujuan subtask, rumus/enterpretasi tensor shapes `[B, T, d]`, kompleksitas `O(B·T²·d)` / `O(B·H·T²)`, dan edge cases SEBELUM menulis kode.
3. Implementasikan satu subtask saja (perubahan minimal, manual tanpa `nn.MultiheadAttention`/`nn.Transformer*`).
4. Jalankan test subtask itu dan amati output aktual.
5. Jika error, pahami dan perbaiki; catat bukti reproduksi error.
6. Simpan log AI (raw JSONL + laporan Markdown) sesuai ADR-006.
7. Minta review kepada koordinator/anggota lain sebelum menyatakan subtask selesai.
8. Centang checkbox subtask hanya setelah hasil dan test benar-benar terverifikasi.

## 9. Aturan berhenti

- Setelah satu subtask selesai dan diverifikasi, **berhenti**. Jangan mengerjakan subtask berikutnya tanpa instruksi eksplisit.
- Jangan membangun komponen selanjutnya sebelum komponen yang menjadi prasyaratnya lulus test.
- Jika hasil test gagal atau log AI belum tersimpan, **jangan lanjut**; perbaiki dulu.
- Jangan mengklaim test lulus jika belum dijalankan; jangan mengarang shape, gradien, atau hasil tes.

## 10. Acceptance criteria (wajib benar-benar diuji)

- [ ] Tidak ada `nn.Transformer`, `nn.TransformerDecoder`, atau `nn.MultiheadAttention` pada jalur inti.
- [ ] Tensor shapes output sesuai §6 untuk input acak (test shape dijalankan dan diamati).
- [ ] Causal mask terbukti mencegah posisi sebelumnya melihat token masa depan (test invariance: mengubah logit posisi masa depan tidak mengubah output posisi sebelumnya).
- [ ] Forward pass dan backward pass berjalan; gradient pada seluruh parameter bukan `None` setelah `loss.backward()`.
- [ ] `T > max_len` (PE) dan `d_model % n_heads != 0` (MHA) → `ValueError`.
- [ ] Kompleksitas algoritma didokumentasikan sesuai §7.
- [ ] Setiap subtask B1–B14 memiliki bukti berupa output aktual atau test yang dijalankan.

## 11. Unit test yang diperlukan

- PE: buffer non-trainable, pola sin/cos, `ValueError` saat `T > max_len`, shape output.
- MHA: shape output, invarian causal mask, validasi head dimension, dropout berperilaku berbeda train vs eval.
- DecoderBlock: shape output, jalur residual + pre-norm, dropout train vs eval, gradient mengalir di seluruh sub-komponen.

## 12. Aturan logging AI

- Ikuti `docs/AI_RULES.md` §6, `docs/AI_LOG_TEMPLATE.md`, dan ADR-006.
- Raw log di `docs/ai-logs/raw/<member-id>/`, laporan di `docs/ai-logs/reports/`; dilarang menulis API key, token, password, atau data sensitif.

## 13. Dokumentasi yang harus diperbarui

- Laporan AI di `docs/ai-logs/reports/` sesuai template.
- Catatan kompleksitas, edge cases, dan hasil tes di laporan eksperimen (mengikuti template, bukan mengubah `docs/TECH_SPEC.md`/`docs/ARCHITECTURE_DECISIONS.md` tanpa proses ADR).

## 14. Amendemen untuk eksperimen C15 (2026-10-24)

Konfigurasi pada butir 13 di atas adalah **baseline** ADR-004 dan tetap berlaku sebagai default. Eksperimen C15 memakai konfigurasi berbeda melalui ADR baru:

| Parameter | Baseline di issue ini | C15 | ADR |
|---|---|---|---|
| `n_layers` | 2 | **4** | ADR-014 |
| `context_length` | 64 | **128** | ADR-015 |
| `tie_embeddings` | tidak ada (LM head terpisah) | **True** (satu matriks `V x d` dipakai embedding dan LM head) | ADR-014 |
| `epochs` | 10 | **20** | ADR-016 |

Nilai `n_heads`, `d_model`, `d_ff`, dropout, epsilon LayerNorm, pre-LayerNorm, GELU, dan implementasi attention/PE manual tidak berubah. Signature `MiniGPT` bertambah satu parameter opsional `tie_embeddings: bool = False` sehingga pemanggil lama tidak terpengaruh.
