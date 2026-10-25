# D10 — Verifikasi Perbaikan Berdasarkan Tes Aktual

**Issue:** [STEP 3] Issue D — Unit Test, Integrasi & Dokumentasi Teknis
**Subtask:** D10. Verifikasi perbaikan berdasarkan tes aktual
**Tanggal eksekusi:** 2026-10-24 20:51–21:03 WIB (UTC+07:00)
**Commit saat eksekusi:** `b5c2b80` (`feat(Issue D): Substask D9`), branch `master`
**Anggota:** Rafa Suryaputra (rafasuryaputra-80048)
**Status subtask:** **dieksplorasi, hasil: 0 dari 6 temuan tertutup** (lihat §2)

Dokumen ini mencatat eksekusi ulang **setiap** jalur reproduksi D9 pada kode saat ini dan
menilai apakah perbaikan sudah ada. Tidak ada hasil yang dikarang: setiap klaim berasal dari
output yang tercetak pada run yang tercatat di §4–§10. `src/`, `tests/`, `README.md`, dan
kontrak publik **tidak diubah** oleh D10.

## 1. Mengapa D10 dieksekusi sebagai *verification attempt*

Definisi D10 adalah "**setelah pemilik modul memperbaiki**, jalankan ulang tes dan catat output;
temuan tertutup dengan bukti tes lulus". Prasyarat itu belum terpenuhi pada `b5c2b80`:

| Prasyarat | Perintah verifikasi | Hasil aktual |
|---|---|---|
| Ada perubahan modul sejak D9 | `git diff --stat b5c2b80 HEAD -- src tests README.md` | kosong |
| Commit terakhir yang menyentuh `src/` | `git log --oneline -8 -- src/` | `4c7d670` (sebelum D9) |
| Jalur restore resmi tersedia | `hasattr(Tokenizer, "from_vocab")` | `False` |
| `generate` memakai `model.context_length` | `inspect.signature(generate).parameters["context_length"].default` | `64` |

Karena tidak ada objek perbaikan untuk diverifikasi, D10 dijalankan sebagai **verification
attempt** dengan persetujuan anggota: jalankan ulang seluruh probe D9, catat status
**masih terbuka**, dan hasilkan bukti yang bisa dipakai langsung untuk menutup temuan setelah
pemilik modul memperbaiki. Konsekuensi yang harus dipahami: **D10 belum memenuhi hasil yang
diminta Issue D** ("temuan tertutup dengan bukti tes lulus"). D10 baru bisa dinyatakan selesai
setelah probe §4–§9 berstatus `CLOSED` pada commit perbaikan.

## 2. Ringkasan status

| ID | Temuan | Pemilik | Status D10 | Bukti |
|---|---|---|---|---|
| F-D9-01 | Restore checkpoint → `generate()` kosong tanpa error | C (+A) | **OPEN** | §4, §5 |
| F-D9-02 | `generate()` memakai `context_length=64` hardcode | C | **OPEN** | §6, §7 |
| F-D9-03 | Signature `generate` ≠ `TECH_SPEC.md` §6 | C + koordinator | **OPEN** | §8 |
| F-D9-04 | `src/train.py:31` merujuk `ADR-014` yang tidak ada | C / dokumen | **OPEN** | §9 |
| F-D9-05 | 3 dokumen `docs/` yang diklaim laporan D1 tidak ada | D | **OPEN** | §9 |
| F-D9-06 | Contoh restore di README menunjuk artefak tak tersedia | C / D | **OPEN** | §10 |

Total: `checks=21 closed=0 open=16` (5 check berstatus `OK` adalah kontrol negatif/observasi,
bukan penutupan temuan). Kesimpulan: **belum ada satu pun temuan yang dapat ditutup.**

## 3. Lingkungan dan cara reproduksi

| Item | Nilai |
|---|---|
| OS / shell | Windows, PowerShell 5.1 |
| Python | 3.10.6 (`.venv\Scripts\python.exe`) |
| pytest | 9.1.1 |
| torch | 2.14.1+cpu |
| CUDA | tidak tersedia |
| Probe | `%TEMP%\kilo\d10\d10_verify.py` (di luar repo, tidak menulis ke repository) |
| Output lengkap | `%TEMP%\kilo\d10\d10_stdout.txt` (193 baris), `d10_stderr.txt` (traceback), `d10_results.json` |

