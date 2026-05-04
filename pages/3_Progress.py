import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.state import init_state, get_weak_areas, overall_score, topic_score, TOPICS
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Progress · MRCS", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
.stApp { background-color: #0D1B2A; font-family: 'Inter', sans-serif; }
[data-testid="stSidebar"] { background-color: #0A1628 !important; border-right: 1px solid #1E3A5F; }
.metric-card { background:#112240; border-radius:14px; padding:1.2rem; border:1px solid #1E3A5F; text-align:center; }
.metric-card .val { color:white; font-size:2rem; font-weight:700; }
.metric-card .lbl { color:#7B9CBB; font-size:0.8rem; margin-top:0.2rem; }
.weak-card { background:#112240; border-radius:14px; padding:1.5rem; border-left:4px solid #F44336; border-top:1px solid #1E3A5F; border-right:1px solid #1E3A5F; border-bottom:1px solid #1E3A5F; }
p, li { color:#E8EEF6; }
h1,h2,h3 { color:white !important; }
</style>
""", unsafe_allow_html=True)

init_state()

# ── SIDEBAR ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:0.5rem 0 1rem;'>
        <div style='font-size:2rem'>📊</div>
        <div style='color:white; font-weight:700;'>Progress</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🏠 Home",          use_container_width=True): st.switch_page("Home.py")
    if st.button("🎓 Tutor Mode",    use_container_width=True): st.switch_page("pages/1_Tutor.py")
    if st.button("📋 Exam Simulation", use_container_width=True): st.switch_page("pages/2_Exam.py")

# ── MAIN ───────────────────────────────────────────────────────────────────
st.markdown("<h2 style='color:white;'>📊 Your Progress</h2>", unsafe_allow_html=True)

overall = overall_score()
weak = get_weak_areas()
total_q = sum(
    sum(c["total"] for c in st.session_state.performance[t]["concepts"].values())
    for t in TOPICS
)
exam_sessions = [s for s in st.session_state.sessions if s.get("type") == "exam"]

# Top metrics
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Overall Score", f"{overall}%" if overall else "—", help="Average across all topics")
with c2:
    st.metric("Questions Done", total_q)
with c3:
    st.metric("Exams Taken", len(exam_sessions))
with c4:
    st.metric("Weak Areas", len(weak), delta=f"{len(weak)} need work" if weak else "All good!",
              delta_color="inverse")

st.markdown("<br>", unsafe_allow_html=True)

# Topic performance chart
st.markdown("### Performance by Topic")
topic_data = []
for tid, t in TOPICS.items():
    score = topic_score(tid)
    concepts = st.session_state.performance[tid]["concepts"]
    total = sum(c["total"] for c in concepts.values())
    topic_data.append({
        "topic": f"{t['icon']} {t['name']}",
        "score": score if score is not None else 0,
        "questions": total,
        "has_data": score is not None,
    })

if any(d["has_data"] for d in topic_data):
    fig = go.Figure()
    for d in topic_data:
        colour = "#00C853" if d["score"] >= 70 else ("#FFB300" if d["score"] >= 50 else "#F44336")
        opacity = 1.0 if d["has_data"] else 0.3
        fig.add_trace(go.Bar(
            x=[d["score"]],
            y=[d["topic"]],
            orientation="h",
            marker_color=colour,
            opacity=opacity,
            text=f"{d['score']}%  ({d['questions']} Qs)" if d["has_data"] else "Not started",
            textposition="outside",
            textfont=dict(color="#E8EEF6", size=12),
            showlegend=False,
        ))
    fig.add_vline(x=70, line_dash="dash", line_color="#FFB300",
                  annotation_text="Pass mark 70%", annotation_font_color="#FFB300")
    fig.update_layout(
        plot_bgcolor="#112240",
        paper_bgcolor="#112240",
        font_color="#E8EEF6",
        xaxis=dict(range=[0, 115], showgrid=False, color="#7B9CBB"),
        yaxis=dict(showgrid=False, color="#E8EEF6"),
        margin=dict(l=0, r=60, t=10, b=10),
        height=320,
        barmode="overlay",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Start answering questions in Tutor Mode to see your topic performance here.")

# Weak areas panel
if weak:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class='weak-card'>
        <h3 style='color:#F44336; margin:0 0 1rem;'>🎯 Focus Areas — These need work</h3>
    """, unsafe_allow_html=True)
    for w in weak:
        colour = "#F44336" if w["pct"] < 50 else "#FFB300"
        icon = TOPICS[w["topic"]]["icon"]
        st.markdown(f"""
        <div style='display:flex; justify-content:space-between; align-items:center;
                    padding:0.6rem 0; border-bottom:1px solid #1E3A5F;'>
            <div>
                <span style='color:#7B9CBB; font-size:0.8rem;'>{icon} {w["topic_name"]}</span><br>
                <span style='color:white; font-weight:500;'>{w["concept"]}</span>
            </div>
            <div style='text-align:right;'>
                <span style='color:{colour}; font-weight:700; font-size:1.1rem;'>{w["pct"]}%</span><br>
                <span style='color:#7B9CBB; font-size:0.75rem;'>{w["correct"]}/{w["total"]} correct</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🎓 Practise Weak Areas in Tutor Mode →", type="primary"):
        if weak:
            st.session_state.topic = weak[0]["topic"]
            st.session_state.messages = []
        st.switch_page("pages/1_Tutor.py")

# Exam history
if exam_sessions:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Exam History")
    for i, s in enumerate(reversed(exam_sessions[-10:])):
        pct = s["pct"]
        colour = "#00C853" if pct >= 70 else ("#FFB300" if pct >= 50 else "#F44336")
        st.markdown(f"""
        <div style='background:#112240; border-radius:10px; padding:0.8rem 1.2rem;
                    border:1px solid #1E3A5F; margin-bottom:0.5rem;
                    display:flex; justify-content:space-between; align-items:center;'>
            <span style='color:#7B9CBB;'>Exam {len(exam_sessions)-i}</span>
            <span style='color:{colour}; font-weight:700; font-size:1.1rem;'>{s["score"]:.1f}/9 &nbsp; ({pct}%)</span>
        </div>
        """, unsafe_allow_html=True)

    # Trend chart
    if len(exam_sessions) >= 2:
        scores = [s["pct"] for s in exam_sessions]
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            y=scores, mode="lines+markers",
            line=dict(color="#2979FF", width=2),
            marker=dict(color="#2979FF", size=8),
            fill="tozeroy", fillcolor="rgba(41,121,255,0.1)",
        ))
        fig2.add_hline(y=70, line_dash="dash", line_color="#FFB300",
                       annotation_text="70% pass mark", annotation_font_color="#FFB300")
        fig2.update_layout(
            plot_bgcolor="#112240", paper_bgcolor="#112240",
            font_color="#E8EEF6",
            xaxis=dict(title="Exam #", showgrid=False, color="#7B9CBB"),
            yaxis=dict(title="Score %", range=[0, 105], showgrid=True,
                       gridcolor="#1E3A5F", color="#7B9CBB"),
            margin=dict(l=0, r=0, t=10, b=0),
            height=220,
        )
        st.plotly_chart(fig2, use_container_width=True)
