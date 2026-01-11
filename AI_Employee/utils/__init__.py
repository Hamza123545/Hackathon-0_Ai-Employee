"""
AI Employee Utilities Package

This package contains utility functions and classes for
configuration, dashboard updates, and other shared functionality.

Bronze Tier Utilities:
- Config: Environment configuration loader
- DashboardUpdater: Updates Dashboard.md with system status

Silver Tier Utilities:
- CredentialSanitizer: Recursive credential sanitization
- sanitize_credentials: Convenience function for sanitization
- AuditLogger: Structured logging to daily JSON files
- ApprovalHelper: Creates and manages approval requests (HITL workflow)
"""

from .config import Config
from .dashboard import DashboardUpdater
from .sanitizer import CredentialSanitizer, sanitize_credentials
from .audit_logger import AuditLogger
from .approval_helper import ApprovalHelper

__all__ = [
    'Config',
    'DashboardUpdater',
    'CredentialSanitizer',
    'sanitize_credentials',
    'AuditLogger',
    'ApprovalHelper',
]
