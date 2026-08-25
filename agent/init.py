"""
Agent modules for the marketing pipeline.
Each agent has a single, focused responsibility.
"""

from agent.research import research
from agent.instagram_generator import generate_daily_instagram_post
from agent.exporter import export_package
from agent.telegram import notify
from agent.history import update_history

__all__ = [
    'research',
    'generate_daily_instagram_post',
    'export_package',
    'notify',
    'update_history'
]
