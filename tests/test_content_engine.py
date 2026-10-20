import shutil
from pathlib import Path

import pytest

from content_engine import ContentEngine, Request
from content_engine.brand_os import BrandOS
from content_engine.llm import json_schema
from content_engine.models import Brief, Draft, Hook, VoiceVerdict
from content_engine import seo, voice

REPO = Path(__file__).resolve().parents[1]

BRIEF = Brief(
    topic="is retinol worth it", format="reel", channel="instagram", angle="purging vs breakout",
    audience="first-time retinol users", primary_keyword="retinol purging",
    secondary_keywords=["retinol week 3"], key_points=["purging is normal", "give it 3-4 weeks"],
    call_to_action="Save this for week 3", claims_to_avoid=["cures acne"],
)
GOOD = Draft(
    title="Retinol purging is not a breakout",
    body="Retinol purging is normal. Your skin looks worse before it looks better.\n"
         "Retinol week 3 is the hard part. Give it three to four weeks before you panic.\nSave this for week 3.",
    caption="Retinol purging, explained.", hashtags=["#retinol", "#skincare", "#retinolpurging"], meta_description="",
)
WEAK = GOOD.model_copy(update={"title": "A note on skin", "body": "Skin changes. Be patient.", "hashtags": []})
HOOK = Hook(pattern="Nobody warns you about X", hook="Nobody warns you about week 3.", alternatives=["a", "b"])
ON_BRAND = VoiceVerdict(on_brand=True, score=91, reads_like_a_promise=False, issues=[], fixes=[])


class FakeClaude:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []
        self.usage = {"input_tokens": 0, "output_tokens": 0}

    def ask(self, system, prompt, out):
        self.calls.append((out.__name__, prompt))
        reply = self.replies.pop(0)
        assert isinstance(reply, out), f"expected {out.__name__}, got {type(reply).__name__}"
        return reply


@pytest.fixture
def project(tmp_path):
    for d in ["brand-os", "owner", "queue", "logs"]:
        shutil.copytree(REPO / d, tmp_path / d)
    return tmp_path


def test_brand_os_loads_voice_keywords_and_banned_phrases():
    b = BrandOS.load(REPO)
    assert "Warm, confident" in b.voice_context()
    assert "last chance" in b.banned_phrases
    kw = b.keywords_for("is retinol worth it")
    assert kw and kw.primary == "retinol purging"


def test_schema_is_strict_for_structured_outputs():
    s = json_schema(Brief)
    assert s["additionalProperties"] is False
    assert set(s["required"]) == set(Brief.model_fields)


def test_seo_scores_good_draft_above_weak_one():
    assert seo.score(BRIEF, GOOD, HOOK.hook).score >= 80
    weak = seo.score(BRIEF, WEAK)
    assert weak.score < 80 and "Primary keyword in the hook or title" in weak.failed


def test_voice_rules_catch_hype():
    issues = voice.rule_issues("LIMITED SPOTS!! Book now, last chance. It cures acne.", ["last chance"])
    joined = " ".join(issues)
    assert "ALL CAPS" in joined and "exclamation" in joined and "last chance" in joined and "cures" in joined


def test_run_ready_saves_draft_and_logs(project):
    fake = FakeClaude([BRIEF, GOOD, HOOK, ON_BRAND])
    r = ContentEngine(project, fake).run(Request(topic="is retinol worth it", angle="purging vs breakout"))
    assert r.status == "ready" and r.item_id == "reel_001"
    assert [c[0] for c in fake.calls] == ["Brief", "Draft", "Hook", "VoiceVerdict"]
    assert "Nobody warns you about week 3." in (project / r.draft_path).read_text()
    assert "reel_001 | ready" in (project / "logs/results.md").read_text()
    assert "reel_001" not in (project / "queue/held-for-voice-review.md").read_text()


def test_run_revises_weak_draft_for_seo(project):
    fake = FakeClaude([BRIEF, WEAK, GOOD, HOOK, ON_BRAND])
    r = ContentEngine(project, fake).run(Request(topic="is retinol worth it"))
    assert [c[0] for c in fake.calls] == ["Brief", "Draft", "Draft", "Hook", "VoiceVerdict"]
    assert "Primary keyword in the hook or title" in fake.calls[2][1]
    assert r.seo_score >= 80 and r.seo_fixes


def test_rule_gate_holds_even_when_claude_says_on_brand(project):
    hype = GOOD.model_copy(update={"caption": "Last chance!! Book NOW"})
    r = ContentEngine(project, FakeClaude([BRIEF, hype, HOOK, ON_BRAND])).run(Request(topic="is retinol worth it"))
    assert r.status == "held"
    assert r.item_id in (project / "queue/held-for-voice-review.md").read_text()


def test_promise_goes_to_needs_your_ok(project):
    promise = ON_BRAND.model_copy(update={"reads_like_a_promise": True})
    r = ContentEngine(project, FakeClaude([BRIEF, GOOD, HOOK, promise])).run(Request(topic="is retinol worth it"))
    assert r.status == "ready"
    assert f"**{r.item_id}**" in (project / "queue/needs-your-ok.md").read_text()


def test_item_ids_increment(project):
    eng = ContentEngine(project, FakeClaude([BRIEF, GOOD, HOOK, ON_BRAND] * 2))
    assert eng.run(Request(topic="t")).item_id == "reel_001"
    assert eng.run(Request(topic="t")).item_id == "reel_002"
