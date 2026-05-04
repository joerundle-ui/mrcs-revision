import streamlit as st
import re

def speak(text: str):
    """Use browser Web Speech API for TTS — no pydub/ffmpeg needed."""
    if not st.session_state.get("voice_enabled", True):
        return
    try:
        clean = re.sub(r'[✅❌💎⚠️🎓👩‍⚕️🧑‍⚕️*#]', '', text)
        clean = clean.replace('"', '\\"').replace('\n', ' ').replace("'", "\\'")[:600]
        st.components.v1.html(f"""
            <script>
            (function() {{
                const u = new SpeechSynthesisUtterance("{clean}");
                u.lang = 'en-GB';
                u.rate = 0.95;
                window.speechSynthesis.cancel();
                window.speechSynthesis.speak(u);
            }})();
            </script>
        """, height=0)
    except Exception:
        pass
