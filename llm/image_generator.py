"""
Image Generator - Produces the actual Instagram-ready image file using Gemini's
native image generation model.

Unlike llm/providers/gemini.py (text-only, reads response.text), this reads the
inline image bytes back out of the response and writes them to disk.
"""

import io
from typing import Optional

from google import genai

from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

IMAGE_MODEL = "gemini-2.5-flash-image"


def generate_image(prompt: str, out_path: str, tries: int = 2) -> Optional[str]:
    """
    Generate a single image from `prompt` and save it to `out_path`.

    Returns the saved file path on success, or None if every attempt failed
    (e.g. missing API key, or no image part in the response).
    """
    api_key = Config.get('GEMINI_API_KEY')
    if not api_key:
        logger.error("GEMINI_API_KEY not configured; cannot generate image.")
        return None

    client = genai.Client(api_key=api_key)

    last_error = None
    for attempt in range(1, tries + 1):
        try:
            response = client.models.generate_content(
                model=IMAGE_MODEL,
                contents=[prompt],
            )
            for candidate in response.candidates or []:
                for part in candidate.content.parts or []:
                    inline_data = getattr(part, "inline_data", None)
                    if inline_data and inline_data.data:
                        from PIL import Image
                        image = Image.open(io.BytesIO(inline_data.data))
                        image.save(out_path)
                        logger.info(f"Image generated and saved to {out_path}")
                        return out_path
            last_error = "No image data found in response"
        except Exception as e:
            last_error = e

        logger.warning(f"Image generation attempt {attempt}/{tries} failed: {last_error}")

    logger.error(f"Image generation failed after {tries} attempts: {last_error}")
    return None
