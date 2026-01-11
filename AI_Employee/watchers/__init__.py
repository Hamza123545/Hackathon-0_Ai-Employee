"""
AI Employee Watchers Package

This package contains watcher implementations for monitoring external sources
and creating action items in the Obsidian vault.

Available watchers:
- FilesystemWatcher: Monitors a folder for new files
- GmailWatcher: Polls Gmail API for new emails
- WhatsAppWatcher: Monitors WhatsApp Web for new messages (Silver tier)
- LinkedInWatcher: Polls LinkedIn API for interactions (Silver tier)
"""

from .base_watcher import BaseWatcher
from .filesystem_watcher import FilesystemWatcher
from .gmail_watcher import GmailWatcher
from .whatsapp_watcher import WhatsAppWatcher
from .linkedin_watcher import LinkedInWatcher

__all__ = [
    'BaseWatcher',
    'FilesystemWatcher',
    'GmailWatcher',
    'WhatsAppWatcher',
    'LinkedInWatcher'
]
