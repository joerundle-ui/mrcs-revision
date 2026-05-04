import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils.state import init_state, get_weak_areas, overall_score, TOPICS

st.set_page_config(
    page_title="MRCS Part B Revision",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.stApp { background-color: #0D1B2A; font-family: 'Inter', sans-serif; }

[data-testid="stSidebar"] {
    background-color: #0A1628 !important;
    border-right: 1px solid #1E3A5F;
}

section[data-testid="stSidebarContent"] { padding-top: 1rem; }

.mrcs-header {
    background: linear-gradient(135deg, #1a3a5c, #0f2540);
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 1.5rem;
    border: 1px solid #1E3A5F;
    text-align: center;
}
.mrcs-header h1 { color: white; font-size: 2.2rem; font-weight: 700; margin: 0; }
.mrcs-header p  { color: #7B9CBB; margin: 0.5rem 0 0; font-size: 1rem; }

.nav-card {
    background: #112240;
    border-radius: 14px;
    padding: 1.5rem;
    border: 1px solid #1E3A5F;
    cursor: pointer;
    transition: all 0.2s;
    text-align: center;
    height: 160px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}
.nav-card:hover { border-color: #2979FF; background: #162A4A; }
.nav-card .icon { font-size: 2.5rem; }
.nav-card h3 { color: white; margin: 0; font-size: 1.1rem; font-weight: 600; }
.nav-card p  { color: #7B9CBB; margin: 0; font-size: 0.85rem; }

.stat-card {
    background: #112240;
    border-radius: 12px;
    padding: 1.2rem;
    border: 1px solid #1E3A5F;
    text-align: center;
}
.stat-card .val { color: white; font-size: 2rem; font-weight: 700; }
.stat-card .lbl { color: #7B9CBB; font-size: 0.8rem; margin-top: 0.2rem; }

.weak-badge {
    background: #F44336;
    color: white;
    padding: 2px 8px;
    border-radius: 99px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* Sidebar buttons */
div[data-testid="stSidebar"] .stButton > button {
    background: transparent;
    border: 1px solid #1E3A5F;
    color: #E8EEF6;
    border-radius: 10px;
    text-align: left;
    font-size: 0.9rem;
    padding: 0.6rem 1rem;
    transition: all 0.15s;
}
div[data-testid="stSidebar"] .stButton > button:hover {
    background: #162A4A;
    border-color: #2979FF;
}
div[data-testid="stSidebar"] .stButton[data-active="true"] > button {
    background: #2979FF;
    border-color: #2979FF;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    background: #112240 !important;
    border-radius: 12px !important;
    border: 1px solid #1E3A5F !important;
    margin-bottom: 0.5rem;
}

p, li, span { color: #E8EEF6; }
h1, h2, h3 { color: white !important; }
</style>
""", unsafe_allow_html=True)

init_state()

# ── SIDEBAR ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 0.5rem 0 1rem;'>
        <div style='font-size:2.5rem'>🏥</div>
        <div style='color:white; font-weight:700; font-size:1.1rem;'>MRCS Part B</div>
        <div style='color:#7B9CBB; font-size:0.8rem;'>AI Revision Tool</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='color:#7B9CBB; font-size:0.75rem; padding: 0 0 0.5rem; text-transform:uppercase; letter-spacing:1px;'>Navigation</div>", unsafe_allow_html=True)

    if st.button("🎓  Tutor Mode",       use_container_width=True, key="nav_tutor"):
        st.switch_page("pages/1_Tutor.py")
    if st.button("📋  Exam Simulation",  use_container_width=True, key="nav_exam"):
        st.switch_page("pages/2_Exam.py")
    if st.button("📊  Progress",         use_container_width=True, key="nav_progress"):
        st.switch_page("pages/3_Progress.py")

    st.divider()

    # Quick stats
    overall = overall_score()
    weak = get_weak_areas()
    total_q = sum(
        sum(c["total"] for c in st.session_state.performance[t]["concepts"].values())
        for t in TOPICS
    )

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Overall", f"{overall}%" if overall else "—")
    with col2:
        st.metric("Questions", total_q)

    if weak:
        st.markdown(f"<span class='weak-badge'>⚠️ {len(weak)} weak areas</span>", unsafe_allow_html=True)

    st.divider()
    if st.button("🔄 Reset All Data", use_container_width=True):
        for key in ["messages", "topic", "performance", "sessions",
                    "exam_active", "exam_station", "exam_results", "exam_complete"]:
            if key in st.session_state:
                del st.session_state[key]
        init_state()
        st.rerun()

# ── HOME PAGE ──────────────────────────────────────────────────────────────
st.markdown("""
<div class='mrcs-header'>
    <h1>🏥 MRCS Part B</h1>
    <p>AI-powered revision with Dr. Sarah Mitchell · Salah's Notes · PassMRCS</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class='nav-card'>
        <div class='icon'>🎓</div>
        <h3>Tutor Mode</h3>
        <p>Conversational questions with voice input & Socratic guidance</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Start Tutoring →", use_container_width=True, type="primary"):
        st.switch_page("pages/1_Tutor.py")

with col2:
    st.markdown("""
    <div class='nav-card'>
        <div class='icon'>📋</div>
        <h3>Exam Simulation</h3>
        <p>9 timed stations · 7 minutes each · Scored & reviewed</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Start Exam →", use_container_width=True):
        st.switch_page("pages/2_Exam.py")

with col3:
    st.markdown("""
    <div class='nav-card'>
        <div class='icon'>📊</div>
        <h3>Progress</h3>
        <p>Track weak areas, concept scores & improvement over time</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("View Progress →", use_container_width=True):
        st.switch_page("pages/3_Progress.py")

st.markdown("<br>", unsafe_allow_html=True)

# Stats row
s1, s2, s3, s4 = st.columns(4)
with s1:
    st.metric("Overall Score", f"{overall}%" if overall else "Not started")
with s2:
    st.metric("Questions Done", total_q)
with s3:
    exam_count = len([s for s in st.session_state.sessions if s.get("type") == "exam"])
    st.metric("Exams Taken", exam_count)
with s4:
    st.metric("Weak Areas", len(weak), delta=f"-{len(weak)} to fix" if weak else None,
              delta_color="inverse")
