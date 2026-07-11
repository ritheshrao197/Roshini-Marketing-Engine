import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
HISTORY_PATH = os.path.join(LOGS_DIR, "llm_history.jsonl")
STATS_PATH = os.path.join(LOGS_DIR, "provider_stats.json")

def _ensure_logs_dir():
    os.makedirs(LOGS_DIR, exist_ok=True)

def log_request(
    provider: str,
    model: str,
    latency: float,
    tokens: int,
    cached: bool,
    status: str,
    cost: float,
    error: str = None
):
    """Writes a structured JSON line entry to logs/llm_history.jsonl."""
    _ensure_logs_dir()
    
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "provider": provider,
        "model": model,
        "latency": round(latency, 3),
        "tokens": tokens,
        "cached": cached,
        "status": status,
        "cost": round(cost, 6),
        "error": error
    }
    
    with open(HISTORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
        
    # Also update provider aggregated statistics
    update_provider_stats(provider, latency, status, cached, cost)

def update_provider_stats(
    provider: str,
    latency: float,
    status: str,
    cached: bool,
    cost: float
):
    """Updates and saves aggregated performance statistics in logs/provider_stats.json."""
    _ensure_logs_dir()
    
    stats = {}
    if os.path.exists(STATS_PATH):
        try:
            with open(STATS_PATH, "r", encoding="utf-8") as f:
                stats = json.load(f)
        except Exception:
            stats = {}
            
    if provider not in stats:
        stats[provider] = {
            "requests": 0,
            "failures": 0,
            "latency_sum": 0.0,
            "cache_hits": 0,
            "cost": 0.0
        }
        
    p_stats = stats[provider]
    p_stats["requests"] += 1
    if status == "failure":
        p_stats["failures"] += 1
    if not cached:
        p_stats["latency_sum"] += latency
    if cached:
        p_stats["cache_hits"] += 1
    p_stats["cost"] += cost
    
    # Calculate averages
    non_cached_reqs = p_stats["requests"] - p_stats["cache_hits"]
    p_stats["average_latency"] = round(
        p_stats["latency_sum"] / max(non_cached_reqs, 1), 3
    )
    p_stats["cache_hit_rate_pct"] = round(
        (p_stats["cache_hits"] / p_stats["requests"]) * 100, 1
    )
    
    try:
        with open(STATS_PATH, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        print(f"[ANALYTICS] Failed to write provider stats: {e}")
