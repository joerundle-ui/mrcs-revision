import streamlit as st
import datetime

TOPICS = {
    "anatomy":       {"name": "Applied Surgical Anatomy",   "icon": "🦴"},
    "physiology":    {"name": "Physiology & Critical Care", "icon": "❤️"},
    "pathology":     {"name": "Surgical Pathology",         "icon": "🔬"},
    "perioperative": {"name": "Perioperative Care",         "icon": "💉"},
    "emergency":     {"name": "Emergency & Trauma",         "icon": "🚨"},
    "oncology":      {"name": "Surgical Oncology",          "icon": "🎗️"},
    "communication": {"name": "Communication & Ethics",     "icon": "💬"},
}

EXAM_STATIONS = [
    {"topic": "anatomy",       "label": "Applied Anatomy"},
    {"topic": "physiology",    "label": "Physiology & Critical Care"},
    {"topic": "pathology",     "label": "Surgical Pathology"},
    {"topic": "perioperative", "label": "Perioperative Care"},
    {"topic": "emergency",     "label": "Emergency & Trauma"},
    {"topic": "oncology",      "label": "Surgical Oncology"},
    {"topic": "anatomy",       "label": "Clinical Anatomy"},
    {"topic": "communication", "label": "Communication Skills"},
    {"topic": "communication", "label": "Ethics & Consent"},
]

STATION_TIME = 7 * 60  # 7 minutes in seconds

def init_state():
    st.session_state.setdefault("page", "tutor")
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("topic", None)
    st.session_state.setdefault("answer_attempts", 0)
    st.session_state.setdefault("performance", {t: {"concepts": {}} for t in TOPICS})
    st.session_state.setdefault("sessions", [])
    # Exam state
    st.session_state.setdefault("exam_active", False)
    st.session_state.setdefault("exam_station", 0)
    st.session_state.setdefault("exam_start_time", None)
    st.session_state.setdefault("exam_station_start", None)
    st.session_state.setdefault("exam_results", [])
    st.session_state.setdefault("exam_complete", False)
    st.session_state.setdefault("exam_question", None)
    st.session_state.setdefault("exam_answer", "")
    st.session_state.setdefault("exam_feedback", None)

def get_weak_areas():
    weak = []
    for topic, data in st.session_state.performance.items():
        for concept, perf in data["concepts"].items():
            if perf["total"] >= 2:
                pct = int(perf["correct"] / perf["total"] * 100)
                if pct < 70:
                    weak.append({
                        "topic": topic,
                        "topic_name": TOPICS[topic]["name"],
                        "concept": concept,
                        "pct": pct,
                        "correct": perf["correct"],
                        "total": perf["total"],
                    })
    return sorted(weak, key=lambda x: x["pct"])

def record_concept(topic, concept, correct: bool):
    if concept not in st.session_state.performance[topic]["concepts"]:
        st.session_state.performance[topic]["concepts"][concept] = {"correct": 0, "total": 0}
    st.session_state.performance[topic]["concepts"][concept]["total"] += 1
    if correct:
        st.session_state.performance[topic]["concepts"][concept]["correct"] += 1

def topic_score(topic_id):
    concepts = st.session_state.performance[topic_id]["concepts"]
    if not concepts:
        return None
    total_q = sum(v["total"] for v in concepts.values())
    total_c = sum(v["correct"] for v in concepts.values())
    return int(total_c / total_q * 100) if total_q else None

def overall_score():
    scores = [topic_score(t) for t in TOPICS if topic_score(t) is not None]
    return int(sum(scores) / len(scores)) if scores else None
