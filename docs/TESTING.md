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

Snapshot historis (D5, bukan status terkini): **117 passed** setelah D5 (103 passed sebelum D5; torch 2.14.1+cpu via `.venv`). Status terkini yang benar-benar dijalankan ada pada bagian **Subtask D12** di bawah dan pada [`docs/D12_TESTING_REPORT.md`](D12_TESTING_REPORT.md) §1.3.

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

Modul dari Issues A, B, dan C sudah tersedia, sehingga seluruh tes dikoleksi tanpa `ImportError`.

Catatan status (D8, terverifikasi): penanda `integration` terdaftar di `pytest.ini` dan mekanisme skip-nya ada di `tests/conftest.py`, tetapi **belum ada satu pun tes yang memakai `@pytest.mark.integration`**. Akibatnya `-q --run-integration` menjalankan 162 tes yang sama dengan `-q` biasa. Penandaan tes integrasi yang sesungguhnya belum diputuskan dan berada di luar scope D8 (kandidat: D11).

Status terkini (**D11**, 2026-10-24): marker `integration` sudah dipakai oleh **15 tes** di tiga berkas (`test_end_to_end_pipeline.py` 7, `test_integration_components.py` 7, `test_train_integration.py` 1). `python -m pytest -q` menjalankan 154 tes dan melewati 15 tes integrasi; `python -m pytest -q --run-integration` menjalankan seluruh 169 tes.

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

### Subtask D8 — Status tes lintas modul (eksekusi aktual)

Eksekusi: 2026-10-24 19:40–19:47 WIB pada `master` @ `ffc5372`, tanpa perubahan pada `src/` maupun file tes. Environment: Python 3.10.6, pytest 9.1.1, torch 2.14.1+cpu (`.venv`), CPU-only, Windows PowerShell.

Seluruh modul Issue A, B, dan C sudah tersedia di repository, sehingga eksekusi dijalankan atas kode nyata (bukan stub) dan tidak ada `ImportError` saat koleksi. D8 tidak menambah tes baru; ia menjalankan suite yang sudah ada dan mencatat hasil aktual per modul.

#### Ringkasan grup

| Grup | File tes | Tes | Command (dirangkum) | Output aktual | Status |
|---|---|---:|---|---|---|
| Modul A — data pipeline & tokenizer | 6 | 31 | `python -m pytest tests/test_tokenizer.py tests/test_data_pipeline.py tests/test_dataloader.py tests/test_sliding_window.py tests/test_bos_eos.py tests/test_data_split.py -v` | `31 passed in 12.61s` | PASS |
| Modul B — komponen inti transformer | 6 | 90 | `python -m pytest tests/test_positional_encoding.py tests/test_attention.py tests/test_causal_masking.py tests/test_decoder_block.py tests/test_decoder_block_contract.py tests/test_integration_components.py -v` | `90 passed in 20.52s` | PASS |
| Modul C — MiniGPT, training, generation | 8 | 41 | `python -m pytest tests/test_minigpt_logits.py tests/test_minigpt_mock.py tests/test_minigpt_contract.py tests/test_training_step.py tests/test_training_contract.py tests/test_checkpoint.py tests/test_generation_stop.py tests/test_train_integration.py -v` | `41 passed in 20.44s` | PASS |
| Suite penuh | 20 | 162 | `python -m pytest -q` | `162 passed in 23.53s` | PASS |
| Suite + mode integrasi | 20 | 162 | `python -m pytest -q --run-integration` | `162 passed in 23.57s` | PASS (identik, lihat keterbatasan 1) |

Konsistensi: `31 + 90 + 41 = 162` sama dengan jumlah tes yang dikoleksi suite penuh. Tidak ada `failed`, `error`, `skipped`, atau `xfail` pada kelima run.

#### Rincian per file (jumlah tes aktual hasil koleksi)

