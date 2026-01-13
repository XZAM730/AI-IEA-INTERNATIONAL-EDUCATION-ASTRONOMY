import streamlit as st
import requests
import time

# --- PENGAMAN IMPORT ---
try:
    from langchain_groq import ChatGroq
    from langchain_core.messages import SystemMessage, HumanMessage
except ImportError:
    st.error("Library missing! Periksa requirements.txt")

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="IEA COSMOS",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS: ULTRA CLEAN & RESPONSIVE UI ---
st.markdown("""
    <style>
    /* Dasar Tema: Gelap Pekat untuk Kontras Maksimal */
    .stApp {
        background-color: #050505;
        color: #FFFFFF;
    }

    /* Judul Utama: Tanpa Ikon, Terang & Bold */
    .main-title {
        font-family: 'Inter', sans-serif;
        font-size: clamp(2rem, 8vw, 4rem);
        font-weight: 800;
        text-align: center;
        color: #00FBFF;
        text-transform: uppercase;
        letter-spacing: -2px;
        margin-top: 50px;
        line-height: 1;
    }

    .sub-title {
        font-family: monospace;
        text-align: center;
        color: #BC13FE;
        letter-spacing: 5px;
        font-size: 0.8rem;
        margin-bottom: 40px;
    }

    /* Container Login & Chat agar Nyaman di Semua Gadget */
    .stTextInput > div > div > input {
        background-color: #111111 !important;
        color: white !important;
        border: 1px solid #333333 !important;
        border-radius: 10px !important;
        font-size: 1.1rem !important;
        padding: 15px !important;
    }

    /* Menghilangkan Spasi Putih Berlebih di Mobile */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 900px !important;
    }

    /* Chat Bubble: Full Width di Mobile */
    .stChatMessage {
        background-color: #111111 !important;
        border: 1px solid #222222 !important;
        border-radius: 15px !important;
        padding: 20px !important;
        margin-bottom: 15px !important;
    }

    /* Menghilangkan Ikon Avatar Chat agar Text Lebih Luas */
    [data-testid="stChatMessageAvatarUser"], 
    [data-testid="stChatMessageAvatarAssistant"] {
        display: none !important;
    }

    /* Tombol: Kontras Tinggi & Reaktif */
    .stButton > button {
        width: 100% !important;
        background: #00FBFF !important;
        color: #000000 !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 15px !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        border-radius: 10px !important;
        transition: 0.3s !important;
    }

    .stButton > button:hover {
        background: #BC13FE !important;
        color: white !important;
        box-shadow: 0 0 20px rgba(188, 19, 254, 0.4);
    }

    /* Status Box / Loading */
    div[data-testid="stStatusWidget"] {
        background-color: #000000 !important;
        border: 1px solid #00FBFF !important;
        color: #00FBFF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE & CONFIG ---
FIREBASE_URL = "https://iea-pendaftaran-default-rtdb.asia-southeast1.firebasedatabase.app"
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

def check_membership(name):
    name = name.strip().lower()
    grup_list = ["iea_grup_1", "iea_grup_2"]
    try:
        for grup in grup_list:
            res = requests.get(f"{FIREBASE_URL}/{grup}.json", timeout=10)
            data = res.json()
            if data:
                for key in data:
                    if data[key].get('n', '').lower() == name: return True
        return False
    except: return False

# --- STATE ---
if "auth" not in st.session_state: st.session_state.auth = False
if "msgs" not in st.session_state: st.session_state.msgs = []

# --- HALAMAN LOGIN ---
if not st.session_state.auth:
    st.markdown("<h1 class='main-title'>IEA COSMOS</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>QUANTUM SECURE TERMINAL</p>", unsafe_allow_html=True)
    
    with st.container():
        nama = st.text_input("MASUKKAN NAMA LENGKAP", placeholder="Tulis nama anda...")
        if st.button("BUKA AKSES"):
            if nama:
                with st.status("MENGECEK OTORISASI...", expanded=True) as status:
                    if check_membership(nama):
                        st.session_state.auth = True
                        st.session_state.user = nama.upper()
                        status.update(label="AKSES DIBERIKAN", state="complete")
                        st.rerun()
                    else:
                        st.error("NAMA TIDAK TERDAFTAR")

# --- HALAMAN CHAT ---
else:
    st.markdown(f"<h3 style='color:#00FBFF; margin-bottom:0;'>OPERATOR: {st.session_state.user}</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#666; font-size:0.8rem; margin-bottom:30px;'>Koneksi: Terenkripsi (Llama 3.3 70B)</p>", unsafe_allow_html=True)

    # Tampilkan Pesan
    for m in st.session_state.msgs:
        with st.chat_message(m["role"]):
            st.markdown(f"<div style='font-size:1.1rem; line-height:1.6;'>{m['content']}</div>", unsafe_allow_html=True)

    # Input Chat
    if prompt := st.chat_input("Ketik pertanyaan anda..."):
        st.session_state.msgs.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.status("MENGOLAH DATA SEMESTA...", expanded=False) as status:
                try:
                    llm = ChatGroq(temperature=0.7, groq_api_key=GROQ_API_KEY, model_name="llama-3.3-70b-versatile")
                    sys_msg = f"Kamu adalah IEA AI. User bernama {st.session_state.user}. Jawablah dengan cerdas, jelas, dan profesional dalam bahasa Indonesia."
                    
                    res = llm.invoke([SystemMessage(content=sys_msg), HumanMessage(content=prompt)]).content
                    status.update(label="DATA DITERIMA", state="complete")
                    
                    st.markdown(f"<div style='font-size:1.1rem; line-height:1.6;'>{res}</div>", unsafe_allow_html=True)
                    st.session_state.msgs.append({"role": "assistant", "content": res})
                except Exception as e:
                    st.error(f"Koneksi Terputus: {e}")
