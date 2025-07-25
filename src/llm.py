import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from loguru import logger
from openai import AsyncOpenAI, OpenAIError

from .config import Config, ModelConfig


class LLM(ABC):
    """Abstract Base Class for all LLM implementations."""

    @abstractmethod
    async def generate(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """Generate a response from the LLM based on a prompt."""
        pass

    @abstractmethod
    async def summarize(self, text: str, context: Optional[str] = None) -> str:
        """Summarize a piece of text."""
        pass


class OpenAICompatibleLLM(LLM):
    """LLM implementation for OpenAI-compatible APIs (LM Studio, Ollama)."""

    def __init__(self, model_config: ModelConfig, base_url: Optional[str] = None):
        self.model_config = model_config
        self.client = AsyncOpenAI(base_url=base_url)
        logger.info(f"Initialized OpenAI-compatible LLM with model: {model_config.name}")
        if base_url:
            logger.info(f"Using custom base URL: {base_url}")

    async def generate(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """Generate a response using the OpenAI completions endpoint."""
        if system_prompt is None:
            system_prompt = "You are a helpful research assistant."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        try:
            response = await self.client.chat.completions.create(
                model=self.model_config.name,
                messages=messages,
                temperature=self.model_config.temperature,
                max_tokens=self.model_config.max_tokens,
                top_p=self.model_config.top_p,
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("LLM returned an empty response.")
            return content.strip()
        except OpenAIError as e:
            logger.error(f"An error occurred with the LLM API: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during LLM generation: {e}")
            raise

    async def summarize(self, text: str, context: Optional[str] = None) -> str:
        """Summarize text using a predefined system prompt."""
        system_prompt = (
            "Please summarize the following text concisely. Focus on the key findings, data, and conclusions. "
            "Extract the most critical information that would be useful for a research report."
        )
        if context:
            system_prompt += f"\n\nThe summary should be relevant to the following topic: {context}"

        return await self.generate(prompt=text, system_prompt=system_prompt)


class LLMFactory:
    """Factory to create LLM instances based on configuration."""

    @staticmethod
    def create_llm(config: Config) -> LLM:
        """Create and return an LLM instance."""
        if config.use_lmstudio:
            logger.info("Creating LLM client for LM Studio...")
            # LM Studio uses a default local server URL
            base_url = config.openai_base_url or "http://localhost:1234/v1"
            return OpenAICompatibleLLM(model_config=config.model, base_url=base_url)
        
        # Add logic for other providers like 'mlx-lm' direct here
        # elif config.llm_provider == 'mlx':
        #     return MlxLLM(config.model)
        
        else:
            # Default to Ollama if not LM Studio, assuming it's running remotely or locally
            logger.info("Creating LLM client for Ollama or other OpenAI-compatible API...")
            return OpenAICompatibleLLM(
                model_config=config.model, base_url=config.openai_base_url
            )
