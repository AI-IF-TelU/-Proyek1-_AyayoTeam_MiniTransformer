# D13 — Laporan Akhir Berbasis Bukti

**Issue:** [STEP 3] Issue D — Unit Test, Integrasi & Dokumentasi Teknis
**Subtask:** D13. Susun laporan akhir berdasarkan bukti aktual
**Commit saat eksekusi:** `edbf5cc` (`feat(Issue D): Substask D12`), branch `master`
**Tanggal eksekusi:** 2026-10-24 (WIB, UTC+07:00)
**Anggota:** Rafa Suryaputra (rafasuryaputra-80048)

Dokumen ini merekap status acceptance criteria Issues #2–#6 berdasarkan bukti yang **dijalankan
ulang pada commit di atas**, bukan salinan status D12 (`4dbe3a2`). Setiap klaim diberi salah satu
status berikut:

| Status | Arti |
|---|---|
| **TERVERIFIKASI** | Ada tes/perintah yang dijalankan pada `edbf5cc` dan hasilnya diamati langsung |
| **SEBAGIAN** | Sebagian aspek terbukti; aspek lain tidak tercakup tes atau gagal |
| **TIDAK TERVERIFIKASI** | Tidak ada tes/bukti yang dapat dijalankan dari clone ini |
| **DI LUAR KENDALI D13** | Bukti milik anggota/modul lain; tidak diperiksa ulang di sini |

Tiga jenis angka dipisahkan secara eksplisit: (a) **diukur pada D13**, (b) **dikutip** dari dokumen
lain beserta sumbernya, (c) **asumsi/analitis** yang tidak diukur.

---

## 1. Snapshot dan metode

### 1.1 Lingkungan

| Item | Nilai |
|---|---|
| OS / shell | Windows, PowerShell 5.1 |
| Python | 3.10.6 (`.venv\Scripts\python.exe`) |
| pytest | 9.1.1 |
| PyTorch | 2.14.1+cpu |
| NumPy | tersedia (dipakai `src/train.py`) |
| CUDA | tidak tersedia (`torch.cuda.is_available() == False`) |
| Runner | `pytest` + `pytest.ini` (`-ra --strict-markers`, marker `contract`, `integration`) |
| Dependency baru | tidak ada |

### 1.2 Snapshot working tree

```
$ git rev-parse HEAD
edbf5ccfd6b151bd5afc60e15fefee8c2cc8660e
$ git rev-parse --abbrev-ref HEAD
master
$ git status --porcelain=v1
?? docs/ai-logs/reports/AI-LOG-rafasuryaputra-80048-ses_e91a0d69effeiLpWOjVOGxzpMn.md
```

Satu file untracked adalah laporan otomatis logger untuk sesi ini. Tidak ada operasi Git
(commit/push/pull/branch/merge/staging) dijalankan pada D13.

### 1.3 Bukti bahwa kontrak publik tidak berubah selama D9–D13

```
$ git log --oneline -3 -- src
4c7d670 feat(gitkeep): delete all .gitkeep
4af23b8 Subtask Fix (C9 regression)
752e4ed feat(C14): Test Training 1 Epoch

$ git diff --stat 266c611 HEAD -- src tests pytest.ini requirements.txt
 tests/test_end_to_end_pipeline.py    | 294 +++++++++++++++++++++++++++++++++++
 tests/test_integration_components.py |   3 +
 tests/test_train_integration.py      |   3 +
 3 files changed, 300 insertions(+)
```

`src/` tidak disentuh sejak `4c7d670` (sebelum D9). Perubahan `tests/` pada rentang itu hanya:
satu berkas integrasi baru (D11) dan penambahan `pytestmark = pytest.mark.integration` pada dua
berkas lama. Tidak ada asersi atau kontrak tes yang diubah:

```diff
+# test_integration_components.py, test_train_integration.py
+import pytest
+...
+pytestmark = pytest.mark.integration
```

### 1.4 Suite yang dijalankan pada `edbf5cc`

| Perintah (semua via `.\.venv\Scripts\python.exe -m`) | Output aktual | Status |
|---|---|---|
| `pytest --collect-only -q --run-integration` | `169 tests collected in 8.49s` | OK |
| `pytest -q` | `154 passed, 15 skipped in 22.08s` | PASS |
| `pytest -q --run-integration` | `169 passed in 23.38s` | PASS |
| `pytest -q -m integration --run-integration` | `15 passed, 154 deselected in 17.95s` | PASS |
| Modul A (6 berkas) | `31 passed in 10.82s` | PASS |
| Modul B (6 berkas, `--run-integration`) | `90 passed in 13.52s` | PASS |
| Modul C (8 berkas, default) | `40 passed, 1 skipped in 15.71s` | PASS |
| Modul C (8 berkas, `--run-integration`) | `41 passed in 17.32s` | PASS |
| `pytest tests/test_end_to_end_pipeline.py -q --run-integration` | `7 passed in 15.98s` | PASS |

Run konfirmasi setelah seluruh perubahan dokumentasi D13 selesai:
`pytest -q --run-integration` → `169 passed in 28.32s`. `git status --porcelain` setelah run itu
hanya menampilkan `M README.md`, `M docs/TESTING.md`, dan tiga berkas dokumentasi baru — tidak ada
perubahan pada `src/`, `tests/`, `data/`, atau `pytest.ini`.

