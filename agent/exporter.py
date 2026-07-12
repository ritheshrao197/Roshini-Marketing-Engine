"""
Exporter Agent - Responsible only for generating the daily export file.
Creates outputs/YYYY-MM-DD.md package.
"""

import os
import json
import datetime
from typing import Dict, Any

from config import Config
from utils.logger import get_logger
from utils.files import ensure_directory

logger = get_logger(__name__)


def export_package(content: Dict[str, Any], seo_data: Dict[str, Any], upload_results: Dict[str, Any]) -> str:
    """
    Export complete marketing package to markdown file.
    
    Args:
        content: Content from content generator.
        seo_data: SEO metadata.
        upload_results: Results from uploader.
    
    Returns:
        Path to exported file.
    """
    logger.info("Exporting package...")
    
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    output_dir = Config.get('OUTPUT_DIR', 'outputs')
    ensure_directory(output_dir)
    
    filename = f"{output_dir}/{date_str}-marketing-package.md"
    
    # Build markdown content
    markdown = _build_markdown(content, seo_data, upload_results, date_str)
    
    # Write to file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    logger.info(f"Package exported to {filename}")
    return filename


def _build_markdown(content: Dict[str, Any], seo_data: Dict[str, Any], upload_results: Dict[str, Any], date_str: str) -> str:
    """Build markdown content."""
    sections = []
    
    # Header
    sections.append(f"# Daily Marketing Package: {date_str}\n")
    
    # Summary
    sections.append("## Summary")
    sections.append(f"- **Product:** {content.get('product', 'N/A')}")
    sections.append(f"- **Theme:** {content.get('theme', 'N/A')}")
    sections.append(f"- **Persona:** {content.get('persona', 'N/A')}")
    sections.append(f"- **Blogs:** {len(content.get('blogs', []))}")
    sections.append(f"- **Recipes:** {len(content.get('recipes', []))}")
    sections.append(f"- **Health Tips:** {len(content.get('health_tips', []))}")
    sections.append(f"- **Drafts Uploaded:** {len(upload_results.get('draft_ids', []))}")
    sections.append("")
    
    # Instagram Content
    if content.get('instagram'):
        sections.append("## Instagram Post")
        instagram = content.get('instagram', {})
        sections.append(f"**Headline:** {instagram.get('headline', 'N/A')}")
        sections.append(f"**Caption:** {instagram.get('caption', 'N/A')}")
        sections.append("**Hashtags:**")
        for category, tags in instagram.get('hashtags', {}).items():
            if tags:
                sections.append(f"- {category.title()}: {' '.join(tags)}")
        sections.append("")
    
    # Blogs
    if content.get('blogs'):
        sections.append("## Blog Posts")
        for i, blog in enumerate(content.get('blogs', [])):
            seo_page = seo_data.get('pages', [{}])[i] if i < len(seo_data.get('pages', [])) else {}
            sections.append(f"### {i+1}. {blog.get('title', 'Untitled')}")
            sections.append(f"**SEO Title:** {seo_page.get('seo_title', 'N/A')}")
            sections.append(f"**Slug:** {seo_page.get('slug', 'N/A')}")
            sections.append(f"**Meta Description:** {seo_page.get('meta_description', 'N/A')}")
            sections.append(f"**Keywords:** {', '.join(seo_page.get('keywords', []))}")
            sections.append(f"**Excerpt:** {seo_page.get('excerpt', blog.get('excerpt', 'N/A'))}")
            sections.append("")
            sections.append(blog.get('content', ''))
            sections.append("")
    
    # Recipes
    if content.get('recipes'):
        sections.append("## Recipes")
        for i, recipe in enumerate(content.get('recipes', [])):
            sections.append(f"### {i+1}. {recipe.get('name', 'Untitled')}")
            sections.append(f"**Prep Time:** {recipe.get('prep_time', 'N/A')}")
            sections.append(f"**Cook Time:** {recipe.get('cook_time', 'N/A')}")
            sections.append("**Ingredients:**")
            for ingredient in recipe.get('ingredients', []):
                sections.append(f"- {ingredient}")
            sections.append("**Instructions:**")
            for j, instruction in enumerate(recipe.get('instructions', [])):
                sections.append(f"{j+1}. {instruction}")
            sections.append("")
    
    # Health Tips
    if content.get('health_tips'):
        sections.append("## Health Tips")
        for i, tip in enumerate(content.get('health_tips', [])):
            sections.append(f"{i+1}. {tip}")
        sections.append("")
    
    # News
    if content.get('news'):
        sections.append("## News")
        for i, news in enumerate(content.get('news', [])):
            sections.append(f"**{news.get('title', '')}**")
            sections.append(f"{news.get('summary', '')}")
            sections.append("")
    
    # Upload Results
    sections.append("## Upload Results")
    sections.append(f"- **Draft IDs:** {', '.join(upload_results.get('draft_ids', []))}")
    sections.append(f"- **Uploaded:** {len(upload_results.get('uploaded', []))}")
    sections.append(f"- **Failed:** {len(upload_results.get('failed', []))}")
    sections.append("")
    
    # Image Prompts
    if content.get('image_prompts'):
        sections.append("## Image Prompts")
        for key, prompt in content.get('image_prompts', {}).items():
            sections.append(f"### {key.title()}")
            sections.append(f"{prompt}")
            sections.append("")
    
    return '\n'.join(sections)