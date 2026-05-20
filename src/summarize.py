"""Generate deep summaries (llama-3.3-70b) and brief summaries (llama-3.1-8b)."""

import logging

from groq import Groq

logger = logging.getLogger(__name__)

DEEP_MODEL = "llama-3.3-70b-versatile"
BRIEF_MODEL = "llama-3.1-8b-instant"

_DEEP_SYSTEM = """\
You write concise, substantive summaries for a daily agentic AI digest read by \
technical practitioners. Your prose is clear, specific, and avoids filler phrases \
like "marks a significant step" or "in the rapidly evolving landscape".\
"""

_DEEP_USER = """\
Summarize the article below in 2-3 paragraphs (150-220 words total).

Structure:
1. Open with the core development or finding — be specific.
2. Explain the technical significance for AI agents or autonomous systems.
3. Close with what this means for practitioners or the broader field.

No bullet points. Flowing prose only.

Title: {title}
Source: {source}
Content:
{content}\
"""

_BRIEF_USER = """\
Write 1-2 crisp sentences summarizing this article for a daily agentic AI digest. \
Be specific about what happened and why it matters for AI agents or automation.

Title: {title}
Content:
{content}\
"""


def _deep_summary(article: dict, client: Groq) -> str:
    resp = client.chat.completions.create(
        model=DEEP_MODEL,
        max_tokens=400,
        messages=[
            {"role": "system", "content": _DEEP_SYSTEM},
            {"role": "user", "content": _DEEP_USER.format(
                title=article["title"],
                source=article["source"],
                content=article["content"][:4000],
            )},
        ],
    )
    return resp.choices[0].message.content.strip()


def _brief_summary(article: dict, client: Groq) -> str:
    resp = client.chat.completions.create(
        model=BRIEF_MODEL,
        max_tokens=120,
        messages=[{"role": "user", "content": _BRIEF_USER.format(
            title=article["title"],
            content=article["content"][:800],
        )}],
    )
    return resp.choices[0].message.content.strip()


def summarize_articles(
    deep_articles: list[dict],
    brief_articles: list[dict],
    client: Groq,
) -> None:
    for i, article in enumerate(deep_articles, 1):
        try:
            article["summary"] = _deep_summary(article, client)
            logger.info("Deep summary %d/%d: %s", i, len(deep_articles), article["title"][:60])
        except Exception as exc:
            logger.warning("Deep summary failed for '%s': %s", article["title"][:60], exc)
            article["summary"] = article["snippet"]

    for i, article in enumerate(brief_articles, 1):
        try:
            article["summary"] = _brief_summary(article, client)
            logger.info("Brief summary %d/%d: %s", i, len(brief_articles), article["title"][:60])
        except Exception as exc:
            logger.warning("Brief summary failed for '%s': %s", article["title"][:60], exc)
            article["summary"] = article["snippet"]
