"""Configuration management for ResearchBot."""
import os
from pathlib import Path
from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from loguru import logger

class ModelConfig(BaseModel):
    """Configuration for LLM models."""
    name: str = "phi-3-mini"
    context_window: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 1024

class SearchConfig(BaseModel):
    """Configuration for web search."""
    provider: Literal["duckduckgo", "serpapi"] = "duckduckgo"
    max_results: int = 10
    api_key: Optional[str] = None

class StorageConfig(BaseModel):
    """Configuration for data storage."""
    db_path: Path = Path.home() / "ai" / "chromadb_store"
    persist_interval: int = 5  # minutes

class LoggingConfig(BaseModel):
    """Configuration for logging."""
    level: str = "INFO"
    file_path: Path = Path.home() / "logs" / "researchbot.log"
    max_size: str = "10 MB"
    retention: str = "7 days"

class Config(BaseModel):
    """Main configuration class for ResearchBot."""
    # Core settings
    topic: str = ""
    use_lmstudio: bool = True
    openai_base_url: Optional[str] = None
    
    # Model settings
    model: ModelConfig = Field(default_factory=ModelConfig)
    
    # Component configurations
    search: SearchConfig = Field(default_factory=SearchConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    @field_validator('topic')
    def validate_topic(cls, v: str) -> str:
        """Validate that topic is not empty."""
        if not v or not v.strip():
            raise ValueError("Research topic cannot be empty")
        return v.strip()
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create config from environment variables."""
        # Get base config from environment
        config = {
            'topic': os.getenv('RESEARCH_TOPIC', ''),
            'use_lmstudio': os.getenv('USE_LMSTUDIO', '1') == '1',
            'openai_base_url': os.getenv('OPENAI_BASE_URL'),
            'model': {
                'name': os.getenv('MODEL', 'phi-3-mini'),
            },
            'search': {
                'provider': os.getenv('SEARCH_PROVIDER', 'duckduckgo'),
                'api_key': os.getenv('SERPAPI_API_KEY'),
            },
            'logging': {
                'level': os.getenv('LOG_LEVEL', 'INFO'),
                'file_path': Path(os.getenv('LOG_PATH', '~/logs/researchbot.log')).expanduser(),
            }
        }
        
        return cls.model_validate(config)
    
    def setup_logging(self) -> None:
        """Configure logging based on config."""
        # Create log directory if it doesn't exist
        self.logging.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove default logger
        logger.remove()
        
        # Add file handler
        logger.add(
            self.logging.file_path,
            level=self.logging.level,
            rotation=self.logging.max_size,
            retention=self.logging.retention,
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )
        
        # Add console handler
        logger.add(
            sys.stderr,
            level=self.logging.level,
            colorize=True,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        
        logger.info("Logging configured")

# Global config instance
config = Config.from_env()