Tidak ada `failed`, `error`, atau `xfail`. Bentuk skip yang diamati pada run default:

```text
SKIPPED [7] tests\test_end_to_end_pipeline.py: integration tests require --run-integration
SKIPPED [7] tests\test_integration_components.py: integration tests require --run-integration
SKIPPED [1] tests/test_train_integration.py: integration tests require --run-integration
154 passed, 15 skipped in 22.08s
```

Rekonsiliasi: `31 + 90 + 40 + 1 + 7 = 169`; `169 − 15 = 154`. Jumlah per berkas dari koleksi
aktual: attention 28, positional 16, training_contract 18, data_pipeline 17, decoder_block 18,
minigpt_contract 14, decoder_block_contract 13, causal_masking 8, e2e 7, integration_components 7,
tokenizer 6, sliding_window 3, dataloader 2, data_split 2, minigpt_logits 2, minigpt_mock 2,
generation_stop 2, bos_eos 1, checkpoint 1, training_step 1, train_integration 1
(`28+16+18+17+18+14+13+8+7+7+6+3+2+2+2+2+2+1+1+1+1 = 169`).

### 1.5 Verifikasi kutipan tes pada dokumen sebelumnya

Seluruh rujukan tes di `docs/D12_TESTING_REPORT.md` diperiksa terhadap inventaris `--collect-only`
pada `edbf5cc` (69 rujukan `file::Class::test` + 26 rujukan singkat `::test`):

```text
explicit file::path refs: 69
  files not in collection: none
  node paths not in collection: none
bare ::test refs: 26 unique
  not in collection: none
```

Artinya matriks kontrak→test D12 masih menunjuk tes yang benar-benar ada pada HEAD ini.

### 1.6 Verifikasi angka `DATASET_CARD.md` (diukur ulang)

Dijalankan ulang dari `data/processed/*.jsonl` dengan `Tokenizer.fit(train)`:

```text
articles  : {'train': 720, 'val': 80, 'test': 200}
tokens    : {'train': 290920, 'val': 33157, 'test': 77330}
vocab_size: 19192
match articles: True
match tokens  : True
match vocab   : True
val ids outside train vocab : 0
test ids outside train vocab: 0
special ids                 : {'<pad>': 0, '<bos>': 1, '<eos>': 2, '<unk>': 3}
```

Angka `DATASET_CARD.md` (720/80/200; 290.920/33.157/77.330 token; vocab 19.192) **cocok persis**
dan tidak ada id val/test di luar vocab train.

### 1.7 Pemindaian modul terlarang

`tests/test_integration_components.py::test_no_forbidden_transformer_module` memakai
`assertNotIsInstance` terhadap `nn.Transformer`, `nn.TransformerDecoder`, dan
`nn.MultiheadAttention` pada pohon modul PE → MHA → DecoderBlock. Itu pemeriksaan **runtime**,
bukan pemindaian sumber. D13 menambahkan pemindaian sumber case-sensitive:

```text
Select-String -Path src\*.py, src\model\*.py, src\data\*.py `
  -Pattern "nn\.Transformer|MultiheadAttention|torch\.transformer|F\.multi_head_attention_forward" -CaseSensitive
