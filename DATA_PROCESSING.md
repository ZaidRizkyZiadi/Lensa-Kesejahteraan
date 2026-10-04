# Dokumentasi Pengolahan Data

Seluruh pengolahan data dilakukan **secara manual di Microsoft Excel**, tanpa kode. Dokumen ini mencatat langkahnya supaya dapat diulang dan diperiksa. Sumber, judul tabel, URL, dan tanggal akses ada di `README.md` (bagian "Sumber data") dan di halaman SUMBER dasbor.

## Struktur folder data di repositori

| Folder | Isi |
|---|---|
| `data_mentah/` | File unduhan asli dari BPS, tidak diubah. Nama file mengikuti judul tabel BPS dan tahunnya. |
| `data_olahan/` | File antara hasil penggabungan per indikator (`IPM_Merged_2023_2025_Cleaned`, `TPT_Merged_2023_2025_Cleaned`, `RLS_Merged_2023_2025_Cleaned`, `Kemiskinan_Merged_2023_2025_Cleaned`). |
| folder utama | Empat file akhir yang dibaca langsung oleh `app.py`. |

File akhir yang dipakai aplikasi:

| File akhir | Isi | Dipakai untuk |
|---|---|---|
| `Pengeluaran_Hierarki_2025_Cleaned.xlsx` | 20 baris: Level 1, Level 2, Level 3, Nilai Rupiah (2025) | Treemap dan Sunburst |
| `Pengeluaran_Hierarki_2024_Cleaned.xlsx` | Struktur sama, nilai 2024 | Pembanding pertumbuhan 2024 ke 2025 |
| `Kemiskinan_KabKota_2025_Cleaned.xlsx` | Kolom `Wilayah` dan `Kemiskinan_2025` untuk kab/kota | Choropleth dan peta simbol proporsional |
| `Dataset_Multivariat_LENGKAP_8_Variabel.xlsx` | 38 provinsi x 24 kolom (8 variabel x 3 tahun) | PCA, SPLOM, koordinat paralel, heatmap |

Catatan: `Dataset_Multivariat_BPS_2023_2025.xlsx` adalah versi awal dengan variabel lebih sedikit dan **tidak dipakai lagi**.

## Prinsip umum

- Kunci penggabungan antartahun dan antarindikator: **nama provinsi**.
- Nama provinsi diseragamkan ke satu penulisan (misalnya `KEP. BANGKA BELITUNG` menjadi `Kepulauan Bangka Belitung`, `KEP. RIAU` menjadi `Kepulauan Riau`).
- Baris agregat nasional (`INDONESIA`) tidak dimasukkan.
- **Tidak ada imputasi, interpolasi, atau pembuangan baris.** Sel yang kosong di data akhir memang tidak tersedia di tabel BPS yang diunduh.
- Angka tidak dihitung ulang; nilai disalin dari tabel BPS apa adanya.

## 1. Dataset multivariat (8 variabel, 38 provinsi, 2023-2025)

Satu baris per provinsi, dengan kolom `Variabel_Tahun`. Sumber tiap variabel dan kolom yang diambil dari tabel mentah:

| Variabel | Tabel mentah BPS | Kolom yang diambil |
|---|---|---|
| `IPM_2023-2025` | Indeks Pembangunan Manusia Menurut Provinsi | Nilai IPM per provinsi |
| `Kemiskinan_Maret_2023-2025` | Jumlah dan Persentase Penduduk Miskin Menurut Provinsi | Persentase Penduduk Miskin, **Maret** |
| `TPT_Agustus_2023-2025` | Tingkat Pengangguran Terbuka Menurut Provinsi | Kolom **Agustus** |
| `RLS_2023-2025` | Rata-rata Lama Sekolah menurut Provinsi | Nilai per provinsi, tahun 2023-2025 |
| `HLS_2023-2025` | [Metode Baru] Harapan Lama Sekolah | Baris tingkat provinsi |
| `UHH_2023-2025` | [Metode Baru] Umur Harapan Hidup Saat Lahir (UHH) Hasil Long Form SP2020 | Baris tingkat provinsi |
| `Pengeluaran_2023-2025` | [Metode Baru] Pengeluaran per Kapita Disesuaikan | Baris tingkat provinsi |
| `Gini_2023-2025` | Gini Ratio Menurut Provinsi dan Daerah | Perkotaan+Perdesaan, **Semester 1 (Maret)** |

