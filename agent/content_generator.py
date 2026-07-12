"""
Content Generator Agent - Responsible only for generating content.
Creates specialized articles (Blogs, Health Tips, Nutrition News, Recipes, Ingredient Spotlights)
using specialized prompts and returns the unified article JSON format.
"""

import json
import re
from typing import Dict, Any, List, Optional
from utils.logger import get_logger
from llm import call_llm
from llm.brand_assets import resolve_product_assets
from agent.image_prompt_generator import generate_image_prompt_for_article

logger = get_logger(__name__)

UNIFIED_SCHEMA_TEMPLATE = {
    "title": "",
    "slug": "",
    "content": "",
    "format": "html",
    "category": "",
    "tags": [],
    "excerpt": "",
    "seoTitle": "",
    "seoDescription": "",
    "seoKeywords": [],
    "canonicalUrl": "",
    "featuredImagePrompt": "",
    "references": [],
    "relatedProducts": [],
    "author": "Roshini Content Team",
    "status": "Draft",
    "isPublished": False
}


def generate_content(plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate Instagram post and 5 specialized articles (Blogs, Health Tips, Recipes, etc.).
    
    Args:
        plan_data: Plan from planner agent.
    
    Returns:
        Generated content for all channels, with articles in the 'blogs' list for backward compatibility.
    """
    logger.info("Generating content campaign articles...")
    
    product = plan_data.get('product', 'Nutrimix')
    theme = plan_data.get('theme', 'Health & Wellness')
    persona = plan_data.get('persona', 'Health-conscious parent')
    articles_plan = plan_data.get('articles', [])
    
    # Resolve product assets
    assets = resolve_product_assets(product)
    
    # Generate Instagram post
    insta_plan = plan_data.get('instagram', {})
    instagram_post = _generate_instagram_post(
        product, theme, persona, 
        headline=insta_plan.get('headline', ''), 
        topic=insta_plan.get('topic', ''), 
        assets=assets
    )
    
    # Generate each article planned
    generated_articles = []
    for idx, art in enumerate(articles_plan):
        art_type = art.get('type', 'blog')
        art_title = art.get('title', 'Untitled')
        art_category = art.get('category', 'General')
        art_keywords = art.get('keywords', [])
        
        logger.info(f"Generating article {idx+1}/{len(articles_plan)}: Type='{art_type}', Title='{art_title}'...")
        
        article_data = _generate_single_article(
            art_type=art_type,
            title=art_title,
            category=art_category,
            keywords=art_keywords,
            product=product,
            theme=theme,
            persona=persona,
            assets=assets
        )
        
        generated_articles.append(article_data)
        
    result = {
        "product": product,
        "theme": theme,
        "persona": persona,
        "instagram": instagram_post,
        "blogs": generated_articles,  # All unified articles go here for backward compatibility
        "assets": assets
    }
    
    logger.info(f"Successfully generated Instagram post and {len(generated_articles)} articles.")
    return result


def _generate_instagram_post(product: str, theme: str, persona: str, headline: str, topic: str, assets: Dict) -> Dict[str, Any]:
    """Generate Instagram post content."""
    prompt = f"""
    Create an Instagram post for Roshini's Home Products.
    
    Product: {product}
    Theme: {theme}
    Target Persona: {persona}
    Planned Headline: {headline}
    Planned Topic: {topic}
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
        response_clean = response.strip().replace('```json', '').replace('```', '').strip()
        return json.loads(response_clean)
    except Exception as e:
        logger.error(f"Instagram post generation failed: {e}")
        return {
            "caption": f"Experience the natural goodness of {product}! Sprouted grains packed with nutrition. 🌿 #Roshinis",
            "headline": headline or f"Wholesome Nutrition with {product}",
            "supporting_text": topic or f"Family health and millet benefits.",
            "hashtags": {"brand": [product.lower(), "roshinis"], "niche": ["wellness", "health"], "discovery": ["millets"]}
        }


def _generate_single_article(
    art_type: str, title: str, category: str, keywords: List[str], 
    product: str, theme: str, persona: str, assets: Dict
) -> Dict[str, Any]:
    """Compile specialized prompts and generate a single article using the unified schema."""
    
    # Resolve product packaging image path for reference
    product_file = assets.get("package") or "brand-kit/products-photos/RoshinisNutrimix.jpg"
    logo_file = assets.get("logo_color") or "brand-kit/Logo.png"
    
    # Build prompt instructions based on article type
    if art_type == "blog":
        specific_instructions = f"""
        Article Type: Blog Post
        Word Count: 1200–1800 words
        Required Content Structure:
        - Introduction (professional, hook without AI clichés)
        - H2 Sections and H3 Sections dividing the topics logically
        - Bullet Lists and at least one HTML table comparing data or values
        - FAQs (3-4 relevant questions and answers)
        - Scientific References (2-3 medical/nutrition references)
        - Conclusion
        - Mention a Related Product: '{product}' naturally in the text
        """
    elif art_type == "health_tip":
        specific_instructions = f"""
        Article Type: Health Tip
        Word Count: 600–900 words
        Required Content Structure:
        - Problem: Explain a common health/lifestyle challenge
        - Explanation: The science behind why this challenge occurs
        - Benefits: How addressing it helps wellness
        - Practical Tips: Actionable, simple, step-by-step tips
        - Common Mistakes to avoid
        - FAQs (2-3 short wellness FAQs)
        - Naturally reference '{product}'
        """
    elif art_type == "nutrition_news":
        specific_instructions = f"""
        Article Type: Nutrition News
        Word Count: 700–1200 words
        Required Content Structure:
        - Headline: Catchy and news-journalism styled
        - Summary: Brief summary of the scientific or industrial update
        - What Happened: Background events / studies
        - Why It Matters: Nutri-health implications
        - Scientific Context: Research details and citations
        - Indian Relevance: How it applies specifically to the Indian diet/lifestyle
        - Takeaways: Quick bullet list of takeaways
        - References: Cite sources or publications
        """
    elif art_type == "recipe":
        specific_instructions = f"""
        Article Type: Nutritious Recipe
        Word Count: 800–1000 words
        Required Content Structure:
        - Introduction: Description of the recipe using '{product}'
        - Prep Time, Cook Time, Servings
        - Nutrition Table: HTML table with calories, protein, carbs, fats, fiber
        - Ingredients: List of ingredients
        - Instructions: Step-by-step cooking steps
        - Chef Tips: Expert hints for taste/texture
        - Storage instructions
        - Variations (e.g. vegan, gluten-free)
        - FAQs (2-3 recipe FAQs)
        """
    elif art_type == "ingredient_spotlight":
        specific_instructions = f"""
        Article Type: Ingredient Spotlight
        Word Count: 1000–1400 words
        Required Content Structure:
        - History: Traditional origins of the key ingredient of '{product}'
        - Nutrition Profile: Rich overview of nutrients, vitamins, minerals
        - Benefits: Direct health benefits of this ingredient
        - Usage: How to incorporate it into everyday diets
        - Recipes: Quick recipes or usage ideas
        - FAQs: Core questions
        - Scientific References: Studies backing the health claims
        """
    else:
        # Fallback to general blog
        art_type = "blog"
        specific_instructions = f"Write a standard blog article of 1000 words about {title}."

    prompt = f"""
    You are an expert medical writer and professional journalist writing for Roshini's Home Products.
    Write a high-quality, professional article about: '{title}'
    
    Cohesive Campaign Context:
    - Main Product Featured: {product} (Ingredients: {assets.get('ingredients', [])})
    - Target Persona: {persona}
    - Campaign Theme: {theme}
    
    {specific_instructions}
    
    Writing Style Guidelines:
    - Write in the tone of Healthline, Medical News Today, Verywell Health, or Times of India Health.
    - Professional, objective, journalism style. Do NOT sound like generic AI.
    - Avoid using words like "Discover...", "Unlock...", "Journey...", "Alternative Angle...", "Step into...", "In this article, we will...", or generic introductory clichés.
    
    Featured Image Prompt Guidelines:
    Generate a detailed image prompt in the "featuredImagePrompt" field. It must include:
    - Subject (hero focus), Composition, Lighting, Background, Props, Colour Palette (Natural Green #4E7A2E, Millet Gold #D98C2B, Light Warm #FFF8EE), Typography Space, Brand Assets, Logo Placement, Negative Prompt, Aspect Ratio (16:9).
    - NEVER recreate product packaging. Always reference the actual packaging file '{product_file}' and logo file '{logo_file}'.
    
    Return ONLY a complete JSON object matching this schema. Do NOT return partial JSON:
    {{
        "title": "{title}",
        "slug": "url-friendly-slug",
        "content": "<h1>HTML formatted body...</h1><p>...</p>",
        "format": "html",
        "category": "{category}",
        "tags": {json.dumps(keywords)},
        "excerpt": "Compelling 1-2 sentence summary of the article.",
        "seoTitle": "SEO optimized title (60 characters max)",
        "seoDescription": "Meta description (160 characters max)",
        "seoKeywords": {json.dumps(keywords)},
        "canonicalUrl": "https://roshinis.com/blog/url-friendly-slug",
        "featuredImagePrompt": "Subject: ... Composition: ... Brand Assets: '{product_file}', '{logo_file}' ...",
        "references": ["Scientific reference 1", "Scientific reference 2"],
        "relatedProducts": ["{product}"],
        "author": "Roshini Content Team",
        "status": "Draft",
        "isPublished": false
    }}
    """
    
    try:
        response = call_llm(prompt, json_format=True)
        response_clean = response.strip().replace('```json', '').replace('```', '').strip()
        data = json.loads(response_clean)
        
        # Ensure it conforms to unified schema
        validated_data = _apply_unified_schema(data, art_type, title, category, keywords, product, theme)
        return validated_data
        
    except Exception as e:
        logger.error(f"Failed to generate {art_type} article '{title}': {e}. Using local fallback content.")
        
        # Create a local fallback article that conforms to the schema
        fallback_content = f"<h1>{title}</h1><p>Learn how {product} fits into a healthy lifestyle under the theme of {theme}. Our sprouted grains and traditional recipes provide key nutrients for a balanced diet.</p><h2>Key Wellness Benefits</h2><ul><li>High fiber and protein</li><li>Rich in essential micro-nutrients</li><li>100% natural, no preservatives</li></ul>"
        
        fallback_prompt = generate_image_prompt_for_article(art_type, title, product, theme)
        
        fallback_art = UNIFIED_SCHEMA_TEMPLATE.copy()
        slug = re.sub(r'[^a-z0-9\s-]', '', title.lower())
        slug = re.sub(r'[\s-]+', '-', slug).strip('-')
        
        fallback_art.update({
            "title": title,
            "slug": slug,
            "content": fallback_content,
            "category": category,
            "tags": keywords,
            "excerpt": f"An informative look at {title} in the context of {theme}.",
            "seoTitle": title[:60],
            "seoDescription": f"Learn more about {title} and how it relates to wellness.",
            "seoKeywords": keywords,
            "canonicalUrl": f"https://roshinis.com/blog/{slug}",
            "featuredImagePrompt": fallback_prompt,
            "references": ["Roshini Nutrition Guidelines 2026"],
            "relatedProducts": [product],
            "author": "Roshini Content Team",
            "status": "Draft",
            "isPublished": False
        })
        return fallback_art


def _apply_unified_schema(
    data: Dict[str, Any], art_type: str, planned_title: str, 
    planned_category: str, planned_keywords: List[str], product: str, theme: str
) -> Dict[str, Any]:
    """Sanitize and validate that all keys in the unified schema are present and correct."""
    sanitized = UNIFIED_SCHEMA_TEMPLATE.copy()
    
    # Map key values
    sanitized["title"] = data.get("title") or data.get("headline") or planned_title
    
    # Slug resolution
    slug = data.get("slug")
    if not slug:
        slug = re.sub(r'[^a-z0-9\s-]', '', sanitized["title"].lower())
        slug = re.sub(r'[\s-]+', '-', slug).strip('-')
    sanitized["slug"] = slug
    
    # HTML content validation
    content = data.get("content") or ""
    if not content.strip().startswith("<"):
        # Wrap content in basic HTML tags if the model returned markdown
        content = f"<h1>{sanitized['title']}</h1><p>{content.replace(chr(10), '</p><p>')}</p>"
        content = content.replace("<p></p>", "")
    sanitized["content"] = content
    sanitized["format"] = "html"
    
    sanitized["category"] = data.get("category") or planned_category
    sanitized["tags"] = data.get("tags") or planned_keywords or ["wellness"]
    sanitized["excerpt"] = data.get("excerpt") or data.get("summary") or sanitized["title"][:150]
    
    sanitized["seoTitle"] = data.get("seoTitle") or data.get("seo_title") or sanitized["title"][:60]
    sanitized["seoDescription"] = data.get("seoDescription") or data.get("seo_description") or data.get("meta_description") or sanitized["excerpt"][:160]
    
    seo_kws = data.get("seoKeywords") or data.get("seo_keywords") or data.get("keywords") or sanitized["tags"]
    sanitized["seoKeywords"] = seo_kws if isinstance(seo_kws, list) else [str(seo_kws)]
    
    sanitized["canonicalUrl"] = data.get("canonicalUrl") or data.get("canonical_url") or f"https://roshinis.com/blog/{sanitized['slug']}"
    
    # Featured image prompt check or build
    img_prompt = data.get("featuredImagePrompt") or data.get("image_prompt") or data.get("imagePrompt")
    if not img_prompt or len(img_prompt) < 30:
        img_prompt = generate_image_prompt_for_article(art_type, sanitized["title"], product, theme)
    sanitized["featuredImagePrompt"] = img_prompt
    
    refs = data.get("references")
    sanitized["references"] = refs if isinstance(refs, list) else ([refs] if refs else [])
    
    prods = data.get("relatedProducts") or data.get("related_products")
    sanitized["relatedProducts"] = prods if isinstance(prods, list) else [product]
    
    # Constant forced settings
    sanitized["author"] = "Roshini Content Team"
    sanitized["status"] = "Draft"
    sanitized["isPublished"] = False
    
    return sanitized