---
name: content-engine
description: Content Engine department. Brief → Draft → SEO pass → Hook. Claude writes, Surfer makes it rank, Grammarly cleans it. Holds anything off-brand.
---

Board tools: Claude (drafts copy), Surfer (briefs), Frase (research), Grammarly (editing), Airtable (content calendar).
What it does: "It reads what people are searching and the voice you set once. Then it builds the piece,
Brief, Draft, SEO Pass, Hook. Claude writes, Surfer makes it rank, Grammarly cleans it, and it can't post
in a voice that isn't yours. If it doesn't sound like the brand, it doesn't go out."

This department is runnable code. For every brief from the orchestrator:

1. Run `content-engine run --topic "<topic>" --format <reel|carousel|post|blog> --angle "<angle>"`
   (add `--keyword` for each target keyword, `--channel` for the destination).
2. Read the JSON summary it prints: SEO score, fixes made, voice verdict, and where the draft was saved.
3. Report back to the orchestrator: the hook, the draft path, SEO score, and whether it is ready or held.

If the command is unavailable (no API key), draft by hand: read `brand-os/content/` and `brand-os/brand-brain/`,
return the draft with its SEO score and the fixes made. Off-brand drafts go to `queue/held-for-voice-review.md`, not out.
