## 0. Pemilik tugas

- **Pemilik (rekomendasi):** Firdaus Akbar Amrullah — Training Loop Engineer.

## 1. Tujuan

Merakit MiniGPT (decoder-only) dari komponen inti, membangun training loop (Cross-Entropy + AdamW), checkpoint, pencatatan loss, dan text generation greedy. Kerangka boleh dibangun dengan mock model sesuai kontrak sambil menunggu komponen inti; integrasi final menunggu Issue B lulus.

## 2. Konteks teknis dan file terkait

- `docs/TECH_SPEC.md` §5 (loss), §6 (MiniGPT, Training, Generation), §7 (kompleksitas); `docs/ARCHITECTURE_DECISIONS.md` ADR-004, ADR-009.
- File target: `src/model/minigpt.py`, `src/train.py`, `src/generate.py` (dan `src/config.py` — format JSON).
- Konfigurasi: batch size 32, epochs 10, AdamW `lr=3e-4`, `weight_decay=0.01`, seed 42, `CrossEntropyLoss(ignore_index=pad_id)`.
- Output: metrics dan checkpoint ke `outputs/metrics/` (metrics format JSONL, ADR-011; checkpoint berisi state dict model + vocab + config).

## 3. Ruang lingkup

1. `MiniGPT` — `Embedding(vocab_size, d_model)` → `+ SinCosPositionalEncoding` → `n_layers` × `DecoderBlock` → LayerNorm akhir → `Linear(d_model, vocab_size)`. Output logits `[B, T, vocab_size] float32`. `T > context_length` → `ValueError`.
2. Training loop — seed 42, batch 32, AdamW, per-epoch train + validation loss, simpan ke `outputs/metrics/`.
3. Checkpoint — state dict model + vocabulary + konfigurasi; dapat dimuat ulang untuk generate.
4. Generation greedy — `generate(prompt, max_new_tokens=64)`: lowercase → `encode` → prepend `bos_id` → loop argmax → berhenti saat menghasilkan `eos_id` atau mencapai `max_new_tokens`; konteks dibatasi ke `context_length` terakhir (window geser).
5. Mock development: kerangka dan interface dapat diuji dengan model tiruan sesuai kontrak §6 sebelum Issue B tersedia.
6. Dokumentasi eksperimen dengan hasil aktual, tanpa mengarang keberhasilan atau kualitas generasi.

## 4. Di luar scope

- Implementasi komponen inti: PE, attention, decoder block (Issue B) — dipakai, bukan ditulis ulang.
- Prep data: tokenizer, dataset, loader (Issue A) — sebagai konsumen.
- Sampling temperature (opsional, bukan kewajiban v1).
- Pretrained weights atau external GPT API sebagai model proyek.

## 5. Dependensi

- Integrasi final logits dari komponen inti (Issue B) menunggu Issue B lulus tes.
- Konsumen tokenizer/loader dari Issue A untuk menjalankan training sungguhan.
- Kerangka + training interface boleh dibangun dan diuji dengan mock lebih awal (paralel dengan A/B).
- Hasil teste digunakan Issue D dan berkontribusi ke Issue E.

## 6. Interface dan kontrak (dari TECH_SPEC)

- `MiniGPT(vocab_size: int, n_layers: int = 2, n_heads: int = 4, d_model: int = 64, context_length: int = 64, dropout: float = 0.1, layer_norm_eps: float = 1e-5)`.
- `forward(idx: [B, T] int64) -> logits: [B, T, vocab_size] float32`; `T > context_length` → `ValueError`.
- Loss: `CrossEntropyLoss(ignore_index=pad_id)`; logits flat `[B*T, V]` vs target flat `[B*T]`; posisi pad tidak berkontribusi.
- Training: batch 32, epochs 10 awal, AdamW `lr=3e-4`, `weight_decay=0.01`, seed 42; tiap epoch catat train dan validation loss.
- `generate(prompt: str, max_new_tokens: int = 64) -> str` — greedy, berhenti di `eos_id` atau `max_new_tokens`.

## 7. Task checklist berurutan

Kerjakan **satu subtask pada satu waktu**, dari atas ke bawah. Kerangka dan mock boleh dikerjakan lebih awal, tetapi jangan mengklaim training nyata berhasil sebelum model dan dataset asli terintegrasi.

