import streamlit as st
import pandas as pd
import folium
from folium import DivIcon
from streamlit_folium import st_folium
import plotly.express as px

# 1. Konfigurasi Halaman & Tema Gelap Command Center
st.set_page_config(
    page_title="TERASI - Monitoring Sampah Wonoayu",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan Dashboard Dark-Modern ala Command Center
st.markdown("""
<style>
    /* Styling Card & Feed di Sidebar */
    .report-card {
        background-color: #1a1e24;
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 8px;
        border-left: 4px solid #e63946;
        font-size: 13px;
    }
    .badge-urgent {
        background-color: #e63946;
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: bold;
    }
    .badge-process {
        background-color: #f39c12;
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: bold;
    }
    .badge-done {
        background-color: #2ecc71;
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# 2. Dataset Dummy Representatif Wilayah Wonoayu, Sidoarjo
# Titik Resmi TPST 3R
DATA_TPST = pd.DataFrame([
    {"id": "TPST-01", "nama": "TPST 3R Popoh Mandiri", "desa": "Popoh", "lat": -7.4290, "lng": 112.6045, "kapasitas": "8 Ton/hari"},
    {"id": "TPST-02", "nama": "TPST 3R Wonoayu Bersih", "desa": "Wonoayu", "lat": -7.4365, "lng": 112.6180, "kapasitas": "12 Ton/hari"},
    {"id": "TPST-03", "nama": "TPST 3R Candinegoro", "desa": "Candinegoro", "lat": -7.4180, "lng": 112.6240, "kapasitas": "6 Ton/hari"},
    {"id": "TPST-04", "nama": "TPST 3R Pilang Hijau", "desa": "Pilang", "lat": -7.4520, "lng": 112.6310, "kapasitas": "10 Ton/hari"},
])

# Titik Laporan Sampah Liar Warga
DATA_SAMPAH_LIAR = pd.DataFrame([
    {"id": "REP-01", "lokasi": "Bantaran Saluran Irigasi Desa Becirongengor", "desa": "Becirongengor", "lat": -7.4230, "lng": 112.6090, "status": "Urgent", "waktu": "10m lalu", "foto": "https://images.unsplash.com/photo-1605600659873-d808a13e4d2a?w=300", "estimasi": "Tumpukan ±2 Truk"},
    {"id": "REP-02", "lokasi": "Lahan Kosong Dekat Pasar Jimbaran", "desa": "Jimbaran Wetan", "lat": -7.4410, "lng": 112.6050, "status": "Proses", "waktu": "25m lalu", "foto": "https://images.unsplash.com/photo-1530587191325-3db32d826c18?w=300", "estimasi": "Sampah Plastik Liar"},
    {"id": "REP-03", "lokasi": "Tepi Jalan Alternatif Tanggul Ploso", "desa": "Ploso", "lat": -7.4470, "lng": 112.6210, "status": "Urgent", "waktu": "1j lalu", "foto": "https://images.unsplash.com/photo-1611284446314-60a58ac0deb9?w=300", "estimasi": "Limbah Rumah Tangga"},
    {"id": "REP-04", "lokasi": "Pinggir Saluran Desa Sawocangkring", "desa": "Sawocangkring", "lat": -7.4320, "lng": 112.6360, "status": "Menunggu", "waktu": "2j lalu", "foto": "https://images.unsplash.com/photo-1528323273322-d81458248d40?w=300", "estimasi": "Tumpukan Ranting & Plastik"},
    {"id": "REP-05", "lokasi": "Tikungan Perbatasan Desa Lambangan", "desa": "Lambangan", "lat": -7.4150, "lng": 112.6130, "status": "Selesai", "waktu": "4j lalu", "foto": "https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?w=300", "estimasi": "Sudah Diangkut Armada"},
])

# 3. Sidebar: Brand, Navigasi, Analytics, & Feed Laporan
with st.sidebar:
    st.markdown("### ♻️ **TERASI WONOAYU**")
    st.caption("Sistem Informasi & Tanggap Darurat Sampah Terpadu")
    st.divider()

    # Navigasi Menu
    menu = st.radio("Navigasi", ["Dashboard Peta", "Analitik & Evaluasi Rute", "Pengaturan Armada"], label_visibility="collapsed")
    st.divider()

    # KPI Metrics Ringkas
    total_tpst = len(DATA_TPST)
    total_liar = len(DATA_SAMPAH_LIAR[DATA_SAMPAH_LIAR['status'] != 'Selesai'])
    
    col_kpi1, col_kpi2 = st.columns(2)
    col_kpi1.metric("TPST 3R Aktif", f"{total_tpst}", delta="Operasional")
    col_kpi2.metric("Titik Liar Aktif", f"{total_liar}", delta="-1 Teratasi", delta_color="inverse")

    st.divider()

    # Citizen Report Feed (Daftar Laporan Warga Realtime)
    st.markdown("#### 🚨 Laporan Warga Terkini")
    for _, row in DATA_SAMPAH_LIAR.iterrows():
        badge_class = "badge-urgent" if row['status'] == "Urgent" else ("badge-process" if row['status'] == "Proses" else "badge-done")
        st.markdown(f"""
        <div class="report-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <b>{row['id']}</b>
                <span class="{badge_class}">{row['status']}</span>
            </div>
            <div style="margin-top: 4px; color: #ddd;">{row['lokasi']}</div>
            <small style="color: #888;">Desa {row['desa']} • {row['waktu']}</small>
        </div>
        """, unsafe_allow_html=True)

# 4. Area Konten Utama
if menu == "Dashboard Peta":
    st.subheader("🗺️ Kendali Spasial Wilayah Kecamatan Wonoayu")
    
    # CSS Animasi Radar Berkedip untuk Folium
    radar_css = """
    <style>
        .radar-pulse-container {
            position: relative;
            width: 50px;
            height: 50px;
        }
        .radar-core {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 14px;
            height: 14px;
            background: #ff2a2a;
            border: 2px solid #ffffff;
            border-radius: 50%;
            box-shadow: 0 0 12px #ff0000;
            z-index: 2;
        }
        .radar-ring {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 44px;
            height: 44px;
            border: 2px solid rgba(255, 42, 42, 0.85);
            border-radius: 50%;
            background: rgba(255, 0, 0, 0.2);
            animation: radarPulsing 1.6s ease-out infinite;
            z-index: 1;
        }
        @keyframes radarPulsing {
            0% {
                transform: translate(-50%, -50%) scale(0.3);
                opacity: 1;
            }
            100% {
                transform: translate(-50%, -50%) scale(1.6);
                opacity: 0;
            }
        }
        .tpst-pin {
            background-color: #00e676;
            border: 2px solid #ffffff;
            color: #003314;
            border-radius: 50%;
            text-align: center;
            font-size: 16px;
            font-weight: bold;
            width: 32px;
            height: 32px;
            line-height: 28px;
            box-shadow: 0 0 15px rgba(0, 230, 118, 0.7);
        }
    </style>
    """
    st.markdown(radar_css, unsafe_allow_html=True)

    # Inisialisasi Peta Folium (Pusat di Wonoayu, Sidoarjo)
    m = folium.Map(
        location=[-7.4330, 112.6170],
        zoom_start=14,
        tiles="CartoDB dark_matter",
        control_scale=True
    )

    # 4A. Render Titik Fasilitas TPST 3R (Pin Hijau Resmi)
    for _, tpst in DATA_TPST.iterrows():
        popup_html = f"""
        <div style="font-family: Arial; width: 200px; color: #222;">
            <h4 style="margin: 0; color: #1b5e20;">♻️ {tpst['nama']}</h4>
            <hr style="margin: 4px 0;">
            <p style="font-size: 12px; margin: 2px 0;"><b>Wilayah:</b> Desa {tpst['desa']}</p>
            <p style="font-size: 12px; margin: 2px 0;"><b>Kapasitas:</b> {tpst['kapasitas']}</p>
            <span style="background: #e8f5e9; color: #2e7d32; padding: 2px 6px; border-radius: 4px; font-size: 11px;">Status: Aktif</span>
        </div>
        """
        icon_tpst = DivIcon(
            icon_size=(32, 32),
            icon_anchor=(16, 16),
            html='<div class="tpst-pin">♻</div>'
        )
        folium.Marker(
            location=[tpst['lat'], tpst['lng']],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"Fasilitas TPST: {tpst['nama']}",
            icon=icon_tpst
        ).add_to(m)

    # 4B. Render Titik Sampah Liar (Efek Radar Berkedip Merah)
    for _, liar in DATA_SAMPAH_LIAR.iterrows():
        popup_liar = f"""
        <div style="font-family: Arial; width: 230px; color: #222;">
            <h4 style="margin: 0; color: #c0392b;">⚠️ {liar['id']} - Sampah Liar</h4>
            <hr style="margin: 4px 0;">
            <img src="{liar['foto']}" style="width: 100%; height: 110px; object-fit: cover; border-radius: 4px; margin-bottom: 4px;">
            <p style="font-size: 11px; margin: 2px 0;"><b>Lokasi:</b> {liar['lokasi']}</p>
            <p style="font-size: 11px; margin: 2px 0;"><b>Estimasi:</b> {liar['estimasi']}</p>
            <p style="font-size: 11px; margin: 2px 0;"><b>Pelaporan:</b> {liar['waktu']}</p>
            <span style="background: #ffebee; color: #c62828; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold;">Prioritas: {liar['status']}</span>
        </div>
        """
        radar_icon = DivIcon(
            icon_size=(50, 50),
            icon_anchor=(25, 25),
            html='<div class="radar-pulse-container"><div class="radar-ring"></div><div class="radar-core"></div></div>'
        )
        folium.Marker(
            location=[liar['lat'], liar['lng']],
            popup=folium.Popup(popup_liar, max_width=260),
            tooltip=f"Laporan Masuk: {liar['lokasi']} ({liar['status']})",
            icon=radar_icon
        ).add_to(m)

    # 4C. Opsi Visualisasi Jalur Pengangkutan (Rute Evaluasi Armada)
    coords_rute = [
        [DATA_TPST.iloc[0]['lat'], DATA_TPST.iloc[0]['lng']],
        [DATA_SAMPAH_LIAR.iloc[0]['lat'], DATA_SAMPAH_LIAR.iloc[0]['lng']],
        [DATA_TPST.iloc[1]['lat'], DATA_TPST.iloc[1]['lng']],
        [DATA_SAMPAH_LIAR.iloc[1]['lat'], DATA_SAMPAH_LIAR.iloc[1]['lng']],
        [DATA_TPST.iloc[3]['lat'], DATA_TPST.iloc[3]['lng']]
    ]
    folium.PolyLine(
        locations=coords_rute,
        color="#f39c12",
        weight=2.5,
        opacity=0.7,
        dash_array="6, 8",
        tooltip="Simulasi Koridor Pengangkutan Armada"
    ).add_to(m)

    # Tampilkan Peta ke Streamlit
    st_folium(m, width="100%", height=620, returned_objects=[])

elif menu == "Analitik & Evaluasi Rute":
    st.subheader("📊 Analitik & Rasio Kebutuhan TPST per Desa")
    
    # Agregasi Data per Desa
    desa_list = ["Popoh", "Wonoayu", "Candinegoro", "Pilang", "Becirongengor", "Jimbaran Wetan", "Ploso", "Sawocangkring", "Lambangan"]
    df_evaluasi = pd.DataFrame({
        "Desa": desa_list,
        "Jumlah TPST 3R": [1, 1, 1, 1, 0, 0, 0, 0, 0],
        "Laporan Sampah Liar": [0, 0, 0, 0, 1, 1, 1, 1, 1]
    })
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("**Perbandingan Ketersediaan TPST vs Titik Liar**")
        fig_bar = px.bar(
            df_evaluasi, 
            x="Desa", 
            y=["Jumlah TPST 3R", "Laporan Sampah Liar"], 
            barmode="group",
            color_discrete_map={"Jumlah TPST 3R": "#2ecc71", "Laporan Sampah Liar": "#e74c3c"},
            template="plotly_dark"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_chart2:
        st.markdown("**Proporsi Status Penanganan Sampah Liar**")
        fig_pie = px.pie(
            DATA_SAMPAH_LIAR, 
            names="status", 
            color="status",
            color_discrete_map={"Urgent": "#e74c3c", "Proses": "#f39c12", "Menunggu": "#3498db", "Selesai": "#2ecc71"},
            hole=0.45,
            template="plotly_dark"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("#### 💡 Rekomendasi Alokasi Armada")
    st.info("Desa **Becirongengor, Ploso, dan Sawocangkring** saat ini belum memiliki TPST 3R aktif namun memiliki laporan berstatus *Urgent*. Disarankan membuat jadwal armada keliling dari **TPST Wonoayu Bersih** ke wilayah-wilayah tersebut.")

elif menu == "Pengaturan Armada":
    st.subheader("🚛 Penjadwalan & Disposisi Petugas")
    st.dataframe(
        DATA_SAMPAH_LIAR[["id", "desa", "lokasi", "estimasi", "status", "waktu"]],
        use_container_width=True
    )
