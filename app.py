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

# --- CSS: NEON PURPLE BLUR THEME + LOADING + TYPEWRITER --- 
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

    /* GLOBAL BACKGROUND (deep navy with neon purple glow + blur) */
    .stApp {
        background: radial-gradient(circle at 10% 10%, #0b0f1a 0%, #070818 25%, #04020b 60%, #000000 100%);
        color: #F2F7FF;
        font-family: 'Inter', -apple-system, sans-serif;
        min-height: 100vh;
        overflow-x: hidden;
    }

    /* ambient neon blur layers */
    .ambient {
        position: fixed;
        width: 80vmax;
        height: 80vmax;
        left: -10vmax;
        top: -20vmax;
        filter: blur(80px) saturate(140%);
        opacity: 0.16;
        pointer-events: none;
        z-index: 0;
        background: radial-gradient(circle at 30% 30%, rgba(124, 58, 237, 0.9), transparent 25%),
                    radial-gradient(circle at 80% 80%, rgba(88, 28, 135, 0.8), transparent 25%);
    }
    .ambient2 {
        position: fixed;
        width: 60vmax;
        height: 60vmax;
        right: -5vmax;
        bottom: -10vmax;
        filter: blur(60px) saturate(130%);
        opacity: 0.12;
        pointer-events: none;
        z-index: 0;
        background: radial-gradient(circle at 20% 20%, rgba(72, 16, 144, 0.8), transparent 30%),
                    radial-gradient(circle at 70% 70%, rgba(148, 50, 255, 0.6), transparent 30%);
    }

    /* TOP STATUS (small text) */
    .top-status {
        position: absolute;
        left: 14px;
        top: 8px;
        color: rgba(242,247,255,0.75);
        font-size: 0.8rem;
        font-family: monospace;
        letter-spacing: 0.4px;
        z-index: 5;
    }

    /* LOGIN CARD (glass + heavy blur) */
    .login-card {
        margin: 48px auto 24px;
        max-width: 720px;
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.008));
        border: 1px solid rgba(180,150,255,0.06);
        border-radius: 18px;
        padding: 36px;
        text-align: center;
        box-shadow: 0 30px 120px rgba(0,0,0,0.7), inset 0 1px 0 rgba(255,255,255,0.02);
        backdrop-filter: blur(8px) saturate(120%);
        position: relative;
        z-index: 3;
    }

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

    .hero-title {
        font-size: clamp(2rem, 6vw, 3.6rem);
        font-weight: 900;
        margin: 6px 0 6px;
        letter-spacing: -2px;
        background: linear-gradient(90deg, #F8F9FF 30%, #C9B8FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .system-status {
        color: rgba(180, 180, 255, 0.98);
        font-family: monospace;
        letter-spacing: 6px;
        font-size: 0.78rem;
        margin-bottom: 22px;
    }

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

    /* neon blur glow for CTA */
    .get-link {
        display:inline-block;
        margin-top: 10px;
        padding: 10px 16px;
        border-radius: 10px;
        background: linear-gradient(90deg, rgba(124,58,237,0.12), rgba(99,102,241,0.06));
        border: 1px solid rgba(148,50,255,0.12);
        color: rgba(250,250,255,0.95);
        font-weight:600;
        cursor:pointer;
        box-shadow: 0 8px 30px rgba(124,58,237,0.12);
    }

    /* CHAT BUBBLES (slightly blurred and neon outline) */
    .bubble {
        padding: 15px 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        max-width: 85%;
        line-height: 1.6;
        box-shadow: 0 10px 40px rgba(2,6,23,0.6);
        backdrop-filter: blur(3px);
    }
    .user-bubble {
        background: rgba(255,255,255,0.04);
        align-self: flex-end;
        margin-left: auto;
        border: 1px solid rgba(255,255,255,0.06);
    }
    .ai-bubble {
        background: linear-gradient(90deg, rgba(124,58,237,0.06), rgba(255,255,255,0.01));
        align-self: flex-start;
        border: 1px solid rgba(148,50,255,0.08);
        box-shadow: 0 10px 40px rgba(99,102,241,0.08);
    }

    /* INPUT STYLING */
    .stTextInput > div > div > input,
    .stTextArea textarea {
        background-color: rgba(5,8,12,0.8) !important;
        border: 1px solid rgba(255,255,255,0.03) !important;
        color: #EAF9FF !important;
        padding: 14px !important;
        border-radius: 12px !important;
        backdrop-filter: blur(3px);
    }
    
    .stButton > button {
        width: 100% !important;
        background: linear-gradient(90deg,#b28aff,#6e3bff) !important;
        color: white !important;
        font-weight: 900 !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px !important;
        transition: 0.25s;
        box-shadow: 0 10px 30px rgba(124,58,237,0.15);
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 14px 40px rgba(124,58,237,0.22);
    }

    /* LOADING OVERLAY (full-screen, shown once) */
    .boot-overlay {
        position: fixed;
        inset: 0;
        display:flex;
        justify-content:center;
        align-items:center;
        z-index:9999;
        background: linear-gradient(180deg, rgba(2,0,10,0.65), rgba(6,2,20,0.85));
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
        backdrop-filter: blur(6px) saturate(120%);
    }
    .boot-title {
        font-size: 1.4rem;
        font-weight:800;
        background:linear-gradient(90deg,#e6d5ff,#ffffff);
        -webkit-background-clip:text;
        -webkit-text-fill-color:transparent;
        margin-bottom:8px;
    }
    .boot-sub {color: rgba(180,170,255,0.95); font-family:monospace; letter-spacing:4px; margin-bottom:12px;}
    .boot-bar {
        height:4px;
        width:100%;
        background: linear-gradient(90deg, transparent, rgba(148,50,255,0.9), transparent);
        background-size:200% 100%;
        animation:boot-scan 1.6s linear infinite;
        border-radius:6px;
        margin-top:6px;
    }
    @keyframes boot-scan {
        0%{background-position:200% 0}
        100%{background-position:-200% 0}
    }

    /* typing cursor style (for typewriter placeholder) */
    .typewriter {
        font-family: Inter, -apple-system, sans-serif;
        color: #eaf6ff;
        border-left: 2px solid rgba(255,255,255,0.6);
        padding-left: 6px;
        animation: blink 1s steps(2, start) infinite;
    }
    @keyframes blink {
        50% { border-color: transparent; }
    }

    /* responsive tweaks */
    @media (max-width:640px) {
        .login-card{padding:22px;border-radius:14px}
        .hero-title{font-size:1.6rem}
        .link-box{padding:12px}
    }
    </style>
""", unsafe_allow_html=True)

# ambient blurred neon layers
st.markdown('<div class="ambient"></div><div class="ambient2"></div>', unsafe_allow_html=True)

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

# --- helper: nicer ID verification loading (UX only) ---
def verify_identity_with_fanciness(user_id):
    # keep original logic but add UX delays (no logic change)
    with st.spinner("Decrypting Identity..."):
        time.sleep(1.1)  # short cinematic pause
        ok = check_identity(user_id)
        time.sleep(0.8)  # moment to feel the scan
        return ok

# --- helper: typewriter effect (display inside assistant block, then append full) ---
def typewriter_streaming(response_text, container, bubble_class="ai-bubble", speed=0.015, chunk=24):
    """
    container: a streamlit element (e.g., st.empty()) inside which we render incremental content.
    We'll render chunks of text to give the typing feel, then return when done.
    """
    displayed = ""
    # use chunked updates (faster than per-char for long text)
    for i in range(0, len(response_text), chunk):
        piece = response_text[i:i+chunk]
        displayed += piece
        # render as bubble (so it visually matches chat bubbles)
        container.markdown(f"<div class='bubble {bubble_class} typewriter'>{html.escape(displayed).replace('\\n','<br>')}</div>", unsafe_allow_html=True)
        time.sleep(speed)
    # leave final content rendered
    return

# --- UI: LOGIN INTERFACE ---
if not st.session_state.auth:
    st.markdown("<div style='height: 12vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='hero-title'>IEA ALPHA</h1>", unsafe_allow_html=True)
    st.markdown("<p class='system-status'>IDENTITY VERIFICATION REQUIRED</p>", unsafe_allow_html=True)
    
    _, col_mid, _ = st.columns([1, 2, 1])
    with col_mid:
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        user_id = st.text_input("SCAN ID CARD (ENTER NAME)", placeholder="Masukkan nama terdaftar...")
        
        if st.button("AUTHORIZE ACCESS"):
            if user_id:
                # use the nicer verification helper (UX only)
                verified = verify_identity_with_fanciness(user_id)
                if verified:
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
        <div style='display:flex; justify-content:space-between; align-items:center; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.02); position: relative; z-index: 3;'>
            <div style='color:#bfa7ff; font-weight:900;'>OPERATOR: {st.session_state.user}</div>
            <div style='color:rgba(255,255,255,0.45); font-size:0.7rem; font-family:monospace;'>MODEL: LLAMA-3.3-70B</div>
        </div>
    """, unsafe_allow_html=True)

    # Render History (static snapshot)
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
        # create a chat_message assistant block to show loader and typewriter in context
        with st.chat_message("assistant"):
            st.markdown("<div style='height:6px;background:linear-gradient(90deg,transparent,rgba(148,50,255,0.9),transparent);background-size:200% 100%;animation:scan 1.6s linear infinite;border-radius:4px;margin-bottom:8px'></div>", unsafe_allow_html=True)
            try:
                from langchain_groq import ChatGroq
                from langchain_core.messages import SystemMessage, HumanMessage
                
                llm = ChatGroq(temperature=0.7, groq_api_key=GROQ_API_KEY, model_name="llama-3.3-70b-versatile")
                
                # Membangun konteks percakapan (TIDAK DIUBAH)
                messages = [SystemMessage(content=f"Kamu adalah AI IEA. Kamu berbicara dengan {st.session_state.user}. Jawab dengan sangat cerdas, puitis, dan profesional dalam Bahasa Indonesia.")]
                
                # Ambil 5 pesan terakhir untuk memori
                for m in st.session_state.chat_history[-6:]:
                    if m["role"] == "user":
                        messages.append(HumanMessage(content=m["content"]))
                    else:
                        messages.append(SystemMessage(content=m["content"]))
                
                # invoke model
                response = llm.invoke(messages).content

                # TYPEWRITER: display streaming into a temp container (inside assistant block)
                placeholder = st.empty()
                typewriter_streaming(response, placeholder, bubble_class="ai-bubble", speed=0.02, chunk=28)

                # after streaming finishes, append final response to history (no duplication)
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
