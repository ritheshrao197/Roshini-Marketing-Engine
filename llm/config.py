import os
import yaml

# Determine base path for the module
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "models.yaml")

# Load local .env relative to the project root (parent of llm folder)
def _load_dotenv():
    project_root = os.path.dirname(BASE_DIR)
    filepath = os.path.join(project_root, ".env")
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip().strip("'").strip('"')

_load_dotenv()

# Primary configuration variables loaded from .env/environment
PRIMARY_PROVIDER = os.getenv("PRIMARY_PROVIDER", "auto")
ENABLE_FALLBACK = os.getenv("ENABLE_FALLBACK", "true").lower() == "true"
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "60"))
MAX_DAILY_COST = float(os.getenv("MAX_DAILY_COST", "2.0"))
LLM_CACHE_ENABLED = os.getenv("LLM_CACHE_ENABLED", "true").lower() == "true"


def load_models_config():
    """Loads and returns the models.yaml configuration."""
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH}")
    
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_available_providers():
    """
    Returns a dictionary of active providers based on available environment credentials.
    Key: provider_name, Value: {base_url, api_key_env, api_key_value, models}
    """
    config = load_models_config()
    providers_config = config.get("providers", {})
    available = {}
    
    for name, info in providers_config.items():
        key_env = info.get("api_key_env")
        # Ollama doesn't require a strict key, but might have a URL configured.
        # If no OLLAMA_URL is set, we can check standard http://localhost:11434
        if name == "ollama":
            url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            available[name] = {
                "base_url": url + "/v1" if not url.endswith("/v1") else url,
                "api_key": "ollama",
                "models": info.get("models", [])
            }
        elif key_env:
            key_val = os.getenv(key_env)
            if key_val:
                available[name] = {
                    "base_url": info.get("base_url"),
                    "api_key": key_val,
                    "models": info.get("models", [])
                }
                
    return available
