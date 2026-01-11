"""
Playwright MCP server for Silver Tier Personal AI Employee.

FastMCP server providing browser automation capabilities via Playwright,
including navigation, clicks, form filling, and screenshot capture.
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastmcp import FastMCP

# Playwright import with graceful fallback
try:
    from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    sync_playwright = None

# Initialize MCP server
mcp = FastMCP(name="playwright-mcp")

# Error codes per contract
ErrorCode = Literal[
    'SESSION_EXPIRED',
    'WHATSAPP_DISCONNECTED',
    'BROWSER_ERROR',
    'CONTACT_NOT_FOUND',
    'SELECTOR_NOT_FOUND',
    'TIMEOUT',
    'NAVIGATION_ERROR',
    'UNKNOWN'
]

# Action types for browser_action tool
ActionType = Literal['navigate', 'click', 'type', 'fill_form', 'screenshot']


class PlaywrightConfig:
    """Configuration for Playwright loaded from environment variables."""

    @property
    def browser_type(self) -> str:
        return os.environ.get('PLAYWRIGHT_BROWSER', 'chromium')

    @property
    def headless(self) -> bool:
        return os.environ.get('PLAYWRIGHT_HEADLESS', 'true').lower() == 'true'

    @property
    def screenshot_dir(self) -> Path:
        path = os.environ.get(
            'PLAYWRIGHT_SCREENSHOT_DIR',
            os.path.join(os.getcwd(), 'Logs', 'screenshots')
        )
        return Path(path)

    @property
    def timeout_ms(self) -> int:
        return int(os.environ.get('PLAYWRIGHT_TIMEOUT_MS', '30000'))

    @property
    def whatsapp_session_path(self) -> Path:
        path = os.environ.get(
            'WHATSAPP_SESSION_PATH',
            os.path.join(os.getcwd(), 'whatsapp_session.json')
        )
        return Path(path)


config = PlaywrightConfig()


def _ensure_screenshot_dir() -> Path:
    """Ensure screenshot directory exists and return path."""
    config.screenshot_dir.mkdir(parents=True, exist_ok=True)
    return config.screenshot_dir


def _generate_screenshot_path(prefix: str = 'screenshot') -> Path:
    """Generate unique screenshot path with timestamp."""
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    filename = f'{prefix}_{timestamp}.png'
    return _ensure_screenshot_dir() / filename


def _classify_playwright_error(e: Exception) -> tuple[str, ErrorCode]:
    """
    Classify Playwright exception into error message and code.

    Args:
        e: The exception to classify.

    Returns:
        Tuple of (error_message, error_code).
    """
    error_str = str(e).lower()

    if 'timeout' in error_str:
        return str(e), 'TIMEOUT'
    elif 'selector' in error_str or 'locator' in error_str or 'element' in error_str:
        return str(e), 'SELECTOR_NOT_FOUND'
    elif 'navigation' in error_str or 'navigate' in error_str:
        return str(e), 'NAVIGATION_ERROR'
    elif 'browser' in error_str or 'launch' in error_str:
        return str(e), 'BROWSER_ERROR'
    elif 'session' in error_str or 'context' in error_str:
        return str(e), 'SESSION_EXPIRED'
    else:
        return str(e), 'UNKNOWN'


@mcp.tool
def browser_action(
    url: str | None = None,
    action_type: str = 'navigate',
    selector: str | None = None,
    value: str | None = None,
    screenshot: bool = True,
    screenshot_path: str | None = None,
    wait_for_selector: str | None = None,
    form_fields: list[dict[str, str]] | None = None
) -> dict[str, Any]:
    """
    Perform browser automation action using Playwright.

    Args:
        url: URL to navigate to (required for 'navigate' action).
        action_type: Type of action - 'navigate', 'click', 'type', 'fill_form', 'screenshot'.
        selector: CSS selector for click/type actions.
        value: Value to type for 'type' action.
        screenshot: Whether to take screenshot after action.
        screenshot_path: Custom path for screenshot (optional).
        wait_for_selector: Wait for this selector before action.
        form_fields: List of {selector, value, field_type} for 'fill_form' action.

    Returns:
        Dict with status, screenshot_path, timestamp, or error details.
    """
    if not PLAYWRIGHT_AVAILABLE:
        return {
            'status': 'error',
            'error': 'Playwright not installed. Run: pip install playwright && playwright install chromium',
            'error_code': 'BROWSER_ERROR'
        }

    start_time = datetime.now(timezone.utc)
    result: dict[str, Any] = {
        'status': 'error',
        'timestamp': start_time.isoformat()
    }

    try:
        with sync_playwright() as p:
            # Launch browser
            browser_launcher = getattr(p, config.browser_type, p.chromium)
            browser = browser_launcher.launch(headless=config.headless)
            context = browser.new_context()
            page = context.new_page()
            page.set_default_timeout(config.timeout_ms)

            try:
                # Navigate if URL provided
                if url:
                    page.goto(url, wait_until='domcontentloaded')

                # Wait for specific selector if requested
                if wait_for_selector:
                    page.wait_for_selector(wait_for_selector)

                # Perform action based on type
                if action_type == 'navigate':
                    if not url:
                        return {
                            'status': 'error',
                            'error': 'URL required for navigate action',
                            'error_code': 'UNKNOWN'
                        }
                    result['final_url'] = page.url
                    result['status'] = 'success'

                elif action_type == 'click':
                    if not selector:
                        return {
                            'status': 'error',
                            'error': 'Selector required for click action',
                            'error_code': 'SELECTOR_NOT_FOUND'
                        }
                    page.click(selector)
                    result['status'] = 'success'

                elif action_type == 'type':
                    if not selector or value is None:
                        return {
                            'status': 'error',
                            'error': 'Selector and value required for type action',
                            'error_code': 'SELECTOR_NOT_FOUND'
                        }
                    page.fill(selector, value)
                    result['status'] = 'success'

                elif action_type == 'fill_form':
                    if not form_fields:
                        return {
                            'status': 'error',
                            'error': 'form_fields required for fill_form action',
                            'error_code': 'UNKNOWN'
                        }

                    for field in form_fields:
                        field_selector = field.get('selector', '')
                        field_value = field.get('value', '')
                        field_type = field.get('field_type', 'text')

                        if not field_selector:
                            continue

                        if field_type == 'checkbox':
                            if field_value.lower() == 'true':
                                page.check(field_selector)
                            else:
                                page.uncheck(field_selector)
                        elif field_type == 'select':
                            page.select_option(field_selector, field_value)
                        elif field_type == 'radio':
                            page.check(field_selector)
                        else:
                            # text, email, password, etc.
                            page.fill(field_selector, field_value)

                    result['status'] = 'success'

                elif action_type == 'screenshot':
                    result['status'] = 'success'

                else:
                    return {
                        'status': 'error',
                        'error': f'Unknown action_type: {action_type}',
                        'error_code': 'UNKNOWN'
                    }

                # Take screenshot if requested
                if screenshot:
                    if screenshot_path:
                        ss_path = Path(screenshot_path)
                        ss_path.parent.mkdir(parents=True, exist_ok=True)
                    else:
                        ss_path = _generate_screenshot_path(action_type)

                    page.screenshot(path=str(ss_path))
                    result['screenshot_path'] = str(ss_path)

                # Calculate execution duration
                end_time = datetime.now(timezone.utc)
                result['execution_duration_ms'] = int(
                    (end_time - start_time).total_seconds() * 1000
                )

            finally:
                context.close()
                browser.close()

    except Exception as e:
        error_msg, error_code = _classify_playwright_error(e)
        result['status'] = 'error'
        result['error'] = error_msg
        result['error_code'] = error_code

    return result


@mcp.tool
def health_check() -> dict[str, Any]:
    """
    Check if Playwright browser is available.

    Returns:
        Dict with status, browser_available, and checked_at timestamp.
    """
    result = {
        'status': 'error',
        'browser_available': False,
        'whatsapp_session_valid': False,
        'whatsapp_authenticated': False,
        'checked_at': datetime.now(timezone.utc).isoformat()
    }

    if not PLAYWRIGHT_AVAILABLE:
        result['error'] = 'Playwright not installed'
        return result

    try:
        with sync_playwright() as p:
            browser_launcher = getattr(p, config.browser_type, p.chromium)
            browser = browser_launcher.launch(headless=True)
            browser.close()
            result['browser_available'] = True
            result['status'] = 'available'

            # Check WhatsApp session file exists
            if config.whatsapp_session_path.exists():
                result['whatsapp_session_valid'] = True

    except Exception as e:
        result['error'] = str(e)

    return result


@mcp.tool
def take_screenshot(
    url: str,
    output_path: str | None = None,
    full_page: bool = False,
    wait_for_selector: str | None = None
) -> dict[str, Any]:
    """
    Navigate to URL and take a screenshot.

    Args:
        url: URL to capture.
        output_path: Custom path for screenshot (optional).
        full_page: Capture full page scroll (default: False).
        wait_for_selector: Wait for this selector before capturing.

    Returns:
        Dict with status, screenshot_path, or error details.
    """
    if not PLAYWRIGHT_AVAILABLE:
        return {
            'status': 'error',
            'error': 'Playwright not installed',
            'error_code': 'BROWSER_ERROR'
        }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=config.headless)
            context = browser.new_context()
            page = context.new_page()
            page.set_default_timeout(config.timeout_ms)

            try:
                page.goto(url, wait_until='domcontentloaded')

                if wait_for_selector:
                    page.wait_for_selector(wait_for_selector)

                if output_path:
                    ss_path = Path(output_path)
                    ss_path.parent.mkdir(parents=True, exist_ok=True)
                else:
                    ss_path = _generate_screenshot_path('capture')

                page.screenshot(path=str(ss_path), full_page=full_page)

                return {
                    'status': 'success',
                    'screenshot_path': str(ss_path),
                    'url': url,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }

            finally:
                context.close()
                browser.close()

    except Exception as e:
        error_msg, error_code = _classify_playwright_error(e)
        return {
            'status': 'error',
            'error': error_msg,
            'error_code': error_code
        }


if __name__ == '__main__':
    mcp.run(transport='stdio')
