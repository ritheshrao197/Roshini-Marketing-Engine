"""
Research Agent - Responsible only for collecting today's research data.
Loads sources, RSS feeds, APIs, and returns structured data.
"""

import os
import json
import datetime
from typing import Dict, Any, List
from collections import defaultdict

from config import Config
from ..utils.logger import get_logger
from llm import call_llm
from collectors.rss import RSSCollector
from collectors.health_news import HealthNewsCollector
from collectors.research import ResearchCollector
from collectors.recipes import RecipeCollector
from collectors.products import ProductCollector

logger = get_logger(__name__)


def research() -> Dict[str, Any]:
    """
    Load sources, RSS, APIs and collect today's research.
    
    Returns:
        Structured research data with topics, trends, and insights.
    """
    logger.info("Starting research collection...")
    
    # Load knowledge base
    knowledge_base = _load_knowledge_base()
    
    # Load calendar data
    calendar_data = _load_calendar()
    
    # Load history
    history_data = _load_history()
    
    # Collect from various sources
    rss_data = RSSCollector().collect()
    health_news = HealthNewsCollector().collect()
    research_data = ResearchCollector().collect()
    recipes = RecipeCollector().collect()
    products = ProductCollector().collect()
    
    # Combine and structure
    combined_data = _combine_research(
        rss_data=rss_data,
        health_news=health_news,
        research=research_data,
        recipes=recipes,
        products=products,
        knowledge_base=knowledge_base,
        calendar=calendar_data,
        history=history_data
    )
    
    # Generate research brief using LLM
    brief = _generate_research_brief(combined_data)
    
    # Extract topic and keywords
    topic_data = _extract_topic_data(brief)
    
    result = {
        "date": datetime.date.today().isoformat(),
        "brief": brief,
        "topics": topic_data.get("topics", []),
        "keywords": topic_data.get("keywords", []),
        "trends": combined_data.get("trends", []),
        "sources": combined_data.get("sources", []),
        "products": products,
        "recipes": recipes,
        "health_news": health_news,
        "knowledge_base": knowledge_base
    }
    
    logger.info(f"Research complete: {len(result['topics'])} topics found")
    return result


def _load_knowledge_base() -> Dict[str, str]:
    """Load all knowledge base files."""
    kb_dir = "knowledge-base"
    kb_content = {}
    
    # Load main knowledge files
    main_files = [
        "company.md",
        "brand-story.md",
        "certifications.md",
        "manufacturing-process.md",
        "shipping.md",
        "faq.md",
        "pricing.md",
        "customer-personas.md",
        "product-comparison.md",
        "health-claims.md"
    ]
    
    for filename in main_files:
        filepath = os.path.join(kb_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                kb_content[filename] = f.read()
    
    # Load product, ingredient, nutrition, and recipe files
    for folder in ["products", "ingredients", "nutrition", "recipes"]:
        folder_path = os.path.join(kb_dir, folder)
        if os.path.exists(folder_path):
            for filepath in os.listdir(folder_path):
                if filepath.endswith('.md'):
                    full_path = os.path.join(folder_path, filepath)
                    with open(full_path, 'r', encoding='utf-8') as f:
                        key = f"{folder}/{filepath}"
                        kb_content[key] = f.read()
    
    return kb_content


def _load_calendar() -> Dict[str, str]:
    """Load calendar data."""
    calendar_dir = "calendar"
    calendar_data = {}
    
    for filename in ["festivals.md", "campaigns.md"]:
        filepath = os.path.join(calendar_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                calendar_data[filename] = f.read()
    
    return calendar_data


def _load_history() -> List[Dict[str, Any]]:
    """Load history of previous posts."""
    history_file = "history/previous-posts.md"
    history_data = []
    
    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Parse markdown list items
            for line in content.split('\n'):
                if line.strip().startswith('-'):
                    history_data.append({
                        "entry": line.strip()[2:].strip()
                    })
    
    return history_data


def _combine_research(**kwargs) -> Dict[str, Any]:
    """Combine all research sources into structured data."""
    combined = {
        "trends": [],
        "sources": [],
        "insights": []
    }
    
    # Combine from different sources
    for key, value in kwargs.items():
        if isinstance(value, list):
            combined["sources"].extend(value)
        elif isinstance(value, dict):
            combined["insights"].extend(value.get("insights", []))
            combined["trends"].extend(value.get("trends", []))
    
    return combined


def _generate_research_brief(combined_data: Dict[str, Any]) -> str:
    """Generate research brief using LLM."""
    prompt = f"""
    You are the Research Agent for Roshini's Home Products.
    
    Based on the following data, create a comprehensive research brief:
    
    Calendar: {combined_data.get('calendar', {})}
    History: {combined_data.get('history', [])}
    Health News: {combined_data.get('health_news', [])}
    Recipes: {combined_data.get('recipes', [])}
    Products: {combined_data.get('products', [])}
    Knowledge Base: {combined_data.get('knowledge_base', {})}
    
    Provide:
    1. Today's nutrition topic
    2. Trending recipe ideas
    3. Seasonal events or festivals
    4. Competitor insights
    5. Recommended content angles
    6. Relevant keywords
    
    Output as a structured research brief.
    """
    
    response = call_llm(prompt, system_instruction="You are a research analyst specializing in health and nutrition content.")
    return response


def _extract_topic_data(brief: str) -> Dict[str, Any]:
    """Extract topics and keywords from research brief."""
    prompt = f"""
    Extract the main topics and keywords from this research brief:
    
    {brief}
    
    Return ONLY a valid JSON object:
    {{
        "topics": ["topic1", "topic2"],
        "keywords": ["keyword1", "keyword2"],
        "primary_topic": "main topic"
    }}
    """
    
    try:
        response = call_llm(prompt, json_format=True)
        # Clean response if needed
        response = response.strip().replace('```json', '').replace('```', '').strip()
        return json.loads(response)
    except Exception as e:
        logger.error(f"Failed to extract topics: {e}")
        return {
            "topics": ["Health & Wellness", "Nutrition", "Millets"],
            "keywords": ["nutrimix", "millet", "healthy", "wellness"],
            "primary_topic": "Health & Wellness"
        }