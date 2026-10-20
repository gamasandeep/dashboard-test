# 03 · Content Engine

> "It reads what people are searching and the voice you set once. Then it builds the piece:
> Brief, Draft, SEO Pass, Hook. If it doesn't sound like the brand, it doesn't go out."

## Run

```bash
pip install -e ".[dev]"
export ANTHROPIC_API_KEY=...            # or `ant auth login`
content-engine run --topic "is retinol worth it" --format reel --angle "purging vs breakout"
```

Options: `--format reel|carousel|post|blog`, `--channel instagram`, `--keyword "retinol purging"` (repeatable),
`--dry-run` (prints the system prompt and the first step, no API call).

Exit code `0` = ready, `2` = held for voice review, `1` = error.

## What one run does

| Step | Who | Output |
|---|---|---|
| 1 · Brief | Claude, reading `brief-templates.md`, `keyword-map.md`, `positioning.md` | Topic, angle, keywords, key points, CTA, claims to avoid |
| 2 · Draft | Claude, in the voice from `owner/brand-voice.md` + `brand-os/brand-brain/` | Title, body, caption, hashtags, meta description |
| 3 · SEO pass | Local scorer for `seo-checklist.md` (stands in for Surfer). Under 80 → Claude fixes only the failed items, up to 2 rounds | Score 0–100, fixes made |
| 4 · Hook | Claude, picking a pattern from `hook-bank.md` | Hook + two alternatives |
| 5 · Voice check | Rule gate (banned phrases, ALL CAPS, `!!`, medical words) **and** Claude's judgement | On brand? Reads like a promise? |

Then:

- The draft is saved to `drafts/<format>_<nnn>.md` (the calendar stand-in until Airtable is connected).
- A line goes to `logs/results.md` for Results & ROI.
- Off-brand → `queue/held-for-voice-review.md`. The rule gate can't be overruled by Claude.
- Reads like a promise → `queue/needs-your-ok.md` with **Hold / Approve**.
- Nothing is published.

## Settings

| Env var | Default |
|---|---|
| `CONTENT_ENGINE_MODEL` | `claude-opus-5-5` |
| `CONTENT_ENGINE_EFFORT` | `medium` |

Requests use structured outputs (JSON schema per step), prompt caching on the Brand OS context, and
server-side refusal fallback (`fallbacks: "default"`).

## Not connected yet

Surfer, Frase, Grammarly and Airtable (see `TOOLS.md`). The SEO pass and the voice rules run locally until they are.
