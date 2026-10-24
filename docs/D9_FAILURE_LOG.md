# D9 — Log Kegagalan dan Bukti Reproduksi

**Issue:** [STEP 3] Issue D — Unit Test, Integrasi & Dokumentasi Teknis
**Subtask:** D9. Identifikasi error dan catat bukti reproduksinya
**Tanggal eksekusi:** 2026-10-24 19:58–20:11 WIB (UTC+07:00)
**Commit saat eksekusi:** `266c611` (`feat(Issue D): Substask D8`), branch `master`
**Anggota:** Rafa Suryaputra (rafasuryaputra-80048)

Dokumen ini mencatat kegagalan yang **benar-benar direproduksi** pada commit di atas, beserta
perintah, output/traceback aktual, langkah reproduksi, pemilik modul, dan status. Tidak ada
kegagalan, traceback, atau hasil yang dikarang. Temuan yang belum direproduksi diberi label
`statis` dan tidak dihitung sebagai kegagalan terverifikasi.

## 1. Lingkungan

| Item | Nilai |
|---|---|
| OS / shell | Windows, PowerShell 5.1 |
| Python | 3.10.6 (`.venv\Scripts\python.exe`) |
| pytest | 9.1.1 |
| torch | 2.14.1+cpu |
| numpy | 2.2.6 |
| CUDA | tidak tersedia (`torch.cuda.is_available() == False`) |
| Catatan | `python` global (Laragon 3.10) **tidak** memiliki pytest; seluruh perintah di dokumen ini memakai `.\.venv\Scripts\python.exe` |

