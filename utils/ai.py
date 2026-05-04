import os
import anthropic
import streamlit as st

def _client():
    """Create Anthropic client — reads API key fresh each call."""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    return anthropic.Anthropic(api_key=key)

TUTOR_PROMPT = """You are Dr. Sarah Mitchell — a friendly Consultant Surgeon helping a junior colleague revise for MRCS Part B. You're a study buddy, not a formal examiner.

Tone: warm, encouraging, conversational — like a registrar helping an SHO over coffee.

HOW TO HAVE A REAL CONVERSATION:
- Present a short NHS clinical scenario (3-4 lines), then ask ONE clear question. Stop and wait.
- If FULLY CORRECT: celebrate briefly ("Spot on!"), give one pearl, ask if they want another or to go deeper.
- If PARTIALLY RIGHT: acknowledge what's right ("Good, you've got the diagnosis…"), ask a follow-up nudge.
- If WRONG: ask a guiding question, don't just correct ("What happens to venous return if intrathoracic pressure rises?")
- If stuck after 2 nudges: give the full explanation.

KEEP IT SHORT: 2-3 sentences per reply. One question at a time. Feel like a text conversation, not a lecture.

When giving full feedback after they get it:
- ✅ or ❌ verdict
- Brief explanation
- 💎 One clinical pearl
- ⚠️ One exam pitfall
- Then: "Shall we do another one or go deeper on this?"

Style: UK NHS (bleep, SpR, SHO, A&E), British spellings, NICE/ATLS/BOAST naturally."""

EXAM_PROMPT = """You are an MRCS Part B examiner. Generate ONE realistic exam station question.

Topic: {topic}
Station type: {station_label}

Format:
**Clinical Scenario**
[3-4 sentence UK NHS scenario]

**Question**
[One clear direct question]

No multiple choice. No hints. Keep it concise and exam-standard."""

EXAM_MARK_PROMPT = """You are an MRCS examiner marking a student's answer.

Question: {question}
Student's answer: {answer}

Mark it:
1. Score: CORRECT / PARTIAL / INCORRECT
2. In 2-3 sentences: what they got right, what they missed
3. 💎 One clinical pearl
4. ⚠️ One exam pitfall

Start with the score word on its own line."""

def stream_tutor_response(messages, topic=None, weak_areas=None):
    """Stream a tutor response, yielding text chunks."""
    system = TUTOR_PROMPT
    if topic:
        from utils.state import TOPICS
        from utils.knowledge import format_knowledge_for_prompt
        system += f"\n\nCurrent topic: {TOPICS[topic]['name']}."
        # Add relevant knowledge base content
        kb_content = format_knowledge_for_prompt(topic)
        if kb_content:
            system += kb_content
    if weak_areas:
        concepts = ", ".join([w["concept"] for w in weak_areas[:3]])
        system += f"\n\nStudent is weak on: {concepts}. If relevant to current topic, probe these gently with follow-up questions."

    with _client().messages.stream(
        model="claude-opus-4-5",
        max_tokens=400,
        system=system,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            yield text

def get_exam_question(topic, station_label):
    """Get a single exam station question."""
    prompt = EXAM_PROMPT.format(topic=topic, station_label=station_label)
    response = _client().messages.create(
        model="claude-opus-4-5",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

def mark_exam_answer(question, answer):
    """Mark an exam answer and return feedback."""
    prompt = EXAM_MARK_PROMPT.format(question=question, answer=answer)
    response = _client().messages.create(
        model="claude-opus-4-5",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.content[0].text
    if text.upper().startswith("CORRECT"):
        score = 1.0
    elif text.upper().startswith("PARTIAL"):
        score = 0.5
    else:
        score = 0.0
    return {"score": score, "feedback": text}
