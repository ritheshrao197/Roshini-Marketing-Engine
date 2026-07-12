"""
Uploader Agent - Responsible only for uploading to backend.
Posts to /api/blogs/import individually with rate limit retries (429 / Retry-After)
and fallback endpoints, saving failed payloads locally.
"""

import os
import json
import datetime
import time
from typing import Dict, Any, Optional, List
import requests

from config import Config
from utils.logger import get_logger
from utils.files import ensure_directory

logger = get_logger(__name__)


def upload(content: Dict[str, Any], seo_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Upload articles individually to the backend with retry and rate-limiting logic.
    
    Args:
        content: Content from content generator containing articles in 'blogs'.
        seo_data: SEO metadata (legacy parameter, unused since SEO is in articles).
    
    Returns:
        Upload results dictionary.
    """
    logger.info("Uploading content to backend (individual mode)...")
    
    backend_url = Config.get('BACKEND_BASE_URL', 'https://roshini-backend.onrender.com/api')
    api_key = Config.get('WEBSITE_API_KEY') or os.getenv('WEBSITE_API_KEY')
    
    logger.info(f"Backend URL: {backend_url}")
    logger.info(f"API Key configured: {'Yes' if api_key else 'No'}")
    
    # Test backend connectivity
    if not _test_backend_connection(backend_url):
        logger.warning("Backend connectivity check failed. Proceeding with upload attempts anyway...")
        
    categories = _fetch_categories(backend_url)
    logger.info(f"Fetched {len(categories)} categories from backend.")
    
    results = {
        "uploaded": [],
        "failed": [],
        "draft_ids": []
    }
    
    articles = content.get('blogs', [])
    if not articles:
        logger.info("No articles to upload.")
        return results
        
    logger.info(f"Prepared {len(articles)} articles for individual upload.")
    
    for idx, article in enumerate(articles):
        # Build payload
        payload = article.copy()
        
        # Map category
        payload['category'] = _map_category(payload.get('category', 'General'), categories)
        
        # Ensure product context is set
        payload['product'] = content.get('product', 'Nutrimix')
        
        # Ensure format is set to html
        payload['format'] = 'html'
        
        logger.info(f"Uploading article {idx + 1}/{len(articles)}: '{payload.get('title')[:50]}'...")
        
        draft_id = _upload_article_with_retry(payload, backend_url, api_key)
        
        if draft_id:
            results['uploaded'].append({
                "title": payload.get('title'),
                "slug": payload.get('slug'),
                "draft_id": draft_id
            })
            results['draft_ids'].append(draft_id)
            logger.info(f"   ✅ Successfully uploaded. Draft ID: {draft_id}")
        else:
            results['failed'].append(payload)
            _save_failed_upload(payload)
            logger.warning(f"   ❌ Upload failed for '{payload.get('title')[:50]}' after all retries.")
            
    logger.info(f"Upload complete: {len(results['uploaded'])} uploaded, {len(results['failed'])} failed.")
    return results


def _test_backend_connection(backend_url: str) -> bool:
    """Test basic connectivity to the backend."""
    try:
        test_url = backend_url.rstrip('/') + '/vlog-categories'
        response = requests.get(test_url, timeout=15)
        return response.status_code in [200, 404]
    except Exception as e:
        logger.error(f"Backend connectivity test failed: {e}")
        return False


def _fetch_categories(backend_url: str) -> list:
    """Fetch active categories from backend."""
    try:
        url = f"{backend_url.rstrip('/')}/vlog-categories"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data.get('Categories', []) or data.get('categories', [])
    except Exception as e:
        logger.error(f"Failed to fetch categories: {e}")
    return []


def _map_category(category_name: str, categories: list) -> str:
    """Map category name to a valid backend category."""
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


def _upload_article_with_retry(payload: Dict[str, Any], backend_url: str, api_key: Optional[str] = None) -> Optional[str]:
    """Upload a single article with 3 attempts, exponential backoff, and 429 Retry-After support."""
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key
        
    endpoints = [
        f"{backend_url.rstrip('/')}/blogs/import",
        f"{backend_url.rstrip('/')}/vlogs/import"
    ]
    
    for endpoint in endpoints:
        for attempt in range(1, 4):  # 3 attempts
            try:
                logger.info(f"   Attempt {attempt}/3 -> {endpoint}")
                response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    blog_info = data.get('blog', {}) or data.get('data', {}) or data
                    draft_id = blog_info.get('_id') or blog_info.get('id') or data.get('draft_id') or 'unknown_id'
                    return str(draft_id)
                    
                elif response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    delay = 2 ** attempt  # fallback backoff delay
                    if retry_after:
                        try:
                            delay = int(retry_after)
                            logger.warning(f"   Rate limited (429). Retry-After header: wait {delay} seconds.")
                        except ValueError:
                            logger.warning(f"   Rate limited (429). Invalid Retry-After: wait {delay} seconds (backoff).")
                    else:
                        logger.warning(f"   Rate limited (429). No Retry-After. Wait {delay} seconds (backoff).")
                    
                    time.sleep(delay)
                    continue  # retry same endpoint
                    
                elif response.status_code == 404:
                    logger.warning(f"   Endpoint not found: {endpoint}. Trying fallback endpoint...")
                    break  # try the next endpoint in the outer loop
                    
                else:
                    logger.warning(f"   Server returned status {response.status_code}: {response.text[:200]}")
                    delay = 2 ** attempt
                    time.sleep(delay)
                    continue
                    
            except Exception as e:
                logger.error(f"   Connection attempt {attempt} failed: {e}")
                delay = 2 ** attempt
                time.sleep(delay)
                continue
                
    return None


def _save_failed_upload(payload: Dict[str, Any]) -> None:
    """Save failed payload locally as JSON."""
    try:
        ensure_directory("outputs/failed-uploads")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(x for x in payload.get('title', 'untitled') if x.isalnum() or x in ' -_').strip()
        filename = f"outputs/failed-uploads/{timestamp}_{safe_title}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=4)
        
        logger.info(f"Failed upload saved locally to {filename}")
        
        # Log to errors file
        with open("outputs/upload_errors.log", "a", encoding='utf-8') as f:
            f.write(f"[{datetime.datetime.now().isoformat()}] Failed to upload '{payload.get('title')}' after all attempts.\n")
            
    except Exception as e:
        logger.error(f"Failed to save failed upload locally: {e}")