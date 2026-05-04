import json
import os

def load_knowledge_base():
    """Load the knowledge base JSON."""
    kb_path = os.path.join(os.path.dirname(__file__), "knowledge_base.json")
    try:
        with open(kb_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"metadata": {}, "error": "Knowledge base not found"}

def get_topic_concepts(topic: str):
    """Get all concepts for a topic."""
    kb = load_knowledge_base()
    if topic in kb:
        concepts = []
        for section, items in kb[topic].items():
            for item in items:
                concepts.append(item["concept"])
        return concepts
    return []

def get_concept_facts(topic: str, concept: str):
    """Get key facts for a specific concept."""
    kb = load_knowledge_base()
    if topic in kb:
        for section, items in kb[topic].items():
            for item in items:
                if item["concept"].lower() == concept.lower():
                    return item
    return None

def format_knowledge_for_prompt(topic: str):
    """Format knowledge base into a prompt string for the tutor."""
    kb = load_knowledge_base()
    if topic not in kb:
        return ""

    lines = [f"\n### Knowledge Base for {topic.title()}:\n"]
    for section, items in kb[topic].items():
        lines.append(f"\n**{section}**")
        for item in items:
            concept = item["concept"]
            facts = item["key_facts"]
            lines.append(f"\n• {concept}:")
            for fact in facts[:3]:  # Limit to first 3 facts per concept
                lines.append(f"  - {fact}")

    return "\n".join(lines)

def get_related_concepts(topic: str, weak_areas: list):
    """Get concepts from knowledge base that match weak areas."""
    matching_concepts = []
    for weak in weak_areas:
        if weak["topic"] == topic:
            kb_item = get_concept_facts(topic, weak["concept"])
            if kb_item:
                matching_concepts.append(kb_item)
    return matching_concepts
