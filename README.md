# Agentic AI Digest

A daily email digest of agentic AI news, built on GitHub Actions. Every morning at 07:00 UTC it:

1. Fetches articles from a curated set of RSS feeds + Tavily news search
2. Deduplicates against a SQLite database of previously seen URLs
3. Classifies each article's relevance with **Claude Haiku**
4. Ranks results, picking the top 3–5 for deep treatment
5. Generates 2–3 paragraph summaries for top picks (**Claude Sonnet**) and 1–2 sentence briefs for the rest (**Claude Haiku**)
6. Renders a clean HTML email and sends it via **Resend**
7. Commits `data/seen.db` back to the repo so state persists across runs

If the pipeline fails, it emails you the full Python traceback before exiting.

---

## Project layout

```
.
├── main.py                          # Entry point — run this
├── src/
│   ├── sources.py                   # RSS feed list + Tavily queries
│   ├── fetch.py                     # Pull articles from RSS + Tavily
│   ├── dedupe.py                    # URL normalisation + seen-URL filter
│   ├── classify.py                  # Claude Haiku: relevance scoring
│   ├── rank.py                      # Split top picks vs briefs
│   ├── summarize.py                 # Claude Sonnet/Haiku summaries
│   ├── mailer.py                    # HTML rendering + Resend delivery
│   └── state.py                     # SQLite seen.db helpers
├── data/
│   └── seen.db                      # Committed back to repo after each run
├── .github/workflows/
│   └── daily-digest.yml             # Cron schedule + commit-back step
├── requirements.txt
└── .env.example
```

---

## Local setup

```bash
git clone https://github.com/YOUR_USERNAME/agentic-ai-digest.git
cd agentic-ai-digest

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your actual keys (see "Required secrets" below)

python main.py
```

On first run, `data/seen.db` is created automatically.

---

## Required secrets

| Variable | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/) |
| `TAVILY_API_KEY` | [app.tavily.com](https://app.tavily.com/) |
| `RESEND_API_KEY` | [resend.com/api-keys](https://resend.com/api-keys) |
| `EMAIL_TO` | Your inbox address |
| `EMAIL_FROM` | A verified sender on your Resend account, e.g. `digest@yourdomain.com` |

For **local runs**: put them in `.env` (never commit this file).  
For **GitHub Actions**: add each one under *Settings → Secrets and variables → Actions → New repository secret*.

---

## GitHub Actions setup

1. Push this repo to GitHub.
2. Add the five secrets listed above.
3. The workflow runs automatically at 07:00 UTC. To test it immediately, go to *Actions → Daily Agentic AI Digest → Run workflow*.

The runner commits `data/seen.db` back after each successful run using the built-in `GITHUB_TOKEN` — no extra deploy key needed.

---

## Customisation

### Add or remove RSS feeds

Edit `src/sources.py` — the `RSS_FEEDS` list. Each entry needs `name` and `url`.

```python
{"name": "My Blog", "url": "https://example.com/feed.xml"},
```

### Change the lookback window

`LOOKBACK_HOURS` in `src/sources.py` (default `26` — slightly over 24 h to handle schedule drift).

### Change the number of top picks

`TOP_PICKS_MAX` in `src/rank.py` (default `5`).

### Change the schedule

Edit the `cron` expression in `.github/workflows/daily-digest.yml`.  
`'0 7 * * *'` = 07:00 UTC. [crontab.guru](https://crontab.guru/) is handy for this.

### Use a different send time (your local timezone)

If you're in UTC+1 (Dublin/London summer), `'0 6 * * *'` delivers at 07:00 local.

---

## Estimated cost

| Step | Model | ~Cost/day |
|---|---|---|
| Classify 30–50 articles | Haiku | < $0.002 |
| 5 deep summaries | Sonnet | ~$0.02 |
| 25 brief summaries | Haiku | ~$0.005 |
| **Total** | | **< $0.03 / day ≈ $0.90/month** |

---

## Troubleshooting

**No email received** — check the GitHub Actions log for the run. The pipeline logs every step. If the workflow succeeded, check Resend's delivery dashboard.

**`data/seen.db` keeps growing** — this is expected; it accumulates all seen URLs. At personal scale (hundreds of URLs/month) it stays tiny indefinitely.

**An RSS feed returns no articles** — some feeds block GitHub's IP range. Add a fallback Tavily query for that source instead.

**Workflow fails on `git push`** — ensure the workflow has `permissions: contents: write` (it does by default in this repo). If you forked the repo, check that Actions are enabled in your fork's settings.
