"""
History Agent - Responsible only for updating history.
Saves structured JSON campaign histories to history/history.json.
Provides compatibility wrappers to load legacy Markdown histories.
"""

import os
import json
import datetime
from typing import Dict, Any, List

from config import Config
from utils.logger import get_logger
from utils.files import ensure_directory, ensure_file

logger = get_logger(__name__)


def update_history(post: Dict[str, Any]) -> None:
    """
    Append today's Instagram post metadata to the history ledger file.

    Args:
        post: Instagram post dict from instagram_generator.
    """
    logger.info("Updating campaign history.json...")

    history_file = Config.get('HISTORY_FILE', 'history/history.json')
    ensure_directory(os.path.dirname(history_file))

    date_str = post.get('date') or datetime.date.today().strftime("%Y-%m-%d")

    # 2. Build history entry
    new_entry = {
        "date": date_str,
        "contentType": post.get('contentType', ''),
        "product": post.get('product', ''),
        "topic": post.get('topic', ''),
        "hashtags": post.get('hashtags', []),
    }
    
    # Load existing history JSON
    history_data = []
    if os.path.exists(history_file) and history_file.endswith('.json'):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
                if not isinstance(history_data, list):
                    history_data = []
        except Exception as e:
            logger.warning(f"Failed to parse history JSON ({e}). Starting fresh list.")
            
    # Append new entry (remove duplicates for same day if running repeatedly)
    history_data = [entry for entry in history_data if entry.get('date') != date_str]
    history_data.append(new_entry)
    
    # Save back to history.json
    try:
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=4)
        logger.info(f"Successfully appended history entry for {date_str} to {history_file}")
    except Exception as e:
        logger.error(f"Failed to save history update: {e}")


def get_history(limit: int = 30) -> List[Dict[str, Any]]:
    """
    Get recent history entries, falling back to legacy Markdown parsing if JSON is not available.
    
    Args:
        limit: Max entries to return.
        
    Returns:
        List of history entry dicts.
    """
    history_file = Config.get('HISTORY_FILE', 'history/history.json')
    
    if os.path.exists(history_file) and history_file.endswith('.json'):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return sorted(data, key=lambda x: x.get('date', ''), reverse=True)[:limit]
        except Exception as e:
            logger.error(f"Failed to read history JSON file: {e}")
            
    # Fallback to legacy markdown parsing
    md_file = "history/previous-posts.md"
    if os.path.exists(md_file):
        logger.info("Falling back to parsing legacy history/previous-posts.md")
        return _parse_md_history(md_file)[:limit]
        
    return []


def _parse_md_history(filepath: str) -> List[Dict[str, Any]]:
    """Parse markdown history file into structured JSON list format."""
    entries = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        current_entry = {}
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("## "):
                if current_entry:
                    entries.append(current_entry)
                current_entry = {
                    "date": line.replace("## ", "").strip(),
                    "topics": [],
                    "products": [],
                    "keywords": [],
                    "categories": ["General"],
                    "draft_ids": [],
                    "image_prompts": []
                }
            elif not current_entry:
                continue
            elif line.startswith("**Product:**"):
                prod = line.replace("**Product:**", "").strip()
                if prod:
                    current_entry["products"] = [prod]
            elif line.startswith("**Theme:**"):
                theme = line.replace("**Theme:**", "").strip()
                # Store theme or category if relevant
                pass
            elif line.startswith("**Topics:**"):
                # Following lines are bullet points of topics
                current_entry["topics_mode"] = True
            elif line.startswith("- ") and current_entry.get("topics_mode"):
                current_entry["topics"].append(line.replace("- ", "").strip())
            elif line.startswith("**Keywords:**"):
                current_entry["topics_mode"] = False
                kw_str = line.replace("**Keywords:**", "").strip()
                current_entry["keywords"] = [k.strip() for k in kw_str.split(",") if k.strip()]
            elif line.startswith("**Draft IDs:**"):
                ids_str = line.replace("**Draft IDs:**", "").strip()
                current_entry["draft_ids"] = [i.strip() for i in ids_str.split(",") if i.strip()]

        if current_entry:
            # Clean internal helper keys
            current_entry.pop("topics_mode", None)
            entries.append(current_entry)

    except Exception as e:
        logger.warning(f"Failed to parse legacy MD history: {e}")

    return sorted(entries, key=lambda x: x.get('date', ''), reverse=True)