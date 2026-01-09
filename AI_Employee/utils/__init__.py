"""
AI Employee Utilities Package

This package contains utility functions and classes for
configuration, dashboard updates, and other shared functionality.

Available utilities:
- Config: Environment configuration loader
- DashboardUpdater: Updates Dashboard.md with system status
"""

from .config import Config
from .dashboard import DashboardUpdater

__all__ = ['Config', 'DashboardUpdater']
