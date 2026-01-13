import streamlit as st
import requests
import time

# --- PENGAMAN IMPORT ---
try:
    from langchain_groq import ChatGroq
    from langchain_core.messages import SystemMessage, HumanMessage
except ImportError:
    st.error("🚨 Library error! Pastikan requirements.txt sudah benar.")

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="IEA COSMOS TERMINAL",
    page_icon="🔭",
    layout="wide"
)

# --- CSS: ULTIMATE FUTURISTIC UI ---
st.markdown("""
    <style>
    /* Reset & Base Theme */
    .stApp {
        background: radial-gradient(circle at top right, #0d001a, #020107);
        color: #e0e0e0;
    }

    /* Typography Logo (Ganti Gambar) */
    .nebula-title {
        font-family: 'Courier New', Courier, monospace;
        font-size: 3.5rem;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(90deg, #00f2ff, #bc13fe, #00f2ff);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 3s linear infinite;
        margin-bottom: 0;
    }

    @keyframes shine {
        to { background-position: 200% center; }
    }

    /* Glassmorphism Container */
    .glass-panel {
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(20px);
        border-radius: 25px;
        border: 1px solid rgba(0, 242, 255, 0.1);
        padding: 40px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
    }

    /* Input & Chat Styling */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.03) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(188, 19, 254, 0.1) !important;
        transition: 0.3s;
    }

    .stChatMessage:hover {
        border-color: rgba(0, 242, 255, 0.4) !important;
        background: rgba(255, 255, 255, 0.05) !important;
    }

    /* Responsivitas Gadget */
    @media (max-width: 768px) {
        .nebula-title { font-size: 2rem; }
        .glass-panel { padding: 20px; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE & CONFIG ---
FIREBASE_URL = "https://iea-pendaftaran-default-rtdb.asia-southeast1.firebasedatabase.app"
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

# --- LOGIC PEMERIKSAAN MEMBER ---
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

# --- STATE MANAGEMENT ---
if "auth" not in st.session_state: st.session_state.auth = False
if "chat_history" not in st.session_state: st.session_state.chat_history = []

# --- HALAMAN LOGIN ---
if not st.session_state.auth:
    st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='nebula-title'>IEA QUANTUM</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; letter-spacing: 5px; color:#bc13fe; font-size:0.7rem;'>SECURE ASTRONOMY INTERFACE</p>", unsafe_allow_html=True)
    
    _, col_mid, _ = st.columns([1, 2, 1])
    with col_mid:
        st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
        user_input = st.text_input("ENTER ACCESS KEY (NAME)", placeholder="Your registered name...")
        
        if st.button("AUTHORIZE ACCESS"):
            if user_input:
                with st.status("Initializing Security Protocol...", expanded=True) as status:
                    st.write("📡 Connecting to IEA Firebase...")
                    time.sleep(1)
                    if check_membership(user_input):
                        st.write("🔓 Identity Decrypted. Access Granted.")
                        st.session_state.auth = True
                        st.session_state.user = user_input.upper()
                        status.update(label="SYSTEM READY", state="complete")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ UNAUTHORIZED: Name not in records.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- HALAMAN CHAT ---
else:
    # Sidebar Info
    with st.sidebar:
        st.markdown(f"### 👩‍🚀 Operator: {st.session_state.user}")
        st.markdown("---")
        st.caption("IEA AI v2.5 - Model: Llama 3.3 70B")
        if st.button("Logout"):
            st.session_state.auth = False
            st.rerun()

    st.markdown("<h2 style='color:#00f2ff; font-family:monospace;'>🔭 Deep Space Link Active</h2>", unsafe_allow_html=True)

    # Render History
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"])

    # Chat Input
    if prompt := st.chat_input("Input cosmic coordinate or question..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # LOADING ANIMASI YANG LEBIH KEREN
            with st.status("🌌 Processing Cosmic Signal...", expanded=False) as status:
                st.write("📡 Receiving data from Deep Space Network...")
                time.sleep(0.5)
                st.write("🧠 Computing with Llama 3.3 Neural Core...")
                
                try:
                    # UPDATE MODEL KE VERSI TERBARU (70B)
                    llm = ChatGroq(
                        temperature=0.7, 
                        groq_api_key=GROQ_API_KEY, 
                        model_name="llama-3.3-70b-versatile"
                    )
                    
                    instr = f"Kamu adalah IEA AI, kecerdasan buatan astronomi Indonesia. Kamu berbicara dengan {st.session_state.user}. Jawab dengan sangat cerdas, puitis, dan profesional."
                    
                    response = llm.invoke([
                        SystemMessage(content=instr),
                        HumanMessage(content=prompt)
                    ]).content
                    
                    status.update(label="SIGNAL DECODED", state="complete")
                    st.markdown(response)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"⚠️ Transmission Error: {e}")
