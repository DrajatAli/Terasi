import streamlit as st
import pandas as pd
import folium
from folium import DivIcon
from streamlit_folium import st_folium
import plotly.express as px
import re
from urllib.parse import quote

# ==========================================
# 1. KONFIGURASI HALAMAN & TEMA DARK COMMAND CENTER
# ==========================================
st.set_page_config(
    page_title="TERASI - Monitoring Sampah Wonoayu",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .report-card {
        background-color: #1a1e24;
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 8px;
        border-left: 4px solid #e63946;
        font-size: 13px;
    }
    .badge-urgent { background-color: #e63946; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; }
    .badge-proses { background-color: #f39c12; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; }
    .badge-menunggu { background-color: #3498db; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; }
    .badge-selesai { background-color: #2ecc71; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. KONFIGURASI GOOGLE SHEETS
# ==========================================
# Ganti SPREADSHEET_ID dengan ID spreadsheet Anda
SPREADSHEET_ID = "16K7Y9h9n9gEY3RyRaRk6xx9THpAcGG0Ek9KVSHeDEkk"

# Nama sheet sesuai yang Anda tentukan
SHEET_LAPORAN_NAME = quote("Laporan Warga")
SHEET_TPS_NAME = quote("TPS")

URL_LAPORAN = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_LAPORAN_NAME}"
URL_TPS = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_TPS_NAME}"

# Helper konversi link Google Drive ke Direct Image
def convert_drive_url(url: str) -> str:
    if pd.isna(url) or not isinstance(url, str):
        return ""
    match = re.search(r'[-\w]{25,}', url)
    if match:
        return f"https://lh3.googleusercontent.com/d/{match.group(0)}"
    return url

@st.cache_data(ttl=60)
def load_all_data():
    try:
        # 1. Baca Sheet Laporan Warga
        df_laporan = pd.read_csv(URL_LAPORAN)
        df_laporan.columns = [str(c).strip().lower().replace(" ", "_") for c in df_laporan.columns]
        df_laporan['latitude'] = pd.to_numeric(df_laporan['latitude'], errors='coerce')
        df_laporan['longitude'] = pd.to_numeric(df_laporan['longitude'], errors='coerce')
        df_laporan = df_laporan.dropna(subset=['latitude', 'longitude'])
        
        # Konversi Link Foto Drive
        col_foto = next((c for c in df_laporan.columns if 'foto' in c), None)
        if col_foto:
            df_laporan['foto_direct'] = df_laporan[col_foto].apply(convert_drive_url)
        else:
            df_laporan['foto_direct'] = ""

        # 2. Baca Sheet TPS
        df_tps = pd.read_csv(URL_TPS)
        df_tps.columns = [str(c).strip().lower().replace(" ", "_") for c in df_tps.columns]
        df_tps['latitude'] = pd.to_numeric(df_tps['latitude'], errors='coerce')
        df_tps['longitude'] = pd.to_numeric(df_tps['longitude'], errors='coerce')
        df_tps = df_tps.dropna(subset=['latitude', 'longitude'])

        return df_laporan, df_tps
    except Exception as e:
        st.error(f"Gagal memuat data dari Google Sheets: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_laporan, df_tps = load_all_data()

if df_laporan.empty and df_tps.empty:
    st.warning("⚠️ Data belum berhasil dimuat. Pastikan pengaturan Google Sheets sudah diset 'Anyone with the link can view' dan nama tab sudah sesuai ('Laporan Warga' & 'TPS').")
    st.stop()

# ==========================================
# 3. SIDEBAR: BRAND, KPI, & RECENT CITIZEN REPORTS
# ==========================================
with st.sidebar:
    st.markdown("### ♻️ **TERASI WONOAYU**")
    st.caption("Monitoring Sampah Terpadu & Respons Warga")
    st.divider()

    menu = st.radio("Navigasi", ["Dashboard Peta", "Analitik & Evaluasi Rute", "Tabel Rekap Data"], label_visibility="collapsed")
    st.divider()

    # KPI Metrics Ringkas
    total_tps = len(df_tps)
    status_col = 'status_penanganan' if 'status_penanganan' in df_laporan.columns else 'status'
    
    if status_col in df_laporan.columns:
        laporan_aktif = len(df_laporan[~df_laporan[status_col].astype(str).str.lower().str.contains('selesai')])
    else:
        laporan_aktif = len(df_laporan)
        
    kpi1, kpi2 = st.columns(2)
    kpi1.metric("TPST / TPS Aktif", f"{total_tps}")
    kpi2.metric("Laporan Aktif", f"{laporan_aktif}", delta="Perlu Ditangani", delta_color="inverse")

    if st.button("🔄 Refresh Data Sheet"):
        st.cache_data.clear()
        st.rerun()

    st.divider()

    # Feed Laporan Masuk Warga
    st.markdown("#### 🚨 Laporan Warga Terkini")
    if not df_laporan.empty:
        df_feed = df_laporan.iloc[::-1].head(5)
        for _, row in df_feed.iterrows():
            id_lap = str(row.get('id_laporan', 'LAP'))[:8]  # Singkat UUID agar rapi
            status_val = str(row.get(status_col, 'Belum ditangani')).title()
            
            st_low = status_val.lower()
            badge_class = "badge-urgent" if ("belum" in st_low or "urgent" in st_low) else ("badge-proses" if "proses" in st_low else "badge-selesai")

            st.markdown(f"""
            <div class="report-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <b>#{id_lap}</b>
                    <span class="{badge_class}">{status_val}</span>
                </div>
                <div style="margin-top: 4px; color: #eee; font-weight: 500;">{row.get('alamat', '-')}</div>
                <div style="font-size: 11px; color: #bbb;">{row.get('deskripsi_lokasi', '-')}</div>
                <small style="color: #777;">Desa {row.get('desa', '-')} • {row.get('tanggal_laporan', '-')}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("Belum ada laporan masuk.")

# ==========================================
# 4. TAMPILAN UTAMA
# ==========================================
if menu == "Dashboard Peta":
    st.subheader("🗺️ Kendali Spasial Wilayah Kecamatan Wonoayu")
    
    # CSS Animasi Radar Berkedip Merah
    radar_css = """
    <style>
        .radar-pulse-container { position: relative; width: 50px; height: 50px; }
        .radar-core {
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            width: 14px; height: 14px; background: #ff2a2a; border: 2px solid #ffffff;
            border-radius: 50%; box-shadow: 0 0 12px #ff0000; z-index: 2;
        }
        .radar-ring {
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            width: 44px; height: 44px; border: 2px solid rgba(255, 42, 42, 0.85);
            border-radius: 50%; background: rgba(255, 0, 0, 0.2);
            animation: radarPulsing 1.6s ease-out infinite; z-index: 1;
        }
        @keyframes radarPulsing {
            0% { transform: translate(-50%, -50%) scale(0.3); opacity: 1; }
            100% { transform: translate(-50%, -50%) scale(1.6); opacity: 0; }
        }
        .tpst-pin {
            background-color: #00e676; border: 2px solid #ffffff; color: #003314;
            border-radius: 50%; text-align: center; font-size: 16px; font-weight: bold;
            width: 32px; height: 32px; line-height: 28px; box-shadow: 0 0 15px rgba(0, 230, 118, 0.7);
        }
    </style>
    """
    st.markdown(radar_css, unsafe_allow_html=True)

    # Inisialisasi Peta Folium
    center_lat = df_laporan['latitude'].median() if not df_laporan.empty else -7.4330
    center_lng = df_laporan['longitude'].median() if not df_laporan.empty else 112.6170

    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=14,
        tiles="OpenStreetMap"
    )

    # 4A. Plot Fasilitas TPS / TPST 3R (Pin Hijau)
    for _, tps in df_tps.iterrows():
        popup_tps = f"""
        <div style="font-family: Arial; width: 210px; color: #222;">
            <h4 style="margin: 0; color: #1b5e20;">♻️ {tps.get('nama', 'TPS / TPST')}</h4>
            <hr style="margin: 4px 0;">
            <p style="font-size: 12px; margin: 2px 0;"><b>Wilayah:</b> Desa {tps.get('desa', '-')}</p>
            <p style="font-size: 12px; margin: 2px 0;"><b>Kapasitas:</b> {tps.get('kapasitas', '-')}</p>
            <span style="background: #e8f5e9; color: #2e7d32; padding: 2px 6px; border-radius: 4px; font-size: 11px;">Fasilitas Resmi</span>
        </div>
        """
        icon_tps = DivIcon(icon_size=(32, 32), icon_anchor=(16, 16), html='<div class="tpst-pin">♻</div>')
        folium.Marker(
            location=[tps['latitude'], tps['longitude']],
            popup=folium.Popup(popup_tps, max_width=250),
            tooltip=f"Fasilitas TPS: {tps.get('nama', '')}",
            icon=icon_tps
        ).add_to(m)

    # 4B. Plot Titik Laporan Sampah Liar Warga (Radar Merah Berkedip)
    for _, lap in df_laporan.iterrows():
        st_val = str(lap.get(status_col, '')).lower()
        if "selesai" in st_val:
            continue  # Titik selesai tidak lagi memunculkan radar berkedip merah

        foto_html = f"""<img src="{lap['foto_direct']}" style="width: 100%; height: 110px; object-fit: cover; border-radius: 4px; margin-bottom: 4px;" onerror="this.style.display='none';">""" if lap.get('foto_direct') else ""
        
        popup_lap = f"""
        <div style="font-family: Arial; width: 230px; color: #222;">
            <h4 style="margin: 0; color: #c0392b;">⚠️ Laporan Warga</h4>
            <hr style="margin: 4px 0;">
            {foto_html}
            <p style="font-size: 11px; margin: 2px 0;"><b>Desa:</b> {lap.get('desa', '-')}</p>
            <p style="font-size: 11px; margin: 2px 0;"><b>Alamat:</b> {lap.get('alamat', '-')}</p>
            <p style="font-size: 11px; margin: 2px 0;"><b>Deskripsi:</b> {lap.get('deskripsi_lokasi', '-')}</p>
            <p style="font-size: 11px; margin: 2px 0;"><b>Waktu:</b> {lap.get('tanggal_laporan', '-')}</p>
            <div style="margin-top: 6px;">
                <span style="background: #ffebee; color: #c62828; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold;">{lap.get(status_col, 'Belum ditangani')}</span>
            </div>
        </div>
        """
        radar_icon = DivIcon(
            icon_size=(50, 50),
            icon_anchor=(25, 25),
            html='<div class="radar-pulse-container"><div class="radar-ring"></div><div class="radar-core"></div></div>'
        )
        folium.Marker(
            location=[lap['latitude'], lap['longitude']],
            popup=folium.Popup(popup_lap, max_width=260),
            tooltip=f"Laporan: {lap.get('desa', '')} - {lap.get('alamat', '')}",
            icon=radar_icon
        ).add_to(m)

    st_folium(m, width="100%", height=620, returned_objects=[])

elif menu == "Analitik & Evaluasi Rute":
    st.subheader("📊 Analitik Sebaran Laporan Sampah vs Ketersediaan TPS")

    desa_tps = df_tps['desa'].value_counts() if not df_tps.empty and 'desa' in df_tps.columns else pd.Series(dtype=int)
    desa_lap = df_laporan['desa'].value_counts() if not df_laporan.empty and 'desa' in df_laporan.columns else pd.Series(dtype=int)

    all_desas = sorted(list(set(desa_tps.index.tolist() + desa_lap.index.tolist())))
    
    df_evaluasi = pd.DataFrame({
        "Desa": all_desas,
        "Jumlah TPS / TPST": [desa_tps.get(d, 0) for d in all_desas],
        "Laporan Warga": [desa_lap.get(d, 0) for d in all_desas]
    })

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Perbandingan Ketersediaan TPS vs Laporan Masuk per Desa**")
        fig_bar = px.bar(
            df_evaluasi, 
            x="Desa", 
            y=["Jumlah TPS / TPST", "Laporan Warga"], 
            barmode="group",
            color_discrete_map={"Jumlah TPS / TPST": "#2ecc71", "Laporan Warga": "#e74c3c"},
            template="plotly_dark"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        st.markdown("**Status Penanganan Laporan**")
        if not df_laporan.empty and status_col in df_laporan.columns:
            fig_pie = px.pie(
                df_laporan, 
                names=status_col, 
                hole=0.4,
                template="plotly_dark"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Data status belum tersedia.")

elif menu == "Tabel Rekap Data":
    st.subheader("📋 Rekap Data Tabulasi")
    tab1, tab2 = st.tabs(["Laporan Warga", "Daftar TPS / TPST"])
    with tab1:
        # Tampilkan tabel tanpa kolom bantu foto_direct agar bersih
        st.dataframe(df_laporan.drop(columns=['foto_direct'], errors='ignore'), use_container_width=True)
    with tab2:
        st.dataframe(df_tps, use_container_width=True)