```powershell
.\.venv\Scripts\python.exe "$env:TEMP\kilo\d10\d10_verify.py"
```

Probe dinilai **bukan** dengan "tidak error", melainkan dengan **perilaku yang diharapkan
setelah perbaikan**. Setiap temuan punya minimal satu kontrol negatif agar status `OPEN`
tidak berasal dari kesalahan skrip:

- F-D9-01 → tokenizer yang sama dengan `id_to_token` diisi manual harus berfungsi.
- F-D9-02 → `context_length=model.context_length` eksplisit harus berfungsi; sliding window
  baseline 64 harus tetap jalan.
- F-D9-02 (determinisme) → `generate` diulang pada 10 seed untuk mengukur seberapa sering
  guard tercapai.

### 3.1 Baseline suite pada commit yang sama (masih hijau)

Dijalankan ulang sebelum probe agar status "suite hijau namun defect ada" tetap terverifikasi
pada commit yang sama, bukan diwarisi dari D8/D9:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest -q --run-integration
```

Output aktual:

```text
162 passed in 26.37s
162 passed in 24.90s
```

Setelah seluruh probe selesai, suite dijalankan sekali lagi: `162 passed in 25.08s`, dan
`git status --short` hanya menampilkan laporan otomatis logger. Artinya probe tidak memodifikasi
repository dan tidak ada tes yang berubah warna.

## 4. V1 — F-D9-01: restore sesuai README (checkpoint sintetis)

**Perilaku yang diharapkan setelah perbaikan:** tokenizer hasil restore memiliki pemetaan
id→token lengkap, `vocab_size` benar, dan `generate()` mengembalikan string tidak kosong.

**Aktual** (mengikuti persis `README.md:276-286`):

```text
  vocab entries in checkpoint : 14
  restored id_to_token size   : 0
  restored vocab_size         : 0
  encode('presiden indonesia'): [12, 8]
  decode(encoded)             : ''
  generate(...)               : ''
  Tokenizer.from_vocab exists : False
[OPEN     ] F-D9-01 | restored tokenizer has id_to_token for every vocab entry
            expected: 14 entries
            actual  : 0 entries
[OPEN     ] F-D9-01 | restored vocab_size equals checkpoint vocab size
            expected: 14
            actual  : 0
[OPEN     ] F-D9-01 | decode(encode(text)) renders text (not empty)
            expected: 'presiden indonesia'
            actual  : ''
[OPEN     ] F-D9-01 | generate(...) returns non-empty string
            expected: non-empty str
            actual  : ''
[OPEN     ] F-D9-01 | official restore API available on Tokenizer
            expected: Tokenizer.from_vocab present
            actual  : present=False
  CONTROL decode              : 'presiden indonesia'
  CONTROL generate non-empty  : True
[OK       ] F-D9-01 | control: populated mapping makes decode/generate work
  MiniGPT(vocab_size=tok.vocab_size) -> ValueError: vocab_size must be positive, got 0
[OPEN     ] F-D9-01 | second symptom: MiniGPT(vocab_size=restored) must construct
            expected: constructs without exception
            actual  : ValueError: vocab_size must be positive, got 0
```

Kontrol negatif berstatus `OK`: dengan `id_to_token` dan `_vocab_size` diisi manual, decode
kembali `'presiden indonesia'` dan generate non-kosong. Jadi penyebabnya tetap pemetaan yang
tidak dipulihkan, bukan bobot model.

## 5. V1b — F-D9-01 pada checkpoint hasil `run_training.py` nyata

Artefak: checkpoint D9 (`%TEMP%\kilo\d9\out\minigpt_c14.pt`) yang dihasilkan
`run_training.py` 1 epoch pada 50 artikel. Artefak ini dipakai ulang agar tidak melatih ulang
265 s; provenance-nya tercatat di `docs/D9_FAILURE_LOG.md` §13.

```text
  checkpoint vocab     : 3981
  restored id_to_token : 0
  restored vocab_size  : 0
  generate(...)        : ''
[OPEN     ] F-D9-01 | real checkpoint: id_to_token populated
            expected: 3981
            actual  : 0
[OPEN     ] F-D9-01 | real checkpoint: generate non-empty
            expected: non-empty str
            actual  : ''
