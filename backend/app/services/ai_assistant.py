from dataclasses import dataclass
import re
from typing import Sequence


@dataclass(frozen=True)
class Source:
    title: str
    url: str
    terms: tuple[str, ...]


# Authority landing pages verified on 2026-11-03. They are links only: the
# application does not ingest their content or present them as retrieved evidence.
SOURCES = (
    Source(
        "India ERSS 112 (Government of India)",
        "https://112.gov.in/",
        ("emergency", "chest pain", "breathing", "stroke"),
    ),
    Source(
        "MedlinePlus: Medicines",
        "https://medlineplus.gov/medicines.html",
        ("medicine", "medication", "prescription", "dose", "drug"),
    ),
    Source(
        "NHS: Conditions A to Z",
        "https://www.nhs.uk/conditions/",
        ("symptom", "headache", "fever", "pain", "cough"),
    ),
)
EMERGENCY_PATTERNS = re.compile(
    r"\b(chest pain|can't breathe|cannot breathe|difficulty breathing|shortness of breath|"
    r"face drooping|arm weakness|slurred speech|stroke symptoms|unconscious|severe bleeding|"
    r"overdose|suicid(?:e|al)|kill myself|anaphylaxis)\b",
    re.I,
)
INJECTION_PATTERNS = re.compile(
    r"\b(ignore (all |the )?previous instructions|reveal (your )?system prompt|developer message|jailbreak)\b",
    re.I,
)
PRESCRIPTION_PATTERNS = re.compile(
    r"\b(prescribe|what (drug|medicine|medication).{0,30}(take|should i)|dosage for me|change my dose)\b",
    re.I,
)
DIAGNOSIS_PATTERNS = re.compile(
    r"\b(diagnose me|what (disease|condition) do i have|is this (cancer|a heart attack))\b",
    re.I,
)


def detect_emergency(message: str) -> bool:
    """Deterministic pre-provider safety screen; it does not call an LLM."""
    return bool(EMERGENCY_PATTERNS.search(message.strip()))


def emergency_response() -> tuple[str, list[Source]]:
    return (
        "Your message may describe an emergency. If you are in India, call 112 now or go to the nearest emergency department. If you are elsewhere, call your local emergency number. Do not wait for an online response.",
        [SOURCES[0]],
    )


def build_context(
    messages: Sequence[dict[str, str]],
    *,
    max_messages: int = 12,
    max_chars: int = 6000,
) -> list[dict[str, str]]:
    """Keep newest valid turns within strict bounds; callers must owner-filter first."""
    selected: list[dict[str, str]] = []
    used = 0
    for message in reversed(messages):
        role = message.get("role")
        content = message.get("content", "").strip()
        if role not in {"user", "assistant"} or not content or len(selected) >= max_messages:
            continue
        content = content[-max_chars:]
        remaining = max_chars - used
        if remaining <= 0:
            break
        content = content[-remaining:]
        selected.append({"role": role, "content": content})
        used += len(content)
    return list(reversed(selected))


def answer(
    message: str,
    context: Sequence[dict[str, str]] = (),
) -> tuple[str, bool, list[Source]]:
    text = message.strip()
    if detect_emergency(text):
        content, citations = emergency_response()
        return content, True, citations
    if INJECTION_PATTERNS.search(text):
        return (
            "I can help with general health information, symptoms, or finding a doctor. I can’t follow instructions that change my safety rules.",
            False,
            [],
        )
    if PRESCRIPTION_PATTERNS.search(text):
        return (
            "I can’t prescribe medicines or recommend a personal dose. A doctor or pharmacist can review your health history and medicines safely. If you may have taken too much, contact emergency services or your local poison centre now.",
            False,
            [SOURCES[1]],
        )
    if DIAGNOSIS_PATTERNS.search(text):
        return (
            "I can’t diagnose a condition. A clinician can assess your symptoms and medical history. I can help you organize what to share with a doctor or find a relevant specialty.",
            False,
            [SOURCES[2]],
        )

    lowered = text.casefold()
    citations = [source for source in SOURCES[1:] if any(term in lowered for term in source.terms)][:2]
    prior_assistant_question = any(
        item["role"] == "assistant" and "when this started" in item["content"].casefold()
        for item in context
    )
    if prior_assistant_question and len(text) < 120:
        response = (
            "Thanks, I’ll keep that detail with what you shared earlier in this conversation. "
            "I can’t assess what is causing the symptom. Has it become severe or rapidly worse, "
            "or are there any new symptoms you want to include?"
        )
    elif citations:
        titles = ", ".join(source.title for source in citations)
        response = (
            "I can share general information, but I can’t determine what is causing your symptoms. "
            "Consider contacting a healthcare professional, especially if symptoms are severe, worsening, or persistent. "
            f"For general reference, see: {titles}. Tell me when this started and what makes it better or worse, or I can help you find a doctor."
        )
    else:
        response = (
            "I can help organize your health question, explain general medical terms, or find a doctor. "
            "I can’t diagnose or prescribe. What symptoms or question would you like help with?"
        )
    return response, False, citations


def freshness_status() -> str:
    return "Link verified 2026-11-03; page content not ingested or clinically reviewed"
