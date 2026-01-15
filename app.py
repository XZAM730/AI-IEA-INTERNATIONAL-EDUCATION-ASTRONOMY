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

# --- 1. SYSTEM INIT & CONFIG ---
st.set_page_config(
    page_title="IEA OMNI-TERMINAL",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="💠"
)

# --- 2. ADVANCED CSS: OBSIDIAN GLASS THEME ---
st.markdown("""
    <style>
    /* CORE HIDING */
    #MainMenu, header, footer, [data-testid="stDecoration"] {visibility: hidden; display: none;}
    
    /* GLOBAL FONTS & COLORS */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    
    .stApp {
        background-color: #050505;
        color: #e0e0e0;
        font-family: 'JetBrains Mono', monospace;
    }

    /* CUSTOM SCROLLBAR */
    ::-webkit-scrollbar {width: 5px; background: #000;}
    ::-webkit-scrollbar-thumb {background: #333; border-radius: 2px;}

    /* TABS STYLING (PHYSICAL LOOK) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #050505;
        padding: 10px 0;
        border-bottom: 1px solid #333;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: #0f0f0f;
        border: 1px solid #333;
        border-bottom: none;
        color: #666;
        border-radius: 4px 4px 0 0;
        font-family: 'JetBrains Mono', monospace;
        transition: all 0.3s;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1a1a1a;
        color: #00f6ff;
        border-color: #00f6ff;
        border-bottom: 1px solid #1a1a1a; /* Blend with content */
    }

    /* CHAT BUBBLES (MINIMALIST) */
    .stChatMessage {
        background: transparent !important;
        padding: 20px 0 !important;
        border-bottom: 1px solid #111;
    }
    [data-testid="stChatMessageAvatarUser"] {
        background-color: #222 !important; color: #fff !important; border-radius: 0px !important;
    }
    [data-testid="stChatMessageAvatarAssistant"] {
        background-color: #000 !important; border: 1px solid #00f6ff !important; color: #00f6ff !important; border-radius: 0px !important;
    }

    /* INPUT FIELDS */
    .stTextInput input, .stTextArea textarea {
        background: #080808 !important; color: #fff !important; 
        border: 1px solid #333 !important; border-radius: 0px !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #00f6ff !important; box-shadow: 0 0 10px rgba(0,246,255,0.1) !important;
    }

    /* BUTTONS */
    .stButton button {
        background: #111 !important; color: #aaa !important; 
        border: 1px solid #333 !important; border-radius: 0px !important;
        text-transform: uppercase; letter-spacing: 1px; transition: all 0.2s;
    }
    .stButton button:hover {
        background: #00f6ff !important; color: #000 !important; border-color: #00f6ff !important;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #020202;
        border-right: 1px solid #222;
    }
    
    /* BOOT SCREEN ANIMATION */
    #boot-layer {
        position: fixed; inset: 0; z-index: 9999; background: #000;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        animation: systemBoot 0.5s ease-in-out 3.5s forwards; pointer-events: none;
    }
    .boot-text { color: #00f6ff; font-size: 0.8rem; margin-top: 10px; letter-spacing: 3px; }
    .scan-line { width: 200px; height: 2px; background: #333; overflow: hidden; position: relative; }
    .scan-prog { width: 0%; height: 100%; background: #00f6ff; animation: loadBar 3s ease-out forwards; }
    
    @keyframes loadBar { 0%{width:0%} 100%{width:100%} }
    @keyframes systemBoot { to {opacity: 0; visibility: hidden;} }

    /* METRIC CARD IN SIDEBAR */
    .stat-box {
        border: 1px solid #222; padding: 10px; margin-bottom: 5px; background: #080808;
    }
    .stat-label { font-size: 0.65rem; color: #666; text-transform: uppercase; }
    .stat-val { font-size: 0.9rem; color: #00f6ff; font-weight: bold; }

    </style>
    
    <div id="boot-layer">
        <h2 style="color:#fff; font-family:'JetBrains Mono'; letter-spacing:5px; margin-bottom:20px;">IEA SYSTEMS</h2>
        <div class="scan-line"><div class="scan-prog"></div></div>
        <div class="boot-text">INITIALIZING CORE MODULES...</div>
    </div>
""", unsafe_allow_html=True)