(kosong)
```

Tidak ada kemunculan. Catatan: pencarian case-insensitive akan salah menandai kelas sah
`CausalMultiHeadAttention`; karena itu pemindaian di atas memakai mode case-sensitive.

---

## 2. Rekap acceptance criteria Issues #2–#6

Bukti tes ditulis sebagai nama node yang terverifikasi ada di koleksi (§1.5). Ringkasan bukti per
kontrak `TECH_SPEC.md` §3–§7 ada di `docs/D12_TESTING_REPORT.md` §2; D13 tidak menyalin ulang
seluruh 90 baris itu, tetapi memverifikasi rujukannya dan menambal status yang berubah.

### 2.1 Issue #2 (A) — Data Pipeline & Tokenizer

| # | Acceptance criterion | Bukti pada `edbf5cc` | Status |
|---:|---|---|---|
| 1 | `fit`/`encode`/`decode`/`vocab_size` sesuai §3 | `test_tokenizer.py` (6), `test_data_pipeline.py` (17); §1.6 mengukur ulang vocab 19.192 dan special id 0–3 | TERVERIFIKASI |
| 2 | Tidak ada vocabulary leakage train→val/test | `test_tokenizer.py::TestTokenizerLeakage::test_no_vocab_leakage`, `test_data_split.py::test_splits_and_leakage`; §1.6: 0 id di luar vocab train pada 280 dokumen val+test nyata | TERVERIFIKASI |
| 3 | Tidak ada window lintas batas dokumen | `test_data_pipeline.py::test_no_cross_document_windows`, `::test_no_cross_document_windows_for_long_documents`, `test_sliding_window.py::test_no_cross_document_leak`, `test_end_to_end_pipeline.py::test_real_corpus_windows_and_forward` | TERVERIFIKASI |
| 4 | Batch `[B, 64]` + padding sesuai §4 | `test_dataloader.py` (2), `test_data_pipeline.py::test_dataloader_batch_shape`, `::test_dataloader_padding_is_trailing_and_correct_dtype`, `test_end_to_end_pipeline.py::test_tokenizer_dataset_model_shapes` | TERVERIFIKASI |
| 5 | Dokumen kosong dibuang; 1 token tanpa pasangan | `test_data_pipeline.py::test_empty_and_short_docs_skipped`, `test_sliding_window.py::test_empty_and_short_docs` | TERVERIFIKASI |
| 6 | `DATASET_CARD.md` berisi angka yang diverifikasi | §1.6: artikel, token, vocab cocok persis | TERVERIFIKASI |
| 7 | Setiap subtask A1–A13 punya bukti | laporan AI Issue A di `docs/ai-logs/reports/` | DI LUAR KENDALI D13 (tidak dibuka ulang) |

### 2.2 Issue #3 (B) — Implementasi Komponen Inti Transformer

| # | Acceptance criterion | Bukti pada `edbf5cc` | Status |
|---:|---|---|---|
| 1 | Tidak ada `nn.Transformer*`/`nn.MultiheadAttention` di jalur inti | runtime: `test_integration_components.py::TestComponentIntegration::test_no_forbidden_transformer_module`; sumber: pemindaian case-sensitive §1.7 | TERVERIFIKASI |
| 2 | Shapes output sesuai §6 | `test_positional_encoding.py` (16), `test_attention.py` (28), `test_decoder_block.py` (18), `test_decoder_block_contract.py` (13), `test_minigpt_contract.py` (14), `test_minigpt_logits.py` (2) | TERVERIFIKASI |
| 3 | Causal mask mencegah melihat masa depan | 8 tes `test_causal_masking.py` + `test_attention.py::TestCausalMask::test_causal_invariance_with_future_token_changes`; kontrol negatif permanen `test_invariance_fails_without_mask` | TERVERIFIKASI |
| 4 | Forward/backward berjalan, gradien bukan `None` | `test_attention.py::TestAttentionShape::test_gradient_flows_end_to_end`, `test_decoder_block.py::TestGradients::test_gradients_flow_to_all_parameters`, `test_minigpt_contract.py::TestMiniGPTGradients::test_all_parameters_receive_finite_nonzero_gradient`, `test_training_contract.py::TestParameterUpdate::test_every_trainable_parameter_changes_after_one_step` | TERVERIFIKASI |
| 5 | `T > max_len` (PE) dan `d_model % n_heads != 0` (MHA) → `ValueError` | `test_positional_encoding.py::TestPositionalEncoding::test_value_error_when_T_exceeds_max_len`, `test_attention.py::TestAttentionValidation::test_value_error_when_heads_do_not_divide`, `::test_value_error_when_zero_heads`, `::test_value_error_when_more_heads_than_d_model` | TERVERIFIKASI |
| 6 | Kompleksitas didokumentasikan sesuai §7 | `TECH_SPEC.md` §7, `D12_TESTING_REPORT.md` §2.10 | TERDOKUMENTASI (aritmetika analitis, bukan profiler) |
| 7 | Setiap subtask B1–B14 punya bukti | laporan AI Issue B | DI LUAR KENDALI D13 |

### 2.3 Issue #4 (C) — MiniGPT, Training & Text Generation

| # | Acceptance criterion | Bukti pada `edbf5cc` | Status |
|---:|---|---|---|
| 1 | Logits `[B, T, vocab_size]` float32 | `test_minigpt_logits.py::test_logits_shape_and_dtype`, `test_minigpt_contract.py::TestMiniGPTForwardShape::test_baseline_shape_dtype_finite` | TERVERIFIKASI |
| 2 | Satu step training memperbarui parameter, loss finite | `test_training_step.py::test_parameter_update`, `test_training_contract.py::TestParameterUpdate` (7 tes), `test_end_to_end_pipeline.py::test_training_step_updates_parameters` | TERVERIFIKASI |
| 3 | Train/val loss tercatat per epoch, **file metrics terverifikasi isinya** | tidak ada tes yang menyentuh `write_metrics_jsonl`/`metrics_path` (0 kemunculan di `tests/`); artefak `outputs/` tidak ada (§4.4) | **TIDAK TERVERIFIKASI** |
| 4 | Checkpoint berisi model + vocabulary + config, berhasil dimuat ulang | `test_checkpoint.py::test_checkpoint_roundtrip` (roundtrip objek); **jalur restore terdokumentasi gagal** (F-D9-01) | SEBAGIAN |
| 5 | Generation memakai model terlatih, berhenti sesuai aturan | aturan berhenti: `test_generation_stop.py::test_stop_on_eos`, `::test_stop_on_max_new_tokens`, `test_end_to_end_pipeline.py::test_generate_stops_at_eos_on_real_model`, `::test_generate_with_real_tokenizer_and_model`, `::test_generate_sliding_window_on_long_prompt`. Model terlatih: tidak dapat direproduksi dari clone (§5.2) | SEBAGIAN |
| 6 | Hasil aktual dilaporkan tanpa klaim berlebihan | `AI-LOG-C14-experiment.md` ada; tetapi klaim "direproduksi identik" tidak dapat diperiksa ulang karena artefak tidak ada | SEBAGIAN |
| 7 | Setiap subtask C1–C14 punya bukti | laporan AI Issue C | DI LUAR KENDALI D13 |

### 2.4 Issue #5 (D) — Unit Test, Integrasi & Dokumentasi Teknis

| # | Acceptance criterion | Bukti pada `edbf5cc` | Status |
|---:|---|---|---|
| 1 | Seluruh tes dapat dijalankan konsisten, dapat direproduksi | §1.4: 4 perintah runner + 5 subset, hasil deterministik pada dua run berbeda (D12 `4dbe3a2` dan D13 `edbf5cc` memberi hitungan identik). "Semua anggota dapat mereproduksi" hanya terbukti untuk environment ini | SEBAGIAN |
| 2 | Tes memeriksa perilaku, bukan sekadar "tidak error" | kontrol negatif: `test_invariance_fails_without_mask`, `TestParameterUpdate::test_zero_lr_control_leaves_parameters_unchanged`, `TestPadTargetIgnoredInLoss::test_perturbing_pad_row_logits_does_not_change_loss` (+kontrol `ignore_index=-100`), uji mutasi mask D6 (`docs/TESTING.md` §D6) | TERVERIFIKASI |
| 3 | Hasil tes dan error dicatat dari output aktual | §1.4, §4, `docs/D9_FAILURE_LOG.md`, `docs/D10_FIX_VERIFICATION.md`, `docs/TESTING.md` §D4–D12 | TERVERIFIKASI |
| 4 | Integrasi tanpa mengubah kontrak publik sepihak | §1.3: `src/` tidak berubah sejak `4c7d670`; perubahan `tests/` hanya marker + berkas baru; 15 tes integrasi lulus | TERVERIFIKASI |
| 5 | Seluruh kegagalan relevan dilaporkan **dan ditindaklanjuti** dengan bukti | 7 temuan dilaporkan dengan reproduksi (§4); **belum ada perbaikan** sehingga penutupan belum terjadi | SEBAGIAN |
| 6 | Matriks kontrak→test→status (D1) lengkap | tidak ada artefak D1 tersendiri (F-D9-05); matriks konsolidasi ada di `D12_TESTING_REPORT.md` §2–§3 dan diverifikasi ulang di sini | SEBAGIAN |
| 7 | Setiap subtask D1–D13 punya bukti output/test | §3: D2–D13 punya artefak + output; D1 tanpa artefak mandiri | SEBAGIAN |

### 2.5 Issue #6 (E) — Validasi Logging Otomatis

Diperiksa pada berkas yang tersedia di clone (read-only):

```text
reports by member: raihanfahrifi-80017 39, rafasuryaputra-80048 28,
                   dzakialwanf-80006 12, firdausakbar-80011 1, unparsed 2 (total 82)
