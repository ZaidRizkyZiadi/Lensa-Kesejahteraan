# Deploy ke Vercel
1. Pindahkan folder `assets/` ke `public/assets/` (font 6,7 MB melebihi batas respons fungsi 4,5 MB; folder public dilayani CDN).
2. Hapus `.venv` dan `assets/media` (mp4 tidak dipakai) dari repo.
3. Ganti isi requirements.txt dengan versi terkunci (lihat bawah).
4. Di app.py: tambahkan `assets_folder` pada Dash(...) dan ubah `app.run(debug=True)` jadi `debug=False`.
5. Push ke GitHub (publik) -> vercel.com/new -> Import -> Framework: Other -> Deploy.
6. Uji URL preview di HP dan laptop sebelum dikumpulkan.

requirements.txt:
dash==4.4.1
plotly==7.1.0
pandas==3.0.5
numpy==2.5.3
scipy==1.18.1
scikit-learn==1.9.1
openpyxl==3.1.5
