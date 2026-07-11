import time
import threading
from datetime import datetime, timedelta

# Thread safety lock for health updates
_lock = threading.Lock()

# Dictionary to hold provider health profiles
# Schema: { provider_name: { last_success, last_failure, latency_sum, request_count, consecutive_failures, cooldown_until } }
PROVIDER_HEALTH = {}

COOLDOWN_DURATION_MINUTES = 10

def _init_provider_stats(provider_name: str):
    """Initializes default statistics for a provider if not exists."""
    if provider_name not in PROVIDER_HEALTH:
        PROVIDER_HEALTH[provider_name] = {
            "last_success": None,
            "last_failure": None,
            "latency_sum": 0.0,
            "request_count": 0,
            "consecutive_failures": 0,
            "cooldown_until": None
        }

def is_provider_healthy(provider_name: str) -> bool:
    """
    Checks if a provider is healthy.
    Returns False if the provider is currently cooled down, otherwise True.
    """
    with _lock:
        _init_provider_stats(provider_name)
        cooldown = PROVIDER_HEALTH[provider_name]["cooldown_until"]
        if cooldown:
            if datetime.utcnow() < cooldown:
                return False
            else:
                # Cooldown expired
                PROVIDER_HEALTH[provider_name]["cooldown_until"] = None
        return True

def report_success(provider_name: str, latency: float):
    """Logs a successful execution, updating latency metrics and resetting failures."""
    with _lock:
        _init_provider_stats(provider_name)
        stats = PROVIDER_HEALTH[provider_name]
        stats["last_success"] = datetime.utcnow().isoformat()
        stats["latency_sum"] += latency
        stats["request_count"] += 1
        stats["consecutive_failures"] = 0
        stats["cooldown_until"] = None

def report_failure(provider_name: str, is_429: bool = False):
    """
    Logs a request failure. If failures exceed thresholds or it is a 429 rate limit, 
    triggers a cooldown.
    """
    with _lock:
        _init_provider_stats(provider_name)
        stats = PROVIDER_HEALTH[provider_name]
        stats["last_failure"] = datetime.utcnow().isoformat()
        stats["consecutive_failures"] += 1
        
        # If rate limited (429) or 3 consecutive general failures occur, initiate cooldown
        if is_429 or stats["consecutive_failures"] >= 3:
            cooldown_time = datetime.utcnow() + timedelta(minutes=COOLDOWN_DURATION_MINUTES)
            stats["cooldown_until"] = cooldown_time
            print(f"[HEALTH] Provider '{provider_name}' placed in cooldown until {cooldown_time.isoformat()} (429={is_429})")
