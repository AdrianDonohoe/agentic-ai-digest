"""Fetch articles from RSS feeds and Tavily search."""

import html as html_lib
import logging
import os
import re
import socket
from datetime import datetime, timedelta, timezone
from typing import Any

import feedparser
from tavily import TavilyClient

from src.sources import LOOKBACK_HOURS, RSS_FEEDS, TAVILY_QUERIES

logger = logging.getLogger(__name__)

socket.setdefaulttimeout(20)


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html_lib.unescape(text)
    return " ".join(text.split())


def _published_dt(entry: Any) -> datetime | None:
    parsed = getattr(entry, "published_parsed", None)
    if parsed is None:
        return None
    try:
        return datetime(*parsed[:6], tzinfo=timezone.utc)
    except Exception:
        return None


def _is_recent(entry: Any) -> bool:
    dt = _published_dt(entry)
    if dt is None:
        return False  # Skip entries with no parseable date
    return datetime.now(timezone.utc) - dt < timedelta(hours=LOOKBACK_HOURS)


def _entry_to_article(entry: Any, source_name: str) -> dict | None:
    url = getattr(entry, "link", None)
    title = _strip_html(getattr(entry, "title", ""))
    if not url or not title:
        return None

    content_raw = ""
    if hasattr(entry, "content") and entry.content:
        content_raw = entry.content[0].get("value", "")
    if not content_raw:
        content_raw = getattr(entry, "summary", "")

    content = _strip_html(content_raw)
    snippet = content[:400] if content else title

    dt = _published_dt(entry)
    published = dt.strftime("%Y-%m-%d") if dt else ""

    return {
        "url": url,
        "title": title,
        "snippet": snippet,
        "content": content[:3000],
        "source": source_name,
        "published": published,
    }


def fetch_rss() -> list[dict]:
    articles: list[dict] = []
    for feed_cfg in RSS_FEEDS:
        max_articles = feed_cfg.get("max_articles", 20)
        try:
            feed = feedparser.parse(feed_cfg["url"])
            count = 0
            for entry in feed.entries:
                if count >= max_articles:
                    break
                if not _is_recent(entry):
                    continue
                article = _entry_to_article(entry, feed_cfg["name"])
                if article:
                    articles.append(article)
                    count += 1
            logger.info("RSS %s: %d articles taken (cap=%d)", feed_cfg["name"], count, max_articles)
        except Exception as exc:
            logger.warning("RSS fetch failed for %s: %s", feed_cfg["name"], exc)
    return articles


def fetch_tavily() -> list[dict]:
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        logger.warning("TAVILY_API_KEY not set - skipping search.")
        return []

    client = TavilyClient(api_key=api_key)
    articles: list[dict] = []

    for query in TAVILY_QUERIES:
        try:
            response = client.search(
                query=query,
                search_depth="basic",
                topic="news",
                days=2,
                max_results=5,
            )
            for r in response.get("results", []):
                url = r.get("url", "")
                title = r.get("title", "")
                if not url or not title:
                    continue
                content = r.get("content", "")
                articles.append({
                    "url": url,
                    "title": title,
                    "snippet": content[:400],
                    "content": content[:3000],
                    "source": "Tavily Search",
                    "published": r.get("published_date", "")[:10],
                })
            logger.info("Tavily '%s': %d results", query, len(response.get("results", [])))
        except Exception as exc:
            logger.warning("Tavily query '%s' failed: %s", query, exc)

    return articles


def fetch_all() -> list[dict]:
    rss = fetch_rss()
    search = fetch_tavily()
    combined = rss + search
    seen: set[str] = set()
    unique: list[dict] = []
    for a in combined:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)
    return unique
