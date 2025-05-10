# 🍗 D'FRESTO Tools

Aplikasi berbasis Streamlit untuk membantu tim D'FRESTO Fried Chicken dalam:
- Menampilkan lokasi mitra di peta
- Mengecek jarak antar mitra agar tidak terlalu berdekatan
- Memberikan rekomendasi lokasi baru berdasarkan persebaran eksisting

---

## 🚀 Fitur Utama

### 1. 📌 Lihat Lokasi Mitra
- Menampilkan semua lokasi mitra dalam bentuk peta interaktif
- Logo D'FRESTO digunakan sebagai penanda

### 2. 📏 Cek Jarak Antar Mitra
- Input koordinat calon mitra baru
- Menggunakan API OpenRouteService untuk menghitung jarak tempuh jalan
- Sistem memberikan status aman atau terlalu dekat (< 1.5 km)

### 3. 🌟 Rekomendasi Lokasi Baru
- Menghasilkan titik-titik potensial dalam radius 2 km dari pusat lokasi mitra
- Menyaring lokasi yang:
  - Tidak terlalu dekat dengan mitra lain
  - Berada di jalur umum antar mitra
- Menampilkan rekomendasi secara visual di peta

---

## 🛠️ Cara Menggunakan

## 📁 Upload Data Mitra

1. Klik tombol **"Upload file Excel (.xlsx)"**
2. File Excel harus memiliki kolom berikut:
   - `MITRA`
   - `LATITUDE`
   - `LONGITUDE`
3. Setelah file berhasil diunggah, fitur menu akan otomatis muncul.

---

## 🧭 Pilih Menu Fitur

### 📌 Lihat Lokasi Mitra
- Menampilkan lokasi semua mitra pada peta interaktif.
- Setiap mitra ditandai dengan ikon logo **D'FRESTO**.

---

### 📏 Cek Jarak Antar Mitra

1. Masukkan koordinat toko baru:
   - **Latitude**
   - **Longitude**
2. Masukkan **API Key OpenRouteService**  
   👉 Daftar gratis di: [https://openrouteservice.org/dev/#/signup](https://openrouteservice.org/dev/#/signup)
3. Klik tombol **"🚦 Cek Jarak Mitra"**
4. Sistem akan:
   - Menghitung **jarak jalan** ke 5 mitra terdekat
   - Menandai mitra dengan jarak **< 1.5 km** sebagai **"Terlalu Dekat"**
5. Klik **"📍 Lihat Peta Mitra"** untuk menampilkan peta interaktif.

---

### 🌟 Rekomendasi Lokasi Baru

1. Klik tombol **"🔄 Cari Rekomendasi Lokasi Baru"**
2. Sistem akan mencari dan menampilkan titik-titik baru yang:
   - **Aman** (berjarak > 1.5 km dari semua mitra)
   - **Masih dalam jalur sebaran mitra**
3. Hasil ditampilkan dalam bentuk peta interaktif dengan ikon bintang.
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

