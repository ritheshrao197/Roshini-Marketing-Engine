"""
Telegram Agent - Responsible only for sending notifications.
Sends summary, markdown package, and draft IDs via Telegram.
"""

import os
import datetime
from typing import Dict, Any, List
import requests

from config import Config
from utils.logger import get_logger
from utils.files import ensure_directory

logger = get_logger(__name__)


def notify(content: Dict[str, Any], seo_data: Dict[str, Any], upload_results: Dict[str, Any], package_path: str) -> bool:
    """
    Send Telegram notification with content summary.
    
    Args:
        content: Content from content generator.
        seo_data: SEO metadata.
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
    
    # Build messages
    messages = _build_messages(content, upload_results)
    
    # Send each message
    success = True
    for message in messages:
        if not _send_message(message, bot_token, chat_id):
            success = False
    
    # Send package document
    if package_path and os.path.exists(package_path):
        if not _send_document(package_path, bot_token, chat_id):
            success = False
    
    logger.info(f"Telegram notification {'successful' if success else 'failed'}")
    return success


def _build_messages(content: Dict[str, Any], upload_results: Dict[str, Any]) -> List[str]:
    """Build Telegram messages."""
    product = content.get('product', 'Nutrimix')
    theme = content.get('theme', 'Health & Wellness')
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    draft_ids = upload_results.get('draft_ids', [])
    
    messages = []
    
    # Summary message
    summary = f"""
📅 <b>Daily Marketing Package: {date_str}</b>

<b>Product:</b> {product}
<b>Theme:</b> {theme}
<b>Blogs:</b> {len(content.get('blogs', []))}
<b>Recipes:</b> {len(content.get('recipes', []))}
<b>Health Tips:</b> {len(content.get('health_tips', []))}

<b>Upload Status:</b>
- Drafts Uploaded: {len(draft_ids)}
- Draft IDs: {', '.join(draft_ids[:3]) + ('...' if len(draft_ids) > 3 else '')}

━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    messages.append(summary)
    
    # Instagram caption
    if content.get('instagram'):
        instagram = content.get('instagram', {})
        caption = f"""
📱 <b>Instagram Post</b>

<b>Headline:</b> {instagram.get('headline', 'N/A')}

<b>Caption:</b>
{instagram.get('caption', 'N/A')[:500]}

<b>Hashtags:</b>
{instagram.get('hashtags', {}).get('brand', []) + instagram.get('hashtags', {}).get('niche', []) + instagram.get('hashtags', {}).get('discovery', [])}
"""
        messages.append(caption)
    
    # Health tips
    if content.get('health_tips'):
        tips = "\n".join([f"- {tip}" for tip in content.get('health_tips', [])])
        messages.append(f"💡 <b>Health Tips</b>\n\n{tips}")
    
    return messages


def _send_message(message: str, bot_token: str, chat_id: str) -> bool:
    """Send a message via Telegram."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # Truncate if too long
    if len(message) > 4000:
        message = message[:3900] + "\n\n<i>[Truncated]</i>"
    
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
        logger.error(f"Failed to send Telegram message: {e}")
        
        # Try without HTML formatting
        try:
            payload['parse_mode'] = None
            response = requests.post(url, json=payload, timeout=15)
            response.raise_for_status()
            return True
        except Exception as e2:
            logger.error(f"Failed to send plain Telegram message: {e2}")
            return False


def _send_document(file_path: str, bot_token: str, chat_id: str) -> bool:
    """Send a document via Telegram."""
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