Langkah:
1. Unduh tabel tiap tahun (2023, 2024, 2025) dari BPS. Hasilnya ada di `data_mentah/`.
2. Pada tabel yang memuat kab/kota dan provinsi sekaligus (HLS, UHH, Pengeluaran), ambil hanya baris tingkat provinsi. Buang baris judul, catatan, dan baris `INDONESIA`.
3. Seragamkan nama provinsi (lihat prinsip umum), lalu gabungkan tahun 2023, 2024, dan 2025 menurut nama provinsi, per indikator.
4. Untuk IPM, TPT, RLS, dan Kemiskinan, hasil gabungan per indikator disimpan sebagai file antara di `data_olahan/` (`*_Merged_2023_2025_Cleaned.xlsx`). Untuk HLS, UHH, Pengeluaran, dan Gini tidak ada file antara; langsung digabung ke dataset akhir.
5. Gabungkan kedelapan indikator menurut nama provinsi menjadi `Dataset_Multivariat_LENGKAP_8_Variabel.xlsx`.

Data kosong:
- Empat provinsi baru di Papua (Papua Barat Daya, Papua Selatan, Papua Tengah, Papua Pegunungan) **tidak memiliki nilai 2023 untuk IPM, Kemiskinan, TPT, dan RLS** pada tabel BPS. Sel dibiarkan kosong.
- Aplikasi melewati sel kosong saat menggambar grafik, dan hanya mengeluarkan baris yang tidak lengkap dari perhitungan PCA dan klaster tahun yang bersangkutan.

## 2. Hierarki pengeluaran rumah tangga (2024 dan 2025)

Tabel mentah: *Rata-rata Pengeluaran per Kapita Sebulan Menurut Kelompok Komoditas dan Klasifikasi Desa (rupiah)*, tahun 2024 dan 2025.

Langkah:
1. Dari tiga kolom pada tabel mentah (Kota, Desa, Kota+Desa), diambil kolom **Kota+Desa**.
2. Label dwibahasa dipangkas ke bahasa Indonesia dan disingkat (misalnya `Ikan/udang/cumi/kerang/Fish/shrimp/...` menjadi `Ikan`).
3. Baris subtotal (`Jumlah makanan`, `Jumlah bukan makanan`, `Jumlah`) dibuang, karena nilainya dihitung aplikasi dari jumlah anak.
4. Data disusun menjadi tiga tingkat: Level 1 `Total Pengeluaran`, Level 2 `Makanan` atau `Bukan Makanan`, Level 3 komoditas (14 komoditas makanan dan 6 bukan makanan, total 20 baris).

Pertumbuhan 2024 ke 2025 dihitung oleh aplikasi dan bersifat nominal (belum dikoreksi inflasi).

## 3. Kemiskinan kab/kota (2025)

Tabel mentah: *Persentase Penduduk Miskin (P0) Menurut Kabupaten/Kota*, 2025.

Langkah:
1. Tabel mentah memuat baris provinsi yang diselingi baris kab/kota. Baris **provinsi dibuang**, hanya kab/kota yang dipertahankan.
2. Kolom disusun menjadi dua: `Wilayah` dan `Kemiskinan_2025`. Nama wilayah tidak diubah dari tabel BPS.

Penggabungan dengan batas wilayah (GeoJSON) tidak dilakukan di Excel. Aplikasi menormalkan nama (huruf kecil, tanpa awalan "kabupaten") dan memakai kamus alias `NAME_ALIASES` di `app.py` untuk nama yang berbeda penulisan. Jumlah wilayah yang cocok dan tidak cocok dicetak ke konsol saat aplikasi dijalankan (baris berawalan `[GeoJSON]`).

## 4. Pemeriksaan di aplikasi

Saat dijalankan, `app.py` mencetak peringatan bila jumlah baris data kemiskinan tidak 509 atau data multivariat tidak 38.

## Cara mengulang

1. Buka file di `data_mentah/` dan ikuti langkah per dataset di atas.
2. Bandingkan hasilnya dengan empat file akhir di folder utama. Nilainya harus sama.
3. Jalankan `python app.py` dan periksa pesan di konsol.
