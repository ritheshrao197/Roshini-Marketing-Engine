"""
SEO Generator Agent - Responsible only for generating SEO metadata.
Creates SEO titles, slugs, meta descriptions, keywords, and excerpts.
"""

from typing import Dict, Any, List
from utils.logger import get_logger
from llm import call_llm

logger = get_logger(__name__)


def generate_seo(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate SEO metadata for all content.
    
    Args:
        content: Content from content generator.
    
    Returns:
        SEO metadata for each piece of content.
    """
    logger.info("Generating SEO metadata...")
    
    seo_data = {
        "pages": [],
        "global_keywords": [],
        "canonical_urls": []
    }
    
    # Generate SEO for each blog
    for blog in content.get('blogs', []):
        seo_page = _generate_blog_seo(blog, content.get('product', ''))
        seo_data['pages'].append(seo_page)
    
    # Generate global keywords
    seo_data['global_keywords'] = _generate_global_keywords(content)
    
    # Generate canonical URLs
    seo_data['canonical_urls'] = _generate_canonical_urls(content)
    
    logger.info(f"SEO generated for {len(seo_data['pages'])} pages")
    return seo_data


def _generate_blog_seo(blog: Dict[str, Any], product: str) -> Dict[str, Any]:
    """Generate SEO for a single blog."""
    title = blog.get('title', '')
    content_text = blog.get('content', '')
    
    prompt = f"""
    Generate SEO metadata for this blog:
    
    Title: {title}
    Product: {product}
    Content preview: {content_text[:500]}
    
    Return ONLY valid JSON:
    {{
        "seo_title": "optimized title (60 chars max)",
        "slug": "url-friendly-slug",
        "meta_description": "meta description (160 chars max)",
        "keywords": ["keyword1", "keyword2", "keyword3"],
        "excerpt": "short excerpt (155 chars max)",
        "canonical_url": "canonical-url"
    }}
    """
    
    try:
        response = call_llm(prompt, json_format=True)
        seo = json.loads(response.strip().replace('```json', '').replace('```', '').strip())
        
        # Ensure values are within limits
        seo['seo_title'] = seo.get('seo_title', title)[:60]
        seo['meta_description'] = seo.get('meta_description', '')[:160]
        seo['excerpt'] = seo.get('excerpt', '')[:155]
        
        return seo
        
    except Exception as e:
        logger.error(f"SEO generation failed for {title}: {e}")
        # Fallback SEO
        slug = title.lower().replace(' ', '-').replace("'", '').replace('"', '')
        return {
            "seo_title": title[:60],
            "slug": slug[:50],
            "meta_description": f"Learn about {title} with {product}",
            "keywords": [product.lower(), title.lower().split()[0].lower()],
            "excerpt": title[:155],
            "canonical_url": slug[:50]
        }


def _generate_global_keywords(content: Dict[str, Any]) -> List[str]:
    """Generate global keywords for the entire campaign."""
    prompt = f"""
    Generate 10-15 global keywords for this content campaign:
    
    Product: {content.get('product', '')}
    Theme: {content.get('theme', '')}
    Topics: {[b.get('title', '') for b in content.get('blogs', [])]}
    
    Return as JSON array of strings.
    """
    
    try:
        response = call_llm(prompt, json_format=True)
        keywords = json.loads(response.strip().replace('```json', '').replace('```', '').strip())
        if isinstance(keywords, list):
            return keywords
    except Exception as e:
        logger.error(f"Global keywords generation failed: {e}")
    
    return ["health", "wellness", "nutrition", "millets", "family", "recipes", "healthy-living"]


def _generate_canonical_urls(content: Dict[str, Any]) -> List[str]:
    """Generate canonical URLs for content."""
    base_url = "https://roshini.com/blog"
    urls = []
    
    for blog in content.get('blogs', []):
        title = blog.get('title', '')
        slug = title.lower().replace(' ', '-').replace("'", '').replace('"', '')
        urls.append(f"{base_url}/{slug[:50]}")
    
    return urls