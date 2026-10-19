## 0. Pemilik tugas

- **Pemilik (rekomendasi):** Rafa Suryaputra — Documentarian & Error Handler, berkoordinasi dengan seluruh anggota.

## 1. Tujuan

Memvalidasi mekanisme logging otomatis lintas AI agent yang berbeda: menjalankan smoke test pada environment setiap anggota, memverifikasi prompt/respons/event terekam di raw log, laporan Markdown konsisten, redaksi kredensial berfungsi, dan setiap laporan dapat ditelusuri ke sesi dan Issue terkait.

## 2. Konteks teknis dan file terkait

- `docs/AI_RULES.md` §6 (logging), `docs/AI_LOG_TEMPLATE.md`, `docs/ARCHITECTURE_DECISIONS.md` ADR-006.
- ADR-006 mencatat: plugin `.kilo/plugin/mini-transformer-logger.ts` aktif dan teruji hanya untuk anggota `raihanfahrifi-80017` (dua sesi); ini BUKAN bukti anggota lain lulus — tiap anggota wajib menjalankan smoke test sendiri.
- Target: `docs/ai-logs/raw/<member-id>/*.jsonl` dan `docs/ai-logs/reports/*.md`.

## 3. Ruang lingkup

1. Menyusun daftar agent/model yang benar-benar dipakai setiap anggota (tool, model, versi adapter logging).
2. Menjalankan smoke test logging pada masing-masing environment; sesi uji berisi prompt + respons nyata.
3. Memverifikasi raw JSONL berisi prompt aktual dan respons yang terlihat; laporan Markdown konsisten dengan raw.
4. Memeriksa redaksi konten sensitif (API key, token, password) dan validitas JSONL (parseable).
5. Memastikan setiap laporan dapat ditelusuri ke sesi dan Issue/PR terkait.
6. Mencatat keterbatasan adapter per agent dan memperbaikinya bila diperlukan.
- Koordinasi: dengan seluruh anggota untuk jadwal smoke test masing-masing.

## 4. Di luar scope

- Implementasi modul model/pipeline (Issues A–D).
- Mengklaim logging berhasil untuk anggota lain tanpa bukti smoke test.
- Menulis atau mengganti mekanisme logging inti modul proyek.

## 5. Dependensi

- Dapat dikerjakan paralel penuh dengan Issues A–D.
- Berlaku sebagai gerbang: sebelum anggota mulai pekerjaan coding yang wajib dicatat, logging environment anggota tersebut harus sudah lolos.
- Hasil verifikasi logger menjadi input ADR-006 (pembaruan tingkat verifikasi) bila disetujui tim.

## 6. Interface dan kontrak (dari dokumen)

- Raw log: JSONL di `docs/ai-logs/raw/<member-id>/` (ADR-006).
- Laporan: Markdown mengikuti `docs/AI_LOG_TEMPLATE.md` (metadata, kronologi prompt-respons, debugging, verifikasi, refleksi).
- Aturan: raw log adalah bukti; ringkasan AI bukan pengganti raw log (`AI_RULES.md` §6).
- Redaksi: tanpa API key, token, password, data pribadi (`AI_RULES.md` §6, `AGENTS.md`).

## 7. Task checklist berurutan

Kerjakan **satu subtask pada satu waktu**, dari atas ke bawah. Jangan menganggap logging seluruh tim lulus hanya berdasarkan log milik satu anggota.

