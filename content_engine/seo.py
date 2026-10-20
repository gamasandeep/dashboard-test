"""Local SEO pass, scored against brand-os/content/seo-checklist.md.

Stands in for Surfer's content score until Surfer is connected (see TOOLS.md).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .models import Brief, Draft

CTA_WORDS = ("book", "save", "follow", "dm", "message", "comment", "link in bio", "try", "visit", "read", "share", "come in")


@dataclass
class SEOReport:
    score: int
    passed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)


def _words(text: str) -> list[str]:
    return re.findall(r"[\w']+", text.lower())


def _contains(text: str, phrase: str) -> bool:
    return bool(phrase) and phrase.lower() in text.lower()


def score(brief: Brief, draft: Draft, hook: str = "") -> SEOReport:
    full = "\n".join([hook, draft.title, draft.body, draft.caption])
    first_100 = " ".join(_words("\n".join([hook, draft.title, draft.body]))[:100])
    sentences = [s for s in re.split(r"[.!?]+\s|\n+", draft.body) if _words(s)]
    avg_len = sum(len(_words(s)) for s in sentences) / max(len(sentences), 1)

    checks: list[tuple[str, int, bool]] = [
        ("Primary keyword in the hook or title", 20, _contains(hook + " " + draft.title, brief.primary_keyword)),
        ("Primary keyword in the first 100 words", 20, _contains(first_100, brief.primary_keyword)),
        ("At least one secondary keyword", 15, any(_contains(full, k) for k in brief.secondary_keywords)),
        ("Readable: average sentence under 20 words", 15, avg_len < 20),
        ("Has a call to action", 15, any(w in full.lower() for w in CTA_WORDS) or _contains(full, brief.call_to_action)),
    ]
    if brief.format == "blog":
        checks.append(("Meta description of 140-160 characters", 15, 140 <= len(draft.meta_description) <= 160))
    else:
        checks.append(("3-5 relevant hashtags", 15, 3 <= len(draft.hashtags) <= 5))

    total = sum(w for _, w, _ in checks)
    got = sum(w for _, w, ok in checks if ok)
    return SEOReport(
        score=round(100 * got / total),
        passed=[n for n, _, ok in checks if ok],
        failed=[n for n, _, ok in checks if not ok],
    )
