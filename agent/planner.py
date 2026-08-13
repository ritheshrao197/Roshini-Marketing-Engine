"""
Planner Agent - Responsible only for planning content strategy.
Chooses product, theme, customer persona, and website topics.
"""

import json
from typing import Any, Dict, List
from utils.logger import get_logger
from llm import call_llm

logger = get_logger(__name__)

_NEWS_STOP_WORDS = {
    "the", "a", "an", "is", "are", "for", "and", "of", "to", "in", "with",
    "on", "at", "by", "from", "this", "that", "new", "how", "why", "what",
    "your", "you", "as", "it", "its", "be", "or", "india", "news"
}


def plan(research_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Choose product, theme, persona, and a list of 5 specialized articles based on research.
    
    Args:
        research_data: Structured research data from research agent.
    
    Returns:
        Plan with product, theme, persona, and a list of 5 articles to generate.
    """
    logger.info("Planning content strategy...")
    
    trending_topics = research_data.get('trendingTopics', [])
    health_news = research_data.get('healthNews', [])
    keywords = research_data.get('keywords', [])
    products = research_data.get('products', ['Nutrimix', 'Sathvik 7', 'Chia Seeds', 'Flax Seeds', 'Pumpkin Seeds', 'Sunflower Seeds'])
    recommended_products = research_data.get('recommendedProducts', ['Nutrimix'])
    today_info = research_data.get('today', {})
    recent_campaigns = research_data.get('recentCampaigns', [])
    recent_titles = research_data.get('recentTitles', [])
    blocked_topics = research_data.get('blockedTopics', [])
    recent_keywords = research_data.get('recentKeywords', [])
    
    # Generate plan using LLM
    prompt = f"""
    You are the Lead Content Planner for Roshini's Home Products (Homemade Millet & Dry Fruit Nutrition Products).
    Your task is to plan a daily cohesive content campaign for today.
    
    Today's Context:
    - Date: {today_info.get('date')}
    - Season: {today_info.get('season')}
    - Festival: {today_info.get('festival')}
    - Awareness Day: {today_info.get('awarenessDay')}
    
    Research Data (real, current headlines collected today via Google News - this is
    your best signal for what health/nutrition-conscious Indian readers are actually
    searching for and reading right now):
    - Trending Topics: {trending_topics[:10]}
    - Health News: {health_news[:5]}
    - Niche Keywords: {keywords[:15]}
    - Available Products: {products}
    - Recommended Product: {recommended_products}
    - Recent campaign titles (do not repeat their subject, structure, or angle): {recent_titles[:25]}
    - Recent campaign summaries: {recent_campaigns[:7]}
    - Blocked topics: {blocked_topics}
    - Recently used keywords: {recent_keywords[:40]}

    SEO / discoverability rules:
    - Prefer article angles that connect to one or more of today's real Trending
      Topics / Health News above over purely invented angles - real search demand
      beats a clever but ungrounded idea. It is fine to reinterpret a trending
      topic through Roshini's product lens rather than copying it verbatim.
    - Write titles the way a real searcher would phrase a query or the way a
      ranking article would phrase a headline: lead with the primary keyword or
      concrete benefit in the first few words, avoid vague/poetic openers, and
      avoid stuffing more than one core keyword phrase into a single title.
    - Each article's `keywords` should include at least one phrase a real person
      would type into Google (e.g. "is ragi good for weight loss", not just "ragi").

    Non-negotiable freshness rules:
    - Create a genuinely new campaign angle, not a title rewrite. Do not reuse a
      recent ingredient spotlight, recipe format, health outcome, or headline pattern.
    - Use a festival only when it is listed in Today's Context. Never mention
      Sankranti, Pongal, Lohri, Diwali, or another festival merely because it
      appears in the annual calendar.
    - If the active trigger is Back to School Season, focus on lunchboxes,
      breakfast routines, or practical family nutrition—not festival sweets.
    - Rotate products when possible; do not choose the same product used in the
      most recent two campaigns unless it is specifically required by today’s context.
    
    Select:
    1. Product: Choose the best single product from the available products list (usually the recommended product, unless another fits better today).
    2. Campaign Theme: A cohesive medical/wellness theme for today's articles.
    3. Target Customer Persona: Describe a specific target user persona.
    4. Plan exactly 5 distinct articles to generate. One of each type:
       - 'blog': A deep-dive article (1200–1800 words)
       - 'health_tip': Actionable wellness tips (600–900 words)
       - 'nutrition_news': Science/news-based item (700–1200 words)
       - 'recipe': A nutritious recipe featuring the selected product (800–1000 words)
       - 'ingredient_spotlight': A deep dive into a key ingredient of the selected product (1000–1400 words)
       
       For each article, provide:
       - `type`: one of 'blog', 'health_tip', 'nutrition_news', 'recipe', 'ingredient_spotlight'
       - `title`: a professional, compelling headline (Healthline/Medical News Today style)
       - `category`: e.g. 'Health', 'Nutrition', 'Recipes', 'Lifestyle', or 'Wellness'
       - `keywords`: 3-5 target SEO keywords for that article

    Return ONLY a valid JSON object matching this schema:
    {{
        "product": "Product Name",
        "theme": "Theme Name",
        "persona": "Persona Description",
        "articles": [
            {{
                "type": "blog",
                "title": "compelling title",
                "category": "Health",
                "keywords": ["keyword1", "keyword2"]
            }},
            {{
                "type": "health_tip",
                "title": "compelling title",
                "category": "Lifestyle",
                "keywords": ["keyword1", "keyword2"]
            }},
            {{
                "type": "nutrition_news",
                "title": "compelling title",
                "category": "Nutrition",
                "keywords": ["keyword1", "keyword2"]
            }},
            {{
                "type": "recipe",
                "title": "compelling title",
                "category": "Recipes",
                "keywords": ["keyword1", "keyword2"]
            }},
            {{
                "type": "ingredient_spotlight",
                "title": "compelling title",
                "category": "Nutrition",
                "keywords": ["keyword1", "keyword2"]
            }}
        ]
    }}
    """
    
    try:
        response = call_llm(prompt, json_format=True)
        response = response.strip().replace('```json', '').replace('```', '').strip()
        plan_data = json.loads(response)
        
        logger.info(f"Plan complete: {plan_data.get('product')} - {plan_data.get('theme')}")
        return plan_data
        
    except Exception as e:
        logger.error(f"Planning failed: {e}")
        fallback_product = recommended_products[0] if recommended_products else "Nutrimix"
        return {
            "product": fallback_product,
            "theme": "Holistic Millet-based Nutrition for Family Health",
            "persona": "Health-conscious parent looking for nutritious breakfast choices",
            "articles": [
                {
                    "type": "blog",
                    "title": f"The Ultimate Guide to Sprouted Millets with {fallback_product}",
                    "category": "Health",
                    "keywords": ["sprouted millets", "millet benefits", "healthy breakfast"]
                },
                {
                    "type": "health_tip",
                    "title": "5 Morning Wellness Habits for Sustained Energy",
                    "category": "Lifestyle",
                    "keywords": ["morning routine", "energy tips", "family wellness"]
                },
                {
                    "type": "nutrition_news",
                    "title": "Recent Clinical Research Shows Sprouted Grains Improve Nutrient Absorption",
                    "category": "Nutrition",
                    "keywords": ["sprouted grains", "nutrient absorption", "nutrition research"]
                },
                {
                    "type": "recipe",
                    "title": f"Quick and Healthy Sprouted {fallback_product} Breakfast Porridge",
                    "category": "Recipes",
                    "keywords": ["millet porridge recipe", "healthy breakfast recipe", f"{fallback_product} recipe"]
                },
                {
                    "type": "ingredient_spotlight",
                    "title": "Sprouted Ragi: The Iron-Rich Supergrain You Need to Know",
                    "category": "Nutrition",
                    "keywords": ["sprouted ragi", "ragi benefits", "iron rich food"]
                }
            ]
        }


def plan_news(
    news_items: List[Dict[str, Any]],
    recent_titles: List[str] = None,
    count: int = 5
) -> List[Dict[str, Any]]:
    """
    Select up to `count` real, distinct food/nutrition news stories to cover today.

    Unlike plan(), this makes no LLM call: the facts are already real (collected via
    FoodNewsCollector), so selection is a deterministic pick for topic diversity and
    freshness rather than a creative planning step.

    Args:
        news_items: Raw items from FoodNewsCollector.collect() (title, link, summary,
            source, query, suggested_category).
        recent_titles: Titles already covered recently, to avoid re-covering the same story.
        count: Max number of stories to select (default 5).

    Returns:
        List of planned news articles, each carrying the real source facts plus a
        derived category and keyword seed for the writer prompt.
    """
    recent_titles = recent_titles or []
    recent_lower = [t.lower() for t in recent_titles if t]

    if not news_items:
        logger.warning("No real food/nutrition news items available to plan from today.")
        return []

    # Group by originating query to pick one story per topic first (diversity),
    # then backfill from leftovers if a query came up empty or fully blocked.
    by_query: Dict[str, List[Dict[str, Any]]] = {}
    for item in news_items:
        by_query.setdefault(item.get("query", ""), []).append(item)

    def is_fresh(item: Dict[str, Any]) -> bool:
        title_lower = item.get("title", "").lower()
        if not title_lower:
            return False
        return not any(
            title_lower == prior or title_lower in prior or prior in title_lower
            for prior in recent_lower
        )

    selected: List[Dict[str, Any]] = []
    used_titles = set()

    # Round 1: one distinct story per query, in query order.
    for query_items in by_query.values():
        for item in query_items:
            if len(selected) >= count:
                break
            title_lower = item["title"].lower()
            if title_lower in used_titles or not is_fresh(item):
                continue
            selected.append(item)
            used_titles.add(title_lower)
            break

    # Round 2: backfill from any remaining fresh items if a query was empty/blocked.
    if len(selected) < count:
        for item in news_items:
            if len(selected) >= count:
                break
            title_lower = item["title"].lower()
            if title_lower in used_titles or not is_fresh(item):
                continue
            selected.append(item)
            used_titles.add(title_lower)

    planned = []
    for item in selected[:count]:
        planned.append({
            "source_title": item["title"],
            "summary": item.get("summary", ""),
            "link": item.get("link", ""),
            "source": item.get("source", "Google News"),
            "published": item.get("published", ""),
            "category": item.get("suggested_category", "Nutrition News"),
            "keywords": _extract_news_keywords(item["title"], item.get("summary", ""))
        })

    logger.info(f"News plan: selected {len(planned)}/{count} real stories.")
    return planned


def _extract_news_keywords(title: str, summary: str, limit: int = 5) -> List[str]:
    """Lightweight keyword seed from a real headline, no LLM call needed."""
    words = f"{title} {summary}".lower().split()
    keywords = []
    for word in words:
        clean = "".join(c for c in word if c.isalnum())
        if clean and len(clean) > 3 and clean not in _NEWS_STOP_WORDS and clean not in keywords:
            keywords.append(clean)
    return keywords[:limit]
