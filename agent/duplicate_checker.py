"""
Duplicate Checker Agent - Responsible only for checking duplicates.
Searches existing blogs and suggests alternative topics if duplicates found.
"""

import difflib
from typing import Dict, Any, List, Tuple
import requests

from config import Config
from utils.logger import get_logger
from llm import call_llm

logger = get_logger(__name__)


def check_duplicates(content: Dict[str, Any], seo_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check for duplicate content and suggest alternatives.
    
    Args:
        content: Content from content generator.
        seo_data: SEO metadata.
    
    Returns:
        Updated content with duplicates resolved.
    """
    logger.info("Checking for duplicates...")
    
    backend_url = Config.get('BACKEND_BASE_URL', 'https://roshini-backend.onrender.com/api')
    
    # Check each blog for duplicates
    for i, blog in enumerate(content.get('blogs', [])):
        title = blog.get('title', '')
        slug = seo_data.get('pages', [{}])[i].get('slug', '')
        keywords = seo_data.get('pages', [{}])[i].get('keywords', [])
        
        # Check for duplicates
        is_duplicate, reason = _check_single_duplicate(
            title=title,
            slug=slug,
            keywords=keywords,
            backend_url=backend_url
        )
        
        if is_duplicate:
            logger.warning(f"Duplicate detected for '{title}': {reason}")
            # Regenerate topic
            new_blog = _regenerate_topic(title, reason, content.get('product', 'Nutrimix'))
            content['blogs'][i] = new_blog
    
    return content


def _check_single_duplicate(title: str, slug: str, keywords: List[str], backend_url: str) -> Tuple[bool, str]:
    """Check if a single piece of content is duplicate."""
    if not title:
        return False, "No title to check"
    
    # Search existing blogs
    search_url = f"{backend_url}/vlogs/search"
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
                    return True, f"Title similarity of {similarity:.2f} > 80%"
                
                # Check slug match
                existing_slug = blog.get('slug', '')
                if slug and existing_slug == slug:
                    return True, f"Slug '{slug}' already exists"
                
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
                        return True, f"Keyword '{kw}' matches existing blog"
    
    except Exception as e:
        logger.error(f"Duplicate check failed: {e}")
    
    return False, "No duplicates found"


def _regenerate_topic(old_title: str, reason: str, product: str) -> Dict[str, Any]:
    """Generate a new topic to avoid duplicate."""
    prompt = f"""
    We detected a duplicate for topic: {old_title}
    Reason: {reason}
    
    Product: {product}
    
    Suggest a completely different, unique topic that doesn't conflict.
    Return as valid JSON:
    {{
        "title": "new unique title",
        "content": "new content (500-800 words)",
        "excerpt": "new excerpt",
        "tags": ["new", "tags"]
    }}
    """
    
    try:
        response = call_llm(prompt, json_format=True)
        return json.loads(response.strip().replace('```json', '').replace('```', '').strip())
    except Exception as e:
        logger.error(f"Topic regeneration failed: {e}")
        return {
            "title": f"{product} Wellness: Alternative Angle",
            "content": f"Discover a fresh perspective on {product} and wellness...",
            "excerpt": "A unique take on health and nutrition.",
            "tags": [product.lower(), "wellness", "health"]
        }