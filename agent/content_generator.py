"""
Content Generator Agent - Responsible only for generating content.
Creates Instagram posts, blogs, health tips, recipes, and news.
"""

import json
import re
from typing import Dict, Any, List, Optional
from utils.logger import get_logger
from llm import call_llm
from llm.brand_assets import resolve_product_assets

logger = get_logger(__name__)


def generate_content(plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate Instagram posts, blogs, health tips, recipes, and news.
    
    Args:
        plan_data: Plan from planner agent.
    
    Returns:
        Generated content for all channels.
    """
    logger.info("Generating content...")
    
    product = plan_data.get('product', 'Nutrimix')
    theme = plan_data.get('theme', 'Health & Wellness')
    persona = plan_data.get('persona', 'Health-conscious parent')
    topics = plan_data.get('website_topics', [])
    
    # Resolve product assets
    assets = resolve_product_assets(product)
    
    # Generate Instagram post
    instagram_post = _generate_instagram_post(product, theme, persona, assets)
    
    # Generate blogs
    blogs = _generate_blogs(topics, product, assets)
    
    # Generate health tips
    health_tips = _generate_health_tips(theme, product)
    
    # Generate recipes
    recipes = _generate_recipes(product, assets)
    
    # Generate news
    news = _generate_news(theme)
    
    result = {
        "product": product,
        "theme": theme,
        "persona": persona,
        "instagram": instagram_post,
        "blogs": blogs,
        "health_tips": health_tips,
        "recipes": recipes,
        "news": news,
        "assets": assets
    }
    
    logger.info(f"Content generated: {len(blogs)} blogs, {len(recipes)} recipes")
    return result


def _generate_instagram_post(product: str, theme: str, persona: str, assets: Dict) -> Dict[str, Any]:
    """Generate Instagram post content."""
    prompt = f"""
    Create an Instagram post for Roshini's Home Products.
    
    Product: {product}
    Theme: {theme}
    Target Persona: {persona}
    Ingredients: {assets.get('ingredients', [])}
    
    Include:
    1. Caption (with hooks, value, CTA)
    2. Headline
    3. Supporting text
    4. Hashtags (brand, niche, discovery)
    
    Format as JSON:
    {{
        "caption": "...",
        "headline": "...",
        "supporting_text": "...",
        "hashtags": {{"brand": [], "niche": [], "discovery": []}}
    }}
    """
    
    try:
        response = call_llm(prompt, json_format=True)
        return json.loads(response.strip().replace('```json', '').replace('```', '').strip())
    except Exception as e:
        logger.error(f"Instagram post generation failed: {e}")
        return {
            "caption": f"Discover the benefits of {product}! 🌿",
            "headline": f"Your Daily Dose of {theme}",
            "supporting_text": f"Experience wellness with {product}",
            "hashtags": {"brand": [product.lower(), "roshinis"], "niche": ["wellness", "health"], "discovery": []}
        }


def _generate_blogs(topics: List[str], product: str, assets: Dict) -> List[Dict[str, Any]]:
    """Generate blog posts in HTML format."""
    blogs = []
    
    for topic in topics:
        prompt = f"""
        Write a blog post about: {topic}
        
        Product context: {product}
        Ingredients: {assets.get('ingredients', [])}
        
        IMPORTANT: Generate the content in HTML format. Use proper HTML tags:
        - <h1> for main title
        - <h2> for section headings
        - <h3> for subheadings
        - <p> for paragraphs
        - <ul> and <li> for bullet lists
        - <ol> and <li> for numbered lists
        - <strong> for bold text
        - <em> for italic text
        - <a href="..."> for links
        
        Include:
        1. Title (plain text, not HTML)
        2. SEO-optimized content in HTML format (500-800 words)
        3. Excerpt (plain text, 1-2 sentences)
        4. Tags (array of strings)
        
        Return as JSON:
        {{
            "title": "Plain text title",
            "content": "<h1>HTML content here...</h1><p>Paragraph text...</p>",
            "excerpt": "Plain text excerpt",
            "tags": ["tag1", "tag2"]
        }}
        
        Example content format:
        "<h1>5 Quick Millet Breakfasts</h1><p>These breakfast ideas are easy to make and naturally wholesome.</p><ul><li>Millet porridge</li><li>Vegetable millet upma</li></ul>"
        """
        
        try:
            response = call_llm(prompt, json_format=True)
            blog = json.loads(response.strip().replace('```json', '').replace('```', '').strip())
            # Ensure content is HTML (strip markdown code blocks if any)
            content = blog.get('content', '')
            # If content doesn't start with HTML tag, it might be markdown - wrap it
            if content and not content.strip().startswith('<'):
                content = f"<p>{content}</p>"
            blog['content'] = content
            blogs.append(blog)
        except Exception as e:
            logger.error(f"Blog generation failed for {topic}: {e}")
            # Add fallback blog with HTML content
            blogs.append({
                "title": f"Understanding {topic}",
                "content": f"<h1>Understanding {topic}</h1><p>Learn about {topic} and how it relates to {product}.</p><h2>Key Benefits</h2><ul><li>Nutritious and wholesome</li><li>Easy to incorporate into daily meals</li><li>Trusted by families</li></ul>",
                "excerpt": f"An introduction to {topic} in the context of wellness.",
                "tags": [topic.lower(), product.lower(), "wellness"]
            })
    
    return blogs


def _generate_health_tips(theme: str, product: str) -> List[str]:
    """Generate health tips."""
    prompt = f"""
    Generate 5 health tips related to {theme} and {product}.
    
    Make them actionable, science-based, and family-friendly.
    Return as a JSON array of strings.
    """
    
    try:
        response = call_llm(prompt, json_format=True)
        tips = json.loads(response.strip().replace('```json', '').replace('```', '').strip())
        if isinstance(tips, list):
            return tips
    except Exception as e:
        logger.error(f"Health tips generation failed: {e}")
    
    # Fallback tips
    return [
        f"Start your day with {product} for sustained energy",
        "Include millets in your family's weekly meal plan",
        "Pair your meals with fresh seasonal vegetables",
        "Stay hydrated throughout the day",
        "Practice mindful eating for better digestion"
    ]


def _generate_recipes(product: str, assets: Dict) -> List[Dict[str, Any]]:
    """Generate recipes."""
    ingredients = assets.get('ingredients', [])
    
    prompt = f"""
    Create 2 recipes using {product}.
    Ingredients available: {ingredients}
    
    Each recipe should include:
    1. Name
    2. Prep time
    3. Cook time
    4. Ingredients list
    5. Instructions
    
    Return as JSON array.
    """
    
    try:
        response = call_llm(prompt, json_format=True)
        recipes = json.loads(response.strip().replace('```json', '').replace('```', '').strip())
        if isinstance(recipes, list):
            return recipes
    except Exception as e:
        logger.error(f"Recipe generation failed: {e}")
    
    # Fallback recipe
    return [{
        "name": f"{product} Breakfast Bowl",
        "prep_time": "5 minutes",
        "cook_time": "10 minutes",
        "ingredients": ["2 tbsp Nutrimix", "1 cup milk", "Fresh fruits", "Nuts"],
        "instructions": [
            "Mix Nutrimix with milk",
            "Top with fresh fruits and nuts",
            "Serve immediately"
        ]
    }]


def _generate_news(theme: str) -> List[Dict[str, Any]]:
    """Generate news snippets."""
    prompt = f"""
    Create 3 news snippets related to {theme}.
    Make them educational and relevant to the wellness space.
    
    Return as JSON array with 'title' and 'summary' fields.
    """
    
    try:
        response = call_llm(prompt, json_format=True)
        news = json.loads(response.strip().replace('```json', '').replace('```', '').strip())
        if isinstance(news, list):
            return news
    except Exception as e:
        logger.error(f"News generation failed: {e}")
    
    return [
        {"title": f"Global Trend: {theme} Gains Popularity", "summary": "More families embracing healthy lifestyle choices."},
        {"title": "New Study on Nutritional Benefits", "summary": "Research shows positive impact of millet-based diets."},
        {"title": "Wellness Revolution in India", "summary": "Traditional grains making a comeback in modern kitchens."}
    ]