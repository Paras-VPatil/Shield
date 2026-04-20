import re

STOP_WORDS = {
    "what", "which", "how", "should", "would", "could", "is", "are", "the", "for", "and", "this", "that", "with", "from", "into", "your", "their", "must", "will", "can"
}

def _question_keywords(question: str) -> set[str]:
    tokens = re.findall(r"[A-Za-z0-9\-]+", question.lower())
    return {token for token in tokens if len(token) > 3 and token not in STOP_WORDS}

def _is_reasonable_question(question: str) -> bool:
    cleaned = question.strip()
    if len(cleaned) < 12:
        return False
    if not cleaned.endswith("?"):
        return False
    tokens = [token.strip(" ,.:;!?").lower() for token in cleaned.split()]
    keywords = [token for token in tokens if token and token not in STOP_WORDS]
    return len(keywords) >= 3

q = "Can doctors modify medical records?"
print(f"Question: {q}")
print(f"Keywords: {_question_keywords(q)}")
print(f"Reasonable: {_is_reasonable_question(q)}")

record_keywords = ["medical record", "records", "ehr", "emr", "chart"]
lower = "build a healthcare platform where patients can access medical records, doctors and admins can log in, and ai analytics provide insights."
match = any(keyword in lower for keyword in record_keywords)
print(f"Match record_keywords: {match}")
