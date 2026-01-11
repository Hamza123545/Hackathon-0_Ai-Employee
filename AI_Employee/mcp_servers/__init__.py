"""
MCP Servers for Silver Tier Personal AI Employee.

This package contains FastMCP-based servers for external action execution:

- email_mcp: Send emails via SMTP with TLS
- linkedin_mcp: Post to LinkedIn via API v2
- playwright_mcp: Browser automation via Playwright
"""

from .email_mcp import send_email, health_check as email_health_check
from .linkedin_mcp import create_post, health_check as linkedin_health_check
from .playwright_mcp import browser_action, take_screenshot, health_check as playwright_health_check

__all__ = [
    # Email MCP
    'send_email',
    'email_health_check',
    # LinkedIn MCP
    'create_post',
    'linkedin_health_check',
    # Playwright MCP
    'browser_action',
    'take_screenshot',
    'playwright_health_check',
]