- [ ] **C1. Periksa kontrak model, dataset, dan training pada `TECH_SPEC.md`.** Baca §5–§7, ADR-004/009; catat antarmuka MiniGPT, loss, konfigurasi training, dan aturan generation. *Hasil:* ringkasan kontrak tertulis di laporan AI.
- [ ] **C2. Siapkan konfigurasi dan struktur modul.** Buat `src/config.py` (format JSON terpusat) dan kerangka `src/model/minigpt.py`, `src/train.py`, `src/generate.py`. *Hasil:* struktur modul + config siap.
- [ ] **C3. Buat kerangka MiniGPT yang sesuai interface.** Constructor + `forward` sesuai §6, komposisi Embedding → +PE → DecoderBlocks → LayerNorm → Linear, validasi `T > context_length`. *Hasil:* MiniGPT terdefinisi (boleh referensi modul yang belum ada via import kontrak).
- [ ] **C4. Uji alur model menggunakan mock jika komponen sebenarnya belum tersedia.** Gantikan PE/DecoderBlock dengan stub identitas penjaga shape; pastikan alur `[B, T] -> [B, T, V]` tak runtuh. *Hasil:* test alur mock lulus; jelaskan ini bukan integrasi final.
- [ ] **C5. Integrasikan token embedding, Positional Encoding, Decoder Block, dan output layer.** Sambungkan komponen asli Issue B (setelah tersedia/lulus) + `nn.Embedding(vocab_size, d_model)` + `Linear(d_model, vocab_size)`. *Hasil:* MiniGPT lengkap terangkai.
- [ ] **C6. Uji logits dengan bentuk `[B, T, vocab_size]` float32.** Input acak `[B, T] int64`; verifikasi dtype float32 dan `ValueError` saat `T > context_length`. *Hasil:* test shape logits lulus dengan output aktual.
- [ ] **C7. Siapkan fungsi loss dan satu training step.** `CrossEntropyLoss(ignore_index=pad_id)`, flat `[B*T, V]` vs `[B*T]`; satu langkah forward → loss → `backward()` → `optimizer.step()`. *Hasil:* satu step training berjalan.
- [ ] **C8. Pastikan parameter berubah setelah optimizer step.** Catat bobot before/after, cek selisih non-nol dan loss finite. *Hasil:* test parameter-update lulus.
- [ ] **C9. Implementasikan training loop dan validation loss.** Seed 42, batch 32, epochs 10 awal, AdamW `lr=3e-4`, `weight_decay=0.01`; hitung train + validation loss per epoch. *Hasil:* loop + loss per epoch tercatat.
- [ ] **C10. Implementasikan pencatatan metrik dan checkpoint.** Tulis metrics dan checkpoint ke `outputs/metrics/` (metrics format JSONL, ADR-011; checkpoint berisi state dict model + vocab + config, bisa dimuat ulang). *Hasil:* file metrics + checkpoint terverifikasi isinya.
- [ ] **C11. Integrasikan data loader nyata setelah Issue #2 siap.** Ganti data dummy dengan tokenizer/dataset/loader asli dari Issue A; verifikasi batch `[B, 64]` dan loss finite. *Hasil:* training memakai data asli.
- [ ] **C12. Implementasikan greedy text generation.** `generate(prompt, max_new_tokens=64)`: lowercase → encode → prepend `bos_id` → loop argmax → konteks window geser `context_length`. *Hasil:* output `str` terhasilkan dari model terlatih.
- [ ] **C13. Uji penghentian generation pada EOS dan batas token baru.** Verifikasi berhenti saat `eos_id` dihasilkan ATAU `max_new_tokens` tercapai; uji kedua jalur. *Hasil:* test stop-rule lulus.
- [ ] **C14. Jalankan eksperimen serta dokumentasikan hasil aktual.** Jalankan training nyata (sebagian/seluruh epoch), catat loss, contoh generate, durasi; tulis laporan tanpa klaim berlebihan. *Hasil:* laporan eksperimen lengkap.

## 8. Instruksi pengerjaan setiap subtask

1. Baca kembali bagian spesifikasi yang relevan (`TECH_SPEC.md` §5–§7, ADR-004/009).
2. Minta AI menjelaskan tujuan subtask, lewat mana tensor `[B, T, V]` terbentuk, kompleksitas, dan edge cases SEBELUM menulis kode.
3. Implementasikan satu subtask saja (perubahan minimal, mock hanya sebatas menunggu komponen asli).
4. Jalankan test subtask itu dan amati output aktual.
5. Jika error, pahami dan perbaiki; catat bukti reproduksi error.
6. Simpan log AI (raw JSONL + laporan Markdown) sesuai ADR-006.
7. Minta review kepada koordinator/anggota lain sebelum menyatakan subtask selesai.
8. Centang checkbox subtask hanya setelah hasil dan test benar-benar terverifikasi.

## 9. Aturan berhenti

