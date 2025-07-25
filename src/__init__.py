"""
ResearchBot - An autonomous overnight research utility.

This package provides the core functionality for the ResearchBot application,
including web search, LLM integration, and data persistence.
"""

__version__ = "0.1.0"

# Import key components for easier access
from .config import config, Config
from .search import SearchEngine, SearchResult

__all__ = [
    'config',
    'Config',
    'SearchEngine',
    'SearchProvider',
    'SearchResult'
]
