"""
Unit tests for MCP servers (email, LinkedIn, Playwright).

Tests MCP server functionality including success cases, error handling,
and rate limiting.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
import os
import json
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp_servers.email_mcp import EmailMCP
from mcp_servers.linkedin_mcp import LinkedInMCP
from mcp_servers.playwright_mcp import PlaywrightMCP


class TestEmailMCP(unittest.TestCase):
    """Test cases for Email MCP server."""

    def setUp(self):
        """Set up test fixtures."""
        self.email_mcp = EmailMCP()

    @patch('smtplib.SMTP')
    def test_email_mcp_send_email_success(self, mock_smtp_class):
        """Test successful email sending via Email MCP."""
        # Mock SMTP connection
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp
        
        # Set environment variables for test
        os.environ['SMTP_HOST'] = 'smtp.gmail.com'
        os.environ['SMTP_PORT'] = '587'
        os.environ['SMTP_USERNAME'] = 'test@example.com'
        os.environ['SMTP_PASSWORD'] = 'test_password'
        os.environ['FROM_ADDRESS'] = 'test@example.com'
        
        # Call send_email tool
        result = self.email_mcp.send_email(
            to='recipient@example.com',
            subject='Test Subject',
            body='Test body content'
        )
        
        # Verify result
        self.assertEqual(result['status'], 'sent')
        self.assertIn('message_id', result)
        self.assertIsNotNone(result.get('timestamp'))
        
        # Verify SMTP was called
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with('test@example.com', 'test_password')
        mock_smtp.sendmail.assert_called_once()

    @patch('smtplib.SMTP')
    def test_email_mcp_auth_failure(self, mock_smtp_class):
        """Test email MCP handles authentication failure."""
        # Mock SMTP to raise authentication error
        mock_smtp = MagicMock()
        mock_smtp.login.side_effect = Exception('Authentication failed')
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp
        
        os.environ['SMTP_HOST'] = 'smtp.gmail.com'
        os.environ['SMTP_PORT'] = '587'
        os.environ['SMTP_USERNAME'] = 'test@example.com'
        os.environ['SMTP_PASSWORD'] = 'wrong_password'
        os.environ['FROM_ADDRESS'] = 'test@example.com'
        
        # Call send_email tool
        result = self.email_mcp.send_email(
            to='recipient@example.com',
            subject='Test Subject',
            body='Test body'
        )
        
        # Verify error handling
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error_code'], 'SMTP_AUTH_FAILED')
        self.assertIn('error', result)
        self.assertIn('Authentication', result['error'])


class TestLinkedInMCP(unittest.TestCase):
    """Test cases for LinkedIn MCP server."""

    def setUp(self):
        """Set up test fixtures."""
        self.linkedin_mcp = LinkedInMCP()

    @patch('requests.post')
    def test_linkedin_mcp_create_post_success(self, mock_post):
        """Test successful LinkedIn post creation."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': 'urn:li:activity:1234567890',
            'created': {'actor': 'urn:li:person:12345'}
        }
        mock_post.return_value = mock_response
        
        os.environ['LINKEDIN_ACCESS_TOKEN'] = 'test_token'
        os.environ['LINKEDIN_PERSON_URN'] = 'urn:li:person:12345'
        
        # Call create_post tool
        result = self.linkedin_mcp.create_post(
            content='Test LinkedIn post content',
            visibility='PUBLIC'
        )
        
        # Verify result
        self.assertEqual(result['status'], 'published')
        self.assertIn('post_id', result)
        self.assertIn('post_url', result)
        
        # Verify API was called
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn('headers', call_args.kwargs)
        self.assertIn('Authorization', call_args.kwargs['headers'])

    @patch('requests.post')
    def test_linkedin_mcp_rate_limit(self, mock_post):
        """Test LinkedIn MCP handles rate limit errors."""
        # Mock rate limit response
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            'error': 'Rate limit exceeded',
            'message': 'Too many requests'
        }
        mock_post.return_value = mock_response
        
        os.environ['LINKEDIN_ACCESS_TOKEN'] = 'test_token'
        os.environ['LINKEDIN_PERSON_URN'] = 'urn:li:person:12345'
        
        # Call create_post tool
        result = self.linkedin_mcp.create_post(
            content='Test post',
            visibility='PUBLIC'
        )
        
        # Verify error handling
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error_code'], 'RATE_LIMIT_EXCEEDED')
        self.assertIn('error', result)
        self.assertIn('rate limit', result['error'].lower())


class TestPlaywrightMCP(unittest.TestCase):
    """Test cases for Playwright MCP server."""

    def setUp(self):
        """Set up test fixtures."""
        self.playwright_mcp = PlaywrightMCP()

    @patch('playwright.sync_api.sync_playwright')
    def test_playwright_mcp_browser_action_screenshot(self, mock_playwright):
        """Test browser action with screenshot capture."""
        # Mock Playwright browser
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_playwright.return_value.__enter__.return_value = mock_playwright
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.screenshot.return_value = b'fake_screenshot_data'
        
        # Create temp directory for screenshots
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['SCREENSHOT_DIR'] = tmpdir
            
            # Call browser_action tool
            result = self.playwright_mcp.browser_action(
                action='navigate',
                url='https://example.com',
                take_screenshot=True
            )
            
            # Verify result
            self.assertEqual(result['status'], 'success')
            self.assertIn('screenshot_path', result)
            self.assertTrue(Path(result['screenshot_path']).exists())


if __name__ == '__main__':
    unittest.main()

