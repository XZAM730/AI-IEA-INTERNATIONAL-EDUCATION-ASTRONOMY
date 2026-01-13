"""
app.py — AI IEA (Final)
Features:
- Local persistent chat history (JSON)
- Export / Import history
- Image upload + thumbnail + basic OCR (if libs installed)
- LLM integration with fallback (langchain_groq if available)
- Streaming/typewriter effect for responses
- Responsive, neat UI for mobile/desktop
- No TTS / voice
"""

import streamlit as st
from PIL import Image
import io, os, json, time, base64, html
from datetime import datetime

# Optional libs detection
try:
    import pytesseract
    PYTESSERACT = True
except Exception:
    PYTESSERACT = False

try:
    import easyocr
    import numpy as np
    EASYOCR = True
except Exception:
    EASYOCR = False

# Try to import LLM client (langchain_groq)
def import_llm_client():
    try:
        from langchain_groq import ChatGroq
        from langchain_core.messages import SystemMessage, HumanMessage
        return ChatGroq, SystemMessage, HumanMessage
    except Exception:
        return None, None, None

ChatGroq, SystemMessage, HumanMessage = import_llm_client()

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI IEA", page_icon="🪐", layout="wide")
LOCAL_HISTORY_FILE = "ai_iea_chat_history"
MAX_CONTEXT_MESSAGES = 12     # how many previous msgs to send to LLM
PROMPT_TRUNCATE = 1500        # truncate individual messages to protect cost
RATE_LIMIT_SECS = 1.2

# ---------------- SESSION STATE ----------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []   # list of dicts: {role:user/ai, user, ai, ts, image_meta}
if "last_msg_ts" not in st.session_state:
    st.session_state.last_msg_ts = 0.0
if "font_scale" not in st.session_state:
    st.session_state.font_scale = 1.0

