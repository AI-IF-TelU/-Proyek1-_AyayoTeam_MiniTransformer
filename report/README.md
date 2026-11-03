# Ayayo MiniTransformer — Laporan Proyek

> **Mini-GPT Bahasa Indonesia berbasis Decoder-only Transformer**  
> Repository: [AI-IF-TelU/-Proyek1-_AyayoTeam_MiniTransformer](https://github.com/AI-IF-TelU/-Proyek1-_AyayoTeam_MiniTransformer)  
> Tim: Ayayo Team • 4 anggota • Periode pengembangan tercatat: 14–25 Oktober 2026
> - Rafa Suryaputra - NIM 103012580048
> - Firdaus Akbar Amrullah - NIM 103012580011
> - Dzaki Alwan Firjatullah - NIM 103012580006
> - Muhammad Raihan Fahrifi - NIM 103012580017


## Ringkasan

Ayayo MiniTransformer adalah proyek pembelajaran untuk membangun model bahasa generatif kecil berbahasa Indonesia dari nol. Model mempelajari pola teks berita dan menghasilkan kelanjutan teks dengan memperkirakan token berikutnya berdasarkan konteks sebelumnya.

Model menggunakan **arsitektur Decoder-only Transformer bergaya GPT**. Komponen inti seperti positional encoding sinusoidal, causal multi-head self-attention, decoder block, dan training loop diimplementasikan sendiri menggunakan operasi dasar PyTorch. Proyek tidak menggunakan bobot pretrained GPT/BERT maupun API GPT sebagai model utama, serta tidak mengganti implementasi inti dengan `nn.Transformer` atau `nn.MultiheadAttention`.

Proyek berorientasi pendidikan dan demonstrasi. Keluaran model bukan berita terverifikasi dan tidak boleh diperlakukan sebagai sumber fakta terkini.

## 1. Latar Belakang dan Tujuan

Teks merupakan data berurutan. Posisi dan hubungan antar-token memengaruhi makna, sehingga model bahasa perlu mempelajari pola urutan tersebut. Proyek ini menjadi sarana untuk mempelajari cara kerja Transformer generatif secara langsung, bukan sekadar menggunakan model bahasa siap pakai.

Tujuan proyek:
1. Menyiapkan korpus berita Indonesia untuk tugas *language modeling*.
2. Membangun tokenizer dan proses pembentukan pasangan input-target untuk prediksi token berikutnya.
3. Mengimplementasikan arsitektur Decoder-only Transformer, termasuk causal attention dan positional encoding, secara mandiri.
4. Melatih model, mengevaluasi loss, menyimpan checkpoint, dan menghasilkan kelanjutan teks.
5. Menguji komponen dan integrasi serta mendokumentasikan keputusan dan proses pengembangan.

## 2. Metode

### 2.1 Autoregressive Language Modeling

Metode pembelajaran adalah **autoregressive language modeling dengan next-token prediction**. Model membaca rangkaian token dan belajar memperkirakan token setelahnya. Target pelatihan berasal langsung dari teks, sehingga pendekatan ini termasuk *self-supervised learning* dan tidak membutuhkan label kelas yang dibuat manual.

Contoh sederhana:
- Input: `saya sedang membaca`
- Target: token setelah kata `membaca` pada teks sumber.

Dalam training, urutan digeser satu posisi. Model menerima token sebelumnya dan diminta memprediksi token target pada posisi berikutnya.

### 2.2 Loss dan Optimisasi

- **Loss:** Cross-Entropy Loss untuk mengukur perbedaan prediksi probabilitas model dengan token target. Token padding diabaikan dari perhitungan loss.
- **Optimizer:** AdamW untuk memperbarui bobot berdasarkan gradien.
- **Proses:** *forward pass* → hitung loss → *backpropagation* → pembaruan bobot. Proses berulang per batch dan epoch.
- **Evaluasi:** validation loss dipantau selama training. Checkpoint C15 dipilih berdasarkan validation loss terbaik.

### 2.3 Strategi Generasi

Implementasi menyediakan **greedy decoding** dan **sampling terkontrol**. Fungsi `generate()` menggunakan greedy sebagai perilaku dasar, sedangkan `generate_ids()` mendukung konfigurasi sampling. Helper demonstrasi C15 menggunakan sampling dengan `temperature=1.1`, `top_p=0.9`, `repetition_penalty=1.1`, dan pembatasan n-gram berulang. Strategi ini mengubah cara memilih token saat inferensi, bukan arsitektur atau bobot model.

## 3. Dataset

Sumber data: [Indonesian News Datasets di Hugging Face](https://huggingface.co/datasets/fahadh4ilyas/indonesian_news_datasets).

Proyek menggunakan kolom **`content`**, yaitu isi artikel berita. Data digunakan sebagai teks untuk language modeling, bukan sebagai dataset klasifikasi.

### Eksperimen C15 (hasil akhir utama)

| Split | Artikel | Token (tanpa BOS/EOS) |
|---|---:|---:|
| Train | 1.440 | 567.989 |
| Validation | 159 | 71.188 |
| Test | 200 | 77.330 |
| **Total** | **1.799** | **716.507** |

Informasi penting:
- Dataset diambil dari split `train` (1.600 artikel) dan `test` (200 artikel) pada revision `13f841935cf1adbe3e41e474bf926e49a0e2943e`.
- Setelah konten kosong dibuang dan deduplikasi dilakukan, 1.799 artikel unik dipakai.
- Validation diambil 10% dari bagian train secara deterministik dengan seed 42. Pembagian dilakukan pada tingkat dokumen sebelum tokenisasi dan pembuatan window.
- Tokenizer dibangun hanya dari data train. C15 memakai `min_freq=2` dan menghasilkan vocabulary 16.278 token, termasuk empat token khusus.
- Tingkat `<unk>` yang tercatat: 4,93% pada validation dan 4,68% pada test.
- Lisensi yang dicantumkan dataset: CC BY-NC 4.0. Hak dan ketentuan artikel sumber tetap perlu diperhatikan saat penggunaan atau distribusi ulang.

**Catatan:** C14 merupakan eksperimen sebelumnya dengan korpus dan konfigurasi berbeda (720/80/200 artikel; vocabulary 19.192; konteks 64). Angka C14 dan C15 tidak boleh dibandingkan sebagai eksperimen yang sepenuhnya setara.

## 4. Model yang Dibangun

Model adalah **Decoder-only Transformer kecil (MiniGPT)**. Berbeda dari BERT yang umumnya memakai encoder dan bidirectional attention, model ini menggunakan *causal self-attention*: token hanya dapat memperhatikan token di posisi sebelumnya dan dirinya sendiri, bukan token masa depan.

Alur utama model:
1. **Token embedding:** mengubah ID token menjadi vektor angka.
2. **Sinusoidal positional encoding:** menambahkan informasi posisi token menggunakan pola sinus dan cosinus.
3. **Decoder blocks:** memproses konteks melalui beberapa lapisan Pre-LayerNorm, causal multi-head self-attention, residual connection, dan FFN dengan aktivasi GELU.
4. **Final LayerNorm dan Language Modeling Head:** mengubah representasi menjadi skor untuk setiap token dalam vocabulary.
5. **Next-token prediction:** skor digunakan untuk menentukan probabilitas token kelanjutan.

### Konfigurasi C15

| Parameter | Nilai |
|---|---:|
| Jumlah decoder layer | 4 |
| Jumlah attention head | 4 |
| Dimensi embedding (`d_model`) | 64 |
| Dimensi FFN (`d_ff`) | 256 |
| Panjang konteks | 128 token |
| Vocabulary | 16.278 token |
| Dropout | 0,2 |
| Weight tying | Aktif |
| Jumlah parameter | 1.241.856 |

Arsitektur inti dibuat manual menggunakan operasi dasar PyTorch. Komponen standar seperti `nn.Linear`, `nn.Embedding`, autograd, loss, dan optimizer digunakan sebagai building blocks.

## 5. Implementasi dan Alur Sistem

```text
Hugging Face dataset (kolom content)
          ↓
Unduh subset dan simpan data mentah
          ↓
Pembersihan, normalisasi, deduplikasi, split dokumen
          ↓
Tokenizer dan vocabulary dari train
          ↓
Tambah BOS/EOS, sliding window, padding dan batching
          ↓
MiniGPT: Embedding + Positional Encoding + Decoder Blocks
          ↓
Language Modeling Head menghasilkan logits
          ↓
Cross-Entropy Loss → Backpropagation → AdamW
          ↓
Validasi, pencatatan metrik, pemilihan checkpoint
          ↓
Greedy decoding / sampling → post-processing → teks
```

### Bagian implementasi utama

| Area | Peran |
|---|---|
| `src/data/tokenizer.py` | Tokenisasi regex, vocabulary, encode/decode |
| `src/data/dataset.py` | Data input-target, sliding window dan batching |
| `src/model/positional_encoding.py` | Positional encoding sinusoidal |
| `src/model/attention.py` | Q/K/V, causal mask, multi-head attention |
| `src/model/decoder_block.py` | Pre-LayerNorm, residual, attention, FFN dan GELU |
| `src/model/minigpt.py` | Menggabungkan embedding, decoder, normalisasi dan LM head |
| `src/train.py` | Training step, evaluasi, metrik dan checkpoint |
| `src/generate.py` | Greedy decoding dan sampling terkontrol |
| `src/postprocess.py` | Perapian teks hasil generasi |
| `kaggle_c15.ipynb` | Eksperimen training C15 di Kaggle |

## 6. Eksperimen dan Hasil

### 6.1 C14 — Baseline awal

C14 dijalankan menggunakan Modal dengan CPU 8 core, selama 4 epoch, sekitar 5.304,64 detik (88,4 menit). Loss training turun dari 5,5686 menjadi 3,3356, sedangkan validation loss naik dari 7,1352 menjadi 8,6499. Pola ini menunjukkan indikasi overfitting pada run tersebut: model semakin baik pada data training, tetapi validation loss memburuk.

### 6.2 C15 — Eksperimen lanjutan

| Aspek | Hasil |
|---|---:|
| Epoch yang dijalankan | 20 |
| Epoch checkpoint terbaik | 14 |
| Perangkat | Kaggle, NVIDIA Tesla T4 |
| Durasi | 7.481,21 detik (sekitar 124,7 menit) |
| Jumlah parameter | 1.241.856 |
| Validation loss per dokumen (best) | 5,028038 ± 0,111551 |
| Test loss per dokumen | 5,009093 ± 0,097116 |

Checkpoint terbaik dipilih pada epoch 14 berdasarkan validation loss, bukan otomatis checkpoint terakhir. C15 memakai protokol evaluasi per dokumen dan mengecualikan `<unk>` pada angka utama yang dilaporkan. Karena konfigurasi dan protokol berbeda dari C14, hasil ini tidak membuktikan peningkatan kualitas hanya karena satu perubahan tertentu.

### 6.3 Keluaran Model

Model dapat menghasilkan kelanjutan teks berbahasa Indonesia dari sebuah prompt. Keluaran bersifat generatif dan dapat terdengar menyerupai berita, tetapi tidak diverifikasi terhadap sumber aktual. Model dapat mengulang kata, membuat hubungan kalimat yang tidak tepat, atau menghasilkan klaim keliru. Hasil generasi hanya digunakan sebagai demonstrasi kemampuan model.

## 7. Pengujian dan Validasi

Pengujian mencakup kontrak bentuk tensor, causal mask, training step, checkpoint, generation, serta integrasi antarbagian.

| Perintah | Hasil |
|---|---:|
| `python -m pytest -q` | 221 passed, 16 skipped |
| `python -m pytest -q --run-integration` | 236 passed, 1 skipped |
| `python -m pytest -q -m integration --run-integration` | 15 passed, 222 deselected |
| `python -m pytest --collect-only -q --run-integration` | 237 tests collected |

Satu test yang tetap dilewati pada mode integrasi adalah test CUDA karena lingkungan audit yang digunakan CPU-only. Hasil test memverifikasi perilaku dan kontrak perangkat lunak, bukan menjamin kualitas faktual teks yang dihasilkan.

## 8. Penggunaan AI dalam Pengembangan

Proyek menerapkan pendekatan **Vibe Coding / AI-assisted development** dengan aturan dan jejak terdokumentasi. AI coding agent digunakan sebagai pendamping untuk analisis tugas, perencanaan implementasi, bantuan penulisan/perbaikan kode, penjelasan, dan dukungan pengujian. Kode inti dan keputusan tetap harus mengikuti spesifikasi proyek, ditinjau, diuji, serta dipahami oleh anggota tim.

Praktik pengelolaan AI:
- Instruksi utama tersedia di `AGENTS.md`, `docs/AI_RULES.md`, dan dokumen spesifikasi.
- Pekerjaan dibagi per Issue dan subtask dengan batas file serta acceptance criteria.
- Prompt, respons, event tool, dan error dicatat melalui plugin logger Kilo Code ke `docs/ai-logs/`.
- Raw log menjadi bukti; ringkasan tidak menggantikan log asli. Konten sensitif harus di-redact.
- AI tidak digunakan sebagai model bahasa utama yang menghasilkan output proyek. MiniGPT dilatih dari nol menggunakan dataset dan implementasi tim.

**Batas bukti:** keberadaan logger, laporan, dan aturan membuktikan mekanisme pencatatan dirancang dan digunakan pada sesi tertentu. Hal tersebut tidak otomatis membuktikan semua interaksi semua anggota selalu terekam sempurna.

## 9. Manajemen Proyek

Tim menggunakan kombinasi **Agile Kanban**, **Contract-First Development**, dan workflow **master-only**.

- Pekerjaan dikelola melalui GitHub Issues dan checklist subtask.
- Kontrak antarmodul, interface, bentuk tensor, dan keputusan arsitektur ditetapkan sebelum integrasi.
- Setiap subtask dikerjakan, diuji, ditinjau, lalu di-commit dan di-push.
- Pengembangan dilakukan bergiliran pada branch `master`; panduan proyek melarang anggota membuat branch baru, PR, atau merge.
- Keputusan desain dicatat dalam Architecture Decision Records (ADR), sedangkan spesifikasi teknis menjadi acuan bersama.
- Pengujian dan log AI digunakan sebagai bukti penyelesaian.

### Tahapan kerja utama

1. **Issue A — Data Pipeline & Tokenizer:** pengunduhan subset, pembersihan, split, tokenizer, dataset, dan DataLoader.
2. **Issue B — Komponen Inti Transformer:** positional encoding, attention, decoder block, dan integrasi komponen.
3. **Issue C — MiniGPT, Training & Generation:** konfigurasi model, model utama, training/evaluasi, checkpoint, serta generasi teks.
4. **Issue D — Unit Test, Integrasi & Dokumentasi:** fixtures, pengujian kontrak dan integrasi, perbaikan regresi, serta laporan hasil audit.
5. **C15 — Eksperimen lanjutan:** perubahan subset, konfigurasi model, evaluasi dan training di Kaggle, serta pencatatan keputusan eksperimen.

## 10. Pembagian Peran Anggota

Pembagian berikut menggabungkan penugasan Issue di README dengan jejak commit yang terlihat pada repository. Commit menunjukkan identitas akun/author yang tercatat, bukan ukuran mutlak jumlah kerja atau bukti bahwa kontribusi hanya dilakukan oleh satu orang.

| Anggota | Peran utama | Bukti pada commit history |
|---|---|---|
| **Dzaki Alwan Firjatullah** | Issue A — Data Pipeline & Tokenizer | Rangkaian commit `feat (Issue A): Subtask A5` sampai `A13`, perbaikan subtask, dan pengujian akhir Issue A. |
| **Muhammad Raihan Fahrifi** | Issue B — Komponen Inti Transformer | Rangkaian commit Subtask B1–B14 dan bug fix Issue B. Juga terlihat membantu perbaikan data pada Issue A serta mengerjakan perubahan lanjutan dan eksperimen C15. |
| **Firdaus Akbar Amrullah** | Issue C — MiniGPT, Training & Generation | Commit `feat(Issue C): Subtask C1-C3` hingga subtask berikutnya, perbaikan `train.py`, serta kontribusi implementasi training/generation. README menetapkan Issue C sebagai tanggung jawab utamanya. |
| **Rafa Suryaputra** | Issue D — Unit Test, Integrasi & Dokumentasi | Rangkaian commit `feat(Issue D): Subtask D1` sampai `D13`, perbaikan Issue D, dan artefak pengujian/dokumentasi. |

### Catatan atribusi commit

- Nama/akun pada commit dapat berbeda karena konfigurasi identitas Git. Penugasan Issue resmi pada README menjadi dasar peran utama.
- Sejumlah commit `fahritech04` mencakup pekerjaan lintas area. Repository mengaitkan akun tersebut dengan perubahan subtask Issue B dan eksperimen C15; pemetaan akun ke nama anggota mengikuti konsistensi penugasan dan pola commit, bukan metadata Git yang secara eksplisit memuat identitas akademik.
- Commit author tidak selalu sama dengan pihak yang mengoperasikan tool atau membantu pekerjaan. Karena itu jumlah commit tidak dipakai sebagai pembobot kontribusi individu.

## 11. Luaran Proyek

Luaran yang tersedia di repository meliputi:
1. Source code pipeline data, tokenizer, model Decoder-only Transformer, training dan generation.
2. Dataset hasil olahan berupa split train, validation, dan test beserta dataset card dan metadata.
3. Notebook eksperimen C15 dan skrip pendukung training.
4. Checkpoint model dan metrik eksperimen C14/C15 pada direktori output proyek (artefak besar dapat dikecualikan dari Git sesuai `.gitignore`).
5. Contoh generasi teks dan post-processing.
6. Unit test, integration test, dokumentasi teknis, ADR, Git history, serta AI interaction logs.

## 12. Keterbatasan

- Korpus relatif kecil untuk melatih model bahasa generatif yang kuat.
- Tokenizer berbasis regex dan vocabulary tetap memiliki keterbatasan terhadap kata langka, variasi ejaan, dan nama entitas.
- Ukuran model kecil membatasi pengetahuan dan koherensi jangka panjang.
- Teks yang dihasilkan tidak melalui verifikasi fakta atau pemeriksaan berita.
- C14 dan C15 memiliki konfigurasi serta protokol evaluasi berbeda; perbandingan langsung perlu kehati-hatian.
- Lisensi dataset CC BY-NC 4.0 dan hak atas artikel sumber harus diperhatikan.

## 13. Kesimpulan

Ayayo MiniTransformer berhasil membangun alur lengkap model bahasa generatif kecil: pengolahan data, tokenisasi, implementasi Decoder-only Transformer, training autoregresif, evaluasi, checkpoint, dan text generation. Nilai utama proyek terletak pada implementasi dan pemahaman komponen Transformer dari dasar serta proses pengembangan yang didukung pengujian, dokumentasi, AI logging, dan riwayat kolaborasi Git.

Model ini merupakan prototipe akademik untuk demonstrasi next-token prediction, bukan sistem produksi atau sumber berita tepercaya.

## Referensi

- [README proyek](../README.md)
- [Product Requirements Document](../docs/PRD.md)
- [Technical Specification](../docs/TECH_SPEC.md)
- [Architecture Decision Records](../docs/ARCHITECTURE_DECISIONS.md)
- [Dataset Card](../docs/DATASET_CARD.md)
- [AI Rules](../docs/AI_RULES.md)
- [Commit history](https://github.com/AI-IF-TelU/-Proyek1-_AyayoTeam_MiniTransformer/commits/master)
- [Hugging Face — Indonesian News Datasets](https://huggingface.co/datasets/fahadh4ilyas/indonesian_news_datasets)