raw logs         : raw/rafasuryaputra-80048 21 jsonl (total 21)
git check-ignore : .gitignore:29:docs/ai-logs/raw/  -> docs/ai-logs/raw
git ls-files     : docs/ai-logs/raw -> kosong
JSONL lines parsed: 234611, unparseable: none
```

| # | Acceptance criterion | Bukti | Status |
|---:|---|---|---|
| 1 | Setiap anggota punya bukti smoke test tertulis | 82 laporan Markdown untuk ≥4 member id; **raw log hanya tersedia untuk satu anggota** dan di-gitignore | SEBAGIAN |
| 2 | Prompt uji dan respons benar-benar ada di raw log (bukan ringkasan) | prompt perencanaan D13 dan prompt implementasi D13 ditemukan **verbatim** (bukan `<br>`-summary) di `raw/rafasuryaputra-80048/ses_e91a0d69effeiLpWOjVOGxzpMn.jsonl` | TERVERIFIKASI (sesi ini); anggota lain TIDAK TERVERIFIKASI |
| 3 | Laporan Markdown dihasilkan dan konsisten dengan raw log | laporan otomatis dibangkitkan dari raw; **19 dari 19** laporan otomatis milik `rafasuryaputra-80048` masih berisi field `[Isi manual]` | SEBAGIAN |
| 4 | Tidak ada klaim "logging berhasil" tanpa bukti | §2.5 hanya menyatakan apa yang terukur; klaim lulus seluruh anggota **tidak** dibuat | TERPENUHI |
| 5 | Tidak ada API key/token/password di log | pemindaian 8 pola pada 103 berkas (`.md` + `.jsonl`): 2 hit, keduanya literal `password=[REDACTED]` yang merupakan hasil redaksi logger atas teks prompt sesi ini — bukan nilai rahasia | TERVERIFIKASI (untuk berkas yang tersedia) |
| 6 | File log dan laporan tersimpan di `docs/ai-logs/` | laporan: tracked di `docs/ai-logs/reports/`; raw: ada di `docs/ai-logs/raw/` tetapi **di-gitignore** sehingga tidak ikut repo | SEBAGIAN |
| 7 | Setiap subtask E1–E10 punya bukti | tidak ada dokumen E1–E10 di repo; hanya laporan per sesi | TIDAK TERVERIFIKASI |

---

## 3. Ledger bukti D1–D13

| Subtask | Artefak bukti | Status |
|---|---|---|
| D1 | tidak ada dokumen `docs/D1_*`; matriks kontrak→test dikonsolidasikan di `D12_TESTING_REPORT.md` §2–§3 dan diverifikasi ulang di §1.5/§2 | SEBAGIAN (F-D9-05) |
| D2 | `pytest.ini` + `requirements.txt` + `docs/TESTING.md` §Ringkasan/§Konfigurasi | TERVERIFIKASI |
| D3 | `tests/` (21 berkas, `conftest.py`, `helpers.py`) | TERVERIFIKASI |
| D4 | `docs/TESTING.md` §D4 (`29 passed`), `test_tokenizer.py` + `test_data_pipeline.py` + 4 berkas pipeline | TERVERIFIKASI |
| D5 | `docs/TESTING.md` §D5 (`24 passed`), `test_positional_encoding.py::TestPositionalEncodingContract` (6), `test_causal_masking.py` (8) | TERVERIFIKASI |
| D6 | `docs/TESTING.md` §D6 (`27 passed`, uji mutasi mask), `test_decoder_block_contract.py` (13), `test_minigpt_contract.py` (14) | TERVERIFIKASI |
| D7 | `docs/TESTING.md` §D7 (`18 passed`, kontrol `ignore_index`), `test_training_contract.py` (18) | TERVERIFIKASI |
| D8 | `docs/TESTING.md` §D8 (run per modul `31/90/41/162`) | TERVERIFIKASI (angka historis; jumlah berubah setelah D11) |
| D9 | `docs/D9_FAILURE_LOG.md` (6 temuan + reproduksi R1–R3b) | TERVERIFIKASI |
| D10 | `docs/D10_FIX_VERIFICATION.md` (verification attempt, 0/6 tertutup) | SEBAGIAN (prasyarat "pemilik memperbaiki" tidak terpenuhi) |
| D11 | 15 tes integrasi ber-marker; `test_end_to_end_pipeline.py` (7) | TERVERIFIKASI |
| D12 | `docs/D12_TESTING_REPORT.md`, `docs/TESTING.md` §D12, `README.md` §12 | TERVERIFIKASI |
| D13 | dokumen ini + `docs/TESTING.md` §D13 + laporan AI D13 | TERVERIFIKASI |

---

## 4. Status temuan terbuka di `edbf5cc` (probe aktual)

> **Status per D14 (2026-10-24):** F-D9-01, F-D9-02, F-D9-04, F-D9-05, F-D9-06, dan F-D11-01
> sudah **CLOSED** dengan perbaikan + tes; F-D9-03 tetap **OPEN** menunggu keputusan koordinator.
> Bukti penutupan ada di §4.7 dan `docs/D14_FIX_REPORT.md`. Isi §4.1–§4.6 dipertahankan sebagai
> rekaman historis probe pada `edbf5cc` dan tidak diubah.

Probe dijalankan dari luar repo (`%TEMP%\kilo\d13\probe_d13.py`) sehingga tidak ada berkas uji
baru di repository.

### 4.1 F-D9-01 — restore checkpoint → `generate` kosong (OPEN)

```text
checkpoint vocab entries                          : 14
restored tok.token_to_id size                     : 14
restored tok.id_to_token size                     : 0
restored tok.vocab_size                           : 0
tok.encode('presiden indonesia')                  : [12, 8]
tok.decode(encoded)                               : ''
generate(..., 40)                                 : ''
generate is empty string                          : True
MiniGPT(vocab_size=restored)                      : ValueError: vocab_size must be positive, got 0
control: decode(encoded) is non-empty             : 'presiden indonesia'
control: generate(..., 5) is non-empty            : True
```

Masih OPEN dan masih senyap (tanpa exception). Kontrol membuktikan penyebabnya pemetaan
`id_to_token` yang tidak dipulihkan, bukan bobot model.

### 4.2 F-D9-02 — `context_length=64` hardcode di `src/generate.py:8` (OPEN)

```text
small model.context_length                        : 8
generate default context_length                   : 64
generate(eos_id=-1, default ctx)                  : ValueError: sequence length T=9 exceeds context_length=8
control: explicit ctx=model.context_length        : returned 12 ids
10 seeds, same weights, default eos_id=2 -> ValueError: 0
    per-seed outcome                                : seed0:ok ... seed9:ok
