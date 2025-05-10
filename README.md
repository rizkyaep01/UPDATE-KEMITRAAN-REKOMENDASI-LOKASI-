# D'FRESTO Tools Kemitraan

Aplikasi interaktif berbasis Streamlit untuk memudahkan analisis lokasi mitra dan perencanaan ekspansi franchise D'FRESTO Fried Chicken.

---

## 🖼️ Tampilan Awal Aplikasi

![Tampilan Awal](tampilan%20awal.jpeg)

---

## 📁 Upload Data Mitra

1. Klik tombol **"Upload file Excel (.xlsx)"**
2. File Excel harus memiliki kolom berikut:
   - `MITRA`
   - `LATITUDE`
   - `LONGITUDE`
3. Setelah file berhasil diunggah, menu fitur akan muncul secara otomatis.

---

## 🧭 Pilih Menu Fitur

### 📌 Lihat Lokasi Mitra

- Menampilkan lokasi semua mitra dalam peta interaktif.
- Setiap titik ditandai dengan ikon logo D'FRESTO.

![Lihat Lokasi Mitra](lihat%20lokasi%20mitra.jpeg)

---

### 📏 Cek Jarak Antar Mitra

1. Masukkan koordinat toko baru:
   - Latitude
   - Longitude
2. Masukkan API Key dari OpenRouteService.
   👉 [Daftar di sini](https://openrouteservice.org/dev/#/signup)
3. Klik **"🚦 Cek Jarak Mitra"**
   - Sistem menghitung jarak jalan ke 5 mitra terdekat.
   - Lokasi dengan jarak < 1.5 km akan diberi label **"Terlalu Dekat"**
4. Klik **"📍 Lihat Peta Mitra"** untuk melihat peta interaktif.

![Cek Jarak Antar Mitra](cek%20jarak%20antar%20mitra.jpeg)

---

### 🌟 Rekomendasi Lokasi Baru

- Klik tombol **"🔄 Cari Rekomendasi Lokasi Baru"**
- Sistem akan mencari titik-titik baru yang:
  - **Aman**: Berjarak > 1.5 km dari mitra mana pun
  - **Strategis**: Masih dalam jalur sebaran mitra
- Lokasi-lokasi hasil rekomendasi akan ditampilkan dalam bentuk peta.

![Rekomendasi Lokasi Baru](rekomendasi%20lokasi%20area%20kemitraan.jpeg)

---

## 📁 Format Data Excel (Contoh)

| MITRA       | LATITUDE   | LONGITUDE   |
|-------------|------------|-------------|
| Mitra A     | -6.201234  | 106.812345  |
| Mitra B     | -6.202345  | 106.813456  |

---

## 🔐 API Key OpenRouteService

Untuk fitur pengecekan jarak jalan, Anda perlu mendapatkan API Key dari:
👉 https://openrouteservice.org/dev/#/signup

