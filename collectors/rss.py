"""
RSS Feed Collector - Gathers content from RSS feeds.
"""

import os
import json
import datetime
from typing import Dict, Any, List

from utils.logger import get_logger

logger = get_logger(__name__)


class RSSCollector:
    """Collects articles from configured RSS feeds."""

    def __init__(self):
        self.feeds = self._load_feeds()

    def _load_feeds(self) -> List[Dict[str, str]]:
        """Load RSS feed URLs from sources.md or config."""
        sources_file = "sources.md"
        feeds = []
        if os.path.exists(sources_file):
            with open(sources_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('-') and 'http' in line:
                        parts = line.split('(')
                        if len(parts) > 1:
                            url = parts[1].rstrip(')')
                            feeds.append({"url": url, "name": line.split(']')[0].lstrip('- [')})
        return feeds

    def collect(self) -> List[Dict[str, Any]]:
        """Collect recent items from RSS feeds."""
        logger.info(f"Collecting from {len(self.feeds)} RSS feeds...")
        articles = []
        # Stub: return empty list if no feed parser available
        # In production, use feedparser or similar
        try:
            import feedparser
            for feed_info in self.feeds:
                try:
                    feed = feedparser.parse(feed_info["url"])
                    for entry in feed.entries[:5]:
                        articles.append({
                            "source": feed_info.get("name", feed_info["url"]),
                            "title": entry.get("title", ""),
                            "link": entry.get("link", ""),
                            "summary": entry.get("summary", "")[:500],
                            "published": entry.get("published", ""),
                            "collected_at": datetime.datetime.now().isoformat()
                        })
                except Exception as e:
                    logger.warning(f"Failed to parse feed {feed_info.get('url')}: {e}")
        except ImportError:
            logger.warning("feedparser not installed; RSS collection skipped")
        logger.info(f"Collected {len(articles)} RSS articles")
        return articles
