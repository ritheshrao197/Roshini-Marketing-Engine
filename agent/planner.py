"""
Planner Agent - Responsible only for planning content strategy.
Chooses product, theme, customer persona, and website topics.
"""

from typing import Dict, Any
from utils.logger import get_logger
from llm import call_llm

logger = get_logger(__name__)


def plan(research_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Choose product, theme, persona, and website topics based on research.
    
    Args:
        research_data: Structured research data from research agent.
    
    Returns:
        Plan with product, theme, persona, and topics.
    """
    logger.info("Planning content strategy...")
    
    # Extract relevant data
    topics = research_data.get('topics', [])
    keywords = research_data.get('keywords', [])
    trends = research_data.get('trends', [])
    products = research_data.get('products', {})
    knowledge_base = research_data.get('knowledge_base', {})
    
    # Generate plan using LLM
    prompt = f"""
    You are the Content Planner for Roshini's Home Products.
    
    Based on this research:
    Topics: {topics}
    Keywords: {keywords}
    Trends: {trends}
    Available Products: {products}
    Brand Info: {knowledge_base.get('company.md', '')}
    
    Create a content plan for today including:
    1. Instagram Product (select from available products)
    2. Today's Theme (based on trends and calendar)
    3. Customer Persona (from knowledge base)
    4. Website Topics (2-3 blog topics)
    
    Return ONLY a valid JSON object:
    {{
        "product": "product_name",
        "theme": "theme_name",
        "persona": "persona_name",
        "website_topics": ["topic1", "topic2", "topic3"]
    }}
    """
    
    try:
        response = call_llm(prompt, json_format=True)
        response = response.strip().replace('```json', '').replace('```', '').strip()
        plan_data = json.loads(response)
        
        logger.info(f"Plan complete: {plan_data.get('product')} - {plan_data.get('theme')}")
        return plan_data
        
    except Exception as e:
        logger.error(f"Planning failed: {e}")
        # Return fallback plan
        return {
            "product": "Nutrimix",
            "theme": "Health & Wellness",
            "persona": "Health-conscious parent",
            "website_topics": [
                "Nutrition Benefits of Millets",
                "Healthy Recipes for Families",
                "Wellness Tips for Daily Life"
            ]
        }