import re

QUESTION_TERMS = {
    "are",
    "covers",
    "does",
    "for",
    "how",
    "is",
    "lot",
    "many",
    "of",
    "required",
    "the",
    "this",
    "to",
    "what",
    "which",
    "with",
}


def evidence_query(question: str) -> str:
    """Keep meaningful question terms for strict full-text retrieval."""
    terms = re.findall(r"[\w-]{3,}", question.lower(), flags=re.UNICODE)
    retained = [term for term in terms if term not in QUESTION_TERMS]
    return " ".join(retained) or question
