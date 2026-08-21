# Agentic AI Digest

A daily email digest of agentic AI news, built on GitHub Actions and LangGraph. Every morning at 07:00 UTC it:

1. Fetches articles from a curated set of RSS feeds + Tavily news search
2. Deduplicates against a SQLite database of previously seen URLs
3. Classifies each article's relevance with **Groq** (`openai/gpt-oss-20b`)
4. Ranks results and picks the top 5 most relevant stories
5. Generates 2–3 paragraph summaries for each (**Groq** `llama-3.3-70b-versatile`)
6. Renders a clean HTML email and sends it via **Resend**
7. Commits `data/seen.db` back to the repo so state persists across runs

If the pipeline fails at any step, it emails you the full Python traceback before exiting.

---

## Project layout

```
.
├── main.py                          # Entry point — LangGraph pipeline
├── src/
│   ├── sources.py                   # RSS feed list + Tavily queries
│   ├── fetch.py                     # Pull articles from RSS + Tavily
│   ├── dedupe.py                    # URL normalisation + seen-URL filter
│   ├── classify.py                  # Groq: relevance scoring
│   ├── rank.py                      # Pick top 5 stories
│   ├── summarize.py                 # Groq: deep summaries
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
| `GROQ_API_KEY` | [console.groq.com/keys](https://console.groq.com/keys) — free tier is generous |
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

Edit `src/sources.py` — the `RSS_FEEDS` list. Each entry needs `name`, `url`, and optionally `max_articles` (default 20).

```python
{"name": "My Blog", "url": "https://example.com/feed.xml", "max_articles": 10},
```

### Change the number of stories

`MAX_STORIES` in `src/rank.py` (default `5`).

### Change the lookback window

`LOOKBACK_HOURS` in `src/sources.py` (default `26` — slightly over 24 h to handle schedule drift).

### Change the schedule

Edit the `cron` expression in `.github/workflows/daily-digest.yml`.  
`'0 7 * * *'` = 07:00 UTC. [crontab.guru](https://crontab.guru/) is handy for this.

### Adjust for your local timezone

If you're in UTC+1 (Dublin/London summer), `'0 6 * * *'` delivers at 07:00 local.

---

## Estimated cost

Groq's free tier covers this comfortably. If you're on a paid plan:

| Step | Model | ~Cost/day |
|---|---|---|
| Classify ~80 articles | `openai/gpt-oss-20b` | < $0.001 |
| 5 deep summaries | `llama-3.3-70b-versatile` | < $0.005 |
| **Total** | | **effectively free** |

---

## Troubleshooting

**No email received** — check the GitHub Actions log for the run. The pipeline logs every step. If the workflow succeeded, check Resend's delivery dashboard.

**`data/seen.db` keeps growing** — this is expected; it accumulates all seen URLs. At personal scale (hundreds of URLs/month) it stays tiny indefinitely.

**An RSS feed returns no articles** — some feeds block GitHub's IP range. Add a fallback Tavily query for that source instead.

**Workflow fails on `git push`** — ensure the workflow has `permissions: contents: write` (it does by default in this repo). If you forked the repo, check that Actions are enabled in your fork's settings.
