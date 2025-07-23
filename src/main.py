"""
ResearchBot - An autonomous overnight research utility.

This module provides the main entry point for the ResearchBot application.
"""
import asyncio
import signal
import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from .config import config


class ResearchBot:
    """Main ResearchBot class that orchestrates the research process."""

    def __init__(self):
        """Initialize the ResearchBot with default settings."""
        self.running = False
        self._shutdown_event = asyncio.Event()
        
    async def initialize(self) -> None:
        """Initialize the bot components."""
        logger.info("Initializing ResearchBot...")
        
        # Set up signal handlers for graceful shutdown
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._handle_shutdown_signal)
            
        logger.info(f"Research topic: {config.topic}")
        logger.info(f"Using {'LM Studio' if config.use_lmstudio else 'Ollama'} as LLM backend")
        
        # Initialize components here
        # self.search = SearchEngine(config.search)
        # self.llm = LLMClient(config.model, config.use_lmstudio, config.openai_base_url)
        # self.storage = VectorStore(config.storage)
        
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
                    # Main research cycle
                    logger.info("Starting research cycle...")
                    
                    # 1. Search for information
                    # search_results = await self.search.query(config.topic)
                    # 
                    # # 2. Process and summarize results
                    # for result in search_results:
                    #     summary = await self.llm.summarize(result)
                    #     await self.storage.store(result, summary)
                    #     
                    # # 3. Generate follow-up questions
                    # questions = await self.llm.generate_questions(config.topic)
                    # 
                    # logger.info(f"Research cycle complete. Generated {len(questions)} follow-up questions.")
                    
                    # Sleep until next cycle or shutdown
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=300  # 5 minutes between cycles
                    )
                    
                except asyncio.TimeoutError:
                    # Expected - continue to next cycle
                    continue
                except Exception as e:
                    logger.error(f"Error in research cycle: {e}")
                    # Add backoff/delay on error
                    await asyncio.sleep(60)
                    
        except Exception as e:
            logger.critical(f"Fatal error in main loop: {e}")
            raise
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Shut down the bot gracefully."""
        if not self.running:
            return
            
        logger.info("Shutting down ResearchBot...")
        self.running = False
        self._shutdown_event.set()
        
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
        # Set up logging first
        config.setup_logging()
        
        # Create and run the bot
        bot = ResearchBot()
        asyncio.run(bot.run())
        return 0
        
    except KeyboardInterrupt:
        logger.info("ResearchBot stopped by user")
        return 0
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
