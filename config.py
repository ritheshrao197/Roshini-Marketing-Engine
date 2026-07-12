"""
Configuration management for the marketing pipeline.
Loads environment variables and provides configuration access.
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv


class Config:
    """Configuration manager."""
    
    _instance = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from environment."""
        # Load .env file
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_file):
            load_dotenv(env_file)
        
        # Essential configuration
        self._config = {
            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
            'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN'),
            'TELEGRAM_CHAT_ID': os.getenv('TELEGRAM_CHAT_ID'),
            'BACKEND_BASE_URL': os.getenv('BACKEND_BASE_URL', 'https://roshini-backend.onrender.com/api'),
            'WEBSITE_API_URL': os.getenv('WEBSITE_API_URL', 'https://roshini-backend.onrender.com/api'),
            'WEBSITE_API_KEY': os.getenv('WEBSITE_API_KEY'),
            'OUTPUT_DIR': os.getenv('OUTPUT_DIR', 'outputs'),
            'LOG_DIR': os.getenv('LOG_DIR', 'logs'),
            'CACHE_DIR': os.getenv('CACHE_DIR', 'cache'),
            'HISTORY_FILE': os.getenv('HISTORY_FILE', 'history/history.json'),
            'MAX_RETRIES': int(os.getenv('MAX_RETRIES', '3')),
            'TIMEOUT': int(os.getenv('TIMEOUT', '30')),
        }
    
    @classmethod
    def get(cls, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration value."""
        instance = cls()
        return instance._config.get(key, default)
    
    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """Set configuration value."""
        instance = cls()
        instance._config[key] = value
    
    @classmethod
    def load_env(cls) -> None:
        """Load environment variables (compatibility method)."""
        cls()
    
    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """Get all configuration."""
        return cls()._config.copy()