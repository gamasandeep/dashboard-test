"""Brief → Draft → SEO pass → Hook → Voice check. Saves the draft; never publishes."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from . import seo, voice
from .brand_os import BrandOS
from .llm import Claude
from .models import Brief, Draft, Format, Hook, VoiceVerdict

SEO_TARGET = 80
MAX_SEO_REVISIONS = 2

SYSTEM = """You are the Content Engine of a one-owner social media team. You write in the brand's voice and nothing else.
The orchestrator briefs you; you never publish. The owner owns the voice, the budget, and anything that reads like a promise.

Below is the brand's playbook. Follow it exactly. If a rule in the playbook and the request conflict, the playbook wins.

{voice}

{content}"""


@dataclass
class Request:
    topic: str
    format: Format = "reel"
    channel: str = "instagram"
    angle: str = ""
    keywords: list[str] = field(default_factory=list)


@dataclass
class Result:
    item_id: str
    status: str  # "ready" | "held"
    draft_path: str
    hook: str
    seo_score: int
    seo_failed: list[str]
    seo_fixes: list[str]
    voice_score: int
    voice_issues: list[str]
    reads_like_a_promise: bool
    usage: dict


class ContentEngine:
    def __init__(self, root: Path, claude: Claude | None = None):
        self.root = root
        self.brand = BrandOS.load(root)
        self.claude = claude
        self.system = SYSTEM.format(voice=self.brand.voice_context(), content=self.brand.content_context())

    # ---------------------------------------------------------------- steps
    def brief_prompt(self, req: Request) -> str:
        kw = self.brand.keywords_for(req.topic)
        known = ""
        if req.keywords:
            known = f"Target keywords from the orchestrator: {', '.join(req.keywords)}."
        elif kw:
            known = f"keyword-map.md row: primary '{kw.primary}', secondary {', '.join(kw.secondary) or 'none'}."
        return (
            f"Step 1 · Brief. Fill the brief template for a {req.format} on {req.channel}.\n"
            f"Topic: {req.topic}\nAngle: {req.angle or 'pick the strongest one for this audience'}\n{known}\n"
            "Pick keywords from keyword-map.md when it has a row for this topic. "
            "List any claims positioning.md says we cannot make."
        )

    def brief(self, req: Request) -> Brief:
        b = self._claude().ask(self.system, self.brief_prompt(req), Brief)
        # The orchestrator's request is authoritative for where the piece goes.
        return b.model_copy(update={"format": req.format, "channel": req.channel})

    def draft(self, brief: Brief) -> Draft:
        return self._claude().ask(
            self.system,
            "Step 2 · Draft. Write the piece from this brief using the matching brief template. "
            "Short sentences, the brand voice, no claims from claims_to_avoid.\n\n"
            f"<brief>{brief.model_dump_json(indent=2)}</brief>",
            Draft,
        )

    def revise_for_seo(self, brief: Brief, draft: Draft, report: seo.SEOReport) -> Draft:
        return self._claude().ask(
            self.system,
            f"Step 3 · SEO pass. This draft scored {report.score}/100 on seo-checklist.md. Fix only these failures, "
            "keep everything else and keep the voice:\n- " + "\n- ".join(report.failed) +
            f"\n\n<brief>{brief.model_dump_json(indent=2)}</brief>\n<draft>{draft.model_dump_json(indent=2)}</draft>",
            Draft,
        )

    def hook(self, brief: Brief, draft: Draft) -> Hook:
        return self._claude().ask(
            self.system,
            "Step 4 · Hook. Pick a pattern from hook-bank.md and write the opening line for this piece. "
            f"For video it must land in 2 seconds. Use the primary keyword '{brief.primary_keyword}' if it fits naturally.\n\n"
            f"<draft>{draft.model_dump_json(indent=2)}</draft>",
            Hook,
        )

    def voice_check(self, draft: Draft, hook: Hook) -> VoiceVerdict:
        return self._claude().ask(
            self.system,
            "Step 5 · Voice check. Compare this piece with brand-voice.md, voice-guide.md and tone-rules.md. "
            "Be strict: if it doesn't sound like the brand, on_brand is false. Flag anything that reads like a promise "
            "(prices, guarantees, results, availability) per approval-bar.md.\n\n"
            f"<hook>{hook.hook}</hook>\n<draft>{draft.model_dump_json(indent=2)}</draft>",
            VoiceVerdict,
        )

    # ---------------------------------------------------------------- run
    def run(self, req: Request) -> Result:
        brief = self.brief(req)
        draft = self.draft(brief)

        fixes: list[str] = []
        report = seo.score(brief, draft)
        for _ in range(MAX_SEO_REVISIONS):
            if report.score >= SEO_TARGET:
                break
            before = report
            draft = self.revise_for_seo(brief, draft, report)
            report = seo.score(brief, draft)
            fixes += [f for f in before.failed if f not in report.failed]

        hk = self.hook(brief, draft)
        report = seo.score(brief, draft, hk.hook)
        verdict = self.voice_check(draft, hk)

        text = "\n".join([hk.hook, draft.title, draft.body, draft.caption])
        rule_issues = voice.rule_issues(text, self.brand.banned_phrases)
        issues = rule_issues + verdict.issues
        held = bool(rule_issues) or not verdict.on_brand

        item_id = self._next_item_id(brief.format)
        path = self._save(item_id, brief, draft, hk, report, verdict, issues, held)
        status = "held" if held else "ready"
        self._log(item_id, status, report.score, verdict, path)
        if held:
            self._hold(item_id, path, issues)
        elif verdict.reads_like_a_promise:
            self._needs_ok(item_id, path)

        return Result(
            item_id=item_id, status=status, draft_path=str(path.relative_to(self.root)), hook=hk.hook,
            seo_score=report.score, seo_failed=report.failed, seo_fixes=fixes,
            voice_score=verdict.score, voice_issues=issues,
            reads_like_a_promise=verdict.reads_like_a_promise, usage=dict(self.claude.usage),
        )

    def dry_run(self, req: Request) -> dict:
        return {"model": "(not called)", "system": self.system, "step_1_prompt": self.brief_prompt(req)}

    # ---------------------------------------------------------------- files
    def _claude(self) -> Claude:
        if self.claude is None:
            self.claude = Claude()
        return self.claude

    def _next_item_id(self, fmt: str) -> str:
        d = self.root / "drafts"
        nums = [int(m.group(1)) for p in d.glob(f"{fmt}_*.md") if (m := re.match(rf"{fmt}_(\d+)", p.stem))]
        return f"{fmt}_{max(nums, default=0) + 1:03d}"

    def _save(self, item_id, brief, draft, hk, report, verdict, issues, held) -> Path:
        d = self.root / "drafts"
        d.mkdir(exist_ok=True)
        path = d / f"{item_id}.md"
        tags = " ".join(h if h.startswith("#") else f"#{h}" for h in draft.hashtags)
        meta = {
            "item": item_id, "status": "held" if held else "ready", "format": brief.format, "channel": brief.channel,
            "seo_score": report.score, "voice_score": verdict.score, "reads_like_a_promise": verdict.reads_like_a_promise,
            "created": datetime.now().isoformat(timespec="minutes"),
        }
        parts = [
            "---", *(f"{k}: {json.dumps(v)}" for k, v in meta.items()), "---", "",
            f"# {draft.title}", "", f"**Hook:** {hk.hook}", "", draft.body, "",
        ]
        if draft.caption:
            parts += ["## Caption", "", draft.caption, "", tags, ""]
        if draft.meta_description:
            parts += ["## Meta description", "", draft.meta_description, ""]
        parts += [
            "## Content Engine notes", "",
            f"- Topic: {brief.topic} · Angle: {brief.angle}",
            f"- Keywords: {brief.primary_keyword}; {', '.join(brief.secondary_keywords)}",
            f"- Hook pattern: {hk.pattern} · Alternatives: {' / '.join(hk.alternatives)}",
            f"- SEO passed: {', '.join(report.passed) or 'none'}",
            f"- SEO failed: {', '.join(report.failed) or 'none'}",
            f"- Voice issues: {'; '.join(issues) or 'none'}",
            f"- Voice fixes suggested: {'; '.join(verdict.fixes) or 'none'}",
        ]
        path.write_text("\n".join(parts) + "\n")
        return path

    def _append_row(self, rel: str, cells: list[str]) -> None:
        path = self.root / rel
        clean = [c.replace("|", "/").replace("\n", " ") for c in cells]
        with path.open("a") as fh:
            fh.write("| " + " | ".join(clean) + " |\n")

    def _log(self, item_id, status, seo_score, verdict, path) -> None:
        when = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._append_row("logs/results.md", [
            when, "Content Engine", item_id, status,
            f"SEO {seo_score} · voice {verdict.score} · {path.relative_to(self.root)}",
        ])

    def _hold(self, item_id, path, issues) -> None:
        when = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._append_row("queue/held-for-voice-review.md",
                         [when, item_id, str(path.relative_to(self.root)), "; ".join(issues) or "off-brand"])

    def _needs_ok(self, item_id, path) -> None:
        with (self.root / "queue/needs-your-ok.md").open("a") as fh:
            fh.write(f"\n- **{item_id}** ({path.relative_to(self.root)}): reads like a promise. **Hold / Approve**\n")


def result_json(r: Result) -> str:
    return json.dumps(asdict(r), indent=2)
