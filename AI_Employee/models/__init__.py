"""
AI Employee Models Package

This package contains data models and utilities for managing
action items and tracking processed items.

Available models:
- ActionItem: Represents a detected item requiring attention
- ProcessedTracker: Tracks processed item IDs to prevent duplicates
"""

from .action_item import ActionItem, create_action_file
from .processed_tracker import ProcessedTracker

__all__ = ['ActionItem', 'create_action_file', 'ProcessedTracker']
