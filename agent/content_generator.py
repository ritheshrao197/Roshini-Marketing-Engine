"""
Content Generator Agent - Responsible only for generating content.
Creates specialized articles (Blogs, Health Tips, Nutrition News, Recipes, Ingredient Spotlights)
using specialized prompts and returns the unified article JSON format.
"""

import datetime
import json
import re
from concurrent.futures import ThreadPoolExecutor
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
    "faqs": [],
    "author": "Roshini Content Team",
    "status": "Draft",
    "isPublished": False
}

# Bounded concurrency for article generation: high enough to meaningfully cut wall
# clock time (articles are otherwise generated one HTTP round-trip at a time), low
# enough to avoid tripping free-tier per-minute rate limits across providers.
MAX_CONCURRENT_GENERATIONS = 4


def _generate_json_with_retry(
    prompt: str, tries: int = 2, max_tokens: int = 8192, log_label: str = "request"
) -> Optional[Dict[str, Any]]:
    """
    Call the LLM for a JSON response, retrying with a fresh cache key on failure.

    Long-form articles (full body + schema + image prompt) can easily exceed a small
    completion budget and get truncated mid-JSON. A truncated response still counts as
    an HTTP "success" upstream, so the provider failover never triggers - only
    json.loads() here catches it. Retrying with a larger token budget and a fresh
    version tag (to bypass the response cache) recovers most of these before any
    caller has to fall back to local placeholder content.
    """
    last_error = None
    for attempt in range(1, tries + 1):
        try:
            response = call_llm(prompt, json_format=True, max_tokens=max_tokens, version=f"v1-attempt{attempt}")
            response_clean = response.strip().replace('```json', '').replace('```', '').strip()
            return json.loads(response_clean)
        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt}/{tries} to generate {log_label} failed: {e}")

    logger.error(f"Failed to generate {log_label} after {tries} attempts: {last_error}.")
    return None


def _run_concurrently(fn, items: List[Any]) -> List[Any]:
    """Run fn(item) across items on a bounded thread pool, preserving input order."""
    if not items:
        return []
    max_workers = min(MAX_CONCURRENT_GENERATIONS, len(items))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(fn, items))