| Modul | File | Tes | Perilaku yang dibuktikan |
|---|---|---:|---|
| A | `test_tokenizer.py` | 6 | id special 0–3, lowercase + regex `\w+\|[^\w\s]`, fallback `<unk>`, urutan id mengikuti teks, `vocab_size = 4 + token unik train`, tanpa vocab leakage (train vs val/test) |
| A | `test_data_pipeline.py` | 17 | `x[i,t] == y[i,t-1]`, padding hanya di kanan + dtype `int64`, jumlah window `L-64` stride 1, tidak ada window lintas dokumen, dokumen kosong/1 token dibuang, `decode` melewati special |
| A | `test_dataloader.py` | 2 | batch `[B, 64]` lewat collate `pad_id=0`, teks lebih panjang dari konteks |
| A | `test_sliding_window.py` | 3 | dokumen panjang/pendek, no cross-document leak, dokumen kosong dan pendek |
| A | `test_bos_eos.py` | 1 | `<bos>`/`<eos>` disisipkan sebagai id setelah tokenisasi |
| A | `test_data_split.py` | 2 | normalisasi teks; split 720/80/200 seed 42 dan nol irisan train/val/test dari berkas `data/raw` nyata |
| B | `test_positional_encoding.py` | 16 | shape `[B,T,d]`, buffer `pe` non-trainable, rumus sin/cos, `ValueError` saat `T > max_len`, offset sama tiap item batch, gradien identitas |
| B | `test_attention.py` | 28 | shape proyeksi Q/K/V/O, skala `1/sqrt(head_dim)`, mask segitiga atas `-inf`, invariance causal + kontrol `test_invariance_fails_without_mask`, `ValueError` saat `d_model % n_heads != 0` |
| B | `test_causal_masking.py` | 8 | invariance per titik potong, probabilitas masa depan tepat 0, posisi 0 hanya ke diri sendiri, `T=1`, float64, skor besar tetap finite |
| B | `test_decoder_block.py` | 18 | FFN GELU + shape `d_ff`, pre/post-norm manual, residual, dropout train vs eval, gradien ke seluruh parameter |
| B | `test_decoder_block_contract.py` | 13 | pre-norm baseline, residual aditif (parameter nol → `out == x`), gradien identitas, causality menembus block, tanpa guard `context_length` |
| B | `test_integration_components.py` | 7 | PE → MHA → DecoderBlock sebagai satu alur, gradient flow, tidak ada `nn.Transformer*`/`nn.MultiheadAttention` pada jalur inti |
| C | `test_minigpt_logits.py` | 2 | logits `[B,T,V]` float32, `ValueError` saat `T > context_length` |
| C | `test_minigpt_mock.py` | 2 | alur `[B,T] -> [B,T,V]` dengan stub (by design C4, bukan bukti integrasi komponen nyata) |
| C | `test_minigpt_contract.py` | 14 | struktur 2 block, LM head tidak di-tie, buffer `pos_enc.pe`, guard `context_length` terkonfigurasi, causality end-to-end, PE benar-benar dipakai, semua parameter bergradien |
| C | `test_training_step.py` | 1 | satu step memperbarui parameter |
| C | `test_training_contract.py` | 18 | loss = CE manual dengan `ignore_index=pad_id`, baris pad tidak memengaruhi loss/gradien, semua parameter berubah, kontrol `lr=0`, seed 42 reproduktif |
| C | `test_checkpoint.py` | 1 | roundtrip `state_dict` + `vocab` + `config` |
| C | `test_generation_stop.py` | 2 | berhenti pada `<eos>` dan pada `max_new_tokens` |
| C | `test_train_integration.py` | 1 | `Tokenizer` + `TextDataset` + `create_dataloader` + `train` nyata (Issue A) dalam satu epoch, train/val loss finite |

#### Keterbatasan yang tercatat pada D8

