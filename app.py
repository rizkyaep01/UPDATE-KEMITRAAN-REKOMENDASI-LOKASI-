import streamlit as st
import pandas as pd
import openrouteservice
from openrouteservice.exceptions import ApiError, HTTPError
import folium
from streamlit_folium import st_folium
from time import sleep
import random
from geopy.distance import geodesic
from sklearn.neighbors import LocalOutlierFactor
import numpy as np
import base64

# ===== Logo Base64 Encoding =====
with open("logo dfresto.png", "rb") as image_file:
    logo_base64 = base64.b64encode(image_file.read()).decode()

# ===== Page Config =====
st.set_page_config(page_title="D'FRESTO Tools", layout="centered")

# ===== Custom Header with Logo and Red Title =====
st.markdown(
    f"""
    <h1 style="text-align:center; color:red;"> 
        <img src="data:image/png;base64,{logo_base64}" width="50" height="50" /> 
        D'FRESTO FRIED CHICKEN
    </h1>
    """,
    unsafe_allow_html=True
)

st.subheader("📁 Upload File Data Lokasi Mitra")
uploaded_file = st.file_uploader("Upload file Excel (.xlsx)", type="xlsx")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.upper().str.strip().str.replace("\xa0", "", regex=True)

        # Pastikan kolom penting ada
        required_cols = ["MITRA", "LATITUDE", "LONGITUDE", "REGIONAL"]
        if not all(col in df.columns for col in required_cols):
            st.error(f"❌ Kolom wajib {required_cols} tidak ditemukan.")
            st.stop()

        # Format koordinat
        df["LATITUDE"] = df["LATITUDE"].astype(str).str.replace(",", ".").astype(float)
        df["LONGITUDE"] = df["LONGITUDE"].astype(str).str.replace(",", ".").astype(float)
        st.success("✅ File berhasil dibaca!")

        # Pilihan regional
        daftar_regional = sorted(df["REGIONAL"].dropna().unique())
        regional_pilih = st.selectbox("🌍 Pilih Regional yang ingin dipakai:", ["-- Pilih Regional --"] + daftar_regional)

        if regional_pilih == "-- Pilih Regional --":
            st.info("⚠️ Silakan pilih regional terlebih dahulu untuk memproses data.")
            st.stop()

        # Filter data sesuai regional
        df_regional = df[df["REGIONAL"] == regional_pilih].reset_index(drop=True)
        df = df_regional
        st.write(f"Jumlah mitra di regional **{regional_pilih}**: {len(df)}")
        menu = st.radio("Pilih Menu:", [
            "📌 Lihat Lokasi Mitra",
            "📏 Cek Jarak Antar Mitra",
            "🌟 Rekomendasi Lokasi Baru"
        ])

        icon_url = "logo dfresto.png"

        # ===== MENU 1: LIHAT LOKASI MITRA =====
        if menu == "📌 Lihat Lokasi Mitra":
            mean_lat = df["LATITUDE"].mean()
            mean_lon = df["LONGITUDE"].mean()
            m = folium.Map(location=[mean_lat, mean_lon], zoom_start=14)

            for _, row in df.iterrows():
                icon = folium.CustomIcon(icon_url, icon_size=(35, 35))
                folium.Marker(
                    location=[row["LATITUDE"], row["LONGITUDE"]],
                    popup=row["MITRA"],
                    tooltip=row["MITRA"],
                    icon=icon
                ).add_to(m)

            st.subheader("🗺️ Peta Lokasi Mitra")
            st_folium(m, width=700, height=500)

        # ===== MENU 2: CEK JARAK ANTAR MITRA =====
        elif menu == "📏 Cek Jarak Antar Mitra":
            lat_baru = st.number_input("🧭 Latitude mitra baru", value=-6.181080, format="%.6f")
            lon_baru = st.number_input("🧭 Longitude mitra baru", value=106.668730, format="%.6f")
            api_key = st.text_input("🔑 Masukkan API Key OpenRouteService kamu", type="password")

            if "cek_ditekan" not in st.session_state:
                st.session_state.cek_ditekan = False
            if "lihat_peta" not in st.session_state:
                st.session_state.lihat_peta = False

            df_jarak = df.copy()
            df_jarak.columns = df_jarak.columns.str.strip()
            df_jarak['Latitude'] = df_jarak['LATITUDE']
            df_jarak['Longitude'] = df_jarak['LONGITUDE']

            if api_key:
                try:
                    client = openrouteservice.Client(key=api_key)
                except:
                    st.error("❌ API Key tidak valid atau koneksi gagal.")
                    st.stop()

                def hitung_jarak_jalan(lon1, lat1, lon2, lat2, max_retry=3):
                    for attempt in range(max_retry):
                        try:
                            coords = ((lon1, lat1), (lon2, lat2))
                            route = client.directions(coords)
                            jarak_m = route['routes'][0]['summary']['distance']
                            return jarak_m / 1000
                        except (ApiError, HTTPError):
                            sleep(0.5 + random.random())
                        except Exception:
                            return None
                    return None

                if st.button("🚦 Cek Jarak Mitra"):
                    st.session_state.cek_ditekan = True
                    st.session_state.lihat_peta = False
                    jarak_minimal = 1.5
                    aman = True

                    df_jarak['JARAK_AWAL'] = ((df_jarak['Latitude'] - lat_baru) ** 2 + (df_jarak['Longitude'] - lon_baru) ** 2) ** 0.5
                    df_terdekat = df_jarak.nsmallest(5, 'JARAK_AWAL').copy()

                    hasil_cek = []
                    progress = st.progress(0)
                    for i, (_, row) in enumerate(df_terdekat.iterrows()):
                        try:
                            coords = ((row['Longitude'], row['Latitude']), (lon_baru, lat_baru))
                            route = client.directions(coords, format='geojson')
                            jarak = route['features'][0]['properties']['summary']['distance'] / 1000  # km
                            geometry = route['features'][0]['geometry']['coordinates']  # polyline
                        except Exception as e:
                            jarak = None
                            geometry = None
                        progress.progress((i + 1) / len(df_terdekat))

                        if jarak is not None:
                            status = "aman"
                            if jarak < jarak_minimal:
                                status = "terlalu dekat"
                                aman = False
                            hasil_cek.append({
                                'MITRA': row['MITRA'],
                                'Latitude': row['Latitude'],
                                'Longitude': row['Longitude'],
                                'Jarak': jarak,
                                'Status': status,
                                'Geometry': geometry
                            })
                        else:
                            st.error(f"❌ Gagal menghitung jarak ke mitra {row['MITRA']}")

                    progress.empty()
                    st.session_state.hasil_cek = hasil_cek

                if st.session_state.cek_ditekan and "hasil_cek" in st.session_state:
                    hasil = st.session_state.hasil_cek
                    aman = all(h['Status'] == "aman" for h in hasil)
                    st.subheader("🔍 Hasil Pengecekan:")

                    for h in hasil:
                        if h['Status'] == "terlalu dekat":
                            st.warning(f"⚠️ TERLALU DEKAT: {h['MITRA']} | Jarak Jalan = {h['Jarak']:.2f} km")

                    if aman:
                        st.success("✅ Toko baru AMAN — tidak ada toko lain dalam radius 1.5 km (jalan).")

                    if st.button("📍 Lihat Peta Mitra"):
                        st.session_state.lihat_peta = True

                if st.session_state.lihat_peta and "hasil_cek" in st.session_state:
                    st.subheader("🗺️ Peta Mitra Terlalu Dekat Dengan Mitra Baru")
                    m = folium.Map(location=[lat_baru, lon_baru], zoom_start=14)

                    # Marker toko baru
                    folium.Marker(
                        location=[lat_baru, lon_baru],
                        popup="Toko Baru",
                        tooltip="Toko Baru",
                        icon = folium.CustomIcon(icon_url, icon_size=(35, 35)),
                    ).add_to(m)

                    for row in st.session_state.hasil_cek:
                        if row['Status'] == "terlalu dekat":
                            popup = f"{row['MITRA']} ({row['Jarak']:.2f} km)"
                            # Pastikan icon_url sudah didefinisikan sebelumnya, kalau belum pakai icon default
                            icon = folium.Icon(color="red", icon="info-sign")

                            folium.Marker(
                                location=[row['Latitude'], row['Longitude']],
                                popup=popup,
                                tooltip=row['MITRA'],
                                icon=icon
                            ).add_to(m)

                            geometry = row.get('Geometry')
                            if geometry and isinstance(geometry, list):
                                try:
                                    # Pastikan geometry berupa list koordinat [lon, lat]
                                    coords = [[coord[1], coord[0]] for coord in geometry]
                                    folium.PolyLine(
                                        coords,
                                        color='red',
                                        weight=4,
                                        opacity=0.8,
                                        tooltip=f"Jalur ke {row['MITRA']}"
                                    ).add_to(m)
                                except Exception as e:
                                    st.warning(f"⚠️ Gagal gambar rute untuk {row['MITRA']}: {e}")
                            else:
                                st.info(f"ℹ️ Tidak ada data jalur rute untuk {row['MITRA']}")

                    st_folium(m, width=700, height=500)

        # ===== MENU 3: REKOMENDASI LOKASI BARU =====
        elif menu == "🌟 Rekomendasi Lokasi Baru":
            st.info("🧠 Sistem akan mencari titik acak dalam radius 2 km dari pusat semua mitra dan menyaring yang aman (jarak > 1.5 km), serta tidak terlalu jauh dari jalur antar mitra.")

            if 'rekomendasi_lokasi' not in st.session_state:
                st.session_state.rekomendasi_lokasi = None
            if 'cek_ditekan' not in st.session_state:
                st.session_state.cek_ditekan = False

            coords = df[['LATITUDE', 'LONGITUDE']].to_numpy()
            lof = LocalOutlierFactor(n_neighbors=8, contamination=0.05)
            outliers = lof.fit_predict(coords)
            df_filtered = df[outliers == 1]  # 1 = inlier, -1 = outlier

            lat_center = df_filtered["LATITUDE"].mean()
            lon_center = df_filtered["LONGITUDE"].mean()

            if st.button("🔄 Cari Rekomendasi Lokasi Baru"):
                st.session_state.rekomendasi_lokasi = []
                st.session_state.cek_ditekan = True

                def titik_acak_dalam_radius(lat, lon, radius_km, n=200):
                    hasil = []
                    for _ in range(n * 2):
                        dx = random.uniform(-radius_km, radius_km) / 111
                        dy = random.uniform(-radius_km, radius_km) / 111
                        new_lat = lat + dx
                        new_lon = lon + dy
                        if geodesic((lat, lon), (new_lat, new_lon)).km <= radius_km:
                            hasil.append((new_lat, new_lon))
                        if len(hasil) >= n:
                            break
                    return hasil

                def titik_aman(lat, lon, df, batas_km=1.5):
                    for _, row in df.iterrows():
                        if geodesic((lat, lon), (row["LATITUDE"], row["LONGITUDE"])).km < batas_km:
                            return False
                    return True

                def di_jalur(lat, lon, df, ambang_km=0.3):
                    for i in range(len(df) - 1):
                        lat1, lon1 = df.iloc[i]["LATITUDE"], df.iloc[i]["LONGITUDE"]
                        lat2, lon2 = df.iloc[i+1]["LATITUDE"], df.iloc[i+1]["LONGITUDE"]
                        d1 = geodesic((lat1, lon1), (lat, lon)).km
                        d2 = geodesic((lat2, lon2), (lat, lon)).km
                        d12 = geodesic((lat1, lon1), (lat2, lon2)).km
                        if abs((d1 + d2) - d12) <= ambang_km:
                            return True
                    return False

                titik_acak = titik_acak_dalam_radius(lat_center, lon_center, radius_km=2, n=300)
                titik_rekomendasi = []

                for lat, lon in titik_acak:
                    if titik_aman(lat, lon, df_filtered) and di_jalur(lat, lon, df_filtered):
                        titik_rekomendasi.append((lat, lon))
                    if len(titik_rekomendasi) >= 10:
                        break

                st.session_state.rekomendasi_lokasi = titik_rekomendasi

            if st.session_state.rekomendasi_lokasi is not None:
                if len(st.session_state.rekomendasi_lokasi) > 0:
                    st.success(f"✅ Ditemukan {len(st.session_state.rekomendasi_lokasi)} lokasi aman untuk direkomendasikan!")

                    m = folium.Map(location=[lat_center, lon_center], zoom_start=13)

                    for _, row in df_filtered.iterrows():
                        icon = folium.CustomIcon(icon_url, icon_size=(30, 30))
                        folium.Marker(
                            location=[row["LATITUDE"], row["LONGITUDE"]],
                            popup=row["MITRA"],
                            icon=icon,
                            tooltip=row["MITRA"]
                        ).add_to(m)

                    for i, (lat, lon) in enumerate(st.session_state.rekomendasi_lokasi):
                        folium.Marker(
                            location=[lat, lon],
                            popup=f"Rekomendasi #{i+1}",
                            tooltip=f"Rekomendasi #{i+1}",
                            icon=folium.Icon(color="purple", icon="star")
                        ).add_to(m)

                    st.subheader("📍 Rekomendasi Lokasi Baru")
                    st_folium(m, width=700, height=500)

                else:
                    st.warning("⚠️ Lokasi sudah padat, tidak ada rekomendasi yang aman ditemukan.")

    except Exception as e:
        st.error(f"❌ Terjadi kesalahan: {e}")
else:
    st.info("📄 Silakan upload file Excel terlebih dahulu untuk memulai.")
