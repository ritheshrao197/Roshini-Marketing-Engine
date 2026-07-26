"""
Planner Agent - Responsible only for planning content strategy.
Chooses product, theme, customer persona, and website topics.
"""

import json
from typing import Dict, Any
from utils.logger import get_logger
from llm import call_llm

logger = get_logger(__name__)


def plan(research_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Choose product, theme, persona, and a list of 5 specialized articles based on research.
    
    Args:
        research_data: Structured research data from research agent.
    
    Returns:
        Plan with product, theme, persona, instagram plan, and a list of 5 articles to generate.
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
    
    Research Data:
    - Trending Topics: {trending_topics[:10]}
    - Health News: {health_news[:5]}
    - Niche Keywords: {keywords[:15]}
    - Available Products: {products}
    - Recommended Product: {recommended_products}
    - Recent campaign titles (do not repeat their subject, structure, or angle): {recent_titles[:25]}
    - Recent campaign summaries: {recent_campaigns[:7]}
    - Blocked topics: {blocked_topics}
    - Recently used keywords: {recent_keywords[:40]}

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
       
    5. Instagram post plan:
       - `headline`: Hooky headline for an Instagram post
       - `topic`: Topic description for the post

    Return ONLY a valid JSON object matching this schema:
    {{
        "product": "Product Name",
        "theme": "Theme Name",
        "persona": "Persona Description",
        "instagram": {{
            "headline": "headline here",
            "topic": "topic description here"
        }},
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
            "instagram": {
                "headline": f"Why we choose wholesome {fallback_product} for breakfast!",
                "topic": f"Benefits of sprouted grains in {fallback_product}"
            },
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
