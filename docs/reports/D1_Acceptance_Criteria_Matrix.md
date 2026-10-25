# D1 — Matriks Acceptance Criteria → Test → Status

**Issue:** [STEP 3] Issue D — Unit Test, Integrasi & Dokumentasi Teknis
**Subtask:** D1 (artefak yang sebelumnya diklaim ada tetapi belum dibuat — F-D9-05)
**Commit saat eksekusi:** `cd757da` + perubahan D14 (lihat `git status`)
**Tanggal eksekusi:** 2026-10-24 (WIB, UTC+07:00)
**Anggota:** Rafa Suryaputra (rafasuryaputra-80048)

Dokumen ini adalah matriks **kontrak → test → status** untuk acceptance criteria Issues #2–#6.
Isi awalnya dikonsolidasikan dari `docs/D12_TESTING_REPORT.md` §2–§3 dan diverifikasi ulang pada
D14: setiap nama node tes di bawah ada di koleksi aktual (`pytest --collect-only -q
--run-integration` → `190 tests collected`) dan seluruh suite lulus pada run D14
(`190 passed` dengan `--run-integration`, `175 passed, 15 skipped` tanpa opsi itu).

Status yang dipakai:

| Status | Arti |
|---|---|
| **PASS** | Ada tes yang dijalankan pada D14 dan lulus; perilaku kontrak terbukti |
| **PASS (kontrol)** | Lulus, dan disertai kontrol negatif sehingga bukan asersi vakum |
| **DOKUMEN** | Dibuktikan oleh dokumen/artefak, bukan tes otomatis |
| **DI LUAR KENDALI D** | Bukti milik pemilik modul lain; tidak diperiksa ulang di sini |
| **GAP** | Kontrak ada tetapi tidak dicakup tes |
| **OPEN** | Dicakup/dilaporkan, tetapi implementasi masih menyimpang dari kontrak |

Kolom **Sumber** menandai asal tes: `A`/`B`/`C` = tes milik pemilik modul, `D` = tes Issue D
(D4–D7, D11), `D14` = tes regresi yang ditambahkan untuk menutup temuan.

---

## 1. Issue #2 (A) — Data Pipeline & Tokenizer

| # | Acceptance criterion | Bukti test | Sumber | Status |
|---:|---|---|---|---|
| 1 | `fit`/`encode`/`decode`/`vocab_size` sesuai `TECH_SPEC.md` §3 | `test_data_pipeline.py::test_special_token_ids_and_order`, `::test_lowercase_and_regex`, `::test_unknown_fallback`, `::test_decode_skips_specials`, `test_tokenizer.py` (11 tes) | A/D | PASS |
| 2 | Urutan id special `<pad>=0`, `<bos>=1`, `<eos>=2`, `<unk>=3` | `test_data_pipeline.py::test_special_token_ids_and_order`, `test_tokenizer.py::TestTokenizerFromVocab::test_from_vocab_keeps_special_token_ids` | A/D14 | PASS |
| 3 | Urutan id berdasarkan frekuensi, tie-break deterministik | `test_data_pipeline.py::test_frequency_ordering_with_tiebreak`, `::test_fit_with_multiple_documents_counts_across_corpus` | A | PASS |
| 4 | Tidak ada vocabulary leakage train→val/test | `test_tokenizer.py::TestTokenizerLeakage::test_no_vocab_leakage`, `test_data_split.py::test_splits_and_leakage` | A | PASS (kontrol) |
| 5 | Relasi `x[i,t] == y[i,t-1]` pada posisi non-pad | `test_data_pipeline.py::test_dataset_xy_relation_and_padding`, `test_helpers_contract.py::test_make_batch_follows_contract_direction`, `::test_assert_x_y_shift_rejects_broken_shift`, `::test_make_batch_matches_real_dataset_direction` | A/D14 | PASS (kontrol) |
| 6 | Tidak ada window lintas batas dokumen | `test_data_pipeline.py::test_no_cross_document_windows`, `::test_no_cross_document_windows_for_long_documents`, `test_sliding_window.py::test_no_cross_document_leak`, `test_end_to_end_pipeline.py::test_real_corpus_windows_and_forward` | A/D | PASS |
| 7 | Batch `x`/`y` `[B, 64]` int64 dengan padding trailing `pad_id` | `test_dataloader.py` (2), `test_data_pipeline.py::test_dataloader_batch_shape`, `::test_dataloader_padding_is_trailing_and_correct_dtype` | A | PASS |
| 8 | Dokumen kosong dibuang; dokumen 1 token tanpa pasangan | `test_data_pipeline.py::test_empty_and_short_docs_skipped`, `test_sliding_window.py::test_empty_and_short_docs` | A | PASS |
| 9 | `DATASET_CARD.md` berisi angka yang diverifikasi | `docs/DATASET_CARD.md`; diukur ulang D13 §1.6 (720/80/200 artikel; 290.920/33.157/77.330 token; vocab 19.192) | D | DOKUMEN |
| 10 | Setiap subtask A1–A13 punya bukti | laporan AI Issue A di `docs/ai-logs/reports/` | A | DI LUAR KENDALI D |
| 11 | Restore tokenizer dari checkpoint (prasyarat pemakaian terdokumentasi) | `test_tokenizer.py::TestTokenizerFromVocab` (5 tes), `test_checkpoint_restore_contract.py::test_restore_checkpoint_then_generate_is_not_empty` | D14 | PASS (menutup F-D9-01) |

