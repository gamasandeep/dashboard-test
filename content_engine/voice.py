"""Rule-based voice gate. Runs before Claude's own voice check and can't be talked out of a hold."""
from __future__ import annotations

import re

URGENCY = ("before it's too late", "only today", "act now", "last chance", "hurry", "don't miss out")
MEDICAL = ("cure", "cures", "treats", "heals", "clinically proven")


def rule_issues(text: str, banned_phrases: list[str]) -> list[str]:
    issues = []
    lower = text.lower()
    for p in sorted(set(banned_phrases) | set(URGENCY)):
        if p and p in lower:
            issues.append(f'Banned or urgency phrase: "{p}"')
    for w in MEDICAL:
        if re.search(rf"\b{re.escape(w)}\b", lower):
            issues.append(f'Medical claim word: "{w}"')
    caps = [w for w in re.findall(r"\b[A-Z]{4,}\b", text) if w not in {"SPF", "FAQ", "HTML", "UTM"}]
    if caps:
        issues.append(f"ALL CAPS hype: {', '.join(sorted(set(caps)))}")
    if re.search(r"!{2,}", text):
        issues.append("Stacked exclamation marks")
    return issues
