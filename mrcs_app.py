import os
import io
import tempfile
import anthropic
import streamlit as st
import whisper
from pydub import AudioSegment
from streamlit_mic_recorder import mic_recorder

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MRCS Part B Revision",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Topics ─────────────────────────────────────────────────────────────────
TOPICS = {
    "anatomy":       {"name": "Applied Surgical Anatomy",   "icon": "🦴"},
    "physiology":    {"name": "Physiology & Critical Care", "icon": "❤️"},
    "pathology":     {"name": "Surgical Pathology",         "icon": "🔬"},
    "perioperative": {"name": "Perioperative Care",         "icon": "💉"},
    "emergency":     {"name": "Emergency & Trauma",         "icon": "🚨"},
    "oncology":      {"name": "Surgical Oncology",          "icon": "🎗️"},
    "communication": {"name": "Communication & Ethics",     "icon": "💬"},
}

OPENERS = {
    "anatomy":       "Give me an open-ended MRCS applied anatomy question — a clinical scenario where I have to describe the anatomy, structures at risk, or surgical approach in my own words. No multiple choice.",
    "physiology":    "Give me an open-ended Physiology & Critical Care question — a realistic HDU/A&E scenario with ABG and bloods where I explain my interpretation and management. No multiple choice.",
    "pathology":     "Give me an open-ended Surgical Pathology question — ask me to explain the pathophysiology, wound healing, or neoplasia process. No multiple choice.",
    "perioperative": "Give me an open-ended perioperative care question — a ward scenario where I have to explain my assessment and management plan. No multiple choice.",
    "emergency":     "Give me an open-ended emergency surgery scenario — ask me what I would do on call at 2am and why. No multiple choice.",
    "oncology":      "Give me an open-ended Surgical Oncology question — ask me about staging, management principles, or investigations and I'll explain my reasoning. No multiple choice.",
    "communication": "Set up a communication station scenario — I will respond as if talking to the patient or relative. No multiple choice.",
}

SYSTEM_PROMPT = """You are Dr. Sarah Mitchell — a friendly, approachable Consultant Surgeon who is helping a junior colleague revise for their MRCS Part B. Think of yourself as a knowledgeable study buddy, not a formal examiner.

Your tone is warm, encouraging, and conversational — like a registrar helping an SHO over coffee. Use first names, be human, and make the revision feel enjoyable rather than stressful.

## How you ask questions:
- NEVER give multiple choice (no A–E options)
- Present a short, realistic UK NHS clinical scenario, then ask one clear open question
- Keep scenarios punchy — 3–4 lines max before the question

## How you respond to answers — BE SOCRATIC:
- If their answer is **fully correct**: celebrate it genuinely ("Spot on!", "Exactly right — you clearly know this"), give a quick pearl, and move on
- If their answer is **partially right**: acknowledge what they got right first ("Good — you've got the nerve injury, but what about the vascular supply?"), then guide with a follow-up question rather than just telling them
- If their answer is **on the wrong track**: don't just correct them — ask a nudging question to get them thinking ("Hmm, think about what's happening to the intrathoracic pressure here — what would that do to venous return?")
- If they're really stuck after 2 nudges: then give the full answer with explanation

## When you give full feedback (after they've worked it out or after 2 nudges):
- ✅ or ❌ verdict
- Full ideal answer
- 💎 One clinical pearl from real practice
- ⚠️ One exam pitfall

## Conversational rules:
- Keep replies concise — don't dump everything at once
- Ask one question at a time
- Sound like a person, not a textbook
- Use UK NHS language naturally (bleep, SpR, SHO, A&E, theatre)
- British spellings throughout (haematology, oesophagus, anaesthesia)
- Reference guidelines naturally in conversation (ATLS, NICE, BOAST) — don't list them robotically
- End with a natural question, not a formal "What would you like to do next?"
"""

# ── Session state defaults ─────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "topic" not in st.session_state:
    st.session_state.topic = None
if "performance" not in st.session_state:
    st.session_state.performance = {t: {"correct": 0, "total": 0} for t in TOPICS}
if "pending_score" not in st.session_state:
    st.session_state.pending_score = False

