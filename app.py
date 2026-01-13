import streamlit as st
import requests
import time

# --- PENGAMAN IMPORT ---
try:
    from langchain_groq import ChatGroq
    from langchain_core.messages import SystemMessage, HumanMessage
except ImportError:
    st.error(" System Failure: Dependencies missing.")

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="IEA COSMOS",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS: PRO-GRADE UI (Hiding Streamlit Elements) ---
st.markdown("""
    <style>
    /* Menghilangkan Header, Footer, dan Ikon GitHub */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .viewerBadge_container__1QS1Z {display: none !important;}
    [data-testid="stHeader"] {background: rgba(0,0,0,0);}
    
    /* Background & Core Theme */
    .stApp {
        background: #000000;
        color: #FFFFFF;
    }

    /* Typography: High Contrast & Clean */
    .hero-text {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: clamp(2.5rem, 10vw, 5rem);
        font-weight: 900;
        text-align: center;
        color: #00FBFF;
        letter-spacing: -3px;
        margin-top: 5vh;
        line-height: 0.9;
    }

    .status-badge {
        font-family: monospace;
        text-align: center;
        color: #BC13FE;
        font-size: 0.7rem;
        letter-spacing: 4px;
        margin-bottom: 50px;
        text-transform: uppercase;
    }

    /* Container Chat: Optimized for All Screens */
    .block-container {
        padding: 1rem 2rem !important;
        max-width: 1000px !important;
    }

    /* Styling Bubble Chat Tanpa Avatar */
    .stChatMessage {
        background-color: #0A0A0A !important;
        border: 1px solid #1A1A1A !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        margin-bottom: 1rem !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    [data-testid="stChatMessageAvatarUser"], 
    [data-testid="stChatMessageAvatarAssistant"] {
        display: none !important;
    }

    /* Input Styling */
    .stTextInput > div > div > input {
        background-color: #0F0F0F !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
        color: white !important;
        padding: 12px !important;
    }

    /* Button Pro */
    .stButton > button {
        width: 100% !important;
        background: #00FBFF !important;
        color: black !important;
        font-weight: 800 !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 1rem !important;
        transition: 0.4s;
    }
    .stButton > button:hover {
        background: #BC13FE !important;
        color: white !important;
        transform: translateY(-2px);
    }

    /* Loading Animation Bar */
    @keyframes load {
        0% { width: 0%; }
        50% { width: 70%; }
        100% { width: 100%; }
    }
    .loading-bar {
        height: 2px;
        background: linear-gradient(90deg, #00FBFF, #BC13FE);
        animation: load 2s infinite;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIG & DATABASE ---
FIREBASE_URL = "https://iea-pendaftaran-default-rtdb.asia-southeast1.firebasedatabase.app"
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

def check_membership(name):
    name = name.strip().lower()
    grup_list = ["iea_grup_1", "iea_grup_2"]
    try:
        for grup in grup_list:
            data = requests.get(f"{FIREBASE_URL}/{grup}.json", timeout=10).json()
            if data:
                for key in data:
                    if data[key].get('n', '').lower() == name: return True
        return False
    except: return False

# --- STATE ---
if "auth" not in st.session_state: st.session_state.auth = False
if "msgs" not in st.session_state: st.session_state.msgs = []

# --- UI: LOGIN ---
if not st.session_state.auth:
    st.markdown("<h1 class='hero-text'>COSMOS</h1>", unsafe_allow_html=True)
    st.markdown("<p class='status-badge'>Encrypted Network Access</p>", unsafe_allow_html=True)
    
    _, mid, _ = st.columns([1, 3, 1])
    with mid:
        nama = st.text_input("USER IDENTIFICATION", placeholder="Type your name...")
        if st.button("LOGIN TO SYSTEM"):
            if nama:
                with st.status("Verifying...", expanded=False):
                    if check_membership(nama):
                        st.session_state.auth = True
                        st.session_state.user = nama.upper()
                        st.rerun()
                    else:
                        st.error("ACCESS DENIED: Not Registered.")

# --- UI: CHAT ---
else:
    st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; border-bottom:1px solid #222; padding-bottom:10px;'><span style='color:#00FBFF; font-weight:bold;'>USER: {st.session_state.user}</span><span style='color:#444; font-size:10px;'>V3.3-QUANTUM</span></div>", unsafe_allow_html=True)

    for m in st.session_state.msgs:
        with st.chat_message(m["role"]):
            st.markdown(f"<div style='font-size:1.1rem;'>{m['content']}</div>", unsafe_allow_html=True)

    if prompt := st.chat_input("Ask the universe..."):
        st.session_state.msgs.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            st.markdown("<div class='loading-bar'></div>", unsafe_allow_html=True)
            with st.status("Computing...", expanded=False) as status:
                try:
                    # Model Paling Canggih: Llama 3.3 70B
                    llm = ChatGroq(temperature=0.6, groq_api_key=GROQ_API_KEY, model_name="llama-3.3-70b-versatile")
                    
                    sys_prompt = f"You are COSMOS AI, an expert astronomer. You are talking to {st.session_state.user}. Answer in Bahasa Indonesia. Use sophisticated, accurate, and inspiring language. Format your response with clear spacing."
                    
                    res = llm.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=prompt)]).content
                    status.update(label="Complete", state="complete")
                    
                    st.markdown(f"<div style='font-size:1.1rem; line-height:1.7;'>{res}</div>", unsafe_allow_html=True)
                    st.session_state.msgs.append({"role": "assistant", "content": res})
                except Exception as e:
                    st.error(f"Signal Lost: {e}")
