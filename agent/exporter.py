"""
Exporter Agent - Responsible only for generating the daily export files.
Creates outputs/YYYY-MM-DD.md and outputs/YYYY-MM-DD.json for the day's
single Instagram post package.
"""

import json
import datetime
from typing import Dict, Any, Optional
from config import Config
from utils.files import ensure_directory
from utils.logger import get_logger

logger = get_logger(__name__)


def export_package(post: Dict[str, Any], image_path: Optional[str]) -> str:
    """
    Export the daily Instagram post package into Markdown and JSON formats.

    Args:
        post: Instagram post dict from instagram_generator.
        image_path: Local path to the generated image, if any.

    Returns:
        The file path of the markdown package.
    """
    logger.info("Exporting daily Instagram package...")

    date_str = post.get('date') or datetime.date.today().strftime("%Y-%m-%d")
    output_dir = Config.get('OUTPUT_DIR', 'outputs')
    ensure_directory(output_dir)

    md_filename = f"{output_dir}/{date_str}.md"
    json_filename = f"{output_dir}/{date_str}.json"

    markdown_content = _build_markdown(post, image_path, date_str)
    with open(md_filename, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    logger.info(f"   💾 Saved Markdown to {md_filename}")

    json_data = dict(post)
    json_data['imagePath'] = image_path
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=4, ensure_ascii=False)
    logger.info(f"   💾 Saved Content JSON to {json_filename}")

    return md_filename


def _build_markdown(post: Dict[str, Any], image_path: Optional[str], date_str: str) -> str:
    """Build markdown package presentation."""
    sections = [f"# Daily Instagram Post: {date_str}\n"]

    sections.append("## Summary")
    sections.append(f"- **Content Type:** {post.get('contentType', 'N/A')}")
    sections.append(f"- **Product:** {post.get('product', 'N/A')}")
    sections.append(f"- **Topic:** {post.get('topic', 'N/A')}")
    sections.append(f"- **Image:** {image_path or 'Not generated'}")
    sections.append("")

    sections.append("## English Caption")
    sections.append(post.get('captionEn', 'N/A'))
    sections.append("")

    sections.append("## Kannada Caption")
    sections.append(post.get('captionKn', 'N/A'))
    sections.append("")

    sections.append("## Hashtags")
    sections.append(' '.join(post.get('hashtags', [])) or 'N/A')
    sections.append("")

    sections.append("## Image Prompt")
    sections.append(f"```\n{post.get('imagePrompt', 'N/A')}\n```")
    sections.append("")

    return '\n'.join(sections)
