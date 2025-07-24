"""
Search module for ResearchBot.

Provides web search functionality using DuckDuckGo and SerpAPI.
"""
import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional, AsyncGenerator
from urllib.parse import urlparse

import aiohttp
from duckduckgo_search import AsyncDDGS
from loguru import logger

from .config import config


class SearchProvider(Enum):
    """Supported search providers."""
    DUCKDUCKGO = "duckduckgo"
    SERPAPI = "serpapi"


@dataclass
class SearchResult:
    """Represents a single search result."""
    title: str
    url: str
    snippet: str
    source: str
    favicon: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "favicon": self.favicon,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchResult':
        """Create from dictionary."""
        return cls(**data)


class SearchEngine:
    """Search engine for web content."""
    
    def __init__(self, provider: SearchProvider = SearchProvider.DUCKDUCKGO, 
                 api_key: Optional[str] = None, max_results: int = 10):
        """Initialize the search engine.
        
        Args:
            provider: Search provider to use
            api_key: API key for SerpAPI (if using SerpAPI)
            max_results: Maximum number of results to return per query
        """
        self.provider = provider
        self.api_key = api_key
        self.max_results = max_results
        self._rate_limit = 1.0  # Minimum seconds between requests
        self._last_request = 0.0
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
            self._session = None

    async def _enforce_rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request
        if elapsed < self._rate_limit:
            await asyncio.sleep(self._rate_limit - elapsed)
        self._last_request = time.time()

    async def _search_duckduckgo(self, query: str) -> List[SearchResult]:
        """Search using DuckDuckGo."""
        await self._enforce_rate_limit()
        
        try:
            results = []
            async with AsyncDDGS() as ddgs:
                async for result in ddgs.text(query, max_results=self.max_results):
                    if not all(key in result for key in ['title', 'href', 'body']):
                        continue
                    
                    domain = urlparse(result['href']).netloc
                    results.append(SearchResult(
                        title=result['title'],
                        url=result['href'],
                        snippet=result['body'],
                        source=domain,
                        favicon=f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
                    ))
                    
                    if len(results) >= self.max_results:
                        break
                        
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []

    async def _search_serpapi(self, query: str) -> List[SearchResult]:
        """Search using SerpAPI."""
        if not self.api_key:
            logger.error("SerpAPI key not provided")
            return []
            
        await self._enforce_rate_limit()
        
        params = {
            'q': query,
            'api_key': self.api_key,
            'num': self.max_results,
            'hl': 'en',
            'gl': 'us'
        }
        
        try:
            if not self._session:
                self._session = aiohttp.ClientSession()
                
            async with self._session.get('https://serpapi.com/search', params=params) as response:
                data = await response.json()
                
                if 'error' in data:
                    logger.error(f"SerpAPI error: {data['error']}")
                    return []
                    
                results = []
                for result in data.get('organic_results', [])[:self.max_results]:
                    domain = urlparse(result.get('link', '')).netloc
                    results.append(SearchResult(
                        title=result.get('title', ''),
                        url=result.get('link', ''),
                        snippet=result.get('snippet', ''),
                        source=domain,
                        favicon=result.get('favicon', '')
                    ))
                    
                return results
                
        except Exception as e:
            logger.error(f"SerpAPI search failed: {e}")
            return []

    async def search(self, query: str) -> List[SearchResult]:
        """Search the web for the given query.
        
        Args:
            query: The search query string
            
        Returns:
            List of SearchResult objects
        """
        if not query or not query.strip():
            return []
            
        logger.info(f"Searching for: {query}")
        
        try:
            if self.provider == SearchProvider.SERPAPI:
                return await self._search_serpapi(query)
            else:
                return await self._search_duckduckgo(query)
                
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def batch_search(self, queries: List[str]) -> Dict[str, List[SearchResult]]:
        """Perform multiple searches in parallel.
        
        Args:
            queries: List of search queries
            
        Returns:
            Dictionary mapping queries to their search results
        """
        if not queries:
            return {}
            
        tasks = [self.search(query) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        return {
            query: result if not isinstance(result, Exception) else []
            for query, result in zip(queries, results)
        }
