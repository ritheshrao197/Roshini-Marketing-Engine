"""
Telegram Agent - Responsible only for sending notifications.
Sends concise run summaries via Telegram to avoid oversized messages.
"""

import os
import datetime
from typing import Dict, Any, List
import requests

from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)


def notify(content: Dict[str, Any], seo_data: Dict[str, Any], upload_results: Dict[str, Any], package_path: str) -> bool:
    """
    Send Telegram notification with campaign run summaries.
    
    Args:
        content: Content from content generator.
        seo_data: SEO metadata compatibility object.
        upload_results: Results from uploader.
        package_path: Path to exported package.
    
    Returns:
        True if successful, False otherwise.
    """
    logger.info("Sending Telegram notification...")
    
    bot_token = Config.get('TELEGRAM_BOT_TOKEN')
    chat_id = Config.get('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        logger.warning("Telegram credentials missing. Skipping notification.")
        return False
        
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    theme = content.get('theme', 'N/A')
    
    # 1. Instagram summary
    insta = content.get('instagram', {})
    insta_headline = insta.get('headline', 'N/A')
    insta_caption = insta.get('caption', 'N/A')
    insta_summary = f"{insta_headline}\n(Caption: {insta_caption[:120]}...)"
    
    # 2. Generated Articles
    articles = content.get('blogs', [])
    articles_summary = []
    for art in articles:
        art_type = art.get('format', 'html') # fallback
        # Let's find category or format for type representation
        category = art.get('category', 'Blog')
        articles_summary.append(f"- [{category}] {art.get('title')}")
    articles_list_str = "\n".join(articles_summary) if articles_summary else "None"
    
    # 3. Draft IDs
    draft_ids = upload_results.get('draft_ids', [])
    draft_ids_str = ", ".join(draft_ids) if draft_ids else "None"
    
    # 4. Failures
    failed_payloads = upload_results.get('failed', [])
    failed_titles = [f.get('title', 'Untitled') for f in failed_payloads]
    failures_str = ", ".join(failed_titles) if failed_titles else "None"
    
    # Construct unified message
    message = f"""<b>🚀 Roshini Content Pipeline Summary</b>
<b>Date:</b> {date_str}
<b>Theme:</b> {theme}

📱 <b>Instagram Summary:</b>
{insta_summary}

📝 <b>Generated Articles:</b>
{articles_list_str}

📤 <b>Upload Status:</b>
- Draft IDs: <code>{draft_ids_str}</code>
- Failures: {failures_str}

📦 <b>Package Location:</b>
<code>{package_path}</code> (outputs/{date_str}.md/json/-api.json)
"""
    
    success = _send_message(message, bot_token, chat_id)
    
    # Send document if package exists
    if package_path and os.path.exists(package_path):
        if not _send_document(package_path, bot_token, chat_id):
            logger.warning("Failed to upload markdown package document, summary was sent successfully.")
            
    return success


def _send_message(message: str, bot_token: str, chat_id: str) -> bool:
    """Send HTML message via Telegram API."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # Limit length
    if len(message) > 4000:
        message = message[:3900] + "\n\n<i>[Truncated...]</i>"
        
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Failed to send HTML Telegram message: {e}")
        # Try sending plain text if HTML parsing failed
        try:
            payload['parse_mode'] = None
            response = requests.post(url, json=payload, timeout=15)
            response.raise_for_status()
            return True
        except Exception as e2:
            logger.error(f"Failed to send plain Telegram message: {e2}")
            return False


def _send_document(file_path: str, bot_token: str, chat_id: str) -> bool:
    """Send document via Telegram API."""
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    try:
        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': chat_id}
            response = requests.post(url, data=data, files=files, timeout=30)
            response.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"Failed to send document: {e}")
        return False