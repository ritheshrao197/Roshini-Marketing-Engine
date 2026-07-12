"""
Duplicate Checker Agent - Responsible only for checking duplicates.
Searches existing blogs and suggests alternative topics if duplicates found.
Runs before content generation to optimize API usage.
"""

import json
import difflib
import re
from typing import Dict, Any, List, Tuple
import requests

from config import Config
from utils.logger import get_logger
from llm import call_llm

logger = get_logger(__name__)


def check_duplicates(plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check planned articles for duplicates and suggest alternatives.
    
    Args:
        plan_data: Plan from planner agent.
    
    Returns:
        Updated plan with duplicates resolved in-place.
    """
    logger.info("Checking planned articles for duplicates...")
    
    backend_url = Config.get('BACKEND_BASE_URL', 'https://roshini-backend.onrender.com/api')
    product = plan_data.get('product', 'Nutrimix')
    theme = plan_data.get('theme', 'Health & Wellness')
    articles = plan_data.get('articles', [])
    
    for i, article in enumerate(articles):
        title = article.get('title', '')
        keywords = article.get('keywords', [])
        
        # Generate slug
        slug = re.sub(r'[^a-z0-9\s-]', '', title.lower())
        slug = re.sub(r'[\s-]+', '-', slug).strip('-')
        
        is_duplicate, reason = _check_single_duplicate(
            title=title,
            slug=slug,
            keywords=keywords,
            backend_url=backend_url
        )
        
        if is_duplicate:
            logger.warning(f"Duplicate detected for planned article '{title}': {reason}")
            # Regenerate planned title & keywords
            new_info = _regenerate_planned_title(
                old_title=title,
                reason=reason,
                product=product,
                theme=theme,
                article_type=article.get('type', 'blog')
            )
            article['title'] = new_info.get('title', title)
            article['keywords'] = new_info.get('keywords', keywords)
            logger.info(f"   🔄 Regenerated planned title to: '{article['title']}'")
            
    return plan_data


def _check_single_duplicate(title: str, slug: str, keywords: List[str], backend_url: str) -> Tuple[bool, str]:
    """Check if a single piece of content is duplicate in the database."""
    if not title:
        return False, "No title to check"
    
    # Search existing blogs
    search_url = f"{backend_url.rstrip('/')}/vlogs/search"
    try:
        response = requests.get(search_url, params={"query": title}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            existing_blogs = data.get('vlogs', []) or data.get('blogs', []) or data.get('data', [])
            
            for blog in existing_blogs:
                # Check title similarity
                existing_title = blog.get('title', '')
                similarity = difflib.SequenceMatcher(None, title.lower(), existing_title.lower()).ratio()
                
                if similarity > 0.8:
                    return True, f"Title similarity of {similarity:.2f} > 80% with existing: '{existing_title}'"
                
                # Check slug match
                existing_slug = blog.get('slug', '')
                if slug and existing_slug == slug:
                    return True, f"Slug '{slug}' already exists in database"
                
                # Check keyword matches
                existing_tags = blog.get('vTags', [])
                existing_keywords = []
                for tag in existing_tags:
                    if isinstance(tag, dict):
                        existing_keywords.append(tag.get('cName', '').lower())
                    else:
                        existing_keywords.append(str(tag).lower())
                
                for kw in keywords:
                    if kw.lower() in existing_keywords or kw.lower() in existing_title.lower():
                        return True, f"Keyword '{kw}' matches existing blog: '{existing_title}'"
    
    except Exception as e:
        logger.error(f"Duplicate check failed (ignoring to proceed): {e}")
    
    return False, "No duplicates found"


def _regenerate_planned_title(old_title: str, reason: str, product: str, theme: str, article_type: str) -> Dict[str, Any]:
    """Generate a new unique title and keywords for a planned article to avoid duplicate."""
    prompt = f"""
    We planned an article of type '{article_type}' with title '{old_title}' for the product '{product}' and theme '{theme}'.
    However, we detected a duplicate in the database:
    Reason: {reason}
    
    Suggest a completely different, unique title and a fresh set of keywords for this article that matches the theme and type but will not conflict with existing content.
    Do NOT write the article. Only return a new title and keywords.
    
    Return as valid JSON:
    {{
        "title": "new unique title (Healthline style)",
        "keywords": ["new", "keywords"]
    }}
    """
    
    try:
        response = call_llm(prompt, json_format=True)
        response_clean = response.strip().replace('```json', '').replace('```', '').strip()
        return json.loads(response_clean)
    except Exception as e:
        logger.error(f"Title regeneration failed: {e}")
        # Return fallback modification
        return {
            "title": f"New Insights: {old_title}",
            "keywords": ["wellness", product.lower(), "health tips"]
        }