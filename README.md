# Lensa Kesenjangan: Pola Kesenjangan, Pengeluaran, dan Pendidikan di Indonesia
Dasbor Plotly Dash (UAS Visualisasi Data dan Informasi 2026). Sumber data: BPS.

## Topik visualisasi
- **Hierarki**: Treemap dan Sunburst (3 level), ukuran = pengeluaran 2025 (Rp), warna = pertumbuhan nominal 2024-2025 (%), penunjuk posisi. Catatan: pertumbuhan bersifat nominal (belum dikoreksi inflasi).
- **Geospasial**: Choropleth (% kemiskinan, 509 kab/kota) dan peta simbol proporsional; tooltip, zoom/pan, legenda.
- **Multivariat** (8 variabel, 38 provinsi, 2023-2025): PCA (biplot + klaster k-means + pencilan), SPLOM, koordinat paralel, heatmap terklaster; brushing & linking antar tampilan.

## Data
Empat file akhir yang dibaca aplikasi ada di folder utama:
`Pengeluaran_Hierarki_2025_Cleaned.xlsx`, `Pengeluaran_Hierarki_2024_Cleaned.xlsx`, `Kemiskinan_KabKota_2025_Cleaned.xlsx`, `Dataset_Multivariat_LENGKAP_8_Variabel.xlsx`

Folder pendukung:
- `data_mentah/`: file unduhan asli dari BPS, tidak diubah.
- `data_olahan/`: file antara hasil penggabungan per indikator (IPM, TPT, RLS, Kemiskinan).

Pengolahan dilakukan manual di Excel (tanpa kode) dan tidak ada baris yang dibuang atau diisi ulang. Nilai yang kosong memang tidak tersedia di tabel BPS (empat provinsi Papua baru, tahun 2023) dan dilewati saat render. **Rincian langkah pengolahan: lihat [`DATA_PROCESSING.md`](DATA_PROCESSING.md).**

Batas wilayah: `indonesia_kabkota.geojson` (non-BPS) dengan properti nama `WADMKK`.

## Menjalankan secara lokal
```
pip install -r requirements.txt
python app.py   # http://127.0.0.1:8050
```
Aset tampilan (CSS, JS, font, SFX) berada di `public/assets/`.

## Deployment (Vercel)
- `api/index.py` mengambil `server` (Flask milik Dash) dari `app.py`, dan `vercel.json` mengarahkan semua rute ke sana.
- Aset ada di `public/assets/` agar dilayani CDN Vercel (font berukuran 6,7 MB melebihi batas respons fungsi 4,5 MB).
- Versi paket dikunci di `requirements.txt`; versi Python di `.python-version`.
- File video (`*.mp4`) tidak dipakai aplikasi dan dikecualikan dari repo serta bundle fungsi.
- Langkah lengkap ada di `DEPLOY.md`: push ke GitHub, impor di vercel.com/new, Framework: Other, lalu Deploy.
- Catatan: akses pertama bisa lambat sekitar 2-3 detik karena cold start.

## Sumber data
Semua data BPS diakses pada **4 Oktober 2026**. Isi yang sama tampil di halaman SUMBER dasbor (konstanta `SOURCES` di `app.py`); salin tabel ini ke bagian sumber/daftar pustaka makalah.

