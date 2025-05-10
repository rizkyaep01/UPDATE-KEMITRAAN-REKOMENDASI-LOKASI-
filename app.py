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

st.set_page_config(page_title="D'FRESTO Tools", layout="centered")
st.title("\U0001F357 D'FRESTO FRIED CHICKEN")

st.subheader("\U0001F4C1 Upload File Data Lokasi Mitra")
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

        # Deteksi outlier lokasi
        coords = df[["LATITUDE", "LONGITUDE"]]
        lof = LocalOutlierFactor(n_neighbors=5, contamination=0.1)
        outlier_flags = lof.fit_predict(coords)
        df['OUTLIER'] = outlier_flags
        df = df[df['OUTLIER'] == 1].reset_index(drop=True)

        st.success(f"✅ File berhasil dibaca! Total mitra valid (tanpa outlier): {len(df)}")

        menu = st.radio("Pilih Menu:", [
            "\U0001F4CC Lihat Lokasi Mitra",
            "\U0001F4CF Cek Jarak Antar Mitra",
            "✨ Rekomendasi Lokasi Baru"
        ])

        icon_url = "logo dfresto.png"

        if menu == "\U0001F4CC Lihat Lokasi Mitra":
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
            st.subheader("\U0001F5FA️ Peta Lokasi Mitra")
            st_folium(m, width=700, height=500)

        elif menu == "\U0001F4CF Cek Jarak Antar Mitra":
            lat_baru = st.number_input("\U0001F9ED Latitude mitra baru", value=-6.181080, format="%.6f")
            lon_baru = st.number_input("\U0001F9ED Longitude mitra baru", value=106.668730, format="%.6f")
            api_key = st.text_input("\U0001F511 Masukkan API Key OpenRouteService kamu", type="password")

            if api_key:
                client = openrouteservice.Client(key=api_key)

                def hitung_jarak(lon1, lat1, lon2, lat2):
                    try:
                        coords = ((lon1, lat1), (lon2, lat2))
                        route = client.directions(coords)
                        return route['routes'][0]['summary']['distance'] / 1000
                    except:
                        return None

                if st.button("\U0001F6A6 Cek Jarak Mitra"):
                    df_jarak = df.copy()
                    df_jarak['Jarak'] = df_jarak.apply(
                        lambda row: hitung_jarak(row['LONGITUDE'], row['LATITUDE'], lon_baru, lat_baru), axis=1)
                    df_jarak = df_jarak.dropna(subset=['Jarak'])
                    df_jarak = df_jarak.sort_values('Jarak')

                    aman = True
                    for _, row in df_jarak.head(5).iterrows():
                        if row['Jarak'] < 1.5:
                            st.warning(f"⚠️ Terlalu dekat dengan {row['MITRA']} ({row['Jarak']:.2f} km)")
                            aman = False

                    if aman:
                        st.success("✅ Lokasi mitra baru AMAN — tidak ada mitra dalam radius 1.5 km.")

                    m = folium.Map(location=[lat_baru, lon_baru], zoom_start=14)
                    folium.Marker([lat_baru, lon_baru], tooltip="Toko Baru", icon=folium.Icon(color="green")).add_to(m)
                    for _, row in df_jarak.head(5).iterrows():
                        icon = folium.CustomIcon(icon_url, icon_size=(35, 35))
                        folium.Marker([row['LATITUDE'], row['LONGITUDE']], popup=row['MITRA'], icon=icon).add_to(m)
                    st.subheader("\U0001F5FA️ Peta Lokasi")
                    st_folium(m, width=700, height=500)

        elif menu == "✨ Rekomendasi Lokasi Baru":
            lat_center = df["LATITUDE"].mean()
            lon_center = df["LONGITUDE"].mean()

            def titik_acak_dalam_radius(lat, lon, radius_km, n=100):
                hasil = []
                for _ in range(n * 3):
                    dx = random.uniform(-radius_km, radius_km) / 111
                    dy = random.uniform(-radius_km, radius_km) / 111
                    new_lat = lat + dx
                    new_lon = lon + dy
                    if geodesic((lat, lon), (new_lat, new_lon)).km <= radius_km:
                        hasil.append((new_lat, new_lon))
                    if len(hasil) >= n:
                        break
                return hasil

            def titik_aman(lat, lon):
                for _, row in df.iterrows():
                    if geodesic((lat, lon), (row["LATITUDE"], row["LONGITUDE"])).km < 1.5:
                        return False
                return True

            if st.button("\U0001F504 Cari Lokasi Aman"):
                kandidat = titik_acak_dalam_radius(lat_center, lon_center, radius_km=2, n=100)
                rekomendasi = [(lat, lon) for lat, lon in kandidat if titik_aman(lat, lon)][:10]

                if rekomendasi:
                    st.success(f"✅ {len(rekomendasi)} lokasi aman ditemukan")
                    m = folium.Map(location=[lat_center, lon_center], zoom_start=13)
                    for _, row in df.iterrows():
                        icon = folium.CustomIcon(icon_url, icon_size=(30, 30))
                        folium.Marker([row["LATITUDE"], row["LONGITUDE"]], icon=icon, tooltip=row["MITRA"]).add_to(m)
                    for i, (lat, lon) in enumerate(rekomendasi):
                        folium.Marker([lat, lon], tooltip=f"Rekomendasi #{i+1}", icon=folium.Icon(color="purple")).add_to(m)
                    st.subheader("\U0001F4CD Rekomendasi Lokasi Baru")
                    st_folium(m, width=700, height=500)
                else:
                    st.warning("⚠️ Lokasi terlalu padat, tidak ada lokasi aman ditemukan.")

    except Exception as e:
        st.error(f"❌ Terjadi kesalahan: {e}")
else:
    st.info("\U0001F4C4 Silakan upload file Excel terlebih dahulu untuk memulai.")
