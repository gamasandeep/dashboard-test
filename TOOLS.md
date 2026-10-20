# Tools

What each tile on the board is for. None of these are connected yet; connect them one at a time
(an MCP server, an API key in `.env`, or a Claude Code connector) and note it in the Status column.

## 01 · Signals
| Tool | Used for | Status |
|---|---|---|
| Google Search Console | Search queries, impressions, clicks | Not connected |
| Google Analytics 4 | Sessions, conversions | Not connected |
| Semrush | Rankings, keyword demand spikes | Not connected |
| Google Business Profile | Reviews, local posts | Not connected |
| Meta (FB & IG) | Insights | Not connected |
| LinkedIn | Page analytics | Not connected |
| YouTube | Channel analytics | Not connected |
| Brand24 | Web mentions | Not connected |

## 02 · System of record
| Tool | Used for | Status |
|---|---|---|
| HubSpot | CRM | Not connected |
| Airtable | Content calendar | Not connected (Content Engine writes `drafts/` instead) |
| Google Drive | Brand asset drive | Not connected |
| Notion | Brand wiki | Not connected |
| Segment | CDP | Not connected |
| Supabase | Unified store | Not connected |
| Google Calendar | Publish calendar | Not connected |

## 03 · The brain
| Tool | Used for | Status |
|---|---|---|
| Claude | Reasoning and writing | **Connected** via `ANTHROPIC_API_KEY` (Content Engine) |
| LangGraph | Multi-step agent runner | Not used; Claude Code subagents run the agents |
| PostgreSQL + pgvector | Memory store | Not connected (`logs/results.md` stands in) |
| Midjourney | Visuals | Not connected |
| ElevenLabs | Voice-over | Not connected |
| Whisper | Transcription | Not connected |

## Departments
| Department | Tools |
|---|---|
| 01 Search Visibility | GSC, Semrush, GA4, Ahrefs, Screaming Frog |
| 02 Market Radar | Semrush, Brand24, SparkToro, Similarweb, Google Alerts |
| 03 Content Engine | Claude (connected), Surfer, Frase, Grammarly, Airtable. SEO pass and editing run locally until Surfer/Grammarly are connected |
| 04 Creative Studio | Canva, Midjourney, Remotion, Figma, ElevenLabs |
| 05 Publishing & Social | Metricool, WordPress, GBP, Facebook, Instagram, LinkedIn, TikTok |
| 06 Reviews & Reputation | GBP, Podium, NiceJob, Claude, Brand24 |
| 07 Leads & Conversations | ManyChat, HubSpot, Twilio, Calendly, Front |
| 08 Results & ROI | Looker, BigQuery, Metabase, margin watch |

## 06 · Engage
Metricool scheduler, WordPress posts, GBP posts, ManyChat chat replies.

## 07 · Data & observability
Airbyte, dbt, BigQuery, Looker, Vercel, Sentry, LaunchDarkly (flags).

## Owner access
Owner dashboard, approval queue (`queue/needs-your-ok.md`), activity log (`logs/`), permissions, alerts, kill switch.
