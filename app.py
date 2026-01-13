# app.py (UPGRADED COSMOS TERMINAL)
import streamlit as st
import requests
import time
import html
from datetime import datetime

# ------------- CONFIG -------------
st.set_page_config(
    page_title="IEA COSMOS ALPHA",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

FIREBASE_URL = "https://iea-pendaftaran-default-rtdb.asia-southeast1.firebasedatabase.app"
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

# ------------- STYLES (NEON GLASS) -------------
st.markdown(
    """
    <style>
    :root{
        --bg:#05050a;
        --panel:#07070c;
        --glass: rgba(255,255,255,0.03);
        --accent:#00f6ff;
        --accent-2:#7c3cff;
        --muted:#9aa3b2;
    }
    html,body,#root{background:var(--bg) !important;}
    #MainMenu, header, footer {visibility: hidden;}
    .block-container {max-width: 980px; padding: 18px;}
    .cosmos-hero {
        text-align:center; padding: 32px 12px 18px;
        margin-bottom: 8px;
        background: linear-gradient(180deg, rgba(255,255,255,0.02), transparent);
        border-radius: 16px;
        box-shadow: 0 6px 30px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.03);
    }
    .cosmos-title{
        font-size:clamp(2.2rem, 7vw, 4rem);
        font-weight:900;
        letter-spacing:-4px;
        background: linear-gradient(90deg,var(--accent), var(--accent-2));
        -webkit-background-clip: text; color: transparent;
        margin: 0;
    }
    .cosmos-sub {color:var(--accent); font-family: monospace; letter-spacing:6px; margin-top:6px;}
    .panel {
        background: linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.015));
        border-radius: 14px;
        padding: 14px;
        border:1px solid rgba(255,255,255,0.03);
    }
    /* chat bubble */
    .bubble {
        padding: 14px 16px;
        margin: 10px 0;
        border-radius: 12px;
        box-shadow: 0 6px 20px rgba(2,6,23,0.6);
        font-size:1rem;
        line-height:1.6;
        max-width: 92%;
        word-wrap:break-word;
    }
    .bubble.user { background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); align-self:flex-end; border:1px solid rgba(255,255,255,0.02); }
    .bubble.assist { background: linear-gradient(90deg, rgba(0,246,255,0.06), rgba(124,60,255,0.03)); border:1px solid rgba(0,246,255,0.08); align-self:flex-start;}
    .chat-wrap { display:flex; flex-direction:column; gap:8px; }
    /* loader neon scan */
    .neon-loader {
        height:3px; width:100%;
        background: linear-gradient(90deg, transparent, rgba(0,246,255,0.6), transparent);
        background-size: 200% 100%;
        animation: scan 1.6s linear infinite;
        border-radius:4px;
        margin: 10px 0 18px;
    }
    @keyframes scan {
        0%{background-position:200%}
        100%{background-position:-200%}
    }
    /* typing skeleton */
    .skeleton {height:14px;width:80%;background:linear-gradient(90deg, rgba(255,255,255,0.02), rgba(255,255,255,0.05));border-radius:8px; margin:6px 0}
    /* responsive */
    @media (max-width:600px){
        .cosmos-title{font-size:2rem}
        .block-container{padding:12px}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------- HELPERS -------------
def check_membership(name: str) -> bool:
    name = (name or "").strip().lower()
    try:
        for g in ["iea_grup_1", "iea_grup_2"]:
            resp = requests.get(f"{FIREBASE_URL}/{g}.json", timeout=8)
            if resp.status_code != 200:
                continue
            data = resp.json()
            if not data:
                continue
            for k in data:
                if data[k].get("n", "").strip().lower() == name:
                    return True
        return False
    except Exception:
        # silent: membership check failed (treat as not found)
        return False

def safe_speech_text(text: str) -> str:
    # Escape single quotes/newlines for embedding in JS
    t = text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
    return t

def append_msg(role: str, content: str):
    st.session_state.msgs.append({"role": role, "content": content, "ts": time.time()})

def model_invoke(messages, primary="llama-3.3-70b-versatile", fallback="llama-3.1-8b-instant"):
    """Call ChatGroq LLM with fallback. Returns (success, text or error)."""
    try:
        from langchain_groq import ChatGroq
        from langchain_core.messages import SystemMessage, HumanMessage
    except Exception as e:
        return False, f"Model libs not available: {e}"

    try:
        llm = ChatGroq(groq_api_key=GROQ_API_KEY, model_name=primary, temperature=0.7)
        res = llm.invoke(messages).content
        return True, res
    except Exception as e:
        # try fallback smaller model
        try:
            llm = ChatGroq(groq_api_key=GROQ_API_KEY, model_name=fallback, temperature=0.7)
            res = llm.invoke(messages).content
            return True, res + "\n\n(note: served from fallback model)"
        except Exception as e2:
            return False, f"Model error: {e}; fallback error: {e2}"

# ------------- STATE -------------
if "auth" not in st.session_state:
    st.session_state.auth = False
if "msgs" not in st.session_state:
    st.session_state.msgs = []
if "last_msg" not in st.session_state:
    st.session_state.last_msg = 0.0
if "voice" not in st.session_state:
    st.session_state.voice = True
if "font_scale" not in st.session_state:
    st.session_state.font_scale = 1.0

# ------------- UI: HERO -------------
st.markdown(
    "<div class='cosmos-hero panel'>"
    "<h1 class='cosmos-title'>COSMOS</h1>"
    "<div class='cosmos-sub'>BEYOND IMAGINATION</div>"
    "</div>",
    unsafe_allow_html=True
)

# ------------- SIDEBAR (LOCAL SETTINGS) -------------
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.session_state.voice = st.checkbox("Voice (text-to-speech)", value=st.session_state.voice)
    scale = st.slider("Font scale", 0.8, 1.6, value=st.session_state.font_scale, step=0.05)
    st.session_state.font_scale = scale
    st.markdown("---")
    st.markdown("**Commands** (type in chat):")
    st.code("/clear  — reset chat\n/help   — show this help\n/about  — about COSMOS\n/voice on|off  — toggle voice locally")
    st.markdown("---")
    if st.button("Exit Terminal"):
        st.session_state.auth = False
        st.experimental_rerun()

# small inline font scaling (applies globally to chat content)
st.markdown(f"<style>.bubble{{font-size:{0.96*st.session_state.font_scale}rem}}</style>", unsafe_allow_html=True)

# ------------- LOGIN -------------
if not st.session_state.auth:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        name = st.text_input("IDENTIFICATION CODE", placeholder="Type your full name...")
        authorize = st.button("AUTHORIZE")
        if authorize:
            if not name:
                st.error("Please type your name.")
            else:
                # quick local throttling to avoid hammering Firebase
                if time.time() - st.session_state.get("last_auth", 0) < 2:
                    st.warning("Please wait a moment before retrying.")
                else:
                    st.session_state.last_auth = time.time()
                    ok = check_membership(name)
                    if ok:
                        st.session_state.auth = True
                        st.session_state.user = name.upper()
                        st.session_state.msgs = []
                        append_msg("assistant", f"Selamat datang {st.session_state.user}. COSMOS online.")
                        st.experimental_rerun()
                    else:
                        st.error("ACCESS DENIED — membership not found.")
    st.stop()

# ------------- TERMINAL -------------
# header quick info
st.markdown(
    f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;'>"
    f"<div style='color:var(--accent);font-weight:800'>{st.session_state.user}</div>"
    f"<div style='font-family:monospace;color:var(--muted)'>COSMOS • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>"
    f"</div>",
    unsafe_allow_html=True
)

# main panel layout
left, right = st.columns([3, 1], gap="large")

with left:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    # chat area container (render messages)
    chat_placeholder = st.empty()

    def render_chat():
        html_parts = ["<div class='chat-wrap'>"]
        for m in st.session_state.msgs:
            role = m.get("role", "assistant")
            cls = "user" if role == "user" else "assist"
            content = html.escape(m.get("content", ""))
            # simple markdown-like newlines to <br>
            content = content.replace("\n", "<br>")
            html_parts.append(f"<div class='bubble {cls}'>{content}</div>")
        html_parts.append("</div>")
        chat_placeholder.markdown("".join(html_parts), unsafe_allow_html=True)

    render_chat()

    # input box
    prompt = st.chat_input("Speak to COSMOS... (try /help)")
    if prompt:
        # basic rate-limit & cost protection
        if time.time() - st.session_state.last_msg < 1.5:
            st.warning("Too fast — slow down a bit.")
            st.stop()
        st.session_state.last_msg = time.time()

        # commands
        if prompt.strip().lower().startswith("/clear"):
            st.session_state.msgs = []
            append_msg("assistant", "Chat cleared.")
            render_chat()
            st.experimental_rerun()
        if prompt.strip().lower().startswith("/help"):
            help_text = ("Commands:\n"
                         "/clear — clear chat\n"
                         "/help — show commands\n"
                         "/about — about COSMOS\n"
                         "/voice on|off — toggle voice locally")
            append_msg("assistant", help_text)
            render_chat()
            st.stop()
        if prompt.strip().lower().startswith("/about"):
            about = "COSMOS — IEA private terminal. Designed for community: fast, sleek, and secure."
            append_msg("assistant", about)
            render_chat()
            st.stop()
        # voice toggle via command
        if prompt.strip().lower().startswith("/voice"):
            arg = prompt.strip().lower().split()
            if len(arg) > 1 and arg[1] in ("on", "off"):
                st.session_state.voice = (arg[1] == "on")
                append_msg("assistant", f"Voice set to {'ON' if st.session_state.voice else 'OFF'}.")
                render_chat()
                st.stop()

        # normal user content
        append_msg("user", prompt)
        render_chat()

        # show loader
        loader_ph = st.empty()
        loader_ph.markdown("<div class='neon-loader'></div>", unsafe_allow_html=True)

        # build messages for model (use last 6 entries local)
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            history = st.session_state.msgs[-8:]
            messages = [SystemMessage(content="You are COSMOS AI for IEA. Use Bahasa Indonesia. Be concise, futuristic, respectful.")]
            for h in history:
                if h["role"] == "user":
                    messages.append(HumanMessage(content=h["content"][:1500]))  # truncate long prompts
                else:
                    messages.append(SystemMessage(content=h["content"][:1200]))
        except Exception:
            # fallback strings if langchain messages absent
            messages = [{"role":"system","content":"COSMOS AI"}, {"role":"user","content": prompt[:1500]}]

        # invoke model with fallback
        ok, res = model_invoke(messages)
        loader_ph.empty()

        if not ok:
            # fail: show descriptive error but user-friendly
            append_msg("assistant", "COSMOS offline — gagal terhubung ke model. Coba lagi nanti.")
            render_chat()
            st.error(res)
            st.stop()

        # progressive typewriter rendering to feel premium
        append_msg("assistant", "")  # placeholder
        render_chat()
        # find last index to update
        idx = len(st.session_state.msgs) - 1

        # typewriter effect: chunk and update
        chunk_size = 30
        for i in range(0, len(res), chunk_size):
            st.session_state.msgs[idx]["content"] += res[i:i+chunk_size]
            render_chat()
            time.sleep(0.03)  # fast but smooth

        # finalize and optionally do voice TTS
        render_chat()
        if st.session_state.voice:
            safe = safe_speech_text(res)
            # embed TTS JS
            tts_html = f"""
            <script>
            try {{
                var u = new SpeechSynthesisUtterance('{safe}');
                u.lang = 'id-ID';
                u.rate = 1.0;
                u.volume = 1.0;
                window.speechSynthesis.cancel(); // stop any previous
                window.speechSynthesis.speak(u);
            }} catch(e){{console.log(e)}}
            </script>
            """
            st.components.v1.html(tts_html, height=0)

with right:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("### 🔭 Quick Tools")
    st.markdown("- `/help` untuk perintah\n- Voice: toggle pada Settings\n- Chat saved only locally (no Firebase writes)")
    st.markdown("---")
    st.markdown("### 📌 Tips")
    st.markdown("1. Keep prompts short (< 1.5k chars).\n2. Use clear requests (ex: 'Ringkas 5 poin tentang...').\n3. Use `/clear` to reset chat.")
    st.markdown("</div>", unsafe_allow_html=True)
