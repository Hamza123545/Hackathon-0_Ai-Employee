#!/usr/bin/env python3
"""
Entry point for running watchers via PM2.

Accepts watcher type as command-line argument and instantiates
the appropriate watcher class. Compatible with PM2 args parameter.

Usage:
    python run_watcher.py gmail
    python run_watcher.py whatsapp
    python run_watcher.py linkedin
    python run_watcher.py filesystem

PM2 Usage:
    pm2 start ecosystem.config.js --only gmail-watcher
    (PM2 will call: python run_watcher.py gmail)
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import Config
from watchers.filesystem_watcher import FilesystemWatcher
from watchers.gmail_watcher import GmailWatcher
from watchers.linkedin_watcher import LinkedInWatcher
from watchers.whatsapp_watcher import WhatsAppWatcher


def setup_logging(level: str = 'INFO') -> None:
    """
    Configure logging for the watcher.

    Args:
        level: Logging level string (DEBUG, INFO, WARNING, ERROR).
    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main() -> int:
    """
    Main entry point for watcher.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    # Get watcher type from command line argument
    if len(sys.argv) < 2:
        print("Usage: python run_watcher.py <watcher_type>")
        print("Watcher types: gmail, whatsapp, linkedin, filesystem")
        return 1

    watcher_type = sys.argv[1].lower()

    # Load configuration
    config = Config()

    # Setup logging
    setup_logging(config.log_level)
    logger = logging.getLogger(__name__)

    logger.info("=" * 50)
    logger.info(f"Personal AI Employee - {watcher_type.upper()} Watcher")
    logger.info("=" * 50)
    logger.info(f"Vault path: {config.vault_path}")
    logger.info(f"Watcher type: {watcher_type}")
    logger.info(f"Check interval: {config.check_interval}s")

    # Validate configuration
    errors = config.validate()
    if errors:
        for error in errors:
            logger.error(f"Configuration error: {error}")
        return 1

    # Ensure vault structure exists
    config.ensure_vault_structure()
    logger.info(f"Vault structure verified at {config.vault_path}")

    # Create the appropriate watcher
    try:
        if watcher_type == 'filesystem':
            logger.info("Initializing filesystem watcher...")
            logger.info(f"Watch path: {config.watch_path}")
            watcher = FilesystemWatcher(config)

        elif watcher_type == 'gmail':
            logger.info("Initializing Gmail watcher...")
            watcher = GmailWatcher(config)

        elif watcher_type == 'whatsapp':
            logger.info("Initializing WhatsApp watcher...")
            watcher = WhatsAppWatcher(config)

        elif watcher_type == 'linkedin':
            logger.info("Initializing LinkedIn watcher...")
            watcher = LinkedInWatcher(config)

        else:
            logger.error(f"Unknown watcher type: {watcher_type}")
            logger.error("Valid types: gmail, whatsapp, linkedin, filesystem")
            return 1

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Failed to initialize watcher: {e}", exc_info=True)
        return 1

    # Run the watcher
    logger.info("Starting watcher... Press Ctrl+C to stop.")
    try:
        watcher.run()
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.error(f"Watcher error: {e}", exc_info=True)
        return 1

    logger.info(f"{watcher_type} watcher stopped.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
