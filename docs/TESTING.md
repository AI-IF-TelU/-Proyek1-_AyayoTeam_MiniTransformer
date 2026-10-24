# Dokumentasi Pengujian (pytest)

## Ringkasan

Framework pengujian resmi proyek Mini-Transformer adalah **pytest**, ditetapkan oleh koordinator pada 2026-10-19 (Issue D, subtask D2). `pytest` sudah tercantum di `requirements.txt`, tidak diperlukan dependency baru.

## Konfigurasi

File `pytest.ini` di root repository:

- `testpaths = tests` — semua tes berada di folder `tests/`.
- `python_files = test_*.py` — pola nama file tes.
- `python_classes = Test*` — pola nama kelas tes (untuk gaya `unittest`).
- `python_functions = test_*` — pola nama fungsi tes (untuk gaya `pytest` murni).
- `addopts = -ra --strict-markers` — ringkasan tes yang dilewati/gagal, penolak penanda tak terdaftar.
- Marker terdaftar:
  - `contract`: tes berbasis kontrak dari `docs/TECH_SPEC.md`.
  - `integration`: tes lintas modul (memerlukan `--run-integration`).

Marker `integration` dilewati secara default oleh `conftest.py` kecuali menjalankan dengan opsi `--run-integration`.

## Perintah Pengeksekusian

### Seluruh suite (default, tanpa integrasi)

```powershell
python -m pytest -q
```

Hasil aktual (sesuai versi yang tersedia): **117 passed** setelah D5 (103 passed sebelum D5; torch 2.14.1+cpu via `.venv`).

### Subset per modul

Contoh tes tokenizer:

```powershell
python -m pytest tests/test_tokenizer.py -q
```

Contoh tes model:

```powershell
python -m pytest tests/test_positional_encoding.py tests/test_attention.py tests/test_decoder_block.py tests/test_minigpt_logits.py -q
```

### Tes integrasi (lintas modul)

```powershell
python -m pytest -q --run-integration
```

Tes integrasi menunggu modul dari Issues A, B, dan C tersedia. Jika modul belum tersedia, collection akan gagal dengan `ImportError` — bukan kegagalan tes.

## Hasil Verifikasi Aktual

Perintah `python -m pytest -q` dijalankan dan terlihat output: `103 passed in 17.55s` (durasi dapat bervariasi antarrun; run verifikasi lain mencatat 18.35s). Semua tes kontrak lulus pada environment yang tersedia. Hasil ini mencakup tes tokenizer, positional encoding, causal attention, decoder block, MiniGPT logits, training step, checkpoint roundtrip, generation stop, sliding window, dan data pipeline.

### Subtask D4 — Tes tokenizer dan data pipeline

Perintah:

```powershell
python -m pytest tests/test_tokenizer.py tests/test_data_pipeline.py tests/test_dataloader.py tests/test_sliding_window.py tests/test_bos_eos.py -v
```

Output aktual: `29 passed in 8.13s` (Python 3.10.6, pytest 9.1.1, torch 2.14.1+cpu; durasi dapat bervariasi antarrun).

Tes baru/penambahan pada D4:

- `test_tokenizer.py::TestTokenizerOrder::test_encode_preserves_text_order` — `encode` mengikuti urutan teks, bukan urutan vocab.
- `test_tokenizer.py::TestTokenizerOrder::test_vocab_size_equals_specials_plus_unique_train_tokens` — `vocab_size = 4 + token unik train`.
- `test_data_pipeline.py::test_sliding_window_exact_count_and_stride_one` — jumlah window `L - (T+1) + 1`, pergeseran stride 1, `x=ids[:T]`, `y=ids[1:T+1]`.
- `test_data_pipeline.py::test_no_cross_document_windows_for_long_documents` — setiap sample adalah suburutan kontigu satu dokumen (bos hanya di awal, eos hanya di akhir window).
- `test_data_pipeline.py::test_dataloader_padding_is_trailing_and_correct_dtype` — padding hanya di kanan, posisi pad `x`/`y` identik, dtype `int64`.
- `test_data_pipeline.py::test_decode_specials_only_returns_empty_string` — `decode` special-only/`[]` menghasilkan string kosong.
- `test_data_pipeline.py::test_fit_with_multiple_documents_counts_across_corpus` — frekuensi dihitung lintas dokumen korpus train.

