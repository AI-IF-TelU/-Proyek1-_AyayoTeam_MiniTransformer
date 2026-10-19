## Tujuan dan ruang lingkup

Membagi pekerjaan Mini-Transformer menjadi lima unit kerja paralel yang masing-masing dapat dikerjakan oleh satu anggota menggunakan AI coding agent yang berbeda, berdasarkan kontrak final `docs/TECH_SPEC.md` (dikunci pada Issue #1). Issue ini adalah pusat pemantauan seluruh pekerjaan Step 3.

Ruang lingkup: hanya pembagian kerja + definisi Issue dan acceptance criteria. Tidak ada implementasi kode pada Issue ini.

## Daftar Issue implementasi

| Issue | Judul | Pemilik yang direkomendasikan | Status |
|---|---|---|---|
| [#2](https://github.com/AI-IF-TelU/AyayoTeam_MiniTransformer/issues/2) | [STEP 3] Issue A — Data Pipeline & Tokenizer | Dzaki Alwan | Menunggu |
| [#4](https://github.com/AI-IF-TelU/AyayoTeam_MiniTransformer/issues/4) | [STEP 3] Issue B — Implementasi Komponen Inti Transformer | Muhammad Raihan Fahrifi | Menunggu |
| [#3](https://github.com/AI-IF-TelU/AyayoTeam_MiniTransformer/issues/3) | [STEP 3] Issue C — MiniGPT, Training Loop & Text Generation | Firdaus Akbar Amrullah | Menunggu |
| [#5](https://github.com/AI-IF-TelU/AyayoTeam_MiniTransformer/issues/5) | [STEP 3] Issue D — Unit Test, Integrasi & Dokumentasi Teknis | Rafa Suryaputra | Menunggu |
| [#6](https://github.com/AI-IF-TelU/AyayoTeam_MiniTransformer/issues/6) | [STEP 3] Issue E — Validasi Logging Otomatis Lintas AI Agent | Rafa Suryaputra (berkoordinasi dengan seluruh anggota) | Menunggu |

Catatan assignment: pemilik di atas adalah rekomendasi. Assignment GitHub belum dilakukan karena verifikasi username belum lengkap; koordinator dapat menugaskan setelah username tiap anggota terverifikasi di organisasi.

## Urutan pengerjaan yang disarankan

Tim ingin bekerja **bertahap dengan satu anggota aktif pada satu waktu** (bukan paralel penuh). Urutan direkomendasikan:

1. **Semua anggota** → smoke test logging personal (Issue E, sebagai gerbang awal).
2. **Dzaki Alwan** → Issue A (Data Pipeline & Tokenizer) — fondasi semua training.
3. **M. Raihan Fahrifi** → Issue B (Komponen Inti Transformer) — fondasi model.
4. **Firdaus Akbar Amrullah** → Issue C (MiniGPT, Training & Generation) — rakitan + training, setelah A dan B siap.
5. **Rafa Suryaputra** → Issue D (Unit Test & Integrasi) — koordinasi tes lintas modul setelah A, B, C selesai.

Meskipun kontrak memungkinkan paralel, pengerjaan bertahap mengurangi risiko konflik integrasi dan memungkinkan setiap anggota memahami hasil anggota sebelumnya.

## Hubungan dependensi antartugas

- **Issue A → C**: Issue C mengonsumsi tokenizer/loader dari A untuk training sungguhan.
- **Issue B → C**: integrasi final MiniGPT menunggu komponen inti (B) lulus tes; kerangka C boleh dibangun dengan mock lebih dulu.
- **Issue A, B → D**: integrasi tes penuh menunggu modul A dan B tersedia.
- **Issue C → D**: tes training/generation masuk ke D setelah C tersedia.
- **Issue E → seluruh anggota**: sebelum anggota mulai coding yang wajib dicatat, logging environment anggota tersebut (E) harus lolos.

## Tugas yang dapat dikerjakan paralel

- A dan B (paralel penuh; kontrak sudah dikunci).
- D (mulai test berbasis kontrak tanpa menunggu implementasi; integrasi penuh menunggu A/B/C).
- C (kerangka + interface dengan mock; integrasi final menunggu B).
- E (paralel penuh; gerbang logging per anggota).

## Tugas yang harus menunggu

- Integrasi final MiniGPT (C) menunggu Issue B lulus tes.
- Training sungguhan (C) menunggu data dari A.
- Integrasi tes (D) menunggu A, B, C tersedia untuk dieksekusi bersama.
- Pekerjaan coding anggota mana pun yang wajib dicatat menunggu smoke test logging (E) lolos pada environment anggota tersebut.

## Pembagian tanggung jawab

| Anggota | Peran | Issue |
|---|---|---|
| Muhammad Raihan Fahrifi | Prompt Engineer & LLM Navigator | B (komponen inti) |
| Dzaki Alwan | Data Pipeline Engineer | A (data & tokenizer) |
| Firdaus Akbar Amrullah | Training Loop Engineer | C (MiniGPT, training, generation) |
| Rafa Suryaputra | Documentarian & Error Handler | D (test/integrasi) + E (validasi logging) |

Setiap anggota: bekerja langsung di branch `master` (master-only, tanpa branch baru, tanpa PR/merge). Perubahan direview anggota lain sebelum commit dan push ke `master`.

## Status logging tiap anggota

| Anggota | Tool | Status smoke test | Catatan |
|---|---|---|---|
| Muhammad Raihan Fahrifi | Kilo | ✅ Lulus (2 sesi terverifikasi, ADR-006) | Plugin `.kilo/plugin/mini-transformer-logger.ts` |
| Dzaki Alwan | — | ⬜ Belum diverifikasi | Smoke test 19 Okt; dimonitor koordinator — tidak ditandai lulus tanpa bukti |
| Firdaus Akbar Amrullah | — | ⬜ Belum diverifikasi | Smoke test 19 Okt; dimonitor koordinator — tidak ditandai lulus tanpa bukti |
| Rafa Suryaputra | — | ⬜ Belum diverifikasi | Smoke test 19 Okt; dimonitor koordinator — tidak ditandai lulus tanpa bukti |

## Status task dan acceptance criteria (keseluruhan)

- [ ] **Issue A** (#2): 13 subtask, belum dimulai → A1–A13.
- [ ] **Issue B** (#4): 14 subtask, belum dimulai → B1–B14.
- [ ] **Issue C** (#3): 14 subtask, belum dimulai → C1–C14.
- [ ] **Issue D** (#5): 13 subtask, belum dimulai → D1–D13.
- [ ] **Issue E** (#6): 10 subtask, belum dimulai → E1–E10.

Per subtask acceptance criteria verifiable, setiap anggota bertanggung jawab atas miliknya. Issue D mengoordinasikan pengujian lintas modul.

## Checklist review serta integrasi

- [ ] Setiap anggota memiliki log smoke test lolos (Issue E).
- [ ] Setiap anggota bekerja master-only (tanpa branch baru), push langsung ke `master`.
- [ ] Setiap perubahan ditinjau anggota selain pembuatnya sebelum push ke `master`.
- [ ] Test kontrak lokal tiap modul lulus sebelum push ke `master`.
- [ ] Issue D menjalankan tes integrasi setelah seluruh modul tersedia.
- [ ] Acceptance criteria Issue #2–#6 terverifikasi dengan bukti aktual.
- [ ] `DATASET_CARD.md` diisi hasil aktual dari Issue A.
- [ ] Laporan eksperimen disusun berdasarkan hasil nyata, bukan dikarang.

## Catatan hambatan dan keputusan yang masih tertunda

- **Assignment GitHub:** dianggap selesai per keputusan koordinator (2026-10-19). Assignment GitHub aktual dikerjakan koordinator/anggota secara manual; tidak diverifikasi via API oleh AI agent.
- **Framework testing:** **`pytest`** ditetapkan koordinator (2026-10-19) sebagai runner resmi. Issue D D2 menggunakannya tanpa izin tambahan.
- **Struktur file final (keputusan koordinator 2026-10-19, Opsi 1):** tetap persis per kontrak TECH_SPEC §6 — `src/data/tokenizer.py`, `src/data/dataset.py`, `src/model/{positional_encoding,attention,decoder_block,minigpt}.py`, `src/train.py`, `src/generate.py`, opsional `src/config.py`. Tidak ada `src/data/preprocessing.py`, `scripts/prepare_data.py`, `src/training/`, `src/generation/`, `configs/`. Kalimat "dikonfirmasi saat integrasi" pada Issue A §2 dan Issue B §2 telah diubah menjadi "dikonfirmasi koordinator 2026-10-19".
- **Format metrik output:** **JSONL** (keputusan koordinator 2026-10-19; ADR-011) — menggantikan pilihan ganda CSV/JSONL pada TECH_SPEC §6 dan Issue C.
- **Jumlah subset dataset & strategi split (keputusan koordinator 2026-10-19):** subset = **1.000 artikel**; split bawaan train/test (25.8k/6.46k) dipertahankan tanpa resplit; validation diambil 10% dari split train (seed 42); fallback 80/10/10 **tidak dipakai** (ADR-012).
- **Kerja di `master` langsung (master-only):** seluruh anggota bekerja pada satu branch `master`. Dilarang membuat branch baru, pull request, atau merge. `git pull --ff-only origin master` hanya dijalankan saat anggota lain mengabarkan telah push (pengerjaan berurutan, saling menunggu).
- **ADR-006 pembaruan tingkat verifikasi:** menunggu seluruh smoke test anggota selesai dan disetujui tim.

## Acceptance criteria keseluruhan

- [ ] Seluruh Issue #2–#6 didefinisikan sesuai kontrak `docs/TECH_SPEC.md` dan dapat langsung dikerjakan.
- [ ] Tidak ada duplikat dengan Issue yang sudah ada (Issue #1 tetap closed, riwayat tidak diubah).
- [ ] A: tokenizer/dataset sesuai §3–§4; tidak ada vocab leakage; tidak ada window lintas dokumen; Dataset Card diperbarui.
- [ ] B: implementasi manual PE, causal MHA, DecoderBlock (pre-norm, FFN GELU) tanpa `nn.Transformer*`/`nn.MultiheadAttention`; shape dan causal mask teruji.
- [ ] C: MiniGPT logits `[B, T, V]`; training berjalan; loss tercatat; checkpoint lengkap; generation greedy teruji; hasil aktual dilaporkan jujur.
- [ ] D: seluruh tes konsisten dan memeriksa perilaku; hasil aktual dicatat; integrasi tanpa ubah kontrak sepihak.
- [ ] E: bukti smoke test per anggota; raw JSONL + laporan Markdown di `docs/ai-logs/`; tanpa secret.
- [ ] Setiap Issue yang dibuat sesuai format 10 bagian (tujuan, konteks, scope, non-scope, dependensi, kontrak, acceptance criteria, test, aturan logging, dokumentasi).
- [ ] Setiap anggota bekerja master-only (tanpa branch baru); review lintas anggota sebelum push ke `master`.
- [ ] Semua task checklist Issue #2–#6 memiliki checkbox status yang mencerminkan kemajuan aktual (tidak dicentang otomatis).

## Batasan

- Jangan menutup Issue yang baru dibuat sebelum acceptance criteria terpenuhi.
- Jangan mengubah interface, dependency, atau keputusan arsitektur tanpa persetujuan dan pencatatan ADR.
- Jangan mengarang status pengujian, bukti dataset, atau persetujuan anggota.
- Jangan mengubah Issue #1 (closed, riwayat tidak diubah).
- Jika direct push ke `master` tidak diizinkan oleh proteksi repository, jangan mencoba melewati proteksi.

## Jadwal Eksekusi dan Deadline per Anggota (Update 2026-10-18)

Update ini menambahkan jadwal per anggota: tanggal mulai, deadline, estimasi durasi, target subtask per hari, dan buffer debugging, berdasarkan checklist Issue #2–#6. Workflow tetap berurutan: **satu anggota aktif pada satu waktu, satu subtask dikerjakan dan diverifikasi sebelum melanjutkan**. Deadline keseluruhan proyek: **Jumat, 30 Oktober 2026, 17.00 WIB**.

| Fase | Anggota | Issue | Subtask | Mulai | Deadline | Estimasi durasi | Buffer |
|---|---|---|---|---|---|---|---|
| 0 — Smoke test logging | Semua anggota | E (#6) | E1–E3 (per anggota), E4–E10 (verifikasi Rafa) | Sen 19 Okt 2026 (09.00) | Sen 19 Okt 2026 (17.00) | 2 jam/anggota + 4 jam verifikasi | 1 jam |
| 1 — Data Pipeline & Tokenizer | Dzaki Alwan | A (#2) | A1–A13 (13 subtask) | Sen 19 Okt 2026 (18.00) | Rab 21 Okt 2026 (17.00) | ~15 jam | 3 jam |
| 2 — Komponen Inti Transformer | Muhammad Raihan Fahrifi | B (#4) | B1–B14 (14 subtask) | Kam 22 Okt 2026 (09.00) | Sen 26 Okt 2026 (17.00) | ~19 jam | 4 jam |
| 3 — MiniGPT, Training & Generation | Firdaus Akbar Amrullah | C (#3) | C1–C14 (14 subtask) | Sen 26 Okt 2026 (18.00) | Rab 28 Okt 2026 (17.00) | ~17 jam | 2–3 jam |
| 4 — Unit Test, Integrasi & Dokumentasi | Rafa Suryaputra | D (#5) | D1–D13 (13 subtask) | Kam 29 Okt 2026 (09.00) | Jum 30 Okt 2026 (17.00) | ~16 jam | 1–2 jam |

Verifikasi Issue E (E4–E10) oleh Rafa ditargetkan selesai Sel 20 Okt 2026 (12.00), paralel dan tidak memblokir Fase 1.

### Fase 0 — Smoke test logging (Issue E, seluruh anggota)
- **Deadline:** Senin, 19 Oktober 2026, 17.00 WIB.
- E1–E3: setiap anggota mencatat tool/agent yang dipakai, verifikasi konfigurasi logger, dan menjalankan satu smoke test unik pada environment sendiri. Nuansa wajib: milik anggota lain tidak menggantikan bukti milik sendiri (Issue #6 §9).
- E4–E10: verifikasi JSONL, laporan Markdown, redaksi secret, lokasi file, dan merangkum bukti tiap anggota — dikerjakan Rafa, selesai Sel 20 Okt 12.00 WIB.
- Buffer: 1 jam. Jika logger gagal pada environment anggota, coding anggota tersebut berhenti sampai logger diperbaiki.

### Fase 1 — Issue A (Dzaki Alwan) — 13 subtask
- **Mulai:** Sen 19 Okt 2026 (18.00) · **Deadline:** Rab 21 Okt 2026 (17.00) · **Estimasi:** ~15 jam · **Buffer:** 3 jam.
- Sen 19 Okt (2–3 jam): A1, A2, A3 — spesifikasi, metadata dataset, strategi subset.
- Sel 20 Okt (6–7 jam): A4, A5, A6, A7, A8 — subset + metadata, dedup/split, tokenizer regex, `fit`/`encode`/`decode`, tes no-leakage.
- Rab 21 Okt (5–6 jam): A9, A10, A11, A12, A13 — BOS/EOS, sliding window + input-target, padding + DataLoader, test bertahap, Dataset Card.
- Risiko: ukuran unduhan dataset dan verifikasi metadata tak terduga. Prioritas bila slippage: A1–A12 (inti) dulu; A13 wajib selesai sebelum C11 (training data asli).

### Fase 2 — Issue B (Muhammad Raihan Fahrifi) — 14 subtask
- **Mulai:** Kam 22 Okt 2026 (09.00) · **Deadline:** Sen 26 Okt 2026 (17.00) · **Estimasi:** ~19 jam · **Buffer:** 4 jam.
- Kam 22 Okt (5 jam): B1, B2, B3, B4 — kontrak, struktur file, Sinusoidal PE, tes PE.
- Jum 23 Okt (5 jam): B5, B6, B7 — proyeksi Q/K/V, scaled dot-product attention, causal mask + tes invariance.
- Sab 24 Okt (5 jam, perlu konfirmasi ketersediaan): B8, B9, B10 — multi-head + `W_o`, tes MHA, FFN GELU.
- Sen 26 Okt (5 jam): B11, B12, B13, B14 — DecoderBlock pre-norm, tes backward/gradient, integrasi komponen, dokumentasi kompleksitas.
- Risiko: Sabtu belum tentu hari kerja → efektif 3 hari; buffer 4 jam dipakai penuh bila perlu. Bukti B13 (integrasi) dapat diperkuat saat C5 berjalan; B14 (dokumentasi) tidak dihapus, hanya boleh diberi prioritas terakhir tanpa mengubah acceptance criteria.

### Fase 3 — Issue C (Firdaus Akbar Amrullah) — 14 subtask
- **Mulai:** Sen 26 Okt 2026 (18.00) · **Deadline:** Rab 28 Okt 2026 (17.00) · **Estimasi:** ~17 jam · **Buffer:** 2–3 jam.
- Sen 26 Okt (2–3 jam): C1, C2 — kontrak §5–§7, config + struktur modul.
- Sel 27 Okt (7 jam): C3, C4, C5, C6, C7, C8 — kerangka MiniGPT, alur mock, integrasi komponen Issue B, tes shape logits, loss + satu training step, tes parameter-update.
- Rab 28 Okt (7 jam): C9, C10, C11, C12, C13, C14 — training loop + validation loss, metrik + checkpoint, loader asli Issue A, greedy generation, tes aturan stop, eksperimen + laporan.
- **Fase paling rapat** (14 subtask / 2,5 hari, dependensi A dan B). Eksperimen C14 boleh memakai sebagian epoch dan dilaporkan jujur sebagai hasil aktual; klaim penuh 10 epoch hanya jika benar-benar dijalankan.

### Fase 4 — Issue D (Rafa Suryaputra) — 13 subtask
- **Mulai:** Kam 29 Okt 2026 (09.00) · **Deadline:** Jum 30 Okt 2026 (17.00) · **Estimasi:** ~16 jam · **Buffer:** 1–2 jam.
- Kam 29 Okt (8 jam): D1, D2, D3, D4, D5, D6 — matriks kontrak→test→status, keputusan runner, struktur `tests/`, tes tokenizer/data pipeline, tes PE/causal mask, tes DecoderBlock/MiniGPT.
- Jum 30 Okt (8 jam): D7, D8, D9, D10, D11, D12, D13 — tes training/loss, jalankan per modul, catat error + bukti reproduksi, verifikasi perbaikan, tes integrasi penuh, dokumentasi testing, laporan akhir.
- Risiko: hanya 2 hari efektif. Mitigasi (butuh persetujuan koordinator): D1–D7 penulisan test berbasis kontrak boleh dimulai 28 Okt malam karena tidak menunggu modul selesai (Issue #5 §5), sehingga Jumat difokuskan ke eksekusi D8–D13.

## Risiko dan prioritas MVP (tidak menghapus acceptance criteria wajib)

- **R1 — Tinggi (Fase C):** 14 subtask dalam 2,5 hari + dua dependensi. Jika slippage: utamakan C1–C11 (kerangka, training loop, checkpoint, data asli); C12–C13 (generation + aturan stop) tetap wajib dan digeser ke jam buffer Fase D; C14 boleh eksperimen sebagian epoch.
- **R2 — Tinggi (Fase A):** 13 subtask dalam 2,5 hari, unduhan dataset tak terprediksi. Jika slippage: prioritas A1–A12; A13 (Dataset Card) wajib untuk acceptance dan harus tuntas paling lambat awal Fase 3.
- **R3 — Tinggi (Fase D):** 13 subtask dalam 2 hari. Usulan: izinkan D1–D7 dimulai paralel pada Fase 2/3 (penulisan test berbasis kontrak, tidak butuh modul selesai); keputusan menunggu persetujuan koordinator.
- **R4 — Sedang (Fase B):** Sabtu 24 Okt belum tentu hari kerja. Bila tidak tersedia, jadwal B dipadatkan ke Kam 22 / Jum 23 / Sen 26 dengan buffer 4 jam penuh.
- **R5 — Rendah–Sedang (Gerbang E):** kegagalan logger environment anggota menghentikan coding anggota tersebut (aturan Issue #6); seluruh anggota wajib lolos smoke test sebelum Sen 19 Okt 17.00.
- **R6 — Proses:** assignment GitHub per anggota belum dilakukan; koordinator perlu menyelesaikan agar status Issue terlacak.
- **Prioritas MVP (hanya saat slippage, tanpa menghapus acceptance criteria):** 1) A — tokenizer + dataset + no-leakage + no-window-crossing; 2) B — PE + causal MHA + DecoderBlock + gradient mengalir; 3) C — training loop + checkpoint + data asli; 4) generation (C12–C13) dan integrasi penuh (D11–D13) sebagai lapisan terakhir, semuanya tetap wajib tuntas sebelum **30 Okt 2026, 17.00 WIB**.