10 seeds, model rebuilt per seed -> ValueError    : 7
    per-seed outcome                                : seed0:ValueError seed1:ValueError seed2:ok
                                                      seed3:ValueError seed4:ValueError seed5:ValueError
                                                      seed6:ok seed7:ok seed8:ValueError seed9:ValueError
```

**Penajaman dibanding D10.** Kegagalan ini bergantung pada **bobot**, bukan pada seed sebagai
variabel bebas: dengan dropout 0 model bersifat deterministik, sehingga me-reseed tanpa membangun
ulang model tidak mengubah hasil (0/10). Jika model dibangun ulang per seed, hasilnya **7/10
ValueError** dengan seed 2, 6, 7 berhenti lebih dulu di `<eos>` — persis angka D10. Tes regresi
untuk temuan ini karena itu wajib menetralkan `<eos>` (mis. `eos_id=-1`), jika tidak hasilnya
bergantung bobot dan dapat lolos palsu.

### 4.3 F-D9-03 — signature `generate` ≠ `TECH_SPEC.md` §6 (OPEN, butuh keputusan)

```text
implemented signature : (model, tokenizer, prompt: str, max_new_tokens: int = 64,
                         context_length: int = 64, bos_id: int = 1, eos_id: int = 2) -> str
TECH_SPEC.md:105      : generate(prompt: str, max_new_tokens: int = 64) -> str
parameter count       : 7
```

Tidak ada kegagalan runtime (pemanggil internal konsisten), tetapi kontrak publik tertulis tidak
cocok dengan implementasi. Perubahan salah satu sisi memerlukan keputusan koordinator + ADR.

### 4.4 F-D9-04 dan F-D9-06 — dokumentasi/artefak (OPEN)

```text
src\train.py:31 : """Pick CUDA when available, otherwise CPU (ADR-014 device policy)."""
jumlah ADR      : 12 (ADR-001 … ADR-012)
Test-Path outputs : False
Test-Path outputs/metrics/full/minigpt_c14.pt : False
git ls-files outputs : ''
```

F-D9-04: rujukan `ADR-014` masih tidak ada. F-D9-06: artefak contoh README masih tidak ada di repo
dan tidak dilacak Git, sehingga contoh restore tidak dapat dijalankan dari clone.

### 4.5 F-D9-05 — artefak D1/D2/D3 yang diklaim (OPEN, sebagian termitigasi)

Ketiga berkas yang disebut laporan D1 (`docs/D1_Acceptance_Criteria_Matrix.md`,
`docs/D2_Testing_Framework.md`, `docs/D3_Test_Structure.md`) tetap tidak ada. Kebutuhan isinya
sebagian tertutup oleh `D12_TESTING_REPORT.md` §2–§3 dan §2 dokumen ini; log lama tidak diubah.

### 4.6 F-D11-01 — arah shift di `tests/helpers.py` (OPEN, dampak nol)

```text
helpers.make_batch contract x[t]==y[t-1] (ok/bad) : 0/222
helpers.make_batch reversed  y[t]==x[t-1] (ok/bad): 226/0
helpers.assert_x_y_shift(make_batch)              : PASS
real dataset sample0 len(x), len(y)               : 64, 64
real dataset sample0 x[:5]                        : [1, 9, 3, 3, 3]
real dataset sample0 y[:5]                        : [9, 3, 3, 3, 3]
real dataset sample0 satisfies y[t]==x[t+1] (all) : True
real dataset sample0 satisfies y[t+1]==x[t] (all) : False
helpers.assert_x_y_shift(contract-direction batch): AssertionError: x[0,0] != y[0,1] for non-pad
tests taking a 'batch' parameter                  : none
```

Terbukti: `make_batch` membangun relasi terbalik dari dataset nyata dan `assert_x_y_shift`
melegalkan arah yang salah tersebut (helper menolak batch yang benar). Helper juga membungkus
pemeriksaan torch di dalam `try/except Exception: pass`, sehingga asersi pertama tidak pernah
menjadi bukti untuk tensor (selalu jatuh ke fallback dengan arah yang sama). Dampak saat ini **nol**
karena fixture `batch` tidak dikonsumsi tes mana pun; jika helper ini dipakai tes baru, ia harus
diperbaiki lebih dulu (D14/keputusan pemilik Issue D).

### 4.7 Status setelah D14 (OPEN → CLOSED)

D14 memperbaiki temuan yang dapat ditutup tanpa keputusan pihak lain. Bukti lengkap ada di
`docs/D14_FIX_REPORT.md`; ringkasannya:

| ID | Status D14 | Perubahan | Bukti tes / probe |
|---|---|---|---|
| F-D9-01 | **CLOSED** | `Tokenizer.from_vocab(vocab)` mengisi `token_to_id`, `id_to_token`, `_vocab_size`; README §11 memakai jalur ini | `test_tokenizer.py::TestTokenizerFromVocab` (5), `test_checkpoint_restore_contract.py::test_restore_checkpoint_then_generate_is_not_empty`; probe checkpoint nyata: `id_to_token 2364/2364`, `vocab_size 2364`, `generate` non-kosong |
| F-D9-02 | **CLOSED** | `generate(context_length=None)` → `getattr(model, "context_length", 64)` | `test_generate_context_contract.py` (4 tes); probe `context_length=8` + `eos_id=-1` tidak lagi `ValueError` |
| F-D9-03 | **OPEN** (butuh keputusan) | tidak diubah — lihat §4.3 dan `docs/D14_FIX_REPORT.md` §6 | perbandingan statis `TECH_SPEC.md:105` vs signature aktual |
| F-D9-04 | **CLOSED** | docstring `src/train.py:31` tidak lagi merujuk `ADR-014` | pemindaian `ADR-01[3-9]` di `src/` → kosong |
| F-D9-05 | **CLOSED** | `docs/D1_Acceptance_Criteria_Matrix.md`, `docs/D2_Testing_Framework.md`, `docs/D3_Test_Structure.md` dibuat | ketiga berkas ada dan dirujuk `docs/TESTING.md` §D14 |
| F-D9-06 | **CLOSED** | README §11 menyertakan perintah `run_training.py` yang menghasilkan artefak dari clone, dan contoh memakai path yang benar-benar dibuat perintah itu | jalur restore dijalankan pada checkpoint hasil `run_training.py` 1 epoch (subset 20/10 artikel): decode + generate non-kosong |
| F-D11-01 | **CLOSED** | `make_batch` membangun `y[:, :-1] = x[:, 1:]`; `assert_x_y_shift` memeriksa arah kontrak tanpa `try/except` yang menelan `AssertionError` | `test_helpers_contract.py` (7 tes), termasuk penolakan arah terbalik dan perbandingan dengan `TextDataset` nyata |

Catatan: F-D9-06 ditutup sebatas "contoh restore dapat dijalankan dari clone"; artefak C14 asli
tetap tidak ada di repo (tidak dilacak Git) dan angka loss C14 tetap dikutip, bukan diukur ulang.

---

## 5. Hasil eksperimen

### 5.1 Eksperimen C14 — dikutip, tidak dijalankan ulang

Angka dari `docs/ai-logs/reports/AI-LOG-C14-experiment.md` (sumber: `c14_metrics.jsonl` yang
**tidak ada di repo**):

| Epoch | Train loss | Val loss | Durasi (s) |
|---:|---:|---:|---:|
| 1 | 5.568583 | 7.135150 | 1123,65 |
| 2 | 4.152143 | 7.856671 | 921,85 |
| 3 | 3.640476 | 8.304918 | 1115,32 |
| 4 | 3.335589 | 8.649888 | 2120,66 |

Konfigurasi: 2.556.672 parameter, vocab 19.192, `n_layers=2/n_heads=4/d_model=64/d_ff=256/
context_length=64`, dropout 0,1, AdamW `lr=3e-4`, `weight_decay=0,01`, batch 32, seed 42,
PyTorch `2.5.1+cu121` di Modal CPU. Interpretasi yang diizinkan: train loss turun monoton (−40%)
dan val loss naik monoton (+21%) pada run ini → **indikasi overfitting pada run tersebut**, bukan
klaim kualitas model.

### 5.2 Apa yang terverifikasi dan tidak dari eksperimen

| Klaim C14/README | Dapat diverifikasi di D13? |
|---|---|
| Checkpoint memuat `state_dict` + `vocab` + `config` tanpa key hilang | **Ya**, secara struktural: `test_checkpoint.py::test_checkpoint_roundtrip` |
| `state_dict` dapat dimuat ke `MiniGPT` | **Ya** (roundtrip objek) |
| Generate dari checkpoint C14 mereproduksi keluaran identik | **Tidak** — artefak tidak ada (F-D9-06) dan jalur restore README rusak (F-D9-01) |
| Metrics JSONL berisi satu baris per epoch | **Tidak** — tidak ada tes untuk penulisan metrics dan berkasnya tidak ada |
| Angka loss per epoch | **Dikutip** dari laporan C14, tidak diukur ulang |

Karena itu laporan ini **tidak** menyimpulkan bahwa model terlatih memenuhi kriteria generation
Issue #4; yang terbukti oleh suite adalah aturan berhenti generation pada model/tokenizer uji.

---

## 6. Keterbatasan laporan ini

1. **CPU-only.** Tidak ada uji CUDA, mixed precision, atau multi-GPU; versi dependency di luar
   environment §1.1 tidak diverifikasi.
2. **Suite hijau ≠ seluruh kontrak tertutup.** Empat gap cakupan bertahan: (a) restore checkpoint →
   `generate` non-kosong, (b) `generate` dengan `model.context_length != 64`, (c) penulisan/verifikasi
   metrics JSONL oleh `train()`, (d) `Tokenizer` tanpa `from_vocab`. Ditambah F-D11-01 pada helper.
3. **Tidak ada pengukuran kompleksitas empiris.** Angka §7 `TECH_SPEC.md` adalah aritmetika
   analitis (attention ≈ 8,4M operasi/blok; matriks attention 524.288 elemen ≈ 2 MiB fp32 untuk
   `B=32,T=64,d=64,H=4`), bukan hasil profiler.
4. **Tes korpus nyata memakai subset.** `test_end_to_end_pipeline.py` memakai 60 dokumen pertama
   `data/processed/train.jsonl`, bukan 720 penuh, agar durasi suite wajar; bila berkas hilang tes
   gagal eksplisit. `test_data_split.py` membaca `data/raw/*.jsonl` dan menulis ulang
   `data/processed/*.jsonl`; pada run D13 `git status` tetap hanya menampilkan laporan logger.
5. **Bukti anggota lain tidak dapat diperiksa dari clone.** `docs/ai-logs/raw/` di-gitignore dan
   hanya berisi milik `rafasuryaputra-80048`; laporan Markdown anggota lain ada, tetapi
   konsistensinya terhadap raw tidak dapat diverifikasi di sini.
6. **Durasi tes bervariasi antarrun.** Yang stabil hanya jumlah pass/skip.
7. **Status Issue #2–#6 per subtask A/B/C/E** dirangkum dari artefak yang ada; D13 tidak membuka
   dan memverifikasi setiap laporan AI anggota lain.
8. **F-D9-01/02/03/04/05/06 dan F-D11-01 tetap terbuka.** D13 tidak memperbaiki `src/`, `tests/`,
   README, maupun kontrak (sesuai Issue D §4).

---

## 7. Koreksi terhadap dokumentasi sebelumnya (errata)

1. **D12 §2.10** menyebut `test_no_forbidden_transformer_module` sebagai "pemindaian statis".
   Aktualnya itu pemeriksaan `isinstance` runtime pada pohon modul. Pemindaian sumber yang
   sebenarnya dilakukan D13 (§1.7) dan hasilnya bersih.
2. **D12** mencatat status suite pada `4dbe3a2`. D13 mencatat status pada `edbf5cc`: hitungan
   identik (154/15/169), durasi berbeda. Tidak ada regresi.
3. **D10** melaporkan F-D9-02 "7/10 seed melempar ValueError". D13 mempersempit: hasil itu
   tereproduksi hanya bila model dibangun ulang per seed; dengan bobot tetap, reseeding tidak
   berpengaruh karena dropout 0. Implikasi untuk tes regresi tetap sama (netralkan `<eos>`).
4. **D8** melaporkan Modul C "8 berkas / 41 tes", **D12** "7 berkas / 40 tes". Keduanya benar:
   berkas ke-8 adalah `test_train_integration.py` yang sejak D11 ber-marker `integration`
   (default: `1 skipped`; dengan `--run-integration`: `41 passed`).

---

## 8. Kesimpulan

### 8.1 Yang terbukti pada `edbf5cc`

- 169 tes lulus dengan `--run-integration`; 154 lulus + 15 skip pada suite default; 15 tes
  integrasi lulus terpisah.
- Seluruh kontrak `TECH_SPEC.md` §3–§7 yang **memang diuji** berperilaku sesuai spesifikasi:
  special token 0–3, lowercase+regex, relasi shift `x[i,t]==y[i,t-1]`, tanpa window lintas
  dokumen, batch `[B,64]` int64, padding diabaikan loss, buffer PE non-trainable, causal mask
  (dengan kontrol negatif), guard `ValueError`, logits `[B,T,V]` float32, satu step training
  mengubah parameter, seed 42 reproduktif, aturan berhenti generation.
- Angka `DATASET_CARD.md` cocok persis dan tidak ada vocabulary leakage pada data nyata.
- Tidak ada API Transformer terlarang di `src/` (runtime + pemindaian sumber case-sensitive).
- `src/` tidak berubah selama D9–D13; integrasi dilakukan tanpa mengubah kontrak publik.
- Tidak ada secret pada 103 berkas log/laporan yang tersedia; prompt sesi ini tercatat verbatim.

### 8.2 Yang tidak terbukti

- Kriteria Issue #4 nomor 3 (metrics terverifikasi) — **tidak ada tes dan tidak ada artefak**.
- Jalur restore checkpoint → generate (F-D9-01) dan `generate` pada konteks non-baseline (F-D9-02).
- Kesesuaian signature `generate` dengan `TECH_SPEC.md` (F-D9-03) — butuh keputusan.
- Kualitas model terlatih dan angka loss C14 — hanya dikutip.
- Reproduksibilitas runner oleh anggota lain dan konsistensi laporan↔raw mereka — tidak dapat
  diperiksa dari clone (raw di-gitignore).

### 8.3 Verdict Issue D

Acceptance criteria Issue D: **3 dari 7 TERVERIFIKASI** (§2.4 nomor 2, 3, 4: tes menguji perilaku,
hasil dicatat dari output aktual, integrasi tanpa perubahan kontrak), **4 dari 7 SEBAGIAN** (nomor 1
reproduksi lintas anggota, 5 penindaklanjutan kegagalan, 6 kelengkapan matriks D1, 7 kelengkapan
bukti D1–D13). Tidak ada klaim bahwa Issue D "selesai penuh" dibuat di sini.

### 8.4 Tindakan yang masih diperlukan (bukan dikerjakan D13)

| Prioritas | Tindakan | Pemilik |
|---|---|---|
| Tinggi | Tambah `Tokenizer.from_vocab(...)` (isi `token_to_id`, `id_to_token`, `_vocab_size`) + perbarui README; setelah itu masukkan tes regresi "restore → generate non-empty" | Issue C (+A) |
| Tinggi | `src/generate.py`: default `context_length=None` → `getattr(model, "context_length", 64)`; tes regresi dengan `eos_id=-1` | Issue C |
| Tinggi | Tes untuk penulisan/verifikasi metrics JSONL (satu baris per epoch) | Issue C |
| Sedang | Keputusan koordinator untuk F-D9-03 (revisi `TECH_SPEC.md` §6 + ADR, atau ubah implementasi) | Koordinator |
| Rendah | Perbaiki `ADR-014` di `src/train.py:31`; sediakan artefak contoh atau ubah README | Issue C / D |
| Rendah | Perbaiki arah shift di `tests/helpers.py::make_batch`/`assert_x_y_shift` sebelum dipakai | Issue D (D14) |

---

## 9. Perubahan file pada D13

| File | Status |
|---|---|
| `docs/D13_FINAL_REPORT.md` | baru (dokumen ini) |
| `docs/TESTING.md` | ditambah bagian D13 (ringkasan + tautan) |
| `README.md` | §12 ditambah tautan laporan akhir D13 |
| `docs/ai-logs/reports/AI-LOG-rafasuryaputra-80048-IssueD-D13.md` | baru (laporan AI) |
| `src/`, `tests/`, `pytest.ini`, `requirements.txt`, `docs/TECH_SPEC.md`, ADR, `issues/`, `data/` | **tidak diubah** |

Skrip probe/audit D13 ditulis di luar repo (`%TEMP%\kilo\d13\`), bukan bagian repository.
Tidak ada operasi Git yang dijalankan (commit/push/pull/branch/merge/staging).
