"""Render HTML email and send via Resend."""

import logging
import os
from datetime import datetime, timezone

import resend

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

_ARTICLE_TMPL = """\
<div style="margin-bottom:36px;">
  <h2 style="margin:0 0 6px;font-size:19px;font-weight:normal;line-height:1.4;">
    <a href="{url}" style="color:#0f172a;text-decoration:none;">{title}</a>
  </h2>
  <p style="margin:0 0 14px;font-size:12px;color:#94a3b8;font-family:Arial,sans-serif;">
    {source}{date_part}
  </p>
  <div style="font-size:15px;line-height:1.85;color:#334155;">{summary}</div>
</div>
"""

_BRIEF_TMPL = """\
<div style="margin-bottom:18px;padding-bottom:18px;border-bottom:1px solid #f1f5f9;">
  <h3 style="margin:0 0 5px;font-size:14px;font-weight:bold;">
    <a href="{url}" style="color:#0f172a;text-decoration:none;">{title}</a>
  </h3>
  <p style="margin:0;font-size:13px;color:#475569;line-height:1.65;">{summary}</p>
</div>
"""

_EMAIL_TMPL = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agentic AI Digest</title>
</head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:Georgia,'Times New Roman',serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;">
  <tr><td align="center" style="padding:28px 16px;">
    <table width="100%" cellpadding="0" cellspacing="0"
           style="max-width:660px;background:#ffffff;border-radius:10px;
                  overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.07);">

      <!-- Header -->
      <tr><td style="background:#0f172a;padding:36px 44px;text-align:center;">
        <p style="margin:0;font-size:11px;letter-spacing:3px;text-transform:uppercase;
                  color:#64748b;font-family:Arial,sans-serif;">Daily</p>
        <h1 style="margin:6px 0 4px;color:#f8fafc;font-size:26px;font-weight:normal;
                   letter-spacing:1px;">Agentic AI Digest</h1>
        <p style="margin:0;color:#64748b;font-size:13px;font-family:Arial,sans-serif;">{date}</p>
      </td></tr>

      <!-- Body -->
      <tr><td style="padding:36px 44px;">

        <!-- Top Picks -->
        <p style="margin:0 0 22px;font-size:10px;text-transform:uppercase;letter-spacing:3px;
                  color:#94a3b8;border-bottom:2px solid #e2e8f0;padding-bottom:10px;
                  font-family:Arial,sans-serif;">&#11088; Top Picks</p>
        {top_picks_html}

        <!-- Briefs -->
        {briefs_section}

      </td></tr>

      <!-- Footer -->
      <tr><td style="background:#f8fafc;padding:18px 44px;text-align:center;
                     border-top:1px solid #e2e8f0;">
        <p style="margin:0;font-size:11px;color:#94a3b8;font-family:Arial,sans-serif;">
          {total} articles reviewed &middot; Summaries by Claude
        </p>
      </td></tr>

    </table>
  </td></tr>
</table>
</body>
</html>
"""

_BRIEFS_SECTION_TMPL = """\
<p style="margin:36px 0 22px;font-size:10px;text-transform:uppercase;letter-spacing:3px;
          color:#94a3b8;border-bottom:2px solid #e2e8f0;padding-bottom:10px;
          font-family:Arial,sans-serif;">Also Worth Noting</p>
{briefs_html}
"""


def _date_part(published: str) -> str:
    return f" &middot; {published}" if published else ""


def _render_article(article: dict) -> str:
    return _ARTICLE_TMPL.format(
        url=article["url"],
        title=article["title"],
        source=article["source"],
        date_part=_date_part(article.get("published", "")),
        summary=article.get("summary", article["snippet"]).replace("\n\n", "</p><p style='margin:12px 0 0;'>"),
    )


def _render_brief(article: dict) -> str:
    return _BRIEF_TMPL.format(
        url=article["url"],
        title=article["title"],
        summary=article.get("summary", article["snippet"]),
    )


def build_html(deep_articles: list[dict], brief_articles: list[dict]) -> str:
    dt = datetime.now(timezone.utc)
    date_str = dt.strftime(f"%A, %B {dt.day}, %Y")
    top_picks_html = "".join(_render_article(a) for a in deep_articles)

    briefs_section = ""
    if brief_articles:
        briefs_html = "".join(_render_brief(a) for a in brief_articles)
        briefs_section = _BRIEFS_SECTION_TMPL.format(briefs_html=briefs_html)

    total = len(deep_articles) + len(brief_articles)
    return _EMAIL_TMPL.format(
        date=date_str,
        top_picks_html=top_picks_html,
        briefs_section=briefs_section,
        total=total,
    )


# ---------------------------------------------------------------------------
# Sending
# ---------------------------------------------------------------------------

def send_email(html: str, total_reviewed: int = 0) -> None:
    resend.api_key = os.environ["RESEND_API_KEY"]
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    params: resend.Emails.SendParams = {
        "from": os.environ["EMAIL_FROM"],
        "to": [os.environ["EMAIL_TO"]],
        "subject": f"Agentic AI Digest — {date_str}",
        "html": html,
    }
    result = resend.Emails.send(params)
    logger.info("Email sent: id=%s", result.get("id", "unknown"))
