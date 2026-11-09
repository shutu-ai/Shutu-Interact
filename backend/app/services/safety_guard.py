"""Safety guard — content screening per plan §5 (安全与合规设计要求).

Output side (assistant text): PII questions, unsafe topics (violence,
adult, drugs), money / medical / legal advice, secrecy and dependency
phrasing → blocked.
Input side (child text): unsafe topics and dependency phrasing →
blocked. The child asking the AI its own name is harmless and allowed.

Guard results carry an anonymous reason category only; flagged text is
never logged or persisted (spec §7.3). Patterns are intentionally
conservative — on a miss the scripted fallback keeps the chat safe and
on-topic (spec §8.3).
"""

import re
from dataclasses import dataclass

Rule = tuple[re.Pattern[str], str]


def _compile(pairs: tuple[tuple[str, str], ...]) -> tuple[Rule, ...]:
    return tuple(
        (re.compile(pattern, re.IGNORECASE), reason)
        for pattern, reason in pairs
    )


_PII: tuple[Rule, ...] = _compile((
    (r"what\s*(?:is|'s)\s*your\s*name", "asks_child_name"),
    (r"\byour\s+(?:phone|telephone)\b", "asks_phone"),
    (r"\bwhere\s+do\s+you\s+live\b", "asks_address"),
    (r"\bwhere\s+are\s+you\s+from\b", "asks_hometown"),
    (r"\b(?:what|which)\s+school\b", "asks_school"),
    (r"\bhow\s+old\s+are\s+you\b", "asks_age"),
))

_UNSAFE: tuple[Rule, ...] = _compile((
    (
        r"\b(?:kill|kills|killing|killed|gun|guns|knife|knives|blood|"
        r"bloody|death|die|dies|died|dying|sex|sexy|drug|drugs|"
        r"weapon|weapons|cigarette|cigarettes|smoke|smoking|beer|"
        r"wine|alcohol)\b",
        "unsafe_topic",
    ),
))

_MONEY: tuple[Rule, ...] = _compile((
    (
        r"\b(?:invest|investing|bitcoin|crypto|gamble|gambling|bet|"
        r"betting|loan|loans|borrow|money)\b",
        "money_advice",
    ),
))

_MEDICAL_LEGAL: tuple[Rule, ...] = _compile((
    (
        r"\b(?:medicine|hospital|doctor|sick|lawyer|sue|suing|court|"
        r"police)\b",
        "medical_legal_advice",
    ),
))

_DEPENDENCY: tuple[Rule, ...] = _compile((
    (r"keep\s+(?:this|it|our)\s+(?:a\s+)?secret", "secrecy"),
    (r"our\s+(?:little\s+)?secret", "secrecy"),
    (
        r"don'?t\s+tell\s+your\s+(?:mom|dad|parents|mother|father|teacher)",
        "secrecy",
    ),
    (r"leave\s+your\s+(?:mom|dad|parents|house|home)", "leave_guardian"),
    (r"\bonly\s+(?:i|me)\s+(?:can|will|am|understand)\b", "dependency"),
))


@dataclass(frozen=True)
class GuardResult:
    """Outcome of a guard check; reason is a short anonymous category."""

    ok: bool
    reason: str | None = None


def _first_match(text: str, rules: tuple[Rule, ...]) -> GuardResult:
    for pattern, reason in rules:
        if pattern.search(text):
            return GuardResult(ok=False, reason=reason)
    return GuardResult(ok=True)


class SafetyGuard:
    """Screens assistant output and child input against the safety rules."""

    def check_output(self, text: str) -> GuardResult:
        """Screen assistant text before it reaches the child."""
        return _first_match(text, _DEPENDENCY + _PII + _UNSAFE + _MONEY + _MEDICAL_LEGAL)

    def check_input(self, text: str) -> GuardResult:
        """Screen child text before it reaches the engine or history."""
        return _first_match(text, _UNSAFE + _DEPENDENCY)
