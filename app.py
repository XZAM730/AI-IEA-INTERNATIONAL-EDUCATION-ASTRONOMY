import streamlit as st
import requests
import time
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="IEA ALPHA TERMINAL", layout="wide", initial_sidebar_state="collapsed")

# --- CSS: STEALTH & GADGET COMFORT ---
st.markdown("""
    <style>
    /* HIDE STREAMLIT BRANDING */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .viewerBadge_container__1QS1Z {display: none !important;}
    
    /* THEME DARK ALPHA */
    .stApp { background: #000000; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    
    /* HERO TEXT */
    .hero-title {
        font-size: clamp(2.5rem, 10vw, 5rem);
        font-weight: 900;
        text-align: center;
        background: linear-gradient(180deg, #FFFFFF 0%, #444 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }

    /* RANK BADGE */
    .rank-badge {
        background: linear-gradient(90deg, #00FBFF, #BC13FE);
        color: black;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.7rem;
        text-transform: uppercase;
    }

    /* CHAT BUBBLES */
    .stChatMessage {
        background-color: #0A0A0A !important;
        border: 1px solid #1A1A1A !important;
        border-radius: 15px !important;
        margin-bottom: 10px !important;
    }

    /* FULL WIDTH FOR MOBILE */
    .block-container { padding: 1rem !important; max-width: 900px !important; }

    /* SKYMAP CONTAINER */
    .skymap-container {
        border: 1px solid #333;
        border-radius: 15px;
        overflow: hidden;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIC & DATABASE ---
FIREBASE_URL = "https://iea-pendaftaran-default-rtdb.asia-southeast1.firebasedatabase.app"
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

def get_rank(msg_count):
    if msg_count < 10: return "SPACE CADET", "🛰️"
    elif msg_count < 30: return "GALACTIC VOYAGER", "🚀"
    else: return "COSMIC COMMANDER", "👑"

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

# --- STATE ---
if "auth" not in st.session_state: st.session_state.auth = False
if "msgs" not in st.session_state: st.session_state.msgs = []

# --- UI: LOGIN ---
if not st.session_state.auth:
    st.markdown("<h1 class='hero-title'>ALPHA</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#666; letter-spacing:10px;'>IEA QUANTUM LINK</p>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 2, 1])
    with col:
        u_name = st.text_input("IDENTIFICATION", placeholder="Type your name...")
        if st.button("SYNC TERMINAL"):
            if u_name and check_membership(u_name):
                st.session_state.auth = True
                st.session_state.user = u_name.upper()
                st.rerun()
            else:
                st.error("UNAUTHORIZED ACCESS")

# --- UI: MAIN TERMINAL ---
else:
    # Top Bar (Rank & User)
    rank_title, rank_icon = get_rank(len(st.session_state.msgs))
    st.markdown(f"""
        <div style='display:flex; justify-content:space-between; align-items:center;'>
            <div>
                <span style='color:#00FBFF; font-weight:900;'>{st.session_state.user}</span>
                <span style='color:#444; margin-left:10px;'>{rank_icon} {rank_title}</span>
            </div>
            <div class='rank-badge'>XP: {len(st.session_state.msgs) * 10}</div>
        </div>
        <hr style='border-color:#222;'>
    """, unsafe_allow_html=True)

    # 1. NASA & SKY MAP (Expandable)
    col1, col2 = st.columns(2)
    with col1:
        with st.expander("🔭 LIVE SKY MAP", expanded=False):
            st.markdown("""<div class='skymap-container'><iframe src="https://virtualsky.lco.global/embed/index.html?longitude=106.8&latitude=-6.2&projection=gnomic&constellations=true&constellationlabels=true&showstarlabels=true&live=true" width="100%" height="400" frameborder="0" scrolling="no"></iframe></div>""", unsafe_allow_html=True)
    with col2:
        with st.expander("📅 2026 CALENDAR", expanded=False):
            st.write("• Jan 2026: Mars Oposition\n• Aug 2026: Total Solar Eclipse\n• Nov 2026: Leonid Meteor Shower")

    # 2. CHAT AREA
    for m in st.session_state.msgs:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # 3. INPUT AREA
    if prompt := st.chat_input("Ask Cosmos or Command..."):
        st.session_state.msgs.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                from langchain_groq import ChatGroq
                from langchain_core.messages import SystemMessage, HumanMessage
                
                llm = ChatGroq(temperature=0.7, groq_api_key=GROQ_API_KEY, model_name="llama-3.3-70b-versatile")
                
                sys_inst = f"You are ALPHA, the IEA Quantum AI. User: {st.session_state.user} (Rank: {rank_title}). Speak in Bahasa Indonesia. Be poetic, brilliant, and scientific."
                
                # Fetch Response
                res = llm.invoke([SystemMessage(content=sys_inst), HumanMessage(content=prompt)]).content
                st.markdown(res)
                st.session_state.msgs.append({"role": "assistant", "content": res})
                
                # Voice Feature (Text-to-Speech Injection)
                st.components.v1.html(f"""
                    <script>
                    var msg = new SpeechSynthesisUtterance('{res.replace("'", "")}');
                    msg.lang = 'id-ID';
                    window.speechSynthesis.speak(msg);
                    </script>
                """, height=0)

            except Exception as e:
                st.error(f"Sync Lost: {e}")

    # Sidebar Logout
    with st.sidebar:
        st.title("COMMAND")
        if st.button("TERMINATE SESSION"):
            st.session_state.auth = False
            st.rerun()
