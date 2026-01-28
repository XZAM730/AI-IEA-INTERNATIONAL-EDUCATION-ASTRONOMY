import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
from io import BytesIO
from gtts import gTTS
import PyPDF2
import time

# ==========================================
# 1. KONFIGURASI HALAMAN (WAJIB PALING ATAS)
# ==========================================
st.set_page_config(
    page_title="IEA INTELLIGENCE",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="collapsed" # Sidebar tertutup biar clean pas awal
)

# ==========================================
# 2. INJECT CSS & LOADER (VISUAL HD)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Orbitron:wght@500;700;900&display=swap');

    /* --- GLOBAL THEME --- */
    .stApp {
        background-color: #0a0a0f;
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }

    /* --- LOADING SCREEN (Sama Persis Portal) --- */
    #loader {
        position: fixed; inset: 0; z-index: 999999;
        background-color: #0a0a0f;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        transition: opacity 1s ease-out;
    }
    .loader-hide { opacity: 0; pointer-events: none; }
    
    .ring { fill: none; stroke-width: 3; }
    .ring-1 { stroke: #a855f7; transform-origin: center; animation: ringSpin 2s linear infinite; }
    .ring-2 { stroke: #f97316; transform-origin: center; animation: ringSpinRev 3s linear infinite; }
    @keyframes ringSpin { 100% { transform: rotate(360deg); } }
    @keyframes ringSpinRev { 100% { transform: rotate(-360deg); } }
    
    .loader-text {
        font-family: 'Orbitron'; color: #a855f7; margin-top: 20px;
        letter-spacing: 3px; font-size: 0.9rem; animation: pulse 1s infinite;
    }
    @keyframes pulse { 50% { opacity: 0.5; } }

    /* --- SIDEBAR GLASSMORPHISM --- */
    [data-testid="stSidebar"] {
        background-color: rgba(20, 20, 30, 0.85);
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* --- CUSTOM HEADER --- */
    .iea-header {
        text-align: center; padding: 20px 0;
        border-bottom: 1px solid rgba(168, 85, 247, 0.2);
        margin-bottom: 30px;
    }
    .iea-title {
        font-family: 'Orbitron'; font-size: 3rem; font-weight: 900;
        background: linear-gradient(to right, #a855f7, #f97316);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(168, 85, 247, 0.4);
    }

    /* --- CHAT BUBBLES --- */
    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    [data-testid="stChatMessageAvatarUser"] { background-color: #f97316 !important; }
    [data-testid="stChatMessageAvatarAssistant"] { background-color: #a855f7 !important; }

    /* --- HIDE DEFAULT ELEMENTS --- */
    #MainMenu, footer, header { visibility: hidden; }
    
    /* --- INPUT BOX --- */
    .stTextInput input, .stChatInput textarea {
        background-color: rgba(0,0,0,0.3) !important;
        border: 1px solid rgba(168, 85, 247, 0.3) !important;
        color: white !important;
        border-radius: 12px !important;
    }
    .stChatInput textarea:focus {
        border-color: #f97316 !important;
        box-shadow: 0 0 15px rgba(249, 115, 22, 0.2) !important;
    }
    </style>

    <div id="loader">
        <div style="width: 100px; height: 100px;">
            <svg viewBox="0 0 200 200">
                <ellipse class="ring ring-1" cx="100" cy="100" rx="90" ry="30" />
                <ellipse class="ring ring-2" cx="100" cy="100" rx="90" ry="30" />
                <text x="50%" y="55%" text-anchor="middle" dominant-baseline="middle" fill="#fff" font-family="Orbitron" font-weight="900" font-size="50">AI</text>
            </svg>
        </div>
        <div class="loader-text">MENGHUBUNGKAN NEURAL NETWORK...</div>
    </div>

    <script>
        setTimeout(function() {
            const loader = document.getElementById('loader');
            loader.classList.add('loader-hide');
            setTimeout(() => { loader.style.display = 'none'; }, 1000);
        }, 2500); // Loader muncul selama 2.5 detik
    </script>
""", unsafe_allow_html=True)

# ==========================================
# 3. BACKEND LOGIC (The Brain)
# ==========================================

# Setup Gemini
def init_gemini():
    # Mengambil API Key dari Secrets (Aman)
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key: return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

# Fungsi Baca PDF
def get_pdf_text(pdf_file):
    text = ""
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        for page in reader.pages: text += page.extract_text()
    except: return "Gagal membaca PDF."
    return text

# Fungsi NASA
@st.cache_data(ttl=3600)
def get_nasa_apod():
    try:
        url = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY"
        return requests.get(url).json()
    except: return None

# ==========================================
# 4. SIDEBAR (CONTROL PANEL)
# ==========================================
with st.sidebar:
    st.markdown("<h3 style='font-family:Orbitron; color:#a855f7;'>KONTROL SISTEM</h3>", unsafe_allow_html=True)
    
    # 1. Navigasi
    st.link_button("🏠 KEMBALI KE PORTAL", "https://xzam730.github.io/PORTAL-IEA/", type="primary")
    
    st.divider()
    
    # 2. Upload Tools
    st.markdown("**📂 Input Data**")
    uploaded_image = st.file_uploader("Upload Foto Bintang/Galaksi", type=["jpg", "png", "jpeg"])
    uploaded_pdf = st.file_uploader("Upload Jurnal PDF", type=["pdf"])
    
    st.divider()

    # 3. Fitur Utilitas (Kalkulator Mini)
    st.markdown("**🧮 Kalkulator Astrofisika**")
    calc_mode = st.selectbox("Pilih Alat:", ["Konversi Tahun Cahaya", "Berat di Mars"])
    if calc_mode == "Konversi Tahun Cahaya":
        ly = st.number_input("Tahun Cahaya (ly):", value=1.0)
        km = ly * 9.461e12
        st.code(f"{km:.2e} km")
    else:
        weight = st.number_input("Berat di Bumi (kg):", value=60)
        mars_w = weight * 0.38
        st.code(f"{mars_w:.2f} kg di Mars")

    st.divider()
    
    # 4. Widget NASA
    nasa = get_nasa_apod()
    if nasa and "url" in nasa:
        st.image(nasa['url'], caption="NASA Live Feed")
    
    # 5. Clear Chat
    if st.button("🗑️ Reset Memori"):
        st.session_state.messages = []
        st.rerun()

# ==========================================
# 5. HALAMAN UTAMA (CHAT INTERFACE)
# ==========================================

# Header Keren
st.markdown("""
<div class='iea-header'>
    <div class='iea-title'>IEA INTELLIGENCE</div>
    <div style='color:#888; letter-spacing:1px; margin-top:5px;'>ADVANCED ASTRONOMY ASSISTANT</div>
</div>
""", unsafe_allow_html=True)

# Cek API Key
model = init_gemini()
if not model:
    st.error("⚠️ SISTEM OFFLINE: Masukkan GOOGLE_API_KEY di Streamlit Secrets.")
    st.stop()

# Session State History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Halo Peneliti. Sistem IEA Intelligence siap. Ada yang bisa saya bantu analisis hari ini?"}
    ]

# Tampilkan Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# INPUT CHAT USER
if prompt := st.chat_input("Perintahkan sistem..."):
    
    # 1. Render User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_image:
            img = Image.open(uploaded_image)
            st.image(img, width=300, caption="Gambar dianalisis")
    
    # 2. Proses AI
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        with st.spinner("Mengakses Database Neural..."):
            try:
                # Siapkan Konteks
                context = ""
                vision_input = []
                
                if uploaded_pdf:
                    pdf_text = get_pdf_text(uploaded_pdf)
                    context += f"\n[SUMBER PDF USER]:\n{pdf_text[:3000]}\n"
                
                system_instruction = f"""
                Kamu adalah AI Resmi dari IEA (International Education Astronomy).
                Gaya Bicara: Profesional, Ilmiah, tapi mudah dimengerti (Bahasa Indonesia).
                Tugas: Menjawab pertanyaan astronomi, fisika, dan analisis data.
                Konteks Tambahan: {context}
                Jika user mengirim gambar, analisis objek astronomi tersebut secara detail.
                """
                
                # Cek Input (Gambar atau Teks)
                input_parts = [system_instruction, prompt]
                if uploaded_image:
                    img = Image.open(uploaded_image)
                    input_parts.append(img)
                
                # Generate
                response = model.generate_content(input_parts)
                full_response = response.text
                
                # Efek Mengetik (Typing Effect)
                # Kita tidak pakai stream biar format markdown rapi
                message_placeholder.markdown(full_response)
                
            except Exception as e:
                full_response = f"⚠️ Terjadi kesalahan koneksi: {str(e)}"
                message_placeholder.error(full_response)
        
        # Simpan Respons ke History
        st.session_state.messages.append({"role": "assistant", "content": full_response})