```

Gejala identik dengan checkpoint sintetis, sehingga bukan artefak corpus kecil.

## 6. V2 — F-D9-02: guard `context_length`

```text
  generate signature            : (model, tokenizer, prompt: str, max_new_tokens: int = 64, context_length: int = 64, bos_id: int = 1, eos_id: int = 2) -> str
  default context_length        : 64
  model.context_length          : 8
  (a) natural run (eos_id=2)    : ValueError: sequence length T=9 exceeds context_length=8
  (b) forced run (eos_id=-1)    : ValueError: sequence length T=9 exceeds context_length=8
[OPEN     ] F-D9-02 | context guard: default call on context_length=8 (eos forced off)
            expected: returns str without exception
            actual  : ValueError: sequence length T=9 exceeds context_length=8
[OK       ] F-D9-02 | reproduction is deterministic (not dependent on early <eos>)
  CONTROL explicit ctx returned : '5 6 3 3 3 3 3 3 3 3 3 3'
[OK       ] F-D9-02 | control: explicit context_length=model.context_length works
[OPEN     ] F-D9-02 | default context_length follows model.context_length
            expected: None default resolved from model (or equal to model.context_length)
            actual  : default=64
```

Signature dan perilaku belum berubah: default tetap `64`, sehingga model dengan
`context_length=8` gagal di tengah generasi. Kontrol eksplisit berjalan normal (12 token:
2 prompt + 10 generated), membuktikan algoritma sliding window benar dan cacatnya ada pada
konstanta default.

## 7. Penajaman temuan: F-D9-02 bersifat *intermiten* pada run natural

Ini koreksi/penajaman terhadap D9, bukan temuan baru. D9 menulis guard terpicu "pada token
ke-7". Pengamatan D10 menunjukkan run natural bisa berhenti lebih dulu karena `<eos>`:

```text
V2c (F-D9-02) how often does a natural run hit the guard? seeds 0..9
  seed= 0 -> ValueError sequence length T=9 exceeds context_length=8
  seed= 1 -> ValueError sequence length T=9 exceeds context_length=8
  seed= 2 -> returned   5 6 4
  seed= 3 -> ValueError sequence length T=9 exceeds context_length=8
  seed= 4 -> ValueError sequence length T=9 exceeds context_length=8
  seed= 5 -> ValueError sequence length T=9 exceeds context_length=8
  seed= 6 -> returned   5 6
  seed= 7 -> returned   5 6
  seed= 8 -> ValueError sequence length T=9 exceeds context_length=8
  seed= 9 -> ValueError sequence length T=9 exceeds context_length=8
  raised on 7/10 seeds
[OK       ] F-D9-02 | guard defect is reachable on most seeds (not a one-off init)
            expected: documented frequency
            actual  : 7/10 seeds raise ValueError
```

Implikasi praktis:

1. Repro D9 **valid** (terbukti 7/10 seed), tetapi tidak deterministik karena inisialisasi
   bobot menentukan apakah `<eos>` muncul sebelum konteks melampaui batas.
2. Tes regresi untuk temuan ini **wajib** menetralkan `<eos>` (mis. `eos_id=-1`) atau memakai
   `max_new_tokens` yang dijamin melewati batas; jika tidak, tes bisa lolos palsu pada seed
   yang kebetulan menghasilkan `<eos>`. Ini juga alasan D9 tidak menambahkan tes yang gagal:
   tes semacam itu akan *flaky*, bukan sekadar merah.
3. Sliding window baseline tetap benar (kontrol V2b):

```text
  model.context_length : 64
  prompt tokens        : 100
  generated tokens     : 105 (100 prompt + 5 generated = 105)
[OK       ] F-D9-02 | control: sliding window on baseline 64 still works
```

## 8. V3 — F-D9-03: kontrak signature

```text
  TECH_SPEC.md:105 - `generate(prompt: str, max_new_tokens: int = 64) -> str`.
  src/generate.py     def generate(model, tokenizer, prompt: str, max_new_tokens: int = 64, context_length: int = 64, bos_id: int = 1, eos_id: int = 2) -> str
  params in spec      : ['prompt', 'max_new_tokens']
  params in impl      : ['model', 'tokenizer', 'prompt', 'max_new_tokens', 'context_length', 'bos_id', 'eos_id']
