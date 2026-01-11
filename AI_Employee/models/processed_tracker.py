"""
Processed item tracker for duplicate prevention.

Tracks processed item IDs in a JSON file to prevent creating
duplicate action items for the same source.

Silver tier adds cross-source duplicate detection using content hashes
to detect when the same event is reported from multiple sources.
"""

import hashlib
import json
from pathlib import Path
from typing import Literal


SourceType = Literal['gmail', 'file', 'whatsapp', 'linkedin']


class ProcessedTracker:
    """
    Tracks processed item IDs to prevent duplicate processing.

    Stores processed IDs in a JSON file with separate sets for
    each source type (gmail, file, whatsapp, linkedin).

    Silver tier features:
    - Cross-source duplicate detection using content hashes
    - Content hash to action file mapping for adding notes

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
            'file': set(),
            'whatsapp': set(),
            'linkedin': set()
        }
        # Cross-source duplicate tracking: content_hash -> (source, item_id, action_file_path)
        self._content_hashes: dict[str, dict[str, str]] = {}
        self._load()

    def _load(self) -> None:
        """Load processed IDs from the JSON file."""
        if self.tracker_path.exists():
            try:
                with open(self.tracker_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._processed = {
                        'gmail': set(data.get('gmail', [])),
                        'file': set(data.get('file', [])),
                        'whatsapp': set(data.get('whatsapp', [])),
                        'linkedin': set(data.get('linkedin', []))
                    }
                    # Load content hashes for cross-source duplicate detection
                    self._content_hashes = data.get('content_hashes', {})
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: Could not load processed IDs: {e}")
                # Start fresh if file is corrupted
                self._processed = {
                    'gmail': set(),
                    'file': set(),
                    'whatsapp': set(),
                    'linkedin': set()
                }
                self._content_hashes = {}

    def _save(self) -> None:
        """Save processed IDs to the JSON file."""
        try:
            # Ensure parent directory exists
            self.tracker_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'gmail': sorted(self._processed['gmail']),
                'file': sorted(self._processed['file']),
                'whatsapp': sorted(self._processed['whatsapp']),
                'linkedin': sorted(self._processed['linkedin']),
                'content_hashes': self._content_hashes
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
            self._processed = {
                'gmail': set(),
                'file': set(),
                'whatsapp': set(),
                'linkedin': set()
            }
            self._content_hashes = {}
        self._save()

    def compute_content_hash(self, content: str) -> str:
        """
        Compute a hash for content to detect cross-source duplicates.

        Uses SHA-256 truncated to 16 chars for compact storage while
        maintaining sufficient uniqueness for duplicate detection.

        Args:
            content: The content string to hash (e.g., email body, message text).

        Returns:
            A 16-character hex hash string.
        """
        # Normalize content: lowercase, strip whitespace, remove extra spaces
        normalized = ' '.join(content.lower().split())
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]

    def is_duplicate_content(self, content_hash: str) -> tuple[bool, str | None]:
        """
        Check if content has already been processed from another source.

        Args:
            content_hash: The hash to check for duplicates.

        Returns:
            Tuple of (is_duplicate, action_file_path or None).
        """
        if content_hash in self._content_hashes:
            info = self._content_hashes[content_hash]
            return True, info.get('action_file')
        return False, None

    def register_content_hash(
        self,
        content_hash: str,
        source: SourceType,
        item_id: str,
        action_file: str
    ) -> None:
        """
        Register a content hash for cross-source duplicate detection.

        Args:
            content_hash: The hash of the content.
            source: The source type that first processed this content.
            item_id: The unique identifier of the item.
            action_file: Path to the action file created for this content.
        """
        self._content_hashes[content_hash] = {
            'source': source,
            'item_id': item_id,
            'action_file': action_file
        }
        self._save()

    def get_content_hash_info(self, content_hash: str) -> dict[str, str] | None:
        """
        Get information about a content hash if it exists.

        Args:
            content_hash: The hash to look up.

        Returns:
            Dict with source, item_id, action_file or None if not found.
        """
        return self._content_hashes.get(content_hash)

    def __repr__(self) -> str:
        return (
            f"ProcessedTracker("
            f"gmail={len(self._processed['gmail'])}, "
            f"file={len(self._processed['file'])}, "
            f"whatsapp={len(self._processed['whatsapp'])}, "
            f"linkedin={len(self._processed['linkedin'])}, "
            f"content_hashes={len(self._content_hashes)})"
        )
