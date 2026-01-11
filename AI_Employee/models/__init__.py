"""
AI Employee Models Package

This package contains data models and utilities for managing
action items and tracking processed items.

Bronze Tier Models:
- ActionItem: Represents a detected item requiring attention
- ProcessedTracker: Tracks processed item IDs to prevent duplicates

Silver Tier Models:
- ApprovalRequest: External action awaiting human approval
- create_approval_file: Helper to create approval request files
- parse_approval_file: Helper to parse approval request files
- MCPServer: MCP server metadata and status tracking
- WatcherInstance: Watcher process status and metrics
- WatcherConfig: Watcher configuration settings
- WatcherHealth: Watcher health metrics
"""

from .action_item import ActionItem, create_action_file
from .processed_tracker import ProcessedTracker
from .approval_request import (
    ApprovalRequest,
    create_approval_file as create_approval_request_file,
    parse_approval_file,
)
from .mcp_server import MCPServer
from .watcher_instance import WatcherInstance, WatcherConfig, WatcherHealth

__all__ = [
    # Bronze tier
    'ActionItem',
    'create_action_file',
    'ProcessedTracker',
    # Silver tier
    'ApprovalRequest',
    'create_approval_request_file',
    'parse_approval_file',
    'MCPServer',
    'WatcherInstance',
    'WatcherConfig',
    'WatcherHealth',
]
