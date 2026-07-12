"""
History Agent - Responsible only for updating history.
Appends date, product, topics, keywords, and draft IDs.
"""

import os
import datetime
from typing import Dict, Any, List

from config import Config
from utils.logger import get_logger
from utils.files import ensure_directory, ensure_file

logger = get_logger(__name__)


def update_history(content: Dict[str, Any], seo_data: Dict[str, Any], upload_results: Dict[str, Any]) -> None:
    """
    Update history ledger with today's content.
    
    Args:
        content: Content from content generator.
        seo_data: SEO metadata.
        upload_results: Results from uploader.
    """
    logger.info("Updating history...")
    
    history_file = Config.get('HISTORY_FILE', 'history/previous-posts.md')
    ensure_directory(os.path.dirname(history_file))
    ensure_file(history_file)
    
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    
    # Build entry
    entry = _build_entry(content, seo_data, upload_results, date_str)
    
    # Append to history
    with open(history_file, 'a', encoding='utf-8') as f:
        f.write(f"\n{entry}")
    
    logger.info(f"History updated: {date_str}")


def _build_entry(content: Dict[str, Any], seo_data: Dict[str, Any], upload_results: Dict[str, Any], date_str: str) -> str:
    """Build history entry."""
    product = content.get('product', 'N/A')
    theme = content.get('theme', 'N/A')
    blogs = content.get('blogs', [])
    draft_ids = upload_results.get('draft_ids', [])
    
    # Build topics
    topics = []
    for blog in blogs:
        title = blog.get('title', '')
        if title:
            topics.append(title)
    
    # Build keywords
    keywords = []
    for page in seo_data.get('pages', []):
        keywords.extend(page.get('keywords', []))
    
    # Deduplicate keywords
    keywords = list(dict.fromkeys(keywords))
    
    entry = f"""
## {date_str}

**Product:** {product}
**Theme:** {theme}
**Topics:**
{chr(10).join(['- ' + topic for topic in topics[:5]])}

**Keywords:** {', '.join(keywords[:10])}
**Draft IDs:** {', '.join(draft_ids[:3])}
**Blog Count:** {len(blogs)}
---
"""
    
    return entry


def get_history(limit: int = 30) -> List[Dict[str, Any]]:
    """
    Get recent history entries.
    
    Args:
        limit: Maximum number of entries to return.
    
    Returns:
        List of history entries.
    """
    history_file = Config.get('HISTORY_FILE', 'history/previous-posts.md')
    
    if not os.path.exists(history_file):
        return []
    
    entries = []
    current_entry = {}
    
    with open(history_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            if line.startswith('## '):
                if current_entry:
                    entries.append(current_entry)
                current_entry = {'date': line.replace('## ', '').strip()}
                
            elif line.startswith('**Product:**'):
                current_entry['product'] = line.replace('**Product:**', '').strip()
                
            elif line.startswith('**Theme:**'):
                current_entry['theme'] = line.replace('**Theme:**', '').strip()
                
            elif line.startswith('**Topics:**'):
                current_entry['topics'] = []
                
            elif line.startswith('- ') and 'topics' in current_entry:
                current_entry['topics'].append(line.replace('- ', '').strip())
                
            elif line.startswith('**Keywords:**'):
                keywords_str = line.replace('**Keywords:**', '').strip()
                current_entry['keywords'] = [k.strip() for k in keywords_str.split(',') if k.strip()]
                
            elif line.startswith('**Draft IDs:**'):
                ids_str = line.replace('**Draft IDs:**', '').strip()
                current_entry['draft_ids'] = [i.strip() for i in ids_str.split(',') if i.strip()]
                
            elif line.startswith('**Blog Count:**'):
                try:
                    current_entry['blog_count'] = int(line.replace('**Blog Count:**', '').strip())
                except ValueError:
                    current_entry['blog_count'] = 0
    
    if current_entry:
        entries.append(current_entry)
    
    return entries[:limit]