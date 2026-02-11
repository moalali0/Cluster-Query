"""Clause language detection and LLM instructions for non-English clauses.

This handles clauses written in non-English languages (French law clauses,
German Rahmenvertrag terms, etc.) — NOT UI translation.
"""

LANGUAGE_INSTRUCTIONS: dict[str, str] = {
    "fr": (
        "Some clauses below are in French. "
        "Translate key legal terms into English and explain their meaning. "
        "Quote the original French where relevant."
    ),
    "de": (
        "Some clauses below are in German. "
        "Translate key legal terms into English and explain their meaning. "
        "Quote the original German where relevant."
    ),
    "es": (
        "Some clauses below are in Spanish. "
        "Translate key legal terms into English and explain their meaning. "
        "Quote the original Spanish where relevant."
    ),
    # TODO: Add more language instructions as needed
    # "zh": "...",
    # "ja": "...",
}


def detect_clause_language(text: str) -> str:
    """Detect clause language from text content. Returns ISO 639-1 code.

    # TODO: Replace with proper library (langdetect / fasttext) for production.
    #       This heuristic approach only covers common ISDA-related patterns.
    """
    lower = text.lower()
    if any(w in lower for w in ["soumise au droit", "la présente", "convention-cadre", "aux termes de"]):
        return "fr"
    if any(w in lower for w in ["unterliegt dem", "vereinbarung", "rahmenvertrag", "gemäß"]):
        return "de"
    if any(w in lower for w in ["conforme a la ley", "acuerdo marco", "obligaciones"]):
        return "es"
    return "en"


def get_language_instruction(results: list[dict]) -> str | None:
    """If any retrieved clauses are non-English, return instruction for the LLM."""
    langs = {detect_clause_language(r.get("text_content", "")) for r in results}
    non_english = langs - {"en"}
    if not non_english:
        return None
    parts = [LANGUAGE_INSTRUCTIONS.get(lang, "") for lang in sorted(non_english)]
    return " ".join(p for p in parts if p) or None
