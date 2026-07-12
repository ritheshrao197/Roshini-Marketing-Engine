"""
Uploader Agent - Responsible only for uploading to backend.
Posts to /api/blogs/import with 3 retries, saves locally if failed.
"""

import os
import json
import datetime
from typing import Dict, Any, Optional
import requests

from config import Config
from utils.logger import get_logger
from utils.files import ensure_directory

logger = get_logger(__name__)


def upload(content: Dict[str, Any], seo_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Upload blogs to backend with retries.
    
    Args:
        content: Content from content generator.
        seo_data: SEO metadata.
    
    Returns:
        Upload results with draft IDs.
    """
    logger.info("Uploading content to backend...")
    
    backend_url = Config.get('BACKEND_BASE_URL', 'https://roshini-backend.onrender.com/api')
    categories = _fetch_categories(backend_url)
    
    results = {
        "uploaded": [],
        "failed": [],
        "draft_ids": []
    }
    
    # Upload each blog
    for i, blog in enumerate(content.get('blogs', [])):
        seo_page = seo_data.get('pages', [{}])[i] if i < len(seo_data.get('pages', [])) else {}
        
        # Build payload
        payload = _build_payload(blog, seo_page, content.get('product', 'Nutrimix'))
        
        # Map category
        payload['category'] = _map_category(payload.get('category', 'General'), categories)
        
        # Upload with retries
        result = _upload_with_retry(payload, backend_url)
        
        if result and result.get('success'):
            results['uploaded'].append(result)
            results['draft_ids'].append(result.get('draft_id', 'unknown'))
        else:
            results['failed'].append(payload)
            # Save failed upload locally
            _save_failed_upload(payload)
    
    logger.info(f"Upload complete: {len(results['uploaded'])} uploaded, {len(results['failed'])} failed")
    return results


def _fetch_categories(backend_url: str) -> list:
    """Fetch active categories from backend."""
    try:
        url = f"{backend_url}/vlog-categories"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data.get('Categories', [])
    except Exception as e:
        logger.error(f"Failed to fetch categories: {e}")
    return []


def _build_payload(blog: Dict[str, Any], seo_page: Dict[str, Any], product: str) -> Dict[str, Any]:
    """Build upload payload."""
    return {
        "title": blog.get('title', ''),
        "content": blog.get('content', ''),
        "format": "markdown",
        "category": "General",
        "tags": blog.get('tags', []),
        "excerpt": seo_page.get('excerpt', '') or blog.get('excerpt', ''),
        "seoTitle": seo_page.get('seo_title', ''),
        "seoDescription": seo_page.get('meta_description', ''),
        "seoKeywords": seo_page.get('keywords', []),
        "canonicalUrl": seo_page.get('canonical_url', ''),
        "ogImage": "",
        "imageUrl": "",
        "status": "Draft",
        "isPublished": False,
        "product": product
    }


def _map_category(category_name: str, categories: list) -> str:
    """Map category name to valid category."""
    if not category_name:
        return "General"
    
    category_name_clean = category_name.lower().strip()
    
    # Try exact match
    for cat in categories:
        c_name = cat.get('cName', '')
        if c_name.lower().strip() == category_name_clean:
            return c_name
    
    # Try substring match
    for cat in categories:
        c_name = cat.get('cName', '')
        if c_name.lower().strip() in category_name_clean or category_name_clean in c_name.lower().strip():
            return c_name
    
    return "General"


def _upload_with_retry(payload: Dict[str, Any], backend_url: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    """Upload with retry logic."""
    url = f"{backend_url}/blogs/import"
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Upload attempt {attempt} of {max_retries}")
            response = requests.post(url, json=payload, timeout=15)
            
            if response.status_code in [200, 201]:
                data = response.json()
                blog_info = data.get('blog', {})
                return {
                    "success": True,
                    "draft_id": blog_info.get('_id', 'unknown'),
                    "slug": blog_info.get('slug', ''),
                    "title": blog_info.get('title', '')
                }
            else:
                logger.warning(f"Upload returned {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"Upload attempt {attempt} failed: {e}")
    
    return None


def _save_failed_upload(payload: Dict[str, Any]) -> None:
    """Save failed upload locally."""
    try:
        ensure_directory("outputs/failed-uploads")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(x for x in payload.get('title', 'untitled') if x.isalnum() or x in ' -_').strip()
        filename = f"outputs/failed-uploads/{timestamp}_{safe_title}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=4)
        
        logger.info(f"Failed upload saved to {filename}")
        
        # Log error
        with open("outputs/upload_errors.log", "a", encoding='utf-8') as f:
            f.write(f"[{datetime.datetime.now().isoformat()}] Failed to upload '{payload.get('title')}' after 3 attempts.\n")
            
    except Exception as e:
        logger.error(f"Failed to save failed upload: {e}")