- Setelah satu subtask selesai dan diverifikasi, **berhenti**. Jangan mengerjakan subtask berikutnya tanpa instruksi eksplisit.
- Jangan mengklaim training nyata berhasil sebelum model asli (Issue B) dan dataset asli (Issue A) terintegrasi di C5–C11.
- Jika hasil test gagal atau log AI belum tersimpan, **jangan lanjut**; perbaiki dulu.
- Jangan mengarang loss, checkpoint, contoh generate, atau klaim kualitas generasi.

## 10. Acceptance criteria (wajib benar-benar diuji)

- [ ] MiniGPT menghasilkan logits `[B, T, vocab_size]` float32 untuk input acak.
- [ ] Satu step training berjalan dan optimizer benar-benar memperbarui parameter (bobot sebelum/after berbeda, lengkungan finite).
- [ ] Train dan validation loss tercatat per epoch (file metrics terverifikasi isinya).
- [ ] Checkpoint berisi model + vocabulary + config dan berhasil dimuat ulang.
- [ ] Generation menggunakan model terlatih dan berhenti sesuai aturan (`eos_id` atau `max_new_tokens`).
- [ ] Hasil aktual (loss, contoh keluaran) dilaporkan tanpa klaim berlebihan.
- [ ] Setiap subtask C1–C14 memiliki bukti berupa output aktual atau test yang dijalankan.

## 11. Unit test yang diperlukan

- MiniGPT: shape logits, `ValueError` saat `T > context_length`.
- Training: loss finite, grad non-`None`, bobot berubah setelah step.
- Checkpoint: roundtrip simpan-muat identik (state dict).
- Loss: posisi pad tidak berkontribusi (bandingkan dengan mask manual).
- Generation: aturan stop, format output `str`.

## 12. Aturan logging AI

- Ikuti `docs/AI_RULES.md` §6, `docs/AI_LOG_TEMPLATE.md`, dan ADR-006.
- Smoke test logging personal (Issue E) WAJIB lolos sebelum coding dimulai.
- Raw log di `docs/ai-logs/raw/<member-id>/`, laporan di `docs/ai-logs/reports/`; dilarang menulis API key, token, password, atau data sensitif.

## 13. Dokumentasi yang harus diperbarui

- Laporan eksperimen (loss, contoh generate) di `docs/ai-logs/reports/` dan catatan hasil aktual.
- README — instruksi menjalankan training dan generate.
- Jangan mengubah `docs/TECH_SPEC.md`/`docs/ARCHITECTURE_DECISIONS.md` tanpa proses ADR.

## 14. Amendemen untuk eksperimen C15 (2026-10-24)

Angka pada butir 13, 44, dan 59 di atas adalah **baseline** (keputusan koordinator 19 Okt 2026) dan dibiarkan apa adanya sebagai catatan historis. Eksperimen C15 mengubahnya melalui ADR baru:

| Parameter | Baseline di issue ini | C15 | ADR |
|---|---|---|---|
| `epochs` | 10 | **20** | ADR-016 |
| `context_length` | 64 (implisit) | **128** | ADR-015 |
| `n_layers` | 2 | **4** | ADR-014 |
| Weight tying | tidak (LM head terpisah) | **ya** (`tie_embeddings=True`) | ADR-014 |
| Protokol `val_loss` | loss per window stride-1 | **loss per dokumen + CI 95%**, target `<unk>` dikecualikan | ADR-013 |

Yang tidak berubah: batch size 32, `lr=3e-4`, `weight_decay=0.01`, seed 42, `CrossEntropyLoss(ignore_index=pad_id)`, greedy decoding sebagai default, dan berhenti pada `<eos>` atau `max_new_tokens`.

Tambahan pada C15 (tidak mengubah kontrak penerimaan issue ini):

- `src/generate.py` menerima `DecodeConfig` opsional untuk `temperature`, `top_k`, `top_p`, `repetition_penalty`, `no_repeat_ngram_size`, dan `ban_unk`. `generate()` tanpa argumen tetap greedy murni sesuai ADR-009.
- `src/postprocess.py` menyediakan detokenisasi, kapitalisasi, dan pemotongan di batas kalimat untuk teks yang ditampilkan. `Tokenizer.decode` tidak diubah.
- Metrik kualitas generasi memakai `dup_4gram` (bukan trigram, yang dilarang `no_repeat_ngram_size=3`), `ends_at_sentence_pre_trim`, dan `verbatim_span_tokens`.

Catatan metodologis: C15 mengubah tying, `min_freq`, `context_length`, dan jumlah epoch dalam satu run, sehingga kontribusi masing-masing tidak dapat dipisahkan. Atribusi per-variabel memerlukan ablation terpisah.
