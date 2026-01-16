import streamlit as st
import re
import time
import base64
from io import BytesIO
from gtts import gTTS
from fpdf import FPDF
from PyPDF2 import PdfReader
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="IEA INTELLIGENCE",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. ADVANCED CSS (DARK NEON THEME)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=JetBrains+Mono:wght@400;700&family=Orbitron:wght@700&display=swap');

    /* --- GLOBAL THEME --- */
    .stApp {
        background-color: #050505;
        color: #E0E0E0;
        font-family: 'Inter', sans-serif;
    }

    /* --- LOADING ANIMATION --- */
    @keyframes fadeOut { to { opacity: 0; visibility: hidden; } }
    #boot-screen {
        position: fixed; inset: 0; z-index: 999999;
        background: #000; display: flex; align-items: center; justify-content: center;
        flex-direction: column; animation: fadeOut 2.5s forwards 1s;
    }
    .boot-logo {
        font-family: 'Orbitron', sans-serif; font-size: 2rem;
        background: linear-gradient(90deg, #00C6FF, #0072FF);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(0, 198, 255, 0.5);
    }

    /* --- HEADER GRADIENT --- */
    .gradient-text {
        font-family: 'Orbitron', sans-serif;
        background: linear-gradient(to right, #00F6FF, #0072FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        font-weight: 800;
        letter-spacing: 2px;
        margin-bottom: 10px;
    }

    /* --- CHAT BUBBLES --- */
    /* User Bubble (Dark Grey) */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: transparent;
    }
    /* AI Bubble (Transparent/Black) */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #0A0A0A;
        border: 1px solid #1A1A1A;
        border-radius: 12px;
    }

    /* --- AVATARS --- */
    [data-testid="stChatMessageAvatarUser"] {
        background-color: #222 !important; color: #FFF !important;
    }
    [data-testid="stChatMessageAvatarAssistant"] {
        background: linear-gradient(135deg, #00F6FF, #0072FF) !important;
        color: #000 !important;
        box-shadow: 0 0 15px rgba(0, 246, 255, 0.3);
    }

    /* --- INPUT FIELD --- */
    .stTextInput input, .stChatInput textarea {
        background-color: #111 !important;
        color: #FFF !important;
        border: 1px solid #333 !important;
        border-radius: 12px !important;
    }
    .stChatInput textarea:focus {
        border-color: #00F6FF !important;
        box-shadow: 0 0 10px rgba(0, 246, 255, 0.1) !important;
    }

    /* --- SUGGESTION CHIPS (TOMBOL CEPAT) --- */
    .suggestion-btn {
        border: 1px solid #333;
        background: #111;
        color: #AAA;
        border-radius: 20px;
        padding: 5px 15px;
        font-size: 0.8rem;
        cursor: pointer;
        transition: 0.3s;
        margin: 5px;
        display: inline-block;
    }
    .suggestion-btn:hover {
        border-color: #00F6FF;
        color: #00F6FF;
    }

    /* --- HIDE BLOAT --- */
    #MainMenu, footer, header { visibility: hidden; }
    
    /* --- AUDIO PLAYER STYLE --- */
    audio { width: 100%; height: 30px; filter: invert(1); opacity: 0.7; }
    </style>

    <div id="boot-screen">
        <div class="boot-logo">IEA INTELLIGENCE</div>
        <div style="color:#555; margin-top:10px; font-family:'JetBrains Mono'">SYSTEM ONLINE</div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 3. BACKEND LOGIC
# ==========================================

@st.cache_data(show_spinner=False)
def process_pdf(file):
    try:
        pdf = PdfReader(file)
        return "".join([p.extract_text() for p in pdf.pages])
    except: return ""

def generate_voice(text):
    try:
        clean = re.sub(r'[*_`#]', '', text)
        clean = re.sub(r'```.*?```', 'Visual ditampilkan.', clean, flags=re.DOTALL)
        if len(clean) > 500: clean = clean[:500]
        tts = gTTS(text=clean, lang='id', slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp
    except: return None

# ==========================================
# 4. SESSION STATE
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [] # Mulai kosong agar bersih
if "doc_context" not in st.session_state:
    st.session_state.doc_context = ""

# ==========================================
# 5. SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("### 🎛️ CONTROL PANEL")
    
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key:
        api_key = st.text_input("🔑 API Key", type="password")
        if not api_key: st.stop()
        
    st.divider()
    
    uploaded_file = st.file_uploader("📂 Upload PDF Riset", type=["pdf"])
    if uploaded_file:
        with st.spinner("Processing..."):
            st.session_state.doc_context = process_pdf(uploaded_file)
            st.success("Data Terbaca")
            
    if st.session_state.doc_context:
        if st.button("🗑️ Hapus Memori"):
            st.session_state.doc_context = ""
            st.rerun()
            
    st.markdown("---")
    if st.button("🔄 Reset Percakapan"):
        st.session_state.messages = []
        st.rerun()

# ==========================================
# 6. MAIN UI
# ==========================================

# 6.1 HEADER DENGAN GRADIENT
st.markdown("<h1 class='gradient-text'>IEA INTELLIGENCE HUB</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#666; font-size:0.9rem; margin-top:-15px;'>Advanced Neural Interface V.5.0</p>", unsafe_allow_html=True)
st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

# 6.2 WELCOME SCREEN & SUGGESTION CHIPS (Jika Chat Masih Kosong)
if not st.session_state.messages:
    st.markdown("""
    <div style="text-align: center; padding: 20px; border: 1px dashed #333; border-radius: 10px; margin-bottom: 20px; background: #0A0A0A;">
        <h3 style="color: #EEE;">Selamat Datang, Peneliti.</h3>
        <p style="color: #888;">Saya siap membantu analisis data, pembuatan diagram, atau diskusi ilmiah.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tombol Cepat (Suggestion Chips)
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("📊 Buat Diagram"):
        st.session_state.messages.append({"role": "user", "content": "Buatkan diagram alur struktur organisasi penelitian."})
        st.rerun()
    if col2.button("📝 Ringkas PDF"):
        if st.session_state.doc_context:
            st.session_state.messages.append({"role": "user", "content": "Ringkas dokumen PDF yang sudah diupload."})
        else:
            st.toast("Upload PDF dulu di sidebar!", icon="⚠️")
        st.rerun()
    if col3.button("🌌 Teori NFT"):
        st.session_state.messages.append({"role": "user", "content": "Jelaskan Node-Field Theory secara ilmiah."})
        st.rerun()
    if col4.button("🧪 Analisis Data"):
        st.session_state.messages.append({"role": "user", "content": "Bagaimana cara menganalisis data voxel?"})
        st.rerun()

# 6.3 RENDER HISTORY
for msg in st.session_state.messages:
    icon = "👤" if msg["role"] == "user" else "💠"
    with st.chat_message(msg["role"], avatar=icon):
        st.markdown(msg["content"])
        if "```graphviz" in msg["content"]:
            try:
                code = re.search(r'```graphviz\n(.*?)\n```', msg["content"], re.DOTALL).group(1)
                st.graphviz_chart(code)
            except: pass

# 6.4 INPUT & LOGIC
if prompt := st.chat_input("Perintahkan sistem..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="💠"):
        resp_placeholder = st.empty()
        full_res = ""
        
        # Context
        ctx = ""
        if st.session_state.doc_context:
            ctx = f"\n[SUMBER PDF]:\n{st.session_state.doc_context[:8000]}...\n"

        # Prompt Engineering
        sys = f"""
        Anda adalah IEA Intelligence. 
        Peran: Asisten Riset Ilmiah (Professional & Concise).
        Bahasa: Indonesia Formal.
        
        INSTRUKSI:
        1. Jawab terstruktur (Poin-poin).
        2. Untuk Diagram/Alur -> Gunakan Graphviz:
           ```graphviz
           digraph G {{
             rankdir=LR; node [style=filled, fillcolor="#0A0A0A", fontcolor="#00F6FF", color="#00F6FF", shape=box];
             edge [color="#555"];
             "A" -> "B";
           }}
           ```
        3. Gunakan data PDF jika ada.
        {ctx}
        """

        msgs = [SystemMessage(content=sys)]
        for m in st.session_state.messages[-8:]:
            if m["role"]=="user": msgs.append(HumanMessage(content=m["content"]))
            else: msgs.append(AIMessage(content=m["content"]))

        try:
            llm = ChatGroq(temperature=0.6, groq_api_key=api_key, model_name="llama-3.3-70b-versatile", streaming=True)
            for chunk in llm.stream(msgs):
                if chunk.content:
                    full_res += chunk.content
                    resp_placeholder.markdown(full_res + "▌")
            
            resp_placeholder.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            
            # Auto Graphviz
            if "```graphviz" in full_res:
                try:
                    code = re.search(r'```graphviz\n(.*?)\n```', full_res, re.DOTALL).group(1)
                    st.graphviz_chart(code)
                except: pass
            
            # Auto Audio (Stylized)
            sound = generate_voice(full_res)
            if sound:
                st.audio(sound, format="audio/mp3")

        except Exception as e:
            st.error(f"System Error: {e}")
