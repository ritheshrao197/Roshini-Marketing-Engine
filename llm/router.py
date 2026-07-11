import os
import json
from datetime import datetime
from llm.config import get_available_providers, MAX_DAILY_COST, PRIMARY_PROVIDER
from llm.health import is_provider_healthy

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_PATH = os.path.join(BASE_DIR, "logs", "llm_history.jsonl")

def get_today_cost() -> float:
    """Calculates total cost spent on LLM requests today."""
    if not os.path.exists(HISTORY_PATH):
        return 0.0
        
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    total_cost = 0.0
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line.strip())
                    # Check if log entry was created today
                    if entry.get("timestamp", "").startswith(today_str):
                        total_cost += entry.get("cost", 0.0)
    except Exception as e:
        print(f"[ROUTER] Error reading today's cost: {e}")
        
    return total_cost

def calculate_score(model_spec: dict) -> float:
    """
    Calculates model score:
    score = free * 40 + speed * 25 + context * 20 + json_support * 10 + vision * 5
    """
    free_val = 1.0 if model_spec.get("is_free", False) else 0.0
    speed_val = float(model_spec.get("speed", 5))
    context_val = float(model_spec.get("context", 5))
    json_val = 1.0 if model_spec.get("json_support", False) else 0.0
    vision_val = 1.0 if model_spec.get("vision", False) else 0.0
    
    score = (free_val * 40.0) + (speed_val * 25.0) + (context_val * 20.0) + (json_val * 10.0) + (vision_val * 5.0)
    return score

def choose_models(requires_json: bool = False, requires_vision: bool = False) -> list[dict]:
    """
    Selects and ranks available models based on availability, health, capability, cost constraints.
    Returns:
        list of dict: [{"provider": str, "model": str, "score": float, "spec": dict}]
    """
    providers = get_available_providers()
    candidates = []
    
    # 1. Budget enforcement: Check if we exceeded our daily limits
    today_cost = get_today_cost()
    force_free = today_cost >= MAX_DAILY_COST
    if force_free:
        print(f"[ROUTER] Daily budget of ${MAX_DAILY_COST} exceeded (spent: ${today_cost:.4f}). Forcing FREE models only.")

    for p_name, p_info in providers.items():
        # 2. Skip cooled down/unhealthy providers
        if not is_provider_healthy(p_name):
            print(f"[ROUTER] Skipping unhealthy/cooled-down provider: {p_name}")
            continue
            
        models = p_info.get("models", [])
        for model in models:
            # 3. Apply capability matching
            if requires_json and not model.get("json_support", False):
                continue
            if requires_vision and not model.get("vision", False):
                continue
                
            # 4. Budget filter
            if force_free and not model.get("is_free", False):
                continue
                
            score = calculate_score(model)
            candidates.append({
                "provider": p_name,
                "model": model.get("name"),
                "score": score,
                "spec": model,
                "base_url": p_info.get("base_url"),
                "api_key": p_info.get("api_key")
            })
            
    # 5. Sort candidates by score descending
    candidates.sort(key=lambda x: x["score"], reverse=True)
    
    # 6. Respect PRIMARY_PROVIDER override if it's explicitly set and healthy
    if PRIMARY_PROVIDER != "auto":
        # Find if primary provider matches any candidates, put them at the top
        matched = [c for c in candidates if c["provider"] == PRIMARY_PROVIDER]
        unmatched = [c for c in candidates if c["provider"] != PRIMARY_PROVIDER]
        candidates = matched + unmatched
        
    return candidates
