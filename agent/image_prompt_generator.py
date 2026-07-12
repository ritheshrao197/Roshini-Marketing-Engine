"""
Image Prompt Generator Agent - Responsible only for generating image prompts.
Creates prompts for Instagram, blog, recipe, and hero images.
No actual image generation.
"""

from typing import Dict, Any, List
from utils.logger import get_logger
from llm import call_llm

logger = get_logger(__name__)


def generate_image_prompts(content: Dict[str, Any], seo_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate image prompts for various use cases.
    
    Args:
        content: Content from content generator.
        seo_data: SEO metadata.
    
    Returns:
        Dictionary of image prompts for different uses.
    """
    logger.info("Generating image prompts...")
    
    product = content.get('product', 'Nutrimix')
    assets = content.get('assets', {})
    theme = content.get('theme', 'Health & Wellness')
    
    prompts = {
        "instagram": _generate_instagram_prompt(product, theme, assets),
        "blog": _generate_blog_prompt(content, assets),
        "recipe": _generate_recipe_prompt(content, assets),
        "hero": _generate_hero_prompt(product, theme, assets)
    }
    
    logger.info(f"Generated {len(prompts)} image prompts")
    return prompts


def _generate_instagram_prompt(product: str, theme: str, assets: Dict) -> str:
    """Generate prompt for Instagram post image."""
    ingredients = assets.get('ingredients', ['grains', 'millets'])
    
    prompt = f"""
    Create a detailed image prompt for an Instagram post for {product}.
    
    Theme: {theme}
    Ingredients: {', '.join(ingredients)}
    Style: Photorealistic commercial food photography
    
    Include details about:
    - Subject (product packaging, ingredients)
    - Camera settings (lens, aperture)
    - Lighting (natural, warm)
    - Background (kitchen, tabletop)
    - Composition (placement, angle)
    - Quality (8K, ultra-realistic)
    
    Return ONLY the prompt text, no additional explanation.
    """
    
    try:
        response = call_llm(prompt)
        return response.strip()
    except Exception as e:
        logger.error(f"Instagram prompt generation failed: {e}")
        return f"Premium {product} on a wooden table, natural morning light, shallow depth of field, professional food photography, 8K"


def _generate_blog_prompt(content: Dict[str, Any], assets: Dict) -> str:
    """Generate prompt for blog featured image."""
    product = content.get('product', 'Nutrimix')
    ingredients = assets.get('ingredients', ['grains', 'millets'])
    first_blog = content.get('blogs', [{}])[0]
    topic = first_blog.get('title', 'health and wellness')
    
    prompt = f"""
    Create a detailed image prompt for a blog featured image.
    
    Topic: {topic}
    Product: {product}
    Ingredients: {', '.join(ingredients)}
    Style: Editorial, professional, warm
    
    Include:
    - Subject description
    - Composition and framing
    - Lighting style
    - Color palette
    - Quality specifications
    
    Return ONLY the prompt text.
    """
    
    try:
        response = call_llm(prompt)
        return response.strip()
    except Exception as e:
        logger.error(f"Blog prompt generation failed: {e}")
        return f"Nutritious ingredients arranged on a rustic table, warm lighting, editoral photography style, professional"


def _generate_recipe_prompt(content: Dict[str, Any], assets: Dict) -> str:
    """Generate prompt for recipe image."""
    product = content.get('product', 'Nutrimix')
    recipes = content.get('recipes', [])
    recipe_name = recipes[0].get('name', 'Healthy Meal') if recipes else 'Healthy Meal'
    
    prompt = f"""
    Create a detailed image prompt for a recipe image.
    
    Recipe: {recipe_name}
    Product: {product}
    Ingredients: {', '.join(assets.get('ingredients', []))}
    Style: Food photography, appetizing, overhead or 45-degree angle
    
    Include:
    - Plating description
    - Background setting
    - Props and styling
    - Lighting and mood
    
    Return ONLY the prompt text.
    """
    
    try:
        response = call_llm(prompt)
        return response.strip()
    except Exception as e:
        logger.error(f"Recipe prompt generation failed: {e}")
        return f"Beautiful presentation of {recipe_name}, overhead shot, natural daylight, food styling, professional"


def _generate_hero_prompt(product: str, theme: str, assets: Dict) -> str:
    """Generate prompt for hero/main image."""
    ingredients = assets.get('ingredients', ['natural', 'healthy'])
    
    prompt = f"""
    Create a detailed image prompt for a hero/main image.
    
    Product: {product}
    Theme: {theme}
    Ingredients: {', '.join(ingredients)}
    Style: Hero photography, impactful, brand-focused
    
    Include:
    - Product hero placement
    - Supporting elements
    - Brand style consideration
    - Premium look and feel
    
    Return ONLY the prompt text.
    """
    
    try:
        response = call_llm(prompt)
        return response.strip()
    except Exception as e:
        logger.error(f"Hero prompt generation failed: {e}")
        return f"Premium {product} packaging front and center, {theme} lifestyle scene, professional product photography, brand-focused"