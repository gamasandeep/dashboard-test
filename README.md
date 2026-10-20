# AI Native Social Media Agent Team

A Claude Code project that runs the complete social media of a company: one orchestrator, eight departments,
eight interrupt playbooks, a shared Brand OS, and one owner who only approves.

The full system board lives in the "AI Native Social Media Agent Team" artifact.

## Open it

```bash
cd dashboard-test
claude                     # start Claude Code in this project
```

Inside Claude Code:

- `/agents` lists the orchestrator and the eight department agents.
- `/search-demand-spikes "glass skin routine +340%"` runs one interrupt playbook.
- Ask "run the orchestrator on today's signals" to walk the pipeline: Collects → Scores → Briefs → Drafts → Schedules → Approves.

## Content Engine (working code)

Department 03 is implemented as a Python package in `content_engine/`. It runs
**Brief → Draft → SEO pass → Hook → Voice check** with Claude, reading the Brand OS before it writes.

```bash
pip install -e ".[dev]"
export ANTHROPIC_API_KEY=...          # or `ant auth login`
content-engine run --topic "is retinol worth it" --format reel --angle "purging vs breakout"
content-engine run --topic "is retinol worth it" --dry-run   # print the prompts, no API call
pytest
```

Every run writes a draft to `drafts/`, appends a line to `logs/results.md`, and sends anything
off-brand to `queue/held-for-voice-review.md` instead of out. Nothing is published.
See `content_engine/README.md`.

## What you fill in

| Part | Status |
|---|---|
| Orchestrator rules (`CLAUDE.md`), agents, slash commands, Brand OS tree | Ready |
| Content Engine (`content_engine/`) | Working: drafts, SEO pass, voice check, queue + log |
| File contents in `brand-os/` and `owner/` | Templates. Write them for your brand |
| Tool connections (Semrush, Brand24, Metricool, HubSpot and the rest) | Not configured. See `TOOLS.md` |
| Other seven departments | Agent prompts only. Next to build |