Perbaikan asersi lemah: `test_lowercase_and_regex` sebelumnya memakai `assert ... or True` (selalu lolos) dan kini memeriksa bahwa `encode("a,b") == encode("a , b")`.

### Subtask D5 — Tes Positional Encoding dan causal masking

Perintah:

```powershell
python -m pytest tests/test_positional_encoding.py tests/test_causal_masking.py -v
```

Output aktual: `24 passed in 12.55s` (Python 3.10.6, pytest 9.1.1, torch 2.14.1+cpu).

Tes baru pada D5 (`tests/test_positional_encoding.py::TestPositionalEncodingContract`, 6 tes):

- `test_buffer_is_registered_and_not_trainable` — `named_parameters()` kosong dan `pe` terdaftar sebagai buffer non-trainable.
- `test_same_offset_for_every_batch_item` — `out[b] - x[b] == pe[:T]` untuk setiap item batch (offset posisi tidak tercampur antarbatch).
- `test_forward_does_not_mutate_input` — `forward` tidak mengubah tensor input.
- `test_gradient_is_identity` — gradien `d out / d x` bernilai 1 (PE tidak memblokir aliran gradien residual).
- `test_deterministic_in_train_and_eval` — keluaran identik pada `train()` dan `eval()`.
- `test_max_len_boundary_at_baseline` — `T = max_len = 64` lolos; `T = 65` melempar `ValueError`.

Tes baru pada `tests/test_causal_masking.py` (8 tes, diuji lewat `forward` publik, dropout 0 + `eval()`):

- `test_every_cut_leaves_past_unchanged` — untuk setiap titik potong `k`, mengubah `x[:, k:]` tidak mengubah `out[:, :k]`, sementara `out[:, k:]` berubah.
- `test_past_perturbation_changes_its_own_output` — kontrol sensitivitas: mengubah posisi 0 mengubah output posisi 0.
- `test_forward_matches_manual_reference` — keluaran `forward` sama dengan perhitungan manual (proyeksi → skala → mask → softmax → `@V` → `W_o`).
- `test_future_probability_is_exactly_zero` — `probs[..., j > i] == 0.0` eksak dan tiap baris berjumlah 1.
- `test_first_position_attends_only_to_itself` — posisi 0 hanya memberi bobot 1 ke dirinya sendiri.
- `test_single_position_has_no_future` — `T = 1`: output = `W_o(W_v(x))`, finite, tanpa NaN.
- `test_float64_input_keeps_dtype_and_causality` — model/input `float64` menghasilkan output `float64` dan invariance tetap berlaku.
- `test_large_scores_remain_finite` — input magnitudo `1e2` menghasilkan output finite dan probs tanpa NaN dengan baris berjumlah 1.

Catatan debugging aktual: run pertama D5 gagal pada `test_same_offset_for_every_batch_item` dengan `Greatest absolute difference: 1.103617250919342e-07` (2/512 elemen). Penyebab: pembulatan `float32` pada `(x + pe) - x`, bukan bug modul. Perbaikan: toleransi uji disamakan ke `atol=1e-6, rtol=1e-5` (setara toleransi yang dipakai tes pemilik modul). Setelah perbaikan: lulus.

Seluruh suite setelah D5:

```powershell
python -m pytest -q
```

Output aktual: `117 passed in 18.06s` (103 tes sebelum D5 + 14 tes baru).

### Subtask D6 — Tes Decoder Block dan MiniGPT

