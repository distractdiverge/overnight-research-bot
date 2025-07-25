import asyncio
import signal
import sys
from typing import Optional

from loguru import logger

from .config import Config
from .config import Config
from .llm import LLMFactory, LLM
from .search import SearchEngine


class ResearchBot:
    """Main ResearchBot class that orchestrates the research process."""

    def __init__(self, bot_config: Config):
        """Initialize the ResearchBot with a given configuration."""
        self.config = bot_config
        self.running = False
        self._shutdown_event = asyncio.Event()
        self.search_engine = SearchEngine(
            api_key=self.config.search.api_key,
            max_results=self.config.search.max_results
        )
        self.llm: Optional[LLM] = None

    async def initialize(self) -> None:
        """Initialize the bot components."""
        logger.info("Initializing ResearchBot...")

        # Set up signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._handle_shutdown_signal, sig, None)

        logger.info(f"Research Prompt: {self.config.prompt}")
        logger.info(f"Using {'LM Studio' if self.config.use_lmstudio else 'Ollama'} as LLM backend")

        # Initialize other components here as they are developed
        self.llm = LLMFactory.create_llm(self.config)
        # self.storage = VectorStore(self.config.storage)

        logger.info("ResearchBot initialized")

    async def run(self) -> None:
        """Run the bot's main research loop."""
        if self.running:
            logger.warning("Bot is already running")
            return

        self.running = True
        logger.info("Starting ResearchBot...")

        try:
            await self.initialize()

            # Main research loop
            while self.running and not self._shutdown_event.is_set():
                try:
                    logger.info("Starting research cycle...")

                    # 1. Search for information based on the prompt
                    async with self.search_engine as searcher:
                        search_results = await searcher.search(self.config.prompt)

                    if search_results:
                        logger.info(f"Found {len(search_results)} results for the initial prompt.")
                        for i, result in enumerate(search_results, 1):
                            logger.info(f"  {i}. {result.title} ({result.url})")
                    else:
                        logger.warning("No search results found for the prompt.")

                    # 2. Process and summarize results
                    if self.llm and search_results:
                        logger.info("Summarizing search results...")
                        summaries = []
                        for result in search_results:
                            if result.snippet:
                                try:
                                    summary = await self.llm.summarize(
                                        text=result.snippet,
                                        context=self.config.prompt
                                    )
                                    summaries.append(summary)
                                    logger.info(f"  - Summary for '{result.title}': {summary[:100]}...")
                                except Exception as e:
                                    logger.error(f"Could not summarize '{result.title}': {e}")
                            else:
                                logger.warning(f"Skipping result with no snippet: {result.title}")
                        # await self.storage.store(search_results, summaries)


                    # 3. Generate follow-up questions (to be implemented)
                    # if self.llm:
                    #     questions = await self.llm.generate_questions(self.config.prompt)
                    #     logger.info(f"Generated {len(questions)} follow-up questions.")

                    logger.info("Research cycle complete. The bot will now shut down.")
                    # For now, we run once and exit. The loop can be adjusted for continuous operation.
                    self.running = False

                except Exception as e:
                    logger.error(f"Error in research cycle: {e}", exc_info=True)
                    self.running = False  # Stop on error

        except Exception as e:
            logger.critical(f"Fatal error in main loop: {e}", exc_info=True)
            raise
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Shut down the bot gracefully."""
        if self._shutdown_event.is_set():
            return

        logger.info("Shutting down ResearchBot...")
        self._shutdown_event.set()
        self.running = False

        # Clean up resources
        # if hasattr(self, 'storage'):
        #     await self.storage.close()

        logger.info("ResearchBot shutdown complete")

    def _handle_shutdown_signal(self, signum, frame) -> None:
        """Handle shutdown signals gracefully."""
        logger.info(f"Received shutdown signal {signal.Signals(signum).name}")
        self._shutdown_event.set()


def main() -> int:
    """Main entry point for the ResearchBot application."""
    try:
        # Load configuration
        bot_config = Config.load()
        # Set up logging first
        bot_config.setup_logging()

        # Create and run the bot
        bot = ResearchBot(bot_config)
        asyncio.run(bot.run())
        return 0

    except (FileNotFoundError, ValueError) as e:
        logger.critical(f"Configuration error: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("ResearchBot stopped by user")
        return 0
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