## 2. Issue #3 (B) — Implementasi Komponen Inti Transformer

| # | Acceptance criterion | Bukti test | Sumber | Status |
|---:|---|---|---|---|
| 1 | Tidak ada `nn.Transformer*`/`nn.MultiheadAttention` di jalur inti | `test_integration_components.py::TestComponentIntegration::test_no_forbidden_transformer_module`; pemindaian sumber case-sensitive D13 §1.7 | B/D | PASS |
| 2 | Shapes output PE/MHA/DecoderBlock/MiniGPT sesuai §6 | `test_positional_encoding.py` (16), `test_attention.py` (28), `test_decoder_block.py` (18), `test_decoder_block_contract.py` (13), `test_minigpt_contract.py` (14), `test_minigpt_logits.py` (2) | B/D | PASS |
| 3 | Causal mask mencegah melihat masa depan | `test_causal_masking.py` (8), `test_attention.py::TestCausalMask::test_causal_invariance_with_future_token_changes` | B/D | PASS (kontrol) |
| 4 | Kontrol negatif: invariance gagal tanpa mask | `test_attention.py::TestCausalMask::test_invariance_fails_without_mask` | B | PASS (kontrol) |
| 5 | Forward/backward berjalan; gradien bukan `None` di semua parameter | `test_attention.py::TestAttentionShape::test_gradient_flows_end_to_end`, `test_decoder_block.py::TestGradients::test_gradients_flow_to_all_parameters`, `test_minigpt_contract.py::TestMiniGPTGradients::test_all_parameters_receive_finite_nonzero_gradient`, `test_training_contract.py::TestParameterUpdate::test_every_trainable_parameter_changes_after_one_step` | B/D | PASS |
| 6 | `T > max_len` (PE) dan `d_model % n_heads != 0` (MHA) → `ValueError` | `test_positional_encoding.py::TestPositionalEncoding::test_value_error_when_T_exceeds_max_len`, `test_attention.py::TestAttentionValidation::test_value_error_when_heads_do_not_divide`, `::test_value_error_when_zero_heads`, `::test_value_error_when_more_heads_than_d_model` | B/D | PASS |
| 7 | Kompleksitas `O(B·T²·d)` / `O(B·H·T²)` / `O(B·T·d²)` didokumentasikan | `TECH_SPEC.md` §7, `D12_TESTING_REPORT.md` §2.10 | D | DOKUMEN (aritmetika analitis, bukan profiler) |
| 8 | Setiap subtask B1–B14 punya bukti | laporan AI Issue B | B | DI LUAR KENDALI D |

## 3. Issue #4 (C) — MiniGPT, Training & Text Generation

