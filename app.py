import streamlit as st
from google import genai
from google.genai import types
import pandas as pd
import plotly.express as px
from PIL import Image
import requests
from io import BytesIO
from gtts import gTTS
import PyPDF2
import time

# ==========================================
# 1. KONFIGURASI SISTEM
# ==========================================
st.set_page_config(
    page_title="IEA INTELLIGENCE",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. ANTARMUKA VISUAL (HD & GLASSMORPHISM)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Orbitron:wght@500;700;900&family=JetBrains+Mono:wght@400&display=swap');

    /* --- TEMA DASAR --- */
    .stApp {
        background-color: #0a0a0f;
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }

    /* --- LOADING SCREEN (Cincin Berputar) --- */
    #loader {
        position: fixed; inset: 0; z-index: 999999;
        background-color: #0a0a0f;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        transition: opacity 0.8s ease-out;
    }
    .loader-hide { opacity: 0; pointer-events: none; }
    
    .ring { fill: none; stroke-width: 3; vector-effect: non-scaling-stroke; }
    .ring-1 { stroke: #a855f7; transform-origin: center; animation: ringSpin 2s linear infinite; }
    .ring-2 { stroke: #f97316; transform-origin: center; animation: ringSpinRev 3s linear infinite; }
    @keyframes ringSpin { 100% { transform: rotate(360deg); } }
    @keyframes ringSpinRev { 100% { transform: rotate(-360deg); } }
    
    .loader-text {
        font-family: 'Orbitron'; color: #a855f7; margin-top: 25px;
        letter-spacing: 4px; font-size: 0.8rem; animation: pulse 1.5s infinite;
    }
    @keyframes pulse { 50% { opacity: 0.4; } }

    /* --- SIDEBAR KACA --- */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 15, 20, 0.85);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* --- HEADER MEWAH --- */
    .iea-header {
        text-align: center; padding: 30px 0 10px 0;
        border-bottom: 1px solid rgba(168, 85, 247, 0.1);
        margin-bottom: 40px;
        animation: fadeInDown 1s ease;
    }
    .iea-title {
        font-family: 'Orbitron'; font-size: 3.5rem; font-weight: 900;
        background: linear-gradient(135deg, #a855f7 20%, #f97316 80%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-shadow: 0 0 40px rgba(168, 85, 247, 0.3);
        letter-spacing: -2px;
    }
    @keyframes fadeInDown { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }

    /* --- CHAT BUBBLES --- */
    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 20px;
        transition: transform 0.2s;
    }
    [data-testid="stChatMessage"]:hover {
        background: rgba(255, 255, 255, 0.04);
    }
    
    /* Avatar User (Oranye) */
    [data-testid="stChatMessageAvatarUser"] {
        background: linear-gradient(135deg, #f97316, #ea580c) !important;
        box-shadow: 0 0 15px rgba(249, 115, 22, 0.4);
    }
    /* Avatar AI (Ungu) */
    [data-testid="stChatMessageAvatarAssistant"] {
        background: linear-gradient(135deg, #a855f7, #7c3aed) !important;
        box-shadow: 0 0 15px rgba(168, 85, 247, 0.4);
    }

    /* --- TOMBOL & INPUT --- */
    .stButton>button {
        background: linear-gradient(90deg, #a855f7, #7c3aed);
        color: white; border: none; font-weight: 600;
        border-radius: 8px; padding: 0.5rem 1rem;
        transition: 0.3s;
    }
    .stButton>button:hover {
        box-shadow: 0 5px 20px rgba(168, 85, 247, 0.4);
        transform: translateY(-2px);
    }
    
    .stTextInput input, .stChatInput textarea {
        background-color: rgba(0,0,0,0.4) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #fff !important;
        border-radius: 12px !important;
    }
    .stChatInput textarea:focus {
        border-color: #a855f7 !important;
        box-shadow: 0 0 15px rgba(168, 85, 247, 0.2) !important;
    }

    /* --- HIDE DEFAULT ELEMENTS --- */
    #MainMenu, footer, header { visibility: hidden; }
    </style>

    <div id="loader">
        <div style="width: 120px; height: 120px;">
            <svg viewBox="0 0 200 200" style="width:100%; height:100%;">
                <ellipse class="ring ring-1" cx="100" cy="100" rx="90" ry="30" />
                <ellipse class="ring ring-2" cx="100" cy="100" rx="90" ry="30" />
                <text x="50%" y="55%" text-anchor="middle" dominant-baseline="middle" fill="#fff" font-family="Orbitron" font-weight="900" font-size="40">AI</text>
            </svg>
        </div>
        <div class="loader-text">MEMUAT NEURAL SYSTEM...</div>
    </div>

    <script>
        setTimeout(function() {
            const loader = document.getElementById('loader');
            loader.classList.add('loader-hide');
            setTimeout(() => { loader.style.display = 'none'; }, 1000);
        }, 2000);
    </script>
""", unsafe_allow_html=True)

# ==========================================
# 3. OTAK SISTEM (BACKEND)
# ==========================================

# Inisialisasi Google GenAI Client (Versi Baru)
def init_ai():
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key: return None
    return genai.Client(api_key=api_key)

# Pembaca PDF
def read_pdf(file):
    text = ""
    try:
        pdf = PyPDF2.PdfReader(file)
        for page in pdf.pages: text += page.extract_text()
    except: return "Gagal membaca dokumen enkripsi."
    return text

# NASA Data Fetcher
@st.cache_data(ttl=3600)
def get_nasa_daily():
    try:
        url = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY"
        return requests.get(url).json()
    except: return None

# ==========================================
# 4. SIDEBAR (PANEL KONTROL)
# ==========================================
with st.sidebar:
    st.markdown("<h3 style='font-family:Orbitron; color:#a855f7; text-align:center;'>PUSAT KONTROL</h3>", unsafe_allow_html=True)
    
    # 1. Navigasi Cepat
    st.link_button("🚀 KEMBALI KE PORTAL IEA", "https://xzam730.github.io/PORTAL-IEA/", type="primary", use_container_width=True)
    st.divider()

    # 2. Input Data Multimodal
    st.markdown("**📂 Input Data Penelitan**")
    
    # Upload Gambar (Mata AI)
    img_file = st.file_uploader("Upload Foto Langit/Objek", type=["jpg", "png", "jpeg"], help="AI akan menganalisis objek astronomi di foto ini.")
    
    # Upload Dokumen (Otak Baca)
    pdf_file = st.file_uploader("Upload Jurnal/Dokumen", type=["pdf"], help="AI akan membaca isi dokumen untuk referensi.")
    
    # Upload Data (Data Lab)
    csv_file = st.file_uploader("Upload Data CSV (Grafik)", type=["csv"], help="AI akan membuat visualisasi data otomatis.")

    st.divider()

    # 3. Widget NASA (Live Feed)
    nasa = get_nasa_daily()
    if nasa and "url" in nasa:
        st.image(nasa['url'], caption=f"NASA Daily: {nasa.get('title','Space')}")

    # 4. Reset
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔴 RESET MEMORI SISTEM", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ==========================================
# 5. HALAMAN UTAMA (CHAT & TOOLS)
# ==========================================

# Header Keren
st.markdown("""
<div class='iea-header'>
    <div class='iea-title'>IEA INTELLIGENCE</div>
    <div style='color:#888; letter-spacing:2px; font-size:0.9rem; margin-top:10px; font-family:Orbitron;'>
        ADVANCED ASTRONOMY & DATA ASSISTANT
    </div>
</div>
""", unsafe_allow_html=True)

# Cek Kunci Akses
client = init_ai()
if not client:
    st.error("⚠️ AKSES DITOLAK: Kunci API Google tidak ditemukan di System Secrets.")
    st.info("Harap masukkan GOOGLE_API_KEY di pengaturan Streamlit.")
    st.stop()

# Inisialisasi Riwayat Chat
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Sistem Online. Halo Peneliti, saya siap membantu analisis data astronomi, visualisasi grafik, atau diskusi ilmiah hari ini."}
    ]

# Tampilkan Chat Sebelumnya
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- BAGIAN LABORATORIUM DATA (AUTO CHART) ---
if csv_file:
    try:
        df = pd.read_csv(csv_file)
        with st.expander("📊 HASIL ANALISIS LABORATORIUM DATA", expanded=True):
            st.dataframe(df.head(), use_container_width=True)
            
            # Auto Plotting (Cerdas)
            numeric_cols = df.select_dtypes(include=['float', 'int']).columns
            if len(numeric_cols) >= 2:
                fig = px.line(df, x=numeric_cols[0], y=numeric_cols[1], title=f"Visualisasi Data: {numeric_cols[0]} vs {numeric_cols[1]}")
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
                st.plotly_chart(fig, use_container_width=True)
                st.caption("✅ Grafik dihasilkan otomatis oleh Neural Data Engine.")
    except Exception as e:
        st.error(f"Gagal memproses data: {e}")

# --- INPUT CHAT USER ---
if prompt := st.chat_input("Masukkan perintah penelitian..."):
    
    # 1. Simpan Pesan User
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if img_file:
            img = Image.open(img_file)
            st.image(img, width=300, caption="[Lampiran Visual]")
    
    # 2. Proses AI
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        with st.spinner("Menganalisis Database Semesta..."):
            try:
                # Kumpulkan Konteks
                contents = []
                
                # Instruksi Kepribadian
                sys_instruct = """
                Kamu adalah IEA Intelligence, asisten riset astronomi tingkat lanjut.
                Gaya Bicara: Formal, Ilmiah, namun mudah dipahami (Bahasa Indonesia).
                Tugas: Menjawab pertanyaan sains, menganalisis gambar antariksa, dan membantu riset.
                Format: Gunakan Markdown (Bold, List, Code Block) agar jawaban rapi.
                """
                contents.append(sys_instruct)

                # Masukkan Konteks PDF
                if pdf_file:
                    pdf_text = read_pdf(pdf_file)
                    contents.append(f"REFERENSI DOKUMEN: {pdf_text[:4000]}...")
                    st.toast("📄 Dokumen PDF sedang dibaca...")

                # Masukkan Gambar
                if img_file:
                    image_data = Image.open(img_file)
                    contents.append(image_data)
                    st.toast("👁️ Menganalisis visual...")

                # Masukkan Prompt User
                contents.append(prompt)

                # Generate Jawaban (Model: Gemini 1.5 Flash)
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=contents
                )
                
                full_response = response.text
                message_placeholder.markdown(full_response)

            except Exception as e:
                err_msg = f"⚠️ GANGGUAN SINYAL: {str(e)}"
                message_placeholder.error(err_msg)
                full_response = err_msg
        
        # Simpan Balasan AI
        st.session_state.messages.append({"role": "assistant", "content": full_response})
