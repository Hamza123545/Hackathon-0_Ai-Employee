#!/usr/bin/env python3
"""
Main entry point for Bronze Tier Personal AI Employee.

Loads configuration, initializes the appropriate watcher based on
WATCHER_TYPE environment variable, and starts the monitoring loop.

Usage:
    python -m AI_Employee.main

Environment Variables:
    VAULT_PATH: Path to the Obsidian vault (default: current directory)
    WATCHER_TYPE: 'filesystem' or 'gmail' (default: filesystem)
    CHECK_INTERVAL: Seconds between checks (default: 60)
    WATCH_PATH: Directory to monitor (for filesystem watcher)
    GMAIL_CREDENTIALS_PATH: Path to Gmail OAuth credentials
    DRY_RUN: If 'true', log actions without writing files
    LOG_LEVEL: Logging level (default: INFO)
"""

import logging
import sys
from pathlib import Path

from .utils.config import Config
from .watchers.filesystem_watcher import FilesystemWatcher
from .watchers.gmail_watcher import GmailWatcher


def setup_logging(level: str) -> None:
    """
    Configure logging for the application.

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
    Main entry point.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    # Load configuration
    config = Config()

    # Setup logging
    setup_logging(config.log_level)
    logger = logging.getLogger(__name__)

    logger.info("=" * 50)
    logger.info("Personal AI Employee - Bronze Tier")
    logger.info("=" * 50)
    logger.info(f"Vault path: {config.vault_path}")
    logger.info(f"Watcher type: {config.watcher_type}")
    logger.info(f"Check interval: {config.check_interval}s")
    if config.dry_run:
        logger.info("DRY RUN MODE - No files will be created")

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
        if config.watcher_type == 'filesystem':
            logger.info(f"Initializing filesystem watcher...")
            logger.info(f"Watch path: {config.watch_path}")
            watcher = FilesystemWatcher(config)

        elif config.watcher_type == 'gmail':
            logger.info(f"Initializing Gmail watcher...")
            watcher = GmailWatcher(config)

        else:
            logger.error(f"Unknown watcher type: {config.watcher_type}")
            return 1

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Failed to initialize watcher: {e}")
        return 1

    # Run the watcher
    logger.info("Starting watcher... Press Ctrl+C to stop.")
    try:
        watcher.run()
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.error(f"Watcher error: {e}")
        return 1

    logger.info("Personal AI Employee stopped.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
