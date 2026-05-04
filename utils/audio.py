import io
import tempfile
import streamlit as st
from gtts import gTTS
from pydub import AudioSegment
from pydub.utils import which

# Ensure pydub finds ffmpeg
AudioSegment.converter = which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"

def speak(text: str):
    """Convert text to speech and autoplay."""
    if not st.session_state.get("voice_enabled", True):
        return
    try:
        clean = (text
                 .replace("✅", "").replace("❌", "").replace("💎", "")
                 .replace("⚠️", "").replace("**", "").replace("#", ""))
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            gTTS(clean[:600], lang="en", slow=False).write_to_file(f.name)
            st.audio(f.name, format="audio/mp3", autoplay=True)
    except Exception:
        pass

@st.cache_resource
def _load_whisper():
    """Load Whisper model once and cache it."""
    import whisper
    return whisper.load_model("base")

def transcribe_audio(audio_bytes: bytes) -> str | None:
    """Convert recorded audio bytes to text using Whisper."""
    if not audio_bytes:
        return None
    try:
        # Try formats the browser might send (WebM, Opus, WAV)
        audio_segment = None
        for fmt in ["webm", "ogg", "wav", None]:
            try:
                kwargs = {"format": fmt} if fmt else {}
                audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), **kwargs)
                break
            except Exception:
                continue

        if audio_segment is None:
            st.error("Could not decode audio — please try again.")
            return None

        audio_segment = audio_segment.set_channels(1).set_frame_rate(16000)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            audio_segment.export(f.name, format="wav")
            tmp_path = f.name

        with st.spinner("🎤 Transcribing…"):
            model = _load_whisper()
            result = model.transcribe(tmp_path, language="en")
            text = result["text"].strip()
            return text if text else None

    except Exception as e:
        st.error(f"Speech error: {e}")
        return None
