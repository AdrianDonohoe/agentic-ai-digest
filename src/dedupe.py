"""URL normalization and seen-URL deduplication."""

import logging
import sqlite3
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from src.state import is_seen

logger = logging.getLogger(__name__)

_STRIP_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "fbclid", "gclid", "ref", "source", "share", "mc_cid", "mc_eid",
})


def normalize_url(url: str) -> str:
    try:
        p = urlparse(url)
        params = [(k, v) for k, v in parse_qsl(p.query) if k.lower() not in _STRIP_PARAMS]
        normalized = p._replace(
            scheme=p.scheme.lower(),
            netloc=p.netloc.lower(),
            path=p.path.rstrip("/") or "/",
            query=urlencode(params),
            fragment="",
        )
        return urlunparse(normalized)
    except Exception:
        return url


def filter_new(conn: sqlite3.Connection, articles: list[dict]) -> list[dict]:
    """Return articles whose normalized URL has not been seen before."""
    new: list[dict] = []
    for article in articles:
        norm = normalize_url(article["url"])
        article["url"] = norm  # Store canonical form
        if is_seen(conn, norm):
            logger.debug("Already seen: %s", norm)
        else:
            new.append(article)
    logger.info("Dedupe: %d -> %d articles", len(articles), len(new))
    return new
