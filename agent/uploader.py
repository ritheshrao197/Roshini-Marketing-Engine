"""
Uploader Agent - Responsible only for uploading to backend.
Posts to /api/blogs/import with 3 retries, saves locally if failed.
"""

import os
import json
import datetime
from typing import Dict, Any, Optional, List
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
    api_key = Config.get('WEBSITE_API_KEY') or os.getenv('WEBSITE_API_KEY')
    categories = _fetch_categories(backend_url)
    
    results = {
        "uploaded": [],
        "failed": [],
        "draft_ids": []
    }
    
    # Build payloads for all blogs
    payloads = []
    for i, blog in enumerate(content.get('blogs', [])):
        seo_page = seo_data.get('pages', [{}])[i] if i < len(seo_data.get('pages', [])) else {}
        payload = _build_payload(blog, seo_page, content.get('product', 'Nutrimix'))
        payload['category'] = _map_category(payload.get('category', 'General'), categories)
        payloads.append(payload)
    
    if not payloads:
        logger.info("No blogs to upload")
        return results
    
    # Try bulk upload first, fall back to individual uploads
    if len(payloads) > 1:
        bulk_result = _bulk_upload_with_retry(payloads, backend_url, api_key)
        if bulk_result and bulk_result.get('success'):
            results['uploaded'] = bulk_result.get('imported', [])
            results['draft_ids'] = bulk_result.get('draft_ids', [])
            failed_payloads = bulk_result.get('failed_payloads', [])
            for failed in failed_payloads:
                results['failed'].append(failed)
                _save_failed_upload(failed)
            logger.info(f"Bulk upload complete: {len(results['uploaded'])} uploaded, {len(results['failed'])} failed")
            return results
        else:
            logger.warning("Bulk upload failed, falling back to individual uploads")
    
    # Individual uploads (either fallback or single blog)
    for payload in payloads:
        result = _upload_with_retry(payload, backend_url, api_key)
        
        if result and result.get('success'):
            results['uploaded'].append(result)
            results['draft_ids'].append(result.get('draft_id', 'unknown'))
        else:
            results['failed'].append(payload)
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
        else:
            logger.warning(f"Failed to fetch categories: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to fetch categories: {e}")
    return []


def _get_headers(api_key: Optional[str] = None) -> Dict[str, str]:
    """Build request headers."""
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key
    return headers


def _build_payload(blog: Dict[str, Any], seo_page: Dict[str, Any], product: str) -> Dict[str, Any]:
    """Build upload payload."""
    # Determine content format - if it starts with HTML tag, it's HTML; otherwise markdown
    content = blog.get('content', '')
    is_html = content.strip().startswith('<') if content else False
    
    payload = {
        "title": blog.get('title', ''),
        "content": content,
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
    
    # Only set format to markdown if content is not HTML
    if not is_html:
        payload["format"] = "markdown"
    
    return payload


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


def _upload_with_retry(payload: Dict[str, Any], backend_url: str, api_key: Optional[str] = None, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    """Upload single blog with retry logic."""
    url = f"{backend_url}/blogs/import"
    headers = _get_headers(api_key)
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Upload attempt {attempt} of {max_retries}")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
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
                logger.warning(f"Upload returned {response.status_code}: {response.text[:500]}")
                
        except Exception as e:
            logger.error(f"Upload attempt {attempt} failed: {e}")
    
    return None


def _bulk_upload_with_retry(payloads: List[Dict[str, Any]], backend_url: str, api_key: Optional[str] = None, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    """Upload multiple blogs in bulk with retry logic."""
    url = f"{backend_url}/blogs/import/bulk"
    headers = _get_headers(api_key)
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Bulk upload attempt {attempt} of {max_retries} ({len(payloads)} blogs)")
            response = requests.post(url, json={"blogs": payloads}, headers=headers, timeout=60)
            
            if response.status_code in [200, 201]:
                data = response.json()
                imported_blogs = data.get('importedBlogs', [])
                return {
                    "success": True,
                    "imported": [{"success": True, "title": b.get('title', ''), "slug": b.get('slug', ''), "draft_id": "bulk"} for b in imported_blogs],
                    "draft_ids": [b.get('_id', 'unknown') for b in imported_blogs],
                    "failed_payloads": [],
                    "importedCount": data.get('importedCount', 0),
                    "failedCount": data.get('failedCount', 0)
                }
            else:
                logger.warning(f"Bulk upload returned {response.status_code}: {response.text[:500]}")
                
        except Exception as e:
            logger.error(f"Bulk upload attempt {attempt} failed: {e}")
    
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