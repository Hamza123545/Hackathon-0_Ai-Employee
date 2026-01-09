"""
Filesystem watcher for Bronze Tier Personal AI Employee.

Monitors a directory for new files and creates action items
in the Obsidian vault when files are detected.
"""

import hashlib
import logging
import queue
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from ..utils.config import Config
from ..models.action_item import ActionItem, create_action_file
from ..models.processed_tracker import ProcessedTracker
from .base_watcher import BaseWatcher


class FileCreatedHandler(FileSystemEventHandler):
    """
    Event handler that captures file creation events.

    Uses a thread-safe queue to pass detected files to the main watcher.
    """

    def __init__(self, event_queue: queue.Queue, logger: logging.Logger):
        """
        Initialize the event handler.

        Args:
            event_queue: Queue to store detected file paths.
            logger: Logger instance for this handler.
        """
        super().__init__()
        self.event_queue = event_queue
        self.logger = logger

    def on_created(self, event: FileSystemEvent) -> None:
        """
        Handle file creation events.

        Args:
            event: The file system event.
        """
        # Ignore directory creation events
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        self.logger.debug(f"Detected new file: {file_path}")
        self.event_queue.put(file_path)


class FilesystemWatcher(BaseWatcher):
    """
    Watches a directory for new files and creates action items.

    Uses the watchdog library to monitor file system events.
    Implements the BaseWatcher interface for the watcher framework.

    Attributes:
        watch_path: Directory to monitor for new files.
        observer: Watchdog Observer instance.
        event_queue: Thread-safe queue for file events.
    """

    def __init__(self, config: Config):
        """
        Initialize the filesystem watcher.

        Args:
            config: Configuration object with vault paths and watch settings.

        Raises:
            ValueError: If watch_path is not configured or doesn't exist.
        """
        super().__init__(config)

        # Validate watch path
        if not config.watch_path:
            raise ValueError("WATCH_PATH is not configured")

        self.watch_path = config.watch_path

        # Ensure watch path exists
        if not self.watch_path.exists():
            self.logger.info(f"Creating watch directory: {self.watch_path}")
            self.watch_path.mkdir(parents=True, exist_ok=True)

        # Initialize watchdog components
        self.event_queue: queue.Queue[Path] = queue.Queue()
        self.observer: Observer | None = None
        self._observer_lock = threading.Lock()

        self.logger.info(f"Watching directory: {self.watch_path}")

    def _start_observer(self) -> None:
        """Start the watchdog observer in a background thread."""
        with self._observer_lock:
            if self.observer is not None:
                return

            handler = FileCreatedHandler(self.event_queue, self.logger)
            self.observer = Observer()
            self.observer.schedule(handler, str(self.watch_path), recursive=False)
            self.observer.start()
            self.logger.debug("Watchdog observer started")

    def _stop_observer(self) -> None:
        """Stop the watchdog observer."""
        with self._observer_lock:
            if self.observer is not None:
                self.observer.stop()
                self.observer.join(timeout=5)
                self.observer = None
                self.logger.debug("Watchdog observer stopped")

    def check_for_updates(self) -> list[Any]:
        """
        Check for new files in the watched directory.

        Drains the event queue and returns file info for unprocessed files.

        Returns:
            List of file info dicts for new, unprocessed files.
        """
        # Ensure observer is running
        self._start_observer()

        new_files = []

        # Drain the event queue
        while True:
            try:
                file_path = self.event_queue.get_nowait()
            except queue.Empty:
                break

            # Skip if file no longer exists (was temporary)
            if not file_path.exists():
                self.logger.debug(f"File no longer exists: {file_path}")
                continue

            # Skip if file is still being written (size changing)
            if not self._is_file_ready(file_path):
                self.logger.debug(f"File not ready yet: {file_path}")
                # Re-queue for next check
                self.event_queue.put(file_path)
                continue

            # Generate file hash for duplicate detection
            try:
                file_hash = self._compute_file_hash(file_path)
            except OSError as e:
                self.logger.error(f"Cannot read file {file_path}: {e}")
                continue

            # Check if already processed
            if self.tracker.is_processed(file_hash, 'file'):
                self.logger.debug(f"File already processed: {file_path}")
                continue

            # Build file info
            file_info = {
                'path': file_path,
                'hash': file_hash,
                'name': file_path.name,
                'size': file_path.stat().st_size,
                'created': datetime.fromtimestamp(file_path.stat().st_ctime),
                'modified': datetime.fromtimestamp(file_path.stat().st_mtime),
            }

            new_files.append(file_info)
            self.logger.info(f"New file detected: {file_path.name}")

        return new_files

    def create_action_file(self, item: Any) -> Path | None:
        """
        Create an action item file for a detected file.

        Args:
            item: File info dict from check_for_updates().

        Returns:
            Path to the created action file, or None if skipped/failed.
        """
        file_info = item
        file_path: Path = file_info['path']

        # Read file content (first 1000 chars for summary)
        try:
            content = self._read_file_content(file_path)
        except OSError as e:
            self.logger.error(f"Cannot read file content: {e}")
            content = "[Unable to read file content]"

        # Determine content type from extension
        content_type = self._get_content_type(file_path)

        # Create action item
        action_item = ActionItem(
            id=file_info['hash'],
            source='file',
            title=file_info['name'],
            created=datetime.now(),
            priority='medium',  # Default for file watcher
            status='pending',
            tags=[content_type],
            summary=f"New {content_type} detected in watch folder",
            from_address=str(file_path),
            original_date=file_info['modified'].strftime('%Y-%m-%d %H:%M:%S'),
            content_type=content_type,
            content=content,
            watcher_type='filesystem'
        )

        # Write the action file
        result = create_action_file(
            action_item,
            self.config.needs_action_path,
            dry_run=self.config.dry_run
        )

        if result:
            # Mark as processed to prevent duplicates
            self.tracker.mark_processed(file_info['hash'], 'file')
            self.logger.info(f"Created action file: {result.name}")

        return result

    def run(self) -> None:
        """
        Main loop: poll for updates and create action files.

        Overrides BaseWatcher.run() to properly manage the observer lifecycle.
        """
        self.running = True
        self.logger.info(f"Starting {self.__class__.__name__}...")

        try:
            self._start_observer()

            while self.running:
                try:
                    # Check for new items
                    items = self.check_for_updates()

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
                    self.logger.error(f"Error in check cycle: {e}")

                # Sleep until next check
                self.logger.debug(f"Sleeping for {self.config.check_interval}s...")
                time.sleep(self.config.check_interval)

        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the watcher and observer gracefully."""
        self._stop_observer()
        super().stop()

    @staticmethod
    def _compute_file_hash(file_path: Path, chunk_size: int = 8192) -> str:
        """
        Compute SHA-256 hash of a file.

        Args:
            file_path: Path to the file.
            chunk_size: Size of chunks to read.

        Returns:
            Hex-encoded SHA-256 hash.
        """
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def _is_file_ready(file_path: Path, wait_seconds: float = 0.5) -> bool:
        """
        Check if a file is fully written (not still being copied).

        Args:
            file_path: Path to the file.
            wait_seconds: Time to wait before checking size again.

        Returns:
            True if file size is stable, False otherwise.
        """
        try:
            initial_size = file_path.stat().st_size
            time.sleep(wait_seconds)
            final_size = file_path.stat().st_size
            return initial_size == final_size
        except OSError:
            return False

    @staticmethod
    def _read_file_content(file_path: Path, max_chars: int = 2000) -> str:
        """
        Read file content, truncating if necessary.

        Args:
            file_path: Path to the file.
            max_chars: Maximum characters to read.

        Returns:
            File content as string.
        """
        # Try UTF-8 first, then fall back to latin-1
        for encoding in ['utf-8', 'latin-1']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read(max_chars)
                    if len(content) == max_chars:
                        content += "\n\n[Content truncated...]"
                    return content
            except UnicodeDecodeError:
                continue

        return "[Binary file - content not displayed]"

    @staticmethod
    def _get_content_type(file_path: Path) -> str:
        """
        Determine content type from file extension.

        Args:
            file_path: Path to the file.

        Returns:
            Human-readable content type string.
        """
        extension_map = {
            '.txt': 'text document',
            '.md': 'markdown document',
            '.pdf': 'PDF document',
            '.doc': 'Word document',
            '.docx': 'Word document',
            '.xls': 'Excel spreadsheet',
            '.xlsx': 'Excel spreadsheet',
            '.csv': 'CSV file',
            '.json': 'JSON file',
            '.xml': 'XML file',
            '.html': 'HTML file',
            '.py': 'Python script',
            '.js': 'JavaScript file',
            '.png': 'PNG image',
            '.jpg': 'JPEG image',
            '.jpeg': 'JPEG image',
            '.gif': 'GIF image',
        }

        ext = file_path.suffix.lower()
        return extension_map.get(ext, 'file')
