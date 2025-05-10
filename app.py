import streamlit as st
import pandas as pd
import openrouteservice
from openrouteservice.exceptions import ApiError, HTTPError
import folium
from streamlit_folium import st_folium
from time import sleep
import random
from geopy.distance import geodesic
import numpy as np

st.set_page_config(page_title="D'FRESTO Tools", layout="centered")
st.title("🍗 D'FRESTO FRIED CHICKEN")

st.subheader("📁 Upload File Data Lokasi Mitra")
uploaded_file = st.file_uploader("Upload file Excel (.xlsx)", type="xlsx")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.upper().str.strip().str.replace("\xa0", "", regex=True)

        if not all(col in df.columns for col in ["MITRA", "LATITUDE", "LONGITUDE"]):
            st.error("❌ Kolom wajib (MITRA, LATITUDE, LONGITUDE) tidak ditemukan.")
            st.stop()

        df["LATITUDE"] = df["LATITUDE"].astype(str).str.replace(",", ".").astype(float)
        df["LONGITUDE"] = df["LONGITUDE"].astype(str).str.replace(",", ".").astype(float)
        st.success("✅ File berhasil dibaca!")

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
                        jarak = hitung_jarak_jalan(row['Longitude'], row['Latitude'], lon_baru, lat_baru)
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
                                'Status': status
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

                    folium.Marker(
                        location=[lat_baru, lon_baru],
                        popup="Toko Baru",
                        tooltip="Toko Baru",
                        icon=folium.Icon(color="green", icon="plus-sign"),
                    ).add_to(m)

                    for row in st.session_state.hasil_cek:
                        if row['Status'] == "terlalu dekat":
                            popup = f"{row['MITRA']} ({row['Jarak']:.2f} km)"
                            icon = folium.CustomIcon(icon_url, icon_size=(35, 35))
                            folium.Marker(
                                location=[row['Latitude'], row['Longitude']],
                                popup=popup,
                                tooltip=row['MITRA'],
                                icon=icon
                            ).add_to(m)

                    st_folium(m, width=700, height=500)

        # ===== MENU 3: REKOMENDASI LOKASI BARU BERDASARKAN GAP ANTAR MITRA =====
        elif menu == "🌟 Rekomendasi Lokasi Baru":
            st.info("📍 Sistem mencari area kosong (gap) yang belum terjangkau mitra dalam radius 1.5 km.")

            grid_step = 0.005  # ~500m per langkah
            radius_gap_km = 1.5

            lat_min, lat_max = df["LATITUDE"].min() - 0.02, df["LATITUDE"].max() + 0.02
            lon_min, lon_max = df["LONGITUDE"].min() - 0.02, df["LONGITUDE"].max() + 0.02
            lat_grid = list(np.arange(lat_min, lat_max, grid_step))
            lon_grid = list(np.arange(lon_min, lon_max, grid_step))

            gap_points = []
            progress = st.progress(0)
            total = len(lat_grid) * len(lon_grid)
            count = 0

            for lat in lat_grid:
                for lon in lon_grid:
                    is_far = all(geodesic((lat, lon), (row["LATITUDE"], row["LONGITUDE"])) .km >= radius_gap_km for _, row in df.iterrows())
                    if is_far:
                        gap_points.append((lat, lon))
                    count += 1
                    if count % 50 == 0:
                        progress.progress(count / total)

            progress.empty()

            if gap_points:
                st.success(f"✅ Ditemukan {len(gap_points)} titik kosong yang direkomendasikan!")
                m = folium.Map(location=[df["LATITUDE"].mean(), df["LONGITUDE"].mean()], zoom_start=13)

                for _, row in df.iterrows():
                    icon = folium.CustomIcon(icon_url, icon_size=(30, 30))
                    folium.Marker(
                        location=[row["LATITUDE"], row["LONGITUDE"]],
                        popup=row["MITRA"],
                        icon=icon,
                        tooltip=row["MITRA"]
                    ).add_to(m)

                for i, (lat, lon) in enumerate(gap_points[:20]):
                    folium.Marker(
                        location=[lat, lon],
                        popup=f"Rekomendasi #{i+1}",
                        tooltip=f"Rekomendasi #{i+1}",
                        icon=folium.Icon(color="purple", icon="star")
                    ).add_to(m)

                st.subheader("📍 Rekomendasi Lokasi Baru")
                st_folium(m, width=700, height=500)
            else:
                st.warning("⚠️ Tidak ditemukan area kosong yang cukup jauh untuk direkomendasikan.")
    except Exception as e:
        st.error(f"❌ Terjadi error saat membaca file: {e}")
else:
    st.info("📄 Silakan upload file Excel terlebih dahulu untuk memulai.")
