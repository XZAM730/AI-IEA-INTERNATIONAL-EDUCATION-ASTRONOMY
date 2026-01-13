import streamlit as st
import requests
import time

# --- PENGAMAN IMPORT LIBRARY ---
try:
    from langchain_groq import ChatGroq
    from langchain_core.messages import SystemMessage, HumanMessage
except ImportError:
    st.error(" Library missing! Pastikan requirements.txt sudah benar.")

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="IEA COSMOS AI",
    page_icon="🌌",
    layout="wide"
)

# --- CSS: FUTURISTIC ANIMATION & UI ---
st.markdown("""
    <style>
    /* Background & Font */
    .stApp {
        background: radial-gradient(circle at top, #1a0033 0%, #05000a 100%);
        color: #e0e0e0;
    }

    /* Efek Loading Pulse untuk Judul */
    @keyframes pulse {
        0% { text-shadow: 0 0 10px #bc13fe; }
        50% { text-shadow: 0 0 25px #00f2ff, 0 0 40px #bc13fe; }
        100% { text-shadow: 0 0 10px #bc13fe; }
    }
    .loading-text {
        animation: pulse 2s infinite;
        font-family: 'Courier New', monospace;
        color: #00f2ff;
        text-align: center;
    }

    /* Card Glassmorphism */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(188, 19, 254, 0.2);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 0 30px rgba(188, 19, 254, 0.1);
    }

    /* Custom Spinner */
    .stSpinner > div {
        border-top-color: #bc13fe !important;
    }

    /* Button Neon */
    .stButton>button {
        background: linear-gradient(45deg, #4b0082, #bc13fe) !important;
        border: none !important;
        color: white !important;
        font-weight: bold !important;
        letter-spacing: 3px !important;
        height: 3em !important;
        transition: 0.5s !important;
    }
    .stButton>button:hover {
        box-shadow: 0 0 20px #bc13fe !important;
        transform: scale(1.02);
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE & API ---
FIREBASE_URL = "https://iea-pendaftaran-default-rtdb.asia-southeast1.firebasedatabase.app"
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

def check_membership(name):
    name = name.strip().lower()
    grup_list = ["iea_grup_1", "iea_grup_2"]
    try:
        for grup in grup_list:
            data = requests.get(f"{FIREBASE_URL}/{grup}.json").json()
            if data:
                for key in data:
                    if data[key].get('n', '').lower() == name: return True
        return False
    except: return False

# --- LOGIC SESSION ---
if "auth" not in st.session_state: st.session_state.auth = False
if "msgs" not in st.session_state: st.session_state.msgs = []

# --- UI LOGIN ---
if not st.session_state.auth:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align:center; color:#bc13fe;'>IEA TERMINAL</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:0.8em;'>QUANTUM ENCRYPTION ENABLED</p>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            nama = st.text_input("USER IDENTIFICATION", placeholder="Type your name...")
            
            if st.button("CONNECT TO COSMOS"):
                if nama:
                    # EFEK LOADING LOGIN YANG KEREN
                    with st.status(" Establishing Quantum Link...", expanded=True) as status:
                        st.write(" Scanning IEA Database...")
                        time.sleep(1)
                        if check_membership(nama):
                            st.write(" Identity Verified.")
                            time.sleep(0.5)
                            st.write(" Syncing with Deep Space Network...")
                            time.sleep(1)
                            st.session_state.auth = True
                            st.session_state.user = nama.upper()
                            status.update(label="CONNECTION ESTABLISHED", state="complete")
                            st.rerun()
                        else:
                            st.error(" ACCESS DENIED: Identity Unknown.")
            st.markdown("</div>", unsafe_allow_html=True)

# --- UI CHAT ---
else:
    st.markdown(f"<p class='loading-text'>SATELLITE LINK ACTIVE: {st.session_state.user}</p>", unsafe_allow_html=True)
    
    # Riwayat Chat
    for m in st.session_state.msgs:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # Input Chat
    if prompt := st.chat_input("Tanya apa saja tentang alam semesta..."):
        st.session_state.msgs.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant", avatar="🌌"):
            # EFEK LOADING CHAT YANG KEREN
            with st.status(" Processing Data...", expanded=False) as status:
                st.write("🔭 Pointing telescope to target...")
                time.sleep(0.5)
                st.write("📡 Decoding radio waves...")
                
                try:
                    llm = ChatGroq(temperature=0.7, groq_api_key=GROQ_API_KEY, model_name="llama3-8b-8192")
                    sys_msg = f"Kamu adalah AI IEA, asisten astronomi tercanggih. Kamu berbicara dengan {st.session_state.user}. Jawab dengan gaya futuristik, cerdas, dan inspiratif."
                    
                    res = llm.invoke([SystemMessage(content=sys_msg), HumanMessage(content=prompt)]).content
                    status.update(label="SIGNAL RECEIVED", state="complete")
                    
                    st.markdown(res)
                    st.session_state.msgs.append({"role": "assistant", "content": res})
                except Exception as e:
                    st.error(f"Signal Lost: {e}")
