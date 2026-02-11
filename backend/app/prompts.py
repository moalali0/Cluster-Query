"""Term-specific prompt registry for LLM analysis.

Each clause type (Governing Law, Netting, etc.) can have a tailored system
prompt that improves LLM output quality. Falls back to a default prompt for
unknown terms.
"""

from dataclasses import dataclass, field

from .config import settings

_SHARED_RULES = (
    "Rules:\n"
    "1. ONLY use information from the provided clusters. Never make things up.\n"
    "2. Refer to clusters by their short ID in square brackets, e.g. [7a4638ab].\n"
    "3. Do NOT give legal advice. Just describe what the data shows.\n"
    "4. Use plain English. Avoid jargon unless it comes directly from the data.\n"
    "5. For each cluster, explain:\n"
    "   - What the clause language says (quote it briefly)\n"
    "   - What was codified (the structured fields and values)\n"
    "   - If there is a query history, mention what was discussed between analyst and client\n"
    "   - Which client environment (bank) it belongs to\n"
    "6. After covering individual clusters, briefly note any patterns — e.g. if multiple banks "
    "use similar language, or if there are notable differences.\n"
    "7. Keep it concise. A few sentences per cluster is enough.\n"
    "8. If no relevant evidence is provided, say so clearly."
)

_DEFAULT_SYSTEM = (
    "You are a helpful contract precedent assistant. "
    "You explain what was found in a simple, conversational way — like a senior colleague briefing an analyst.\n\n"
    + _SHARED_RULES
)

_DEFAULT_USER_TEMPLATE = (
    "The user searched for: {criteria}\n\n"
    "Here are the clusters that matched:\n\n{context}\n\n"
    "Walk through each cluster and explain what it contains in plain language. "
    "For each one, mention:\n"
    "- What the clause says (quote briefly)\n"
    "- What was codified from it\n"
    "- Any queries or discussions that took place on it\n"
    "- Which client environment (bank) it sits in\n\n"
    "Then briefly note any patterns or differences across the clusters."
)


@dataclass
class PromptTemplate:
    term: str                    # term key or "__default__"
    version: str
    system_prompt: str
    user_template: str           # has {criteria} and {context} placeholders
    examples: list[str] = field(default_factory=list)  # few-shot examples


PROMPT_REGISTRY: dict[str, PromptTemplate] = {
    "__default__": PromptTemplate(
        term="__default__",
        version=settings.prompt_version,
        system_prompt=_DEFAULT_SYSTEM,
        user_template=_DEFAULT_USER_TEMPLATE,
        examples=[],
    ),
    "Governing Law": PromptTemplate(
        term="Governing Law",
        version=settings.prompt_version,
        system_prompt=(
            "You are a governing law precedent analyst. Focus on:\n"
            "- Jurisdiction (English Law, New York Law, French Law, etc.)\n"
            "- Whether jurisdiction is exclusive or non-exclusive\n"
            "- Exact wording variations (e.g. 'England' vs 'England and Wales')\n"
            "- Non-contractual obligations coverage\n"
            "- Court specifications and process agents\n\n"
            + _SHARED_RULES
        ),
        user_template=_DEFAULT_USER_TEMPLATE,
        examples=[
            # TODO: 2-3 example Q&A pairs showing ideal output format
        ],
    ),
    "Netting": PromptTemplate(
        term="Netting",
        version=settings.prompt_version,
        system_prompt=(
            "You are a netting clause precedent analyst. Focus on:\n"
            "- Close-out netting enforceability\n"
            "- Netting agreement scope (bilateral vs multilateral)\n"
            "- Jurisdictional netting opinions referenced\n"
            "- Payment netting mechanics\n\n"
            + _SHARED_RULES
        ),
        user_template=_DEFAULT_USER_TEMPLATE,
        examples=[
            # TODO: netting-specific few-shot examples
        ],
    ),
    "Credit Support": PromptTemplate(
        term="Credit Support",
        version=settings.prompt_version,
        system_prompt=(
            "You are a credit support precedent analyst. Focus on:\n"
            "- Collateral types (cash, securities, letters of credit)\n"
            "- Threshold and minimum transfer amounts\n"
            "- Eligible credit support and haircuts\n"
            "- Valuation and dispute mechanics\n\n"
            + _SHARED_RULES
        ),
        user_template=_DEFAULT_USER_TEMPLATE,
        examples=[
            # TODO: credit support-specific few-shot examples
        ],
    ),
    "Close-Out": PromptTemplate(
        term="Close-Out",
        version=settings.prompt_version,
        system_prompt=(
            "You are a close-out precedent analyst. Focus on:\n"
            "- Events of default triggering close-out\n"
            "- Close-out amount calculation methodology\n"
            "- Automatic vs optional early termination\n"
            "- Set-off rights and mechanics\n\n"
            + _SHARED_RULES
        ),
        user_template=_DEFAULT_USER_TEMPLATE,
        examples=[
            # TODO: close-out-specific few-shot examples
        ],
    ),
}


def get_prompt_for_term(term: str | None) -> PromptTemplate:
    """Look up a term-specific prompt, falling back to default."""
    if term:
        key_map = {k.lower(): k for k in PROMPT_REGISTRY}
        matched = key_map.get(term.lower())
        if matched:
            return PROMPT_REGISTRY[matched]
    return PROMPT_REGISTRY["__default__"]
