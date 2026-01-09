"""
Processed item tracker for duplicate prevention.

Tracks processed item IDs in a JSON file to prevent creating
duplicate action items for the same source.
"""

import json
from pathlib import Path
from typing import Literal


SourceType = Literal['gmail', 'file']


class ProcessedTracker:
    """
    Tracks processed item IDs to prevent duplicate processing.

    Stores processed IDs in a JSON file with separate sets for
    each source type (gmail, file).

    Attributes:
        tracker_path: Path to the JSON file storing processed IDs
    """

    def __init__(self, tracker_path: Path):
        """
        Initialize the tracker.

        Args:
            tracker_path: Path to the JSON file for storing processed IDs.
                         File will be created if it doesn't exist.
        """
        self.tracker_path = tracker_path
        self._processed: dict[str, set[str]] = {
            'gmail': set(),
            'file': set()
        }
        self._load()

    def _load(self) -> None:
        """Load processed IDs from the JSON file."""
        if self.tracker_path.exists():
            try:
                with open(self.tracker_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._processed = {
                        'gmail': set(data.get('gmail', [])),
                        'file': set(data.get('file', []))
                    }
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: Could not load processed IDs: {e}")
                # Start fresh if file is corrupted
                self._processed = {'gmail': set(), 'file': set()}

    def _save(self) -> None:
        """Save processed IDs to the JSON file."""
        try:
            # Ensure parent directory exists
            self.tracker_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'gmail': sorted(self._processed['gmail']),
                'file': sorted(self._processed['file'])
            }

            with open(self.tracker_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            print(f"Error: Could not save processed IDs: {e}")

    def is_processed(self, item_id: str, source: SourceType) -> bool:
        """
        Check if an item has already been processed.

        Args:
            item_id: Unique identifier for the item (message ID, file hash, etc.)
            source: Source type ('gmail' or 'file')

        Returns:
            True if the item has been processed, False otherwise.
        """
        return item_id in self._processed[source]

    def mark_processed(self, item_id: str, source: SourceType) -> None:
        """
        Mark an item as processed.

        Args:
            item_id: Unique identifier for the item
            source: Source type ('gmail' or 'file')
        """
        self._processed[source].add(item_id)
        self._save()

    def unmark_processed(self, item_id: str, source: SourceType) -> None:
        """
        Remove an item from the processed set (for recovery/testing).

        Args:
            item_id: Unique identifier for the item
            source: Source type ('gmail' or 'file')
        """
        self._processed[source].discard(item_id)
        self._save()

    def get_processed_count(self, source: SourceType) -> int:
        """
        Get the count of processed items for a source.

        Args:
            source: Source type ('gmail' or 'file')

        Returns:
            Number of processed items.
        """
        return len(self._processed[source])

    def clear(self, source: SourceType | None = None) -> None:
        """
        Clear processed IDs.

        Args:
            source: If provided, clear only that source. If None, clear all.
        """
        if source:
            self._processed[source] = set()
        else:
            self._processed = {'gmail': set(), 'file': set()}
        self._save()

    def __repr__(self) -> str:
        return (
            f"ProcessedTracker("
            f"gmail={len(self._processed['gmail'])}, "
            f"file={len(self._processed['file'])})"
        )
