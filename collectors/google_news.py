"""
Shared Google News RSS fetch helper. No API key required; feeds are public and
query-driven. Used by FoodNewsCollector (real daily news stories) and
HealthNewsCollector (trending-signal grounding for evergreen blog topics).
"""

import datetime
import html
import re
import urllib.parse
from typing import Any, Dict, List, Tuple

from utils.logger import get_logger

logger = get_logger(__name__)


def fetch_google_news(
    queries: List[Tuple[str, str]], per_query_limit: int = 6, label: str = "news"
) -> List[Dict[str, Any]]:
    """
    Fetch and dedupe recent items across a list of (query, suggested_category) pairs.

    Returns a list of dicts: title, link, summary, source, published, query,
    suggested_category, collected_at.
    """
    logger.info(f"Collecting {label} from {len(queries)} Google News queries...")
    items: List[Dict[str, Any]] = []
    seen_titles = set()

    try:
        import feedparser
    except ImportError:
        logger.warning("feedparser not installed; Google News collection skipped")
        return items

    for query, suggested_category in queries:
        url = _build_url(query)
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:per_query_limit]:
                title = _clean_title(entry.get("title", ""))
                if not title or title.lower() in seen_titles:
                    continue
                seen_titles.add(title.lower())

                source = ""
                entry_source = entry.get("source")
                if isinstance(entry_source, dict):
                    source = entry_source.get("title", "")
                elif entry_source is not None:
                    source = getattr(entry_source, "title", "") or ""

                items.append({
                    "title": title,
                    "link": entry.get("link", ""),
                    "summary": _clean_summary(entry.get("summary", "")),
                    "source": source or "Google News",
                    "published": entry.get("published", ""),
                    "query": query,
                    "suggested_category": suggested_category,
                    "collected_at": datetime.datetime.now().isoformat()
                })
        except Exception as e:
            logger.warning(f"Failed to collect {label} for query '{query}': {e}")

    logger.info(f"Collected {len(items)} unique {label} items")
    return items


def _build_url(query: str) -> str:
    q = urllib.parse.quote(query)
    return f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"


def _clean_title(title: str) -> str:
    # Google News titles are usually "Headline - Source Name"; strip the trailing source.
    cleaned = re.sub(r"\s+-\s+[^-]+$", "", html.unescape(title or ""))
    return cleaned.strip()


def _clean_summary(summary: str) -> str:
    # Google News RSS summaries are HTML-wrapped and entity-escaped; strip both.
    text = re.sub(r"<[^>]+>", "", summary or "")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()[:500]
