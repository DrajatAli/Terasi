import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import re
from urllib.parse import quote
import requests
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

# Custom CSS
st.markdown("""
<style>
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
    .report-card {
        background-color: #171923;
        border: 1px solid #2d3748;
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 10px;
        border-left: 4px solid #e53e3e;
        font-size: 13px;
    }
    .badge-belum { background-color: #e53e3e; color: white; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: bold; }
    .badge-sedang { background-color: #dd6b20; color: white; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: bold; }
    .badge-sudah { background-color: #38a169; color: white; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

if "active_nav" not in st.session_state:
    st.session_state["active_nav"] = "🗺️ Dashboard Peta"

# ==========================================
# 2. KONFIGURASI GOOGLE SHEETS
# ==========================================
SPREADSHEET_ID = "16K7Y9h9n9gEY3RyRaRk6xx9THpAcGG0Ek9KVSHeDEkk"

# Opsional: Jika tim Anda punya Google Apps Script Web App URL untuk update baris Google Sheet
GAS_WEBAPP_URL = "GANTI_DENGAN_URL_EXEC_GOOGLE_APPS_SCRIPT_JIKA_ADA"

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
    """Membersihkan format koma desimal Indonesia menjadi float standar"""
    return pd.to_numeric(series.astype(str).str.replace(',', '.').str.strip(), errors='coerce')

@st.cache_data(ttl=30)
def load_all_data():
    df_laporan = pd.DataFrame()
    df_tps = pd.DataFrame()

    # 1. Baca Laporan Warga
    try:
        df_laporan = pd.read_csv(URL_LAPORAN)
        df_laporan.columns = [str(c).strip().lower().replace(" ", "_") for c in df_laporan.columns]
        
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
        st.warning(f"Info: Tab 'Laporan Warga' belum terbaca: {e}")

    # 2. Baca TPS
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
        st.warning(f"Info: Tab 'TPS' belum terbaca: {e}")

    return df_laporan, df_tps

df_laporan, df_tps = load_all_data()

# Kolom kunci status
col_verif = next((c for c in df_laporan.columns if 'verifikasi' in c), 'status_verifikasi')
col_penanganan = next((c for c in df_laporan.columns if 'penanganan' in c), 'status_penanganan')
col_id = next((c for c in df_laporan.columns if 'id' in c), 'id_laporan')

# ==========================================
# 3. SIDEBAR: BRANDING & NAVIGASI
# ==========================================
with st.sidebar:
    if os.path.exists("logo_terasi.png"):
        st.image("logo_terasi.png", use_container_width=True)
    elif os.path.exists("logo_terasi.jpeg"):
        st.image("logo_terasi.jpeg", use_container_width=True)
    else:
        st.markdown("### ♻️ **TERASI**")
        st.caption("Titik Evaluasi Rute & Area Sampah Terintegrasi\nKecamatan Wonoayu • Sidoarjo")

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    st.caption("PILIH MENU")

    def set_nav(menu_name):
        st.session_state["active_nav"] = menu_name

    st.button("🗺️  Dashboard Peta Kendali", on_click=set_nav, args=("🗺️ Dashboard Peta",), use_container_width=True)
    st.button("🛠️  Panel Verifikasi & Status", on_click=set_nav, args=("🛠️ Panel Verifikasi & Status",), use_container_width=True)
    st.button("📊  Analitik & Evaluasi Rute", on_click=set_nav, args=("📊 Analitik & Evaluasi Rute",), use_container_width=True)
    st.button("📋  Tabel Rekapitulasi Data", on_click=set_nav, args=("📋 Tabel Rekapitulasi Data",), use_container_width=True)

    st.divider()

    # KPI Metrics Ringkas
    total_tps = len(df_tps)
    if col_penanganan in df_laporan.columns:
        laporan_belum = len(df_laporan[df_laporan[col_penanganan].astype(str).str.lower().str.contains('belum')])
        laporan_sedang = len(df_laporan[df_laporan[col_penanganan].astype(str).str.lower().str.contains('sedang')])
    else:
        laporan_belum, laporan_sedang = len(df_laporan), 0
        
    kpi1, kpi2 = st.columns(2)
    kpi1.metric("TPST Aktif", f"{total_tps}")
    kpi2.metric("Belum Ditangani", f"{laporan_belum}", delta=f"{laporan_sedang} Sedang Proses", delta_color="inverse")

    if st.button("🔄 Segarkan Data Sheet", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()

    # Feed Laporan Masuk Warga
    st.markdown("#### 🚨 Laporan Warga Terkini")
    if not df_laporan.empty:
        df_feed = df_laporan.iloc[::-1].head(5)
        for _, row in df_feed.iterrows():
            id_lap = str(row.get(col_id, 'LAP'))[:8]
            st_penanganan_val = str(row.get(col_penanganan, 'Belum ditangani')).title()
            
            st_low = st_penanganan_val.lower()
            badge_class = "badge-belum" if "belum" in st_low else ("badge-sedang" if "sedang" in st_low else "badge-sudah")

            st.markdown(f"""
            <div class="report-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <b>#{id_lap}</b>
                    <span class="{badge_class}">{st_penanganan_val}</span>
                </div>
                <div style="margin-top: 4px; color: #f7fafc; font-weight: 500;">{row.get('alamat', '-')}</div>
                <div style="font-size: 11px; color: #a0aec0;">{row.get('deskripsi_lokasi', '-')}</div>
                <small style="color: #718096;">Desa {row.get('desa', '-')} • {row.get('tanggal_laporan', '-')}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("Belum ada laporan masuk.")

# ==========================================
# 4. KONTEN UTAMA
# ==========================================
menu_aktif = st.session_state["active_nav"]

# --- TAB 1: PETA KENDALI SPASIAL ---
if menu_aktif == "🗺️ Dashboard Peta":
    st.subheader("🗺️ Kendali Spasial Titik Sampah Liar & Fasilitas TPST")
    
    # Menentukan Center Peta
    if not df_laporan.empty:
        center_lat = float(df_laporan['latitude'].iloc[0])
        center_lng = float(df_laporan['longitude'].iloc[0])
        zoom_level = 14
    elif not df_tps.empty:
        center_lat = float(df_tps['latitude'].iloc[0])
        center_lng = float(df_tps['longitude'].iloc[0])
        zoom_level = 14
    else:
        center_lat, center_lng = -7.4330, 112.6170
        zoom_level = 13

    st.caption(f"📍 Posisi Terpantau: {len(df_laporan)} Titik Laporan Warga | {len(df_tps)} Titik Fasilitas TPST 3R")

    m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom_level, tiles="OpenStreetMap")

    # 1. Plot TPS / TPST 3R (Pin Hijau)
    for _, tps in df_tps.iterrows():
        popup_tps = f"""
        <div style="font-family: Arial; width: 200px; color: #222;">
            <h4 style="margin: 0; color: #2e7d32;">♻️ {tps.get('nama', 'TPS / TPST')}</h4>
            <hr style="margin: 4px 0;">
            <p style="font-size: 12px; margin: 2px 0;"><b>Desa:</b> {tps.get('desa', '-')}</p>
            <p style="font-size: 12px; margin: 2px 0;"><b>Kapasitas:</b> {tps.get('kapasitas', '-')}</p>
            <span style="background: #e8f5e9; color: #2e7d32; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold;">Fasilitas Resmi</span>
        </div>
        """
        folium.Marker(
            location=[float(tps['latitude']), float(tps['longitude'])],
            popup=folium.Popup(popup_tps, max_width=250),
            tooltip=f"Fasilitas Resmi: {tps.get('nama', 'TPS')}",
            icon=folium.Icon(color="green", icon="recycle", prefix="fa")
        ).add_to(m)

    # 2. Plot Laporan Sampah Liar
    for _, lap in df_laporan.iterrows():
        lat_val = float(lap['latitude'])
        lng_val = float(lap['longitude'])
        
        st_pen = str(lap.get(col_penanganan, 'Belum ditangani')).title()
        st_ver = str(lap.get(col_verif, 'Belum diverifikasi')).title()
        
        foto_html = f"""<img src="{lap['foto_direct']}" style="width: 100%; height: 110px; object-fit: cover; border-radius: 4px; margin-bottom: 4px;" onerror="this.style.display='none';">""" if lap.get('foto_direct') else ""
        
        popup_lap = f"""
        <div style="font-family: Arial; width: 230px; color: #222;">
            <h4 style="margin: 0; color: #c62828;">⚠️ Laporan Sampah Liar</h4>
            <hr style="margin: 4px 0;">
            {foto_html}
            <p style="font-size: 11px; margin: 2px 0;"><b>Pelapor:</b> {lap.get('nama_pelapor', '-')}</p>
            <p style="font-size: 11px; margin: 2px 0;"><b>Desa:</b> {lap.get('desa', '-')}</p>
            <p style="font-size: 11px; margin: 2px 0;"><b>Alamat:</b> {lap.get('alamat', '-')}</p>
            <p style="font-size: 11px; margin: 2px 0;"><b>Keterangan:</b> {lap.get('deskripsi_lokasi', '-')}</p>
            <div style="margin-top: 4px;">
                <span style="background: #e2e8f0; color: #2d3748; padding: 2px 5px; border-radius: 4px; font-size: 10px;">Verifikasi: {st_ver}</span>
                <span style="background: #fed7d7; color: #9b2c2c; padding: 2px 5px; border-radius: 4px; font-size: 10px; font-weight: bold;">Penanganan: {st_pen}</span>
            </div>
        </div>
        """
        
        # Penyesuaian Visual Berdasarkan Status
        if "sudah" in st_pen.lower():
            # Titik yang sudah ditangani: Marker Biru/Hijau kalem (tidak ada efek radar)
            folium.CircleMarker(
                location=[lat_val, lng_val],
                radius=6,
                color="#ffffff",
                weight=1,
                fill=True,
                fill_color="#2b6cb0",
                fill_opacity=0.9,
                popup=folium.Popup(popup_lap, max_width=250),
                tooltip=f"Selesai: {lap.get('desa', '')} - {lap.get('alamat', '')}"
            ).add_to(m)
        elif "sedang" in st_pen.lower():
            # Titik sedang ditangani: Radar Orange
            folium.Circle(location=[lat_val, lng_val], radius=100, color="#dd6b20", fill=True, fill_color="#dd6b20", fill_opacity=0.2, weight=1).add_to(m)
            folium.CircleMarker(location=[lat_val, lng_val], radius=7, color="#ffffff", weight=2, fill=True, fill_color="#dd6b20", fill_opacity=1.0, popup=folium.Popup(popup_lap, max_width=250), tooltip=f"Sedang Proses: {lap.get('desa', '')}").add_to(m)
        else:
            # Titik belum ditangani: RADAR MERAH MENYALA
            folium.Circle(location=[lat_val, lng_val], radius=150, color="#e53e3e", fill=True, fill_color="#e53e3e", fill_opacity=0.3, weight=1).add_to(m)
            folium.CircleMarker(location=[lat_val, lng_val], radius=8, color="#ffffff", weight=2, fill=True, fill_color="#e53e3e", fill_opacity=1.0, popup=folium.Popup(popup_lap, max_width=250), tooltip=f"Belum Ditangani: {lap.get('desa', '')}").add_to(m)

    st_folium(m, width="100%", height=620, returned_objects=[])

