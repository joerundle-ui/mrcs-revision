import streamlit as st
import time
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.state import init_state, EXAM_STATIONS, STATION_TIME, TOPICS
from utils.ai import get_exam_question, mark_exam_answer
from streamlit_js_eval import streamlit_js_eval

def _render_speech_button(context: str):
    """Render a speech-to-text button using browser Web Speech API."""
    if st.button("🎤 Speak", key=f"mic_btn_{context}"):
        result = streamlit_js_eval(js_expressions="""
            new Promise((resolve, reject) => {
                const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SR) { reject('Speech not supported — use Chrome'); return; }
                const r = new SR();
                r.lang = 'en-GB';
                r.continuous = false;
                r.interimResults = false;
                r.onresult = e => resolve(e.results[0][0].transcript);
                r.onerror = e => reject(e.error);
                r.start();
            })
        """, key=f"speech_result_{context}")
        if result:
            key = f"{context}_text_input" if context == "exam" else None
            if key:
                current = st.session_state.get(key, "")
                st.session_state[key] = (current + " " + result).strip()
            st.session_state[f"_speech_{context}"] = result
            st.rerun()

try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except ImportError:
    HAS_AUTOREFRESH = False

st.set_page_config(page_title="Exam · MRCS", page_icon="📋", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=dash');
.stApp { background-color: #0D1B2A; font-family: 'Inter', sans-serif; }
[data-testid="stSidebar"] { background-color: #0A1628 !important; border-right: 1px solid #1E3A5F; }
.exam-card { background: #112240; border-radius: 16px; padding: 1.5rem; border: 1px solid #1E3A5F; margin-bottom: 1rem; }
.timer-normal { font-size: 3.5rem; font-weight: 700; color: white; text-align: center; font-variant-numeric: tabular-nums; }
.timer-urgent { font-size: 3.5rem; font-weight: 700; color: #FF5252; text-align: center; font-variant-numeric: tabular-nums; animation: pulse 1s infinite; }
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.6; } }
.station-row { display: flex; gap: 8px; justify-content: center; margin: 1rem 0; }
.dot { width:32px; height:32px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; font-size:0.75rem; font-weight:700; }
.dot-done   { background:#00C853; color:white; }
.dot-active { background:#2979FF; color:white; }
.dot-todo   { background:#1E3A5F; color:#7B9CBB; }
.score-card { background:#112240; border-radius:16px; padding:2rem; border:1px solid #1E3A5F; text-align:center; }
.result-correct  { background:rgba(0,200,83,0.1);  border-left:4px solid #00C853; padding:0.5rem 1rem; border-radius:8px; margin:0.5rem 0; }
.result-partial  { background:rgba(255,179,0,0.1); border-left:4px solid #FFB300; padding:0.5rem 1rem; border-radius:8px; margin:0.5rem 0; }
.result-incorrect{ background:rgba(244,67,54,0.1); border-left:4px solid #F44336; padding:0.5rem 1rem; border-radius:8px; margin:0.5rem 0; }
p, li { color: #E8EEF6; }
h1,h2,h3 { color:white !important; }
</style>
""", unsafe_allow_html=True)

init_state()

# Only autorefresh when actively answering a question (not on lobby or feedback screens)
_should_refresh = (
    st.session_state.get("exam_active", False)
    and not st.session_state.get("exam_feedback")
    and st.session_state.get("exam_question") is not None
)

# ── SIDEBAR ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:0.5rem 0 1rem;'>
        <div style='font-size:2rem'>📋</div>
        <div style='color:white; font-weight:700;'>Exam Mode</div>
        <div style='color:#7B9CBB; font-size:0.8rem;'>9 Stations · 7 min each</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🏠 Home",           use_container_width=True): st.switch_page("Home.py")
    if st.button("🎓 Tutor Mode",     use_container_width=True): st.switch_page("pages/1_Tutor.py")
    if st.button("📊 Progress",       use_container_width=True): st.switch_page("pages/3_Progress.py")

    if st.session_state.exam_active:
        st.divider()
        station = st.session_state.exam_station
        st.markdown(f"<div style='color:#7B9CBB; font-size:0.85rem;'>Station {station+1} / 9</div>", unsafe_allow_html=True)
        st.progress((station) / 9)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚠️ Abandon Exam", use_container_width=True):
            st.session_state.exam_active = False
            st.session_state.exam_complete = False
            st.session_state.exam_results = []
            st.session_state.exam_station = 0
            st.session_state.exam_question = None
            st.rerun()

# ── STATE A: pre-exam lobby ─────────────────────────────────────────────────
if not st.session_state.exam_active and not st.session_state.exam_complete:
    st.markdown("""
    <div style='max-width:650px; margin:3rem auto;'>
        <div class='score-card'>
            <div style='font-size:3rem; margin-bottom:1rem;'>📋</div>
            <h2>MRCS Part B Exam Simulation</h2>
            <p style='color:#7B9CBB; font-size:1rem;'>9 stations · 7 minutes each · 63 minutes total</p>
            <hr style='border-color:#1E3A5F; margin:1.5rem 0;'>
            <div style='display:flex; justify-content:space-around; margin-bottom:1.5rem;'>
                <div><div style='font-size:1.5rem;'>🦴</div><div style='color:#E8EEF6; font-size:0.85rem;'>Anatomy ×2</div></div>
                <div><div style='font-size:1.5rem;'>❤️</div><div style='color:#E8EEF6; font-size:0.85rem;'>Physiology ×1</div></div>
                <div><div style='font-size:1.5rem;'>🔬</div><div style='color:#E8EEF6; font-size:0.85rem;'>Pathology ×1</div></div>
                <div><div style='font-size:1.5rem;'>💉</div><div style='color:#E8EEF6; font-size:0.85rem;'>Periop ×1</div></div>
                <div><div style='font-size:1.5rem;'>🚨</div><div style='color:#E8EEF6; font-size:0.85rem;'>Emergency ×1</div></div>
                <div><div style='font-size:1.5rem;'>💬</div><div style='color:#E8EEF6; font-size:0.85rem;'>Comms ×2</div></div>
                <div><div style='font-size:1.5rem;'>🎗️</div><div style='color:#E8EEF6; font-size:0.85rem;'>Oncology ×1</div></div>
            </div>
            <p style='color:#7B9CBB; font-size:0.85rem;'>✅ Correct = 1pt &nbsp;·&nbsp; ⚠️ Partial = 0.5pt &nbsp;·&nbsp; ❌ Incorrect = 0pt</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([2, 1, 2])[1]
    with col:
        if st.button("🚀 Start Exam", use_container_width=True, type="primary"):
            st.session_state.exam_active = True
            st.session_state.exam_complete = False
            st.session_state.exam_station = 0
            st.session_state.exam_results = []
            st.session_state.exam_question = None
            st.session_state.exam_answer = ""
            st.session_state.exam_feedback = None
            st.session_state.exam_station_start = time.time()
            st.rerun()

# ── STATE B: active exam ─────────────────────────────────────────────────────
elif st.session_state.exam_active:

    station_idx = st.session_state.exam_station
    station = EXAM_STATIONS[station_idx]

    # BUG FIX 2: Load question then rerun so autorefresh starts on next render
    if not st.session_state.exam_question:
        with st.spinner(f"⏳ Loading Station {station_idx + 1} of 9…"):
            st.session_state.exam_question = get_exam_question(station["topic"], station["label"])
            st.session_state.exam_station_start = time.time()
            st.session_state.exam_answer = ""
            st.session_state.exam_feedback = None
            st.session_state.exam_result_saved = False
        st.rerun()  # rerun so _should_refresh = True and timer starts

    # BUG FIX 2: autorefresh only runs after question is loaded
    if HAS_AUTOREFRESH and _should_refresh:
        st_autorefresh(interval=1000, key="exam_refresh")

    elapsed = int(time.time() - (st.session_state.exam_station_start or time.time()))
    remaining = max(0, STATION_TIME - elapsed)
    mins, secs = divmod(remaining, 60)
    timer_class = "timer-urgent" if remaining < 60 else "timer-normal"

    # Auto-expire if time runs out
    if remaining == 0 and not st.session_state.exam_feedback:
        st.session_state.exam_feedback = {"score": 0.0, "feedback": "⏰ Time expired — no answer submitted."}
        st.rerun()

    col_q, col_timer = st.columns([3, 1])

    with col_q:
        icon = TOPICS[station["topic"]]["icon"]
        st.markdown(f"<div style='color:#7B9CBB; font-size:0.85rem; margin-bottom:0.5rem;'>Station {station_idx+1} of 9 · {icon} {station['label']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='exam-card'>{st.session_state.exam_question}</div>", unsafe_allow_html=True)

        if not st.session_state.exam_feedback:
            # Pre-fill text area with any speech result
            speech_val = st.session_state.pop("_speech_exam", "")
            default_text = st.session_state.get("exam_text_input", "") + (" " + speech_val if speech_val else "")
            default_text = default_text.strip()

            with st.form("exam_form", clear_on_submit=True):
                answer = st.text_area(
                    "Your answer:",
                    value=default_text,
                    height=180,
                    placeholder="Type your full answer here…",
                )
                col_mic, col_submit = st.columns([1, 2])
                with col_mic:
                    _render_speech_button("exam")
                with col_submit:
                    submitted = st.form_submit_button("Submit Answer →", type="primary", use_container_width=True)

            if submitted:
                answer_text = answer.strip()
                if answer_text:
                    st.session_state.exam_text_input = ""
                    st.session_state.exam_answer = answer_text
                    with st.spinner("Marking…"):
                        st.session_state.exam_feedback = mark_exam_answer(
                            st.session_state.exam_question,
                            answer_text,
                        )
                    st.session_state.exam_result_saved = False
                    st.rerun()
                else:
                    st.warning("Please write or speak an answer first.")
        else:
            # Show feedback
            fb = st.session_state.exam_feedback
            score = fb["score"]
            css_class = "result-correct" if score == 1.0 else ("result-partial" if score == 0.5 else "result-incorrect")
            icon_s = "✅" if score == 1.0 else ("⚠️" if score == 0.5 else "❌")
            st.markdown(f"<div class='{css_class}'>{icon_s} {fb['feedback']}</div>", unsafe_allow_html=True)

            # BUG FIX 1: save result only ONCE, not on every render
            if not st.session_state.get("exam_result_saved", False):
                st.session_state.exam_results.append({
                    "station": station_idx + 1,
                    "topic": station["topic"],
                    "label": station["label"],
                    "question": st.session_state.exam_question,
                    "answer": st.session_state.exam_answer,
                    "score": score,
                    "feedback": fb["feedback"],
                })
                st.session_state.exam_result_saved = True

            st.markdown("<br>", unsafe_allow_html=True)
            if station_idx + 1 < 9:
                if st.button("Next Station →", type="primary"):
                    st.session_state.exam_station += 1
                    st.session_state.exam_question = None
                    st.session_state.exam_answer = ""
                    st.session_state.exam_feedback = None
                    st.session_state.exam_text_input = ""
                    st.session_state.exam_result_saved = False
                    st.rerun()
            else:
                if st.button("🏁 Complete Exam", type="primary"):
                    st.session_state.exam_active = False
                    st.session_state.exam_complete = True
                    total = sum(r["score"] for r in st.session_state.exam_results)
                    st.session_state.sessions.append({
                        "type": "exam",
                        "score": total,
                        "max": 9,
                        "pct": int(total / 9 * 100),
                        "results": list(st.session_state.exam_results),
                    })
                    st.rerun()

    with col_timer:
        # Station progress dots
        dots_html = "<div class='station-row'>"
        for i in range(9):
            if i < station_idx:
                cls = "dot-done"
            elif i == station_idx:
                cls = "dot-active"
            else:
                cls = "dot-todo"
            dots_html += f"<div class='dot {cls}'>{i+1}</div>"
        dots_html += "</div>"
        st.markdown(dots_html, unsafe_allow_html=True)

        st.markdown(f"<div class='{timer_class}'>{mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)
        st.progress(remaining / STATION_TIME)
        st.markdown(f"<div style='text-align:center; color:#7B9CBB; font-size:0.8rem;'>Station {station_idx+1} / 9</div>", unsafe_allow_html=True)

# ── STATE C: post-exam scorecard ─────────────────────────────────────────────
elif st.session_state.exam_complete:
    results = st.session_state.exam_results
    total = sum(r["score"] for r in results)
    pct = int(total / len(results) * 100) if results else 0
    colour = "#00C853" if pct >= 70 else ("#FFB300" if pct >= 50 else "#F44336")

    st.markdown(f"""
    <div class='score-card' style='margin-bottom:1.5rem;'>
        <div style='font-size:3rem; margin-bottom:0.5rem;'>🏁</div>
        <h2>Exam Complete</h2>
        <div style='font-size:3rem; font-weight:700; color:{colour};'>{total:.1f} / 9</div>
        <div style='color:#7B9CBB; font-size:1.1rem;'>{pct}% &nbsp;·&nbsp; {"Pass ✅" if pct >= 70 else "Needs Work ❌"}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Station Breakdown")
    for r in results:
        score = r["score"]
        css = "result-correct" if score == 1.0 else ("result-partial" if score == 0.5 else "result-incorrect")
        icon = "✅" if score == 1.0 else ("⚠️" if score == 0.5 else "❌")
        topic_icon = TOPICS[r["topic"]]["icon"]
        with st.expander(f"{icon} Station {r['station']} — {topic_icon} {r['label']}  ({score}/1)"):
            st.markdown(f"**Feedback:** {r['feedback']}")
            st.markdown(f"**Your answer:** *{r['answer'] or 'No answer submitted'}*")

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 Take Another Exam", use_container_width=True, type="primary"):
            st.session_state.exam_complete = False
            st.session_state.exam_results = []
            st.session_state.exam_station = 0
            st.rerun()
    with col2:
        if st.button("🎓 Go to Tutor — Practice Weak Areas", use_container_width=True):
            st.switch_page("pages/1_Tutor.py")
