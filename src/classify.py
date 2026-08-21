"""Classify article relevance to agentic AI using Groq (openai/gpt-oss-20b)."""

import json
import logging

from groq import Groq

logger = logging.getLogger(__name__)

MODEL = "openai/gpt-oss-20b"

_SYSTEM = """\
You are an AI news classifier. Determine whether a news article is relevant to \
"agentic AI" — AI systems that can autonomously plan, reason, use tools, and \
complete multi-step tasks without constant human intervention.

Relevant topics include: AI agents, tool-using models, autonomous coding assistants \
(Claude Code, Cursor, Devin, Copilot Workspace), multi-agent systems, computer use / \
web-browsing AI, Model Context Protocol (MCP), AI planning and reasoning, agent \
memory and orchestration, autonomous research agents, and academic papers on \
reasoning, planning, or tool use in AI.

Always respond with valid JSON only.\
"""

_USER_TMPL = """\
Classify this article.

Title: {title}
Snippet: {snippet}

Return JSON with exactly these fields:
{{
  "relevance": "high" | "medium" | "low" | "none",
  "reason": "one sentence"
}}

Definitions:
- high: directly about agentic AI products, capabilities, or research
- medium: general AI progress with clear agent implications, or key AI infrastructure
- low: tangentially related (broad ML, AI policy without agent focus)
- none: unrelated to AI agents\
"""


def _classify_one(article: dict, client: Groq) -> dict:
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            max_tokens=128,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": _USER_TMPL.format(
                    title=article["title"],
                    snippet=article["snippet"][:400],
                )},
            ],
        )
        parsed = json.loads(resp.choices[0].message.content)
        article["relevance"] = parsed.get("relevance", "none")
        article["reason"] = parsed.get("reason", "")
    except Exception as exc:
        logger.warning("Classification failed for '%s': %s", article["title"][:60], exc)
        article["relevance"] = "none"
        article["reason"] = ""
    return article


def classify_articles(articles: list[dict], client: Groq) -> list[dict]:
    for i, article in enumerate(articles, 1):
        _classify_one(article, client)
        logger.debug(
            "[%d/%d] %s -> %s",
            i, len(articles),
            article["title"][:55],
            article["relevance"],
        )
    return articles