# --- TAB 2: PANEL VERIFIKASI & UPDATE STATUS (ADMIN) ---
elif menu_aktif == "🛠️ Panel Verifikasi & Status":
    st.subheader("🛠️ Manajemen & Pembaruan Status Laporan Warga")
    st.info("Petugas dapat memverifikasi laporan yang masuk dan memperbarui status eksekusi penanganan sampah.")

    if not df_laporan.empty:
        col_list, col_form = st.columns([1, 1.2])

        with col_list:
            st.markdown("##### Pilih Laporan untuk Ditindaklanjuti")
            pilihan_id = st.selectbox(
                "ID Laporan:",
                options=df_laporan[col_id].tolist(),
                format_func=lambda x: f"#{str(x)[:8]} - {df_laporan[df_laporan[col_id] == x]['desa'].values[0]} ({df_laporan[df_laporan[col_id] == x]['alamat'].values[0]})"
            )
            
            # Ambil data terpilih
            row_terpilih = df_laporan[df_laporan[col_id] == pilihan_id].iloc[0]
            st.write(f"**Nama Pelapor:** {row_terpilih.get('nama_pelapor', '-')}")
            st.write(f"**Waktu:** {row_terpilih.get('tanggal_laporan', '-')}")
            st.write(f"**Nomor Telepon:** {row_terpilih.get('nomor_telepon', '-')}")
            st.write(f"**Deskripsi Masalah:** {row_terpilih.get('deskripsi_lokasi', '-')}")
            
            if row_terpilih.get('foto_direct'):
                st.image(row_terpilih['foto_direct'], caption="Foto Bukti Lapangan", use_container_width=True)

        with col_form:
            st.markdown("##### Formulir Update Status Petugas")
            with st.form("form_update_status"):
                
                # Pilihan 3 Status: Belum, Sedang, Sudah
                status_verif_options = ["Belum diverifikasi", "Sedang diverifikasi", "Sudah diverifikasi"]
                current_verif = str(row_terpilih.get(col_verif, "Belum diverifikasi")).strip()
                idx_verif = status_verif_options.index(current_verif) if current_verif in status_verif_options else 0
                new_verif = st.selectbox("1. Status Verifikasi Lapangan:", status_verif_options, index=idx_verif)

                status_penanganan_options = ["Belum ditangani", "Sedang ditangani", "Sudah ditangani"]
                current_pen = str(row_terpilih.get(col_penanganan, "Belum ditangani")).strip()
                idx_pen = status_penanganan_options.index(current_pen) if current_pen in status_penanganan_options else 0
                new_pen = st.selectbox("2. Status Penanganan / Pengangkutan:", status_penanganan_options, index=idx_pen)

                catatan_petugas = st.text_area("Catatan Disposisi Armada (Opsional):", placeholder="Misal: Dijadwalkan armada truk nomor 02 jam 09.00 besok")

                btn_simpan = st.form_submit_button("💾 Simpan Perubahan Status", use_container_width=True)

                if btn_simpan:
                    # Update lokal dataframe sesi
                    df_laporan.loc[df_laporan[col_id] == pilihan_id, col_verif] = new_verif
                    df_laporan.loc[df_laporan[col_id] == pilihan_id, col_penanganan] = new_pen
                    
                    # Jika terhubung dengan endpoint Google Apps Script
                    if GAS_WEBAPP_URL and "GANTI" not in GAS_WEBAPP_URL:
                        try:
                            payload = {
                                "id_laporan": str(pilihan_id),
                                "status_verifikasi": new_verif,
                                "status_penanganan": new_pen,
                                "catatan": catatan_petugas
                            }
                            res = requests.post(GAS_WEBAPP_URL, json=payload, timeout=5)
                            st.success("✅ Status berhasil diperbarui dan tersinkron ke Google Sheets!")
                        except Exception as err:
                            st.warning(f"Berhasil diubah di dashboard, namun sinkronisasi otomatis ke Google Sheets gagal: {err}")
                    else:
                        st.success(f"✅ Status berhasil diubah menjadi: Verifikasi [{new_verif}] | Penanganan [{new_pen}]")
                        st.info("💡 Catatan: Untuk mengizinkan penulisan balik ke Google Sheets secara permanen, cukup sediakan doGet/doPost di Google Apps Script tim Anda.")
                    
                    st.cache_data.clear()
    else:
        st.warning("Belum ada data laporan yang tersedia untuk diverifikasi.")

