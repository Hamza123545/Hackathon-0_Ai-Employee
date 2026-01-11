#!/usr/bin/env python3
"""
Entry point for running ApprovalOrchestrator via PM2.

Instantiates ApprovalOrchestrator and starts the monitoring loop
for the /Approved/ folder. Keeps alive with 60-second sleep loop.

Usage:
    python run_orchestrator.py
    python run_orchestrator.py --interval 60 --expiration 24

PM2 Usage:
    pm2 start ecosystem.config.js --only approval-orchestrator
"""

import logging
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import ApprovalOrchestrator
from utils.config import Config


def setup_logging(level: str = 'INFO') -> None:
    """
    Configure logging for the orchestrator.

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
    Main entry point for approval orchestrator.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    # Load configuration
    config = Config()

    # Setup logging
    setup_logging(config.log_level)
    logger = logging.getLogger(__name__)

    logger.info("=" * 50)
    logger.info("Personal AI Employee - Approval Orchestrator")
    logger.info("=" * 50)
    logger.info(f"Vault path: {config.vault_path}")
    logger.info(f"Check interval: {config.approval_check_interval}s")
    logger.info(f"Expiration: 24 hours")

    # Ensure vault structure exists
    config.ensure_vault_structure(include_silver=True)
    logger.info(f"Vault structure verified at {config.vault_path}")

    # Create orchestrator
    try:
        orchestrator = ApprovalOrchestrator(
            config,
            check_interval=config.approval_check_interval,
            expiration_hours=24
        )
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}", exc_info=True)
        return 1

    # Run the orchestrator
    logger.info("Starting approval orchestrator... Press Ctrl+C to stop.")
    try:
        orchestrator.run()
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.error(f"Orchestrator error: {e}", exc_info=True)
        return 1

    logger.info("Approval orchestrator stopped.")
    return 0


if __name__ == '__main__':
    sys.exit(main())

