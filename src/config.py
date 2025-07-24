import os
import json
from pathlib import Path
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from loguru import logger
import sys


class ModelConfig(BaseModel):
    """Configuration for LLM models."""
    name: str = "phi-3-mini"
    context_window: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 1024
    model_config = ConfigDict(extra='forbid')


class SearchConfig(BaseModel):
    """Configuration for web search."""
    provider: Literal["duckduckgo", "serpapi"] = "duckduckgo"
    max_results: int = 10
    api_key: Optional[str] = None
    model_config = ConfigDict(extra='forbid')


class StorageConfig(BaseModel):
    """Configuration for data storage."""
    db_path: Path = Path.home() / "ai" / "chromadb_store"
    persist_interval: int = 5  # minutes
    model_config = ConfigDict(extra='forbid')


class LoggingConfig(BaseModel):
    """Configuration for logging."""
    level: str = "INFO"
    file_path: Path = Path.home() / "logs" / "researchbot.log"
    max_size: str = "10 MB"
    retention: str = "7 days"
    model_config = ConfigDict(extra='forbid')


class Config(BaseModel):
    """Main configuration class for ResearchBot."""
    # Core directive
    prompt: str

    # Core settings from environment
    use_lmstudio: bool = True
    openai_base_url: Optional[str] = None

    # Component configurations
    model: ModelConfig = Field(default_factory=ModelConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    model_config = ConfigDict(extra='forbid')

    @classmethod
    def load(cls, directives_path: Path = Path("Directives.json")) -> 'Config':
        """Create config from Directives.json and environment variables."""
        if not directives_path.is_file():
            raise FileNotFoundError(f"Directives file not found at {directives_path.resolve()}")

        with open(directives_path, 'r', encoding='utf-8') as f:
            directives = json.load(f)

        prompt = directives.get("Prompt")
        if not prompt or not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Directives.json must contain a non-empty 'Prompt' string.")

        config_data = {
            'prompt': prompt.strip(),
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
            }
        }

        return cls.model_validate(config_data)

    def setup_logging(self) -> None:
        """Configure logging based on config."""
        self.logging.file_path.parent.mkdir(parents=True, exist_ok=True)
        logger.remove()
        logger.add(
            self.logging.file_path,
            level=self.logging.level,
            rotation=self.logging.max_size,
            retention=self.logging.retention,
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )
        logger.add(
            sys.stderr,
            level=self.logging.level,
            colorize=True,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        logger.info("Logging configured")


# Global config instance
config = Config.load()
