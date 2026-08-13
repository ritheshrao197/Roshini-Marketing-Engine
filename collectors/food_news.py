"""
Food News Collector - Gathers real, current food/nutrition/health news stories,
used to write the daily grounded "food_news" articles (see agent.planner.plan_news).
"""

from typing import Any, Dict, List, Tuple

from collectors.google_news import fetch_google_news

# Each query maps to a suggested category for articles built from it, and doubles
# as a source of topic diversity: one story is drawn from each query where possible.
DEFAULT_QUERIES: List[Tuple[str, str]] = [
    ("food and nutrition news India", "Nutrition News"),
    ("nutrition research superfoods", "Nutrition Research"),
    ("FSSAI food safety", "Food Safety"),
    ("millets OR dry fruits health benefits", "Nutrition"),
    ("healthy eating trends India", "Lifestyle"),
]


class FoodNewsCollector:
    """Collects real, recent food/nutrition news stories from Google News RSS."""

    def __init__(self, queries: List[Tuple[str, str]] = None, per_query_limit: int = 6):
        self.queries = queries or DEFAULT_QUERIES
        self.per_query_limit = per_query_limit

    def collect(self) -> List[Dict[str, Any]]:
        return fetch_google_news(self.queries, self.per_query_limit, label="food news")
