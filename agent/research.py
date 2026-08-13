"""
Research Engine - Collects and structures today's research data.
Returns structured dataset without dumping entire knowledge base.
No LLM calls - pure data collection and structuring.
"""

import os
import json
import datetime
import re
from typing import Dict, Any, List

from config import Config
from utils.logger import get_logger
from collectors.rss import RSSCollector
from collectors.health_news import HealthNewsCollector
from collectors.research import ResearchCollector
from collectors.recipes import RecipeCollector
from collectors.products import ProductCollector

logger = get_logger(__name__)

SEASON_MAP = {
    1: "Winter", 2: "Winter", 3: "Spring",
    4: "Spring", 5: "Summer", 6: "Summer",
    7: "Monsoon", 8: "Monsoon", 9: "Monsoon",
    10: "Autumn", 11: "Autumn", 12: "Winter"
}


def research() -> Dict[str, Any]:
    """
    Collect today's research data and return structured dataset.
    No LLM calls - pure data collection.

    Returns:
        Structured research dataset.
    """
    logger.info("Starting research engine...")

    today = datetime.date.today()
    day_name = today.strftime("%A")

    # Build today's context
    today_info = _build_today_context(today, day_name)

    # Collect from various sources
    health_news = HealthNewsCollector().collect()
    recipes = RecipeCollector().collect()
    products = ProductCollector().collect()
    rss_data = RSSCollector().collect()
    research_data = ResearchCollector().collect()

    # Load memory for blocked/recent topics
    memory = _load_memory()
    blocked_topics = memory.get("blockedTopics", [])

    # Load history for recent keywords
    history = _load_history()
    recent_keywords = _extract_recent_keywords(history, days=7)
    recent_campaigns = _recent_campaign_summaries(history, days=14)
    recent_titles = list(dict.fromkeys(
        _recent_titles(history, days=21) + _recent_output_titles(days=21)
    ))

    # Extract trending topics from collectors
    trending_topics = _extract_trending_topics(rss_data, research_data, health_news)

    # Build product list
    product_names = [p.get("name", "") for p in products if p.get("name")]

    # Extract keywords from trending topics
    keywords = _extract_keywords_from_topics(trending_topics)

    result = {
        "today": today_info,
        "trendingTopics": trending_topics,
        "healthNews": [item.get("title", "") for item in health_news[:6] if item.get("title")],
        "recipes": recipes[:5],
        "keywords": keywords,
        "products": product_names,
        "recommendedProducts": _recommend_products(today_info, product_names),
        "blockedTopics": blocked_topics,
        "competitors": [],
        "recentKeywords": recent_keywords,
        "recentCampaigns": recent_campaigns,
        "recentTitles": recent_titles,
        "dayName": day_name
    }

    logger.info(
        f"Research complete: {len(trending_topics)} trending topics, "
        f"{len(health_news)} news, {len(products)} products"
    )
    return result


def _build_today_context(today: datetime.date, day_name: str) -> Dict[str, Any]:
    """Build structured context for today."""
    month = today.month
    season = SEASON_MAP.get(month, "General")

    # Check for festivals
    festival = _check_festival(today)
    awareness_day = _check_awareness_day(today)

    return {
        "date": today.isoformat(),
        "dayName": day_name,
        "season": season,
        "festival": festival,
        "awarenessDay": awareness_day
    }


def _check_festival(today: datetime.date) -> str:
    """Return a campaign trigger only when its calendar window is active.

    The old file-wide keyword search let July content match "Sankranti" from the
    Q1 section of the calendar. Explicit windows prevent that false festival cue.
    """
    if today.month == 1 and 10 <= today.day <= 20:
        return "Sankranti"
    if today.month in (6, 7):
        return "Back to School Season"
    if today.month == 5 and today.weekday() == 6 and 8 <= today.day <= 14:
        return "Mother's Day"

    # Movable religious festivals are omitted until verified dates are maintained.
    return None


def _check_awareness_day(today: datetime.date) -> str:
    """Check if today matches a health/nutrition awareness day."""
    awareness_days = {
        (1, 1): "New Year Health Resolutions",
        (3, 4): "World Obesity Day",
        (4, 7): "World Health Day",
        (5, 29): "World Digestive Health Day",
        (6, 1): "Global Day of Parents",
        (8, 14): "World Lymphoma Day",
        (9, 29): "World Heart Day",
        (10, 16): "World Food Day",
        (11, 14): "World Diabetes Day",
        (12, 1): "World AIDS Day"
    }

    key = (today.month, today.day)
    return awareness_days.get(key)


