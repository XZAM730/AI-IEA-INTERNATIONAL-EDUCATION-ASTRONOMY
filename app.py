import streamlit as st
import requests
import time
import html
from datetime import datetime

# ================= CONFIG =================
st.set_page_config(
    page_title="IEA COSMOS ALPHA",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

FIREBASE_URL = "https://iea-pendaftaran-default-rtdb.asia-southeast1.firebasedatabase.app"
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

# ================= STYLE =================
st.markdown("""
<style>
:root{
    --bg:#05050a;
    --panel:#0a0a12;
    --accent:#00f6ff;
    --accent2:#7c3cff;
}
#MainMenu, header, footer {visibility:hidden;}
.stApp{background:var(--bg);color:#fff;font-family:Inter,sans-serif;}
.block-container{max-width:980px;padding:16px;}
.hero{
    text-align:center;
    padding:32px 16px;
    border-radius:18px;
    background:linear-gradient(180deg,rgba(255,255,255,.04),transparent);
    border:1px solid rgba(255,255,255,.05);
    box-shadow:0 10px 40px rgba(0,0,0,.7);
}
.hero h1{
    font-size:clamp(2.3rem,7vw,4.2rem);
    font-weight:900;
    letter-spacing:-4px;
    background:linear-gradient(90deg,var(--accent),var(--accent2));
    -webkit-background-clip:text;
    color:transparent;
}
.hero p{
    color:var(--accent);
    letter-spacing:6px;
    font-family:monospace;
}
.panel{
    background:linear-gradient(180deg,rgba(255,255,255,.02),rgba(255,255,255,.01));
    border:1px solid rgba(255,255,255,.04);
    border-radius:14px;
    padding:14px;
}
.chat{
    display:flex;
    flex-direction:column;
    gap:10px;
}
.bubble{
    padding:14px 16px;
    border-radius:12px;
    max-width:90%;
    line-height:1.6;
    box-shadow:0 8px 25px rgba(0,0,0,.6);
}
.user{
    align-self:flex-end;
    background:rgba(255,255,255,.05);
}
.ai{
    align-self:flex-start;
    background:linear-gradient(90deg,rgba(0,246,255,.12),rgba(124,60,255,.05));
}
.loader{
    height:3px;
    background:linear-gradient(90deg,transparent,var(--accent),transparent);
    background-size:200% 100%;
    animation:scan 1.6s linear infinite;
    border-radius:4px;
}
@keyframes scan{
    0%{background-position:200%}
    100%{background-position:-200%}
}
</style>
""", unsafe_allow_html=True)

# ================= UTILS =================
def check_membership(name: str) -> bool:
    name = name.strip().lower()
    try:
        for g in ["iea_grup_1", "iea_grup_2"]:
            r = requests.get(f"{FIREBASE_URL}/{g}.json", timeout=8)
            if r.status_code != 200:
                continue
            data = r.json()
            if not data:
                continue
            for k in data:
                if data[k].get("n", "").lower() == name:
                    return True
        return False
    except:
        return False

def add_msg(role, content):
    st.session_state.msgs.append({"role": role, "content": content})

# ================= STATE =================
if "auth" not in st.session_state:
    st.session_state.auth = False
if "msgs" not in st.session_state:
    st.session_state.msgs = []
if "last_msg" not in st.session_state:
    st.session_state.last_msg = 0.0
if "voice" not in st.session_state:
    st.session_state.voice = True

# ================= HERO =================
st.markdown("""
<div class="hero">
    <h1>COSMOS</h1>
    <p>BEYOND IMAGINATION</p>
</div>
""", unsafe_allow_html=True)

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("### ⚙️ SETTINGS")
    st.session_state.voice = st.checkbox("Voice Output", value=st.session_state.voice)
    st.markdown("Commands:")
    st.code("/clear\n/help\n/about")
    if st.button("EXIT"):
        st.session_state.auth = False
        st.rerun()

# ================= LOGIN =================
if not st.session_state.auth:
    _, mid, _ = st.columns([1,2,1])
    with mid:
        name = st.text_input("IDENTIFICATION CODE", placeholder="Your name...")
        if st.button("AUTHORIZE"):
            if name and check_membership(name):
                st.session_state.auth = True
                st.session_state.user = name.upper()
                st.session_state.msgs = []
                add_msg("ai", f"Selamat datang {st.session_state.user}. COSMOS online.")
                st.rerun()
            else:
                st.error("ACCESS DENIED")
    st.stop()

# ================= TERMINAL =================
st.markdown(
    f"<div style='color:var(--accent);font-weight:700;margin-bottom:10px;'>"
    f"{st.session_state.user} — COSMOS ACTIVE</div>",
    unsafe_allow_html=True
)

chat_box = st.empty()

def render_chat():
    out = ["<div class='chat'>"]
    for m in st.session_state.msgs:
        cls = "user" if m["role"] == "user" else "ai"
        txt = html.escape(m["content"]).replace("\n", "<br>")
        out.append(f"<div class='bubble {cls}'>{txt}</div>")
    out.append("</div>")
    chat_box.markdown("".join(out), unsafe_allow_html=True)

render_chat()

prompt = st.chat_input("Speak to COSMOS...")
if prompt:
    if time.time() - st.session_state.last_msg < 1.5:
        st.warning("Slow down.")
        st.stop()
    st.session_state.last_msg = time.time()

    if prompt.startswith("/clear"):
        st.session_state.msgs = []
        add_msg("ai", "Chat cleared.")
        st.rerun()

    if prompt.startswith("/help"):
        add_msg("ai", "Commands:\n/clear - clear chat\n/help - help\n/about - about COSMOS")
        st.stop()

    if prompt.startswith("/about"):
        add_msg("ai", "COSMOS adalah AI terminal privat untuk komunitas IEA.")
        st.stop()

    add_msg("user", prompt)
    render_chat()

    loader = st.empty()
    loader.markdown("<div class='loader'></div>", unsafe_allow_html=True)

    try:
        from langchain_groq import ChatGroq
        from langchain_core.messages import SystemMessage, HumanMessage

        llm = ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name="llama-3.3-70b-versatile",
            temperature=0.7
        )

        history = st.session_state.msgs[-6:]
        msgs = [SystemMessage(content="You are COSMOS AI for IEA. Use Bahasa Indonesia. Futuristic, calm, professional.")]
        for h in history:
            if h["role"] == "user":
                msgs.append(HumanMessage(content=h["content"]))
            else:
                msgs.append(SystemMessage(content=h["content"]))

        res = llm.invoke(msgs).content
        loader.empty()
        add_msg("ai", res)
        render_chat()

        if st.session_state.voice:
            safe = res.replace("'", "").replace("\n", " ")
            st.components.v1.html(f"""
            <script>
            var u = new SpeechSynthesisUtterance('{safe}');
            u.lang='id-ID';
            window.speechSynthesis.speak(u);
            </script>
            """, height=0)

    except Exception:
        loader.empty()
        st.error("COSMOS connection failed")
