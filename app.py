# app.py — AI IEA (Final: long-term local memory, image upload + analysis, streaming responses)
import streamlit as st
from PIL import Image
import io, os, json, time, html, base64
from datetime import datetime

# Optional libs (used if tersedia)
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except Exception:
    PYTESSERACT_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except Exception:
    EASYOCR_AVAILABLE = False

# LLM client will be attempted if available
def import_llm():
    try:
        from langchain_groq import ChatGroq
        from langchain_core.messages import SystemMessage, HumanMessage
        return ChatGroq, SystemMessage, HumanMessage
    except Exception:
        return None, None, None

ChatGroq, SystemMessage, HumanMessage = import_llm()

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI IEA", page_icon="🪐", layout="wide")
LOCAL_HISTORY_FILE = os.path.join(os.getcwd(), "ai_iea_chat_history.json")
MAX_HISTORY_MESSAGES = 12   # how many messages to include in context

# ---------------- SESSION STATE ----------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []   # list of dict: {role:user/ai, user, ai, ts, image_meta}
if "last_msg" not in st.session_state:
    st.session_state.last_msg = 0.0
if "font_scale" not in st.session_state:
    st.session_state.font_scale = 1.0
if "voice" not in st.session_state:
    st.session_state.voice = False  # voice removed per request