# --- 3. BACKEND FUNCTIONS ---
FIREBASE_URL = "https://iea-pendaftaran-default-rtdb.asia-southeast1.firebasedatabase.app"
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

def verify_user(username):
    """Verifikasi User ke Firebase"""
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
    """Membaca teks dari file PDF"""
    try:
        pdf_reader = PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        return str(e)

def generate_pdf_report(history, user):
    """Membuat laporan PDF dari chat"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=10)
    
    # Header
    pdf.cell(0, 10, txt="IEA MISSION LOG REPORT", ln=1, align='C')
    pdf.cell(0, 10, txt=f"OPERATOR: {user} | DATE: {datetime.date.today()}", ln=1, align='C')
    pdf.ln(10)
    
    # Content
    for msg in history:
        role = "SYS" if msg['role'] == "assistant" else "OPR"
        # Sanitize text for basic FPDF (removes emoji/special chars)
        clean_text = msg['content'].encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 5, txt=f"[{role}]: {clean_text}")
        pdf.ln(3)
        
    return pdf.output(dest='S').encode('latin-1')

def generate_audio(text):
    """Text to Speech Engine"""
    try:
        # Batasi karakter agar tidak error/lambat
        clean_text = re.sub(r'[*_`#]', '', text)[:400] 
        tts = gTTS(text=clean_text, lang='id', slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp
    except:
        return None

# --- 4. SESSION MANAGEMENT ---
if "auth" not in st.session_state: st.session_state.auth = False
if "username" not in st.session_state: st.session_state.username = "UNKNOWN"
if "messages" not in st.session_state: st.session_state.messages = []
if "doc_context" not in st.session_state: st.session_state.doc_context = ""
if "last_graph" not in st.session_state: st.session_state.last_graph = None

# --- 5. AUTHENTICATION PAGE ---
if not st.session_state.auth:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="border:1px solid #333; background:#0a0a0a; padding:40px; text-align:center;">
            <h2 style="color:#fff; letter-spacing:4px; margin-bottom:5px;">IEA ACCESS</h2>
            <p style="color:#666; font-size:0.8rem; margin-bottom:30px;">SECURE TERMINAL LOGIN</p>
        </div>
        """, unsafe_allow_html=True)
        
        input_user = st.text_input("IDENTITY TOKEN", label_visibility="collapsed", placeholder="ENTER NAME...")
        
        if st.button("INITIATE UPLINK", use_container_width=True):
            if input_user:
                with st.spinner("AUTHENTICATING BIOMETRICS..."):
                    time.sleep(1.2)
                    valid, name = verify_user(input_user)
                    if valid:
                        st.session_state.auth = True
                        st.session_state.username = name
                        # Welcome Message
                        st.session_state.messages.append({"role": "assistant", "content": f"UPLINK ESTABLISHED. WELCOME, OPERATOR {name}. SYSTEM READY."})
                        st.rerun()
                    else:
                        st.error("ACCESS DENIED: IDENTITY UNKNOWN")
            else:
                st.warning("INPUT REQUIRED")

