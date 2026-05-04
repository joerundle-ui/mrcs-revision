import os
import io
import json
import tempfile
import datetime
import anthropic
import streamlit as st
import whisper
from pydub import AudioSegment
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder

# ── Config ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MRCS Part B Revision",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

TOPICS = {
    "anatomy":       {"name": "Applied Surgical Anatomy",   "icon": "🦴"},
    "physiology":    {"name": "Physiology & Critical Care", "icon": "❤️"},
    "pathology":     {"name": "Surgical Pathology",         "icon": "🔬"},
    "perioperative": {"name": "Perioperative Care",         "icon": "💉"},
    "emergency":     {"name": "Emergency & Trauma",         "icon": "🚨"},
    "oncology":      {"name": "Surgical Oncology",          "icon": "🎗️"},
    "communication": {"name": "Communication & Ethics",     "icon": "💬"},
}

SYSTEM_PROMPT = """You are Dr. Sarah Mitchell — a friendly, approachable Consultant Surgeon who is helping a junior colleague revise for MRCS Part B. Think of yourself as a knowledgeable study buddy.

Your tone is warm, encouraging, conversational — like a registrar helping an SHO over coffee. Use their name if you know it, be human.

## HOW TO HAVE A REAL CONVERSATION:

When asking questions:
- Present a short NHS clinical scenario (3-4 lines max)
- Ask ONE clear question
- Stop and wait for their answer

When they answer:
- If FULLY CORRECT: celebrate it genuinely ("Spot on!", "Exactly, you've nailed it") and ask if they want another question or want to explore further. DON'T explain everything.
- If PARTIALLY RIGHT: acknowledge what they got right first ("Good, you've got the diagnosis right..."), then ask a follow-up question to help them complete their thinking ("But what about the blood supply to that structure?")
- If ON THE WRONG TRACK: ask a nudging question to redirect them ("Hmm, what effect does increased intrathoracic pressure have on venous return?")
- If REALLY STUCK after they've tried: then give the full answer with explanation

## KEEP RESPONSES SHORT:
- One or two sentences per turn
- Ask one question at a time
- Don't dump everything at once
- Feel like a natural back-and-forth

## When giving full feedback (after they work it out or after 2-3 attempts):
- Confirm their answer is correct
- Explain the key concept
- 💎 One clinical pearl
- ⚠️ One exam pitfall
- Then ask: "Shall we do another one or explore this more?"

## Style:
- UK NHS language (bleep, SpR, SHO, A&E, theatre)
- British spellings (haematology, oesophagus, anaesthesia)
- Reference guidelines naturally (NICE, ATLS, BOAST)
- Sound like a person
"""

# ── Session state ──────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "topic" not in st.session_state:
    st.session_state.topic = None
if "performance" not in st.session_state:
    # New structure: track concepts, not just topics
    st.session_state.performance = {t: {"concepts": {}} for t in TOPICS}
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "answer_attempts" not in st.session_state:
    st.session_state.answer_attempts = 0

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
client = anthropic.Anthropic(api_key=API_KEY)

# ── Helper: Text-to-speech ─────────────────────────────────────────────────
def speak(text: str):
    """Convert text to speech and play it."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tts = gTTS(text, lang="en", slow=False)
            tts.write_to_file(f.name)
            st.audio(f.name, format="audio/mp3", autoplay=True)
    except Exception as e:
        st.warning(f"TTS error: {e}")

# ── Helper: Extract weak areas from performance ─────────────────────────────
def get_weak_areas():
    """Return list of (topic, concept, performance%) tuples sorted by weakness."""
    weak = []
    for topic, data in st.session_state.performance.items():
        for concept, perf in data["concepts"].items():
            if perf["total"] >= 2:  # only if at least 2 attempts
                pct = int(perf["correct"] / perf["total"] * 100)
                if pct < 70:
                    weak.append((topic, concept, pct, perf))
    return sorted(weak, key=lambda x: x[2])  # sort by lowest %

# ── SIDEBAR ────────────────────────────────────────────────────────────────
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
            st.session_state.messages = []
            st.session_state.current_question = None
            st.session_state.answer_attempts = 0
            st.rerun()

    st.divider()
    st.markdown("**📊 Progress**")

    weak_areas = get_weak_areas()
    if weak_areas:
        st.warning("🎯 Focus on these weak areas:")
        for topic_id, concept, pct, data in weak_areas[:3]:
            st.caption(f"**{concept}** ({pct}% — {data['correct']}/{data['total']})")
    else:
        st.success("✅ No weak areas yet — keep going!")

    st.divider()
    if st.button("🔄 Reset Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.topic = None
        st.session_state.performance = {t: {"concepts": {}} for t in TOPICS}
        st.session_state.current_question = None
        st.session_state.answer_attempts = 0
        st.rerun()

# ── MAIN AREA ──────────────────────────────────────────────────────────────
topic_name = TOPICS[st.session_state.topic]["name"] if st.session_state.topic else "Select a topic →"
st.markdown(f"### {topic_name}")

if not st.session_state.topic:
    st.info("👈 **Pick a topic to start.**\n\nDr. Mitchell will ask questions and speak her responses. She'll learn your weak areas and adapt.")
else:
    # Display chat
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🧑‍⚕️" if msg["role"] == "user" else "👩‍⚕️"):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("should_speak"):
                speak(msg["content"])

    # Auto-generate if last message is from user
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        system = SYSTEM_PROMPT
        tname = TOPICS[st.session_state.topic]["name"]
        system += f"\n\nCurrent topic: {tname}."

        weak = get_weak_areas()
        if weak:
            weak_concepts = ", ".join([c[1] for c in weak[:3]])
            system += f"\n\nStudent is weak on: {weak_concepts}. Gently probe these areas if relevant."

        with st.chat_message("assistant", avatar="👩‍⚕️"):
            with client.messages.stream(
                model="claude-opus-4-5",
                max_tokens=512,
                system=system,
                messages=st.session_state.messages,
            ) as stream:
                response = st.write_stream(stream.text_stream)

        # Mark for speaking + save
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "should_speak": True
        })
        st.session_state.pending_score = False
        st.rerun()

    st.divider()

    # Input section
    st.markdown("**Your answer:**")
    col1, col2 = st.columns([3, 1])

    with col1:
        # Voice input
        audio = mic_recorder(
            start_prompt="🎤 Speak",
            stop_prompt="⏹ Stop",
            just_once=True,
            key="mic"
        )
        if audio and audio.get("bytes"):
            try:
                audio_segment = AudioSegment.from_file(io.BytesIO(audio["bytes"]))
                audio_segment = audio_segment.set_channels(1).set_frame_rate(16000)
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    audio_segment.export(f.name, format="wav")
                    tmp_path = f.name
                with st.spinner("🎤 Transcribing..."):
                    model = whisper.load_model("base")
                    result = model.transcribe(tmp_path, language="en")
                    spoken_text = result["text"].strip()
                st.success(f"You said: *{spoken_text}*")
                st.session_state.messages.append({"role": "user", "content": spoken_text})
                st.session_state.answer_attempts += 1
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    # Text input
    if prompt := st.chat_input("Or type your answer…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.answer_attempts += 1
        st.rerun()
