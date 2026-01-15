import streamlit as st
import requests
import time
import datetime
import re
from io import BytesIO
from gtts import gTTS
from fpdf import FPDF
from PyPDF2 import PdfReader
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# --- 1. SYSTEM CONFIGURATION ---
st.set_page_config(
    page_title="IEA TERMINAL",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🌌"
)

# --- 2. CSS: HIGH CONTRAST OBSIDIAN THEME ---
st.markdown("""
    <style>
    /* HIDE BLOATWARE */
    #MainMenu, header, footer, [data-testid="stDecoration"] {visibility: hidden; display: none;}
    
    /* GLOBAL FONT & COLOR */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    
    .stApp {
        background-color: #000000; /* Hitam Pekat */
        color: #FFFFFF; /* Tulisan Putih Terang */
        font-family: 'JetBrains Mono', monospace;
    }

    /* TEXT VISIBILITY FIX */
    p, h1, h2, h3, div, span, label {
        color: #FFFFFF !important; /* Paksa semua tulisan jadi putih */
        text-shadow: 0px 0px 1px rgba(0,0,0,0.5); /* Shadow tipis biar makin jelas */
    }

    /* CUSTOM SCROLLBAR */
    ::-webkit-scrollbar {width: 8px; background: #111;}
    ::-webkit-scrollbar-thumb {background: #444; border-radius: 4px;}

    /* TABS (TAB NAVIGASI) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #000;
        padding-bottom: 5px;
        border-bottom: 2px solid #333;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #1a1a1a;
        border: 1px solid #444;
        color: #AAAAAA !important; /* Tulisan tab pasif abu terang */
        border-radius: 5px 5px 0 0;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background-color: #000;
        color: #00FF00 !important; /* Tab aktif hijau neon */
        border: 1px solid #00FF00;
        border-bottom: 1px solid #000;
    }

    /* CHAT BUBBLES (KOTAK CHAT) */
    .stChatMessage {
        background: #0a0a0a !important;
        border: 1px solid #333;
        border-radius: 10px !important;
        margin-bottom: 10px;
        padding: 15px !important;
    }
    /* User Avatar */
    [data-testid="stChatMessageAvatarUser"] {
        background-color: #333 !important; color: #fff !important;
    }
    /* Assistant Avatar */
    [data-testid="stChatMessageAvatarAssistant"] {
        background-color: #000 !important; border: 1px solid #00FF00 !important; color: #00FF00 !important;
    }

    /* INPUT FIELDS (KOTAK KETIK) */
    .stTextInput input, .stTextArea textarea {
        background-color: #111111 !important; /* Abu gelap biar beda sama background */
        color: #FFFFFF !important; /* Tulisan ketikan putih */
        border: 1px solid #555 !important; /* Garis pinggir abu terang */
        border-radius: 5px !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #00FF00 !important; /* Fokus jadi hijau */
        box-shadow: 0 0 10px rgba(0, 255, 0, 0.2) !important;
    }

    /* BUTTONS */
    .stButton button {
        background-color: #222 !important;
        color: #FFFFFF !important;
        border: 1px solid #555 !important;
        border-radius: 5px !important;
        font-weight: bold !important;
        transition: all 0.2s;
    }
    .stButton button:hover {
        background-color: #00FF00 !important;
        color: #000000 !important; /* Hover jadi tulisan hitam background hijau */
        border-color: #00FF00 !important;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #050505;
        border-right: 1px solid #333;
    }
    
    /* FILE UPLOADER */
    [data-testid="stFileUploader"] section {
        background-color: #111;
        border: 1px dashed #666;
    }
    
    /* BOOT LOADER (LAYAR LOADING AWAL) */
    #boot-screen {
        position: fixed; inset: 0; z-index: 9999; background: #000;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        animation: fadeOut 0.5s ease-in-out 3.0s forwards; pointer-events: none;
    }
    .loading-text { font-size: 1.5rem; color: #00FF00 !important; font-weight: bold; letter-spacing: 5px; }
    
    @keyframes fadeOut { to {opacity: 0; visibility: hidden;} }

    /* CODE BLOCKS */
    code {
        color: #a6e22e !important;
        background: #272822 !important;
        border: 1px solid #444;
        padding: 2px 5px;
        font-weight: bold;
    }
    </style>
    
    <div id="boot-screen">
        <div class="loading-text">SYSTEM LOADING...</div>
    </div>
""", unsafe_allow_html=True)

# --- 3. BACKEND FUNCTIONS ---
FIREBASE_URL = "https://iea-pendaftaran-default-rtdb.asia-southeast1.firebasedatabase.app"
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

def verify_user(username):
    username = username.strip().lower()
    grups = ["iea_grup_1", "iea_grup_2"]
    try:
        for g in grups:
            res = requests.get(f"{FIREBASE_URL}/{g}.json", timeout=5).json()
            if res:
                for k, v in res.items():
                    if v.get('n', '').lower() == username:
                        return True, v.get('n').upper()
        return False, None
    except:
        return False, None

def extract_pdf_text(uploaded_file):
    try:
        pdf_reader = PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        return str(e)

def generate_pdf_report(history, user):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=10)
    pdf.cell(0, 10, txt=f"LOG REPORT - {user}", ln=1, align='C')
    pdf.ln(10)
    for msg in history:
        clean_text = msg['content'].encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 5, txt=f"[{msg['role'].upper()}]: {clean_text}")
        pdf.ln(2)
    return pdf.output(dest='S').encode('latin-1')

