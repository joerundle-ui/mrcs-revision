import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.state import init_state, get_weak_areas, TOPICS
from utils.ai import stream_tutor_response
from utils.audio import speak
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Tutor · MRCS", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
.stApp { background-color: #0D1B2A; font-family: 'Inter', sans-serif; }
[data-testid="stSidebar"] { background-color: #0A1628 !important; border-right: 1px solid #1E3A5F; }
[data-testid="stChatMessage"] { background: #112240 !important; border-radius: 12px !important; border: 1px solid #1E3A5F !important; margin-bottom: 0.5rem; }
p, li, span { color: #E8EEF6; }
h1, h2, h3 { color: white !important; }
.stButton > button { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

init_state()

OPENERS = {
    "anatomy":       "Give me a clinical anatomy scenario — ask me about structures at risk or surgical approach. No multiple choice.",
    "physiology":    "Give me a physiology question with an HDU or A&E scenario. No multiple choice.",
    "pathology":     "Give me a pathology question — wound healing, inflammation, or neoplasia. No multiple choice.",
    "perioperative": "Give me a perioperative scenario — pre-op or post-op ward situation. No multiple choice.",
    "emergency":     "Give me an emergency surgery scenario — on call at 2am. No multiple choice.",
    "oncology":      "Give me an oncology question — staging, management, or investigations. No multiple choice.",
    "communication": "Set up a communication station — consent, bad news, or a complaint. I'll respond as the patient.",
}

# ── SIDEBAR ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:0.5rem 0 1rem;'>
        <div style='font-size:2rem'>🎓</div>
        <div style='color:white; font-weight:700;'>Tutor Mode</div>
        <div style='color:#7B9CBB; font-size:0.8rem;'>Dr. Sarah Mitchell</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("Home.py")
    if st.button("📋 Exam Simulation", use_container_width=True):
        st.switch_page("pages/2_Exam.py")
    if st.button("📊 Progress", use_container_width=True):
        st.switch_page("pages/3_Progress.py")

    st.divider()
    st.markdown("<div style='color:#7B9CBB; font-size:0.8rem; text-transform:uppercase; letter-spacing:1px;'>Topic</div>", unsafe_allow_html=True)

    for tid, t in TOPICS.items():
        is_active = st.session_state.topic == tid
        if st.button(f"{t['icon']} {t['name']}", key=f"t_{tid}", use_container_width=True,
                     type="primary" if is_active else "secondary"):
            st.session_state.topic = tid
            st.session_state.messages = []
            st.session_state.answer_attempts = 0
            st.session_state.messages.append({"role": "user", "content": OPENERS[tid]})
            st.rerun()

    st.divider()
    voice = st.toggle("🔊 Voice responses", value=st.session_state.get("voice_enabled", False))
    st.session_state.voice_enabled = voice

    weak = get_weak_areas()
    if weak:
        st.markdown("<div style='color:#F44336; font-size:0.8rem; font-weight:600; margin-top:0.5rem;'>🎯 Weak Areas</div>", unsafe_allow_html=True)
        for w in weak[:3]:
            pct = w["pct"]
            colour = "#F44336" if pct < 50 else "#FFB300"
            st.markdown(f"<div style='color:{colour}; font-size:0.8rem;'>• {w['concept']} ({pct}%)</div>", unsafe_allow_html=True)

    if st.button("🔄 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.topic = None
        st.rerun()

# ── MAIN ───────────────────────────────────────────────────────────────────
if not st.session_state.topic:
    st.markdown("""
    <div style='background:#112240; border-radius:16px; padding:2rem; border:1px solid #1E3A5F; text-align:center; margin-top:2rem;'>
        <div style='font-size:3rem; margin-bottom:1rem;'>👩‍⚕️</div>
        <h2 style='color:white; margin:0 0 0.5rem;'>Dr. Sarah Mitchell</h2>
        <p style='color:#7B9CBB;'>Consultant Surgeon · MRCS Part B Tutor</p>
        <p style='color:#E8EEF6; margin-top:1rem;'>Pick a topic from the sidebar to start a conversation.<br>You can type or speak your answers.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    topic_name = TOPICS[st.session_state.topic]["name"]
    st.markdown(f"<h3 style='color:white; margin-bottom:1rem;'>👩‍⚕️ {topic_name}</h3>", unsafe_allow_html=True)

    # Display messages
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user" and i == 0:
            continue  # hide the opener prompt
        with st.chat_message(msg["role"], avatar="🧑‍⚕️" if msg["role"] == "user" else "👩‍⚕️"):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("should_speak") and voice:
                speak(msg["content"])

    # Auto-respond if last message is from user
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        weak = get_weak_areas()
        with st.chat_message("assistant", avatar="👩‍⚕️"):
            response = st.write_stream(
                stream_tutor_response(st.session_state.messages, st.session_state.topic, weak)
            )
        is_first_reply = len(st.session_state.messages) <= 2
        st.session_state.messages.append({"role": "assistant", "content": response, "should_speak": not is_first_reply})
        st.rerun()

    # Input area
    st.markdown("<br>", unsafe_allow_html=True)
    col_mic, col_text = st.columns([1, 4])

    with col_mic:
        if st.button("🎤 Speak", key="mic_btn_tutor"):
            result = streamlit_js_eval(js_expressions="""
                new Promise((resolve, reject) => {
                    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
                    if (!SR) { reject('Use Chrome'); return; }
                    const r = new SR();
                    r.lang = 'en-GB'; r.continuous = false; r.interimResults = false;
                    r.onresult = e => resolve(e.results[0][0].transcript);
                    r.onerror = e => reject(e.error);
                    r.start();
                })
            """, key="speech_result_tutor")
            if result:
                st.session_state.messages.append({"role": "user", "content": result})
                st.rerun()

    with col_text:
        if prompt := st.chat_input("Type your answer…"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.rerun()