# ---------------- UTIL: persistence ----------------
def load_local_history():
    if os.path.exists(LOCAL_HISTORY_FILE):
        try:
            with open(LOCAL_HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    st.session_state.chat_history = data
        except Exception:
            # ignore load errors (start fresh)
            pass

def save_local_history():
    try:
        with open(LOCAL_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.chat_history, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# load history at startup
load_local_history()

# ---------------- UI STYLE ----------------
st.markdown("""
<style>
:root{--bg:#05050a;--panel:#0b0b10;--accent:#00f6ff;--muted:#9aa3b2;}
#MainMenu, header, footer {visibility: hidden;}
.block-container{max-width:1100px;padding:14px;}
.row {display:flex; gap:18px;}
.col-left{flex:3}
.col-right{flex:1; min-width:260px}
.chat-wrap {display:flex; flex-direction:column; gap:10px;}
.bubble {padding:12px 14px; border-radius:12px; max-width:95%; box-shadow: 0 8px 30px rgba(0,0,0,0.6);}
.user{align-self:flex-end;background:linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01));}
.ai{align-self:flex-start;background:linear-gradient(90deg, rgba(0,246,255,0.06), rgba(124,60,255,0.03));}
.header{padding:18px;border-radius:14px;margin-bottom:12px;background:linear-gradient(180deg, rgba(255,255,255,0.02), transparent);border:1px solid rgba(255,255,255,0.03)}
.loader {height:3px;background: linear-gradient(90deg, transparent, #00f6ff, transparent); background-size:200% 100%; animation:scan 1.6s linear infinite;border-radius:4px;margin:10px 0}
@keyframes scan {0%{background-position:200%}100%{background-position:-200%}}
.small-muted{color:#9aa3b2;font-size:0.85rem}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("<div class='header'><h1 style='margin:0;line-height:1'>AI IEA</h1><div class='small-muted'>Komunitas IEA • AI Privat</div></div>", unsafe_allow_html=True)

# ---------------- LAYOUT ----------------
left_col, right_col = st.columns([3,1])

# ---------------- RIGHT: controls, history export/import ----------------
with right_col:
    st.markdown("### ⚙️ Pengaturan")
    st.session_state.font_scale = st.slider("Skala font", 0.85, 1.4, value=st.session_state.font_scale, step=0.05)
    st.markdown("---")
    st.markdown("### 🕓 Riwayat")
    st.markdown(f"- Pesan tersimpan lokal: **{len(st.session_state.chat_history)}**")
    if st.button("🗂 Export Riwayat (JSON)"):
        payload = json.dumps(st.session_state.chat_history, ensure_ascii=False, indent=2)
        b64 = base64.b64encode(payload.encode()).decode()
        href = f'<a href="data:application/json;base64,{b64}" download="ai_iea_history_{int(time.time())}.json">Download Riwayat</a>'
        st.markdown(href, unsafe_allow_html=True)
    upload = st.file_uploader("Import riwayat (JSON)", type=["json"])
    if upload is not None:
        try:
            imported = json.load(upload)
            if isinstance(imported, list):
                st.session_state.chat_history = imported + st.session_state.chat_history
                save_local_history()
                st.success("Riwayat berhasil diimport dan digabung.")
            else:
                st.error("Format tidak valid (harus list JSON).")
        except Exception as e:
            st.error(f"Gagal import: {e}")
    st.markdown("---")
    if st.button("🧹 Hapus seluruh riwayat lokal"):
        st.session_state.chat_history = []
        save_local_history()
        st.success("Riwayat dihapus.")
    st.markdown("---")
    st.markdown("### ℹ️ Tips")
    st.markdown("• Gunakan deskripsi singkat & tujuan.\n• Jika kirim gambar, jelaskan apa yang ingin dianalisis.\n• Riwayat disimpan lokal pada server (file JSON).")

# ---------------- LEFT: chat area ----------------
with left_col:
    # render chat
    def render_chat():
        chat_html = f"<div style='font-size:{0.95*st.session_state.font_scale}rem' class='chat-wrap'>"
        for i, e in enumerate(st.session_state.chat_history):
            if e.get("role") == "user":
                txt = html.escape(e.get("user", "")).replace("\n","<br>")
                chat_html += f"<div class='bubble user'>{txt}</div>"
                # if image meta exists, show small preview
                if e.get("image_meta"):
                    meta = e["image_meta"]
                    if meta.get("thumb_b64"):
                        chat_html += f"<div style='margin:6px 0'><img src='data:image/png;base64,{meta['thumb_b64']}' style='max-width:220px;border-radius:8px;border:1px solid rgba(255,255,255,0.03)'></div>"
            else:
                txt = html.escape(e.get("ai", "")).replace("\n","<br>")
                chat_html += f"<div class='bubble ai'>{txt}</div>"
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)

    render_chat()

    st.markdown("---")
    with st.form("input_form", clear_on_submit=False):
        user_text = st.text_area("Kirim pesan ke AI IEA", key="user_text", height=100, placeholder="Tulis permintaanmu di sini...")
        uploaded_file = st.file_uploader("Kirim gambar (opsional) — PNG/JPG", type=["png","jpg","jpeg"])
        cols = st.columns([1,1,1])
        send_btn = cols[0].form_submit_button("Kirim")
        clear_input = cols[1].form_submit_button("Bersihkan Form")
        if clear_input:
            st.session_state["user_text"] = ""
        # send handling
        if send_btn:
            prompt = (user_text or "").strip()
            if prompt == "" and uploaded_file is None:
                st.warning("Tolong isi pesan atau kirim gambar.")
            else:
                # rate limit
                if time.time() - st.session_state.last_msg < 1.2:
                    st.warning("Terlalu cepat — tunggu sebentar.")
                else:
                    st.session_state.last_msg = time.time()

                    # process image if present
                    image_meta = None
                    pil_image = None
                    if uploaded_file is not None:
                        try:
                            pil_image = Image.open(uploaded_file).convert("RGB")
                            # create small thumb base64
                            thumb = pil_image.copy()
                            thumb.thumbnail((480,480))
                            buf = io.BytesIO()
                            thumb.save(buf, format="PNG")
                            thumb_b64 = base64.b64encode(buf.getvalue()).decode()
                            image_meta = {"filename": uploaded_file.name, "size": len(uploaded_file.getvalue()), "thumb_b64": thumb_b64}
                        except Exception:
                            pil_image = None
                            image_meta = None

                    # append user entry to history (role user)
                    st.session_state.chat_history.append({
                        "role": "user",
                        "user": prompt,
                        "ts": datetime.utcnow().isoformat(),
                        "image_meta": image_meta
                    })
                    save_local_history()
                    render_chat()

                    # analyze image (OCR / lightweight) and build context
                    analysis_note = ""
                    if pil_image is not None:
                        analysis_parts = []
                        if PYTESSERACT_AVAILABLE:
                            try:
                                txt = pytesseract.image_to_string(pil_image)
                                if txt and txt.strip():
                                    analysis_parts.append("OCR text: " + txt.strip())
                            except Exception:
                                pass
                        if not analysis_parts and EASYOCR_AVAILABLE:
                            try:
                                reader = easyocr.Reader(['en'], gpu=False)
                                result = reader.readtext(np.array(pil_image))
                                if result:
                                    txts = " | ".join([r[1] for r in result])
                                    analysis_parts.append("Detected text: " + txts)
                            except Exception:
                                pass
                        # fallback: basic meta
                        if not analysis_parts:
                            w, h = pil_image.size
                            analysis_parts.append(f"Image received (size: {w}x{h}).")
                        analysis_note = "\n".join(analysis_parts)
                        # add system-like note to history as assistant preface (not final ai answer)
                        st.session_state.chat_history.append({
                            "role": "ai",
                            "ai": f"[Analisis gambar]\n{analysis_note}",
                            "ts": datetime.utcnow().isoformat()
                        })
                        save_local_history()
                        render_chat()

                    # build LLM prompt: include last messages for context
                    # If langchain available, we build messages accordingly
                    # Otherwise fallback to simple deterministic reply
                    def build_context_messages():
                        history = st.session_state.chat_history[-MAX_HISTORY_MESSAGES:]
                        if ChatGroq and SystemMessage and HumanMessage:
                            msgs = [SystemMessage(content="You are AI IEA — assistant for the IEA community. Use Bahasa Indonesia. Keep answers helpful, concise, and structured.")]
                            for item in history:
                                if item["role"] == "user":
                                    m = item.get("user","")
                                    msgs.append(HumanMessage(content=m[:1500]))
                                else:
                                    msgs.append(SystemMessage(content=item.get("ai","")[:1500]))
                            return msgs
                        else:
                            # fallback: return single combined string
                            combined = "System: You are AI IEA. Use Bahasa Indonesia.\n\nRecent chat:\n"
                            for item in history:
                                if item["role"] == "user":
                                    combined += f"User: {item.get('user','')}\n"
                                else:
                                    combined += f"AI: {item.get('ai','')}\n"
                            combined += "\nAnswer concisely:"
                            return [{"role":"fallback","content":combined}]
                    messages = build_context_messages()

                    # show loader
                    loader_ph = st.empty()
                    loader_ph.markdown("<div class='loader'></div>", unsafe_allow_html=True)

                    # invoke model (with fallback)
                    ai_text = None
                    # prefer real LLM if available
                    if ChatGroq and SystemMessage and HumanMessage:
                        try:
                            llm = ChatGroq(groq_api_key=st.secrets.get("GROQ_API_KEY",""), model_name="llama-3.3-70b-versatile", temperature=0.7)
                            res = llm.invoke(messages).content
                            ai_text = res
                        except Exception as e:
                            # try smaller model
                            try:
                                llm = ChatGroq(groq_api_key=st.secrets.get("GROQ_API_KEY",""), model_name="llama-3.1-8b-instant", temperature=0.7)
                                res = llm.invoke(messages).content
                                ai_text = res + "\n\n(note: served from fallback model)"
                            except Exception as e2:
                                ai_text = None
                    else:
                        # fallback deterministic reply (simple heuristic) when LLM client not installed
                        last_user = st.session_state.chat_history[-1].get("user","")
                        ai_text = f"Aku mengerti: \"{last_user}\".\n\n(Tolong sambungkan LLM untuk jawaban lebih canggih.)"

                    loader_ph.empty()

                    if ai_text is None:
                        # failed to get LLM response
                        st.session_state.chat_history.append({
                            "role":"ai",
                            "ai":"Maaf — gagal terhubung ke model AI. Coba lagi nanti.",
                            "ts": datetime.utcnow().isoformat()
                        })
                        save_local_history()
                        render_chat()
                    else:
                        # streaming / typewriter effect (chunk update)
                        st.session_state.chat_history.append({
                            "role":"ai",
                            "ai":"",  # placeholder to be filled incrementally
                            "ts": datetime.utcnow().isoformat()
                        })
                        save_local_history()
                        render_chat()
                        idx = len(st.session_state.chat_history) - 1
                        chunk_size = 40
                        for i in range(0, len(ai_text), chunk_size):
                            piece = ai_text[i:i+chunk_size]
                            st.session_state.chat_history[idx]["ai"] += piece
                            save_local_history()
                            render_chat()
                            time.sleep(0.03)
                        # final save
                        save_local_history()
                        render_chat()

                    # clear input area
                    st.session_state["user_text"] = ""

# ---------------- END LEFT ----------------

# ensure chat area bottom visible after actions
st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
