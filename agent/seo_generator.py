"""
SEO Generator Agent - Re-purposed to serve as a validator and missing-value generator.
Validates SEO Title, Description, Keywords, Slug, and Canonical Url.
Fills/fixes missing or invalid values in-place inside the content structure.
"""

import re
from typing import Dict, Any, List
from utils.logger import get_logger

logger = get_logger(__name__)


def _truncate_at_word(text: str, limit: int) -> str:
    """Truncate text to at most `limit` chars without cutting a word in half."""
    text = text.strip()
    if len(text) <= limit:
        return text
    truncated = text[:limit].rsplit(' ', 1)[0].rstrip(' :,-')
    return truncated or text[:limit]


def generate_seo(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and correct SEO metadata within the articles in-place.
    
    Args:
        content: Content dictionary from content generator.
    
    Returns:
        SEO metadata ledger mapping for backward compatibility.
    """
    logger.info("Validating and correcting SEO fields in generated articles...")
    
    seo_data = {
        "pages": [],
        "global_keywords": [],
        "canonical_urls": []
    }
    
    blogs = content.get('blogs', [])
    for blog in blogs:
        title = blog.get('title', 'Untitled')
        product = content.get('product', 'Nutrimix')
        
        # 1. Validate / generate Slug
        slug = blog.get('slug', '').strip()
        if not slug:
            slug = re.sub(r'[^a-z0-9\s-]', '', title.lower())
            slug = re.sub(r'[\s-]+', '-', slug).strip('-')
        blog['slug'] = slug
        
        # 2. Validate / generate SEO Title (target 30 - 60 characters, keyword-first,
        # never cut mid-word - a title tag chopped mid-word reads as broken in search results)
        seo_title = blog.get('seoTitle', '').strip()
        if not seo_title or len(seo_title) < 10 or len(seo_title) > 60:
            branded = f"{title} | Roshinis"
            seo_title = branded if len(branded) <= 60 else _truncate_at_word(title, 60)
        blog['seoTitle'] = seo_title[:60]

        # 3. Validate / generate Meta Description (target 80 - 160 characters). A
        # weak/generic description hurts click-through even when the ranking is good,
        # so the fallback chain prefers the real excerpt over a templated line.
        seo_desc = blog.get('seoDescription', '').strip()
        if not seo_desc or len(seo_desc) < 40 or len(seo_desc) > 160:
            excerpt = blog.get('excerpt', '').strip()
            if excerpt and 40 <= len(excerpt) <= 160:
                seo_desc = excerpt
            elif excerpt:
                seo_desc = _truncate_at_word(excerpt, 157) + "..."
            else:
                text_only = re.sub(r'<[^>]+>', ' ', blog.get('content', ''))
                text_only = re.sub(r'\s+', ' ', text_only).strip()
                seo_desc = (
                    _truncate_at_word(text_only, 157) + "..." if text_only
                    else f"{title}: practical, science-backed guidance from Roshini's Home Products."
                )
        blog['seoDescription'] = seo_desc[:160]

        # 4. Validate / generate Keywords (ensure at least 3 keywords). Defaults lean
        # on this article's own category/product rather than a fixed generic trio, so
        # multiple articles in the same campaign don't end up competing for identical
        # fallback keywords.
        keywords = blog.get('seoKeywords') or blog.get('tags') or []
        if not isinstance(keywords, list):
            keywords = [str(keywords)]
        if len(keywords) < 3:
            category = (blog.get('category') or '').strip().lower()
            defaults = [product.lower(), category, "healthy diet", "nutrition", "wellness"]
            for default in defaults:
                if default and default not in [kw.lower() for kw in keywords]:
                    keywords.append(default)
        blog['seoKeywords'] = keywords[:10]  # limit to 10 keywords
        blog['tags'] = keywords[:10]
        
        # 5. Validate / generate Canonical URL
        canonical = blog.get('canonicalUrl', '').strip()
        if not canonical or not canonical.startswith('http'):
            canonical = f"https://roshinis.com/blog/{blog['slug']}"
        blog['canonicalUrl'] = canonical
        
        # Build compatibility pages entry
        seo_data['pages'].append({
            "seo_title": blog['seoTitle'],
            "slug": blog['slug'],
            "meta_description": blog['seoDescription'],
            "keywords": blog['seoKeywords'],
            "excerpt": blog.get('excerpt', ''),
            "canonical_url": blog['canonicalUrl']
        })
        
        seo_data['canonical_urls'].append(blog['canonicalUrl'])
        seo_data['global_keywords'].extend(blog['seoKeywords'])
        
    seo_data['global_keywords'] = list(dict.fromkeys(seo_data['global_keywords']))
    
    logger.info(f"SEO Validation complete: Checked and polished {len(blogs)} articles.")
    return seo_data