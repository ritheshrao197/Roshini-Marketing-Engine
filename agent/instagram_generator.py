"""
Instagram Generator Agent - Produces exactly one Instagram-ready post per day:
a content type (rotated by weekday), a topic line, English + Kannada captions,
hashtags, and the art-direction image prompt fed to the image generator.
"""

import datetime
import json
from typing import Any, Dict

from utils.logger import get_logger
from llm import call_llm
from llm.brand_assets import resolve_product_assets

logger = get_logger(__name__)

CONTENT_TYPE_BY_WEEKDAY = {
    "Monday": "Ingredient Spotlight",
    "Tuesday": "Founder/Heritage Story",
    "Wednesday": "Behind-the-Scenes",
    "Thursday": "Wellness Tip / Ayurveda Education",
    "Friday": "Product-in-Use",
    "Saturday": "Lifestyle/Aesthetic",
    "Sunday": "Community/Question Prompt",
}

# Fixed art direction template - filled in deterministically (not by the LLM) so
# every day's image prompt stays exactly on-brand regardless of what the model
# writes for the topic/captions. Structured and detailed enough to be used as-is
# for a single feed post, or repurposed as a carousel slide / Reel cover / Story
# without losing brand consistency.
IMAGE_PROMPT_TEMPLATE = """A premium, minimal product/lifestyle photograph for an Ayurvedic wellness brand, depicting: {topic}.

Subject: {topic} - the single hero element, shown as a real product, ingredient, or scene directly relevant to today's topic, not a generic stand-in.
Composition: rule-of-thirds framing with generous negative space in one corner/side reserved for text overlay; shallow depth of field on any product/ingredient shown. Works as a standalone single-image post or as slide 1 of a carousel sequence.
Lighting: natural light, soft directional shadows, warm morning or golden-hour quality.
Style: editorial wellness-brand photography - earthy, heritage, handmade - NOT clinical or glossy-corporate, NOT a flat product-catalog shot.
Color Palette: warm Carnaby Tan and Clay Brown tones as the dominant palette, with soft cream/off-white negative space - no bright or saturated colors outside this palette.
Typography Note (if any text is rendered in-image): clean geometric sans-serif in the spirit of Poppins, in Clay Brown or cream, generously spaced, minimal - one short line only, never a paragraph.
Mood: grounded, trustworthy, warm, artisanal - a family brand, not a mass-market FMCG brand.
Format Notes: deliver at 1080x1350px (4:5, Instagram feed/carousel-safe) with an approx. 150px safe margin on all sides so no key subject or text sits at the edge; the same composition and negative-space placement should still read cleanly if reused as a Reel cover, a 1080x1920 Story (extend the background vertically), or an additional carousel slide.
Negative Prompt: plastic-looking props, neon colors, stock-photo clichés, clutter, generic wellness stereotypes (no random yoga poses unless topic-relevant), any text longer than 4-5 words if text is rendered, watermarks, extra logos or branding beyond one subtle mark."""


def generate_daily_instagram_post(research_data: Dict[str, Any]) -> Dict[str, Any]:
    """Plan and write the single Instagram post for today."""
    today = datetime.date.today()
    day_name = today.strftime("%A")
    content_type = CONTENT_TYPE_BY_WEEKDAY[day_name]

    recommended_products = research_data.get('recommendedProducts') or ['Nutrimix']
    product = recommended_products[0]
    assets = resolve_product_assets(product)

    recent_titles = research_data.get('recentTitles', [])
    today_info = research_data.get('today', {})

    prompt = f"""
    You are the Instagram content lead for Roshini's Home Products, a women-led family
    wellness brand from Karnataka, India (grain-and-herb wellness mix, postnatal tonic,
    honey, and natural skincare items).

    Today is {day_name}. Today's content type is fixed: "{content_type}".
    Featured product for context: {product} (key ingredients: {assets.get('ingredients', [])}).
    Season/context: {today_info.get('season')}, Festival: {today_info.get('festival')}, Awareness day: {today_info.get('awarenessDay')}.
    Recently covered topics (do not repeat): {recent_titles[:15]}

    Write:
    1. "topic": a short, specific topic line for today's post, max 12 words. Concrete,
       not generic (e.g. "Ashwagandha: the root behind our wellness mix's calm energy",
       not "Health benefits of herbs").
    2. "caption_en": a 2-3 line Instagram caption in English. Warm, family-brand tone.
       Educate first, sell naturally. Never make a medical cure claim.
    3. "caption_kn": a 2-3 line Instagram caption in Kannada - natural, warm phrasing a
       Karnataka household would actually use, NOT a literal/robotic translation of the
       English caption.
    4. "hashtags": 3-5 relevant hashtags, mixing broad wellness tags and local/regional
       (Karnataka/Kannada/Bengaluru/Ayurveda-India) tags.

    Return ONLY a valid JSON object matching this schema:
    {{
        "topic": "...",
        "caption_en": "...",
        "caption_kn": "...",
        "hashtags": ["#tag1", "#tag2", "#tag3"]
    }}
    """

    data = None
    try:
        response = call_llm(prompt, json_format=True)
        response_clean = response.strip().replace('```json', '').replace('```', '').strip()
        data = json.loads(response_clean)
    except Exception as e:
        logger.error(f"Instagram content generation failed, using fallback: {e}")

    if not data:
        data = _fallback_content(content_type, product)

    topic = data.get('topic') or f"{product}: {content_type}"
    image_prompt = IMAGE_PROMPT_TEMPLATE.format(topic=topic)

    post = {
        "date": today.isoformat(),
        "dayName": day_name,
        "contentType": content_type,
        "product": product,
        "topic": topic,
        "captionEn": data.get('caption_en', ''),
        "captionKn": data.get('caption_kn', ''),
        "hashtags": data.get('hashtags') or [],
        "imagePrompt": image_prompt,
    }
    logger.info(f"Instagram post planned: [{content_type}] {topic}")
    return post


def _fallback_content(content_type: str, product: str) -> Dict[str, Any]:
    """Deterministic content used only if every LLM attempt fails."""
    return {
        "topic": f"{product}: everyday wellness the traditional way",
        "caption_en": (
            f"A little bit of {product} goes a long way. Made the way our family has always "
            f"made it - natural, simple, and full of care.\nHealthy habits, one spoon at a time."
        ),
        "caption_kn": (
            f"{product} - ನಮ್ಮ ಮನೆಯ ಸಂಪ್ರದಾಯದಂತೆ ತಯಾರಿಸಿದ ಆರೋಗ್ಯಕರ ಆಹಾರ. "
            f"ಪ್ರತಿ ದಿನದ ಆರೋಗ್ಯಕ್ಕೆ ಒಂದು ಸಣ್ಣ ಹೆಜ್ಜೆ."
        ),
        "hashtags": [
            "#RoshinisHomeProducts", "#KarnatakaWellness", "#NaturalNutrition",
            "#FamilyWellness", "#MadeInKarnataka",
        ],
    }
