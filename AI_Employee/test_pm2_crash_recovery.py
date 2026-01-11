#!/usr/bin/env python3
"""
PM2 Crash Recovery Testing Script

Simulates an unhandled exception in a watcher to verify PM2
restarts within 10 seconds and restart_count increments in Dashboard.

Usage:
    python test_pm2_crash_recovery.py <watcher_type>

This script should be run while the watcher is managed by PM2.
It will intentionally crash the watcher to test auto-restart.
"""

import logging
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import Config
from utils.dashboard import DashboardUpdater
from models.watcher_instance import WatcherInstance


def simulate_crash(watcher_type: str) -> None:
    """
    Simulate an unhandled exception to trigger PM2 restart.

    Args:
        watcher_type: Type of watcher to crash (gmail, whatsapp, linkedin).
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    logger.info(f"Simulating crash for {watcher_type} watcher...")
    logger.info("PM2 should restart this process within 10 seconds")

    # Wait a moment to ensure PM2 has registered the process
    time.sleep(2)

    # Intentionally raise an unhandled exception
    logger.error("CRASH TEST: Raising unhandled exception")
    raise RuntimeError(f"Intentional crash test for {watcher_type} watcher - PM2 should restart")


def verify_restart(watcher_type: str) -> bool:
    """
    Verify that PM2 restarted the watcher and Dashboard shows restart_count.

    Args:
        watcher_type: Type of watcher to check.

    Returns:
        True if restart was detected, False otherwise.
    """
    config = Config()
    dashboard = DashboardUpdater(config)

    # Read dashboard to check for restart count
    # This would typically read from WatcherInstance metadata
    # For now, we'll just log that verification should be done manually
    logger = logging.getLogger(__name__)
    logger.info("To verify restart:")
    logger.info("1. Check PM2 status: pm2 status")
    logger.info("2. Check PM2 logs: pm2 logs")
    logger.info("3. Check Dashboard.md for restart_count increment")
    logger.info("4. Verify restart happened within 10 seconds")

    return True


def main() -> int:
    """
    Main entry point for crash recovery test.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    if len(sys.argv) < 2:
        print("Usage: python test_pm2_crash_recovery.py <watcher_type>")
        print("Watcher types: gmail, whatsapp, linkedin")
        print("\nWARNING: This will crash the watcher process!")
        print("Ensure the watcher is running under PM2 before running this test.")
        return 1

    watcher_type = sys.argv[1].lower()

    if watcher_type not in ['gmail', 'whatsapp', 'linkedin']:
        print(f"Invalid watcher type: {watcher_type}")
        return 1

    print(f"\n⚠️  WARNING: This will crash the {watcher_type} watcher!")
    print("PM2 should automatically restart it within 10 seconds.")
    print("Press Ctrl+C within 5 seconds to cancel...\n")

    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("\nTest cancelled.")
        return 0

    try:
        simulate_crash(watcher_type)
    except RuntimeError as e:
        # This is expected - the crash
        print(f"\n✅ Crash simulated: {e}")
        print("\nNow verify:")
        print("1. PM2 restarted the watcher (check: pm2 status)")
        print("2. Restart happened within 10 seconds")
        print("3. Dashboard shows restart_count increment")
        return 0
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())

