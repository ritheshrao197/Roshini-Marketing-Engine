"""
Health News Collector - Gathers real, current health/wellness/nutrition search
trends to ground the planner's evergreen article topic selection in genuine reader
demand, instead of picking topics from pure LLM imagination.
"""

from typing import Any, Dict, List, Tuple

from collectors.google_news import fetch_google_news

# Broader than food_news.py's queries on purpose: this feeds general topic/keyword
# signal into the planner (agent/planner.py), not specific stories to write up.
DEFAULT_QUERIES: List[Tuple[str, str]] = [
    ("healthy breakfast trends India", "Lifestyle"),
    ("women's nutrition health India", "Health"),
    ("kids healthy snacks India", "Lifestyle"),
    ("immunity boosting foods trending", "Wellness"),
    ("gut health diet trends", "Nutrition"),
    ("weight management healthy diet India", "Health"),
]


class HealthNewsCollector:
    """Collects recent health/nutrition search-trend headlines from Google News RSS."""

    def __init__(self, queries: List[Tuple[str, str]] = None, per_query_limit: int = 4):
        self.queries = queries or DEFAULT_QUERIES
        self.per_query_limit = per_query_limit

    def collect(self) -> List[Dict[str, Any]]:
        return fetch_google_news(self.queries, self.per_query_limit, label="health news")
