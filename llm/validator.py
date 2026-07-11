import json
import re

def validate_structured_output(text: str) -> tuple[bool, str | None]:
    """
    Verifies that the generated markdown package contains the expected pipeline markers
    and complies with structural expectations (caption, hashtags, image prompts).
    Returns (is_valid, error_message).
    """
    required_markers = [
        "--- START SELECTION ---",
        "--- START CAMPAIGN PART 1 ---",
        "--- START CAMPAIGN PART 2 ---",
        "--- START CAMPAIGN PART 3 ---",
        "--- START IMAGE PROMPTS ---"
    ]
    
    # 1. Check all standard pipeline headers exist
    for marker in required_markers:
        if marker not in text:
            return False, f"Missing required pipeline marker: '{marker}'"
            
    # 2. Check for Caption, CTA, Hashtags structure in Part 2 or Part 3
    # Look for caption section header (usually ## 7. Caption)
    if "Caption" not in text and "caption" not in text.lower():
        return False, "Missing Caption section in the generated content."
        
    # Look for hashtags (Instagram hashtags usually start with #)
    if "#" not in text:
        return False, "Missing hashtags (#) in the generated content."
        
    # 3. Verify JSON block at the end is parseable
    try:
        parts = text.split("--- START IMAGE PROMPTS ---")
        if len(parts) < 2:
            return False, "Could not locate Image Prompts block after marker."
        
        json_content = parts[1].strip()
        # Clean any markdown code fences if present
        json_content = json_content.replace("```json", "").replace("```", "").strip()
        
        parsed_json = json.loads(json_content)
        if not isinstance(parsed_json, dict):
            return False, "Image prompts block is not a valid JSON object."
            
        # Ensure at least post image exists
        if "instagram_post_image" not in parsed_json:
            return False, "Missing 'instagram_post_image' prompt in parsed JSON."
            
    except json.JSONDecodeError as jde:
        return False, f"Failed to parse Image Prompts JSON block: {jde}"
    except Exception as e:
        return False, f"Output validation failed: {e}"

    return True, None