| # | Acceptance criterion | Bukti test | Sumber | Status |
|---:|---|---|---|---|
| 1 | Logits `[B, T, vocab_size]` float32 | `test_minigpt_logits.py::test_logits_shape_and_dtype`, `test_minigpt_contract.py::TestMiniGPTForwardShape::test_baseline_shape_dtype_finite` | C/D | PASS |
| 2 | Satu step training memperbarui parameter, loss finite | `test_training_step.py::test_parameter_update`, `test_training_contract.py::TestParameterUpdate` (7 tes), `test_end_to_end_pipeline.py::test_training_step_updates_parameters` | C/D | PASS (kontrol `lr=0`) |
| 3 | Train/val loss tercatat per epoch; **file metrics JSONL terverifikasi isinya** | `test_metrics_jsonl_contract.py::test_train_writes_one_jsonl_line_per_epoch`, `::test_train_without_metrics_path_writes_nothing`, `::test_write_metrics_jsonl_overwrites_not_appends` | D14 | PASS (menutup gap Issue C #3) |
| 4 | Checkpoint berisi model + vocabulary + config dan dapat dimuat ulang | `test_checkpoint.py::test_checkpoint_roundtrip`, `test_checkpoint_restore_contract.py::test_restored_vocab_size_builds_minigpt` | C/D14 | PASS |
| 5 | Jalur restore terdokumentasi (README) menghasilkan teks | `test_checkpoint_restore_contract.py::test_restore_checkpoint_then_generate_is_not_empty` | D14 | PASS (menutup F-D9-01) |
| 6 | Generation berhenti sesuai aturan (`<eos>` / `max_new_tokens`) | `test_generation_stop.py::test_stop_on_eos`, `::test_stop_on_max_new_tokens`, `test_end_to_end_pipeline.py::test_generate_stops_at_eos_on_real_model`, `::test_generate_with_real_tokenizer_and_model` | C/D | PASS |
| 7 | Window geser dibatasi `model.context_length`, bukan konstanta | `test_generate_context_contract.py` (4 tes), `test_end_to_end_pipeline.py::test_generate_sliding_window_on_long_prompt` | D14/D | PASS (menutup F-D9-02) |
| 8 | Signature `generate` sesuai `TECH_SPEC.md` §6 | tidak ada tes; perbandingan statis `TECH_SPEC.md:105` vs `src/generate.py` | D | **OPEN** (F-D9-03, butuh keputusan koordinator) |
| 9 | Hasil aktual dilaporkan tanpa klaim berlebihan | `docs/ai-logs/reports/AI-LOG-C14-experiment.md`; artefak `outputs/` tidak ada di repo | C | DOKUMEN (angka dikutip, tidak diukur ulang) |
| 10 | Setiap subtask C1–C14 punya bukti | laporan AI Issue C | C | DI LUAR KENDALI D |

## 4. Issue #5 (D) — Unit Test, Integrasi & Dokumentasi Teknis

| # | Acceptance criterion | Bukti pada D14 | Status |
|---:|---|---|---|
| 1 | Seluruh tes dapat dijalankan konsisten dan direproduksi | `pytest -q` → `175 passed, 15 skipped`; `pytest -q --run-integration` → `190 passed`; `pytest --collect-only -q --run-integration` → `190 tests collected` | PASS (untuk environment ini; anggota lain tidak diverifikasi) |
| 2 | Tes memeriksa perilaku, bukan sekadar "tidak error" | kontrol negatif: `test_invariance_fails_without_mask`, `TestParameterUpdate::test_zero_lr_control_leaves_parameters_unchanged`, `TestPadTargetIgnoredInLoss::test_perturbing_pad_row_logits_does_not_change_loss`, `test_helpers_contract.py::test_assert_x_y_shift_rejects_broken_shift`, `::test_make_batch_reversed_direction_is_rejected` | PASS (kontrol) |
| 3 | Hasil tes dan error dicatat dari output aktual | `docs/D9_FAILURE_LOG.md`, `docs/D10_FIX_VERIFICATION.md`, `docs/D12_TESTING_REPORT.md`, `docs/D13_FINAL_REPORT.md`, `docs/D14_FIX_REPORT.md` | PASS |
| 4 | Integrasi tanpa mengubah kontrak publik sepihak | D14 mengubah dua perilaku yang **menyimpang** dari kontrak (F-D9-01, F-D9-02) ke arah `TECH_SPEC.md`, bukan menjauh; signature `generate` tidak diubah (F-D9-03) | PASS |
| 5 | Seluruh kegagalan relevan dilaporkan **dan ditindaklanjuti** dengan bukti | F-D9-01/02/04/05/06 dan F-D11-01 ditutup dengan tes/bukti di `docs/D14_FIX_REPORT.md`; F-D9-03 sengaja tetap OPEN menunggu keputusan | PASS (6 dari 7 ditutup; 1 menunggu keputusan) |
| 6 | Matriks kontrak→test→status (D1) lengkap | dokumen ini | PASS |
| 7 | Setiap subtask D1–D13 punya bukti | D1 (dokumen ini), D2 (`D2_Testing_Framework.md`), D3 (`D3_Test_Structure.md`), D4–D13 di `docs/TESTING.md` dan laporan terkait | PASS |

## 5. Issue #6 (E) — Validasi Logging Otomatis

| # | Acceptance criterion | Bukti | Status |
|---:|---|---|---|
| 1 | Setiap anggota punya bukti smoke test tertulis | 82 laporan Markdown untuk ≥4 member id; raw log hanya tersedia untuk satu anggota dan di-gitignore (`D13_FINAL_REPORT.md` §2.5) | SEBAGIAN |
| 2 | Prompt uji dan respons benar-benar ada di raw log (bukan ringkasan) | prompt sesi ditemukan verbatim di `docs/ai-logs/raw/rafasuryaputra-80048/*.jsonl` (D13 §2.5) | PASS untuk satu anggota; anggota lain TIDAK TERVERIFIKASI |
| 3 | Laporan Markdown dihasilkan dan konsisten dengan raw log | laporan otomatis dibangkitkan dari raw; field manual masih `[Isi manual]` pada laporan lama | SEBAGIAN |
| 4 | Tidak ada klaim "logging berhasil" tanpa bukti | `D13_FINAL_REPORT.md` §2.5 tidak membuat klaim lintas anggota | PASS |
| 5 | Tidak ada API key/token/password di log | pemindaian 8 pola pada 103 berkas: 2 hit, keduanya literal `password=[REDACTED]` hasil redaksi logger | PASS (untuk berkas yang tersedia) |
| 6 | File log dan laporan tersimpan di `docs/ai-logs/` | laporan tracked; raw ada tetapi di-gitignore (`.gitignore:29`) | SEBAGIAN |
| 7 | Setiap subtask E1–E10 punya bukti | tidak ada dokumen E1–E10 di repo; hanya laporan per sesi | TIDAK TERVERIFIKASI |

---

## 6. Rekonsiliasi jumlah tes (koleksi aktual D14)

| Kelompok | Berkas | Tes |
|---|---:|---:|
| Modul A — data pipeline & tokenizer | 6 | 36 |
| Modul B — komponen inti | 6 | 90 |
| Modul C — MiniGPT/training/generation | 10 | 49 |
| Integrasi lintas modul (`test_end_to_end_pipeline.py` 7, `test_train_integration.py` 1) | 2 | 8 |
| Helper bersama | 1 | 7 |
| **Total** | **25** | **190** |

Marker `integration` dipakai oleh 15 tes (7 di `test_integration_components.py`, 7 di
`test_end_to_end_pipeline.py`, 1 di `test_train_integration.py`); angka itu **subset** dari tabel
di atas, bukan kelompok tambahan.

Rincian per berkas (hasil `--collect-only` D14): attention 28, decoder_block 18, training_contract 18,
data_pipeline 17, positional_encoding 16, minigpt_contract 14, decoder_block_contract 13,
tokenizer 11, causal_masking 8, end_to_end_pipeline 7, helpers_contract 7, integration_components 7,
generate_context_contract 4, metrics_jsonl_contract 3, sliding_window 3, checkpoint_restore_contract 2,
data_split 2, dataloader 2, generation_stop 2, minigpt_logits 2, minigpt_mock 2, bos_eos 1,
checkpoint 1, train_integration 1, training_step 1.

Konsistensi: `36 + 90 + 49 + 8 + 7 = 190`; default `190 − 15 = 175`.

## 7. Keterbatasan

1. Status PASS berarti tes lulus pada environment D14 (Python 3.10.6, pytest 9.1.1,
   torch 2.14.1+cpu, CPU-only), bukan jaminan lintas environment.
2. Angka eksperimen C14 tetap **dikutip**, bukan diukur ulang; artefak `outputs/` tidak ada di repo.
3. Kriteria Issue #6 tidak dapat diverifikasi penuh dari clone karena raw log anggota lain
   di-gitignore.
4. F-D9-03 tetap OPEN secara sengaja: perubahan signature `generate` memerlukan keputusan
   koordinator + ADR, dan D14 tidak boleh mengubahnya sepihak.