Perintah:

```powershell
python -m pytest tests/test_decoder_block_contract.py tests/test_minigpt_contract.py -v
```

Output aktual: `27 passed in 11.02s` (Python 3.10.6, pytest 9.1.1, torch 2.14.1+cpu).

Tes baru (13 tes Decoder Block + 14 tes MiniGPT), semuanya di level `forward` publik:

`tests/test_decoder_block_contract.py`:

- `TestDecoderBlockStructure::test_baseline_hyperparameters` — `pre_norm=True`, `d_ff=256`, `head_dim=16`, LayerNorm epsilon `1e-5`.
- `TestDecoderBlockStructure::test_ffn_projection_sizes_follow_d_ff` — `fc1` `[d_ff, d_model]`, `fc2` `[d_model, d_ff]`.
- `TestDecoderBlockStructure::test_block_registers_no_positional_buffers` — tidak ada buffer; PE bukan bagian block.
- `TestDecoderBlockForwardShape::test_baseline_shape_and_finite` / `test_single_position` — `[2,64,64] -> [2,64,64]` dan `T=1` finite.
- `TestResidualConnectionContract::test_zeroed_parameters_make_block_identity` — seluruh parameter dinolkan → `out == x` eksak (residual aditif, bukan penggantian).
- `TestResidualConnectionContract::test_identity_path_keeps_gradient_one` — `d out / d x == 1` eksak; jalur identitas tidak memblokir gradien.
- `TestCausalMaskingThroughBlock::test_every_cut_leaves_past_unchanged` — untuk `k ∈ {1, 8, 32, 63}`, mengubah `x[:, k:]` tidak mengubah `out[:, :k]` (`atol=0`).
- `TestCausalMaskingThroughBlock::test_past_perturbation_changes_its_own_output` / `test_future_perturbation_changes_future_output` — kontrol sensitivitas agar invariance bukan hasil jaringan "mati".
- `TestPositionIndependence::test_identical_positions_produce_identical_outputs` — input identik di semua posisi → output identik; block tidak menambahkan posisi (PE ada di MiniGPT).
- `TestBatchIndependence::test_perturbing_one_item_does_not_change_other_items` — item batch lain tidak berubah eksak; item yang diubah berubah.
- `TestNoContextLengthGuard::test_longer_sequences_still_forward` — `T=65` dan `T=128` valid; guard `context_length` hanya milik MiniGPT.

`tests/test_minigpt_contract.py`:

- `TestMiniGPTStructure::test_component_types_and_baseline_hyperparameters` — 2 `DecoderBlock` dengan `d_ff=256`, `SinCosPositionalEncoding`, `ln_f` epsilon `1e-5`.
- `TestMiniGPTStructure::test_lm_head_is_not_tied_to_embedding` — bobot LM head `[V, d]` terpisah (`data_ptr` berbeda), tanpa bias.
- `TestMiniGPTStructure::test_positional_encoding_buffer_shape` — buffer `pos_enc.pe` `[64, 64]`, non-trainable.
- `TestMiniGPTForwardShape::test_baseline_shape_dtype_finite` / `test_single_token_sequence` — `[2,64] int64 -> [2,64,100] float32` finite, termasuk `T=1`.
- `TestMiniGPTContextGuard::test_boundary_at_baseline_context_length` — `T=64` lolos, `T=65` `ValueError`.
- `TestMiniGPTContextGuard::test_guard_uses_configured_context_length` — `context_length=8`: `T=8` lolos, `T=9` `ValueError`; `context_length=128` menerima `T=128` (bukan hardcode 64).
- `TestMiniGPTCausality::test_every_cut_leaves_past_unchanged` — invariance causal menembus Embedding + PE + 2 block + LN akhir + head (`atol=0`).
- `TestMiniGPTCausality::test_last_position_reacts_to_last_token` — kontrol sensitivitas.
- `TestPositionalEncodingIsApplied::test_identical_tokens_at_different_positions_give_different_logits` — token sama di posisi 0/1/2 menghasilkan logits berbeda; membuktikan PE benar-benar ditambahkan.
- `TestMiniGPTGradients::test_all_parameters_receive_finite_nonzero_gradient` — seluruh parameter (embedding, semua block, `ln_f`, `lm_head`) punya gradien finite dan nonzero.
- `TestMiniGPTGradients::test_embedding_gradient_reaches_used_token_ids_only` — gradien embedding hanya pada id yang dipakai.
- `TestDropoutBehavior::test_eval_is_deterministic_and_train_differs` — `eval()` dua forward identik eksak; `train()` (dropout 0.1) berbeda.
- `TestMiniGPTInitValidation::test_value_error_when_d_model_not_divisible_by_n_heads` — `ValueError` saat `d_model=64, n_heads=3`.