1. **Penanda `integration` belum dipakai satu tes pun.** `pytest.ini` mendaftarkan marker dan `tests/conftest.py` menyediakan mekanisme skip, tetapi tidak ada `@pytest.mark.integration` di `tests/`. Bukti: `-q` dan `-q --run-integration` sama-sama `162 passed` dengan daftar tes identik. Penandaan yang benar menuntut perubahan file tes dan berada di luar scope D8 (kandidat D11).
2. **`test_minigpt_mock.py` bukan bukti integrasi.** Tes ini sengaja memakai stub (subtask C4). Rangkaian komponen nyata dibuktikan `test_minigpt_contract.py` (14 tes) dan `test_integration_components.py` (7 tes).
3. **`test_data_split.py::test_splits_and_leakage` bergantung pada berkas data.** Tes membaca `data/raw/*.jsonl` (tracked) dan menulis ulang `data/processed/*.jsonl`. Setelah run, `git status` tetap bersih, jadi hasil split deterministik (seed 42); namun bila berkas `data/raw/` hilang, tes gagal `FileNotFoundError`, bukan gagal kontrak.
4. **Belum ada eksekusi penuh atas `data/processed/` (720/80/200)** maupun pemuatan checkpoint eksperimen C14 di dalam suite. Cakupan integrasi data nyata end-to-end dijadwalkan D11.
5. **Durasi bervariasi antarrun.** Angka di atas adalah output run D8; run lain pada mesin yang sama mencatat durasi berbeda (mis. modul A 10.95s–12.61s) tanpa perubahan hasil.
6. **CPU-only.** Tidak ada uji CUDA, mixed precision, atau multi-GPU. Versi dependency di luar environment ini tidak diverifikasi.

### Subtask D9 — Identifikasi error dan bukti reproduksi

Eksekusi: 2026-10-24 19:58–20:11 WIB pada `master` @ `266c611`, tanpa perubahan `src/`, file tes,
atau kontrak publik. Environment: Python 3.10.6, pytest 9.1.1, torch 2.14.1+cpu (`.venv`), CPU-only.

Bukti lengkap (perintah, output/traceback, langkah reproduksi, pemilik, status) ada di
[`docs/D9_FAILURE_LOG.md`](D9_FAILURE_LOG.md). Bagian ini hanya ringkasan.

#### Baseline ulang

| Perintah | Output aktual | Status |
|---|---|---|
| `python -m pytest -q` | `162 passed in 24.32s` | PASS |
| `python -m pytest -q --run-integration` | `162 passed in 27.59s` | PASS (identik) |
| Modul A (6 file) | `31 passed in 12.74s` | PASS |
| Modul B (6 file) | `90 passed in 19.49s` | PASS |
| Modul C (8 file) | `41 passed in 21.76s` | PASS |

