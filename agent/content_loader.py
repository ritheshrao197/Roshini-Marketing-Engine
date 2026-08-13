"""
Content Loader Agent - Check and load existing content for today.
Avoids regenerating content if it already exists.
"""

import os
import re
import json
import datetime
from typing import Dict, Any, Optional, Tuple

from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)


def check_existing_content() -> Tuple[bool, Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[str]]:
    """
    Check if content already exists for today.
    
    Returns:
        Tuple of (exists, content, seo_data, package_path)
    """
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    output_dir = Config.get('OUTPUT_DIR', 'outputs')
    
    # Check for marketing package file
    package_path = f"{output_dir}/{date_str}-marketing-package.md"
    
    if not os.path.exists(package_path):
        logger.info(f"No existing content found for {date_str}")
        return False, None, None, None
    
    logger.info(f"Found existing content for {date_str}: {package_path}")
    
    try:
        # Parse the existing package
        content, seo_data = _parse_package(package_path)
        if content and seo_data:
            logger.info(f"Loaded existing content: {len(content.get('blogs', []))} blogs")
            return True, content, seo_data, package_path
        else:
            logger.warning("Failed to parse existing package")
            return False, None, None, None
    except Exception as e:
        logger.error(f"Error loading existing content: {e}")
        return False, None, None, None


def _parse_package(package_path: str) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Parse an existing marketing package file.
    
    Returns:
        Tuple of (content_dict, seo_data_dict)
    """
    with open(package_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract basic info
    product = _extract_field(content, r'\*\*Product:\*\*\s*(.+)') or 'Nutrimix'
    theme = _extract_field(content, r'\*\*Theme:\*\*\s*(.+)') or 'Health & Wellness'
    persona = _extract_field(content, r'\*\*Persona:\*\*\s*(.+)') or 'Health-conscious parent'
    
    # Extract blogs
    blogs = _extract_blogs(content)

    # Extract recipes
    recipes = _extract_recipes(content)
    
    # Extract health tips
    health_tips = _extract_health_tips(content)
    
    # Build content dict
    content_dict = {
        'product': product,
        'theme': theme,
        'persona': persona,
        'blogs': blogs,
        'recipes': recipes,
        'health_tips': health_tips,
        'news': []
    }
    
    # Build SEO data from blogs
    seo_data = {
        'pages': [],
        'global_keywords': [],
        'canonical_urls': []
    }
    
    for blog in blogs:
        seo_page = {
            'seo_title': blog.get('title', '')[:60],
            'slug': blog.get('title', '').lower().replace(' ', '-')[:50],
            'meta_description': blog.get('excerpt', '')[:160],
            'keywords': blog.get('tags', []),
            'excerpt': blog.get('excerpt', ''),
            'canonical_url': ''
        }
        seo_data['pages'].append(seo_page)
    
    return content_dict, seo_data


def _extract_field(content: str, pattern: str) -> Optional[str]:
    """Extract a field using regex pattern."""
    match = re.search(pattern, content)
    return match.group(1).strip() if match else None


def _extract_blogs(content: str) -> list:
    """Extract blog posts from markdown content."""
    blogs = []
    
    # Split by blog headers (### 1. Title, ### 2. Title, etc.)
    blog_sections = re.split(r'###\s+\d+\.\s+', content)
    
    for section in blog_sections[1:]:  # Skip header part
        lines = section.strip().split('\n')
        if not lines:
            continue
        
        title = lines[0].strip()
        
        # Extract fields
        seo_title = _extract_field(section, r'\*\*SEO Title:\*\*\s*(.+)')
        slug = _extract_field(section, r'\*\*Slug:\*\*\s*(.+)')
        meta_desc = _extract_field(section, r'\*\*Meta Description:\*\*\s*(.+)')
        keywords_str = _extract_field(section, r'\*\*Keywords:\*\*\s*(.+)')
        excerpt = _extract_field(section, r'\*\*Excerpt:\*\*\s*(.+)')
        
        keywords = [k.strip() for k in keywords_str.split(',')] if keywords_str else []
        
        # Extract HTML content (everything after the metadata)
        html_content = _extract_html_content(section)
        
        blogs.append({
            'title': title,
            'content': html_content or f"<p>{title}</p>",
            'excerpt': excerpt or title[:155],
            'tags': keywords or ['wellness']
        })
    
    return blogs


def _extract_html_content(section: str) -> str:
    """Extract HTML content from a blog section."""
    # Look for HTML tags
    html_match = re.search(r'(<(?:h[1-6]|p|ul|ol|div)[^>]*>.*?)(?=\n##|\Z)', section, re.DOTALL)
    if html_match:
        return html_match.group(1).strip()
    
    # Fallback: look for any content after metadata
    lines = section.split('\n')
    content_lines = []
    in_content = False
    
    for line in lines:
        if line.startswith('<') or in_content:
            in_content = True
            content_lines.append(line)
    
    return '\n'.join(content_lines).strip()


def _extract_recipes(content: str) -> list:
    """Extract recipes from markdown content."""
    recipes = []
    
    if '## Recipes' not in content:
        return recipes
    
    recipes_section = content.split('## Recipes')[1].split('##')[0]
    recipe_parts = re.split(r'###\s+\d+\.\s+', recipes_section)
    
    for part in recipe_parts[1:]:
        name = part.strip().split('\n')[0]
        prep_time = _extract_field(part, r'\*\*Prep Time:\*\*\s*(.+)')
        cook_time = _extract_field(part, r'\*\*Cook Time:\*\*\s*(.+)')
        
        recipes.append({
            'name': name,
            'prep_time': prep_time or 'N/A',
            'cook_time': cook_time or 'N/A',
            'ingredients': [],
            'instructions': []
        })
    
    return recipes


def _extract_health_tips(content: str) -> list:
    """Extract health tips from markdown content."""
    tips = []
    
    if '## Health Tips' not in content:
        return tips
    
    tips_section = content.split('## Health Tips')[1].split('##')[0]
    
    for line in tips_section.split('\n'):
        line = line.strip()
        if line and line[0].isdigit() and '.' in line[:4]:
            tip = line.split('.', 1)[1].strip()
            if tip:
                tips.append(tip)
    
    return tips
