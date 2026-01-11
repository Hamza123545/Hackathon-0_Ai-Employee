"""
Action item model for Bronze Tier Personal AI Employee.

Defines the ActionItem dataclass and helper functions for creating
action item files in the Obsidian vault.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal


SourceType = Literal['gmail', 'file', 'whatsapp', 'linkedin']
PriorityType = Literal['high', 'medium', 'low', 'unknown']
StatusType = Literal['pending', 'in_progress', 'completed']


@dataclass
class ActionItem:
    """
    Represents an action item detected by a watcher.

    Attributes:
        id: Unique identifier (Gmail message ID, file hash, etc.)
        source: Origin of the action item ('gmail' or 'file')
        title: Subject line (email) or filename
        created: When the item was detected
        priority: Determined priority level
        status: Current status (always 'pending' in /Needs_Action)
        tags: Optional categorization tags
        summary: Brief description or snippet
        from_address: Sender email or file path
        original_date: Original date of email/file
        content_type: Type of content (email/document/etc.)
        content: Full or summarized content
        watcher_type: Type of watcher that detected this item
    """

    id: str
    source: SourceType
    title: str
    created: datetime = field(default_factory=datetime.now)
    priority: PriorityType = 'unknown'
    status: StatusType = 'pending'
    tags: list[str] = field(default_factory=list)

    # Body fields
    summary: str = ''
    from_address: str = ''
    original_date: str = ''
    content_type: str = ''
    content: str = ''
    watcher_type: str = ''

    def to_frontmatter(self) -> str:
        """
        Generate YAML frontmatter string for the action item.

        Returns:
            YAML frontmatter including opening/closing delimiters.
        """
        tags_str = ', '.join(f'"{tag}"' for tag in self.tags) if self.tags else ''

        return f"""---
id: "{self.id}"
source: {self.source}
title: "{self._escape_yaml_string(self.title)}"
created: {self.created.isoformat()}
priority: {self.priority}
status: {self.status}
tags: [{tags_str}]
---"""

    def to_body(self) -> str:
        """
        Generate Markdown body content for the action item.

        Returns:
            Markdown formatted body content.
        """
        return f"""## Summary

{self.summary}

## Details

**From**: {self.from_address}
**Date**: {self.original_date}
**Type**: {self.content_type}

## Content

{self.content}

## Metadata

- **Detected by**: {self.watcher_type}
- **Watcher run**: {self.created.isoformat()}
"""

    def to_markdown(self) -> str:
        """
        Generate complete Markdown file content.

        Returns:
            Complete Markdown with frontmatter and body.
        """
        return f"{self.to_frontmatter()}\n\n{self.to_body()}"

    def generate_filename(self) -> str:
        """
        Generate the filename for this action item.

        Format: action-{source}-{slug}-{timestamp}.md

        Returns:
            The generated filename.
        """
        slug = self._slugify(self.title)
        timestamp = self.created.strftime('%Y%m%d-%H%M%S')
        return f"action-{self.source}-{slug}-{timestamp}.md"

    @staticmethod
    def _slugify(text: str, max_length: int = 30) -> str:
        """
        Convert text to a URL-friendly slug.

        Args:
            text: The text to slugify.
            max_length: Maximum length of the slug.

        Returns:
            A lowercase, hyphenated slug.
        """
        # Convert to lowercase and replace spaces with hyphens
        slug = text.lower().strip()
        # Remove non-alphanumeric characters except hyphens and spaces
        slug = re.sub(r'[^\w\s-]', '', slug)
        # Replace whitespace with hyphens
        slug = re.sub(r'[\s_]+', '-', slug)
        # Remove consecutive hyphens
        slug = re.sub(r'-+', '-', slug)
        # Trim hyphens from ends
        slug = slug.strip('-')
        # Truncate to max length
        if len(slug) > max_length:
            slug = slug[:max_length].rsplit('-', 1)[0]
        return slug or 'untitled'

    @staticmethod
    def _escape_yaml_string(text: str) -> str:
        """
        Escape special characters for YAML string values.

        Args:
            text: The text to escape.

        Returns:
            Escaped text safe for YAML.
        """
        # Escape backslashes and double quotes
        return text.replace('\\', '\\\\').replace('"', '\\"')


def create_action_file(
    action_item: ActionItem,
    needs_action_path: Path,
    dry_run: bool = False
) -> Path | None:
    """
    Create an action item file in the Needs_Action folder.

    Args:
        action_item: The ActionItem to write.
        needs_action_path: Path to the Needs_Action folder.
        dry_run: If True, log instead of writing.

    Returns:
        Path to the created file, or None if dry_run or failed.
    """
    filename = action_item.generate_filename()
    file_path = needs_action_path / filename

    if dry_run:
        print(f"[DRY RUN] Would create: {file_path}")
        return None

    try:
        # Ensure directory exists
        needs_action_path.mkdir(parents=True, exist_ok=True)

        # Write the file
        content = action_item.to_markdown()
        file_path.write_text(content, encoding='utf-8')
        return file_path

    except OSError as e:
        print(f"Error creating action file: {e}")
        return None
