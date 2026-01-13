import streamlit as st
import requests
import time
import html
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(
    page_title="IEA AI",
    page_icon="🪐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS: STEALTH & HIGH-CONTRAST UI (UPDATED THEME LIKE IMAGE + LOADING) ---
st.markdown("""
    <style>
    /* HIDE STREAMLIT BRANDING */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stDecoration"] {display: none !important;}
    [data-testid="stHeader"] {background: rgba(0,0,0,0);}
    .viewerBadge_container__1QS1Z {display: none !important;}
    [data-testid="stDeployButton"] {display: none !important;}

    /* GLOBAL BACKGROUND (deep navy gradient) */
    .stApp {
        background: radial-gradient(circle at 10% 10%, #0b2a3a 0%, #071827 25%, #020617 60%, #000000 100%);
        color: #E6F7FF;
        font-family: 'Inter', -apple-system, sans-serif;
        min-height: 100vh;
    }

    /* TOP STATUS (small text like in screenshot) */
    .top-status {
        position: absolute;
        left: 14px;
        top: 8px;
        color: rgba(230,247,255,0.65);
        font-size: 0.8rem;
        font-family: monospace;
        letter-spacing: 0.4px;
    }

    /* SKIP text (top-right) */
    .skip-text {
        position: absolute;
        right: 18px;
        top: 10px;
        color: rgba(230,247,255,0.6);
        font-size: 0.85rem;
        cursor: pointer;
    }

    /* LOGIN CARD AREA (centered, glass-like) */
    .login-card {
        margin: 48px auto 24px;
        max-width: 720px;
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        border: 1px solid rgba(255,255,255,0.03);
        border-radius: 18px;
        padding: 34px;
        text-align: center;
        box-shadow: 0 24px 80px rgba(2,6,23,0.7), inset 0 1px 0 rgba(255,255,255,0.02);
        backdrop-filter: blur(6px);
    }

    /* ICON BOX like screenshot */
    .hero-icon {
        width: 84px;
        height: 84px;
        margin: 0 auto 18px;
        border-radius: 18px;
        display:flex;
        align-items:center;
        justify-content:center;
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.03);
    }
    .hero-icon svg, .hero-icon .emoji {
        font-size: 38px;
        color: rgba(255,255,255,0.92);
        opacity: 0.95;
    }

    /* HERO TITLE */
    .hero-title {
        font-size: clamp(2rem, 6vw, 3.6rem);
        font-weight: 900;
        margin: 6px 0 6px;
        letter-spacing: -2px;
        background: linear-gradient(90deg, #FFFFFF 30%, #AAB7C4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* SUBTITLE */
    .system-status {
        color: rgba(0,246,255,0.95);
        font-family: monospace;
        letter-spacing: 6px;
        font-size: 0.78rem;
        margin-bottom: 22px;
    }

    /* LINK BOX (simulating the download box in screenshot) */
    .link-box {
        margin: 18px auto 6px;
        max-width: 560px;
        background: linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.007));
        border: 1px solid rgba(255,255,255,0.03);
        padding: 14px 18px;
        border-radius: 12px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.6);
        color: rgba(230,247,255,0.9);
        font-family: monospace;
        font-size: 0.95rem;
    }
    .link-box .copy {
        float: right;
        background: rgba(255,255,255,0.03);
        padding: 6px 8px;
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.02);
        cursor: pointer;
    }

    /* CTA button subtle */
    .get-link {
        display:inline-block;
        margin-top: 10px;
        padding: 10px 16px;
        border-radius: 10px;
        background: linear-gradient(90deg, rgba(0,246,255,0.08), rgba(124,60,255,0.03));
        border: 1px solid rgba(0,246,255,0.06);
        color: rgba(230,247,255,0.95);
        font-weight:600;
        cursor:pointer;
    }

    /* CHAT BUBBLES */
    .bubble {
        padding: 15px 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        max-width: 85%;
        line-height: 1.6;
        box-shadow: 0 10px 30px rgba(2,6,23,0.6);
    }
    .user-bubble {
        background: rgba(255,255,255,0.04);
        align-self: flex-end;
        margin-left: auto;
        border: 1px solid rgba(255,255,255,0.06);
    }
    .ai-bubble {
        background: linear-gradient(90deg, rgba(0,246,255,0.04), rgba(255,255,255,0.01));
        align-self: flex-start;
        border: 1px solid rgba(0,246,255,0.06);
    }

    /* INPUT STYLING */
    .stTextInput > div > div > input,
    .stTextArea textarea {
        background-color: #07121A !important;
        border: 1px solid rgba(255,255,255,0.03) !important;
        color: #EAF9FF !important;
        padding: 14px !important;
        border-radius: 12px !important;
    }
    
    .stButton > button {
        width: 100% !important;
        background: linear-gradient(90deg,#00f6ff,#bfeaff) !important;
        color: black !important;
        font-weight: 900 !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px !important;
        transition: 0.25s;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 30px rgba(0,246,255,0.08);
    }

    /* LOADING OVERLAY (full-screen, shown once) */
    .boot-overlay {
        position: fixed;
        inset: 0;
        display:flex;
        justify-content:center;
        align-items:center;
        z-index:9999;
        background: linear-gradient(180deg, rgba(0,0,0,0.6), rgba(2,6,23,0.85));
    }
    .boot-card {
        width: 86%;
        max-width: 520px;
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        border-radius: 18px;
        padding: 30px;
        text-align:center;
        border:1px solid rgba(255,255,255,0.03);
        box-shadow: 0 30px 120px rgba(0,0,0,0.8);
    }
    .boot-title {
        font-size: 1.5rem;
        font-weight:800;
        background:linear-gradient(90deg,#00f6ff,#ffffff);
        -webkit-background-clip:text;
        -webkit-text-fill-color:transparent;
        margin-bottom:10px;
    }
    .boot-sub {color: rgba(0,246,255,0.9); font-family:monospace; letter-spacing:4px; margin-bottom:16px;}
    .boot-bar {
        height:4px;
        width:100%;
        background: linear-gradient(90deg, transparent, #00f6ff, transparent);
        background-size:200% 100%;
        animation:boot-scan 1.6s linear infinite;
        border-radius:6px;
        margin-top:6px;
    }
    @keyframes boot-scan {
        0%{background-position:200% 0}
        100%{background-position:-200% 0}
    }

    /* responsive tweaks */
    @media (max-width:640px) {
        .login-card{padding:22px;border-radius:14px}
        .hero-title{font-size:1.6rem}
        .link-box{padding:12px}
    }
    </style>
""", unsafe_allow_html=True)

# --- DATABASE & AUTH LOGIC ---
FIREBASE_URL = "https://iea-pendaftaran-default-rtdb.asia-southeast1.firebasedatabase.app"
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

def check_identity(id_name):
    """Verifikasi ID di database Firebase IEA"""
    id_name = id_name.strip().lower()
    grup_list = ["iea_grup_1", "iea_grup_2"]
    try:
        for grup in grup_list:
            res = requests.get(f"{FIREBASE_URL}/{grup}.json", timeout=10).json()
            if res:
                for key in res:
                    if res[key].get('n', '').lower() == id_name:
                        return True
        return False
    except:
        return False

# --- STATE MANAGEMENT ---
if "auth" not in st.session_state: st.session_state.auth = False
if "chat_history" not in st.session_state: st.session_state.chat_history = []

# --- BOOT LOADING (one-time overlay) ---
if "boot_done" not in st.session_state:
    st.session_state.boot_done = True
    with st.empty():
        st.markdown("""
        <div class="boot-overlay">
            <div class="boot-card">
                <div style="display:flex;justify-content:center;margin-bottom:10px;">
                    <div class="hero-icon"><span class="emoji">🖥️</span></div>
                </div>
                <div class="boot-title">IEA AI</div>
                <div class="boot-sub">INITIALIZING SYSTEM</div>
                <div class="boot-bar"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(2.2)
        st.rerun()

# --- UI: LOGIN INTERFACE ---
if not st.session_state.auth:
    st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='hero-title'>IEA ALPHA</h1>", unsafe_allow_html=True)
    st.markdown("<p class='system-status'>IDENTITY VERIFICATION REQUIRED</p>", unsafe_allow_html=True)
    
    _, col_mid, _ = st.columns([1, 2, 1])
    with col_mid:
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        user_id = st.text_input("SCAN ID CARD (ENTER NAME)", placeholder="Masukkan nama terdaftar...")
        
        if st.button("AUTHORIZE ACCESS"):
            if user_id:
                with st.spinner("Decrypting Identity..."):
                    if check_identity(user_id):
                        st.session_state.auth = True
                        st.session_state.user = user_id.upper()
                        st.rerun()
                    else:
                        st.error("ACCESS DENIED: Identity not found in IEA Database.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- UI: MAIN CHAT TERMINAL ---
else:
    # Header minimalis
    st.markdown(f"""
        <div style='display:flex; justify-content:space-between; align-items:center; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.02);'>
            <div style='color:#00f6ff; font-weight:900;'>OPERATOR: {st.session_state.user}</div>
            <div style='color:rgba(255,255,255,0.45); font-size:0.7rem; font-family:monospace;'>MODEL: LLAMA-3.3-70B</div>
        </div>
    """, unsafe_allow_html=True)

    # Render History
    chat_container = st.container()
    with chat_container:
        for chat in st.session_state.chat_history:
            role_class = "user-bubble" if chat["role"] == "user" else "ai-bubble"
            st.markdown(f"<div class='bubble {role_class}'>{chat['content']}</div>", unsafe_allow_html=True)

    # Input Form (Tanpa Fitur Gambar)
    with st.form("chat_input", clear_on_submit=True):
        prompt = st.text_area("Transmit Message", placeholder="Tulis pesan astronomi kamu di sini...", height=100)
        submit = st.form_submit_button("SEND SIGNAL")

        if submit and prompt.strip():
            # Tambah pesan user
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.rerun()

    # Logika AI (Lari setelah rerun jika pesan terakhir adalah user)
    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
        with st.chat_message("assistant"):
            st.markdown("<div style='height:6px;background:linear-gradient(90deg,transparent,#00f6ff,transparent);background-size:200% 100%;animation:scan 1.6s linear infinite;border-radius:4px;margin-bottom:8px'></div>", unsafe_allow_html=True)
            try:
                from langchain_groq import ChatGroq
                from langchain_core.messages import SystemMessage, HumanMessage
                
                llm = ChatGroq(temperature=0.7, groq_api_key=GROQ_API_KEY, model_name="llama-3.3-70b-versatile")
                
                # Membangun konteks percakapan
                messages = [SystemMessage(content=f"Kamu adalah AI IEA. Kamu berbicara dengan {st.session_state.user}. Jawab dengan sangat cerdas, puitis, dan profesional dalam Bahasa Indonesia.")]
                
                # Ambil 5 pesan terakhir untuk memori
                for m in st.session_state.chat_history[-6:]:
                    if m["role"] == "user":
                        messages.append(HumanMessage(content=m["content"]))
                    else:
                        messages.append(SystemMessage(content=m["content"]))
                
                response = llm.invoke(messages).content
                
                # Efek mengetik sederhana
                st.session_state.chat_history.append({"role": "ai", "content": response})
                st.rerun()

            except Exception as e:
                st.error(f"Signal lost: {e}")

    # Sidebar Logout
    with st.sidebar:
        st.markdown("### SYSTEM")
        if st.button("LOGOUT / LOCK"):
            st.session_state.auth = False
            st.session_state.chat_history = []
            st.rerun()
