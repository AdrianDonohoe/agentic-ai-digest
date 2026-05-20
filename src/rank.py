"""Rank classified articles and split into deep-summary and brief-summary sets."""

import logging

logger = logging.getLogger(__name__)

_SCORES = {"high": 3, "medium": 2, "low": 1, "none": 0}
MAX_STORIES = 5


def split_deep_brief(
    articles: list[dict],
) -> tuple[list[dict], list[dict]]:
    """Return top MAX_STORIES articles (all deep-summarised) and an empty briefs list."""
    relevant = [a for a in articles if _SCORES.get(a.get("relevance", "none"), 0) > 0]
    ranked = sorted(relevant, key=lambda a: _SCORES.get(a.get("relevance", "none"), 0), reverse=True)

    deep = ranked[:MAX_STORIES]

    logger.info(
        "Ranked %d relevant articles, keeping top %d for digest.",
        len(relevant),
        len(deep),
    )
    return deep, []