Nilai tambah dibanding tes pemilik modul: tes Issue B/C memeriksa shape, dtype, guard, dropout, dan kesetaraan pre/post-norm; D6 membuktikan sifat kontraktual (residual aditif, gradien identitas, causality lintas block/model, PE benar-benar dipakai, LM head tidak di-tie) dan guard `context_length` yang terkonfigurasi.

#### Debugging aktual D6

Run pertama (`python -m pytest tests/test_decoder_block_contract.py tests/test_minigpt_contract.py -v`): `3 failed, 24 passed in 10.34s`.

1. `TestPositionIndependence::test_identical_positions_produce_identical_outputs` gagal dengan `Greatest absolute difference: 2.384185791015625e-07` (28/64 elemen) saat memakai `atol=0`. Penyebab: jumlah suku softmax bertambah dengan posisi sehingga penjumlahan `float32` berbeda urutan/panjang, bukan pelanggaran kontrak. Perbaikan: toleransi `atol=1e-6, rtol=1e-5` (setara preseden pembulatan `float32` pada D5).
2. `TestBatchIndependence::test_perturbing_one_item_does_not_change_other_items` gagal karena asersi uji salah: item batch 0 (yang sengaja diubah) diperiksa "tidak berubah". Perbaikan: item 0 harus berubah (`assertFalse(allclose)`), item 1 harus identik eksak.
3. `TestMiniGPTStructure::test_positional_encoding_buffer_shape` gagal `KeyError: 'pe'` karena buffer milik submodul sehingga nama terdaftarnya `pos_enc.pe`. Perbaikan: kunci `pos_enc.pe`.

#### Kontrol negatif (verifikasi tes tidak lolos palsu)

Skrip sementara di luar repo (`%TEMP%\kilo\mutation_check.py`) menjalankan ulang invariansi causal block/model, lalu mengganti `_causal_mask` menjadi nol pada proses yang sama. Output aktual:

```text
causal intact   -> block fails: False model fails: False
mask removed    -> block fails: True model fails: True
```

Artinya tes causality D6 benar-benar gagal bila causal mask dihilangkan. `src/` tidak diubah permanen.

Seluruh suite setelah D6:

```powershell
python -m pytest -q
```

Output aktual: `144 passed in 16.26s` (117 tes sebelum D6 + 27 tes baru). Subset regresi model: `python -m pytest tests/test_decoder_block.py tests/test_decoder_block_contract.py tests/test_causal_masking.py tests/test_minigpt_logits.py tests/test_minigpt_contract.py tests/test_minigpt_mock.py -q` → `57 passed in 10.66s`.

#### Perbaikan helper (di luar `src/`)

`tests/helpers.py::make_model("minigpt")` sebelumnya meneruskan `d_ff` ke `MiniGPT`, yang tidak memiliki parameter tersebut (`TypeError: MiniGPT.__init__() got an unexpected keyword argument 'd_ff'`), sehingga helper tidak pernah bisa membuat MiniGPT. Perbaikan: argumen `d_ff` tidak diteruskan; nilai `d_ff` memang ditetapkan internal `4 * d_model` (TECH_SPEC §6). Verifikasi: `make_model('minigpt')` → `MiniGPT 2 256 torch.Size([100, 64])`. Tidak ada perubahan kontrak `src/`.


