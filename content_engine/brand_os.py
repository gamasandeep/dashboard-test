"""Loads the Brand OS files the Content Engine reads before it writes."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Files sent to Claude as the brand's voice, in this order.
VOICE_FILES = [
    "owner/brand-voice.md",
    "brand-os/brand-brain/voice-guide.md",
    "brand-os/brand-brain/tone-rules.md",
    "brand-os/brand-brain/positioning.md",
    "brand-os/brand-brain/messaging-bank.md",
    "owner/positioning.md",
    "owner/approval-bar.md",
]
CONTENT_FILES = [
    "brand-os/content/brief-templates.md",
    "brand-os/content/hook-bank.md",
    "brand-os/content/seo-checklist.md",
    "brand-os/signals-seo/keyword-map.md",
    "brand-os/signals-seo/serp-rules.md",
    "brand-os/social/channel-playbooks.md",
    "brand-os/social/hashtag-rules.md",
]


@dataclass
class KeywordTarget:
    topic: str
    primary: str
    secondary: list[str] = field(default_factory=list)


@dataclass
class BrandOS:
    root: Path
    docs: dict[str, str]
    banned_phrases: list[str]
    keyword_map: list[KeywordTarget]

    @classmethod
    def load(cls, root: Path) -> "BrandOS":
        docs = {}
        for rel in VOICE_FILES + CONTENT_FILES:
            path = root / rel
            if path.exists():
                docs[rel] = path.read_text()
        return cls(
            root=root,
            docs=docs,
            banned_phrases=_banned_phrases(docs),
            keyword_map=_keyword_map(docs.get("brand-os/signals-seo/keyword-map.md", "")),
        )

    def voice_context(self) -> str:
        return _join(self.docs, VOICE_FILES)

    def content_context(self) -> str:
        return _join(self.docs, CONTENT_FILES)

    def keywords_for(self, topic: str) -> KeywordTarget | None:
        t = topic.lower().strip()
        for k in self.keyword_map:
            if k.topic.lower() == t or k.primary.lower() in t:
                return k
        return None


def _join(docs: dict[str, str], order: list[str]) -> str:
    return "\n\n".join(f'<file path="{p}">\n{docs[p].strip()}\n</file>' for p in order if p in docs)


def _section_items(text: str, heading: str) -> list[str]:
    """Bullet items under a markdown heading such as '## Never' or '## Banned phrases'."""
    m = re.search(rf"^##\s+{re.escape(heading)}\s*$(.*?)(?=^#|\Z)", text, re.M | re.S | re.I)
    if not m:
        return []
    return [line[2:].strip() for line in m.group(1).splitlines() if line.startswith("- ")]


def _banned_phrases(docs: dict[str, str]) -> list[str]:
    phrases = _section_items(docs.get("brand-os/brand-brain/tone-rules.md", ""), "Banned phrases")
    return sorted({p.lower() for p in phrases if p})


def _keyword_map(text: str) -> list[KeywordTarget]:
    rows = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower() == "topic" or set(cells[0]) <= {"-", " "}:
            continue
        secondary = [s.strip() for s in cells[2].split(",") if s.strip()]
        rows.append(KeywordTarget(topic=cells[0], primary=cells[1], secondary=secondary))
    return rows
