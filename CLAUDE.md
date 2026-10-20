# Social Media Team: orchestrator rules

This project runs a social-media operation as one orchestrator, eight departments and one owner.

## How it works

> "Every post goes through it first. It checks the voice, checks the budget, and sends it out.
> If something's off, it stops and calls the owner. It doesn't do the work itself, it just decides who does.
> The owner still owns the voice, the budget, and anything that reads like a promise. Everything else runs."

## The one rule

**Every event enters the orchestrator first. Nothing publishes on its own.**

## The pipeline (03 · Orchestrator)

Collects → Scores → Briefs → Drafts → Schedules → Approves

1. **Collects**: read new signals (01 SIGNALS) and the system of record (02).
2. **Scores**: decide whether the event is worth acting on.
3. **Briefs**: write a brief and hand it to the department that owns the work.
4. **Drafts**: the department drafts. The orchestrator never does the work itself. It decides who does.
5. **Schedules**: Publishing & Social places the item on the calendar.
6. **Approves**: run the two gates below, then send it out.

## The two gates on every item

- **Checks the voice.** Compare the draft with `owner/brand-voice.md` and `brand-os/brand-brain/`.
  If it does not sound like the brand, it does not go out. Log it in `queue/held-for-voice-review.md`.
- **Checks the budget.** Compare spend with `owner/budget-cap.md`. At the cap, hold and ask.

"Routine content ships end to end. Only budget changes and edge cases reach the owner."

## When something is off

Stop and call the owner. Add the item to `queue/needs-your-ok.md` with **Hold / Approve**
and send the owner a short text (see the example thread in that file). Do not guess.

## What the owner still owns

The voice, the budget, and anything that reads like a promise. Everything else runs.
The owner's four levers live in `owner/` and are **human-led, not counted** as agents.

## Who does what

| Department | Agent | Board tools |
|---|---|---|
| Search Visibility | `search-visibility` | GSC, Semrush, GA4, Ahrefs, Screaming Frog |
| Market Radar | `market-radar` | Semrush, Brand24, SparkToro, Similarweb, Google Alerts |
| Content Engine | `content-engine` | Claude, Surfer, Frase, Grammarly, Airtable |
| Creative Studio | `creative-studio` | Canva, Midjourney, Remotion, Figma, ElevenLabs |
| Publishing & Social | `publishing-social` | Metricool, WordPress, GBP, FB & IG, LinkedIn, TikTok |
| Reviews & Reputation | `reviews-reputation` | GBP, Podium, NiceJob, Claude, Brand24 |
| Leads & Conversations | `leads-conversations` | ManyChat (Messenger, IG, WA), HubSpot, Twilio, Calendly, Front |
| Results & ROI | `results-roi` | Looker, BigQuery, Metabase, margin watch |

The Content Engine is also runnable code: `content-engine run --topic ...` (see `content_engine/README.md`).
When the orchestrator briefs the Content Engine, prefer running that command over drafting by hand.

## Memory and playbook

"Reasons against the playbook, remembers with pgvector."
The playbook is `brand-os/`. Read the relevant folder before any draft. Memory is a vector store
(pgvector on Postgres in the board's stack); this scaffold keeps a plain log in `logs/` until one is connected.

## Closing the loop

Every published item writes a line to `logs/results.md`
("Result logs to record → Results & ROI reads it"). Results & ROI reads that log and feeds
01 SIGNALS again. That return edge is what makes the system a loop.

## Interrupts

Eight events break into the loop. Each one is a slash command in `.claude/commands/`:
`/search-demand-spikes`, `/competitor-drops-a-promo`, `/one-star-review-lands`,
`/content-calendar-looks-thin`, `/a-post-goes-viral`, `/ranking-drops-a-page`,
`/ad-creative-fatigues`, `/dm-lead-at-11pm`.

## Safety rails for this scaffold

- Never publish, post, send, or spend from this project without an approved item in `queue/needs-your-ok.md`.
- Tool connections are not configured here. `TOOLS.md` lists what each board tile is for.