- [ ] **E1. Data agent, model, dan metode penggunaan yang dipakai setiap anggota.** Catat tool/agent tiap anggota (Kilo, Cursor, dll.), model yang dipakai, dan adapter logging yang tersedia. *Hasil:* daftar environment per anggota.
- [ ] **E2. Verifikasi konfigurasi logger masing-masing.** Periksa path raw log `<member-id>/`, format JSONL, redaksi, dan keterkaitan template laporan untuk setiap anggota. *Hasil:* konfigurasi logger per anggota dipastikan.
- [ ] **E3. Jalankan satu smoke test unik untuk setiap anggota.** Setiap anggota menjalankan sesi uji sendiri berisi prompt + respons nyata pada environment-nya. *Hasil:* bukti smoke test per anggota (bukan hanya milik `raihanfahrifi-80017`).
- [ ] **E4. Pastikan prompt dan respons benar-benar tercatat dalam JSONL.** Periksa teks prompt uji dan respons yang terlihat muncul persis (bukan ringkasan) di raw log; semua baris JSONL parseable. *Hasil:* verifikasi isi raw log per anggota.
- [ ] **E5. Pastikan laporan Markdown terbentuk.** Tiap smoke test menghasilkan laporan sesuai `AI_LOG_TEMPLATE.md` (metadata, kronologi, verifikasi). *Hasil:* file `.md` ada per anggota.
- [ ] **E6. Verifikasi laporan terhadap raw log.** Cek konsistensi field (session ID, timestamp, link Issue) antara laporan dan raw log; laporan bukan salinan ringkasan tanpa landasan raw. *Hasil:* konsistensi terdokumentasi.
- [ ] **E7. Periksa redaksi API key, token, password, dan informasi sensitif.** Cari pola secret sebelum/sesudah redaksi di raw log; pastikan tidak ada yang lolos. *Hasil:* hasil pemeriksaan redaksi per anggota.
- [ ] **E8. Pastikan file tersimpan pada lokasi yang ditentukan.** Raw log di `docs/ai-logs/raw/<member-id>/`, laporan di `docs/ai-logs/reports/`. *Hasil:* lokasi file diverifikasi di repo.
- [ ] **E9. Dokumentasikan tool yang berhasil, gagal, atau memiliki keterbatasan.** Catat adapter mana yang lolos, gagal, atau punya batasan (field hilang, redaksi lambat, dll.); perbaiki bila memungkinkan. *Hasil:* matriks status adapter per tool.
- [ ] **E10. Pastikan setiap anggota memiliki bukti verifikasi sendiri.** Setiap anggota menyimpan bukti smoke test (raw + laporan) untuk tool yang dipakainya; tidak ada klaim silang tanpa bukti. *Hasil:* bukti verifikasi per anggota lengkap.

## 8. Instruksi pengerjaan setiap subtask

1. Baca kembali bagian spesifikasi yang relevan (`AI_RULES.md` §6, `AI_LOG_TEMPLATE.md`, ADR-006).
2. Minta AI menjelaskan tujuan subtask, format raw JSONL vs laporan Markdown, dan cara memverifikasi tanpa menebak SEBELUM menulis/eksekusi.
3. Kerjakan satu subtask saja; koordinasikan jadwal smoke test dengan anggota terkait.
4. Jalankan pemeriksaan (parse JSONL, grep secret, bandingkan field) dan catat output aktual.
5. Jika logger gagal di environment anggota: hentikan coding proyek anggota itu, beri tahu koordinator, perbaiki logger dulu — jangan lanjut.
6. Simpan log AI dari pekerjaan Issue E itu sendiri (smoke test adalah bukti logging).
7. Minta review kepada koordinator/anggota lain sebelum menyatakan subtask selesai.
8. Centang checkbox subtask hanya setelah hasil benar-benar terverifikasi.

## 9. Aturan berhenti

- Setelah satu subtask selesai dan diverifikasi, **berhenti**. Jangan mengerjakan subtask berikutnya tanpa instruksi eksplisit.
- Jika smoke test seorang anggota gagal, jangan melanjutkan steps lain untuk anggota itu sampai loggernya diperbaiki.
- Jangan menganggap logging seorang anggota "lulus" berdasarkan log atau klaim anggota lain.
- Jangan mengarang baris JSONL, laporan, atau hasil pemeriksaan redaksi; dilarang menulis secret ke log.

## 10. Acceptance criteria (wajib benar-benar diuji)

- [ ] Setiap anggota memiliki bukti smoke test tertulis pada tool yang dipakainya.
- [ ] Prompt uji dan respons benar-benar ada di raw log (bukan ringkasan).
- [ ] Laporan Markdown dihasilkan dan konsisten dengan raw log.
- [ ] Tidak ada klaim "logging berhasil" tanpa bukti.
- [ ] Log tidak mengandung API key, token, password, atau informasi sensitif (verifikasi redaksi dijalankan).
- [ ] File log dan laporan tersimpan di `docs/ai-logs/`.
- [ ] Setiap subtask E1–E10 memiliki bukti berupa output aktual atau pemeriksaan yang dijalankan.

## 11. Unit test / pemeriksaan yang diperlukan

- Pemeriksaan JSONL valid (parse seluruh baris).
- Pemeriksaan prompt dan respons uji muncul persis di raw log.
- Pemeriksaan redaksi: cari pola secret (key/token/password) pada raw log sebelum dan sesudah redaksi.
- Cek konsistensi field laporan Markdown terhadap raw log (session ID, timestamp, issue link).

## 12. Aturan logging AI

- Pekerjaan Issue E itu sendiri juga dicatat (smoke test = bukti logging).
- Jika logger gagal pada environment anggota, hentikan coding proyek anggota tersebut hingga logger diperbaiki; laporkan ke koordinator.
- Dilarang menulis API key, token, password, atau data sensitif ke log.

## 13. Dokumentasi yang harus diperbarui

- Laporan smoke test per anggota di `docs/ai-logs/reports/`.
- Catatan keterbatasan adapter per agent (dokumentasi teknis di `docs/ai-logs/` atau ADR-006 bila disetujui tim).