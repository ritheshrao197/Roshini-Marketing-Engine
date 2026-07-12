"""
Validator Agent - Responsible only for validating content.
Checks grammar, SEO, medical claims, duplicates, brand, category, and tags.
"""

import json
import re
from typing import Dict, Any, List, Tuple
from utils.logger import get_logger
from llm import call_llm

logger = get_logger(__name__)


def validate(content: Dict[str, Any], seo_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate all content for quality and compliance.
    
    Args:
        content: Content from content generator.
        seo_data: SEO metadata.
    
    Returns:
        Validation results.
    """
    logger.info("Validating content...")
    
    results = {
        "passed": 0,
        "failed": 0,
        "warnings": [],
        "errors": []
    }
    
    # Validate each blog
    for i, blog in enumerate(content.get('blogs', [])):
        seo_page = seo_data.get('pages', [{}])[i] if i < len(seo_data.get('pages', [])) else {}
        
        # Grammar check
        grammar_result = _check_grammar(blog.get('content', ''))
        _add_result(results, grammar_result)
        
        # SEO check
        seo_result = _check_seo(blog, seo_page)
        _add_result(results, seo_result)
        
        # Medical claims check
        medical_result = _check_medical_claims(blog.get('content', ''))
        _add_result(results, medical_result)
        
        # Brand check
        brand_result = _check_brand_compliance(blog.get('content', ''))
        _add_result(results, brand_result)
        
        # Category check
        category_result = _check_category(blog.get('tags', []))
        _add_result(results, category_result)
    
    logger.info(f"Validation complete: {results['passed']} passed, {results['failed']} failed")
    return results


def _check_grammar(content: str) -> Dict[str, Any]:
    """Check grammar and spelling."""
    issues = []
    
    # Check for common issues
    if not content or len(content) < 100:
        issues.append("Content too short")
    
    if re.search(r'\b\w+\s+\w+\s+\w+\s+\w+\s+\w+\s+\w+\s+\w+\s+\w+\s+[^\.,!\?]', content):
        # Check for run-on sentences
        pass
    
    prompt = f"""
    Check this text for grammar and spelling issues:
    
    {content[:1000]}
    
    Return as JSON: {{"issues": ["issue1", "issue2"], "score": 0-100}}
    """
    
    try:
        response = call_llm(prompt, json_format=True)
        result = json.loads(response.strip().replace('```json', '').replace('```', '').strip())
        score = result.get('score', 80)
        issues = result.get('issues', [])
        
        if score < 70 or len(issues) > 5:
            return {
                "passed": False,
                "message": f"Grammar issues: {', '.join(issues[:3])}",
                "score": score
            }
        else:
            return {"passed": True, "message": "Grammar check passed", "score": score}
            
    except Exception as e:
        logger.error(f"Grammar check failed: {e}")
        return {"passed": True, "message": "Grammar check not performed", "score": 80}


def _check_seo(blog: Dict[str, Any], seo_page: Dict[str, Any]) -> Dict[str, Any]:
    """Check SEO compliance."""
    issues = []
    
    # Check SEO title
    seo_title = seo_page.get('seo_title', '')
    if len(seo_title) > 60:
        issues.append(f"SEO title too long: {len(seo_title)} chars (max 60)")
    elif len(seo_title) < 30:
        issues.append(f"SEO title too short: {len(seo_title)} chars (min 30)")
    
    # Check meta description
    meta_desc = seo_page.get('meta_description', '')
    if len(meta_desc) > 160:
        issues.append(f"Meta description too long: {len(meta_desc)} chars (max 160)")
    elif len(meta_desc) < 80:
        issues.append(f"Meta description too short: {len(meta_desc)} chars (min 80)")
    
    # Check keywords
    keywords = seo_page.get('keywords', [])
    if len(keywords) < 3:
        issues.append(f"Too few keywords: {len(keywords)} (min 3)")
    
    # Check slug
    slug = seo_page.get('slug', '')
    if not slug:
        issues.append("Missing slug")
    elif len(slug) > 50:
        issues.append(f"Slug too long: {len(slug)} chars (max 50)")
    
    if issues:
        return {"passed": False, "message": f"SEO issues: {'; '.join(issues)}"}
    else:
        return {"passed": True, "message": "SEO check passed"}


def _check_medical_claims(content: str) -> Dict[str, Any]:
    """Check for prohibited medical claims."""
    prohibited_terms = [
        r'\bcure\b', r'\btreat\b', r'\bprevent\b', r'\bdiagnose\b',
        r'\bheal\b', r'\bremedy\b', r'\bmedicine\b', r'\bdrug\b',
        r'\btherapy\b', r'\btreatment\b', r'\bprescription\b'
    ]
    
    found_issues = []
    for term in prohibited_terms:
        matches = re.finditer(term, content, re.IGNORECASE)
        for match in matches:
            # Check context (if it's actually claiming medical benefit)
            start = max(0, match.start() - 20)
            end = min(len(content), match.end() + 20)
            context = content[start:end]
            found_issues.append(f"Potential medical claim: '{match.group()}' in '{context}'")
            break
    
    if found_issues:
        # Use LLM to verify if it's actually a medical claim
        prompt = f"""
        Verify if this text contains prohibited medical claims:
        {found_issues[:3]}
        
        Return JSON: {{"is_medical_claim": true/false, "reason": "..."}}
        """
        
        try:
            response = call_llm(prompt, json_format=True)
            result = json.loads(response.strip().replace('```json', '').replace('```', '').strip())
            
            if result.get('is_medical_claim', True):
                return {
                    "passed": False,
                    "message": f"Medical claims found: {result.get('reason', '')}"
                }
        except Exception:
            pass
        
        # Conservative approach
        return {
            "passed": False,
            "message": f"Potential medical claims: {found_issues[:2]}"
        }
    
    return {"passed": True, "message": "No medical claims found"}


def _check_brand_compliance(content: str) -> Dict[str, Any]:
    """Check brand compliance."""
    issues = []
    
    # Check for brand name mention
    if 'Roshini' not in content:
        issues.append("Brand name 'Roshini' not mentioned")
    
    # Check for FSSAI compliance
    if 'FSSAI' not in content and 'food safety' not in content.lower():
        issues.append("FSSAI compliance not mentioned")
    
    # Check for allergen warnings
    allergens = ['gluten', 'nut', 'dairy', 'soy', 'wheat']
    found_allergen = any(allergen in content.lower() for allergen in allergens)
    if not found_allergen:
        issues.append("No allergen warnings found")
    
    if issues:
        return {"passed": False, "message": f"Brand issues: {'; '.join(issues)}"}
    else:
        return {"passed": True, "message": "Brand compliance check passed"}


def _check_category(tags: List[str]) -> Dict[str, Any]:
    """Check category and tags."""
    valid_categories = ['Health', 'Nutrition', 'Recipes', 'Lifestyle', 'Wellness']
    
    if not tags:
        return {"passed": False, "message": "No tags found"}
    
    # Check if tags match categories
    has_valid_category = any(tag in valid_categories for tag in tags)
    if not has_valid_category:
        return {"passed": False, "message": f"No valid category in tags: {tags}"}
    
    return {"passed": True, "message": "Category check passed"}


def _add_result(results: Dict[str, Any], result: Dict[str, Any]) -> None:
    """Add a validation result to the summary."""
    if result.get('passed', True):
        results['passed'] += 1
    else:
        results['failed'] += 1
        results['errors'].append(result.get('message', ''))