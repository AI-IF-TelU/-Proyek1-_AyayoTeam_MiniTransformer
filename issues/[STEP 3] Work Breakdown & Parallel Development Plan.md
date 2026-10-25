## Tujuan dan ruang lingkup

Membagi pekerjaan Mini-Transformer menjadi empat unit kerja paralel yang masing-masing dapat dikerjakan oleh satu anggota menggunakan AI coding agent yang berbeda, berdasarkan kontrak final `docs/TECH_SPEC.md` (dikunci pada Issue #1). Issue ini adalah pusat pemantauan seluruh pekerjaan Step 3.

Ruang lingkup: hanya pembagian kerja + definisi Issue dan acceptance criteria. Tidak ada implementasi kode pada Issue ini.

## Daftar Issue implementasi

| Issue | Judul | Pemilik yang direkomendasikan | Status |
|---|---|---|---|
| [#2](https://github.com/AI-IF-TelU/AyayoTeam_MiniTransformer/issues/2) | [STEP 3] Issue A — Data Pipeline & Tokenizer | Dzaki Alwan | Menunggu |
| [#4](https://github.com/AI-IF-TelU/AyayoTeam_MiniTransformer/issues/4) | [STEP 3] Issue B — Implementasi Komponen Inti Transformer | Muhammad Raihan Fahrifi | Menunggu |
| [#3](https://github.com/AI-IF-TelU/AyayoTeam_MiniTransformer/issues/3) | [STEP 3] Issue C — MiniGPT, Training Loop & Text Generation | Firdaus Akbar Amrullah | Menunggu |
| [#5](https://github.com/AI-IF-TelU/AyayoTeam_MiniTransformer/issues/5) | [STEP 3] Issue D — Unit Test, Integrasi & Dokumentasi Teknis | Rafa Suryaputra | Menunggu |

Catatan assignment: pemilik di atas adalah rekomendasi. Assignment GitHub belum dilakukan karena verifikasi username belum lengkap; koordinator dapat menugaskan setelah username tiap anggota terverifikasi di organisasi.

## Urutan pengerjaan yang disarankan

Tim ingin bekerja **bertahap dengan satu anggota aktif pada satu waktu** (bukan paralel penuh). Urutan direkomendasikan:

1. **Dzaki Alwan** → Issue A (Data Pipeline & Tokenizer) — fondasi semua training.
2. **M. Raihan Fahrifi** → Issue B (Komponen Inti Transformer) — fondasi model.
3. **Firdaus Akbar Amrullah** → Issue C (MiniGPT, Training & Generation) — rakitan + training, setelah A dan B siap.
4. **Rafa Suryaputra** → Issue D (Unit Test & Integrasi) — koordinasi tes lintas modul setelah A, B, C selesai.

Meskipun kontrak memungkinkan paralel, pengerjaan bertahap mengurangi risiko konflik integrasi dan memungkinkan setiap anggota memahami hasil anggota sebelumnya.

## Hubungan dependensi antartugas

- **Issue A → C**: Issue C mengonsumsi tokenizer/loader dari A untuk training sungguhan.
- **Issue B → C**: integrasi final MiniGPT menunggu komponen inti (B) lulus tes; kerangka C boleh dibangun dengan mock lebih dulu.
- **Issue A, B → D**: integrasi tes penuh menunggu modul A dan B tersedia.
- **Issue C → D**: tes training/generation masuk ke D setelah C tersedia.

## Tugas yang dapat dikerjakan paralel

- A dan B (paralel penuh; kontrak sudah dikunci).
- D (mulai test berbasis kontrak tanpa menunggu implementasi; integrasi penuh menunggu A/B/C).
- C (kerangka + interface dengan mock; integrasi final menunggu B).

## Tugas yang harus menunggu

- Integrasi final MiniGPT (C) menunggu Issue B lulus tes.
- Training sungguhan (C) menunggu data dari A.
- Integrasi tes (D) menunggu A, B, C tersedia untuk dieksekusi bersama.

## Pembagian tanggung jawab

| Anggota | Peran | Issue |
|---|---|---|
| Muhammad Raihan Fahrifi | Prompt Engineer & LLM Navigator | B (komponen inti) |
| Dzaki Alwan | Data Pipeline Engineer | A (data & tokenizer) |
| Firdaus Akbar Amrullah | Training Loop Engineer | C (MiniGPT, training, generation) |
| Rafa Suryaputra | Documentarian & Error Handler | D (test/integrasi) |

Setiap anggota: bekerja langsung di branch `master` (master-only, tanpa branch baru, tanpa PR/merge). Perubahan direview anggota lain sebelum commit dan push ke `master`.

## Status logging tiap anggota

| Anggota | Tool | Status logging | Catatan |
|---|---|---|---|
| Muhammad Raihan Fahrifi | Kilo | ✅ Lulus (terverifikasi, ADR-006) | Plugin `.kilo/plugin/mini-transformer-logger.ts`, raw & reports tersedia |
| Dzaki Alwan | Kilo | ✅ Lulus (terverifikasi) | 12 report (`AI-LOG-dzakialwanf-80006-*`) & raw JSONL tersedia |
| Firdaus Akbar Amrullah | Kilo | ✅ Lulus (terverifikasi) | Sesi smoke test `AI-LOG-firdausakbar-80011-*` & raw JSONL tersedia |
| Rafa Suryaputra | Kilo | ✅ Lulus (terverifikasi) | 30 report (`AI-LOG-rafasuryaputra-80048-*`) & raw JSONL tersedia |

## Checklist review serta integrasi

- [ ] Setiap anggota bekerja master-only (tanpa branch baru), push langsung ke `master`.
- [ ] Setiap perubahan ditinjau anggota selain pembuatnya sebelum push ke `master`.
- [ ] Test kontrak lokal tiap modul lulus sebelum push ke `master`.
- [ ] Issue D menjalankan tes integrasi setelah seluruh modul tersedia.
- [ ] Acceptance criteria Issue #2–#5 terverifikasi dengan bukti aktual.
- [ ] `DATASET_CARD.md` diisi hasil aktual dari Issue A.
- [ ] Laporan eksperimen disusun berdasarkan hasil nyata, bukan dikarang.

## Catatan hambatan dan keputusan yang masih tertunda

- **Assignment GitHub:** dianggap selesai per keputusan koordinator (2026-10-19). Assignment GitHub aktual dikerjakan koordinator/anggota secara manual; tidak diverifikasi via API oleh AI agent.
- **Framework testing:** **`pytest`** ditetapkan koordinator (2026-10-19) sebagai runner resmi. Issue D D2 menggunakannya tanpa izin tambahan.
- **Struktur file final (keputusan koordinator 2026-10-19, Opsi 1):** tetap persis per kontrak TECH_SPEC §6 — `src/data/tokenizer.py`, `src/data/dataset.py`, `src/model/{positional_encoding,attention,decoder_block,minigpt}.py`, `src/train.py`, `src/generate.py`, opsional `src/config.py`. Tidak ada `src/data/preprocessing.py`, `scripts/prepare_data.py`, `src/training/`, `src/generation/`, `configs/`. Kalimat "dikonfirmasi saat integrasi" pada Issue A §2 dan Issue B §2 telah diubah menjadi "dikonfirmasi koordinator 2026-10-19".
- **Format metrik output:** **JSONL** (keputusan koordinator 2026-10-19; ADR-011) — menggantikan pilihan ganda CSV/JSONL pada TECH_SPEC §6 dan Issue C.
- **Jumlah subset dataset & strategi split (keputusan koordinator 2026-10-19):** subset = **1.000 artikel**; split bawaan train/test (25.8k/6.46k) dipertahankan tanpa resplit; validation diambil 10% dari split train (seed 42); fallback 80/10/10 **tidak dipakai** (ADR-012). *Diamendemen untuk C15:* subset **1.800 artikel** (ADR-015); strategi split tetap sama.
- **Kerja di `master` langsung (master-only):** seluruh anggota bekerja pada satu branch `master`. Dilarang membuat branch baru, pull request, atau merge. `git pull --ff-only origin master` hanya dijalankan saat anggota lain mengabarkan telah push (pengerjaan berurutan, saling menunggu).

## Acceptance criteria keseluruhan

- [ ] Seluruh Issue #2–#5 didefinisikan sesuai kontrak `docs/TECH_SPEC.md` dan dapat langsung dikerjakan.
- [ ] Tidak ada duplikat dengan Issue yang sudah ada (Issue #1 tetap closed, riwayat tidak diubah).
- [ ] A: tokenizer/dataset sesuai §3–§4; tidak ada vocab leakage; tidak ada window lintas dokumen; Dataset Card diperbarui.
- [ ] B: implementasi manual PE, causal MHA, DecoderBlock (pre-norm, FFN GELU) tanpa `nn.Transformer*`/`nn.MultiheadAttention`; shape dan causal mask teruji.
- [ ] C: MiniGPT logits `[B, T, V]`; training berjalan; loss tercatat; checkpoint lengkap; generation greedy teruji; hasil aktual dilaporkan jujur.
- [ ] D: seluruh tes konsisten dan memeriksa perilaku; hasil aktual dicatat; integrasi tanpa ubah kontrak sepihak.
- [ ] Setiap Issue yang dibuat sesuai format 10 bagian (tujuan, konteks, scope, non-scope, dependensi, kontrak, acceptance criteria, test, aturan logging, dokumentasi).
- [ ] Setiap anggota bekerja master-only (tanpa branch baru); review lintas anggota sebelum push ke `master`.
- [ ] Semua task checklist Issue #2–#5 memiliki checkbox status yang mencerminkan kemajuan aktual (tidak dicentang otomatis).

## Batasan

- Jangan menutup Issue yang baru dibuat sebelum acceptance criteria terpenuhi.
- Jangan mengubah interface, dependency, atau keputusan arsitektur tanpa persetujuan dan pencatatan ADR.
- Jangan mengarang status pengujian, bukti dataset, atau persetujuan anggota.
- Jangan mengubah Issue #1 (closed, riwayat tidak diubah).
- Jika direct push ke `master` tidak diizinkan oleh proteksi repository, jangan mencoba melewati proteksi.

## Risiko dan prioritas MVP (tidak menghapus acceptance criteria wajib)

- **R1 — Tinggi (Fase C):** 14 subtask dalam 2,5 hari + dua dependensi. Jika slippage: utamakan C1–C11 (kerangka, training loop, checkpoint, data asli); C12–C13 (generation + aturan stop) tetap wajib dan digeser ke jam buffer Fase D; C14 boleh eksperimen sebagian epoch.
- **R2 — Tinggi (Fase A):** 13 subtask dalam 2,5 hari, unduhan dataset tak terprediksi. Jika slippage: prioritas A1–A12; A13 (Dataset Card) wajib untuk acceptance dan harus tuntas paling lambat awal Fase 3.
- **R3 — Tinggi (Fase D):** 13 subtask dalam 2 hari. Usulan: izinkan D1–D7 dimulai paralel pada Fase 2/3 (penulisan test berbasis kontrak, tidak butuh modul selesai); keputusan menunggu persetujuan koordinator.
- **R4 — Sedang (Fase B):** Sabtu 24 Okt belum tentu hari kerja. Bila tidak tersedia, jadwal B dipadatkan ke Kam 22 / Jum 23 / Sen 26 dengan buffer 4 jam penuh.
- **R5 — Proses:** assignment GitHub per anggota belum dilakukan; koordinator perlu menyelesaikan agar status Issue terlacak.
- **Prioritas MVP (hanya saat slippage, tanpa menghapus acceptance criteria):** 1) A — tokenizer + dataset + no-leakage + no-window-crossing; 2) B — PE + causal MHA + DecoderBlock + gradient mengalir; 3) C — training loop + checkpoint + data asli; 4) generation (C12–C13) dan integrasi penuh (D11–D13) sebagai lapisan terakhir, semuanya tetap wajib tuntas sebelum **30 Okt 2026, 17.00 WIB**.