# ── Anthropic client ───────────────────────────────────────────────────────
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
client = anthropic.Anthropic(api_key=API_KEY)

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏥 MRCS Part B")
    st.caption("AI Revision · Salah's Notes · PassMRCS")
    st.divider()

    st.markdown("**📚 Topics**")
    for tid, t in TOPICS.items():
        label = f"{t['icon']} {t['name']}"
        is_active = st.session_state.topic == tid
        if st.button(label, key=f"btn_{tid}", use_container_width=True,
                     type="primary" if is_active else "secondary"):
            st.session_state.topic = tid
            opener = OPENERS[tid]
            st.session_state.messages.append({"role": "user", "content": opener})
            st.session_state.pending_score = False
            st.rerun()

    st.divider()
    st.markdown("**📊 Performance**")
    for tid, t in TOPICS.items():
        p = st.session_state.performance[tid]
        total = p["total"]
        correct = p["correct"]
        pct = int(correct / total * 100) if total else 0
        label = f"{t['icon']} {t['name'].split()[0]}"
        if total == 0:
            st.caption(f"{label} — not started")
        else:
            colour = "🟢" if pct >= 70 else "🟡" if pct >= 40 else "🔴"
            st.caption(f"{colour} {label}: {correct}/{total} ({pct}%)")
            st.progress(pct / 100)

    st.divider()
    if st.button("🔄 Reset Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.topic = None
        st.session_state.performance = {t: {"correct": 0, "total": 0} for t in TOPICS}
        st.session_state.pending_score = False
        st.rerun()

# ── Main area ──────────────────────────────────────────────────────────────
topic_name = TOPICS[st.session_state.topic]["name"] if st.session_state.topic else "Select a topic →"
st.markdown(f"### {topic_name}")

# Quick action buttons
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("❓ New Question"):
        if st.session_state.topic:
            st.session_state.messages.append({"role": "user", "content": "Give me a new MRCS-style question on this topic."})
            st.session_state.pending_score = False
            st.rerun()
with col2:
    if st.button("🏥 Clinical Scenario"):
        if st.session_state.topic:
            st.session_state.messages.append({"role": "user", "content": "Give me a detailed clinical scenario with investigations."})
            st.session_state.pending_score = False
            st.rerun()
with col3:
    if st.button("🦴 Anatomy Viva"):
        st.session_state.messages.append({"role": "user", "content": "Give me an applied anatomy question with surgical correlations."})
        st.session_state.pending_score = False
        st.rerun()
with col4:
    if st.button("💬 Comms Station"):
        st.session_state.messages.append({"role": "user", "content": "Set up a communication station scenario for me to practise."})
        st.session_state.pending_score = False
        st.rerun()

st.divider()

# Welcome message if no messages
if not st.session_state.messages:
    st.info("👈 **Pick a topic from the sidebar to start**, or click one of the buttons above.\n\nDr. Mitchell will give you MRCS-style questions, full explanations, and track your progress.")

# Display chat history
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"], avatar="🧑‍⚕️" if msg["role"] == "user" else "👩‍⚕️"):
        st.markdown(msg["content"])

# Auto-generate response if last message is from user
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    # Build system with topic + weak area context
    system = SYSTEM_PROMPT
    if st.session_state.topic:
        tname = TOPICS[st.session_state.topic]["name"]
        system += f"\n\nCurrent focus: **{tname}**."
    weak = [TOPICS[t]["name"] for t, p in st.session_state.performance.items()
            if p["total"] >= 2 and p["correct"] / p["total"] < 0.5]
    if weak:
        system += f"\n\nStudent is weak on: {', '.join(weak)}. Reinforce these areas."

    with st.chat_message("assistant", avatar="👩‍⚕️"):
        def stream_response():
            with client.messages.stream(
                model="claude-opus-4-5",
                max_tokens=2048,
                system=system,
                messages=st.session_state.messages,
            ) as stream:
                for text in stream.text_stream:
                    yield text

        response = st.write_stream(stream_response())

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.session_state.pending_score = True
    st.rerun()

# Auto-score based on Dr. Mitchell's response (✅ or ❌)
if st.session_state.pending_score and len(st.session_state.messages) >= 2:
    assistant_response = st.session_state.messages[-1]["content"]
    topic = st.session_state.topic or "anatomy"

    if "✅" in assistant_response or "Correct" in assistant_response:
        st.session_state.performance[topic]["total"] += 1
        st.session_state.performance[topic]["correct"] += 1
        st.session_state.pending_score = False
        st.rerun()
    elif "❌" in assistant_response or "Incorrect" in assistant_response:
        st.session_state.performance[topic]["total"] += 1
        st.session_state.pending_score = False
        st.rerun()

# 🎤 Dictation input
st.markdown("**🎤 Or speak your answer:**")
audio = mic_recorder(
    start_prompt="🎤 Click to speak",
    stop_prompt="⏹ Stop recording",
    just_once=True,
    key="mic"
)
if audio and audio.get("bytes"):
    try:
        # Convert WebM/Opus to WAV
        audio_segment = AudioSegment.from_file(io.BytesIO(audio["bytes"]))
        audio_segment = audio_segment.set_channels(1).set_frame_rate(16000)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            audio_segment.export(f.name, format="wav")
            tmp_path = f.name

        # Transcribe with Whisper (much better quality than Google Speech API)
        with st.spinner("🎤 Transcribing..."):
            model = whisper.load_model("base")
            result = model.transcribe(tmp_path, language="en")
            spoken_text = result["text"].strip()

        st.success(f"🎤 You said: *{spoken_text}*")
        st.session_state.messages.append({"role": "user", "content": spoken_text})
        st.session_state.pending_score = False
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

# Chat input
if prompt := st.chat_input("Or type your answer here…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.pending_score = False
    st.rerun()
