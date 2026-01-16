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
# 1. PAGE CONFIGURATION (SYSTEM LEVEL)
# ==========================================
st.set_page_config(
    page_title="IEA INTELLIGENCE PRO",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. ADVANCED CSS INJECTION (DARK THEME ENGINE)
# ==========================================
st.markdown("""
    <style>
    /* --- IMPORT PREMIUM FONTS --- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=JetBrains+Mono:wght@400;500&display=swap');

    /* --- GLOBAL DARK THEME RESET --- */
    :root {
        --bg-color: #0E0E0E;        /* Hitam Pekat Premium */
        --sidebar-bg: #151515;      /* Abu Sangat Gelap */
        --text-color: #ECECEC;      /* Putih Tulang (Nyaman di mata) */
        --accent-color: #00D2FF;    /* Neon Cyan IEA */
        --input-bg: #1E1E1E;
        --border-color: #333333;
    }

    /* Force Background & Text Color */
    .stApp {
        background-color: var(--bg-color);
        color: var(--text-color);
        font-family: 'Inter', sans-serif;
    }

    /* --- LOADING SCREEN ANIMATION (FUTURISTIC) --- */
    @keyframes fadeOutLoader {
        0% { opacity: 1; z-index: 999999; }
        80% { opacity: 1; }
        100% { opacity: 0; z-index: -1; visibility: hidden; }
    }
    @keyframes scanline {
        0% { transform: translateY(-100%); }
        100% { transform: translateY(100%); }
    }
    
    #boot-screen {
        position: fixed; inset: 0; 
        background-color: #000;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        z-index: 999999;
        animation: fadeOutLoader 3s forwards ease-in-out;
    }
    .boot-text {
        font-family: 'JetBrains Mono', monospace;
        color: var(--accent-color);
        font-size: 1.5rem; letter-spacing: 4px; font-weight: bold;
        text-shadow: 0 0 15px var(--accent-color);
        margin-bottom: 20px;
    }
    .loader-bar {
        width: 200px; height: 2px; background: #333;
        position: relative; overflow: hidden;
    }
    .loader-bar::after {
        content: ''; position: absolute; top: 0; left: 0;
        width: 50%; height: 100%; background: var(--accent-color);
        animation: scanline 1s infinite linear alternate; /* Animasi geser */
        transform: translateX(-100%);
        animation: loadingBar 1.5s infinite;
    }
    @keyframes loadingBar { 0% {left: -50%;} 100% {left: 100%;} }

    /* --- HIDE DEFAULT STREAMLIT BLOAT --- */
    #MainMenu, footer, header, [data-testid="stDecoration"] { visibility: hidden; height: 0; display: none; }
    
    /* --- SIDEBAR CUSTOMIZATION --- */
    [data-testid="stSidebar"] {
        background-color: var(--sidebar-bg);
        border-right: 1px solid var(--border-color);
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label {
        color: #FFFFFF !important; /* Paksa teks sidebar putih */
    }
    
    /* --- CHAT BUBBLES (DARK MODE) --- */
    .stChatMessage {
        background-color: transparent !important;
        border: none !important;
        padding: 1rem 0 !important;
    }
    
    /* User Avatar */
    [data-testid="stChatMessageAvatarUser"] {
        background-color: #333 !important;
        color: #fff !important;
        border-radius: 50%;
        border: 1px solid #555;
    }
    
    /* AI Avatar (IEA Glowing Icon) */
    [data-testid="stChatMessageAvatarAssistant"] {
        background-color: rgba(0, 210, 255, 0.1) !important;
        color: var(--accent-color) !important;
        border: 1px solid var(--accent-color);
        box-shadow: 0 0 10px rgba(0, 210, 255, 0.3);
        border-radius: 50%;
    }

    /* --- TEXT VISIBILITY FIXER --- */
    /* Ini penting! Memaksa semua teks markdown menjadi terang */
    div.stMarkdown, div.stMarkdown p, div.stMarkdown li, div.stMarkdown h1, div.stMarkdown h2, div.stMarkdown h3 {
        color: #E0E0E0 !important;
    }
    
    /* Code Block Styling (Dark) */
    code {
        color: #FF79C6 !important;
        background-color: #282A36 !important;
        border: 1px solid #444;
        font-family: 'JetBrains Mono', monospace;
    }

    /* --- INPUT FIELDS (DARK) --- */
    .stTextInput input, .stTextArea textarea, .stChatInput textarea {
        background-color: var(--input-bg) !important;
        color: #FFFFFF !important; /* Teks input putih */
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
    }
    .stChatInput textarea:focus {
        border-color: var(--accent-color) !important;
        box-shadow: 0 0 0 1px var(--accent-color) !important;
    }

    /* --- BUTTONS --- */
    .stButton button {
        background-color: #252525;
        color: #FFF;
        border: 1px solid #444;
        transition: all 0.3s;
    }
    .stButton button:hover {
        background-color: var(--accent-color);
        color: #000;
        border-color: var(--accent-color);
        box-shadow: 0 0 15px rgba(0, 210, 255, 0.4);
    }

    /* --- UPLOADER --- */
    [data-testid="stFileUploader"] {
        background-color: #1A1A1A;
        padding: 15px; border-radius: 10px;
        border: 1px dashed #444;
    }
    [data-testid="stFileUploader"] small { color: #888; }
    </style>
    
    <div id="boot-screen">
        <div class="boot-text">IEA INTELLIGENCE</div>
        <div class="loader-bar"></div>
        <div style="margin-top:10px; color:#555; font-family:'JetBrains Mono'; font-size:0.8rem;">SYSTEM INITIALIZING...</div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 3. BACKEND CORE (ENGINE LOGIC)
# ==========================================

@st.cache_data(show_spinner=False)
def process_document(uploaded_file):
    """Membaca PDF dengan senyap."""
    try:
        pdf_reader = PdfReader(uploaded_file)
        text_data = ""
        for page in pdf_reader.pages:
            text_data += page.extract_text() or ""
        return text_data
    except Exception as e:
        return f"Error reading file: {e}"

def generate_pdf_report(chat_history):
    """Engine pembuat laporan PDF Hitam Putih (Professional)."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "IEA RESEARCH SESSION LOG", ln=1, align='C')
    pdf.ln(10)
    
    for msg in chat_history:
        role = "AI SYSTEM" if msg['role'] == "assistant" else "USER"
        # Sanitasi teks agar kompatibel dengan FPDF
        content = msg['content'].encode('latin-1', 'replace').decode('latin-1')
        
        pdf.set_font("Arial", 'B', 9)
        pdf.set_text_color(100, 100, 100) # Abu-abu untuk Role
        pdf.cell(0, 6, f"[{role}]", ln=1)
        
        pdf.set_font("Arial", '', 10)
        pdf.set_text_color(0, 0, 0) # Hitam untuk isi (di kertas putih)
        pdf.multi_cell(0, 5, content)
        pdf.ln(4)
        
    return pdf.output(dest='S').encode('latin-1')

def generate_voice_stream(text):
    """Engine Suara: Bersih dari kode."""
    try:
        # Hapus blok kode dan markdown agar suara enak didengar
        clean_text = re.sub(r'```.*?```', 'Berikut adalah kode atau diagramnya.', text, flags=re.DOTALL)
        clean_text = re.sub(r'[*_`#]', '', clean_text) 
        
        # Batasi panjang karakter untuk TTS (Free tier limit prevention)
        if len(clean_text) > 600: clean_text = clean_text[:600] + "..."
        
        if not clean_text.strip(): return None

        tts = gTTS(text=clean_text, lang='id', slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp
    except:
        return None

# ==========================================
# 4. SESSION STATE MANAGEMENT
# ==========================================
if "messages" not in st.session_state:
    # Pesan awal yang ramah namun profesional
    st.session_state.messages = [
        {"role": "assistant", "content": "Sistem Online. IEA Intelligence siap membantu riset Anda. \n\nSilakan upload dokumen PDF untuk analisis konteks, atau ajukan pertanyaan ilmiah secara langsung."}
    ]
if "document_context" not in st.session_state:
    st.session_state.document_context = ""

# ==========================================
# 5. SIDEBAR CONTROLS (DARK MODE)
# ==========================================
with st.sidebar:
    st.title("🎛️ CONTROL PANEL")
    st.caption("IEA Neural Interface V.5.0 (Dark)")
    st.divider()

    # 5.1 SECURE API KEY INPUT
    # Mencari di secrets dulu, kalau tidak ada baru minta input
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key:
        api_key = st.text_input("🔑 Groq API Key", type="password", help="Masukkan API Key Groq Anda di sini")
        if not api_key:
            st.warning("Menunggu Kunci Akses...")
            st.stop()
    
    # 5.2 DOCUMENT UPLOADER
    st.subheader("📄 INPUT DATA RISET")
    uploaded_file = st.file_uploader("Upload PDF (Maks 200MB)", type=["pdf"])
    
    if uploaded_file:
        with st.spinner("Mengenkripsi & Menganalisis Data..."):
            extracted_text = process_document(uploaded_file)
            st.session_state.document_context = extracted_text
            st.success(f"✅ Memori Terisi: {len(extracted_text)} karakter")
    
    if st.session_state.document_context:
        if st.button("🗑️ Hapus Memori Dokumen"):
            st.session_state.document_context = ""
            st.rerun()

    st.divider()
    
    # 5.3 UTILITIES
    col1, col2 = st.columns(2)
    with col1:
        # Slider Kreativitas
        creativity = st.slider("Kreativitas AI", 0.0, 1.0, 0.6)
    with col2:
        # Reset Button
        if st.button("🔄 Reset Chat"):
            st.session_state.messages = []
            st.rerun()
            
    # Export Chat to PDF
    if len(st.session_state.messages) > 1:
        pdf_data = generate_pdf_report(st.session_state.messages)
        st.download_button("📥 Export Log (PDF)", pdf_data, "IEA_Session_Log.pdf", "application/pdf", use_container_width=True)

# ==========================================
# 6. MAIN CHAT AREA (THE BRAIN)
# ==========================================

# Judul Halaman Minimalis (Teks Putih/Abu)
st.markdown("<h3 style='text-align: center; color: #555; margin-bottom: 30px; font-family:Orbitron; letter-spacing:2px;'>IEA INTELLIGENCE HUB</h3>", unsafe_allow_html=True)

# 6.1 RENDER CHAT HISTORY
for msg in st.session_state.messages:
    # Tentukan Ikon Avatar
    avatar_icon = "👤" if msg["role"] == "user" else "💠"
    
    with st.chat_message(msg["role"], avatar=avatar_icon):
        st.markdown(msg["content"])
        
        # Smart Feature: Auto-Render Diagram jika ada di history lama
        if "```graphviz" in msg["content"]:
            try:
                # Regex untuk mengambil kode di dalam blok graphviz
                graph_code = re.search(r'```graphviz\n(.*?)\n```', msg["content"], re.DOTALL).group(1)
                st.graphviz_chart(graph_code)
            except: pass

# 6.2 CHAT INPUT & PROCESSING
if prompt := st.chat_input("Masukkan perintah atau pertanyaan..."):
    
    # Simpan & Tampilkan Pesan User
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # AI Response Logic
    with st.chat_message("assistant", avatar="💠"):
        response_placeholder = st.empty()
        full_response = ""
        
        # Membangun Konteks (RAG)
        context_block = ""
        if st.session_state.document_context:
            context_block = f"\n[SUMBER DATA PDF]:\n{st.session_state.document_context[:10000]}...\n"

        # SYSTEM PROMPT (ULTIMATE INSTRUCTION)
        system_instruction = f"""
        Anda adalah IEA Intelligence, Asisten Riset Ilmiah Tingkat Lanjut.
        Karakteristik: Objektif, Analitis, Profesional, namun mudah dipahami.
        Bahasa: Indonesia Formal (EYD) yang baik.

        INSTRUKSI KHUSUS:
        1. Jawablah dengan struktur yang rapi (Gunakan Bullet Points atau Numbered Lists untuk keterbacaan).
        2. Jika pengguna meminta DIAGRAM, ALUR, STRUKTUR, atau PETA KONSEP, Anda WAJIB menyertakan blok kode Graphviz.
           Contoh Format Graphviz:
           ```graphviz
           digraph G {{
             rankdir=LR;
             node [style=filled, fillcolor="#1E1E1E", fontcolor="white", color="#00D2FF", shape=box, fontname="Arial"];
             edge [color="#555"];
             "Mulai" -> "Proses A" -> "Selesai";
           }}
           ```
        3. Gunakan informasi dari [SUMBER DATA PDF] jika relevan dengan pertanyaan user.
        4. Hindari penggunaan emoji yang berlebihan (keep it professional).
        {context_block}
        """

        messages_payload = [SystemMessage(content=system_instruction)]
        # Memori Jangka Pendek (Mengingat 8 percakapan terakhir)
        for m in st.session_state.messages[-8:]:
            if m["role"] == "user": messages_payload.append(HumanMessage(content=m["content"]))
            else: messages_payload.append(AIMessage(content=m["content"]))

        try:
            # Inisialisasi Model LLM (Groq)
            llm = ChatGroq(
                temperature=creativity,
                groq_api_key=api_key,
                model_name="llama-3.3-70b-versatile", # Model Llama 3 terbaik saat ini
                streaming=True
            )
            
            # Streaming Generation (Efek Mengetik)
            chunks = llm.stream(messages_payload)
            for chunk in chunks:
                if chunk.content:
                    full_response += chunk.content
                    # Menambahkan kursor "▌" untuk efek real-time
                    response_placeholder.markdown(full_response + "▌")
            
            # Final Render (Hapus kursor)
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            # POST-PROCESSING: AUTO DIAGRAM
            if "```graphviz" in full_response:
                try:
                    code_block = re.search(r'```graphviz\n(.*?)\n```', full_response, re.DOTALL).group(1)
                    st.graphviz_chart(code_block)
                except Exception as e:
                    st.error(f"Gagal Merender Visual: {e}")

            # POST-PROCESSING: AUTO VOICE
            # Membuat ikon audio kecil di bawah respons
            audio_bytes = generate_voice_stream(full_response)
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")

        except Exception as e:
            st.error(f"Koneksi Terputus: {str(e)}")
