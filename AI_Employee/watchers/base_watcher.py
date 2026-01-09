"""
Base watcher abstract class for Bronze Tier Personal AI Employee.

Defines the common interface that all watcher implementations must follow.
Uses Template Method pattern for the run loop.
"""

import random
import time
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, TypeVar

from ..utils.config import Config
from ..models.processed_tracker import ProcessedTracker


T = TypeVar('T')


def retry_with_backoff(
    func: Callable[[], T],
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    logger: logging.Logger | None = None
) -> T:
    """
    Execute a function with exponential backoff retry logic.

    Args:
        func: The function to execute.
        max_attempts: Maximum number of retry attempts.
        base_delay: Initial delay in seconds before first retry.
        max_delay: Maximum delay between retries.
        logger: Optional logger for retry messages.

    Returns:
        The return value of the function if successful.

    Raises:
        Exception: The last exception if all retries fail.
    """
    last_exception: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e

            if attempt == max_attempts:
                if logger:
                    logger.error(f"All {max_attempts} attempts failed: {e}")
                raise

            # Calculate delay with exponential backoff and jitter
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            # Add jitter (0-25% of delay)
            jitter = delay * random.uniform(0, 0.25)
            actual_delay = delay + jitter

            if logger:
                logger.warning(
                    f"Attempt {attempt}/{max_attempts} failed: {e}. "
                    f"Retrying in {actual_delay:.1f}s..."
                )

            time.sleep(actual_delay)

    # This should never be reached, but satisfies type checker
    raise last_exception if last_exception else RuntimeError("Unexpected error")


class BaseWatcher(ABC):
    """
    Abstract base class for watchers.

    Watchers monitor external sources (filesystem, Gmail, etc.) and create
    action item files in the Obsidian vault when new items are detected.

    Subclasses must implement:
    - check_for_updates(): Poll the external source for new items
    - create_action_file(item): Create a Markdown file in /Needs_Action/

    Attributes:
        config: Configuration object with vault paths and settings
        tracker: ProcessedTracker for duplicate prevention
        logger: Logger instance for this watcher
        running: Flag to control the main loop
    """

    def __init__(self, config: Config):
        """
        Initialize the base watcher.

        Args:
            config: Configuration object with vault paths and settings
        """
        self.config = config
        self.tracker = ProcessedTracker(config.processed_ids_path)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.running = False

        # Ensure vault structure exists
        self.config.ensure_vault_structure()

        self.logger.info(f"Initialized {self.__class__.__name__}")
        self.logger.info(f"Vault path: {self.config.vault_path}")
        self.logger.info(f"Check interval: {self.config.check_interval}s")

    @abstractmethod
    def check_for_updates(self) -> list[Any]:
        """
        Poll the external source for new items.

        Must be implemented by subclasses to check their specific source
        (filesystem, Gmail, etc.) and return a list of new items.

        Returns:
            List of new items to process. Each item should contain enough
            information to create an action file.
        """
        pass

    @abstractmethod
    def create_action_file(self, item: Any) -> Path | None:
        """
        Create an action item file in /Needs_Action/.

        Must be implemented by subclasses to write a properly formatted
        Markdown file with YAML frontmatter.

        Args:
            item: The item to create an action file for

        Returns:
            Path to the created file, or None if creation failed
            or was skipped (e.g., in dry-run mode)
        """
        pass

    def update_dashboard(self) -> None:
        """
        Update Dashboard.md with current watcher status and all sections.

        This is called after each check cycle to update the dashboard
        with watcher status, pending count, recent activity, and quick stats.
        Uses filesystem scan to automatically reflect /Done/ and /Plans/ state.
        """
        # Import here to avoid circular imports
        from ..utils.dashboard import DashboardUpdater

        try:
            updater = DashboardUpdater(self.config)
            # Use comprehensive update that scans filesystem for all sections
            updater.update_all_sections(
                status='running',
                watcher_type=self.config.watcher_type
            )
        except Exception as e:
            self.logger.error(f"Failed to update dashboard: {e}")

    def run(self) -> None:
        """
        Main loop: poll for updates and create action files.

        This method runs indefinitely until stopped. It:
        1. Checks for new items (with retry on transient errors)
        2. Creates action files for each new item
        3. Updates the dashboard
        4. Sleeps for the configured interval
        5. Repeats

        Handles KeyboardInterrupt for graceful shutdown.
        Uses exponential backoff retry for transient errors.
        """
        self.running = True
        self.logger.info(f"Starting {self.__class__.__name__}...")

        try:
            while self.running:
                try:
                    # Check for new items with retry logic
                    items = retry_with_backoff(
                        func=self.check_for_updates,
                        max_attempts=3,
                        base_delay=1.0,
                        max_delay=60.0,
                        logger=self.logger
                    )

                    if items:
                        self.logger.info(f"Found {len(items)} new item(s)")

                        # Create action files for each item
                        for item in items:
                            try:
                                result = self.create_action_file(item)
                                if result:
                                    self.logger.info(f"Created action file: {result.name}")
                            except Exception as e:
                                self.logger.error(f"Failed to create action file: {e}")

                    # Update dashboard
                    self.update_dashboard()

                except Exception as e:
                    self.logger.error(f"Error in check cycle (all retries exhausted): {e}")

                # Sleep until next check
                self.logger.debug(f"Sleeping for {self.config.check_interval}s...")
                time.sleep(self.config.check_interval)

        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        finally:
            self.stop()

    def stop(self) -> None:
        """
        Stop the watcher gracefully.

        Sets the running flag to False and updates the dashboard
        to reflect the stopped state with final activity snapshot.
        """
        self.running = False
        self.logger.info(f"Stopped {self.__class__.__name__}")

        # Update dashboard to show stopped status with final state
        try:
            from ..utils.dashboard import DashboardUpdater
            updater = DashboardUpdater(self.config)
            updater.update_all_sections(
                status='stopped',
                watcher_type=self.config.watcher_type
            )
        except Exception as e:
            self.logger.error(f"Failed to update dashboard on stop: {e}")