def generate_content(plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate the 5 specialized articles (Blogs, Health Tips, Recipes, etc.).

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

    # Generate each planned article concurrently - these are independent HTTP calls
    # to the LLM router, so running them one at a time only adds wall-clock time.
    def _build_article(idx_and_art):
        idx, art = idx_and_art
        art_type = art.get('type', 'blog')
        art_title = art.get('title', 'Untitled')
        art_category = art.get('category', 'General')
        art_keywords = art.get('keywords', [])

        logger.info(f"Generating article {idx+1}/{len(articles_plan)}: Type='{art_type}', Title='{art_title}'...")

        return _generate_single_article(
            art_type=art_type,
            title=art_title,
            category=art_category,
            keywords=art_keywords,
            product=product,
            theme=theme,
            persona=persona,
            assets=assets
        )

    generated_articles = _run_concurrently(_build_article, list(enumerate(articles_plan)))

    result = {
        "product": product,
        "theme": theme,
        "persona": persona,
        "blogs": generated_articles,  # All unified articles go here for backward compatibility
        "assets": assets
    }

    logger.info(f"Successfully generated {len(generated_articles)} articles.")
    return result


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
    - Stay faithful to the planned title and campaign theme. Do not add a festival,
      seasonal event, or health outcome that is not explicitly present in them.
    - Give each article one clear practical angle and a fresh structure; do not
      fall back to generic millet-and-immunity copy.
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
        "faqs": [
            {{"question": "The exact FAQ question text as it appears in the FAQs section of content", "answer": "The exact FAQ answer text as it appears in the FAQs section of content"}}
        ],
        "author": "Roshini Content Team",
        "status": "Draft",
        "isPublished": false
    }}

    The "faqs" array must exactly mirror the Q&A pairs written in the FAQs section of
    "content" above (same questions and answers, just structured) - it powers search
    engine rich results, so it must not invent extra questions or omit any that are
    in the body. If this article type has no FAQs section, return an empty array.
    """

    data = _generate_json_with_retry(prompt, log_label=f"{art_type} article '{title}'")
    if data is not None:
        return _apply_unified_schema(data, art_type, title, category, keywords, product, theme)

    # Create a local fallback article that conforms to the schema
    fallback_content = _build_fallback_content(art_type, title, category, product, theme, persona)

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
        "seoTitle": _truncate_at_word(title, 60),
        "seoDescription": _truncate_at_word(f"{title}: what it means for your family's everyday nutrition, from Roshini's Home Products.", 160),
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


def _truncate_at_word(text: str, limit: int) -> str:
    """Truncate text to at most `limit` chars without cutting a word in half."""
    if len(text) <= limit:
        return text
    truncated = text[:limit].rsplit(' ', 1)[0].rstrip(' :,-')
    return truncated or text[:limit]


def _build_fallback_content(art_type: str, title: str, category: str, product: str, theme: str, persona: str) -> str:
    """
    Build a more substantial last-resort article body for when every LLM attempt fails.
    Still short of the full spec, but structured enough (multiple sections, no bare stub)
    to avoid publishing a two-sentence placeholder as the blog header and body.
    """
    return (
        f"<h1>{title}</h1>"
        f"<p>{product} is designed for readers like {_truncate_at_word(persona, 120).rstrip('.') or 'health-conscious families'}, "
        f"and this piece looks at {title.lower()} through the lens of our current campaign theme: {theme}.</p>"
        f"<h2>Why This Matters</h2>"
        f"<p>Seasonal and lifestyle shifts change what your body needs. {product} is built around sprouted grains, "
        f"roasted nuts, and traditional ingredients that support consistent, natural nutrition without processed shortcuts.</p>"
        f"<h2>Key Wellness Benefits</h2>"
        f"<ul>"
        f"<li>High in fiber and plant-based protein</li>"
        f"<li>Rich in essential micro-nutrients from whole, sprouted grains</li>"
        f"<li>100% natural, with no preservatives or refined sugar</li>"
        f"<li>Easy to prepare, fitting a busy modern routine</li>"
        f"</ul>"
        f"<h2>Bringing It Into Your Routine</h2>"
        f"<p>A daily serving of {product}, mixed into milk, smoothies, or porridge, is a simple way to build these "
        f"benefits into an everyday {category.lower()} habit.</p>"
        f"<h2>Frequently Asked Questions</h2>"
        f"<p><strong>Is {product} suitable for daily use?</strong> Yes, it is formulated as an everyday nutrition source "
        f"for the whole family.</p>"
        f"<p><strong>Does it contain preservatives?</strong> No, it is made from natural, sprouted ingredients only.</p>"
    )


def generate_news_content(
    news_plan: List[Dict[str, Any]], product: str, theme: str, persona: str, assets: Dict
) -> List[Dict[str, Any]]:
    """
    Write grounded food/nutrition news articles from real, pre-selected stories
    (see planner.plan_news). Each write-up must stay faithful to the real headline,
    summary, and source provided - the model is explicitly told not to invent
    additional facts, statistics, or quotes beyond what's given.
    """
    logger.info(f"Generating {len(news_plan)} grounded food news articles...")
    return _run_concurrently(
        lambda item: _generate_single_news_article(item, product, theme, persona, assets),
        news_plan
    )


def _generate_single_news_article(
    item: Dict[str, Any], product: str, theme: str, persona: str, assets: Dict
) -> Dict[str, Any]:
    """Write one news article grounded in a single real story from plan_news()."""
    source_title = item["source_title"]
    summary = item.get("summary") or "(No further summary available from the source feed - work from the headline only.)"
    link = item.get("link", "")
    source = item.get("source", "a news source")
    category = item.get("category", "Nutrition News")
    keywords = item.get("keywords") or ["nutrition news"]

    logger.info(f"Generating news article: '{source_title}' (source: {source})...")

    product_file = assets.get("package") or "brand-kit/products-photos/RoshinisNutrimix.jpg"
    logo_file = assets.get("logo_color") or "brand-kit/Logo.png"

    prompt = f"""
    You are a food & nutrition news editor for Roshini's Home Products, writing in the
    style of Healthline, Times of India Health, or Medical News Today's news desk.

    REAL STORY TO COVER (ground truth - do not contradict, and do not invent additional
    facts, statistics, studies, or quotes beyond what is given below):
    - Headline: {source_title}
    - Source: {source}
    - Source summary: {summary}
    - Source link: {link}

    Campaign Context (for tone and optional light product relevance only, NOT the news subject):
    - Brand: Roshini's Home Products, homemade millet & dry fruit nutrition
    - Featured product for context: {product} (Ingredients: {assets.get('ingredients', [])})
    - Target Persona: {persona}
    - Campaign Theme: {theme}

    Write a 500-800 word news article structured as:
    - An engaging, brand-voice headline for OUR article (must not be a verbatim copy of
      the source headline, but must accurately represent the same real story)
    - Opening paragraph: what happened, per the real story above
    - "Why It Matters": relevance to Indian, health-conscious readers
    - "The Bigger Picture": general, well-established nutrition/food-safety context that
      helps readers understand the story (do not fabricate specific new studies or numbers)
    - 3-4 practical takeaways as a bullet list
    - If genuinely relevant, ONE natural, non-forced sentence connecting this to {product}.
      If not relevant, omit any product mention entirely rather than forcing it.
    - End the HTML content with exactly this line (use the real values given above):
      <p><em>Source: <a href="{link}" target="_blank" rel="noopener">{source}</a></em></p>

    Writing Style Guidelines:
    - Objective, journalistic tone. Do NOT sound like generic AI.
    - Do NOT invent statistics, named studies, quotes, or details not present in the
      source summary/headline above. When the summary is thin, stay general rather than
      fabricating specifics.
    - Avoid clickbait phrasing like "Discover...", "Unlock...", "You won't believe...".

    Featured Image Prompt Guidelines:
    Generate a detailed image prompt in the "featuredImagePrompt" field. It must include:
    - Subject (hero focus), Composition, Lighting, Background, Props, Colour Palette (Natural Green #4E7A2E, Millet Gold #D98C2B, Light Warm #FFF8EE), Typography Space, Brand Assets, Logo Placement, Negative Prompt, Aspect Ratio (16:9).
    - NEVER recreate product packaging. Always reference the actual packaging file '{product_file}' and logo file '{logo_file}'.

    Return ONLY a complete JSON object matching this schema. Do NOT return partial JSON:
    {{
        "title": "our headline",
        "slug": "url-friendly-slug",
        "content": "<h1>...</h1><p>...</p>...ending with the Source line above",
        "format": "html",
        "category": "{category}",
        "tags": {json.dumps(keywords)},
        "excerpt": "Compelling 1-2 sentence summary of the article.",
        "seoTitle": "SEO optimized title (60 characters max)",
        "seoDescription": "Meta description (160 characters max)",
        "seoKeywords": {json.dumps(keywords)},
        "canonicalUrl": "https://roshinis.com/blog/url-friendly-slug",
        "featuredImagePrompt": "Subject: ... Composition: ... Brand Assets: '{product_file}', '{logo_file}' ...",
        "references": ["{source} - {link}"],
        "relatedProducts": ["{product}"],
        "author": "Roshini Content Team",
        "status": "Draft",
        "isPublished": false
    }}
    """

    data = _generate_json_with_retry(prompt, log_label=f"news article '{source_title}'")
    if data is not None:
        return _apply_news_schema(data, item, product, theme)

    # Fallback: even without a full write-up, keep the real headline/source/link -
    # more honest than fabricating a full article body for a story we couldn't write.
    logger.error(f"Using minimal grounded fallback for news story '{source_title}'.")
    fallback_prompt = generate_image_prompt_for_article("food_news", source_title, product, theme)
    slug = re.sub(r'[^a-z0-9\s-]', '', source_title.lower())
    slug = re.sub(r'[\s-]+', '-', slug).strip('-')

    fallback_art = UNIFIED_SCHEMA_TEMPLATE.copy()
    fallback_art.update({
        "title": source_title,
        "slug": slug,
        "content": (
            f"<h1>{source_title}</h1>"
            f"<p>{summary}</p>"
            f'<p><em>Source: <a href="{link}" target="_blank" rel="noopener">{source}</a></em></p>'
        ),
        "category": category,
        "tags": keywords,
        "excerpt": _truncate_at_word(source_title, 150),
        "seoTitle": _truncate_at_word(source_title, 60),
        "seoDescription": _truncate_at_word(f"{source_title} - {summary}", 160),
        "seoKeywords": keywords,
        "canonicalUrl": f"https://roshinis.com/blog/{slug}",
        "featuredImagePrompt": fallback_prompt,
        "references": [f"{source} - {link}" if link else source],
        "relatedProducts": [product],
        "author": "Roshini Content Team",
        "status": "Draft",
        "isPublished": False
    })
    return fallback_art


def add_internal_links(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Add a real "Related Reading" block linking each article to 2 others generated
    the same day (blog + news combined). Deterministic, no LLM call needed - internal
    links are a core on-page SEO signal, and were already required by
    templates/blogs.md's linking guidelines but never actually implemented.
    """
    n = len(articles)
    if n < 2:
        return articles

    link_count = min(2, n - 1)
    for i, article in enumerate(articles):
        related = [articles[(i + offset) % n] for offset in range(1, link_count + 1)]
        links_html = "".join(
            f'<li><a href="{r["canonicalUrl"]}">{r["title"]}</a></li>'
            for r in related if r.get("canonicalUrl") and r.get("title")
        )
        if links_html:
            article["content"] = article.get("content", "") + f"<h2>Related Reading</h2><ul>{links_html}</ul>"

    logger.info(f"Added internal links across {n} articles.")
    return articles


def _apply_news_schema(data: Dict[str, Any], item: Dict[str, Any], product: str, theme: str) -> Dict[str, Any]:
    """Sanitize a news article response and guarantee the real source citation survives."""
    validated = _apply_unified_schema(
        data, "food_news", item["source_title"], item.get("category", "Nutrition News"),
        item.get("keywords", []), product, theme
    )

    link = item.get("link", "")
    source = item.get("source", "Google News")
    citation = f"{source} - {link}" if link else source

    # Guarantee the real citation survives even if the model dropped or altered it.
    if not any(link and link in ref for ref in validated["references"]):
        validated["references"] = [citation] + [r for r in validated["references"] if r != citation]

    if link and link not in validated["content"]:
        validated["content"] += (
            f'<p><em>Source: <a href="{link}" target="_blank" rel="noopener">{source}</a></em></p>'
        )

    return validated


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
    sanitized["excerpt"] = data.get("excerpt") or data.get("summary") or _truncate_at_word(sanitized["title"], 150)

    sanitized["seoTitle"] = data.get("seoTitle") or data.get("seo_title") or _truncate_at_word(sanitized["title"], 60)
    sanitized["seoDescription"] = data.get("seoDescription") or data.get("seo_description") or data.get("meta_description") or _truncate_at_word(sanitized["excerpt"], 160)
    
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

    # FAQs: kept as structured data (not just prose) so they can power FAQPage
    # rich results. Only well-formed {question, answer} pairs are kept.
    faqs_raw = data.get("faqs")
    faqs = []
    if isinstance(faqs_raw, list):
        for item in faqs_raw:
            if isinstance(item, dict) and item.get("question") and item.get("answer"):
                faqs.append({
                    "question": str(item["question"]).strip(),
                    "answer": str(item["answer"]).strip()
                })
    sanitized["faqs"] = faqs

    # Constant forced settings
    sanitized["author"] = "Roshini Content Team"
    sanitized["status"] = "Draft"
    sanitized["isPublished"] = False

    # Append deterministic structured data (Article/NewsArticle + optional FAQPage
    # JSON-LD) built from the now-finalized fields above - not LLM-generated, so it
    # can't be truncated or malformed like the rest of the response can.
    sanitized["content"] += _build_structured_data_scripts(sanitized, art_type)

    return sanitized


def _build_structured_data_scripts(article: Dict[str, Any], art_type: str) -> str:
    """
    Build Article/NewsArticle (+ optional FAQPage) JSON-LD for this article, ready to
    append to its HTML content. Built entirely from already-sanitized fields so it is
    always valid JSON, regardless of what the LLM did or didn't return.
    """
    today_str = datetime.date.today().isoformat()
    schema_type = "NewsArticle" if art_type == "food_news" else "BlogPosting"

    article_ld = {
        "@context": "https://schema.org",
        "@type": schema_type,
        "headline": article["title"][:110],
        "description": article.get("excerpt", ""),
        "author": {"@type": "Organization", "name": article.get("author", "Roshini Content Team")},
        "publisher": {"@type": "Organization", "name": "Roshini's Home Products"},
        "mainEntityOfPage": {"@type": "WebPage", "@id": article.get("canonicalUrl", "")},
        "datePublished": today_str,
        "dateModified": today_str,
        "keywords": ", ".join(article.get("seoKeywords", [])[:10])
    }

    scripts = [article_ld]

    faqs = article.get("faqs") or []
    faq_entities = [
        {
            "@type": "Question",
            "name": faq["question"],
            "acceptedAnswer": {"@type": "Answer", "text": faq["answer"]}
        }
        for faq in faqs if faq.get("question") and faq.get("answer")
    ]
    if faq_entities:
        scripts.append({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": faq_entities
        })

    return "".join(
        f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
        for ld in scripts
    )
