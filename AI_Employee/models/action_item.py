"""
Action item model for Bronze Tier Personal AI Employee.

Defines the ActionItem dataclass and helper functions for creating
action item files in the Obsidian vault.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal


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


def parse_action_file(file_path: Path) -> ActionItem:
    """
    Parse an action item file and return an ActionItem object.

    Args:
        file_path: Path to the action item markdown file.

    Returns:
        Parsed ActionItem object.

    Raises:
        OSError: If file cannot be read.
        ValueError: If file format is invalid.
    """
    content = file_path.read_text(encoding='utf-8')

    # Extract frontmatter
    frontmatter_match = re.match(
        r'^---\s*\n(.*?)\n---',
        content,
        re.DOTALL
    )
    if not frontmatter_match:
        raise ValueError(f"Invalid action item format: missing frontmatter in {file_path.name}")

    frontmatter_text = frontmatter_match.group(1)
    body_text = content[frontmatter_match.end():].strip()

    # Parse frontmatter (simple YAML-like parsing)
    metadata: dict[str, Any] = {}
    for line in frontmatter_text.split('\n'):
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            
            # Parse special types
            if key == 'created':
                try:
                    metadata[key] = datetime.fromisoformat(value)
                except ValueError:
                    metadata[key] = datetime.now()
            elif key == 'tags':
                # Parse tags array: [tag1, tag2] or ["tag1", "tag2"]
                tags = re.findall(r'"([^"]+)"', value) or re.findall(r"'([^']+)'", value)
                if not tags:
                    # Try without quotes
                    tags = [t.strip() for t in value.strip('[]').split(',') if t.strip()]
                metadata[key] = tags
            else:
                metadata[key] = value

    # Extract body content
    summary = ''
    from_address = ''
    original_date = ''
    content_type = ''
    content = ''
    watcher_type = ''

    # Parse body sections
    if '## Summary' in body_text:
        summary_match = re.search(r'## Summary\s*\n(.*?)(?=\n##|\Z)', body_text, re.DOTALL)
        if summary_match:
            summary = summary_match.group(1).strip()

    if '## Details' in body_text:
        details_match = re.search(r'## Details\s*\n(.*?)(?=\n##|\Z)', body_text, re.DOTALL)
        if details_match:
            details = details_match.group(1)
            from_match = re.search(r'\*\*From\*\*:\s*(.+)', details)
            if from_match:
                from_address = from_match.group(1).strip()
            date_match = re.search(r'\*\*Date\*\*:\s*(.+)', details)
            if date_match:
                original_date = date_match.group(1).strip()
            type_match = re.search(r'\*\*Type\*\*:\s*(.+)', details)
            if type_match:
                content_type = type_match.group(1).strip()

    if '## Content' in body_text:
        content_match = re.search(r'## Content\s*\n(.*?)(?=\n##|\Z)', body_text, re.DOTALL)
        if content_match:
            content = content_match.group(1).strip()

    if '## Metadata' in body_text:
        metadata_section = re.search(r'## Metadata\s*\n(.*?)(?=\n##|\Z)', body_text, re.DOTALL)
        if metadata_section:
            metadata_text = metadata_section.group(1)
            watcher_match = re.search(r'\*\*Detected by\*\*:\s*(.+)', metadata_text)
            if watcher_match:
                watcher_type = watcher_match.group(1).strip()

    # Create ActionItem
    return ActionItem(
        id=metadata.get('id', file_path.stem),
        source=metadata.get('source', 'file'),  # type: ignore
        title=metadata.get('title', file_path.stem),
        created=metadata.get('created', datetime.now()),
        priority=metadata.get('priority', 'unknown'),  # type: ignore
        status=metadata.get('status', 'pending'),  # type: ignore
        tags=metadata.get('tags', []),
        summary=summary,
        from_address=from_address,
        original_date=original_date,
        content_type=content_type,
        content=content,
        watcher_type=watcher_type
    )