# ---------------- persistence ----------------
def load_history():
    if os.path.exists(LOCAL_HISTORY_FILE):
        try:
            with open(LOCAL_HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    st.session_state.chat_history = data
        except Exception:
            # ignore load errors and continue with empty
            pass

def save_history():
    try:
        with open(LOCAL_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.chat_history, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

load_history()

# ---------------- helpers ----------------
def make_thumb_b64(pil_img, max_size=(640, 640)):
    img = pil_img.copy()
    img.thumbnail(max_size)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def append_user_message(text, image_meta=None):
    st.session_state.chat_history.append({
        "role": "user",
        "user": text,
        "ts": datetime.utcnow().isoformat(),
        "image_meta": image_meta
    })
    save_history()

def append_ai_message(init_text=""):
    st.session_state.chat_history.append({
        "role": "ai",
        "ai": init_text,
        "ts": datetime.utcnow().isoformat()
    })
    save_history()

def update_last_ai_text(add_text):
    # append to last AI message content incrementally (for streaming)
    # assume last item is ai placeholder
    if not st.session_state.chat_history:
        return
    if st.session_state.chat_history[-1].get("role") != "ai":
        return
    st.session_state.chat_history[-1]["ai"] += add_text
    save_history()

def build_llm_messages():
    """
    Build messages for LLM (if langchain types available), otherwise
    return a single fallback text to pass to basic logic.
    """
    history = st.session_state.chat_history[-MAX_CONTEXT_MESSAGES:]
    if ChatGroq and SystemMessage and HumanMessage:
        msgs = [SystemMessage(content="You are AI IEA — assistant for the IEA community. "
                                     "Use Bahasa Indonesia. Be concise, helpful, structured.")]
        for item in history:
            if item["role"] == "user":
                msgs.append(HumanMessage(content=item.get("user","")[:PROMPT_TRUNCATE]))
            else:
                msgs.append(SystemMessage(content=item.get("ai","")[:PROMPT_TRUNCATE]))
        return ("llm", msgs)
    else:
        # fallback: combine recent conversation into a single prompt string
        s = "You are AI IEA. Use Bahasa Indonesia. Be concise and helpful.\n\nRecent conversation:\n"
        for item in history:
            if item["role"] == "user":
                s += f"User: {item.get('user','')}\n"
            else:
                s += f"AI: {item.get('ai','')}\n"
        s += "\nAnswer concisely to the last user message."
        return ("fallback", s)

def model_invoke(messages_tuple, primary="llama-3.3-70b-versatile", fallback="llama-3.1-8b-instant"):
    mode, payload = messages_tuple
    if mode == "llm" and ChatGroq and SystemMessage and HumanMessage:
        try:
            llm = ChatGroq(groq_api_key=st.secrets.get("GROQ_API_KEY",""), model_name=primary, temperature=0.7)
            res = llm.invoke(payload).content
            return True, res
        except Exception as e:
            # try fallback smaller model
            try:
                llm = ChatGroq(groq_api_key=st.secrets.get("GROQ_API_KEY",""), model_name=fallback, temperature=0.7)
                res = llm.invoke(payload).content
                return True, res + "\n\n(note: response from fallback model)"
            except Exception as e2:
                return False, f"Model error: {e}; fallback error: {e2}"
    else:
        # fallback deterministic/simple response if no LLM lib available
        if mode == "fallback":
            last_user = st.session_state.chat_history[-1].get("user","")
            return True, f"Aku paham: \"{last_user}\".\n\n(Tolong pasang LLM untuk jawaban yang lebih kaya.)"
        else:
            return False, "No model client available."

# ---------------- UI STYLE ----------------
st.markdown(f"""
<style>
:root{{--bg:#05050a;--panel:#0b0b10;--accent:#00f6ff;--muted:#9aa3b2;}}
#MainMenu, header, footer {{visibility: hidden;}}
.block-container {{max-width:1100px;padding:14px;}}
.header{{padding:16px;border-radius:12px;margin-bottom:12px;background:linear-gradient(180deg, rgba(255,255,255,0.02), transparent);border:1px solid rgba(255,255,255,0.03)}}
.header h1{{margin:0;font-size:clamp(1.6rem,4vw,2.6rem);font-weight:900;background:linear-gradient(90deg,var(--accent),#7c3cff);-webkit-background-clip:text;color:transparent;}}
.sub{{color:var(--accent);letter-spacing:4px;font-family:monospace;margin-top:6px}}
.row{{display:flex;gap:18px}}
.left{{flex:3}}
.right{{flex:1;min-width:260px}}
.panel{{background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));border-radius:12px;padding:12px;border:1px solid rgba(255,255,255,0.03)}}
.chat-wrap{{display:flex;flex-direction:column;gap:10px}}
.bubble{{padding:12px 14px;border-radius:12px;max-width:95%;line-height:1.6;box-shadow:0 8px 30px rgba(0,0,0,0.6)}}
.user{{align-self:flex-end;background:linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01));}}
.ai{{align-self:flex-start;background:linear-gradient(90deg, rgba(0,246,255,0.06), rgba(124,60,255,0.03));}}
.loader{{height:3px;background:linear-gradient(90deg,transparent,var(--accent),transparent);background-size:200% 100%;animation:scan 1.6s linear infinite;border-radius:4px;margin:10px 0}}
@keyframes scan{{0%{{background-position:200%}}100%{{background-position:-200%}}}}
.small-muted{{color:var(--muted);font-size:0.9rem}}
@media (max-width:700px) {{
  .row {{flex-direction:column}}
  .right {{min-width:unset}}
}}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("<div class='header'><h1>AI IEA</h1><div class='sub'>Komunitas IEA</div></div>", unsafe_allow_html=True)

# ---------------- LAYOUT ----------------
col_left, col_right = st.columns([3,1])

# chat rendering area (placeholder for auto update)
chat_placeholder = col_left.empty()

def render_chat():
    html_parts = [f"<div style='font-size:{0.95*st.session_state.font_scale}rem' class='chat-wrap'>"]
    for item in st.session_state.chat_history:
        if item.get("role") == "user":
            txt = html.escape(item.get("user","")).replace("\n","<br>")
            html_parts.append(f"<div class='bubble user'>{txt}</div>")
            # image preview if present
            meta = item.get("image_meta")
            if meta and meta.get("thumb_b64"):
                html_parts.append(
                    f"<div style='margin:6px 0'><img src='data:image/png;base64,{meta['thumb_b64']}' "
                    f"style='max-width:260px;border-radius:8px;border:1px solid rgba(255,255,255,0.03)'></div>"
                )
        else:
            txt = html.escape(item.get("ai","")).replace("\n","<br>")
            html_parts.append(f"<div class='bubble ai'>{txt}</div>")
    html_parts.append("</div>")
    chat_placeholder.markdown("".join(html_parts), unsafe_allow_html=True)

render_chat()

# ---------------- RIGHT: Controls, History management ----------------
with col_right:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("### ⚙️ Pengaturan")
    st.session_state.font_scale = st.slider("Skala font", 0.85, 1.4, value=st.session_state.font_scale, step=0.05)
    st.markdown("---")
    st.markdown("### Riwayat")
    st.markdown(f"- Pesan disimpan lokal: **{len(st.session_state.chat_history)}**")
    if st.button("Export Riwayat"):
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
                save_history()
                st.success("Riwayat berhasil diimport")
                render_chat()
            else:
                st.error("Format tidak valid")
        except Exception as e:
            st.error(f"Gagal import: {e}")
    if st.button("Hapus semua riwayat"):
        st.session_state.chat_history = []
        save_history()
        st.success("Riwayat dihapus.")
        render_chat()
    st.markdown("---")
    st.markdown("### Tips")
    st.markdown("• Gunakan instruksi yang jelas.\n• Jika kirim gambar,jelaskan tujuan analisis")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- INPUT FORM (use clear_on_submit to avoid session_state write errors) ----------------
with col_left.form("input_form", clear_on_submit=True):
    user_input = st.text_area("Kirim pesan ke AI IEA", placeholder="Tulis pertanyaan atau perintahmu...", height=110)
    uploaded_file = st.file_uploader("Kirim gambar (opsional) — PNG/JPG", type=["png","jpg","jpeg"])
    cols = st.columns([1,1,1])
    send = cols[0].form_submit_button("Kirim")
    # optional quick clear (form will auto-clear on submit)
    reset = cols[1].form_submit_button("Bersihkan")
    if reset:
        # form clears itself because clear_on_submit=True is set for the form when submitted,
        # but user clicked reset - we don't need to mutate session_state keys tied to widgets.
        pass

    if send:
        # basic validation
        text = (user_input or "").strip()
        if not text and uploaded_file is None:
            st.warning("Isi pesan atau lampirkan gambar sebelum mengirim.")
        else:
            # rate limit
            if time.time() - st.session_state.last_msg_ts < RATE_LIMIT_SECS:
                st.warning("Terlalu cepat — tunggu sebentar.")
            else:
                st.session_state.last_msg_ts = time.time()

                # handle image: create thumbnail b64 and meta
                image_meta = None
                pil_img = None
                if uploaded_file is not None:
                    try:
                        pil_img = Image.open(uploaded_file).convert("RGB")
                        thumb_b64 = make_thumb_b64(pil_img, max_size=(640,640))
                        image_meta = {"filename": uploaded_file.name, "size": len(uploaded_file.getvalue()), "thumb_b64": thumb_b64}
                    except Exception:
                        pil_img = None
                        image_meta = None

                # append user message
                append_user_message(text, image_meta=image_meta)
                render_chat()

                # if image present, perform lightweight analysis (OCR if available)
                if pil_img is not None:
                    analysis_lines = []
                    if PYTESSERACT:
                        try:
                            ocr_txt = pytesseract.image_to_string(pil_img)
                            if ocr_txt and ocr_txt.strip():
                                analysis_lines.append("OCR (pytesseract): " + ocr_txt.strip())
                        except Exception:
                            pass
                    if not analysis_lines and EASYOCR:
                        try:
                            reader = easyocr.Reader(['en'], gpu=False)
                            np_img = np.array(pil_img)
                            res = reader.readtext(np_img)
                            if res:
                                texts = " | ".join([r[1] for r in res])
                                analysis_lines.append("Detected text (easyocr): " + texts)
                        except Exception:
                            pass
                    if not analysis_lines:
                        w,h = pil_img.size
                        analysis_lines.append(f"Gambar diterima — resolusi {w}x{h} px.")
                    # add quick analysis message to history (assistant role)
                    append_ai_message("[Analisis gambar]\n" + "\n".join(analysis_lines))
                    render_chat()

                # Build LLM messages or fallback prompt
                messages_payload = build_llm_messages()

                # show loader
                loader_ph = st.empty()
                loader_ph.markdown("<div class='loader'></div>", unsafe_allow_html=True)

                # invoke model (primary then fallback)
                ok, response_text = model_invoke(messages_payload)
                loader_ph.empty()

                if not ok:
                    # model failed; append friendly error
                    append_ai_message("Maaf — gagal terhubung ke model AI. Coba lagi nanti.")
                    render_chat()
                else:
                    # streaming/typewriter effect:
                    append_ai_message("")  # placeholder for streaming content
                    render_chat()
                    idx = len(st.session_state.chat_history) - 1
                    chunk = 40
                    for i in range(0, len(response_text), chunk):
                        piece = response_text[i:i+chunk]
                        update_last_ai_text(piece)
                        render_chat()
                        time.sleep(0.03)
                    # final save done inside update_last_ai_text
                # end send handler

# ---------------- ensure bottom spacing ----------------
st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
