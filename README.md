# Bike Sharing Dashboard ✨

Proyek analisis data penyewaan sepeda harian (Capital Bikeshare, Washington D.C., 2011-2012) beserta dashboard interaktif yang dibuat dengan Streamlit dan Plotly.

- **Nama:** Durratul Muna
- **ID Dicoding:** DS322B6X0479

## Pertanyaan Bisnis
1. Seberapa besar penurunan rata-rata jumlah penyewaan sepeda harian pada cuaca berkabut dan hujan/salju ringan dibandingkan cuaca cerah selama 2011-2012?
2. Pada musim apa rata-rata jumlah penyewaan sepeda harian tertinggi dan terendah selama 2011-2012, dan berapa selisihnya?

## Isi Dashboard
- **Pertanyaan 1: Cuaca**: penurunan rata-rata penyewaan saat berkabut dan hujan/salju ringan dibanding cuaca cerah.
- **Pertanyaan 2: Musim**: musim dengan penyewaan tertinggi dan terendah beserta selisihnya.
- **Tren Bulanan**: perbandingan rata-rata penyewaan per bulan pada 2011 dan 2012.
- **Analisis Lanjutan**: clustering manual (binning) tingkat permintaan harian menjadi Rendah, Sedang, dan Tinggi.
- Filter di sidebar: rentang tanggal, musim, dan kondisi cuaca.

## Struktur Folder
```
submission
├───dashboard
| ├───main_data.csv
| └───dashboard.py
├───data
| └───day.csv
├───notebook.ipynb
├───README.md
├───requirements.txt
└───url.txt
```

## Setup Environment - Shell/Terminal
Jalankan dari folder `submission`:
```
python -m pip install -r requirements.txt
```

## Setup Environment - Anaconda (opsional)
```
conda create --name main-ds python=3.10
conda activate main-ds
pip install -r requirements.txt
```

## Run steamlit app
Jalankan dari folder `submission`:
```
python -m streamlit run dashboard/dashboard.py
```
Dashboard akan terbuka di `http://localhost:8501`.

> Catatan: `dashboard.py` membaca `dashboard/main_data.csv`. Jika berkas tersebut belum ada,
> dashboard akan membuatnya otomatis dari `data/day.csv`.

## Dashboard Online
Tautan dashboard yang sudah di-deploy tersedia di berkas `url.txt`.