# --- TAB 3: ANALITIK & EVALUASI RUTE ---
elif menu_aktif == "📊 Analitik & Evaluasi Rute":
    st.subheader("📊 Analitik & Evaluasi Sebaran Laporan vs Ketersediaan Fasilitas TPST")

    desa_tps = df_tps['desa'].value_counts() if not df_tps.empty and 'desa' in df_tps.columns else pd.Series(dtype=int)
    desa_lap = df_laporan['desa'].value_counts() if not df_laporan.empty and 'desa' in df_laporan.columns else pd.Series(dtype=int)

    all_desas = sorted(list(set(desa_tps.index.tolist() + desa_lap.index.tolist())))
    
    df_evaluasi = pd.DataFrame({
        "Desa": all_desas,
        "Jumlah TPS / TPST 3R": [desa_tps.get(d, 0) for d in all_desas],
        "Laporan Sampah Liar": [desa_lap.get(d, 0) for d in all_desas]
    })

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Perbandingan Fasilitas TPS vs Laporan Masuk per Desa**")
        fig_bar = px.bar(
            df_evaluasi, 
            x="Desa", 
            y=["Jumlah TPS / TPST 3R", "Laporan Sampah Liar"], 
            barmode="group",
            color_discrete_map={"Jumlah TPS / TPST 3R": "#38a169", "Laporan Sampah Liar": "#e53e3e"},
            template="plotly_dark"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        st.markdown("**Komposisi Status Penanganan**")
        if not df_laporan.empty and col_penanganan in df_laporan.columns:
            fig_pie = px.pie(
                df_laporan, 
                names=col_penanganan, 
                hole=0.4,
                template="plotly_dark",
                color=col_penanganan,
                color_discrete_map={"Belum ditangani": "#e53e3e", "Sedang ditangani": "#dd6b20", "Sudah ditangani": "#38a169"}
            )
            st.plotly_chart(fig_pie, use_container_width=True)

# --- TAB 4: TABEL REKAPITULASI DATA ---
elif menu_aktif == "📋 Tabel Rekapitulasi Data":
    st.subheader("📋 Rekapitulasi Tabulasi Data")
    tab1, tab2 = st.tabs(["Laporan Warga (Sampah Liar)", "Daftar Fasilitas TPS / TPST 3R"])
    with tab1:
        st.dataframe(df_laporan.drop(columns=['foto_direct'], errors='ignore'), use_container_width=True)
    with tab2:
        st.dataframe(df_tps, use_container_width=True)
