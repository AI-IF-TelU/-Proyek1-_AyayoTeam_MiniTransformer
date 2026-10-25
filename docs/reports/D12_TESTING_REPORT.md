# D12 — Laporan Pengujian dan Hasil Eksperimen

**Issue:** [STEP 3] Issue D — Unit Test, Integrasi & Dokumentasi Teknis
**Subtask:** D12. Susun dokumentasi pengujian dan hasil eksperimen
**Commit saat eksekusi:** `4dbe3a2` (`feat(Issue D): Substask D11`), branch `master`
**Tanggal eksekusi:** 2026-10-24 (WIB, UTC+07:00)
**Anggota:** Rafa Suryaputra (rafasuryaputra-80048)

Dokumen ini mengonsolidasikan tiga hal yang sebelumnya tersebar di `docs/TESTING.md` (riwayat
per subtask), `docs/D9_FAILURE_LOG.md`, `docs/D10_FIX_VERIFICATION.md`, dan
`docs/ai-logs/reports/AI-LOG-C14-experiment.md`:

1. perintah runner dan status suite yang **benar-benar dijalankan** pada commit di atas;
2. matriks kontrak → test → status untuk `docs/TECH_SPEC.md` §3–§7 dan acceptance criteria
   Issues #2–#6;
3. riwayat debugging beserta hasil eksperimen aktual.

Semua angka di sini berasal dari output perintah yang dijalankan pada sesi D12 (lihat §2) atau
dikutip eksplisit dari dokumen bukti yang sudah ada. Angka yang tidak dijalankan ulang diberi
label sumbernya. Tidak ada hasil yang dikarang.

---

## 1. Lingkungan dan cara reproduksi

### 1.1 Environment

| Item | Nilai |
|---|---|
| OS / shell | Windows, PowerShell 5.1 |
| Python | 3.10.6 (`.venv\Scripts\python.exe`) |
| pytest | 9.1.1 |
| PyTorch | 2.14.1+cpu |
| CUDA | tidak tersedia (CPU-only) |
| Runner resmi | `pytest` (D2, keputusan koordinator 2026-10-19); sudah ada di `requirements.txt` |
| Konfigurasi | `pytest.ini` (`testpaths = tests`, `-ra --strict-markers`, marker `contract` dan `integration`) |
| Dependency baru | tidak ada |

Catatan: `python` global (Laragon 3.10) tidak memiliki pytest. Seluruh perintah di dokumen ini
memakai `.\.venv\Scripts\python.exe`; bentuk `python -m pytest` diasumsikan setelah venv aktif.

### 1.2 Peta perintah runner

| Tujuan | Perintah | Cakupan |
|---|---|---|
| Suite default (cepat) | `python -m pytest -q` | semua tes non-`integration` |
| Suite penuh | `python -m pytest -q --run-integration` | seluruh 169 tes, termasuk lintas modul |
| Hanya integrasi | `python -m pytest -q -m integration --run-integration` | 15 tes `integration` |
| Satu modul | `python -m pytest tests/test_tokenizer.py -q` | per berkas |
| Koleksi saja | `python -m pytest --collect-only -q --run-integration` | inventaris `file::test` untuk matriks §3 |

Perilaku skip: `tests/conftest.py::pytest_collection_modifyitems` menambahkan marker `skip` ke
setiap tes ber-`@pytest.mark.integration` bila `--run-integration` tidak diberikan. Jadi suite
default **tidak membuang** tes integrasi secara diam-diam — tes tersebut tampil sebagai
`skipped` dan dihitung di ringkasan.

Semua tes memakai fixture `seed_everything` (autouse) yang menetapkan seed 42 sebelum tiap tes,
sesuai `TECH_SPEC.md` §6.

### 1.3 Status suite terkini (dijalankan 2026-10-24, `master @ 4dbe3a2`)

| Perintah | Output aktual | Status |
|---|---|---|
| `python -m pytest --collect-only -q --run-integration` | `169 tests collected in 10.33s` | OK |
| `python -m pytest --collect-only -q` | `169 tests collected in 7.90s` | OK (koleksi sama; skip terjadi saat eksekusi) |
| `python -m pytest -q` | `154 passed, 15 skipped in 21.54s` | PASS |
| `python -m pytest -q --run-integration` | `169 passed in 22.67s` | PASS |
| `python -m pytest -q -m integration --run-integration` | `15 passed, 154 deselected in 16.48s` | PASS |
| Modul A (6 berkas) | `31 passed in 9.44s` | PASS |
| Modul B (6 berkas, default) | `83 passed, 7 skipped in 15.68s` | PASS |
| Modul B (6 berkas, `--run-integration`) | `90 passed in 15.42s` | PASS |
| Modul C (7 berkas) | `40 passed in 15.26s` | PASS |
| `python -m pytest tests/test_data_split.py -q` | `2 passed in 9.60s` | PASS |

Tidak ada `failed`, `error`, atau `xfail` pada seluruh run di atas. Durasi bervariasi antarrun;
angka durasi bukan bagian dari kontrak.

Perintah persis untuk grup modul:

```powershell
# Modul A
python -m pytest tests/test_tokenizer.py tests/test_data_pipeline.py tests/test_dataloader.py `
  tests/test_sliding_window.py tests/test_bos_eos.py tests/test_data_split.py -q

# Modul B
python -m pytest tests/test_positional_encoding.py tests/test_attention.py `
  tests/test_causal_masking.py tests/test_decoder_block.py `
  tests/test_decoder_block_contract.py tests/test_integration_components.py -q --run-integration

# Modul C
python -m pytest tests/test_minigpt_logits.py tests/test_minigpt_mock.py `
  tests/test_minigpt_contract.py tests/test_training_step.py `
  tests/test_training_contract.py tests/test_checkpoint.py tests/test_generation_stop.py -q
