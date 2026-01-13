import streamlit as st
import requests
import time

# --- INITIAL SETUP ---
st.set_page_config(
    page_title="IEA",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- PENGAMAN IMPORT ---
try:
    from langchain_groq import ChatGroq
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
except ImportError:
    st.error(" Library missing! Pastikan requirements.txt berisi: streamlit, langchain-groq, requests")

# --- CSS: CYBERPUNK DARK MODE UI ---
st.markdown("""
    <style>
    /* Global Theme */
    .stApp {
        background: radial-gradient(circle at 20% 30%, #10002b 0%, #050110 100%);
        color: #e0e0e0;
    }

    /* Typography Logo */
    .nebula-header {
        font-family: 'Orbitron', sans-serif;
        font-size: clamp(2rem, 8vw, 4rem);
        font-weight: 900;
        text-align: center;
        background: linear-gradient(90deg, #00f2ff, #bc13fe, #00f2ff);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradient-flow 4s linear infinite;
        margin-bottom: 0px;
    }

    @keyframes gradient-flow {
        0% { background-position: 0% center; }
        100% { background-position: 200% center; }
    }

    /* Glassmorphism Input & Panels */
    div[data-testid="stForm"], .glass-card {
        background: rgba(255, 255, 255, 0.02) !important;
        backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(0, 242, 255, 0.1) !important;
        border-radius: 20px !important;
        padding: 25px !important;
    }

    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #bc13fe; border-radius: 10px; }

    /* Chat Styling */
    .stChatMessage {
        background: rgba(188, 19, 254, 0.05) !important;
        border-radius: 15px !important;
        border: 1px solid rgba(188, 19, 254, 0.1) !important;
        margin-bottom: 10px !important;
    }
    
    /* Responsive Fixes */
    @media (max-width: 640px) {
        .stChatMessage { padding: 10px !important; }
        .nebula-header { font-size: 2.5rem; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIG & API ---
FIREBASE_URL = "https://iea-pendaftaran-default-rtdb.asia-southeast1.firebasedatabase.app"
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

# --- FUNCTION: DB CHECK ---
def is_member(name):
    name = name.strip().lower()
    try:
        for grup in ["iea_grup_1", "iea_grup_2"]:
            data = requests.get(f"{FIREBASE_URL}/{grup}.json", timeout=5).json()
            if data and any(val.get('n', '').lower() == name for val in data.values()):
                return True
        return False
    except: return False

# --- STATE SESSION (MEMORY) ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "chat_history" not in st.session_state: st.session_state.chat_history = []

# --- LOGIN SCREEN ---
if not st.session_state.authenticated:
    st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='nebula-header'>COSMOS AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#00f2ff; letter-spacing:3px;'>INTEGRATED EDUCATION ASTRONOMY</p>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.container():
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            name_input = st.text_input("IDENTIFICATION REQUIRED", placeholder="Type your name here...")
            if st.button("INITIATE UPLINK"):
                if name_input:
                    with st.status("Verifying Credentials...", expanded=True) as status:
                        if is_member(name_input):
                            st.session_state.authenticated = True
                            st.session_state.user = name_input.upper()
                            status.update(label="ACCESS GRANTED", state="complete")
                            st.rerun()
                        else:
                            st.error("ACCESS DENIED: Credentials not found in IEA Database.")
            st.markdown("</div>", unsafe_allow_html=True)

# --- CHAT INTERFACE ---
else:
    # Sidebar for History Management
    with st.sidebar:
        st.markdown(f"## 👩‍🚀 {st.session_state.user}")
        st.info("System: Llama 3.3 70B Active")
        if st.button(" Clear Chat Memory"):
            st.session_state.chat_history = []
            st.rerun()
        if st.button(" Emergency Logout"):
            st.session_state.authenticated = False
            st.rerun()

    st.markdown(f"<h3 style='color:#bc13fe;'>SATELLITE LINK: {st.session_state.user}</h3>", unsafe_allow_html=True)

    # Display Chat History
    for message in st.session_state.chat_history:
        role = "user" if isinstance(message, HumanMessage) else "assistant"
        with st.chat_message(role):
            st.markdown(message.content)

    # Chat Input
    if prompt := st.chat_input("Ask about the universe..."):
        # Add to history
        st.session_state.chat_history.append(HumanMessage(content=prompt))
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.status("🛸 Scanning Deep Space...", expanded=False) as status:
                try:
                    llm = ChatGroq(
                        groq_api_key=GROQ_API_KEY,
                        model_name="llama-3.3-70b-versatile",
                        temperature=0.8
                    )
                    
                    # Memory Engine: Mengirimkan seluruh riwayat obrolan ke AI
                    messages = [
                        SystemMessage(content=f"Kamu adalah Cosmos AI, asisten astronomi dari IEA. Kamu berbicara dengan {st.session_state.user}. Jawablah dengan gaya yang sangat canggih, inspiratif, dan faktual.")
                    ] + st.session_state.chat_history
                    
                    response = llm.invoke(messages).content
                    
                    status.update(label="DATA RETRIEVED", state="complete")
                    st.markdown(response)
                    st.session_state.chat_history.append(AIMessage(content=response))
                except Exception as e:
                    st.error(f" Connection Lost: {str(e)}")