[OPEN     ] F-D9-03 | documented public signature equals implemented signature
[OPEN     ] F-D9-03 | contract resolved since D9 (spec revised or implementation changed)
            expected: spec or implementation differs from D9 record
            actual  : spec unchanged=True impl unchanged=True
```

Perbandingan dilakukan terhadap **rekaman D9** (dibaca dari `docs/D9_FAILURE_LOG.md`), bukan
asumsi: baik spesifikasi maupun implementasi identik dengan yang dilaporkan D9. Karena
perubahan interface butuh keputusan koordinator, D10 hanya mencatat status.

## 9. V4/V5 — F-D9-04 dan F-D9-05 (dokumentasi)

```text
V4 (F-D9-04) src/train.py ADR-014 reference
  ADR headings present : 12 -> ## ADR-001  ... ## ADR-012
  dangling references  : ['src\train.py:31: """Pick CUDA when available, otherwise CPU (ADR-014 device policy)."""']
[OPEN     ] F-D9-04 | no src reference to a non-existent ADR
            expected: no dangling ADR reference
            actual  : 1 dangling
```

```text
V5 (F-D9-05) docs artifacts claimed by the D1 report
  docs/D1_Acceptance_Criteria_Matrix.md         -> False
  docs/D2_Testing_Framework.md                  -> False
  docs/D3_Test_Structure.md                     -> False
[OPEN     ] F-D9-05 | three documents claimed by the D1 report exist
            expected: all present
            actual  : all False
```

Catatan penting: **dokumen D10 ini tidak menutup F-D9-05.** Membuat dokumen baru bukan berarti
tiga dokumen yang diklaim laporan D1 menjadi ada. Penutupan menuntut salah satu: (a) ketiga
dokumen benar-benar dibuat, atau (b) laporan D1 dikoreksi melalui errata eksplisit (log historis
tidak boleh diubah). Keputusan ini ada pada anggota/koordinator.

## 10. V6 — F-D9-06: artefak contoh di README

```text
  Test-Path outputs                                       -> False
  Test-Path outputs/metrics/full/minigpt_c14.pt           -> False
[OPEN     ] F-D9-06 | README example artifact exists in a fresh clone
            expected: README example artifact present or README points to tracked path
            actual  : outputs exists=False
```

Tingkat bukti tetap `statis` untuk ketiadaan berkas; ketersediaan artefak di volume Modal
tidak dapat diverifikasi dari sesi ini (tidak ada kredensial).

## 11. V7 — Mengapa suite tetap hijau (gap cakupan)

```text
  test calls generate() with a restored tokenizer              -> False
  test calls generate() with context_length != 64              -> False
  test exercises max_new_tokens=0                              -> False
  test builds MiniGPT with context_length != 64 and generates  -> False
[OPEN     ] F-D9-01/02 | suite covers restore->generate and non-baseline context generation
            expected: all four coverage checks present
            actual  : 4 missing
```

Keempat jalur yang menjadi akar F-D9-01/F-D9-02 masih tidak tercakup suite, sehingga
`162 passed` tidak membantah temuan. Ini konsisten dengan analisis D9 dan menegaskan bahwa
perbaikan harus disertai tes regresi, bukan hanya perubahan kode.

## 12. Kriteria penutupan (definition of done untuk D10 ulang)

D10 dapat dinyatakan selesai hanya jika, pada commit perbaikan:

| ID | Kriteria lulus (yang diperiksa probe) |
|---|---|
| F-D9-01 | `len(id_to_token) == len(vocab)`; `vocab_size == len(vocab)`; `decode(encode(t)) == t` untuk teks dalam vocab; `generate(...)` non-kosong; jalur restore resmi tersedia (mis. `Tokenizer.from_vocab`) dan dipakai README |
| F-D9-02 | `generate(model, tok, p, max_new_tokens=10)` pada `context_length=8` tidak melempar exception (dengan `<eos>` dinetralkan); default mengikuti `model.context_length`; parameter eksplisit tetap dihormati |
| F-D9-03 | `TECH_SPEC.md` §6 direvisi (ADR bila perlu) **atau** implementasi disesuaikan; keduanya harus konsisten |
| F-D9-04 | Tidak ada rujukan ADR yang tidak ada di `src/` (atau ADR-014 ditambahkan) |
| F-D9-05 | Tiga dokumen D1–D3 ada, atau errata koreksi diterbitkan |
| F-D9-06 | README menunjuk artefak yang tersedia, atau instruksi pembuatannya lengkap dan dapat dijalankan |

Tes regresi yang disiapkan untuk D11 (belum ditambahkan ke `tests/`, karena akan memerahkan
suite bersama sebelum modul diperbaiki — persetujuan yang diberikan adalah *verification
attempt* tanpa tes gagal di suite):

```python
# tests/test_generate_context_contract.py  (kandidat D11, setelah perbaikan)
def test_generate_uses_model_context_length():
    model = MiniGPT(vocab_size=8, n_layers=1, n_heads=2, d_model=8,
                    context_length=8, dropout=0.0)
    # eos dinetralkan: tanpa ini tes bergantung pada inisialisasi bobot (7/10 seed)
    out = generate(model, _Tok(), "hi", max_new_tokens=10, eos_id=-1)
    assert isinstance(out, str) and out