```

### 1.4 Rekonsiliasi jumlah tes

| Kelompok | Berkas | Tes | Keterangan |
|---|---:|---:|---|
| Modul A — data pipeline & tokenizer | 6 | 31 | tidak ada tes `integration` |
| Modul B — komponen inti | 6 | 90 | 7 di antaranya `integration` (`test_integration_components.py`) |
| Modul C — MiniGPT/training/generation | 7 | 40 | tidak ada tes `integration` |
| `test_train_integration.py` | 1 | 1 | `integration` |
| `test_end_to_end_pipeline.py` (D11) | 1 | 7 | seluruhnya `integration` |
| **Total** | **21** | **169** | |

Konsistensi: `31 + 90 + 40 + 1 + 7 = 169`. Default: `169 − (7 + 1 + 7) = 154`. Hasil aktual
`154 passed, 15 skipped` dan `169 passed` cocok dengan dekomposisi ini.

### 1.5 Jumlah tes per berkas (hasil koleksi aktual)

| Berkas | Tes | Berkas | Tes |
|---|---:|---|---:|
| `test_attention.py` | 28 | `test_minigpt_contract.py` | 14 |
| `test_decoder_block.py` | 18 | `test_positional_encoding.py` | 16 |
| `test_training_contract.py` | 18 | `test_decoder_block_contract.py` | 13 |
| `test_data_pipeline.py` | 17 | `test_causal_masking.py` | 8 |
| `test_end_to_end_pipeline.py` | 7 | `test_integration_components.py` | 7 |
| `test_tokenizer.py` | 6 | `test_sliding_window.py` | 3 |
| `test_dataloader.py` | 2 | `test_data_split.py` | 2 |
| `test_minigpt_logits.py` | 2 | `test_minigpt_mock.py` | 2 |
| `test_generation_stop.py` | 2 | `test_bos_eos.py` | 1 |
| `test_checkpoint.py` | 1 | `test_training_step.py` | 1 |
| `test_train_integration.py` | 1 | | |

---

## 2. Matriks kontrak → test → status

Kolom **Status** berarti: tes yang disebut benar-benar ada di koleksi dan lulus pada run §1.3.
`PASS` = perilaku kontrak dibuktikan tes. `GAP` = perilaku ada di kontrak tetapi tidak dicakup
tes. `OPEN` = dicakup tes namun perilaku implementasi masih menyimpang dari kontrak (lihat §6).

### 2.1 §3 Tokenizer (`src/data/tokenizer.py`)

| Kontrak | Bukti test | Status |
|---|---|---|
| Urutan special `0–3`: `<pad>`, `<bos>`, `<eos>`, `<unk>` | `test_data_pipeline.py::test_special_token_ids_and_order` | PASS |
| Lowercase + regex `\w+\|[^\w\s]` | `test_data_pipeline.py::test_lowercase_and_regex` | PASS |
| Token di luar vocab → `<unk>` | `test_data_pipeline.py::test_unknown_fallback`, `test_tokenizer.py::TestTokenizerBasic::test_tokenizer_unknown` | PASS |
| Token khusus (tanda baca) ditokenisasi terpisah | `test_tokenizer.py::TestTokenizerBasic::test_tokenizer_special_chars` | PASS |
| Id mengikuti urutan teks, bukan urutan vocab | `test_tokenizer.py::TestTokenizerOrder::test_encode_preserves_text_order` | PASS |
| Urutan id berdasarkan frekuensi (tie-break deterministik) | `test_data_pipeline.py::test_frequency_ordering_with_tiebreak` | PASS |
| `fit` menghitung frekuensi lintas dokumen (bukan per dokumen) | `test_data_pipeline.py::test_fit_with_multiple_documents_counts_across_corpus` | PASS |
| `vocab_size = 4 + token unik train` | `test_tokenizer.py::TestTokenizerOrder::test_vocab_size_equals_specials_plus_unique_train_tokens` | PASS |
| Vocab hanya dari train — tanpa leakage ke val/test | `test_tokenizer.py::TestTokenizerLeakage::test_no_vocab_leakage`, `test_data_split.py::test_splits_and_leakage` | PASS |
| `decode` tidak merender special | `test_data_pipeline.py::test_decode_skips_specials`, `::test_decode_specials_only_returns_empty_string` | PASS |
| Roundtrip `decode(encode(t)) == t` **tidak** dijamin (perilaku terdokumentasi) | `test_data_pipeline.py::test_lowercase_and_regex` | PASS (didokumentasikan, bukan bug) |

### 2.2 §4 Dataset (`src/data/dataset.py`)

| Kontrak | Bukti test | Status |
|---|---|---|
| `bos_id` di awal, `eos_id` di akhir, disisipkan sebagai id setelah tokenisasi | `test_bos_eos.py::test_add_bos_eos`, `test_data_pipeline.py::test_add_bos_eos` | PASS |
| Window panjang 65, stride 1, jumlah `L − 64` | `test_data_pipeline.py::test_sliding_window_exact_count_and_stride_one`, `test_sliding_window.py::test_sliding_window_and_pairs` | PASS |
| `x = ids[:64]`, `y = ids[1:65]` | idem | PASS |
| Relasi `x[i,t] == y[i,t−1]` pada posisi non-pad | `test_data_pipeline.py::test_dataset_xy_relation_and_padding`, `test_end_to_end_pipeline.py::test_tokenizer_dataset_model_shapes` | PASS |
| Dokumen pendek → satu pasangan pendek; padding di tahap batching | `test_data_pipeline.py::test_short_doc_no_pad_in_dataset`, `::test_padding_happens_in_dataloader`, `test_sliding_window.py::test_sliding_window_and_pairs` | PASS |
| Dokumen kosong dibuang; dokumen 1 token tanpa pasangan | `test_data_pipeline.py::test_empty_and_short_docs_skipped`, `test_sliding_window.py::test_empty_and_short_docs` | PASS |
| Tidak ada window melintasi batas dokumen | `test_data_pipeline.py::test_no_cross_document_windows`, `::test_no_cross_document_windows_for_long_documents`, `test_sliding_window.py::test_no_cross_document_leak`, `test_end_to_end_pipeline.py::test_real_corpus_windows_and_forward` | PASS |
| Collate pad → `pad_id=0`, pad **trailing** | `test_data_pipeline.py::test_dataloader_padding_is_trailing_and_correct_dtype`, `test_dataloader.py::test_dataloader_padding` | PASS |
| Batch `x`, `y` `[B, 64]` `int64` | `test_data_pipeline.py::test_dataloader_batch_shape`, `test_dataloader.py::test_dataloader_longer_text`, `test_end_to_end_pipeline.py::test_tokenizer_dataset_model_shapes` | PASS |
| Split per dokumen, seed 42, tanpa irisan train/val/test | `test_data_split.py::test_splits_and_leakage` | PASS |

Bukti tambahan untuk no-window-crossing memakai korpus nyata: `test_real_corpus_windows_and_forward`
membandingkan `len(dataset)` dengan penjumlahan per dokumen dari 60 dokumen
`data/processed/train.jsonl`; window lintas dokumen akan membuat jumlahnya berbeda dan tes gagal.

### 2.3 §5 Loss

| Kontrak | Bukti test | Status |
|---|---|---|
| `CrossEntropyLoss(ignore_index=pad_id)` pada logits `[B, T, V]` vs target `[B, T]` | `test_training_contract.py::TestTrainingStepLoss::test_returned_loss_matches_cross_entropy_of_step_logits`, `test_end_to_end_pipeline.py::test_padding_positions_ignored_by_loss` | PASS |
| Posisi target pad tidak berkontribusi | `test_training_contract.py::TestPadTargetIgnoredInLoss::test_perturbing_pad_row_logits_does_not_change_loss` | PASS |
| Gradien nol pada posisi target pad | `test_training_contract.py::TestPadTargetIgnoredInLoss::test_gradient_is_zero_at_pad_target_positions` | PASS |
| `pad_id` benar-benar diparameterkan (bukan hardcode 0) | `test_training_contract.py::TestPadTargetIgnoredInLoss::test_custom_pad_id_is_ignored_too` | PASS |
| Kontrol anti-vakum (tanpa `ignore_index`, hasil berubah) | `test_training_contract.py::TestPadTargetIgnoredInLoss::test_perturbing_nonpad_row_logits_changes_loss` + kontrol internal di `test_perturbing_pad_row_logits_does_not_change_loss` | PASS |
| Target seluruhnya pad → loss `nan` | `test_training_contract.py::TestTrainingStepGuards::test_error_and_pad_only_target_relationship_is_documented` | PASS (perilaku `nn.CrossEntropyLoss` dicatat; §5 tidak mengaturnya) |

### 2.4 §6 Positional Encoding (`src/model/positional_encoding.py`)

| Kontrak | Bukti test | Status |
|---|---|---|
| `forward [B,T,d] → [B,T,d]` | `test_positional_encoding.py::TestPositionalEncoding::test_output_shape` | PASS |
| Buffer `pe` `[max_len, d]` non-trainable | `test_positional_encoding.py::TestPositionalEncoding::test_buffer_non_trainable`, `TestPositionalEncodingContract::test_buffer_is_registered_and_not_trainable` | PASS |
| Rumus sinusoidal standar | `TestPositionalEncoding::test_matches_standard_sinusoid_formula`, `::test_sin_cos_pattern`, `::test_even_odd_pair_share_frequency` | PASS |
| Aditif `x + pe[:T]`, offset sama untuk setiap item batch | `TestPositionalEncoding::test_additive_semantics`, `TestPositionalEncodingContract::test_same_offset_for_every_batch_item` | PASS |
| `T > max_len` → `ValueError`; batas `T = 64` lolos | `TestPositionalEncoding::test_value_error_when_T_exceeds_max_len`, `::test_t_equals_max_len`, `TestPositionalEncodingContract::test_max_len_boundary_at_baseline` | PASS |
| Gradien identitas (PE tidak memblokir residual), tidak memutasi input, deterministik train/eval | `TestPositionalEncodingContract::test_gradient_is_identity`, `::test_forward_does_not_mutate_input`, `::test_deterministic_in_train_and_eval` | PASS |

### 2.5 §6 Causal Multi-Head Self-Attention (`src/model/attention.py`)

| Kontrak | Bukti test | Status |
|---|---|---|
| `forward [B,T,d] → [B,T,d]` float32 | `test_attention.py::TestAttentionShape::test_output_shape`, `::test_output_is_float32`, `::test_output_shape_varied_batch_and_length` | PASS |
| Proyeksi `W_q, W_k, W_v, W_o` `Linear(d,d)` terpisah | `test_attention.py::TestProjectionQKV::test_qkv_output_shape`, `::test_w_o_is_separate`, `::test_projections_are_linear` | PASS |
| Skala `1/sqrt(head_dim)` | `test_attention.py::TestScaledDotProductAttention::test_scale_is_applied`, `::test_matches_manual_scaled_attention` | PASS |
| Causal mask aditif `-inf` di segitiga atas sebelum softmax | `test_attention.py::TestCausalMask::test_mask_is_upper_triangular_negative_infinity`, `::test_mask_shape`, `::test_mask_t1_has_no_future` | PASS |
| Invariance causal: mengubah masa depan tidak mengubah keluaran masa lalu | `TestCausalMask::test_causal_invariance_with_future_token_changes`, `test_causal_masking.py::TestCausalForwardInvariance::test_every_cut_leaves_past_unchanged` | PASS |
| Kontrol negatif: invariance **gagal** tanpa mask | `TestCausalMask::test_invariance_fails_without_mask` | PASS |
| Probabilitas masa depan tepat 0; posisi 0 hanya ke dirinya | `test_causal_masking.py::TestCausalProbabilityMass::test_future_probability_is_exactly_zero`, `::test_first_position_attends_only_to_itself` | PASS |
| `d_model % n_heads != 0` → `ValueError` (termasuk `n_heads=0`, `n_heads > d_model`) | `TestAttentionValidation::test_value_error_when_heads_do_not_divide`, `::test_value_error_when_zero_heads`, `::test_value_error_when_more_heads_than_d_model`, `TestProjectionQKV::test_value_error_when_heads_dont_divide` | PASS |
| Dropout train ≠ eval (skor dan output) | `TestScaledDotProductAttention::test_dropout_train_differs_from_eval`, `TestDropoutBehavior::test_train_differs_from_eval` | PASS |
| `T=1`, float64, skor besar tetap finite, masked score tidak NaN di train mode | `TestCausalEdgeCases::test_single_position_has_no_future`, `::test_float64_input_keeps_dtype_and_causality`, `::test_large_scores_remain_finite`, `TestTrainModeDropoutSafety::test_masked_future_scores_never_nan` | PASS |
| Gradien mengalir melalui proyeksi dan attention | `TestProjectionQKV::test_gradient_flows_through_projections`, `TestScaledDotProductAttention::test_gradient_flows`, `TestAttentionShape::test_gradient_flows_end_to_end` | PASS |

### 2.6 §6 Decoder Block (`src/model/decoder_block.py`)

| Kontrak | Bukti test | Status |
|---|---|---|
| Pre-norm baseline: `x + MHA(LN(x))`, lalu `x + FFN(LN(x))` | `test_decoder_block.py::TestResidualConnection::test_pre_norm_matches_manual_residual_computation`, `test_decoder_block_contract.py::TestDecoderBlockStructure::test_baseline_hyperparameters` | PASS |
| `d_ff = 4 * d_model = 256`; `fc1 [d_ff,d]`, `fc2 [d,d_ff]` | `TestFeedForward::test_linear_layer_shapes`, `TestDecoderBlockStructure::test_ffn_projection_sizes_follow_d_ff` | PASS |
| FFN = Linear→GELU→Linear→dropout | `TestFeedForward::test_matches_manual_gelu_computation` | PASS |
| Residual aditif (parameter dinolkan → `out == x`), gradien identitas | `TestResidualConnectionContract::test_zeroed_parameters_make_block_identity`, `::test_identity_path_keeps_gradient_one` | PASS |
| Causal masking tetap berlaku menembus block | `TestCausalMaskingThroughBlock::test_every_cut_leaves_past_unchanged` + dua kontrol sensitivitas | PASS |
| Block tidak menambahkan posisi (PE milik MiniGPT) | `TestPositionIndependence::test_identical_positions_produce_identical_outputs`, `TestDecoderBlockStructure::test_block_registers_no_positional_buffers` | PASS |
| Tidak ada guard `context_length` di DecoderBlock | `TestNoContextLengthGuard::test_longer_sequences_still_forward` | PASS |
| Dropout train ≠ eval; gradien ke seluruh parameter | `test_decoder_block.py::TestDropoutBehavior::test_train_differs_from_eval`, `TestGradients::test_gradients_flow_to_all_parameters` | PASS |

### 2.7 §6 MiniGPT (`src/model/minigpt.py`)

| Kontrak | Bukti test | Status |
|---|---|---|
| `idx [B,T] int64 → logits [B,T,V] float32` | `test_minigpt_logits.py::test_logits_shape_and_dtype`, `test_minigpt_contract.py::TestMiniGPTForwardShape::test_baseline_shape_dtype_finite` | PASS |
| Komposisi Embedding → +PE → `n_layers`×DecoderBlock → LN → Linear (tanpa weight tying) | `TestMiniGPTStructure::test_component_types_and_baseline_hyperparameters`, `::test_lm_head_is_not_tied_to_embedding` | PASS |
| PE benar-benar diterapkan (token sama di posisi berbeda → logits berbeda) | `TestPositionalEncodingIsApplied::test_identical_tokens_at_different_positions_give_different_logits` | PASS |
| `T > context_length` → `ValueError`, batas 64/65 | `test_minigpt_logits.py::test_valueerror_when_t_exceeds_context`, `TestMiniGPTContextGuard::test_boundary_at_baseline_context_length` | PASS |
| Guard memakai `context_length` terkonfigurasi (bukan hardcode 64) | `TestMiniGPTContextGuard::test_guard_uses_configured_context_length` | PASS |
| Causality end-to-end (Embedding+PE+block+LN+head) | `TestMiniGPTCausality::test_every_cut_leaves_past_unchanged`, `::test_last_position_reacts_to_last_token` | PASS |
| Seluruh parameter menerima gradien finite non-nol | `TestMiniGPTGradients::test_all_parameters_receive_finite_nonzero_gradient`, `::test_embedding_gradient_reaches_used_token_ids_only` | PASS |
| `d_model % n_heads != 0` → `ValueError` di konstruktor | `TestMiniGPTInitValidation::test_value_error_when_d_model_not_divisible_by_n_heads` | PASS |
| `T=1` valid | `TestMiniGPTForwardShape::test_single_token_sequence` | PASS |

### 2.8 §6 Training (`src/train.py`)

| Kontrak | Bukti test | Status |
|---|---|---|
| Satu step training memperbarui parameter | `test_training_step.py::test_parameter_update`, `test_training_contract.py::TestParameterUpdate::test_every_trainable_parameter_changes_after_one_step`, `test_end_to_end_pipeline.py::test_training_step_updates_parameters` | PASS |
| Kontrol negatif `lr=0` → parameter tidak berubah | `TestParameterUpdate::test_zero_lr_control_leaves_parameters_unchanged` | PASS |
| State optimizer maju (`step == 1`, lalu bertambah) | `TestParameterUpdate::test_optimizer_records_one_step_for_all_parameters`, `::test_second_step_advances_optimizer_state` | PASS |
| Arah optimisasi benar (loss turun saat overfit satu batch) | `TestParameterUpdate::test_overfitting_one_batch_reduces_loss` | PASS |
| `training_step` menetapkan `model.train()` | `TestParameterUpdate::test_model_is_in_train_mode_after_step` | PASS |
| Seed 42 mereproduksi loss dan parameter; seed lain berbeda | `TestTrainingReproducibility::test_seed_42_reproduces_loss_and_parameters`, `::test_different_seed_reproduces_differently_with_dropout` | PASS |
| Guard `context_length` lewat jalur training tanpa mengubah parameter | `TestTrainingStepGuards::test_context_length_guard_applies_and_keeps_parameters` | PASS |
| Satu epoch `train()` nyata dengan komponen Issue A (train/val loss finite) | `test_train_integration.py::test_integration_one_epoch` | PASS (integration) |
| Metrics JSONL per epoch (ADR-011) | tidak ada tes otomatis; bukti empiris di `docs/ai-logs/reports/AI-LOG-C14-experiment.md` | GAP (lihat §8) |

### 2.9 §6 Generation (`src/generate.py`) dan checkpoint

| Kontrak | Bukti test | Status |
|---|---|---|
| Berhenti saat `eos_id` dihasilkan | `test_generation_stop.py::test_stop_on_eos`, `test_end_to_end_pipeline.py::test_generate_stops_at_eos_on_real_model` | PASS |
| Berhenti saat `max_new_tokens` tercapai | `test_generation_stop.py::test_stop_on_max_new_tokens`, `test_end_to_end_pipeline.py::test_generate_with_real_tokenizer_and_model` (0, 3, 8) | PASS |
| `max_new_tokens=0` → hanya prompt | `test_end_to_end_pipeline.py::test_generate_with_real_tokenizer_and_model` | PASS |
| Window geser saat prompt > `context_length` | `test_end_to_end_pipeline.py::test_generate_sliding_window_on_long_prompt` | PASS |
| Output `str` | `test_generation_stop.py` (kedua tes), `test_end_to_end_pipeline.py` | PASS |
| Checkpoint berisi `state_dict` + `vocab` + `config`, roundtrip identik | `test_checkpoint.py::test_checkpoint_roundtrip` | PASS |
| Restore checkpoint → tokenizer valid → `generate` non-kosong | tidak ada tes | **GAP** (F-D9-01 masih OPEN) |
| `generate` memakai `model.context_length`, bukan konstanta 64 | tidak ada tes | **GAP** (F-D9-02 masih OPEN) |
| Signature `generate` sesuai `TECH_SPEC.md` §6 | tidak ada tes; perbandingan statis | **OPEN** (F-D9-03) |

Dua baris GAP terakhir adalah alasan mengapa "169 passed" **tidak** berarti seluruh jalur
pemakaian terdokumentasi di README sudah benar. Detail ada di §6 dan §8.

### 2.10 §2 batas library dan §7 kompleksitas

| Item | Bukti | Status |
|---|---|---|
| Tidak ada `nn.Transformer`, `nn.TransformerDecoder`, `nn.MultiheadAttention` pada jalur inti | `test_integration_components.py::TestComponentIntegration::test_no_forbidden_transformer_module` (pemindaian statis) | PASS |
| Kompleksitas attention `O(B·T²·d)`, memori `O(B·H·T²)`, FFN `O(B·T·d²)` | didokumentasikan di `TECH_SPEC.md` §7 dan laporan B14 | Terdokumentasi, bukan diukur profiler |
| Angka baseline `B=32, T=64, d=64, H=4` | aritmetika analitis: attention ≈ 8,4M operasi/blok; matriks attention 524.288 elemen ≈ 2 MiB fp32; FFN 67,1M MAC/blok | Asumsi, dicatat sebagai asumsi |

Tidak ada tes yang mengukur kompleksitas secara empiris. Klaim performa tidak dibuat.

---

## 3. Matriks acceptance criteria Issue #2–#6

### 3.1 Issue #2 (A) — Data Pipeline & Tokenizer

| Acceptance criterion | Bukti | Status |
|---|---|---|
| `fit`/`encode`/`decode`/`vocab_size` sesuai §3 | §2.1 (11 baris PASS) | PASS |
| Tidak ada vocabulary leakage train→val/test | `test_tokenizer.py::TestTokenizerLeakage::test_no_vocab_leakage`, `test_data_split.py::test_splits_and_leakage` | PASS |
| Tidak ada window melintasi batas dokumen | 4 tes di §2.2 + korpus nyata | PASS |
| Batch `[B, 64]` dan padding sesuai §4 | 4 tes di §2.2 | PASS |
| Dokumen kosong dibuang; 1 token tanpa pasangan | 2 tes di §2.2 | PASS |
| `DATASET_CARD.md` berisi angka terverifikasi | `docs/DATASET_CARD.md` (720/80/200; token 290.920/33.157/77.330; vocab 19.192; padding train 0,00%) | Terisi (dokumen, bukan tes) |
| Tiap subtask A1–A13 punya bukti output aktual | laporan AI Issue A di `docs/ai-logs/reports/` | Di luar kendali D12; tidak diverifikasi ulang |

### 3.2 Issue #3 (B) — Implementasi Komponen Inti Transformer

| Acceptance criterion | Bukti | Status |
|---|---|---|
| Tidak ada `nn.Transformer*`/`nn.MultiheadAttention` pada jalur inti | `test_no_forbidden_transformer_module` | PASS |
| Shapes output sesuai §6 | §2.4–§2.7 | PASS |
| Causal mask mencegah melihat masa depan | 8 tes invariance + kontrol negatif `test_invariance_fails_without_mask` | PASS |
| Forward/backward berjalan, gradien bukan `None` di semua parameter | §2.5–§2.7 | PASS |
| `T > max_len` (PE) dan `d_model % n_heads != 0` (MHA) → `ValueError` | §2.4, §2.5 | PASS |
| Kompleksitas didokumentasikan | `TECH_SPEC.md` §7 + laporan B14 | Terdokumentasi |
| Tiap subtask B1–B14 punya bukti | laporan AI Issue B | Di luar kendali D12 |

### 3.3 Issue #4 (C) — MiniGPT, Training & Text Generation

| Acceptance criterion | Bukti | Status |
|---|---|---|
| Logits `[B, T, V]` float32 | `test_minigpt_logits.py`, `TestMiniGPTForwardShape` | PASS |
| Satu step training memperbarui parameter, loss finite | §2.8 | PASS |
| Train/val loss tercatat per epoch, file metrics terverifikasi | tidak ada tes; bukti eksperimen C14 (4 baris JSONL dikutip di laporan C14) | GAP (tidak ada tes otomatis) |
| Checkpoint berisi model + vocab + config, dapat dimuat | `test_checkpoint.py::test_checkpoint_roundtrip` | PASS |
| Generation memakai model terlatih dan berhenti sesuai aturan | `test_generation_stop.py`, `test_end_to_end_pipeline.py` | PASS untuk aturan stop; **jalur restore masih OPEN** (F-D9-01) |
| Hasil aktual dilaporkan tanpa klaim berlebihan | `docs/ai-logs/reports/AI-LOG-C14-experiment.md` | Terpenuhi (dokumen) |
| Tiap subtask C1–C14 punya bukti | laporan AI Issue C | Di luar kendali D12 |

### 3.4 Issue #5 (D) — Unit Test, Integrasi & Dokumentasi Teknis

| Acceptance criterion | Bukti | Status |
|---|---|---|
| Seluruh tes dapat dijalankan konsisten, dapat direproduksi | §1.2–§1.3 (semua perintah dan output) | PASS |
| Tes memeriksa perilaku, bukan sekadar "tidak error" | kontrol negatif: `test_invariance_fails_without_mask`, kontrol `lr=0`, kontrol `ignore_index=-100`, kontrol mutasi mask D6 | PASS |
| Hasil tes dan error dicatat dari output aktual | §1.3, §6, `docs/D9_FAILURE_LOG.md`, `docs/D10_FIX_VERIFICATION.md` | PASS |
| Integrasi tanpa mengubah kontrak publik sepihak | D11: 15 tes integrasi, tanpa perubahan `src/` | PASS |
| Seluruh kegagalan relevan dilaporkan dan ditindaklanjuti | F-D9-01…06 dilaporkan; **belum ditutup** karena perbaikan milik pemilik modul | Sebagian (pelaporan PASS, penutupan OPEN) |
| Matriks kontrak→test→status lengkap | §2 dan §3 dokumen ini | PASS (D12) |
| Tiap subtask D1–D13 punya bukti | D5–D11 di `docs/TESTING.md`; D12 di dokumen ini; D1–D4 hanya sebagian (F-D9-05) | Sebagian |

### 3.5 Issue #6 (E) — Validasi Logging Otomatis

| Acceptance criterion | Bukti | Status |
|---|---|---|
| Smoke test tertulis per anggota | laporan AI per anggota di `docs/ai-logs/reports/` | Di luar scope D12; tidak diverifikasi ulang |
| Prompt dan respons ada di raw log | `docs/ai-logs/raw/<member-id>/*.jsonl` | Ada untuk sesi ini (lihat §9 laporan AI D12) |
| Laporan Markdown konsisten dengan raw log | laporan otomatis per sesi | Dihasilkan otomatis |
| Tidak ada secret pada log | tidak diperiksa pada D12 | Tidak diverifikasi |

---

## 4. Hasil integrasi lintas modul

Marker `integration` dipakai oleh 15 tes di tiga berkas. Sebelum D11, marker terdaftar tetapi
tidak dipakai satu tes pun, sehingga `-q` dan `-q --run-integration` menghasilkan angka identik
(keterbatasan D8 nomor 1). Kondisi itu sudah tertutup.

| Berkas | Tes | Alur yang diintegrasikan |
|---|---:|---|
| `test_end_to_end_pipeline.py` | 7 | `Tokenizer.fit` → `TextDataset` → `create_dataloader` → `MiniGPT.forward` → `CrossEntropyLoss(ignore_index=0)` → `backward`/`optimizer.step` → `generate` |
| `test_integration_components.py` | 7 | `SinCosPositionalEncoding` → `CausalMultiHeadAttention` → `DecoderBlock` (gradien, tanpa modul terlarang) |
| `test_train_integration.py` | 1 | `Tokenizer` + `TextDataset` + `create_dataloader` + `train` nyata, satu epoch kecil |
| **Total** | **15** | |

Perilaku yang dibuktikan (bukan sekadar tidak error):

1. Shape dan relasi shift pada batch nyata `[4, 64]`; guard `T=65` → `ValueError`; logits
   `[4, 64, V]` float32 finite.
2. Loss `ignore_index=0` sama dengan rata-rata manual hanya pada posisi non-pad (selisih
   `1e-6`), dengan jaminan jumlah target pad `> 0` agar tes tidak vakum.
3. Gradien `token_emb.weight` dan `lm_head.weight` non-nol, lalu `optimizer.step()` mengubah
   keduanya.
4. `max_new_tokens` 0, 3, 8 menghasilkan tepat `len(prompt) + n` id (`<eos>` dinetralkan dengan
   `eos_id=-1`).
5. Berhenti di `<eos>`: `lm_head` diarahkan agar argmax = `eos` tanpa mengganti model; tokenizer
   nyata dibungkus perekam sehingga terbukti tidak ada token ditambahkan setelah `<eos>`.
6. Prompt lebih panjang dari `context_length=64` tetap menghasilkan output (window geser).
7. Korpus nyata 60 dokumen: jumlah window dataset sama persis dengan penjumlahan per dokumen.

Angka aktual: §1.3 (`15 passed, 154 deselected`, `169 passed`).

---

## 5. Riwayat debugging

Semua entri berasal dari output run yang tercatat pada laporan AI dan `docs/TESTING.md`.
Tidak ada traceback yang direkonstruksi.

| Subtask | Gejala aktual | Penyebab | Perbaikan | Bukti akhir |
|---|---|---|---|---|
| D4 | `test_lowercase_and_regex` selalu lolos | asersi `assert ... or True` | ganti menjadi perbandingan `encode("a,b") == encode("a , b")` | masuk run D4 (29 passed) |
| D5 | `test_same_offset_for_every_batch_item`: `Greatest absolute difference: 1.103617250919342e-07` (2/512 elemen) | pembulatan float32 pada `(x + pe) − x`, bukan bug modul | toleransi `atol=1e-6, rtol=1e-5` | `24 passed` (PE + causal) |
| D6 | `test_identical_positions_produce_identical_outputs`: diff `2.384185791015625e-07` (28/64 elemen) | panjang penjumlahan softmax berbeda per posisi → urutan penjumlahan float32 berbeda | toleransi `1e-6/1e-5` | `27 passed` |
| D6 | `test_perturbing_one_item_does_not_change_other_items` gagal | asersi uji salah: item yang sengaja diubah diperiksa "tidak berubah" | item 0 harus berubah, item 1 identik eksak | lulus |
| D6 | `test_positional_encoding_buffer_shape`: `KeyError: 'pe'` | buffer milik submodul → nama terdaftar `pos_enc.pe` | kunci `pos_enc.pe` | lulus |
| D6 | `make_model("minigpt")` → `TypeError: unexpected keyword argument 'd_ff'` | helper meneruskan `d_ff` yang bukan parameter `MiniGPT` | `d_ff` tidak diteruskan (diturunkan `4 * d_model`) | helper terverifikasi |
| D7 | `test_perturbing_nonpad_row_logits_changes_loss`: `tensor(True) is not false` | perturbasi `+= 100` ke semua kelas = pergeseran seragam; softmax invarian | perturbasi satu kelas + kontrol `ignore_index=-100` | `18 passed` |
| D7 | `test_context_length_guard_applies_and_keeps_parameters`: `7 != 9` | batch uji `T=6`, ditambah 1 kolom belum melewati batas 8 | batch guard eksplisit `T = context_length + 1 = 9` | lulus |
| D9 | `generate()` = `''` tanpa error (F-D9-01) | restore README hanya mengisi `token_to_id`; `id_to_token` kosong, `vocab_size` 0 | **belum diperbaiki** (milik Issue C/A) | OPEN |
| D9 | `ValueError: sequence length T=9 exceeds context_length=8` (F-D9-02) | `src/generate.py:8` hardcode `context_length=64` | **belum diperbaiki** | OPEN |
| D9 | Rujukan `ADR-014` tidak ada (F-D9-04) | docstring `src/train.py:31` | **belum diperbaiki** | OPEN |
| D10 | 10 seed diuji: 7 melempar `ValueError`, 3 berhenti lebih dulu karena `<eos>` | F-D9-02 intermiten — bergantung token yang dihasilkan | tes regresi wajib menetralkan `<eos>` (`eos_id=-1`) | tercatat |
| D11 | `helpers.make_batch` membangun `x[i,t] == y[i,t+1]` | `y[:, 1:] = x[:, :-1]` (arah terbalik dari §4) | **belum diubah**; fixture `batch` tidak dipakai tes mana pun → dampak nol | OPEN (F-D11-01) |

Kontrol negatif yang dijalankan (agar tes tidak lolos palsu):

- D6: skrip di luar repo menghapus `_causal_mask` → tes causality block dan model **gagal**;
  dengan mask utuh keduanya lulus. `src/` tidak diubah permanen.
- D7: `ignore_index=pad(0)` → baris pad tidak memengaruhi loss dan gradiennya nol;
  `ignore_index=-100` → keduanya berubah. Tes bergantung pada masking yang benar.
- §2.5: `test_invariance_fails_without_mask` adalah kontrol negatif permanen di dalam suite.

---

## 6. Pengaruh temuan terbuka terhadap arti "suite hijau"

Suite hijau pada §1.3 membuktikan kontrak yang **memang diuji**. Berikut kontrak yang tidak
tercakup atau masih menyimpang. Daftar ini wajib dibaca bersama angka pass.

| ID | Ringkasan | Dampak | Status |
|---|---|---|---|
| F-D9-01 | Restore checkpoint sesuai `README.md:276-286` menyisakan `id_to_token` kosong dan `vocab_size=0` → `generate()` = `''` tanpa error | pengguna mengira model gagal padahal bobot benar | OPEN (Issue C + A) |
| F-D9-02 | `src/generate.py:8` `context_length=64` hardcode; model `context_length≠64` → `ValueError` di tengah generasi (intermiten 7/10 seed) | generasi gagal untuk konfigurasi non-baseline | OPEN (Issue C) |
| F-D9-03 | Signature `generate` (7 parameter) ≠ `TECH_SPEC.md:105` (2 parameter) | kontrak publik tertulis tidak cocok dengan implementasi | OPEN (butuh keputusan koordinator/ADR) |
| F-D9-04 | `src/train.py:31` merujuk ADR-014 yang tidak ada (ADR hanya 001–012) | dokumentasi menyesatkan | OPEN |
| F-D9-05 | Laporan D1 mengklaim `docs/D1_*`, `D2_*`, `D3_*` yang tidak ada | deliverable D1 tidak punya artefak; **D12 menyediakan matriks konsolidasi** di §2–§3 | Sebagian tertutup (dokumen ini), log lama tidak diubah |
| F-D9-06 | README menunjuk `outputs/metrics/full/minigpt_c14.pt` yang tidak ada di repo | contoh restore tidak dapat dijalankan dari clone | OPEN |
| F-D11-01 | `tests/helpers.py::make_batch` (dan `assert_x_y_shift`) memakai arah shift terbalik | nol saat ini: fixture `batch` tidak dipakai tes mana pun | OPEN (keputusan pemilik Issue D) |

Gap cakupan yang tersisa (tidak ada tesnya sama sekali):

1. restore checkpoint → `generate` non-kosong;
2. `generate` dengan `model.context_length != 64`;
3. penulisan/verifikasi isi metrics JSONL oleh `train()`;
4. `Tokenizer` tanpa `from_vocab` (API restore resmi belum ada).

---

## 7. Hasil eksperimen

### 7.1 Eksperimen C14 (dikutip dari `docs/ai-logs/reports/AI-LOG-C14-experiment.md`)

Angka berikut **tidak** dijalankan ulang pada D12; sumbernya laporan C14 berdasarkan
`outputs/metrics/full/c14_metrics.jsonl`. Artefak tersebut tidak ada di repo (F-D9-06).

| Field | Nilai |
|---|---|
| Device | CPU 8 core (Modal) |
| PyTorch | `2.5.1+cu121` |
| Epochs | 4 |
| Durasi total | 5304,64 s (≈ 88,4 menit) |
| Parameter | 2.556.672 |
| Vocab | 19.192 (fit pada train) |
| Segmen train / val | 246.290 / 28.229 |
| Konfigurasi | `n_layers=2`, `n_heads=4`, `d_model=64`, `d_ff=256`, `context_length=64`, dropout 0,1 |
| Optimizer | AdamW `lr=3e-4`, `weight_decay=0.01` |
| Batch / seed | 32 / 42 |

| Epoch | Train loss | Val loss | Durasi (s) |
|---:|---:|---:|---:|
| 1 | 5.568583 | 7.135150 | 1123,65 |
| 2 | 4.152143 | 7.856671 | 921,85 |
| 3 | 3.640476 | 8.304918 | 1115,32 |
| 4 | 3.335589 | 8.649888 | 2120,66 |

Interpretasi yang diizinkan: train loss turun monoton (−40% dari epoch 1 ke 4) sementara val loss
naik monoton (+21%) — **indikasi overfitting pada run ini**, bukan klaim umum dan bukan bukti
kualitas model. Contoh greedy generation (`max_new_tokens=40`, prompt `presiden indonesia`)
koheren secara lokal tetapi berhenti karena batas token, bukan karena selesai.

### 7.2 Hubungan eksperimen dengan pengujian

| Klaim di laporan C14 | Diverifikasi tes? |
|---|---|
| Checkpoint memuat `state_dict` + `vocab` + `config` tanpa key hilang | Ya — `test_checkpoint.py::test_checkpoint_roundtrip` |
| `state_dict` dapat dimuat ke `MiniGPT` | Ya — roundtrip `state_dict` |
| Generate menghasilkan keluaran dari checkpoint | **Tidak** — jalur restore tokenizer tidak diuji (F-D9-01) |
| Metrik JSONL berisi satu baris per epoch | **Tidak** — tidak ada tes untuk penulisan metrics |

Karena itu D12 tidak mengulang klaim "checkpoint terbukti konsisten" sebagai hasil pengujian;
yang terbukti oleh suite adalah roundtrip objek, bukan jalur restore end-to-end.

### 7.3 Angka dataset (dari `docs/DATASET_CARD.md`, bukan diukur ulang di D12)

| Split | Artikel | Token (tanpa bos/eos) |
|---|---:|---:|
| Train | 720 | 290.920 |
| Val | 80 | 33.157 |
| Test | 200 | 77.330 |

Vocab 19.192; padding train 0,00% pada `context_length=64`. `data/processed/train.jsonl` yang
ada di working tree berisi 720 baris (dihitung pada sesi D12, konsisten).

---

## 8. Keterbatasan dokumentasi ini

1. **CPU-only.** Tidak ada uji CUDA, mixed precision, atau multi-GPU. Versi dependency di luar
   environment §1.1 tidak diverifikasi.
2. **Bukan bukti kualitas model.** Tes membuktikan kontrak perilaku, bukan kualitas bahasa.
3. **Tes korpus nyata memakai 60 dokumen pertama** `data/processed/train.jsonl`, bukan 720 penuh,
   agar durasi suite wajar. Berkas wajib ada; bila hilang tes gagal eksplisit (`pytest.fail`).
4. **`test_data_split.py` bergantung pada `data/raw/*.jsonl`** dan menulis ulang
   `data/processed/*.jsonl`. Pada run D12, `git status` tetap bersih setelahnya (split
   deterministik, seed 42), tetapi bila `data/raw/` hilang tes gagal `FileNotFoundError` — itu
   kegagalan fixture data, bukan kegagalan kontrak.
5. **Tidak ada pengukuran kompleksitas empiris.** Angka §2.10 adalah aritmetika analitis dari
   `TECH_SPEC.md` §7 dan harus dibaca sebagai asumsi baseline.
6. **Durasi tes bervariasi antarrun**; hanya hasil pass/fail/skip yang stabil.
7. **Status Issue #2–#6 per subtask** hanya dirangkum dari dokumen yang ada; D12 tidak membuka
   dan memverifikasi setiap laporan AI anggota lain.
8. **F-D9-01/F-D9-02/F-D9-03/F-D9-04/F-D9-06/F-D11-01 tetap terbuka.** D12 tidak memperbaiki kode
   modul maupun `src/`, sesuai Issue D §4.

---

## 9. Cara memelihara dokumen ini

1. Setiap kali suite berubah, perbarui §1.3–§1.5 dengan output **yang baru dijalankan**; jangan
   menyalin angka lama tanpa menjalankan ulang.
2. Setiap tes baru wajib muncul di §2 pada baris kontrak yang dibuktikannya, dengan nama
   `file::TestClass::test_name` yang benar-benar ada di `--collect-only`.
3. Jika temuan ditutup, ubah status di §6 **dan** tambahkan bukti run ke
   `docs/D10_FIX_VERIFICATION.md`/`docs/TESTING.md`; jangan menghapus riwayat.
4. Angka eksperimen baru ditulis di laporan eksperimennya sendiri, lalu dirujuk di §7 — tidak
   disalin ulang tanpa sumber.
5. Jangan mengubah `docs/TECH_SPEC.md`/ADR untuk menyesuaikan dokumen ini; kontrak berubah hanya
   lewat ADR.

---

## 10. Perubahan file pada D12

| File | Status |
|---|---|
| `docs/D12_TESTING_REPORT.md` | baru (dokumen ini) |
| `docs/TESTING.md` | ditambah bagian D12 (ringkasan + tautan) |
| `README.md` | §12 diperluas: runner, tautan dokumen, status aktual, temuan terbuka |
| `docs/ai-logs/reports/AI-LOG-rafasuryaputra-80048-IssueD-D12.md` | baru (laporan AI) |
| `src/`, `tests/`, `pytest.ini`, `requirements.txt`, `docs/TECH_SPEC.md`, ADR, `issues/`, `data/` | **tidak diubah** |

Tidak ada operasi Git yang dijalankan (commit/push/pull/branch/merge/staging).
