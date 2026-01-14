#!/usr/bin/env python3
"""
Entry point for running AI Processor via PM2 or directly.

Automatically processes action items from /Needs_Action/ folder
using Claude Code or Anthropic API.

Usage:
    python run_ai_processor.py
    python run_ai_processor.py --method anthropic --interval 30
    python run_ai_processor.py --dry-run

PM2 Usage:
    pm2 start ecosystem.config.js --only ai-processor
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ai_process_items import AIProcessor
from utils.config import Config


def setup_logging(level: str = 'INFO') -> None:
    """
    Configure logging for the AI processor.

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
    Main entry point for AI processor.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='AI Processor for Personal AI Employee'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=None,
        help='Check interval in seconds (default: from env or 60)'
    )
    parser.add_argument(
        '--method',
        type=str,
        choices=['claude-cli', 'anthropic', 'auto', 'simulation'],
        default=None,
        help='Processing method (default: from env or auto)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=None,
        help='Dry run mode (simulate without API calls)'
    )
    args = parser.parse_args()

    # Setup logging
    setup_logging()

    # Load configuration
    config = Config()

    # Setup logging level from config
    setup_logging(config.log_level)

    logger = logging.getLogger(__name__)

    logger.info("=" * 50)
    logger.info("Personal AI Employee - AI Processor")
    logger.info("=" * 50)
    logger.info(f"Vault path: {config.vault_path}")

    # Ensure vault structure exists
    config.ensure_vault_structure(include_silver=True)
    logger.info(f"Vault structure verified at {config.vault_path}")

    # Determine method
    import os
    method = args.method or os.getenv('PROCESS_METHOD', 'auto')

    # Determine interval
    import os
    interval = args.interval or int(os.getenv('PROCESS_INTERVAL', '60'))

    # Determine dry run
    import os
    dry_run = args.dry_run if args.dry_run is not None else (
        os.getenv('DRY_RUN', 'false').lower() in ('true', '1', 'yes')
    )

    # Create processor
    try:
        processor = AIProcessor(config)
    except Exception as e:
        logger.error(f"Failed to initialize processor: {e}", exc_info=True)
        return 1

    # Run the processor
    logger.info("Starting AI processor... Press Ctrl+C to stop.")
    try:
        processor.start()
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
        processor.stop()
    except Exception as e:
        logger.error(f"Processor error: {e}", exc_info=True)
        return 1

    logger.info("AI processor stopped.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
