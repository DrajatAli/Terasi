import streamlit as st
import pandas as pd
import folium
from folium import DivIcon
from streamlit_folium import st_folium
import plotly.express as px
import re
from urllib.parse import quote
import os

# ==========================================
# 1. KONFIGURASI HALAMAN & TEMA DARK COMMAND CENTER
# ==========================================
st.set_page_config(
    page_title="TERASI - Kecamatan Wonoayu",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS: Styling Navigasi Button Keren, Report Cards, & Badges
st.markdown("""
<style>
    /* Styling Navigasi Tombol di Sidebar */
    div[data-testid="stSidebar"] div.stButton > button {
        width: 100%;
        text-align: left;
        display: flex;
        justify-content: flex-start;
        align-items: center;
        padding: 10px 14px;
        margin-bottom: 6px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 14px;
        border: 1px solid #2d3748;
        background-color: #1a202c;
        color: #e2e8f0;
        transition: all 0.2s ease-in-out;
    }
    div[data-testid="stSidebar"] div.stButton > button:hover {
        background-color: #2d3748;
        border-color: #4a5568;
        color: #ffffff;
    }
    /* Feed Kartu Laporan Warga */
    .report-card {
        background-color: #171923;
        border: 1px solid #2d3748;
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 10px;
        border-left: 4px solid #e53e3e;
        font-size: 13px;
    }
    .badge-urgent { background-color: #e53e3e; color: white; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: bold; }
    .badge-proses { background-color: #dd6b20; color: white; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: bold; }
    .badge-selesai { background-color: #38a169; color: white; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# State untuk tab navigasi aktif
if "active_nav" not in st.session_state:
    st.session_state["active_nav"] = "🗺️ Dashboard Peta"

# ==========================================
# 2. KONFIGURASI GOOGLE SHEETS
# ==========================================
SPREADSHEET_ID = "16K7Y9h9n9gEY3RyRaRk6xx9THpAcGG0Ek9KVSHeDEkk"

SHEET_LAPORAN_NAME = quote("Laporan Warga")
SHEET_TPS_NAME = quote("TPS")

URL_LAPORAN = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_LAPORAN_NAME}"
URL_TPS = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_TPS_NAME}"

def convert_drive_url(url: str) -> str:
    """Mengubah format sharing Google Drive menjadi Direct Image View"""
    if pd.isna(url) or not isinstance(url, str):
        return ""
    match = re.search(r'[-\w]{25,}', url)
    if match:
        return f"https://lh3.googleusercontent.com/d/{match.group(0)}"
    return url

def parse_coordinate(series):
    """Membersihkan format koma desimal Indonesia menjadi titik desimal float"""
    return pd.to_numeric(series.astype(str).str.replace(',', '.').str.strip(), errors='coerce')

@st.cache_data(ttl=60)
def load_all_data():
    df_laporan = pd.DataFrame()
    df_tps = pd.DataFrame()

    # 1. Baca Laporan Warga
    try:
        df_laporan = pd.read_csv(URL_LAPORAN)
        df_laporan.columns = [str(c).strip().lower().replace(" ", "_") for c in df_laporan.columns]
        
        # Cari dan bersihkan kolom koordinat
        for lat_col in ['latitude', 'lat']:
            if lat_col in df_laporan.columns:
                df_laporan['latitude'] = parse_coordinate(df_laporan[lat_col])
                break
        for lng_col in ['longitude', 'long', 'lng']:
            if lng_col in df_laporan.columns:
                df_laporan['longitude'] = parse_coordinate(df_laporan[lng_col])
                break

        df_laporan = df_laporan.dropna(subset=['latitude', 'longitude'])
        df_laporan = df_laporan[(df_laporan['latitude'] != 0) & (df_laporan['longitude'] != 0)]
        
        col_foto = next((c for c in df_laporan.columns if 'foto' in c), None)
        df_laporan['foto_direct'] = df_laporan[col_foto].apply(convert_drive_url) if col_foto else ""
    except Exception as e:
        st.warning(f"Info: Tab 'Laporan Warga' belum dimuat: {e}")

    # 2. Baca TPS / TPST
    try:
        df_tps = pd.read_csv(URL_TPS)
        df_tps.columns = [str(c).strip().lower().replace(" ", "_") for c in df_tps.columns]
        
        for lat_col in ['latitude', 'lat']:
            if lat_col in df_tps.columns:
                df_tps['latitude'] = parse_coordinate(df_tps[lat_col])
                break
        for lng_col in ['longitude', 'long', 'lng']:
            if lng_col in df_tps.columns:
                df_tps['longitude'] = parse_coordinate(df_tps[lng_col])
                break

        df_tps = df_tps.dropna(subset=['latitude', 'longitude'])
        df_tps = df_tps[(df_tps['latitude'] != 0) & (df_tps['longitude'] != 0)]
    except Exception as e:
        st.warning(f"Info: Tab 'TPS' belum dimuat: {e}")

    return df_laporan, df_tps

df_laporan, df_tps = load_all_data()

# ==========================================
# 3. SIDEBAR: BRANDING TERASI, NAVIGASI, & FEED
# ==========================================
with st.sidebar:
    # Tampilkan Logo Branding TERASI
    if os.path.exists("logo_terasi.png"):
        st.image("logo_terasi.png", use_container_width=True)
    elif os.path.exists("logo_terasi.jpeg"):
        st.image("logo_terasi.jpeg", use_container_width=True)
    else:
        st.markdown("### ♻️ **TERASI**")
        st.caption("Titik Evaluasi Rute & Area Sampah Terintegrasi\nKecamatan Wonoayu • Sidoarjo")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    st.caption("PILIH MENU")

    # Navigasi Bergaya Card Button
    def set_nav(menu_name):
        st.session_state["active_nav"] = menu_name

    col_btn1 = st.button("🗺️  Dashboard Peta Kendali", on_click=set_nav, args=("🗺️ Dashboard Peta",), use_container_width=True)
    col_btn2 = st.button("📊  Analitik & Evaluasi Rute", on_click=set_nav, args=("📊 Analitik & Evaluasi Rute",), use_container_width=True)
    col_btn3 = st.button("📋  Tabel Rekapitulasi Data", on_click=set_nav, args=("📋 Tabel Rekapitulasi Data",), use_container_width=True)

    st.divider()

    # KPI Metrics Ringkas
    total_tps = len(df_tps)
    status_col = 'status_penanganan' if 'status_penanganan' in df_laporan.columns else ('status' if 'status' in df_laporan.columns else None)
    
    if status_col:
        laporan_aktif = len(df_laporan[~df_laporan[status_col].astype(str).str.lower().str.contains('selesai')])
    else:
        laporan_aktif = len(df_laporan)
        
    kpi1, kpi2 = st.columns(2)
    kpi1.metric("TPST Aktif", f"{total_tps}")
    kpi2.metric("Laporan Liar", f"{laporan_aktif}", delta="Perlu Ditangani", delta_color="inverse")

    if st.button("🔄 Segarkan Data Sheet", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()

    # Feed Laporan Masuk Warga
    st.markdown("#### 🚨 Laporan Warga Terkini")
    if not df_laporan.empty:
        df_feed = df_laporan.iloc[::-1].head(5)
        for _, row in df_feed.iterrows():
            id_lap = str(row.get('id_laporan', row.get('id', 'LAP')))[:8]
            status_val = str(row.get(status_col, 'Belum ditangani')).title() if status_col else "Baru"
            
            st_low = status_val.lower()
            badge_class = "badge-urgent" if ("belum" in st_low or "urgent" in st_low) else ("badge-proses" if "proses" in st_low else "badge-selesai")

            st.markdown(f"""
            <div class="report-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <b>#{id_lap}</b>
                    <span class="{badge_class}">{status_val}</span>
                </div>
                <div style="margin-top: 4px; color: #f7fafc; font-weight: 500;">{row.get('alamat', '-')}</div>
                <div style="font-size: 11px; color: #a0aec0;">{row.get('deskripsi_lokasi', '-')}</div>
                <small style="color: #718096;">Desa {row.get('desa', '-')} • {row.get('tanggal_laporan', '-')}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("Belum ada laporan masuk.")

# ==========================================
# 4. KONTEN UTAMA SESUAI NAVIGASI AKTIF
# ==========================================
menu_aktif = st.session_state["active_nav"]

if menu_aktif == "🗺️ Dashboard Peta":
    st.subheader("🗺️ Kendali Spasial Titik Sampah & Fasilitas TPS")
    
    # CSS Animasi Efek Radar Berkedip Merah
    radar_css = """
    <style>
        .radar-pulse-container { position: relative; width: 44px; height: 44px; }
        .radar-core {
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            width: 14px; height: 14px; background: #e53e3e; border: 2px solid #ffffff;
            border-radius: 50%; box-shadow: 0 0 10px #e53e3e; z-index: 2;
        }
        .radar-ring {
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            width: 40px; height: 40px; border: 2px solid rgba(229, 62, 62, 0.85);
            border-radius: 50%; background: rgba(229, 62, 62, 0.25);
            animation: radarPulsing 1.5s ease-out infinite; z-index: 1;
        }
        @keyframes radarPulsing {
            0% { transform: translate(-50%, -50%) scale(0.3); opacity: 1; }
            100% { transform: translate(-50%, -50%) scale(1.6); opacity: 0; }
        }
        .tps-pin {
            background-color: #38a169; border: 2px solid #ffffff; color: #ffffff;
            border-radius: 50%; text-align: center; font-size: 15px; font-weight: bold;
            width: 32px; height: 32px; line-height: 28px; box-shadow: 0 0 10px rgba(56, 161, 105, 0.7);
        }
    </style>
    """
    st.markdown(radar_css, unsafe_allow_html=True)

    # Menentukan titik tengah peta secara dinamis
    if not df_laporan.empty:
        center_lat = df_laporan['latitude'].iloc[0]
        center_lng = df_laporan['longitude'].iloc[0]
        zoom_level = 14
    elif not df_tps.empty:
        center_lat = df_tps['latitude'].iloc[0]
        center_lng = df_tps['longitude'].iloc[0]
        zoom_level = 14
    else:
        center_lat, center_lng = -7.4330, 112.6170  # Default Kecamatan Wonoayu
        zoom_level = 13

    # Inisialisasi Peta
    m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom_level, tiles="OpenStreetMap")

    # 4A. Plot Fasilitas TPS (Pin Hijau)
    for _, tps in df_tps.iterrows():
        popup_tps = f"""
        <div style="font-family: Arial, sans-serif; width: 200px; color: #222;">
            <h4 style="margin: 0; color: #22543d;">♻️ {tps.get('nama', 'TPS / TPST')}</h4>
            <hr style="margin: 4px 0;">
            <p style="font-size: 12px; margin: 2px 0;"><b>Desa:</b> {tps.get('desa', '-')}</p>
            <p style="font-size: 12px; margin: 2px 0;"><b>Kapasitas:</b> {tps.get('kapasitas', '-')}</p>
            <span style="background: #c6f6d5; color: #22543d; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold;">Fasilitas Resmi</span>
        </div>
        """
        icon_tps = DivIcon(icon_size=(32, 32), icon_anchor=(16, 16), html='<div class="tps-pin">♻</div>')
        folium.Marker(
            location=[tps['latitude'], tps['longitude']],
            popup=folium.Popup(popup_tps, max_width=250),
            tooltip=f"Fasilitas: {tps.get('nama', 'TPS')}",
            icon=icon_tps
        ).add_to(m)

    # 4B. Plot Laporan Sampah Liar (Radar Merah Berkedip)
    for _, lap in df_laporan.iterrows():
        st_val = str(lap.get(status_col, 'Belum ditangani')) if status_col else "Belum ditangani"
        if "selesai" in st_val.lower():
            continue  # Titik yang sudah beres tidak perlu memunculkan radar

        foto_html = f"""<img src="{lap['foto_direct']}" style="width: 100%; height: 110px; object-fit: cover; border-radius: 4px; margin-bottom: 4px;" onerror="this.style.display='none';">""" if lap.get('foto_direct') else ""
        
        popup_lap = f"""
        <div style="font-family: Arial, sans-serif; width: 230px; color: #222;">
            <h4 style="margin: 0; color: #9b2c2c;">⚠️ Titik Sampah Liar</h4>
            <hr style="margin: 4px 0;">
            {foto_html}
            <p style="font-size: 11px; margin: 2px 0;"><b>Pelapor:</b> {lap.get('nama_pelapor', '-')}</p>
            <p style="font-size: 11px; margin: 2px 0;"><b>Desa:</b> {lap.get('desa', '-')}</p>
            <p style="font-size: 11px; margin: 2px 0;"><b>Alamat:</b> {lap.get('alamat', '-')}</p>
            <p style="font-size: 11px; margin: 2px 0;"><b>Keterangan:</b> {lap.get('deskripsi_lokasi', '-')}</p>
            <span style="background: #fed7d7; color: #9b2c2c; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold;">Status: {st_val}</span>
        </div>
        """
        radar_icon = DivIcon(
            icon_size=(44, 44),
            icon_anchor=(22, 22),
            html='<div class="radar-pulse-container"><div class="radar-ring"></div><div class="radar-core"></div></div>'
        )
        folium.Marker(
            location=[lap['latitude'], lap['longitude']],
            popup=folium.Popup(popup_lap, max_width=250),
            tooltip=f"Laporan: {lap.get('desa', '')} - {lap.get('alamat', '')}",
            icon=radar_icon
        ).add_to(m)

    st_folium(m, width="100%", height=620, returned_objects=[])

elif menu_aktif == "📊 Analitik & Evaluasi Rute":
    st.subheader("📊 Analitik Sebaran Laporan vs Ketersediaan Fasilitas TPS")

    desa_tps = df_tps['desa'].value_counts() if not df_tps.empty and 'desa' in df_tps.columns else pd.Series(dtype=int)
    desa_lap = df_laporan['desa'].value_counts() if not df_laporan.empty and 'desa' in df_laporan.columns else pd.Series(dtype=int)

    all_desas = sorted(list(set(desa_tps.index.tolist() + desa_lap.index.tolist())))
    
    df_evaluasi = pd.DataFrame({
        "Desa": all_desas,
        "Jumlah TPS / TPST": [desa_tps.get(d, 0) for d in all_desas],
        "Laporan Sampah Liar": [desa_lap.get(d, 0) for d in all_desas]
    })

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Perbandingan Fasilitas TPS vs Laporan Masuk per Desa**")
        fig_bar = px.bar(
            df_evaluasi, 
            x="Desa", 
            y=["Jumlah TPS / TPST", "Laporan Sampah Liar"], 
            barmode="group",
            color_discrete_map={"Jumlah TPS / TPST": "#38a169", "Laporan Sampah Liar": "#e53e3e"},
            template="plotly_dark"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        st.markdown("**Status Penanganan Titik Laporan**")
        if not df_laporan.empty and status_col in df_laporan.columns:
            fig_pie = px.pie(
                df_laporan, 
                names=status_col, 
                hole=0.4,
                template="plotly_dark"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Data status penanganan belum tersedia.")

elif menu_aktif == "📋 Tabel Rekapitulasi Data":
    st.subheader("📋 Rekapitulasi Tabulasi Laporan & Fasilitas")
    tab1, tab2 = st.tabs(["Laporan Warga (Sampah Liar)", "Daftar Fasilitas TPS / TPST 3R"])
    with tab1:
        st.dataframe(df_laporan.drop(columns=['foto_direct'], errors='ignore'), use_container_width=True)
    with tab2:
        st.dataframe(df_tps, use_container_width=True)
