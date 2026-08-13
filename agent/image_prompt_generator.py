"""
Image Prompt Generator Agent - Responsible only for generating image prompts.
Creates detailed prompts for Midjourney/DALL-E conforming to the Roshini brand guidelines.
Does not generate actual images.
"""

from typing import Dict, Any
from utils.logger import get_logger
from llm import call_llm
from llm.brand_assets import resolve_product_assets

logger = get_logger(__name__)


def generate_image_prompt_for_article(article_type: str, title: str, product: str, theme: str) -> str:
    """
    Generate a detailed image prompt for a single article.
    
    Args:
        article_type: Type of article (blog, health_tip, recipe, etc.)
        title: Article title
        product: Selected brand product
        theme: Overall campaign theme
        
    Returns:
        Structured image prompt string.
    """
    logger.info(f"Generating featured image prompt for '{title}'...")
    assets = resolve_product_assets(product)
    
    # Resolve exact product image path
    product_file = assets.get("package")
    if not product_file:
        # Fallback naming logic based on actual files in brand-kit
        product_lower = product.lower()
        if "chia" in product_lower:
            product_file = "brand-kit/products-photos/Roshinis_Chia_Seeds_Transparent_Pouch.png"
        elif "flax" in product_lower:
            product_file = "brand-kit/products-photos/Roshinis_Flax_Seeds_Transparent_Pouch.png"
        elif "pumpkin" in product_lower:
            product_file = "brand-kit/products-photos/Roshinis_Pumpkin_Seeds_Transparent_Pouch.png"
        elif "sunflower" in product_lower:
            product_file = "brand-kit/products-photos/Roshinis_Sunflower_Seeds_Transparent_Pouch.png"
        elif "sathvik" in product_lower:
            product_file = "brand-kit/products-photos/SATHVIK7.png"
        elif "sambar" in product_lower:
            product_file = "brand-kit/products-photos/SAMBARPOWDER.png"
        elif "turmeric" in product_lower or "termeric" in product_lower:
            product_file = "brand-kit/products-photos/TERMERIC.png"
        elif "chili" in product_lower or "chillipoweder" in product_lower:
            product_file = "brand-kit/products-photos/CHILLIPOWEDER.png"
        else:
            product_file = "brand-kit/products-photos/RoshinisNutrimix.jpg"
            
    logo_file = assets.get("logo_color") or "brand-kit/Logo.png"
    
    prompt = f"""
    Create a highly detailed image generation prompt for the featured image of a wellness/nutrition article.
    
    Article details:
    - Type: {article_type}
    - Title: {title}
    - Product: {product}
    - Cohesive Theme: {theme}
    
    Guidelines:
    1. Do NOT generate the image. Generate only the prompt text that would be fed into an AI image generator (like Midjourney or DALL-E).
    2. Never recreate product packaging in the image. Always reference the actual packaging photo file path: '{product_file}' and the logo file path: '{logo_file}'.
    3. The color palette must align with the brand guidelines: Primary Natural Green (#4E7A2E), Accent Millet Gold (#D98C2B), Background Light Warm (#FFF8EE), and Surface White (#FFFFFF).
    4. The prompt must be structured exactly with these sections:
       - Subject: [detailed description of the hero element]
       - Composition: [arrangement, angle, framing, e.g., overhead flat lay or 45-degree angle]
       - Lighting: [warmth, direction, shadows, soft natural morning light]
       - Background: [setting context, rustic wooden tabletop, warm kitchen]
       - Props: [related items, ingredients like millets, raw seeds, almonds]
       - Colour Palette: [brand colors specified above]
       - Typography Space: [negative space reserved for article text overlay]
       - Brand Assets: [referencing brand-kit/products/ and brand-kit/logo/ paths]
       - Logo Placement: [where the logo should be composite-layered]
       - Negative Prompt: [what to avoid, e.g. text overlay, cartoonish elements, generic packaging]
       - Aspect Ratio: [specify aspect ratio, e.g. 16:9]

    Return ONLY the generated prompt, no extra text, explanations, or quotes.
    """
    
    try:
        response = call_llm(prompt)
        return response.strip()
    except Exception as e:
        logger.error(f"Image prompt generation failed: {e}")
        # Return fallback structured prompt
        return f"""Subject: A premium, professional presentation of fresh ingredients for {product}.
Composition: Overhead flat lay shot with a professional 45-degree angle.
Lighting: Soft natural morning light coming from the side, casting warm shadows.
Background: A rustic, textured warm tabletop.
Props: Raw millets, sprouted grains, and clean ceramic bowls.
Colour Palette: Natural Green (#4E7A2E) and Millet Gold (#D98C2B) accents.
Typography Space: Negative space on the left third of the image for text overlay.
Brand Assets: Reference '{product_file}' and '{logo_file}'.
Logo Placement: Bottom right corner, small and elegant.
Negative Prompt: Text, watermark, low quality, cartoon, generic packaging, digital mockups.
Aspect Ratio: 16:9"""


def generate_image_prompts(content: Dict[str, Any], seo_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Compile a compatibility-mode dict of image prompts for the day's package.

    Args:
        content: Content from content generator.
        seo_data: SEO metadata.

    Returns:
        Dict of image prompts.
    """
    logger.info("Compiling image prompts (compatibility mode)...")
    product = content.get('product', 'Nutrimix')
    theme = content.get('theme', 'Health & Wellness')

    prompts = {}

    # Reuse each article's own already-generated featuredImagePrompt instead of
    # paying for a second LLM call per article - this dict is a read-only summary
    # view, not a separate source of truth, so there's nothing to regenerate here.
    blogs = content.get('blogs', [])
    for i, blog in enumerate(blogs):
        title = blog.get('title', 'Wellness Blog')
        existing_prompt = blog.get('featuredImagePrompt')
        prompts[f"blog_{i}"] = existing_prompt or generate_image_prompt_for_article("blog", title, product, theme)

    # Hero/campaign-level prompt has no per-article equivalent, so it's the one
    # prompt actually worth generating fresh here.
    prompts["hero"] = generate_image_prompt_for_article("hero", f"{product} Wellness Campaign", product, theme)


    return prompts