### Subtask D7 — Tes training step, loss, dan pembaruan parameter

Perintah:

```powershell
python -m pytest tests/test_training_contract.py -v
```

Output aktual: `18 passed in 14.66s` (Python 3.10.6, pytest 9.1.1, torch 2.14.1+cpu).

File baru `tests/test_training_contract.py` melengkapi `tests/test_training_step.py` milik Issue C (subtask C8) — file pemilik modul tidak diubah. Model uji: `MiniGPT(vocab_size=16, n_layers=2, n_heads=2, d_model=8, context_length=8, dropout=0.0)`; batch `x, y [2, 6]` yang konsisten dengan `TECH_SPEC.md` §4 (`y[:,0]` pad, `x[i,t] == y[i,t-1]` pada posisi non-pad, pad trailing).

`TestTrainingStepLoss` (4 tes):

- `test_batch_is_contract_consistent_before_use` — batch uji benar-benar memenuhi relasi shift §4 sebelum dipakai sebagai bukti.
- `test_training_step_returns_finite_python_float` — mengembalikan `float` Python dan finite.
- `test_returned_loss_matches_cross_entropy_of_step_logits` — forward hook menangkap logits step itu; loss yang dikembalikan sama dengan `F.cross_entropy(flat logits, flat y, ignore_index=pad_id)`. Kontrol: tanpa `ignore_index` nilainya berbeda, sehingga tes sensitif.
- `test_returned_loss_is_detached_from_graph` — nilai balik berupa skalar Python, bukan tensor ber-grad.

`TestPadTargetIgnoredInLoss` (4 tes):

- `test_perturbing_pad_row_logits_does_not_change_loss` — logits kelas target pada baris `pad_id` diturunkan ekstrem (`-100`) dan loss tetap identik eksak. Kontrol anti-vakum: dengan `ignore_index=-100` perturbasi yang sama mengubah loss.
- `test_perturbing_nonpad_row_logits_changes_loss` — kontrol sensitivitas pada baris non-pad.
- `test_custom_pad_id_is_ignored_too` — `pad_id=5` diabaikan dengan nilai sama seperti `ignore_index=5` manual, dan berbeda dari criterion default `pad_id=0` → `pad_id` benar-benar diparameterkan.
- `test_gradient_is_zero_at_pad_target_positions` — `logits.grad` tepat nol pada posisi target pad dan nonzero pada posisi non-pad → pad tidak mengalir ke pembaruan parameter.

`TestParameterUpdate` (7 tes):

- `test_every_trainable_parameter_changes_after_one_step` — seluruh `named_parameters()` berubah dan finite setelah satu step AdamW.
- `test_zero_lr_control_leaves_parameters_unchanged` — kontrol negatif `lr=0`: parameter identik bitwise.
- `test_optimizer_records_one_step_for_all_parameters` — state optimizer mencakup semua parameter dengan `step == 1`.
- `test_second_step_advances_optimizer_state` — step kedua menaikkan counter dan mengubah parameter lagi.
- `test_model_is_in_train_mode_after_step` — `training_step` memanggil `model.train()` (dari kondisi `eval()`).
- `test_overfitting_one_batch_reduces_loss` — 25 step pada batch tetap menurunkan loss (arah optimisasi benar).
- (kontrol negatif di atas melengkapi bukti bahwa perubahan berasal dari `optimizer.step()`).

`TestTrainingReproducibility` (2 tes):

- `test_seed_42_reproduces_loss_and_parameters` — dua run dengan `set_seed(42)` dan dropout `0.1` menghasilkan loss identik dan parameter identik → kontrak seed §6.
- `test_different_seed_reproduces_differently_with_dropout` — kontrol: seed 7 menghasilkan loss dan parameter berbeda.