Semua skrip reproduksi dijalankan dari root repo tetapi **ditulis di luar repo**
(`%TEMP%\kilo\d9\`), sehingga tidak ada file uji/skrip baru di repository.

## 2. Baseline ulang (D9)

Dijalankan ulang untuk memastikan status awal sebelum menyimpulkan apa pun.

| Perintah | Output aktual | Status |
|---|---|---|
| `.\.venv\Scripts\python.exe -m pytest -q` | `162 passed in 24.32s` | PASS |
| `.\.venv\Scripts\python.exe -m pytest -q --run-integration` | `162 passed in 27.59s` | PASS (identik, marker belum dipakai — lihat D8) |
| Modul A (6 file) | `31 passed in 12.74s` | PASS |
| Modul B (6 file) | `90 passed in 19.49s` | PASS |
| Modul C (8 file) | `41 passed in 21.76s` | PASS |

`git status --short` setelah seluruh run hanya menampilkan laporan otomatis logger
(`docs/ai-logs/reports/AI-LOG-rafasuryaputra-80048-ses_e9206a204ffe2zhFcZPLV8NwQJ.md`).
Tidak ada perubahan `src/`, `tests/`, atau `data/`.

**Kesimpulan baseline: tidak ada kegagalan suite.** Karena itu D9 tidak berhenti di "suite hijau";
D9 menelusuri jalur yang **tidak dicakup** suite dan mereproduksinya secara terpisah (R1–R3b).

## 3. Ringkasan temuan

| ID | Severity | Ringkasan | Pemilik | Tingkat bukti | Status |
|---|---|---|---|---|---|
| F-D9-01 | Tinggi (silent failure) | Restore checkpoint sesuai README menghasilkan `generate()` = string kosong tanpa error | C (checkpoint/README) + A (API tokenizer) | terverifikasi (R1, R3b) | open |
| F-D9-02 | Sedang | `generate()` memakai `context_length=64` hardcode, bukan `model.context_length`; model non-baseline → `ValueError` di tengah generasi | C | terverifikasi (R2) | open |
| F-D9-03 | Sedang (kontrak) | Signature `generate` berbeda dari `TECH_SPEC.md` §6 | C + koordinator | terverifikasi (statis + R2) | open, butuh keputusan |
| F-D9-04 | Rendah (dokumentasi) | `src/train.py:31` merujuk `ADR-014` yang tidak ada | C / dokumen | terverifikasi (statis) | open |
| F-D9-05 | Rendah (dokumentasi) | Laporan D1 mengklaim 3 file `docs/` yang tidak ada di repo | D (Rafa) | terverifikasi (statis) | open, sudah dilaporkan di D5 |
| F-D9-06 | Rendah (reproduksibilitas) | Contoh restore di README menunjuk artefak yang tidak ada di repo | C / D | terverifikasi (statis) | open |

Observasi (bukan kegagalan kontrak) dicatat di §10.

## 4. F-D9-01 — Restore checkpoint menghasilkan output kosong tanpa error

**Perilaku yang diharapkan.** Snippet `README.md` §11 harus memulihkan model + tokenizer dari
checkpoint, lalu menghasilkan teks. `TECH_SPEC.md` §3 menyatakan `decode(ids)` merender token
kata/tanda baca; §6 menyatakan `generate(...) -> str` mengembalikan kelanjutan teks.

**Aktual.** `generate()` mengembalikan `''` **tanpa exception**. Tidak ada sinyal apa pun bahwa
restore gagal; pengguna melihat "model tidak menghasilkan apa-apa", bukan error.

**Akar masalah (statis + terverifikasi).**

1. `README.md:283-284` hanya menyalin satu arah pemetaan:
   `tok = Tokenizer(); tok.token_to_id = ck["vocab"]`. `id_to_token` tetap `{}` dan
   `_vocab_size` tetap `0`.
2. `src/data/tokenizer.py:44-47` — `decode()` me-render id melalui `self.id_to_token.get(i, "")`,
   sehingga seluruh id menjadi string kosong dan hasil akhir `"".strip() == ""`.
3. `src/generate.py:24` mengembalikan `tokenizer.decode(ids[1:])`; karena decode selalu kosong,
   `generate()` selalu `''` — deterministik, tidak bergantung pada bobot model.
4. `src/data/tokenizer.py:49-51` — `vocab_size` mengembalikan `_vocab_size` yang masih `0`,
   sehingga `MiniGPT(vocab_size=tok.vocab_size, ...)` melempar
   `ValueError: vocab_size must be positive, got 0` (gejala kedua).
5. `Tokenizer` tidak menyediakan konstruktor/loader dari `vocab` (mis. `Tokenizer.from_vocab()`),
   sehingga tidak ada jalur resmi untuk restore yang benar.

**Perintah reproduksi (dijalankan dari root repo).**

```powershell
.\.venv\Scripts\python.exe "$env:TEMP\kilo\d9\r1_restore.py"
```

**Skrip reproduksi minimal (mandiri).**

```python
import os, sys, tempfile
sys.path.insert(0, os.getcwd())
from src.data.tokenizer import Tokenizer
from src.model.minigpt import MiniGPT
from src.train import save_checkpoint, load_checkpoint
from src.generate import generate

corpus = ["presiden indonesia mengumumkan kebijakan baru",
          "jakarta cuaca cerah sepanjang hari"]
tok = Tokenizer(); tok.fit(corpus)
model = MiniGPT(vocab_size=tok.vocab_size, n_layers=1, n_heads=2, d_model=8,
                context_length=64, dropout=0.0)
cfg = {"model": {"vocab_size": tok.vocab_size, "n_layers": 1, "n_heads": 2, "d_model": 8,
                 "context_length": 64, "d_ff": 32, "dropout": 0.0,
                 "layer_norm_eps": 1e-5}}
path = os.path.join(tempfile.mkdtemp(), "ckpt_d9.pt")
save_checkpoint(path, model, vocab=tok.token_to_id, config=cfg)

# --- persis langkah README.md:276-286 ---
ck = load_checkpoint(path)
model_cfg = {k: v for k, v in ck["config"]["model"].items() if k != "d_ff"}
model = MiniGPT(**model_cfg)
model.load_state_dict(ck["state_dict"])
tok = Tokenizer()
tok.token_to_id = ck["vocab"]

print("id_to_token:", len(tok.id_to_token))                 # 0
print("vocab_size :", tok.vocab_size)                       # 0
print("encode     :", tok.encode("presiden indonesia"))     # [17, 12]
print("decode     :", repr(tok.decode([17, 12])))           # ''
print("generate   :", repr(generate(model, tok, "presiden indonesia", 40)))  # ''
```

**Output aktual (R1).**

```text
=== R1: README restore path ===
checkpoint path                : C:\Users\RAFA\AppData\Local\Temp\tmpjbe1pn14\ckpt_d9.pt
checkpoint vocab entries       : 20
restored tok.token_to_id size  : 20
restored tok.id_to_token size  : 0
restored tok.vocab_size        : 0
tok.encode('presiden indonesia')         : [17, 12]
tok.decode(encoded)            : ''
generate(...)                  : ''
generate(...) is empty string  : True
--- control: id_to_token populated ---
control.decode(encoded)        : 'presiden indonesia'
control.vocab_size             : 20
control.generate(...)          : 'presiden indonesia baru mengumumkan baru hari baru dunia mengumumkan kebijakan baru hari baru dunia pendek mengumumkan baru hari baru dunia pendek pendek pendek pendek baru hari baru indonesia baru sepanjang baru hari indonesia baru sepanjang baru hari baru hari indonesia'
--- second symptom: vocab_size == 0 ---
MiniGPT(vocab_size=tok.vocab_size) -> ValueError: vocab_size must be positive, got 0
```

**Kontrol negatif.** Tokenizer yang sama dengan `id_to_token` diisi
(`{i: t for t, i in vocab.items()}`) dan `_vocab_size = len(vocab)` menghasilkan decode
`'presiden indonesia'` dan generate non-kosong. Jadi penyebabnya memang pemetaan id→token yang
tidak dipulihkan, bukan model atau data.

**Reproduksi pada checkpoint hasil training nyata (R3b).** Checkpoint yang dihasilkan
`run_training.py` 1 epoch (50 artikel, vocab 3.981) menunjukkan gejala identik:
`vocab entries 3981`, `id_to_token size 0`, `vocab_size 0`, `generate(...) == ''`.

**Mengapa suite tidak menangkapnya.** `tests/test_checkpoint.py:12-23` hanya membandingkan
`state_dict`, `vocab`, dan `config`; tidak ada tes yang memuat ulang tokenizer dari checkpoint lalu
memanggil `generate`. `tests/test_generation_stop.py:8-28` memakai stub model dan stub tokenizer.

**Dampak.** Siapa pun yang mengikuti README akan mendapat output kosong dan cenderung menyimpulkan
model gagal, padahal bobot benar. Ini juga bertentangan dengan klaim
`docs/ai-logs/reports/AI-LOG-C14-experiment.md:54` bahwa generate "direproduksi identik" dari
checkpoint — jalur restore yang terdokumentasi sekarang tidak mereproduksinya.

**Rekomendasi (bukan dikerjakan di D9).** Pemilik C memilih salah satu: (a) tambahkan
`Tokenizer.from_vocab(vocab)` yang mengisi `token_to_id`, `id_to_token`, dan `_vocab_size`, lalu
perbarui README; atau (b) simpan objek tokenizer utuh di checkpoint dan pulihkan sebagai objek.
Setelah itu tambahkan tes regresi "restore → generate non-empty".

## 5. F-D9-02 — `generate()` memakai `context_length` hardcode

**Perilaku yang diharapkan.** `TECH_SPEC.md` §6: "konteks dibatasi ke `context_length` terakhir
(window geser) jika melebihi". Batas yang benar adalah `model.context_length` (`MiniGPT` menyimpan
nilainya sebagai atribut, `src/model/minigpt.py:44`).

**Aktual.** `src/generate.py:8` menetapkan `context_length: int = 64` sebagai default parameter dan
`:15` memakai nilai itu untuk window geser. Untuk model dengan `context_length != 64` window tidak
pernah menyusut ke batas model, sehingga `MiniGPT.forward` melempar `ValueError` di tengah generasi.

**Perintah reproduksi.**

```powershell
.\.venv\Scripts\python.exe "$env:TEMP\kilo\d9\r2_context_guard.py"
```

**Skrip reproduksi minimal.**

```python
import os, sys
sys.path.insert(0, os.getcwd())
from src.model.minigpt import MiniGPT
from src.generate import generate

class Tok:
    def encode(self, text): return [5, 6]
    def decode(self, ids): return " ".join(str(i) for i in ids)

model = MiniGPT(vocab_size=8, n_layers=1, n_heads=2, d_model=8,
                context_length=8, dropout=0.0)
generate(model, Tok(), "hi", max_new_tokens=10)   # default context_length=64
```

**Output aktual (R2), traceback tidak dipotong.**

```text
=== R2: generate() context guard ===
model.context_length                : 8
generate(...) default context_length: 64 (from src/generate.py signature)
calling generate(model, Tok(), 'hi', max_new_tokens=10) with defaults ...
  raised:
Traceback (most recent call last):
  File "C:\Users\RAFA\AppData\Local\Temp\kilo\d9\r2_context_guard.py", line 42, in main
    out = generate(model, Tok(), "hi", max_new_tokens=10)
  File "C:\Users\RAFA\Documents\TUGAS RAFA\SEMESTER 4\ai gen\AyayoTeam_MiniTransformer\.venv\lib\site-packages\torch\utils\_contextlib.py", line 124, in decorate_context
    return func(*args, **kwargs)
  File "C:\Users\RAFA\Documents\TUGAS RAFA\SEMESTER 4\ai gen\AyayoTeam_MiniTransformer\src\generate.py", line 17, in generate
    logits = model(x)
  File "C:\Users\RAFA\Documents\TUGAS RAFA\SEMESTER 4\ai gen\AyayoTeam_MiniTransformer\.venv\lib\site-packages\torch\nn\modules\module.py", line 1783, in _wrapped_call_impl
    return self._call_impl(*args, **kwargs)
  File "C:\Users\RAFA\Documents\TUGAS RAFA\SEMESTER 4\ai gen\AyayoTeam_MiniTransformer\.venv\lib\site-packages\torch\nn\modules\module.py", line 1794, in _call_impl
    return forward_call(*args, **kwargs)
  File "C:\Users\RAFA\Documents\TUGAS RAFA\SEMESTER 4\ai gen\AyayoTeam_MiniTransformer\src\model\minigpt.py", line 77, in forward
    raise ValueError(
ValueError: sequence length T=9 exceeds context_length=8
--- control: context_length=model.context_length passed explicitly ---
  returned: '5 6 7 7 7 5 5 5 5 5 5 5'
  generated tokens: 12 (max_new_tokens=10)
--- edge case: max_new_tokens=0 ---
  generate(..., max_new_tokens=0) with context_length=64: '5 6'
```

**Analisis kegagalan.** Prompt `[1,5,6]` → panjang konteks 3. Setiap iterasi menambah satu token:
3,4,5,6,7,8 lolos; pada iterasi ke-7 konteks menjadi 9 > 8 dan guard `MiniGPT.forward`
(`src/model/minigpt.py:76-79`) melempar `ValueError`. Kontrol dengan
`context_length=model.context_length` berjalan normal (10 token baru).

**Bukan bug window geser.** R2b membuktikan mekanisme sliding window bekerja pada baseline:
model `context_length=64` dengan prompt 100 token → `105 tokens (100 prompt + 5 generated)`, tanpa
exception. Jadi cacatnya ada pada **konstanta**, bukan algoritma.

**Mengapa suite tidak menangkapnya.** Seluruh tes generation memakai `context_length=64` atau stub
model tanpa guard; tidak ada tes `generate` dengan `model.context_length != 64`.

**Rekomendasi.** Defaultkan `context_length=None` lalu pakai
`context_length = context_length or getattr(model, "context_length", 64)`, dan tambahkan tes
regresi `context_length=8` + `max_new_tokens=10`.

## 6. F-D9-03 — Signature `generate` menyimpang dari `TECH_SPEC`

| Sumber | Signature |
|---|---|
| `docs/TECH_SPEC.md:105` | `generate(prompt: str, max_new_tokens: int = 64) -> str` |
| `src/generate.py:7-8` | `generate(model, tokenizer, prompt: str, max_new_tokens: int = 64, context_length: int = 64, bos_id: int = 1, eos_id: int = 2) -> str` |

Dua parameter pertama berbeda (spesifikasi tidak menyebut `model`/`tokenizer`), dan ada tiga
parameter tambahan yang tidak ada di spesifikasi. Kode saat ini konsisten dengan pemakaian internal
(`run_training.py:160`, `modal_app.py:186`) dan tes, sehingga **tidak ada kegagalan runtime**;
yang bermasalah adalah kontrak publik tertulis. Karena perubahan interface butuh persetujuan,
temuan ini hanya dilaporkan.

**Rekomendasi.** Koordinator memilih: revisi `TECH_SPEC.md` §6 agar sesuai implementasi
(+ ADR bila dianggap perubahan arsitektur), atau ubah implementasi. Keduanya butuh keputusan
eksplisit; D9 tidak mengubah keduanya.

## 7. F-D9-04 — Rujukan `ADR-014` yang tidak ada

`src/train.py:31` menulis docstring: `"""Pick CUDA when available, otherwise CPU (ADR-014 device policy)."""`,
tetapi `docs/ARCHITECTURE_DECISIONS.md` hanya memuat ADR-001 … ADR-012.

```powershell
Select-String -LiteralPath "docs/ARCHITECTURE_DECISIONS.md" -Pattern "^## ADR-"   # 12 baris, ADR-001..012
Select-String -Path "src/*.py","src/**/*.py" -Pattern "ADR-01[3-9]"               # hanya src/train.py:31
```

Dampak: pembaca tidak dapat menelusuri dasar kebijakan device. Rendah, hanya dokumentasi.

## 8. F-D9-05 — File `docs/` yang diklaim ada tetapi tidak ada

`docs/ai-logs/reports/AI-LOG-rafasuryaputra-80048-IssueD-D1-D3.md:18` dan `:30` menyatakan
D1/D2/D3 menghasilkan `docs/D1_Acceptance_Criteria_Matrix.md`,
`docs/D2_Testing_Framework.md`, dan `docs/D3_Test_Structure.md`.

```powershell
foreach ($f in @('docs/D1_Acceptance_Criteria_Matrix.md','docs/D2_Testing_Framework.md','docs/D3_Test_Structure.md')) { "$f -> $(Test-Path -LiteralPath $f)" }
```

Output aktual: ketiganya `False`. Deliverable D1 (matriks kontrak→test→status) karena itu belum
punya artefak di repo; D8 menutup sebagian kebutuhan itu lewat tabel per file di `docs/TESTING.md`.

Temuan ini **sudah dilaporkan** pada `docs/ai-logs/reports/AI-LOG-rafasuryaputra-80048-IssueD-D5.md:20`
dan `:61`; dicatat ulang di sini sebagai item terbuka, bukan temuan baru. Perbaikan ada di ranah D
(Rafa) dan perlu keputusan apakah dokumen dibuat atau laporan D1 dikoreksi. Log AI historis tidak
boleh diubah, sehingga koreksi harus berupa dokumen baru/errata.

## 9. F-D9-06 — Artefak contoh di README tidak tersedia di repo

`README.md:262-263` dan `:276` menunjuk `outputs/metrics/full/minigpt_c14.pt` serta
`outputs/metrics/full/c14_metrics.jsonl`.

```powershell
Test-Path -LiteralPath "outputs"                 # False
git ls-files outputs                             # kosong
```

Direktori `outputs/` tidak ada di working tree dan tidak dilacak Git; `.gitignore`
memuat `*.jsonl` sehingga metrik juga tidak akan masuk repo. Artinya contoh restore di README
**tidak dapat dijalankan langsung dari clone** tanpa lebih dulu menjalankan
`python -m modal run modal_app.py` + `modal volume get` (butuh akses volume Modal).

Tingkat bukti: `statis` untuk ketiadaan berkas; **tidak diverifikasi** apakah volume
`ayayo-c14-vol` masih menyediakan artefak (tidak ada kredensial/akses Modal pada sesi ini).

## 10. Observasi (bukan kegagalan kontrak)

| ID | Observasi | Bukti |
|---|---|---|
| O-D9-01 | `run_training.py` membuat ulang `AdamW` dan `criterion` **di dalam** loop epoch, sehingga state AdamW (momen orde 1/2, `step`) ter-reset setiap epoch. `src/train.py:105` membuat optimizer sekali di luar loop — dua jalur training berperilaku berbeda. | `run_training.py:115-118` (statis) |
| O-D9-02 | `generate` mengembalikan prompt + kelanjutan (`ids[1:]`), bukan hanya kelanjutan: 100 token prompt + 5 token baru → 105 token pada keluaran. `TECH_SPEC.md` §6 tidak menetapkan mana yang dimaksud. | R2, R2b (terverifikasi) |
| O-D9-03 | `generate` tidak menyaring `pad_id`/`unk_id` dari token yang dihasilkan; `decode` membuang id 0–3 sehingga token tersebut hilang diam-diam dari string keluaran meski dihitung dalam `max_new_tokens`. | `src/generate.py:18-21`, `src/data/tokenizer.py:46` (statis) |
| O-D9-04 | Cakupan tes generation/checkpoint terbatas pada stub dan `state_dict`; tidak ada tes restore→generate, tidak ada tes `model.context_length != 64`, tidak ada tes `max_new_tokens=0` (perilaku aktual: mengembalikan prompt saja, `'5 6'`). | R2, `tests/test_generation_stop.py`, `tests/test_checkpoint.py` |

## 11. Laporan ke pemilik modul (siap dikirim)

**Ke pemilik Issue C (checkpoint, training, generation):**

> D9 menemukan tiga hal yang tidak tertangkap suite (162 passed). Bukti lengkap ada di
> `docs/D9_FAILURE_LOG.md` di repo.
> 1. **F-D9-01 (tinggi, silent):** snippet restore di `README.md:276-286` hanya mengisi
>    `tok.token_to_id`; `id_to_token` kosong dan `vocab_size` 0, sehingga `generate()` mengembalikan
>    `''` tanpa error. Terverifikasi pada checkpoint sintetis dan pada checkpoint hasil
>    `run_training.py` (vocab 3.981). Mohon tambahkan jalur restore resmi (mis.
>    `Tokenizer.from_vocab`) + tes regresi restore→generate.
> 2. **F-D9-02 (sedang):** `src/generate.py:8` memakai `context_length=64` hardcode; model dengan
>    `context_length=8` gagal `ValueError: sequence length T=9 exceeds context_length=8` pada token
>    ke-7. Mohon pakai `model.context_length` sebagai default + tes regresi.
> 3. **F-D9-03 (kontrak):** signature `generate` berbeda dari `TECH_SPEC.md:105`; perlu keputusan
>    koordinator (revisi spesifikasi/ADR atau ubah implementasi).
> Tambahan: `src/train.py:31` merujuk ADR-014 yang tidak ada; `run_training.py` membuat ulang
> optimizer tiap epoch.

**Ke koordinator:** F-D9-03 (signature) dan F-D9-05 (matriks D1 tidak ada) butuh keputusan
sebelum D11–D13, karena keduanya menyangkut dokumen/interface, bukan kode modul.

## 12. Perubahan file pada D9

| File | Status |
|---|---|
| `docs/D9_FAILURE_LOG.md` | baru (dokumen ini) |
| `docs/TESTING.md` | ditambah bagian D9 (ringkasan + tautan) |
| `docs/ai-logs/reports/AI-LOG-rafasuryaputra-80048-IssueD-D9.md` | baru (laporan AI) |
| `src/`, `tests/`, `README.md`, `issues/`, `docs/TECH_SPEC.md`, ADR, `pytest.ini`, dependency | **tidak diubah** |

**Catatan tentang unit test.** D9 tidak menambah/mengubah file tes. Alasannya: (a) menambahkan tes
yang mengunci perilaku buggy akan melegalkan bug; (b) menambahkan tes yang gagal akan memerahkan
suite bersama sebelum pemilik modul memperbaiki dan sebelum keputusan diambil — perbaikan kode modul
ada di luar scope D9 (Issue D §4) dan §9 meminta berhenti lalu melapor; (c) Issue D menempatkan
verifikasi perbaikan di **D10** dan integrasi penuh di **D11**. Setiap temuan di atas sudah
dilengkapi usulan tes regresi agar dapat langsung dipakai pada D10.

## 13. Keterbatasan

1. Semua hasil CPU-only (torch 2.14.1+cpu). Perilaku CUDA tidak diuji.
2. Checkpoint C14 asli tidak ada di mesin ini; R3 membuat checkpoint baru (1 epoch, 50 artikel,
   vocab 3.981) sebagai pengganti yang setara secara struktural (`state_dict` + `vocab` + `config`).
3. R3 memakai subset 50/10 artikel yang disalin ke `%TEMP%`, bukan `data/processed/` penuh
   (720/80/200); eksekusi penuh tetap menjadi lingkup D11.
4. Salinan data awal sempat gagal dibaca karena BOM UTF-8 dari `Set-Content -Encoding UTF8`
   (PowerShell 5.1) → `json.decoder.JSONDecodeError: Unexpected UTF-8 BOM`. Itu artefak skrip
   D9, **bukan** defect repository; salinan dibuat ulang tanpa BOM dan run berikutnya berhasil.
   `load_jsonl` memang tidak toleran BOM, tetapi berkas `data/processed/*.jsonl` di repo tidak
   ber-BOM, sehingga tidak dilaporkan sebagai temuan.
5. `outputs/` dan volume Modal tidak dapat diverifikasi (F-D9-06 hanya sampai tingkat
   "berkas tidak ada di repo").
6. Severity ditetapkan berdasarkan dampak pada pemakaian terdokumentasi, bukan kerangka resmi
   proyek (proyek belum punya definisi severity).