# --- 6. MAIN TERMINAL INTERFACE ---
else:
    # --- SIDEBAR: CONTROLS & TELEMETRY ---
    with st.sidebar:
        st.markdown(f"### OPR: {st.session_state.username}")
        
        # Telemetry Dashboard
        st.markdown("""
        <div class="stat-box">
            <div class="stat-label">SYSTEM STATUS</div>
            <div class="stat-val" style="color:#00f6ff;">ONLINE</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">AI MODEL</div>
            <div class="stat-val">LLAMA-3 70B</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 1. RAG SYSTEM (PDF UPLOAD)
        st.caption("DATA INGESTION (RAG)")
        uploaded_file = st.file_uploader("UPLOAD DOCUMENT", type=['pdf', 'txt'], label_visibility="collapsed")
        if uploaded_file:
            if uploaded_file.type == "application/pdf":
                st.session_state.doc_context = extract_pdf_text(uploaded_file)
            else:
                st.session_state.doc_context = str(uploaded_file.read(), "utf-8")
            st.success(f"DATA LOADED: {len(st.session_state.doc_context)} BYTES")
        
        st.markdown("---")
        
        # 2. PARAMETERS
        st.caption("NEURAL SETTINGS")
        temp_val = st.slider("CREATIVITY", 0.0, 1.0, 0.4)
        
        # 3. ACTIONS
        st.markdown("---")
        if st.button("GENERATE REPORT (PDF)"):
            pdf_data = generate_pdf_report(st.session_state.messages, st.session_state.username)
            st.download_button("DOWNLOAD FILE", pdf_data, "IEA_LOG.pdf", "application/pdf")
            
        if st.button("TERMINATE SESSION"):
            st.session_state.auth = False
            st.session_state.messages = []
            st.rerun()

    # --- MAIN AREA: TABS ---
    tab_chat, tab_visual = st.tabs(["[ TERMINAL_FEED ]", "[ VISUAL_CORE ]"])

    # --- TAB 1: CHAT ---
    with tab_chat:
        # Container Chat History
        chat_box = st.container()
        
        with chat_box:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    # Tampilkan Audio Player jika ini pesan terakhir AI
                    if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                         # Kita tidak auto-generate audio agar tidak lag, tapi bisa ditambahkan tombol play
                         pass 

        # Input Area
        if prompt := st.chat_input("ENTER COMMAND / INQUIRY..."):
            # 1. User Message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # 2. AI Processing
            with st.chat_message("assistant"):
                resp_box = st.empty()
                full_response = ""
                
                # Context Management (RAG)
                rag_instruction = ""
                if st.session_state.doc_context:
                    rag_instruction = f"REFERENCE DATA (PRIORITY): {st.session_state.doc_context[:5000]}..."

                # System Prompt: Strict & Intelligent
                sys_prompt = f"""
                SYSTEM IDENTITY: IEA OMNI-AI.
                OPERATOR: {st.session_state.username}.
                LANGUAGE: INDONESIAN (Scientific/Formal).
                
                DIRECTIVES:
                1. STRICTLY NO EMOJIS. TEXT ONLY.
                2. FORMAT: Use clear paragraphs, bullet points, or numbered lists.
                3. DIAGRAMS: If explanation is complex, generate GRAPHVIZ DOT code inside ```graphviz ... ``` block.
                4. {rag_instruction}
                """

                messages_payload = [SystemMessage(content=sys_prompt)]
                # Context Window: 8 Pesan Terakhir
                for m in st.session_state.messages[-8:]:
                    if m["role"] == "user": messages_payload.append(HumanMessage(content=m["content"]))
                    else: messages_payload.append(AIMessage(content=m["content"]))

                try:
                    # Init LLM
                    llm = ChatGroq(temperature=temp_val, groq_api_key=GROQ_API_KEY, model_name="llama-3.3-70b-versatile", streaming=True)
                    chunks = llm.stream(messages_payload)
                    
                    # Streaming Output
                    for chunk in chunks:
                        if chunk.content:
                            full_response += chunk.content
                            resp_box.markdown(full_response + "█") # Cursor Effect
                    
                    # Final Render
                    resp_box.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    
                    # Post-Processing: Diagram Detection
                    if "```graphviz" in full_response:
                        # Extract DOT code
                        try:
                            code = full_response.split("```graphviz")[1].split("```")[0].strip()
                            st.session_state.last_graph = code
                            st.toast("VISUAL DATA GENERATED - CHECK 'VISUAL_CORE' TAB", icon="✅")
                        except:
                            pass

                    # Post-Processing: Audio Generation (Auto-Briefing)
                    # Generate audio singkat untuk 200 karakter pertama agar cepat
                    audio_bytes = generate_audio(full_response)
                    if audio_bytes:
                        st.audio(audio_bytes, format='audio/mp3', start_time=0)

                except Exception as e:
                    st.error(f"SYSTEM FAILURE: {str(e)}")

    # --- TAB 2: VISUALIZATION ---
    with tab_visual:
        st.markdown("### DATA VISUALIZATION MODULE")
        if st.session_state.last_graph:
            try:
                st.graphviz_chart(st.session_state.last_graph)
                st.caption(f"GENERATED AT: {datetime.datetime.now().strftime('%H:%M:%S')}")
            except Exception as e:
                st.error("VISUAL RENDERING ERROR")
                st.code(st.session_state.last_graph)
        else:
            st.info("NO VISUAL DATA IN BUFFER. REQUEST A DIAGRAM TO GENERATE.")
            st.markdown("Example: *'Buatkan diagram struktur tata surya'* or *'Gambarkan alur proses fotosintesis'*")