def test_generate_still_honours_explicit_context_length():
    model = MiniGPT(vocab_size=8, n_layers=1, n_heads=2, d_model=8,
                    context_length=64, dropout=0.0)
    assert generate(model, _Tok(), "hi", max_new_tokens=3,
                    context_length=8, eos_id=-1)

# tests/test_checkpoint_restore_contract.py  (kandidat D11, setelah perbaikan)
def test_restore_then_generate_is_not_empty(tmp_path):
    # save_checkpoint -> load_checkpoint -> restore tokenizer -> generate
    ...
    assert tok.vocab_size == len(vocab) and gen.strip()
```

## 13. Kesimpulan

1. **Tidak ada temuan yang tertutup.** Keenam temuan D9 masih dapat direproduksi pada
   `b5c2b80`; belum ada perbaikan kode/dokumen yang bisa diverifikasi.
2. **Suite tetap hijau** (`162 passed`) sekaligus **tetap tidak mampu** menangkap
   F-D9-01/F-D9-02, karena empat jalur kritis tidak tercakup (V7).
3. **Penajaman baru:** F-D9-02 intermiten (7/10 seed) sehingga tes regresinya wajib
   menetralkan `<eos>` agar tidak flaky.
4. Tindakan yang diperlukan sebelum D10 dapat ditutup:
   - Pemilik Issue C: perbaiki F-D9-01 (jalur restore resmi + README) dan F-D9-02 (`model.context_length`).
   - Koordinator: keputusan F-D9-03 (revisi spesifikasi/ADR atau ubah implementasi) dan F-D9-05 (buat dokumen atau terbitkan errata).
   - Setelah itu D10 dijalankan ulang; status berubah menjadi `CLOSED` hanya jika §12 terpenuhi.

## 14. Keterbatasan

1. CPU-only (torch 2.14.1+cpu); perilaku CUDA tidak diuji.
2. V1b memakai artefak checkpoint D9 (hasil `run_training.py`, 50 artikel, vocab 3.981), bukan
   checkpoint C14 asli maupun `data/processed/` penuh; eksekusi penuh tetap lingkup D11.
3. Ketersediaan artefak di volume Modal tidak diverifikasi (F-D9-06 hanya sampai "berkas tidak
   ada di repo").
4. Probe dijalankan sebagai skrip Python di luar pytest, sehingga hasilnya bukan bagian dari
   suite; konversinya menjadi tes pytest kandidat D11 disediakan di §12.
5. Jumlah seed (10) cukup untuk menunjukkan intermitensi, bukan untuk mengestimasi probabilitas
   populasi.
6. Severity mengikuti D9 (proyek belum punya definisi resmi).

## 15. Perubahan file pada D10

| File | Status |
|---|---|
| `docs/D10_FIX_VERIFICATION.md` | baru (dokumen ini) |
| `docs/TESTING.md` | ditambah bagian D10 (ringkasan + tautan) |
| `docs/ai-logs/reports/AI-LOG-rafasuryaputra-80048-IssueD-D10.md` | baru (laporan AI) |
| `src/`, `tests/`, `README.md`, `issues/`, `docs/TECH_SPEC.md`, ADR, `pytest.ini`, dependency | **tidak diubah** |
