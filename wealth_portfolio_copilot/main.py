"""
Wealth & Portfolio Conversational Co-Pilot

A multi-turn financial assistant for retail banking or wealth management clients,
deployed as a Telegram bot.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import setup_logging
from config.settings import settings

# Set up logging
logger = setup_logging(
    log_level=settings.LOG_LEVEL,
    log_file=settings.LOG_FILE
)


def main():
    """Main entry point for the Wealth & Portfolio Co-Pilot."""
    logger.info("Starting Wealth & Portfolio Co-Pilot...")
    
    # Import and run the bot
    from bot.telegram_bot import main as bot_main
    
    try:
        bot_main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
