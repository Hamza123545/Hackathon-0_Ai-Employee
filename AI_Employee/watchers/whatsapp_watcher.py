"""
WhatsApp watcher for Silver Tier Personal AI Employee.

Monitors WhatsApp Web for new messages using Playwright browser automation
with session persistence to avoid repeated QR code scans.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from ..utils.config import Config
from ..models.action_item import ActionItem, create_action_file
from .base_watcher import BaseWatcher


class WhatsAppSessionExpiredError(Exception):
    """Raised when WhatsApp Web session has expired and needs re-authentication."""
    pass


class WhatsAppWatcher(BaseWatcher):
    """
    Watches WhatsApp Web for new messages and creates action items.

    Uses Playwright for browser automation with session persistence.
    The session is saved after QR code scan and reused for subsequent runs.

    Attributes:
        session_file: Path to the session storage file.
        browser: Playwright browser instance.
        context: Browser context with session state.
        page: Active page for WhatsApp Web.
        monitored_contacts: List of contact names to monitor (from Company_Handbook).
        headless: Whether to run browser in headless mode.
    """

    WHATSAPP_URL = 'https://web.whatsapp.com'
    QR_CODE_SELECTOR = 'canvas[aria-label="Scan this QR code to link a device!"]'
    CHAT_LIST_SELECTOR = 'div[aria-label="Chat list"]'
    UNREAD_BADGE_SELECTOR = 'span[data-testid="icon-unread-count"]'

    def __init__(self, config: Config, headless: bool = True):
        """
        Initialize the WhatsApp watcher.

        Args:
            config: Configuration object with vault paths and settings.
            headless: Whether to run browser in headless mode (False for QR scan).
        """
        super().__init__(config)

        self.session_file = Path(config.whatsapp_session_file)
        self.headless = headless
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.monitored_contacts: list[str] = []
        self._playwright = None

        # Load monitored contacts from Company_Handbook if available
        self._load_monitored_contacts()

        self.logger.info(f"WhatsApp watcher initialized")
        self.logger.info(f"Session file: {self.session_file}")
        self.logger.info(f"Headless mode: {self.headless}")

    def _load_monitored_contacts(self) -> None:
        """
        Load list of monitored contacts from Company_Handbook.md.

        Looks for a section like:
        ## Monitored WhatsApp Contacts
        - Contact Name 1
        - Contact Name 2
        """
        handbook_path = self.config.handbook_path
        if not handbook_path.exists():
            self.logger.warning(f"Company_Handbook.md not found: {handbook_path}")
            return

        try:
            content = handbook_path.read_text(encoding='utf-8')

            # Look for monitored contacts section
            import re
            pattern = r'##\s*Monitored WhatsApp Contacts\s*\n((?:[-*]\s*.+\n)+)'
            match = re.search(pattern, content, re.IGNORECASE)

            if match:
                contacts_text = match.group(1)
                self.monitored_contacts = [
                    line.strip().lstrip('-*').strip()
                    for line in contacts_text.strip().split('\n')
                    if line.strip()
                ]
                self.logger.info(f"Monitoring {len(self.monitored_contacts)} contacts")
            else:
                self.logger.info("No monitored contacts section found, monitoring all")

        except OSError as e:
            self.logger.error(f"Failed to read Company_Handbook.md: {e}")

    def initialize_session(self, timeout: int = 120000) -> bool:
        """
        Initialize WhatsApp Web session with QR code authentication.

        Opens a visible browser window for the user to scan the QR code.
        After successful login, saves the session for future use.

        Args:
            timeout: Maximum time in ms to wait for QR code scan.

        Returns:
            True if session was successfully initialized.

        Raises:
            TimeoutError: If QR code was not scanned within timeout.
        """
        self.logger.info("Starting WhatsApp session initialization...")
        self.logger.info("A browser window will open. Please scan the QR code.")

        playwright = sync_playwright().start()

        try:
            # Launch visible browser for QR code scan
            browser = playwright.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            # Navigate to WhatsApp Web
            page.goto(self.WHATSAPP_URL)
            self.logger.info("Waiting for QR code scan...")

            # Wait for chat list to appear (indicates successful login)
            page.wait_for_selector(self.CHAT_LIST_SELECTOR, timeout=timeout)
            self.logger.info("Login successful!")

            # Save session state
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            context.storage_state(path=str(self.session_file))
            self.logger.info(f"Session saved to {self.session_file}")

            # Cleanup
            context.close()
            browser.close()
            playwright.stop()

            return True

        except Exception as e:
            self.logger.error(f"Session initialization failed: {e}")
            playwright.stop()
            raise

    def _ensure_browser(self) -> None:
        """
        Ensure browser is running with saved session.

        Raises:
            WhatsAppSessionExpiredError: If session file doesn't exist.
            FileNotFoundError: If session file is missing.
        """
        if self.page is not None:
            return

        if not self.session_file.exists():
            raise FileNotFoundError(
                f"WhatsApp session file not found: {self.session_file}\n"
                "Run 'python -m AI_Employee.watchers.whatsapp_watcher --init' to initialize."
            )

        self.logger.debug("Starting browser with saved session...")

        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(headless=self.headless)
        self.context = self.browser.new_context(
            storage_state=str(self.session_file)
        )
        self.page = self.context.new_page()

        # Navigate to WhatsApp Web
        self.page.goto(self.WHATSAPP_URL)

        # Check for session expiration (QR code appears)
        if self._is_session_expired():
            self._handle_session_expired()
            raise WhatsAppSessionExpiredError(
                "WhatsApp session expired. Please re-scan QR code."
            )

        # Wait for chat list
        self.page.wait_for_selector(self.CHAT_LIST_SELECTOR, timeout=30000)
        self.logger.info("WhatsApp Web loaded successfully")

    def _is_session_expired(self) -> bool:
        """
        Check if the WhatsApp session has expired.

        Returns:
            True if QR code is displayed (session expired).
        """
        try:
            # Short timeout to check for QR code
            qr_element = self.page.query_selector(self.QR_CODE_SELECTOR)
            return qr_element is not None
        except Exception:
            return False

    def _handle_session_expired(self) -> None:
        """
        Handle session expiration by creating a notification.

        Creates an action item in /Needs_Action/ to notify the user
        that WhatsApp session needs re-authentication.
        """
        self.logger.error("WhatsApp session expired - QR code detected")

        # Create notification action item
        notification = ActionItem(
            id=f"whatsapp-session-expired-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            source='whatsapp',
            title='WhatsApp Session Expired - Re-authentication Required',
            created=datetime.now(),
            priority='high',
            status='pending',
            tags=['whatsapp', 'session', 'authentication'],
            summary='WhatsApp Web session has expired. Please re-scan QR code to continue monitoring.',
            from_address='System',
            original_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            content_type='notification',
            content=(
                'The WhatsApp Web session has expired and needs re-authentication.\n\n'
                '## Steps to Fix\n\n'
                '1. Stop the WhatsApp watcher\n'
                '2. Run: `python -m AI_Employee.watchers.whatsapp_watcher --init`\n'
                '3. Scan the QR code with your phone\n'
                '4. Restart the watcher\n'
            ),
            watcher_type='whatsapp'
        )

        create_action_file(
            notification,
            self.config.needs_action_path,
            dry_run=self.config.dry_run
        )

        # Cleanup browser
        self._cleanup_browser()

    def _cleanup_browser(self) -> None:
        """Clean up browser resources."""
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self._playwright:
                self._playwright.stop()
        except Exception as e:
            self.logger.error(f"Error cleaning up browser: {e}")
        finally:
            self.page = None
            self.context = None
            self.browser = None
            self._playwright = None

    def check_for_updates(self) -> list[Any]:
        """
        Poll WhatsApp Web for new messages.

        Scans the chat list for unread messages from monitored contacts.

        Returns:
            List of message info dicts for new, unprocessed messages.
        """
        self._ensure_browser()
        new_messages = []

        try:
            # Get all chat items
            chat_items = self.page.locator(
                f'{self.CHAT_LIST_SELECTOR} div[role="listitem"]'
            ).all()

            for chat in chat_items:
                try:
                    # Check for unread indicator
                    unread_badge = chat.locator(self.UNREAD_BADGE_SELECTOR)
                    if unread_badge.count() == 0:
                        continue

                    # Get contact name
                    contact_name_elem = chat.locator('span[dir="auto"][title]').first
                    contact_name = contact_name_elem.get_attribute('title') or 'Unknown'

                    # Check if contact is monitored (if list specified)
                    if self.monitored_contacts and contact_name not in self.monitored_contacts:
                        continue

                    # Get unread count
                    unread_count_text = unread_badge.text_content() or '1'
                    try:
                        unread_count = int(unread_count_text)
                    except ValueError:
                        unread_count = 1

                    # Get last message preview
                    message_preview_elem = chat.locator('span[dir="ltr"]').last
                    message_preview = message_preview_elem.text_content() or ''

                    # Get timestamp
                    time_elem = chat.locator('div[class*="message-time"]')
                    timestamp = time_elem.text_content() if time_elem.count() > 0 else ''

                    # Generate unique ID for this message batch
                    msg_id = f"whatsapp-{contact_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

                    # Check if already processed
                    if self.tracker.is_processed(msg_id, 'whatsapp'):
                        continue

                    message_info = {
                        'id': msg_id,
                        'contact_name': contact_name,
                        'unread_count': unread_count,
                        'message_preview': message_preview[:200],
                        'timestamp': timestamp,
                        'detected_at': datetime.now()
                    }

                    new_messages.append(message_info)
                    self.logger.info(f"New message from: {contact_name} ({unread_count} unread)")

                except Exception as e:
                    self.logger.debug(f"Error processing chat item: {e}")
                    continue

        except WhatsAppSessionExpiredError:
            raise
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")

            # Check if this is a session issue
            if self._is_session_expired():
                self._handle_session_expired()
                raise WhatsAppSessionExpiredError("Session expired during check")

        return new_messages

    def create_action_file(self, item: Any) -> Path | None:
        """
        Create an action item file for a WhatsApp message.

        Args:
            item: Message info dict from check_for_updates().

        Returns:
            Path to the created action file, or None if skipped/failed.
        """
        message_info = item

        # Create action item
        action_item = ActionItem(
            id=message_info['id'],
            source='whatsapp',
            title=f"WhatsApp: {message_info['contact_name']}",
            created=message_info['detected_at'],
            priority=self._determine_priority(message_info),
            status='pending',
            tags=['whatsapp', 'message'],
            summary=f"{message_info['unread_count']} new message(s) from {message_info['contact_name']}",
            from_address=message_info['contact_name'],
            original_date=message_info['timestamp'] or message_info['detected_at'].strftime('%Y-%m-%d %H:%M'),
            content_type='whatsapp_message',
            content=f"**Message Preview**:\n\n{message_info['message_preview']}\n\n---\n\n*Open WhatsApp to see full conversation*",
            watcher_type='whatsapp'
        )

        # Write the action file
        result = create_action_file(
            action_item,
            self.config.needs_action_path,
            dry_run=self.config.dry_run
        )

        if result:
            # Mark as processed to prevent duplicates
            self.tracker.mark_processed(message_info['id'], 'whatsapp')
            self.logger.info(f"Created action file: {result.name}")

        return result

    @staticmethod
    def _determine_priority(message_info: dict) -> str:
        """
        Determine message priority based on content and count.

        Args:
            message_info: Message info dict.

        Returns:
            Priority level: 'high', 'medium', or 'low'.
        """
        preview_lower = message_info.get('message_preview', '').lower()
        unread_count = message_info.get('unread_count', 1)

        # High priority keywords
        high_keywords = ['urgent', 'asap', 'emergency', 'important', 'help', 'critical']
        for keyword in high_keywords:
            if keyword in preview_lower:
                return 'high'

        # Multiple messages might indicate urgency
        if unread_count >= 5:
            return 'high'
        elif unread_count >= 3:
            return 'medium'

        return 'medium'

    def stop(self) -> None:
        """Stop the watcher and clean up browser resources."""
        self._cleanup_browser()
        super().stop()


def main():
    """CLI entry point for WhatsApp watcher."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='WhatsApp Watcher for Personal AI Employee')
    parser.add_argument('--init', action='store_true', help='Initialize WhatsApp session (scan QR code)')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode (after session init)')
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    config = Config()

    if args.init:
        watcher = WhatsAppWatcher(config, headless=False)
        try:
            watcher.initialize_session()
            print("Session initialized successfully!")
            print(f"Session saved to: {watcher.session_file}")
        except Exception as e:
            print(f"Failed to initialize session: {e}")
            sys.exit(1)
    else:
        watcher = WhatsAppWatcher(config, headless=args.headless)
        try:
            watcher.run()
        except KeyboardInterrupt:
            print("\nShutting down...")
        except WhatsAppSessionExpiredError as e:
            print(f"\n{e}")
            print("Run with --init to re-authenticate")
            sys.exit(1)


if __name__ == '__main__':
    main()