**Tidak ada kegagalan suite pada baseline.** Karena itu D9 menelusuri jalur yang tidak dicakup
suite dan mereproduksinya di luar repo (`%TEMP%\kilo\d9\`), bukan mengandalkan status hijau suite.

#### Temuan (ringkas)

| ID | Severity | Ringkasan | Pemilik | Bukti |
|---|---|---|---|---|
| F-D9-01 | Tinggi (silent) | Restore checkpoint sesuai `README.md:276-286` menyisakan `id_to_token` kosong dan `vocab_size=0` → `generate()` = `''` tanpa error | C (+A) | R1, R3b |
| F-D9-02 | Sedang | `src/generate.py:8` memakai `context_length=64` hardcode → `ValueError: sequence length T=9 exceeds context_length=8` untuk model `context_length=8` | C | R2 |
| F-D9-03 | Sedang (kontrak) | Signature `generate` berbeda dari `TECH_SPEC.md:105` | C + koordinator | statis + R2 |
| F-D9-04 | Rendah | `src/train.py:31` merujuk ADR-014 yang tidak ada | C / dokumen | statis |
| F-D9-05 | Rendah | Laporan D1 mengklaim 3 dokumen `docs/` yang tidak ada (sudah dilaporkan di D5) | D | statis |
| F-D9-06 | Rendah | README menunjuk `outputs/metrics/full/minigpt_c14.pt` yang tidak ada di repo/working tree | C / D | statis |

Kontrol negatif dipakai agar temuan tidak lolos palsu: F-D9-01 dikontrol dengan tokenizer yang
`id_to_token`-nya diisi (decode kembali `'presiden indonesia'`, generate non-kosong); F-D9-02
dikontrol dengan `context_length=model.context_length` (berjalan normal) dan R2b menunjukkan
sliding window baseline (64) tetap bekerja untuk prompt 100 token.

#### Mengapa suite hijau tetapi ada defect

| Gap cakupan | Bukti |
|---|---|
| Tidak ada tes restore tokenizer dari checkpoint → `generate` | `tests/test_checkpoint.py:12-23` hanya memeriksa `state_dict`/`vocab`/`config` |
| Generation diuji dengan stub model & stub tokenizer | `tests/test_generation_stop.py:8-28` |
| Tidak ada tes `generate` pada `model.context_length != 64` | seluruh tes generation memakai 64 |
| Tidak ada tes `max_new_tokens=0` | perilaku aktual: mengembalikan prompt saja |

D9 tidak menambah file tes: tes yang mengunci perilaku buggy akan melegalkan bug, dan tes yang gagal
akan memerahkan suite bersama sebelum pemilik modul memperbaiki serta sebelum ada keputusan
(perbaikan kode modul berada di luar scope D9 per Issue D §4, dan §9 meminta berhenti lalu melapor).
Usulan tes regresi per temuan sudah dicantumkan di `docs/D9_FAILURE_LOG.md` untuk dipakai pada D10/D11.

### Subtask D10 — Verifikasi perbaikan berdasarkan tes aktual

Eksekusi: 2026-10-24 20:51–21:03 WIB pada `master` @ `b5c2b80`, tanpa perubahan `src/`,
`tests/`, `README.md`, atau kontrak publik. Environment: Python 3.10.6, pytest 9.1.1,
torch 2.14.1+cpu (`.venv`), CPU-only.

Bukti lengkap (perintah, output aktual, kontrol negatif, kriteria penutupan) ada di
[`docs/D10_FIX_VERIFICATION.md`](D10_FIX_VERIFICATION.md). Bagian ini hanya ringkasan.

#### Prasyarat D10 belum terpenuhi

D10 berbunyi "setelah pemilik modul memperbaiki". Pada `b5c2b80` belum ada perbaikan:
`git diff --stat b5c2b80 HEAD -- src tests README.md` kosong, commit terakhir yang menyentuh
`src/` adalah `4c7d670` (sebelum D9), `Tokenizer.from_vocab` tidak ada, dan
`inspect.signature(generate).parameters["context_length"].default` masih `64`.

Dengan persetujuan anggota, D10 dijalankan sebagai **verification attempt**: seluruh probe D9
dijalankan ulang untuk mencatat status aktual. Hasil: **0 dari 6 temuan tertutup**.

#### Baseline suite (masih hijau pada commit yang sama)

| Perintah | Output aktual | Status |
|---|---|---|
| `python -m pytest -q` | `162 passed in 26.37s` | PASS |
| `python -m pytest -q --run-integration` | `162 passed in 24.90s` | PASS (identik) |
| `python -m pytest -q` (setelah seluruh probe) | `162 passed in 25.08s` | PASS |

#### Status temuan

| ID | Status D10 | Bukti ringkas |
|---|---|---|
| F-D9-01 | OPEN | restore README → `id_to_token 0`, `vocab_size 0`, `decode ''`, `generate ''`; kontrol (pemetaan diisi) berfungsi; `MiniGPT(vocab_size=0)` → `ValueError`; gejala identik pada checkpoint nyata (vocab 3.981) |
| F-D9-02 | OPEN | default `context_length=64`; model `context_length=8` → `ValueError: sequence length T=9 exceeds context_length=8`; kontrol eksplisit berfungsi |
| F-D9-03 | OPEN | spec 2 parameter vs implementasi 7 parameter; keduanya tidak berubah sejak D9 |
| F-D9-04 | OPEN | `src/train.py:31` masih merujuk `ADR-014`; ADR hanya 001–012 |
| F-D9-05 | OPEN | tiga dokumen yang diklaim laporan D1 tetap `Test-Path` `False` |
| F-D9-06 | OPEN | `outputs/` tidak ada di working tree |

#### Penajaman: F-D9-02 intermiten

D9 melaporkan guard terpicu pada token ke-7. D10 menguji 10 seed: **7/10 seed melempar
`ValueError`**, sedangkan 3/10 berhenti lebih dulu karena `<eos>` (seed 2, 6, 7). Jadi reprouksi
D9 valid tetapi tidak deterministik. Tes regresi untuk temuan ini wajib menetralkan `<eos>`
(mis. `eos_id=-1`); jika tidak, tes menjadi flaky dan bisa lolos palsu.

#### Gap cakupan yang membuat suite tetap hijau

Empat pemeriksaan cakupan masih `False` pada `tests/`: (1) `generate()` dengan tokenizer hasil
restore, (2) `generate()` dengan `context_length != 64`, (3) `max_new_tokens=0`, (4) MiniGPT
`context_length != 64` + generate. Karena itu `162 passed` tidak membantah F-D9-01/F-D9-02.

#### Catatan tentang unit test

D10 tidak menambahkan file tes ke `tests/`: persetujuan yang diberikan adalah *verification
attempt* tanpa memerahkan suite bersama, dan menambahkan tes yang mengunci perilaku buggy akan
melegalkan bug. Dua tes regresi kandidat (dengan `<eos>` dinetralkan) sudah ditulis lengkap di
`docs/D10_FIX_VERIFICATION.md` §12 untuk dipakai pada D11 setelah modul diperbaiki.

### Subtask D11 — Tes integrasi lintas modul dalam satu run

Eksekusi: 2026-10-24 21:15–21:45 WIB pada `master` @ `68ff3df` (tanpa operasi Git).
Environment: Python 3.10.6, pytest 9.1.1, torch 2.14.1+cpu (`.venv`), CPU-only.
Tidak ada perubahan `src/`, kontrak publik, `pytest.ini`, atau dependency.

#### Cakupan integrasi

Marker `integration` kini benar-benar dipakai. Tes integrasi menjalankan komponen **nyata** dari
Issues A, B, dan C dalam satu alur, tanpa stub model/tokenizer untuk jalur utama:

| Berkas | Tes | Alur yang diintegrasikan |
|---|---:|---|
| `tests/test_end_to_end_pipeline.py` (baru) | 7 | `Tokenizer.fit` → `TextDataset` → `create_dataloader` → `MiniGPT.forward` → `CrossEntropyLoss(ignore_index=0)` → `backward`/`optimizer.step` → `generate` |
| `tests/test_integration_components.py` | 7 | `SinCosPositionalEncoding` → `CausalMultiHeadAttention` → `DecoderBlock` (gradient, tidak ada `nn.Transformer*`) |
| `tests/test_train_integration.py` | 1 | `Tokenizer` + `TextDataset` + `create_dataloader` + `train` nyata, satu epoch kecil |
| **Total** | **15** | |

Perilaku yang dibuktikan (bukan sekadar "tidak error"):

1. **Shape dan relasi shift.** Batch `x`/`y` `[4, 64]` int64; `x[i,t] == y[i,t-1]` pada posisi
   non-pad; guard `T=65` → `ValueError`; logits `[4, 64, V]` float32 finite.
2. **Padding diabaikan loss.** Batch dengan padding nyata; loss `CrossEntropyLoss(ignore_index=0)`
   dibandingkan dengan rata-rata manual hanya pada posisi non-pad (selisih `1e-6`), dan jumlah
   target pad dipastikan `> 0` agar tes tidak vakum.
3. **Training step nyata.** Gradien `token_emb.weight` dan `lm_head.weight` non-None dan non-nol,
   lalu `optimizer.step()` mengubah kedua parameter tersebut.
4. **Aturan `max_new_tokens`.** Dengan tokenizer nyata dan `<eos>` dinetralkan (`eos_id=-1`),
   jumlah id yang didekode tepat `len(prompt) + max_new_tokens` untuk `max_new_tokens` 0, 3, dan 8.
5. **Aturan berhenti `<eos>`.** `lm_head` diarahkan agar argmax = `eos` (tanpa mengganti model);
   tokenizer nyata dibungkus perekam sehingga terbukti tidak ada token yang ditambahkan setelah
   `<eos>` (id yang didekode tepat sama dengan prompt tanpa `<bos>`).
6. **Sliding window generasi.** Prompt lebih panjang dari `context_length=64` tetap menghasilkan
   output tanpa `ValueError`.
7. **Korpus nyata.** 60 dokumen `data/processed/train.jsonl`: jumlah window dataset **sama persis**
   dengan penjumlahan per dokumen (`len(ids)-64` untuk dokumen ≥ 65 token, 1 untuk dokumen pendek),
   sehingga window lintas dokumen akan membuat tes gagal; satu batch nyata → forward → loss →
   `backward` dengan gradien `lm_head` non-nol.

#### Hasil aktual

| Perintah | Output aktual | Status |
|---|---|---|
| `python -m pytest --collect-only -q --run-integration` | `169 tests collected in 9.87s` | OK |
| `python -m pytest -q` | `154 passed, 15 skipped in 26.13s` | PASS (skip = 15 tes integrasi) |
| `python -m pytest -q --run-integration` | `169 passed in 23.80s` | PASS |
| `python -m pytest -q -m integration --run-integration` | `15 passed, 154 deselected in 20.22s` | PASS |
| `python -m pytest tests/test_end_to_end_pipeline.py -v --run-integration` | `7 passed in 16.91s` | PASS |

Konsistensi jumlah: 154 + 15 = 169 = total koleksi. Tidak ada `failed`, `error`, atau `xfail`.

#### Temuan baru (test-infrastructure, bukan kontrak modul)

**F-D11-01 (rendah): `tests/helpers.py:make_batch` membangun relasi shift terbalik.**
`helpers.make_batch` menetapkan `y[:, 1:] = x[:, :-1]`, yaitu `x[i,t] == y[i,t+1]`, sedangkan
`TECH_SPEC.md` §4 dan dataset nyata memakai `x[i,t] == y[i,t-1]`. Bukti: batch nyata memenuhi
`x[:,1:] == y[:,:-1]` (diverifikasi `test_tokenizer_dataset_model_shapes`), sementara
`test_training_contract.py::_make_batch` memakai arah yang benar sehingga kontrak training tidak
terpengaruh. Dampak saat ini **nol** karena fixture `batch` (satu-satunya pemakai
`helpers.make_batch`) tidak dipakai tes mana pun. Tidak diubah pada D11 agar scope tetap pada
eksekusi integrasi; perlu keputusan pemilik Issue D/koordinator.

#### Temuan D9/D10 yang tetap terbuka

D11 **tidak** menutup F-D9-01…F-D9-06. Jalur restore checkpoint → `generate` dan
`generate` pada `model.context_length != 64` masih tidak dicakup, karena keduanya akan gagal
sampai pemilik Issue C memperbaiki `src/data/tokenizer.py` dan `src/generate.py`. Tes regresi
kandidat tetap disimpan di `docs/D10_FIX_VERIFICATION.md` §12 dan belum dimasukkan ke `tests/`.

#### Keterbatasan

1. CPU-only; tidak ada uji CUDA, mixed precision, atau multi-GPU.
2. Tes korpus nyata memakai 60 dokumen pertama `data/processed/train.jsonl` (bukan 720 penuh) agar
   durasi suite wajar; berkas wajib ada, jika hilang tes gagal eksplisit (`pytest.fail`).
3. Tidak melatih model hingga konvergen; kualitas model tidak diuji, hanya kontrak alur.
4. `max_new_tokens`/stop-`<eos>` diuji dengan arah `lm_head` yang diatur agar deterministik;
   bobot hasil training nyata tidak dipakai untuk menguji aturan berhenti.
5. `test_data_split.py` masih menulis ulang `data/processed/` dan tetap tanpa marker
   `integration` (perilakunya sudah dicatat sebagai keterbatasan D8 nomor 3).

### Subtask D12 — Dokumentasi pengujian dan hasil eksperimen

Eksekusi: 2026-10-24 pada `master` @ `4dbe3a2` (tanpa operasi Git). Environment: Python 3.10.6,
pytest 9.1.1, torch 2.14.1+cpu (`.venv`), CPU-only. Tidak ada perubahan `src/`, `tests/`,
`pytest.ini`, atau dependency.

Dokumen konsolidasi: **[`docs/D12_TESTING_REPORT.md`](D12_TESTING_REPORT.md)**. Isinya:

1. perintah runner dan status suite aktual (default, `--run-integration`, `-m integration`,
   per modul) beserta rekonsiliasi jumlah tes;
2. matriks kontrak → test → status untuk `TECH_SPEC.md` §3–§7, dengan nama
   `file::TestClass::test_name` untuk kontrak wajib (vocab leakage, no-window-crossing,
   causal mask, padding + `ignore_index`, stop generation, checkpoint roundtrip);
3. matriks acceptance criteria Issues #2–#6 → bukti → status;
4. hasil integrasi lintas modul (15 tes ber-marker `integration`);
5. riwayat debugging D4–D11 beserta penyebab dan perbaikan;
6. hasil eksperimen C14 (dikutip dari laporan C14, bukan dijalankan ulang);
7. temuan terbuka dan gap cakupan.

Ringkasan status pada commit tersebut:

| Perintah | Output aktual | Status |
|---|---|---|
| `python -m pytest -q` | `154 passed, 15 skipped in 21.54s` | PASS |
| `python -m pytest -q --run-integration` | `169 passed in 22.67s` | PASS |
| `python -m pytest -q -m integration --run-integration` | `15 passed, 154 deselected in 16.48s` | PASS |
| `python -m pytest --collect-only -q --run-integration` | `169 tests collected in 10.33s` | OK |

Rekonsiliasi: Modul A 31 tes, Modul B 90 tes (7 di antaranya `integration`), Modul C 40 tes,
`test_train_integration.py` 1 tes, `test_end_to_end_pipeline.py` 7 tes → total 169; default
169 − 15 = 154. Durasi pada tabel adalah output run D12 dan bervariasi antarrun; yang stabil
hanya jumlah pass/skip.

Catatan penting: suite hijau **tidak** berarti seluruh kontrak tertutup. F-D9-01 (restore
checkpoint → `generate` kosong), F-D9-02 (`generate` memakai `context_length=64` hardcode),
F-D9-03 (signature `generate` ≠ `TECH_SPEC.md` §6), F-D9-04 (`ADR-014` tidak ada), F-D9-06
(artefak contoh README tidak ada di repo), dan F-D11-01 (`helpers.make_batch` arah shift terbalik)
masih terbuka. Rincian ada di `D12_TESTING_REPORT.md` §6 dan `D9_FAILURE_LOG.md`.

Perubahan file D12: `docs/D12_TESTING_REPORT.md` (baru), `docs/TESTING.md` (bagian ini),
`README.md` §12, dan laporan AI `docs/ai-logs/reports/AI-LOG-rafasuryaputra-80048-IssueD-D12.md`.

## Catatan Teknis

- Tidak ada penambahan dependency baru (pytest sudah terdaftar di `requirements.txt`).
- Koleksi tes memerlukan PyTorch terpasang. Jika modul A/B/C belum tersedia, tes yang mengimpor modul tersebut akan gagal dengan `ImportError` saat koleksi — bukan kegagalan tes.
- Tes menggunakan giga campuran `unittest.TestCase` dan fungsi `pytest` murni; keduanya dijalankan oleh pytest secara bersamaan.
- File `tests/conftest.py` menambahkan root repo ke `sys.path`, menambahkan opsi `--run-integration`, dan menyediakan fixture `base_config`, `batch`, dan `special_ids`.
