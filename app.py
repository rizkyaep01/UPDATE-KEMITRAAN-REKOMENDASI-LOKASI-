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
import time

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

        # Kolom wajib
        required_cols = ["MITRA", "LATITUDE", "LONGITUDE", "REGIONAL"]
        if not all(col in df.columns for col in required_cols):
            st.error(f"❌ Kolom wajib {required_cols} tidak ditemukan.")
            st.stop()

        # Format koordinat
        df["REGIONAL"] = df["REGIONAL"].astype(str).str.lower().str.strip()
        df["LATITUDE"] = df["LATITUDE"].astype(str).str.replace(",", ".").astype(float)
        df["LONGITUDE"] = df["LONGITUDE"].astype(str).str.replace(",", ".").astype(float)

        st.success("✅ File berhasil dibaca!")

        # Pilih regional
        daftar_regional = sorted(df["REGIONAL"].dropna().unique())
        regional_pilih = st.selectbox("🌍 Pilih Regional:", ["-- Pilih Regional --"] + daftar_regional)

        if regional_pilih == "-- Pilih Regional --":
            st.info("⚠️ Silakan pilih regional terlebih dahulu.")
            st.stop()

        # Filter data
        df_regional = df[df["REGIONAL"] == regional_pilih].reset_index(drop=True)
        st.write(f"Jumlah mitra di regional **{regional_pilih}**: {len(df_regional)}")

        # ===== MENU =====
        menu = st.radio("Pilih Menu:", [
            "📌 Lihat Lokasi Mitra",
            "📏 Cek Jarak Antar Mitra",
            "🌟 Rekomendasi Lokasi Baru"
        ])

        icon_url = "logo dfresto.png"

        # ===== MENU 1: Lihat Lokasi Mitra =====
        if menu == "📌 Lihat Lokasi Mitra":
            with st.spinner("Loading lokasi mitra..."):
                time.sleep(0.7)
                mean_lat = df_regional["LATITUDE"].mean()
                mean_lon = df_regional["LONGITUDE"].mean()
                m = folium.Map(location=[mean_lat, mean_lon], zoom_start=14)

                for _, row in df_regional.iterrows():
                    icon = folium.CustomIcon(icon_url, icon_size=(35, 35))
                    folium.Marker(
                        location=[row["LATITUDE"], row["LONGITUDE"]],
                        popup=row["MITRA"],
                        tooltip=row["MITRA"],
                        icon=icon
                    ).add_to(m)

                st.subheader("🗺️ Peta Lokasi Mitra")
                st_folium(m, width=700, height=500)

        # ===== MENU 2: Cek Jarak Antar Mitra =====
        elif menu == "📏 Cek Jarak Antar Mitra":
            with st.spinner("Loading cek jarak..."):
                time.sleep(0.7)
                lat_baru = st.number_input("🧭 Latitude mitra baru", value=-6.181080, format="%.6f")
                lon_baru = st.number_input("🧭 Longitude mitra baru", value=106.668730, format="%.6f")
                api_key = st.text_input("🔑 Masukkan API Key OpenRouteService kamu", type="password")

                if "cek_ditekan" not in st.session_state:
                    st.session_state.cek_ditekan = False
                if "lihat_peta" not in st.session_state:
                    st.session_state.lihat_peta = False

                df_jarak = df_regional.copy()
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

        # ===== MENU 3: Rekomendasi Lokasi Baru =====
        elif menu == "🌟 Rekomendasi Lokasi Baru":
            with st.spinner("Loading rekomendasi lokasi..."):
                time.sleep(0.7)
                st.write("Rekomendasi lokasi baru berdasarkan deteksi outlier (LOF) dan centroid cluster.")

                coords = df_regional[["LATITUDE", "LONGITUDE"]].values

                if len(coords) < 5:
                    st.warning("Data mitra regional kurang dari 5, rekomendasi lokasi kurang optimal.")
                else:
                    lof = LocalOutlierFactor(n_neighbors=5)
                    y_pred = lof.fit_predict(coords)
                    outlier_mask = y_pred == -1

                    st.write(f"Jumlah outlier (lokasi aneh): {sum(outlier_mask)}")

                    non_outlier_coords = coords[~outlier_mask]
                    centroid = non_outlier_coords.mean(axis=0)
                    st.write(f"Centroid lokasi mitra (non-outlier): {centroid}")

                    m = folium.Map(location=centroid, zoom_start=14)

                    icon = folium.CustomIcon(icon_url, icon_size=(35, 35))
                    for i, (lat, lon) in enumerate(coords):
                        color = "red" if outlier_mask[i] else "blue"
                        folium.CircleMarker(
                            location=[lat, lon],
                            radius=6,
                            color=color,
                            fill=True,
                            fill_color=color,
                            fill_opacity=0.7,
                            popup=f"Mitra ke-{i + 1}"
                        ).add_to(m)

                    folium.Marker(
                        location=centroid,
                        popup="Rekomendasi Lokasi Baru",
                        tooltip="Rekomendasi Lokasi Baru",
                        icon=folium.Icon(color="green", icon="star")
                    ).add_to(m)

                    st_folium(m, width=700, height=500)

    except Exception as e:
        st.error(f"❌ Terjadi kesalahan: {e}")
else:
    st.info("📂 Silakan upload file Excel untuk memulai.")
