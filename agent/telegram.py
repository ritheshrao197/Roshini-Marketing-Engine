"""
Telegram Agent - Responsible only for sending notifications.
Sends the daily Instagram post (generated image + bilingual captions) to Telegram
as a normal chat message - no file/document attachments.
"""

import os
from typing import Dict, Any, Optional
import requests

from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)


def notify(post: Dict[str, Any], image_path: Optional[str]) -> bool:
    """
    Send the daily Instagram post to Telegram: the generated image (with a short
    caption) when available, followed by a normal text message with the full
    bilingual captions and hashtags. If image generation failed, the image
    prompt is included in the text message instead, so the post is never lost.

    Args:
        post: Instagram post dict from instagram_generator.
        image_path: Local path to the generated image, if any.

    Returns:
        True if at least one notification part was sent successfully.
    """
    logger.info("Sending Telegram notification...")

    bot_token = Config.get('TELEGRAM_BOT_TOKEN')
    chat_id = Config.get('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        logger.warning("Telegram credentials missing. Skipping notification.")
        return False

    hashtags_str = ' '.join(post.get('hashtags', []))
    has_image = bool(image_path and os.path.exists(image_path))

    photo_sent = False
    if has_image:
        photo_caption = f"📅 {post.get('date', '')} | {post.get('contentType', '')}\n{post.get('topic', '')}"
        photo_sent = _send_photo(image_path, photo_caption, bot_token, chat_id)
    else:
        logger.warning("No generated image found; including the image prompt in the text message instead.")

    message = f"""<b>🌿 Roshini Daily Instagram Post</b>
<b>Date:</b> {post.get('date', '')}
<b>Content Type:</b> {post.get('contentType', '')}
<b>Product:</b> {post.get('product', '')}

<b>Topic:</b> {post.get('topic', '')}

<b>English Caption:</b>
{post.get('captionEn', '')}

<b>Kannada Caption:</b>
{post.get('captionKn', '')}

<b>Hashtags:</b> {hashtags_str}
"""

    if not has_image:
        message += f"\n<b>⚠️ Image generation failed - use this prompt manually:</b>\n{post.get('imagePrompt', 'N/A')}\n"

    message_sent = _send_message(message, bot_token, chat_id)

    return photo_sent or message_sent


def _send_photo(photo_path: str, caption: str, bot_token: str, chat_id: str) -> bool:
    """Send a photo with a short caption via Telegram API."""
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    try:
        with open(photo_path, 'rb') as f:
            files = {'photo': f}
            data = {'chat_id': chat_id, 'caption': caption[:1024]}
            response = requests.post(url, data=data, files=files, timeout=30)
            response.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"Failed to send photo: {e}")
        return False


def _send_message(message: str, bot_token: str, chat_id: str) -> bool:
    """Send a normal HTML-formatted chat message via Telegram API."""
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
