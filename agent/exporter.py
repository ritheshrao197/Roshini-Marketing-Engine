"""
Exporter Agent - Responsible only for generating the daily export files.
Creates outputs/YYYY-MM-DD.md, outputs/YYYY-MM-DD.json, and outputs/YYYY-MM-DD-api.json.
"""

import os
import json
import datetime
from typing import Dict, Any
from config import Config
from utils.files import ensure_directory
from utils.logger import get_logger

logger = get_logger(__name__)


def export_package(content: Dict[str, Any], seo_data: Dict[str, Any], upload_results: Dict[str, Any]) -> str:
    """
    Export marketing data package into Markdown, content JSON, and API JSON formats.
    
    Args:
        content: Content from content generator.
        seo_data: SEO metadata compatibility object.
        upload_results: Upload results from uploader.
        
    Returns:
        The file path of the markdown package (for backward compatibility).
    """
    logger.info("Exporting campaign package files...")
    
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    output_dir = Config.get('OUTPUT_DIR', 'outputs')
    ensure_directory(output_dir)
    
    md_filename = f"{output_dir}/{date_str}.md"
    json_filename = f"{output_dir}/{date_str}.json"
    api_filename = f"{output_dir}/{date_str}-api.json"
    
    # 1. Generate YYYY-MM-DD.md
    markdown_content = _build_markdown(content, upload_results, date_str)
    with open(md_filename, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    logger.info(f"   💾 Saved Markdown to {md_filename}")
    
    # 2. Generate YYYY-MM-DD.json (Internal content dict)
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(content, f, indent=4)
    logger.info(f"   💾 Saved Content JSON to {json_filename}")
        
    # 3. Generate YYYY-MM-DD-api.json (API Payloads)
    api_payloads = []
    articles = content.get('blogs', [])
    for blog in articles:
        # Match with upload result
        draft_id = "failed"
        for item in upload_results.get('uploaded', []):
            if item.get('title') == blog.get('title'):
                draft_id = item.get('draft_id')
                break
                
        payload_entry = {
            "payload": blog,
            "upload_status": "Success" if draft_id != "failed" else "Failed",
            "draft_id": draft_id
        }
        api_payloads.append(payload_entry)
        
    with open(api_filename, 'w', encoding='utf-8') as f:
        json.dump(api_payloads, f, indent=4)
    logger.info(f"   💾 Saved API Payload JSON to {api_filename}")
        
    return md_filename


def _build_markdown(content: Dict[str, Any], upload_results: Dict[str, Any], date_str: str) -> str:
    """Build markdown package presentation."""
    sections = []
    
    # Header
    sections.append(f"# Daily Marketing Package: {date_str}\n")
    
    # Summary
    sections.append("## Campaign Summary")
    sections.append(f"- **Product:** {content.get('product', 'N/A')}")
    sections.append(f"- **Theme:** {content.get('theme', 'N/A')}")
    sections.append(f"- **Persona:** {content.get('persona', 'N/A')}")
    sections.append(f"- **Total Articles:** {len(content.get('blogs', []))}")
    sections.append(f"- **Uploaded Count:** {len(upload_results.get('uploaded', []))}")
    sections.append(f"- **Failed Count:** {len(upload_results.get('failed', []))}")
    sections.append("")
    
    # Articles
    if content.get('blogs'):
        sections.append("## Generated Articles")
        for i, blog in enumerate(content.get('blogs', [])):
            # Find upload result
            draft_id = "N/A"
            for item in upload_results.get('uploaded', []):
                if item.get('title') == blog.get('title'):
                    draft_id = item.get('draft_id')
                    break
                    
            sections.append(f"### {i+1}. {blog.get('title', 'Untitled')}")
            sections.append(f"- **Category:** {blog.get('category', 'General')}")
            sections.append(f"- **Slug:** {blog.get('slug', 'N/A')}")
            sections.append(f"- **SEO Title:** {blog.get('seoTitle', 'N/A')}")
            sections.append(f"- **SEO Description:** {blog.get('seoDescription', 'N/A')}")
            sections.append(f"- **Keywords:** {', '.join(blog.get('seoKeywords', []))}")
            sections.append(f"- **Canonical URL:** {blog.get('canonicalUrl', 'N/A')}")
            sections.append(f"- **Draft ID:** {draft_id}")
            sections.append("")
            sections.append("#### Featured Image Prompt")
            sections.append(f"```\n{blog.get('featuredImagePrompt', 'N/A')}\n```")
            sections.append("")
            sections.append("#### HTML Content Preview")
            sections.append("```html")
            sections.append(blog.get('content', ''))
            sections.append("```")
            sections.append("")
            
            if blog.get('references'):
                ref_heading = "Sources" if "news" in blog.get('category', '').lower() else "Scientific References"
                sections.append(f"#### {ref_heading}")
                for ref in blog.get('references', []):
                    sections.append(f"- {ref}")
                sections.append("")
                
            sections.append("---")
            
    return '\n'.join(sections)