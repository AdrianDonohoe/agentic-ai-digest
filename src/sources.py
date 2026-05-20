"""RSS feeds and Tavily search query configuration."""

LOOKBACK_HOURS = 26  # Slightly over 24h to handle cron schedule drift

# max_articles caps how many recent entries we take per feed per run.
# High-volume feeds (arXiv) need a tighter cap to keep classify costs low.
RSS_FEEDS = [
    {"name": "Anthropic News",    "url": "https://www.anthropic.com/news/rss.xml",                          "max_articles": 10},
    {"name": "OpenAI Blog",       "url": "https://openai.com/blog/rss.xml",                                 "max_articles": 10},
    {"name": "Google DeepMind",   "url": "https://deepmind.google/blog/rss/",                               "max_articles": 10},
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml",                            "max_articles": 10},
    {"name": "The Batch",         "url": "https://www.deeplearning.ai/the-batch/feed/",                     "max_articles": 10},
    {"name": "Import AI",         "url": "https://jack-clark.net/feed/",                                    "max_articles": 5},
    {"name": "Simon Willison",    "url": "https://simonwillison.net/atom/entries/",                          "max_articles": 10},
    {"name": "VentureBeat AI",    "url": "https://venturebeat.com/category/ai/feed/",                       "max_articles": 10},
    {"name": "MIT Tech Review AI","url": "https://www.technologyreview.com/topic/artificial-intelligence/feed", "max_articles": 10},
    {"name": "arXiv cs.AI",       "url": "https://arxiv.org/rss/cs.AI",                                     "max_articles": 20},
    {"name": "arXiv cs.MA",       "url": "https://arxiv.org/rss/cs.MA",                                     "max_articles": 15},
]

TAVILY_QUERIES = [
    "agentic AI news",
    "AI agents autonomous systems",
    "Model Context Protocol MCP",
    "computer use AI browser automation",
    "Claude Code Cursor Devin AI coding",
    "multi-agent AI systems",
    "AI tool use function calling",
    "autonomous AI research 2025",
]
