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

# --- CSS: STEALTH & HIGH-CONTRAST UI ---
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

    /* THEME CORE */
    .stApp {
        background: #000000;
        color: #FFFFFF;
        font-family: 'Inter', -apple-system, sans-serif;
    }

    /* LOGIN CARD STYLE */
    .login-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(0, 246, 255, 0.2);
        border-radius: 20px;
        padding: 40px;
        text-align: center;
        box-shadow: 0 0 50px rgba(0, 246, 255, 0.1);
    }

    /* TYPOGRAPHY */
    .hero-title {
        font-size: clamp(2.5rem, 10vw, 5rem);
        font-weight: 900;
        text-align: center;
        background: linear-gradient(180deg, #FFFFFF 30%, #333333 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -3px;
    }

    .system-status {
        color: #00f6ff;
        font-family: monospace;
        letter-spacing: 5px;
        font-size: 0.7rem;
        text-align: center;
        margin-bottom: 30px;
    }

    /* CHAT BUBBLES */
    .bubble {
        padding: 15px 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        max-width: 85%;
        line-height: 1.6;
    }
    .user-bubble {
        background: rgba(255, 255, 255, 0.05);
        align-self: flex-end;
        margin-left: auto;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .ai-bubble {
        background: linear-gradient(90deg, rgba(0, 246, 255, 0.05), transparent);
        align-self: flex-start;
        border: 1px solid rgba(0, 246, 255, 0.1);
    }

    /* INPUT STYLING */
    .stTextInput > div > div > input {
        background-color: #0A0A0A !important;
        border: 1px solid #333 !important;
        color: white !important;
        padding: 15px !important;
    }
    
    .stButton > button {
        width: 100% !important;
        background: #00f6ff !important;
        color: black !important;
        font-weight: 900 !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px !important;
        transition: 0.3s;
    }
    .stButton > button:hover {
        background: #FFFFFF !important;
        transform: scale(1.02);
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
        <div style='display:flex; justify-content:space-between; align-items:center; padding: 10px 0; border-bottom: 1px solid #222;'>
            <div style='color:#00f6ff; font-weight:900;'>OPERATOR: {st.session_state.user}</div>
            <div style='color:#444; font-size:0.7rem; font-family:monospace;'>MODEL: LLAMA-3.3-70B</div>
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
            st.markdown("<div class='loader'></div>", unsafe_allow_html=True)
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