def _load_memory() -> Dict[str, Any]:
    """Load agent memory."""
    memory_file = "memory/daily-memory.json"
    if os.path.exists(memory_file):
        try:
            with open(memory_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load memory: {e}")
    return {
        "blockedTopics": [],
        "recentKeywords": [],
        "productsUsedThisWeek": []
    }


def _load_history() -> List[Dict[str, Any]]:
    """Load history from JSON file."""
    history_file = Config.get('HISTORY_FILE', 'history/history.json')
    if os.path.exists(history_file) and history_file.endswith('.json'):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load history: {e}")

    # Fallback: try loading from markdown
    md_file = "history/previous-posts.md"
    if os.path.exists(md_file):
        return _parse_md_history(md_file)

    return []


def _parse_md_history(filepath: str) -> List[Dict[str, Any]]:
    """Parse markdown history file into structured data."""
    entries = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        current_entry = {}
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("## "):
                if current_entry:
                    entries.append(current_entry)
                current_entry = {"date": line.replace("## ", "").strip()}
            elif line.startswith("**Product:**"):
                current_entry["product"] = line.replace("**Product:**", "").strip()
            elif line.startswith("**Theme:**"):
                current_entry["theme"] = line.replace("**Theme:**", "").strip()
            elif line.startswith("**Keywords:**"):
                kw_str = line.replace("**Keywords:**", "").strip()
                current_entry["keywords"] = [
                    k.strip() for k in kw_str.split(",") if k.strip()
                ]

        if current_entry:
            entries.append(current_entry)

    except Exception as e:
        logger.warning(f"Failed to parse MD history: {e}")

    return entries


def _extract_recent_keywords(history: List[Dict], days: int = 7) -> List[str]:
    """Extract keywords used in recent history."""
    keywords = []
    today = datetime.date.today()
    cutoff = (today - datetime.timedelta(days=days)).isoformat()

    for entry in history:
        entry_date = entry.get("date", "")
        if entry_date >= cutoff:
            keywords.extend(entry.get("keywords", []))

    return list(dict.fromkeys(keywords))  # deduplicate preserving order


def _recent_campaign_summaries(history: List[Dict], days: int) -> List[str]:
    """Create compact planner-facing summaries of recent campaigns."""
    cutoff = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    summaries = []
    for entry in history:
        if entry.get("date", "") < cutoff:
            continue
        product = ", ".join(entry.get("products", [])) or entry.get("product", "")
        titles = entry.get("topics", [])[:2]
        summaries.append(f"{entry.get('date')}: {product}; {' | '.join(titles)}")
    return summaries


def _recent_titles(history: List[Dict], days: int) -> List[str]:
    cutoff = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    return [
        title
        for entry in history
        if entry.get("date", "") >= cutoff
        for title in entry.get("topics", [])
        if title
    ]


def _recent_output_titles(days: int) -> List[str]:
    """Read local output packages so freshness survives a missed history update."""
    output_dir = Config.get('OUTPUT_DIR', 'outputs')
    cutoff = datetime.date.today() - datetime.timedelta(days=days)
    packages = []
    try:
        for filename in os.listdir(output_dir):
            match = re.fullmatch(r"(\d{4}-\d{2}-\d{2})\.json", filename)
            if match and datetime.date.fromisoformat(match.group(1)) >= cutoff:
                packages.append((match.group(1), os.path.join(output_dir, filename)))
    except OSError as error:
        logger.warning(f"Failed to read local output history: {error}")
        return []

    titles = []
    for _, path in sorted(packages, reverse=True):
        try:
            with open(path, "r", encoding="utf-8") as file:
                package = json.load(file)
            titles.extend(article.get("title", "") for article in package.get("blogs", []))
        except (OSError, ValueError, json.JSONDecodeError) as error:
            logger.warning(f"Skipping unreadable output package '{path}': {error}")
    return [title for title in titles if title]


def _extract_trending_topics(
    rss_data: List, research_data: List, health_news: List
) -> List[str]:
    """Extract trending topics from collected data."""
    topics = []

    for item in rss_data[:10]:
        title = item.get("title", "")
        if title:
            topics.append(title)

    for item in research_data[:10]:
        title = item.get("title", "")
        if title:
            topics.append(title)

    for item in health_news[:10]:
        title = item.get("title", "")
        if title:
            topics.append(title)

    return topics[:15]


def _extract_keywords_from_topics(topics: List[str]) -> List[str]:
    """Extract simple keywords from topic titles."""
    stop_words = {
        "the", "a", "an", "is", "are", "for", "and", "of", "to",
        "in", "with", "on", "at", "by", "from", "this", "that",
        "new", "how", "why", "what", "your", "you"
    }
    keywords = []
    for topic in topics:
        words = topic.lower().split()
        for word in words:
            clean = "".join(c for c in word if c.isalnum())
            if clean and len(clean) > 3 and clean not in stop_words:
                keywords.append(clean)

    return list(dict.fromkeys(keywords))[:20]


def _recommend_products(
    today_info: Dict[str, Any], available_products: List[str]
) -> List[str]:
    """Recommend products based on today's context."""
    season = today_info.get("season", "")
    festival = today_info.get("festival")

    # Season-based recommendations
    seasonal_map = {
        "Winter": ["Nutrimix", "Sathvik 7"],
        "Summer": ["Sathvik 7", "Chia Seeds"],
        "Monsoon": ["Nutrimix", "Pumpkin Seeds"],
        "Spring": ["Sathvik 7", "Flax Seeds"],
        "Autumn": ["Nutrimix", "Sunflower Seeds"]
    }

    recommended = seasonal_map.get(season, ["Nutrimix", "Sathvik 7"])

    # Festival overrides
    if festival:
        festival_products = {
            "Diwali": ["Nutrimix", "Sathvik 7"],
            "Navratri": ["Nutrimix"],
            "Sankranti": ["Nutrimix"],
        }
        if festival in festival_products:
            recommended = festival_products[festival]

    return recommended
