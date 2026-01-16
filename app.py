import streamlit as st
import re
import time
from io import BytesIO
from gtts import gTTS
from fpdf import FPDF
from PyPDF2 import PdfReader
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# =========================================================
# 1. INITIALIZATION & PAGE CONFIG (THE FOUNDATION)
# =========================================================
st.set_page_config(
    page_title="IEA INTELLIGENCE HUB",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# 2. ADVANCED CSS INJECTION (THE "PERFECT" UI)
# =========================================================
st.markdown("""
    <style>
    /* --- FONTS & BASE --- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;700&display=swap');
    
    .stApp {
        background-color: #ffffff;
        color: #1a1a1a;
        font-family: 'Inter', sans-serif;
    }

    /* --- HIDING BLOATWARE --- */
    #MainMenu, footer, header, [data-testid="stDecoration"], [data-testid="stStatusWidget"] {
        visibility: hidden; display: none;
    }

    /* --- SIDEBAR STYLING --- */
    [data-testid="stSidebar"] {
        background-color: #f9f9f9;
        border-right: 1px solid #e5e5e5;
    }
    [data-testid="stSidebar"] h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 1.1rem;
        color: #333;
    }

    /* --- CHAT INTERFACE --- */
    .stChatMessage {
        background-color: transparent !important;
        border: none !important;
        padding: 1.5rem 0 !important;
        gap: 1rem;
    }
    
    /* USER AVATAR */
    [data-testid="stChatMessageAvatarUser"] {
        background-color: #343541 !important;
        color: #fff !important;
        border-radius: 6px !important;
    }
    
    /* AI AVATAR (IEA BRANDING) */
    [data-testid="stChatMessageAvatarAssistant"] {
        background-color: #10a37f !important;
        color: #fff !important;
        border-radius: 6px !important;
    }

    /* --- INPUT FIELDS --- */
    .stTextInput input, .stTextArea textarea {
        background-color: #ffffff !important;
        border: 1px solid #d1d5db !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        color: #000 !important;
        font-family: 'Inter', sans-serif;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #10a37f !important;
        box-shadow: 0 0 0 2px rgba(16, 163, 127, 0.2) !important;
        outline: none;
    }

    /* --- BUTTONS --- */
    .stButton button {
        background-color: #ffffff;
        color: #374151;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        border-color: #10a37f;
        color: #10a37f;
        background-color: #f0fdf4;
    }

    /* --- CODE BLOCKS & UPLOADER --- */
    code {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem;
    }
    [data-testid="stFileUploader"] section {
        background-color: #fff;
        border: 1px dashed #cbd5e1;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 3. BACKEND ENGINES (LOGIC & UTILS)
# =========================================================

@st.cache_data(show_spinner=False)
def process_pdf(file):
    """Membaca PDF dengan Caching Cerdas."""
    try:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        return ""

def create_pdf_report(chat_history):
    """Engine pembuat laporan PDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "IEA INTELLIGENCE LOG", ln=1, align='C')
    pdf.ln(10)
    
    # Content
    for msg in chat_history:
        role = "AI SYSTEM" if msg['role'] == "assistant" else "RESEARCHER"
        content = msg['content'].encode('latin-1', 'replace').decode('latin-1')
        
        pdf.set_font("Arial", 'B', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f"[{role}]", ln=1)
        
        pdf.set_font("Arial", '', 10)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 5, content)
        pdf.ln(4)
        
    return pdf.output(dest='S').encode('latin-1')

def generate_voice(text):
    """Engine Suara: Membersihkan kode sebelum dibaca."""
    try:
        # Hapus blok kode diagram/program agar tidak dieja
        clean = re.sub(r'```.*?```', '[Diagram Visual Ditampilkan]', text, flags=re.DOTALL)
        clean = re.sub(r'[*_`#]', '', clean) # Hapus markdown
        
        if len(clean) > 800: clean = clean[:800] # Limitasi agar cepat
        if not clean.strip(): return None

        tts = gTTS(text=clean, lang='id', slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp
    except:
        return None

# =========================================================
# 4. STATE MANAGEMENT
# =========================================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Sistem Online. IEA Intelligence siap membantu riset Anda. Silakan upload dokumen atau mulai diskusi."}
    ]
if "document_memory" not in st.session_state:
    st.session_state.document_memory = ""