def generate_audio(text):
    try:
        clean = re.sub(r'[*_`#]', '', text)[:300]
        tts = gTTS(text=clean, lang='id', slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp
    except:
        return None

# --- 4. SESSION STATE ---
if "auth" not in st.session_state: st.session_state.auth = False
if "username" not in st.session_state: st.session_state.username = "GUEST"
if "messages" not in st.session_state: st.session_state.messages = []
if "doc_context" not in st.session_state: st.session_state.doc_context = ""
if "last_graph" not in st.session_state: st.session_state.last_graph = None

# --- 5. AUTH SCREEN ---
if not st.session_state.auth:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="border:2px solid #333; background:#111; padding:40px; text-align:center; border-radius:10px;">
            <h2 style="color:#FFF !important; letter-spacing:3px;">LOGIN TERMINAL</h2>
            <p style="color:#AAA !important;">MASUKKAN NAMA SESUAI DATA IEA</p>
        </div>
        """, unsafe_allow_html=True)
        
        input_user = st.text_input("IDENTITAS", label_visibility="collapsed", placeholder="KETIK NAMA LENGKAP...")
        
        if st.button("MASUK SISTEM", use_container_width=True):
            if input_user:
                with st.spinner("MEMERIKSA DATABASE..."):
                    time.sleep(1)
                    valid, name = verify_user(input_user)
                    if valid:
                        st.session_state.auth = True
                        st.session_state.username = name
                        st.session_state.messages.append({"role": "assistant", "content": f"AKSES DITERIMA. SELAMAT DATANG, {name}."})
                        st.rerun()
                    else:
                        st.error("DATA TIDAK DITEMUKAN!")
            else:
                st.warning("HARAP ISI NAMA.")

# --- 6. MAIN INTERFACE ---
else:
    # SIDEBAR
    with st.sidebar:
        st.markdown(f"### OPERATOR: {st.session_state.username}")
        st.success("STATUS: ONLINE")
        st.markdown("---")
        
        # UPLOAD PDF
        uploaded_file = st.file_uploader("UPLOAD DOKUMEN (PDF)", type=['pdf'])
        if uploaded_file:
            st.session_state.doc_context = extract_pdf_text(uploaded_file)
            st.success("DATA TERBACA!")
            
        st.markdown("---")
        temp_val = st.slider("KREATIVITAS AI", 0.0, 1.0, 0.5)
        
        st.markdown("---")
        if st.button("UNDUH LAPORAN (PDF)"):
            pdf_data = generate_pdf_report(st.session_state.messages, st.session_state.username)
            st.download_button("DOWNLOAD", pdf_data, "log.pdf", "application/pdf")
            
        if st.button("KELUAR / LOGOUT"):
            st.session_state.auth = False
            st.session_state.messages = []
            st.rerun()

    # TABS
    tab1, tab2 = st.tabs(["TERMINAL CHAT", "DIAGRAM VISUAL"])

    # CHAT TAB
    with tab1:
        # History
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Input
        if prompt := st.chat_input("TULIS PERINTAH..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                resp_box = st.empty()
                full_res = ""
                
                # Context
                doc_info = f"DATA DOKUMEN: {st.session_state.doc_context[:4000]}" if st.session_state.doc_context else ""
                
                sys = f"""
                Kamu adalah AI IEA. User: {st.session_state.username}.
                Bahasa: Indonesia Formal.
                Instruksi:
                1. JANGAN PAKAI EMOJI SAMA SEKALI.
                2. Jawab to-the-point dan ilmiah.
                3. Jika perlu diagram, buat kode GRAPHVIZ dengan format: ```graphviz ... ```.
                4. {doc_info}
                """
                
                msgs = [SystemMessage(content=sys)]
                for m in st.session_state.messages[-6:]:
                    if m["role"]=="user": msgs.append(HumanMessage(content=m["content"]))
                    else: msgs.append(AIMessage(content=m["content"]))
                
                try:
                    llm = ChatGroq(temperature=temp_val, groq_api_key=GROQ_API_KEY, model_name="llama-3.3-70b-versatile", streaming=True)
                    chunks = llm.stream(msgs)
                    
                    for chunk in chunks:
                        if chunk.content:
                            full_res += chunk.content
                            resp_box.markdown(full_res + "█")
                    
                    resp_box.markdown(full_res)
                    st.session_state.messages.append({"role": "assistant", "content": full_res})
                    
                    # Cek Diagram
                    if "```graphviz" in full_res:
                        try:
                            code = full_res.split("```graphviz")[1].split("```")[0].strip()
                            st.session_state.last_graph = code
                            st.info("DIAGRAM DIBUAT -> CEK TAB SEBELAH")
                        except: pass
                    
                    # Audio
                    aud = generate_audio(full_res)
                    if aud: st.audio(aud, format='audio/mp3')
                        
                except Exception as e:
                    st.error(f"ERROR: {str(e)}")

    # VISUAL TAB
    with tab2:
        st.markdown("### LAYAR DIAGRAM")
        if st.session_state.last_graph:
            try:
                st.graphviz_chart(st.session_state.last_graph)
            except:
                st.warning("GAGAL RENDER GAMBAR")
        else:
            st.info("BELUM ADA DATA VISUAL. MINTA AI UNTUK MEMBUAT STRUKTUR/ALUR.")
