import os
import hashlib
import sqlite3
from datetime import datetime

# Database file inside scratch directory in the workspace root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRATCH_DIR = os.path.join(BASE_DIR, "scratch")
DB_PATH = os.path.join(SCRATCH_DIR, "llm_cache.db")

def init_db():
    """Initializes the SQLite cache table if it doesn't exist."""
    os.makedirs(SCRATCH_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompt_cache (
            hash TEXT PRIMARY KEY,
            system_prompt TEXT,
            user_prompt TEXT,
            prompt_version TEXT,
            model TEXT,
            temperature REAL,
            response TEXT,
            provider TEXT,
            latency REAL,
            token_count INTEGER,
            cost REAL,
            status TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

# Initialize database at module load time
init_db()

def compute_hash(system_prompt: str, user_prompt: str, prompt_version: str, model_name: str, temperature: float) -> str:
    """Computes SHA-256 hash based on system, user prompts, prompt version, model, and temp."""
    payload = f"{system_prompt or ''}||{user_prompt or ''}||{prompt_version or 'v1'}||{model_name}||{temperature}"
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()

def get_cached_response(hash_val: str) -> dict:
    """Looks up and returns a cached response metadata structure, or None if miss."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM prompt_cache WHERE hash = ?", (hash_val,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def set_cached_response(
    hash_val: str,
    system_prompt: str,
    user_prompt: str,
    prompt_version: str,
    model: str,
    temperature: float,
    response: str,
    provider: str,
    latency: float,
    token_count: int,
    cost: float,
    status: str
):
    """Saves response copy and full metadata details to SQLite prompt_cache table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    created_at = datetime.utcnow().isoformat()
    cursor.execute("""
        INSERT OR REPLACE INTO prompt_cache (
            hash, system_prompt, user_prompt, prompt_version, model, 
            temperature, response, provider, latency, token_count, 
            cost, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        hash_val, system_prompt, user_prompt, prompt_version, model,
        temperature, response, provider, latency, token_count,
        cost, status, created_at
    ))
    conn.commit()
    conn.close()
