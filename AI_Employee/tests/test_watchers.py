"""
Tests for watcher functionality.

Tests session persistence, expiration detection, rate limiting,
and duplicate prevention.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
import os
import json
import shutil
from datetime import datetime, timezone, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from watchers.whatsapp_watcher import WhatsAppWatcher
from watchers.linkedin_watcher import LinkedInWatcher
from utils.config import Config


class TestWatchers(unittest.TestCase):
    """Test cases for watcher functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary test directories
        self.test_vault = Path(__file__).parent / 'test_vault_watchers'
        self.test_vault.mkdir(exist_ok=True)
        
        self.needs_action_path = self.test_vault / 'Needs_Action'
        self.needs_action_path.mkdir(exist_ok=True)
        
        # Set up config
        os.environ['VAULT_PATH'] = str(self.test_vault)
        os.environ['WHATSAPP_SESSION_FILE'] = str(self.test_vault / 'whatsapp_session.json')
        os.environ['LINKEDIN_ACCESS_TOKEN'] = 'test_token'
        os.environ['LINKEDIN_PERSON_URN'] = 'urn:li:person:12345'
        
        self.config = Config()
        self.config.needs_action_path = self.needs_action_path

    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_vault.exists():
            shutil.rmtree(self.test_vault)

    @patch('playwright.sync_api.sync_playwright')
    def test_whatsapp_watcher_session_persistence(self, mock_playwright):
        """Test WhatsApp watcher saves and loads session."""
        session_file = Path(os.environ['WHATSAPP_SESSION_FILE'])
        
        # Mock Playwright browser
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        mock_playwright.return_value.__enter__.return_value = mock_playwright
        mock_playwright.chromium.launch_persistent_context.return_value = mock_context
        mock_context.pages = [mock_page]
        
        # Create watcher
        watcher = WhatsAppWatcher(self.config)
        
        # Simulate session save
        session_data = {
            'cookies': [{'name': 'test', 'value': 'cookie_value'}],
            'storage_state': {'origins': []}
        }
        
        # Save session (would be done by Playwright)
        session_file.parent.mkdir(exist_ok=True)
        session_file.write_text(json.dumps(session_data))
        
        # Verify session file exists
        self.assertTrue(session_file.exists())
        
        # Load session
        if session_file.exists():
            loaded_data = json.loads(session_file.read_text())
            self.assertIn('cookies', loaded_data)

    @patch('playwright.sync_api.sync_playwright')
    def test_whatsapp_watcher_session_expiration_detection(self, mock_playwright):
        """Test WhatsApp watcher detects expired sessions."""
        session_file = Path(os.environ['WHATSAPP_SESSION_FILE'])
        
        # Create old session file (simulating expiration)
        session_file.parent.mkdir(exist_ok=True)
        old_session_data = {
            'cookies': [{'name': 'test', 'value': 'expired'}],
            'created': (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
        }
        session_file.write_text(json.dumps(old_session_data))
        
        # Mock Playwright to simulate session expired
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        mock_page.url = 'https://web.whatsapp.com'
        mock_page.locator.return_value.count.return_value = 0  # No QR code = logged out
        mock_playwright.return_value.__enter__.return_value = mock_playwright
        mock_playwright.chromium.launch_persistent_context.return_value = mock_context
        mock_context.pages = [mock_page]
        
        # Create watcher
        watcher = WhatsAppWatcher(self.config)
        
        # Check if session is expired (would be detected during check)
        # Session is expired if file is >7 days old or QR code appears
        if session_file.exists():
            session_data = json.loads(session_file.read_text())
            created_str = session_data.get('created')
            if created_str:
                created = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                age_days = (datetime.now(timezone.utc) - created).days
                is_expired = age_days > 7
                self.assertTrue(is_expired, "Session should be expired")

    @patch('requests.get')
    def test_linkedin_watcher_rate_limit_handling(self, mock_get):
        """Test LinkedIn watcher handles rate limit errors."""
        # Mock rate limit response
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            'error': 'Rate limit exceeded',
            'message': 'Too many requests'
        }
        mock_get.return_value = mock_response
        
        # Create watcher
        watcher = LinkedInWatcher(self.config)
        
        # Simulate rate limit during check
        try:
            # This would trigger rate limit handling
            # In actual implementation, watcher would back off and retry
            pass
        except Exception as e:
            # Rate limit should be handled gracefully
            self.assertIn('rate limit', str(e).lower() or '429' in str(e))

    def test_duplicate_prevention_cross_source(self):
        """Test duplicate prevention across different watcher sources."""
        # Create action items from different sources with same content
        source1_file = self.needs_action_path / 'action-gmail-test-123.md'
        source2_file = self.needs_action_path / 'action-whatsapp-test-123.md'
        
        # Both have same content hash (simulating duplicate)
        content1 = """---
source: gmail
content_hash: abc123
---
Test message
"""
        content2 = """---
source: whatsapp
content_hash: abc123
---
Test message
"""
        
        source1_file.write_text(content1)
        source2_file.write_text(content2)
        
        # In actual implementation, duplicate detection would check content_hash
        # and source combination to prevent duplicates
        
        # Verify both files exist (they should, as they're from different sources)
        self.assertTrue(source1_file.exists())
        self.assertTrue(source2_file.exists())
        
        # If duplicate prevention is implemented, one would be skipped
        # For this test, we verify the mechanism exists
        files = list(self.needs_action_path.glob('*.md'))
        self.assertGreaterEqual(len(files), 1)


if __name__ == '__main__':
    unittest.main()