# =========================================================
# 5. SIDEBAR CONTROLS
# =========================================================
with st.sidebar:
    st.title("🎛️ Control Panel")
    st.caption("IEA Neural Interface V.4.0")
    st.markdown("---")

    # 5.1 SECURE API ENTRY
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key:
        api_key = st.text_input("🔑 Groq API Key", type="password", placeholder="gsk_...")
        if not api_key:
            st.warning("Menunggu Kunci Akses...")
            st.stop()
    
    # 5.2 DOCUMENT INGESTION
    st.subheader("📄 Konteks Data")
    uploaded_file = st.file_uploader("Upload Dokumen PDF", type=["pdf"])
    
    if uploaded_file:
        with st.spinner("Mengasimilasi Data..."):
            extracted_text = process_pdf(uploaded_file)
            st.session_state.document_memory = extracted_text
            st.success(f"Memori Terisi: {len(extracted_text)} karakter")
    
    if st.session_state.document_memory:
        if st.button("🗑️ Hapus Memori Dokumen"):
            st.session_state.document_memory = ""
            st.rerun()

    st.markdown("---")
    
    # 5.3 UTILITIES
    col1, col2 = st.columns(2)
    with col1:
        creativity = st.slider("Kreativitas", 0.0, 1.0, 0.4)
    with col2:
        if st.button("🔄 Reset"):
            st.session_state.chat_history = []
            st.rerun()
            
    if st.session_state.chat_history:
        pdf_log = create_pdf_report(st.session_state.chat_history)
        st.download_button("📥 Export Log", pdf_log, "iea-session.pdf", "application/pdf", use_container_width=True)

# =========================================================
# 6. MAIN INTELLIGENCE INTERFACE
# =========================================================

# Header Minimalis
st.markdown("<h4 style='text-align: center; color: #aaa; margin-bottom: 30px; letter-spacing: 2px;'>IEA INTELLIGENCE</h4>", unsafe_allow_html=True)

# 6.1 RENDER HISTORY (Mengingat Diagram)
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # Auto-Render Diagram dari history lama
        if "```graphviz" in msg["content"]:
            try:
                code_block = re.search(r'```graphviz\n(.*?)\n```', msg["content"], re.DOTALL).group(1)
                st.graphviz_chart(code_block)
            except: pass

# 6.2 CHAT LOGIC
if prompt := st.chat_input("Masukkan perintah atau pertanyaan..."):
    
    # Display User
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display AI Response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # Build Context
        rag_context = ""
        if st.session_state.document_memory:
            rag_context = f"\n[SUMBER DATA PDF]:\n{st.session_state.document_memory[:10000]}...\n"

        # SYSTEM PROMPT (THE BRAIN)
        system_instructions = f"""
        Anda adalah IEA Intelligence, Asisten Riset Ilmiah Tingkat Lanjut.
        Karakteristik: Objektif, Analitis, Profesional.
        Bahasa: Indonesia Formal (EYD).

        INSTRUKSI UTAMA:
        1. Jawab dengan struktur yang rapi (Bullet points/Numbered lists).
        2. Jika pengguna meminta DIAGRAM, ALUR, STRUKTUR, atau PETA KONSEP, WAJIB sertakan blok kode Graphviz.
           Format:
           ```graphviz
           digraph G {{
             rankdir=LR;
             node [style=filled, fillcolor="#f0fdf4", color="#10a37f", shape=box, fontname="Arial"];
             "Mulai" -> "Proses";
           }}
           ```
        3. Gunakan data dari [SUMBER DATA PDF] jika relevan.
        4. Hindari penggunaan emoji yang berlebihan.
        {rag_context}
        """

        messages_payload = [SystemMessage(content=system_instructions)]
        # Memori Percakapan (10 pesan terakhir)
        for m in st.session_state.chat_history[-10:]:
            if m["role"] == "user": messages_payload.append(HumanMessage(content=m["content"]))
            else: messages_payload.append(AIMessage(content=m["content"]))

        try:
            # Initialize LLM
            llm = ChatGroq(
                temperature=creativity,
                groq_api_key=api_key,
                model_name="llama-3.3-70b-versatile",
                streaming=True
            )
            
            # Streaming Generation
            chunks = llm.stream(messages_payload)
            for chunk in chunks:
                if chunk.content:
                    full_response += chunk.content
                    response_placeholder.markdown(full_response + "▌")
            
            # Finalize Output
            response_placeholder.markdown(full_response)
            st.session_state.chat_history.append({"role": "assistant", "content": full_response})
            
            # POST-PROCESSING: DIAGRAM RENDERER
            if "```graphviz" in full_response:
                try:
                    code_block = re.search(r'```graphviz\n(.*?)\n```', full_response, re.DOTALL).group(1)
                    st.graphviz_chart(code_block)
                except Exception as e:
                    st.error(f"Visual Rendering Error: {e}")

            # POST-PROCESSING: AUDIO GENERATOR
            audio_data = generate_voice(full_response)
            if audio_data:
                st.audio(audio_data, format="audio/mp3")

        except Exception as e:
            st.error(f"Koneksi Jaringan Terputus: {str(e)}")