| Dataset | Judul tabel/publikasi | Tahun data | URL | Tanggal akses |
|---|---|---|---|---|
| Pengeluaran per kapita (2024 dan 2025) | Rata-rata Pengeluaran per Kapita Sebulan Menurut Kelompok Komoditas (Rupiah) | 2024, 2025 | https://www.bps.go.id/id/statistics-table/3/VTJaSFFtWklXVnBYZVdSREwyczJlbm93UWpVM1FUMDkjMw==/rata-rata-pengeluaran-per-kapita-sebulan-menurut-kelompok-komoditas-dan-klasifikasi-desa--rupiah---2023.html?year=2025 | 4 Oktober 2026 |
| Kemiskinan kab/kota | Persentase Penduduk Miskin (P0) Menurut Kabupaten/Kota | 2025 | https://www.bps.go.id/id/statistics-table/2/NjIxIzI=/persentase-penduduk-miskin-menurut-kabupaten-kota.html | 4 Oktober 2026 |
| Multivariat 1: TPT | Tingkat Pengangguran Terbuka Menurut Provinsi | 2023-2025 | https://www.bps.go.id/id/statistics-table/2/NTQzIzI=/tingkat-pengangguran-terbuka-menurut-provinsi.html | 4 Oktober 2026 |
| Multivariat 2: IPM | Indeks Pembangunan Manusia Menurut Provinsi | 2023-2025 | https://www.bps.go.id/id/statistics-table/3/V25GaFNHaExaMnhITm1sWmRrUlJZelJzYUc1SGR6MDkjMw==/indeks-pembangunan-manusia-menurut-provinsi--2022.html?year=2025 | 4 Oktober 2026 |
| Multivariat 3: Penduduk miskin provinsi | Jumlah dan Persentase Penduduk Miskin Menurut Provinsi | 2023-2025 | https://www.bps.go.id/id/statistics-table/3/UkVkWGJVZFNWakl6VWxKVFQwWjVWeTlSZDNabVFUMDkjMw==/jumlah-dan-persentase-penduduk-miskin-menurut-provinsi--2023.html?year=2025 | 4 Oktober 2026 |
| Multivariat 4: RLS | (Metode Baru) Rata-rata Lama Sekolah | 2023-2025 | https://www.bps.go.id/id/statistics-table/2/NDE1IzI=/-metode-baru--rata-rata-lama-sekolah.html | 4 Oktober 2026 |
| Multivariat 5: HLS | (Metode Baru) Harapan Lama Sekolah (Tahun) | 2023-2025 | https://www.bps.go.id/id/statistics-table/2/NDE3IzI=/-metode-baru--harapan-lama-sekolah--tahun-.html | 4 Oktober 2026 |
| Multivariat 6: UHH | (Metode Baru) Umur Harapan Hidup Saat Lahir (UHH) Hasil Long Form SP2020 | 2023-2025 | https://www.bps.go.id/id/statistics-table/2/MjIwNiMy/-metode-baru--umur-harapan-hidup-saat-lahir--uhh--hasil-long-form-sp2020.html | 4 Oktober 2026 |
| Multivariat 7: Pengeluaran | (Metode Baru) Pengeluaran per Kapita Disesuaikan | 2023-2025 | https://www.bps.go.id/id/statistics-table/2/NDE2IzI=/-metode-baru--pengeluaran-per-kapita-disesuaikan.html | 4 Oktober 2026 |
| Multivariat 8: Gini | Gini Ratio Menurut Provinsi dan Daerah | 2023-2025 | https://www.bps.go.id/id/statistics-table/2/OTgjMg==/gini-ratio-menurut-provinsi-dan-daerah.html | 4 Oktober 2026 |
| Batas wilayah (non-BPS) | GeoJson-Indonesia-38-Provinsi, folder Kabupaten (ardian28, GitHub) | - | https://github.com/ardian28/GeoJson-Indonesia-38-Provinsi/tree/main/Kabupaten | 4 Oktober 2026 |

## Keterbatasan
- **Peta**: 7 wilayah di data kemiskinan tidak memiliki poligon di GeoJSON, dan 5 poligon di GeoJSON tidak memiliki data. Wilayah-wilayah ini tidak tampil di peta atau tidak berwarna. Daftar lengkapnya dicetak ke konsol saat aplikasi dijalankan (baris `[GeoJSON]`).
- **Pertumbuhan pengeluaran** bersifat nominal, belum dikoreksi inflasi.
- **Data multivariat 2023**: empat provinsi Papua baru tidak memiliki data 2023, sehingga dikeluarkan dari PCA dan klaster tahun tersebut.
- **Pengolahan manual**: data diolah di Excel tanpa skrip; reproduksi dilakukan dengan mengikuti `DATA_PROCESSING.md`.

## Penggunaan alat bantu AI
Dalam pengerjaan proyek ini penulis memanfaatkan Claude (Anthropic) untuk membantu menulis dan memperbaiki kode (HTML, JavaScript, dan Python), memeriksa prosedur validasi data, menyusun draf serta memeriksa naskah, dan mencari serta memahami rujukan. Penulis sendiri yang menentukan topik, alur cerita, pertanyaan penelitian, data yang dianalisis, serta rancangan analisis dan visualisasi. Setiap keluaran AI ditinjau, diuji, dan diverifikasi oleh penulis, mencakup hasil pengolahan data, angka yang dikutip, dan kesesuaian rujukan dengan sumber aslinya.

## TODO sebelum dikumpulkan
- [ ] Tautan proyek publik dan repositori publik: isi di sini dan di akhir makalah setelah Kesimpulan.
- [x] Deklarasi penggunaan alat bantu AI (soal poin 7): teks ada di bagian "Penggunaan alat bantu AI" di atas; salin ke bagian Metodologi makalah.
- [x] Dokumentasi pengolahan data: `DATA_PROCESSING.md`.
- [ ] Unggah `data_mentah/` dan `data_olahan/` ke repositori.