`TestTrainingStepGuards` (2 tes):

- `test_context_length_guard_applies_and_keeps_parameters` — `T=9 > context_length=8` melempar `ValueError` lewat jalur training, parameter tidak berubah, dan state optimizer tetap kosong.
- `test_error_and_pad_only_target_relationship_is_documented` — keterbatasan terdokumentasi: target seluruhnya `pad_id` menghasilkan loss `nan` (perilaku `nn.CrossEntropyLoss(ignore_index=...)` bila tidak ada target yang dihitung). `training_step` tidak memiliki guard dan `TECH_SPEC.md` §5 tidak mengaturnya; tes ini mencatat perilaku aktual, bukan menetapkan kontrak baru.

#### Debugging aktual D7

Run pertama (`python -m pytest tests/test_training_contract.py -v`): `2 failed, 16 passed in 16.68s`.

1. `test_perturbing_nonpad_row_logits_changes_loss` gagal dengan pesan `AssertionError: tensor(True) is not false`. Penyebab: perturbasi `+= 100.0` diterapkan ke **semua kelas** sehingga hanya menggeser logits secara seragam; softmax invarian terhadap pergeseran seragam, jadi loss tidak berubah. Ini juga berarti asersi pasangan (baris pad) berpotensi lolos palsu. Perbaikan: perturbasi diarahkan ke satu kelas (kelas target pad untuk baris pad, kelas non-target untuk baris non-pad) dan ditambahkan kontrol anti-vakum memakai `ignore_index=-100`.
2. `test_context_length_guard_applies_and_keeps_parameters` gagal dengan `AssertionError: 7 != 9`. Penyebab: batch uji memiliki `T=6`, lalu ditambah satu kolom menjadi 7 — belum melewati `context_length=8`. Perbaikan: batch guard dibuat eksplisit `T = context_length + 1 = 9`.

Setelah perbaikan: `18 passed in 14.66s`. Tidak ada perubahan `src/`, kontrak, atau dependency.

#### Kontrol negatif (verifikasi tes tidak lolos palsu)

Skrip sementara di luar repo (`%TEMP%\kilo\d7_mutation_check.py`) menjalankan `training_step` yang sama dengan `ignore_index` berbeda. Output aktual:

```text
ignore_index=pad(0)    pad affects loss: False  pad grad zero: True
ignore_index=-100      pad affects loss: True   pad grad zero: False
```

Artinya asersi "posisi pad diabaikan di loss" dan "gradien nol di posisi pad" benar-benar bergantung pada `ignore_index=pad_id` (gagal bila masking dihilangkan). `src/` tidak diubah permanen.

Seluruh suite setelah D7:

```powershell
python -m pytest -q
```

Output aktual: `162 passed in 22.63s` (144 tes sebelum D7 + 18 tes baru). Subset regresi training: `python -m pytest tests/test_training_step.py tests/test_training_contract.py tests/test_train_integration.py tests/test_checkpoint.py -q` → `21 passed in 16.02s`. Run dengan `--run-integration` → `162 passed in 20.96s`.

## Catatan Teknis

- Tidak ada penambahan dependency baru (pytest sudah terdaftar di `requirements.txt`).
- Koleksi tes memerlukan PyTorch terpasang. Jika modul A/B/C belum tersedia, tes yang mengimpor modul tersebut akan gagal dengan `ImportError` saat koleksi — bukan kegagalan tes.
- Tes menggunakan giga campuran `unittest.TestCase` dan fungsi `pytest` murni; keduanya dijalankan oleh pytest secara bersamaan.
- File `tests/conftest.py` menambahkan root repo ke `sys.path`, menambahkan opsi `--run-integration`, dan menyediakan fixture `base_config`, `batch`, dan `special_ids`.
