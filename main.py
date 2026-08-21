"""Entry point — LangGraph pipeline for the Agentic AI Digest."""

import logging
import os
import sys
import traceback
from datetime import datetime, timezone
from typing import TypedDict

from dotenv import load_dotenv
from groq import Groq
from langgraph.graph import END, StateGraph

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Graph state
# ---------------------------------------------------------------------------

class DigestState(TypedDict, total=False):
    raw_articles: list[dict]
    new_articles: list[dict]
    classified_articles: list[dict]
    deep_articles: list[dict]
    brief_articles: list[dict]
    html: str
    total_reviewed: int


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def fetch_node(state: DigestState) -> dict:
    from src.fetch import fetch_all
    logger.info("[fetch] Fetching from RSS feeds and Tavily...")
    articles = fetch_all()
    logger.info("[fetch] %d raw articles collected.", len(articles))
    return {"raw_articles": articles}


def dedupe_node(state: DigestState) -> dict:
    from src.dedupe import filter_new
    from src.state import init_db
    logger.info("[dedupe] Filtering against seen.db...")
    conn = init_db()
    new = filter_new(conn, state.get("raw_articles", []))
    conn.close()
    logger.info("[dedupe] %d new articles after deduplication.", len(new))
    return {"new_articles": new, "total_reviewed": len(new)}


def classify_node(state: DigestState) -> dict:
    from src.classify import classify_articles
    articles = list(state.get("new_articles", []))
    logger.info("[classify] Classifying %d articles with %s...", len(articles), "openai/gpt-oss-20b")
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    classified = classify_articles(articles, client)
    relevant = sum(1 for a in classified if a.get("relevance") != "none")
    logger.info("[classify] %d/%d articles relevant.", relevant, len(classified))
    return {"classified_articles": classified}


def rank_node(state: DigestState) -> dict:
    from src.rank import split_deep_brief
    relevant = [a for a in state.get("classified_articles", []) if a.get("relevance") != "none"]
    deep, brief = split_deep_brief(relevant)
    logger.info("[rank] Top picks: %d, briefs: %d.", len(deep), len(brief))
    return {"deep_articles": deep, "brief_articles": brief}


def summarize_node(state: DigestState) -> dict:
    from src.summarize import summarize_articles
    logger.info("[summarize] Generating summaries...")
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    deep = list(state.get("deep_articles", []))
    brief = list(state.get("brief_articles", []))
    summarize_articles(deep, brief, client)
    return {"deep_articles": deep, "brief_articles": brief}


def render_node(state: DigestState) -> dict:
    from src.mailer import build_html
    logger.info("[render] Building HTML email...")
    html = build_html(
        state.get("deep_articles", []),
        state.get("brief_articles", []),
    )
    return {"html": html}


def email_node(state: DigestState) -> dict:
    from src.mailer import send_email
    logger.info("[email] Sending digest...")
    send_email(state["html"], state.get("total_reviewed", 0))
    return {}


def persist_node(state: DigestState) -> dict:
    from src.state import init_db, mark_seen
    # Persist whatever we classified; fall back to new_articles if classify was skipped.
    articles = state.get("classified_articles") or state.get("new_articles", [])
    conn = init_db()
    for a in articles:
        mark_seen(conn, a["url"], a.get("title", ""))
    conn.commit()
    conn.close()
    logger.info("[persist] Marked %d URLs as seen.", len(articles))
    return {}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def _route_after_dedupe(state: DigestState) -> str:
    return "classify" if state.get("new_articles") else "persist"


def _route_after_rank(state: DigestState) -> str:
    has_content = state.get("deep_articles") or state.get("brief_articles")
    return "summarize" if has_content else "persist"


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

def build_graph():
    builder = StateGraph(DigestState)

    builder.add_node("fetch",     fetch_node)
    builder.add_node("dedupe",    dedupe_node)
    builder.add_node("classify",  classify_node)
    builder.add_node("rank",      rank_node)
    builder.add_node("summarize", summarize_node)
    builder.add_node("render",    render_node)
    builder.add_node("email",     email_node)
    builder.add_node("persist",   persist_node)

    builder.set_entry_point("fetch")
    builder.add_edge("fetch", "dedupe")
    builder.add_conditional_edges(
        "dedupe", _route_after_dedupe,
        {"classify": "classify", "persist": "persist"},
    )
    builder.add_edge("classify", "rank")
    builder.add_conditional_edges(
        "rank", _route_after_rank,
        {"summarize": "summarize", "persist": "persist"},
    )
    builder.add_edge("summarize", "render")
    builder.add_edge("render",    "email")
    builder.add_edge("email",     "persist")
    builder.add_edge("persist",   END)

    return builder.compile()


# ---------------------------------------------------------------------------
# Failure notification
# ---------------------------------------------------------------------------

def _send_failure_email(tb: str) -> None:
    try:
        import resend
        resend.api_key = os.environ["RESEND_API_KEY"]
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        resend.Emails.send({
            "from": os.environ["EMAIL_FROM"],
            "to": [os.environ["EMAIL_TO"]],
            "subject": f"[FAILED] Agentic AI Digest - {date_str}",
            "html": (
                "<h2 style='color:#c0392b'>Agentic AI Digest - Pipeline Failure</h2>"
                f"<p>Failed at <code>{datetime.now(timezone.utc).isoformat()}</code></p>"
                "<pre style='background:#fef2f2;border-left:4px solid #c0392b;"
                "padding:16px;font-family:monospace;font-size:13px;white-space:pre-wrap;'>"
                f"{tb}</pre>"
            ),
        })
        logger.info("Failure notification sent.")
    except Exception:
        logger.exception("Could not send failure email.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        graph = build_graph()
        project = os.environ.get("LANGCHAIN_PROJECT", "default")
        tracing = bool(os.environ.get("LANGCHAIN_API_KEY"))
        logger.info("=== Agentic AI Digest starting (LangGraph) ===")
        logger.info("LangSmith tracing: %s (project: %s)", "ON" if tracing else "OFF", project)
        graph.invoke({
            "raw_articles": [],
            "new_articles": [],
            "classified_articles": [],
            "deep_articles": [],
            "brief_articles": [],
            "html": "",
            "total_reviewed": 0,
        })
        logger.info("=== Digest complete ===")
    except Exception:
        tb = traceback.format_exc()
        logger.error("Pipeline failed:\n%s", tb)
        _send_failure_email(tb)
        sys.exit(1)
