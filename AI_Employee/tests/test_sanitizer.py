"""
Unit tests for CredentialSanitizer.

Tests credential sanitization to ensure zero credential leaks
in audit logs and approval requests.
"""

import unittest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.sanitizer import CredentialSanitizer


class TestCredentialSanitizer(unittest.TestCase):
    """Test cases for CredentialSanitizer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.sanitizer = CredentialSanitizer()

    def test_sanitize_credentials_removes_passwords(self):
        """Test that passwords are removed from dictionaries."""
        data = {
            'username': 'user@example.com',
            'password': 'secret123',
            'email': 'user@example.com'
        }
        sanitized = self.sanitizer.sanitize(data)
        
        self.assertEqual(sanitized['username'], 'user@example.com')
        self.assertEqual(sanitized['password'], '***REDACTED***')
        self.assertEqual(sanitized['email'], 'user@example.com')

    def test_sanitize_credentials_removes_tokens(self):
        """Test that API tokens are removed."""
        data = {
            'api_key': 'sk_live_1234567890abcdef',
            'access_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9',
            'refresh_token': 'refresh_abc123xyz789'
        }
        sanitized = self.sanitizer.sanitize(data)
        
        self.assertEqual(sanitized['api_key'], '***REDACTED***')
        self.assertEqual(sanitized['access_token'], '***REDACTED***')
        self.assertEqual(sanitized['refresh_token'], '***REDACTED***')

    def test_mask_token_formats_correctly(self):
        """Test that token masking shows first 4 and last 4 characters."""
        # Long token (>8 chars)
        long_token = 'sk_live_1234567890abcdefghijklmnopqrstuvwxyz'
        masked = self.sanitizer._mask_token(long_token)
        self.assertEqual(masked, 'sk_l...wxyz')
        
        # Short token (<=8 chars)
        short_token = 'abc123'
        masked = self.sanitizer._mask_token(short_token)
        self.assertEqual(masked, '***REDACTED***')

    def test_recursive_sanitization(self):
        """Test that sanitization works recursively in nested structures."""
        data = {
            'user': {
                'name': 'John Doe',
                'credentials': {
                    'password': 'secret',
                    'api_key': 'key123'
                }
            },
            'config': {
                'smtp_password': 'email_pass',
                'settings': {
                    'auth_token': 'token123'
                }
            }
        }
        sanitized = self.sanitizer.sanitize(data)
        
        # Top level preserved
        self.assertEqual(sanitized['user']['name'], 'John Doe')
        
        # Nested credentials sanitized
        self.assertEqual(sanitized['user']['credentials']['password'], '***REDACTED***')
        self.assertEqual(sanitized['user']['credentials']['api_key'], '***REDACTED***')
        self.assertEqual(sanitized['config']['smtp_password'], '***REDACTED***')
        self.assertEqual(sanitized['config']['settings']['auth_token'], '***REDACTED***')

    def test_sanitize_list(self):
        """Test that lists are sanitized recursively."""
        data = [
            {'username': 'user1', 'password': 'pass1'},
            {'username': 'user2', 'api_key': 'key2'}
        ]
        sanitized = self.sanitizer.sanitize(data)
        
        self.assertEqual(sanitized[0]['username'], 'user1')
        self.assertEqual(sanitized[0]['password'], '***REDACTED***')
        self.assertEqual(sanitized[1]['username'], 'user2')
        self.assertEqual(sanitized[1]['api_key'], '***REDACTED***')

    def test_no_false_positives(self):
        """Test that non-sensitive data is not sanitized."""
        data = {
            'subject': 'Meeting reminder',
            'body': 'Please attend the meeting at 3pm',
            'recipient': 'client@example.com',
            'timestamp': '2026-01-09T15:30:00Z',
            'status': 'pending',
            'count': 42
        }
        sanitized = self.sanitizer.sanitize(data)
        
        # All fields should remain unchanged
        self.assertEqual(sanitized['subject'], 'Meeting reminder')
        self.assertEqual(sanitized['body'], 'Please attend the meeting at 3pm')
        self.assertEqual(sanitized['recipient'], 'client@example.com')
        self.assertEqual(sanitized['timestamp'], '2026-01-09T15:30:00Z')
        self.assertEqual(sanitized['status'], 'pending')
        self.assertEqual(sanitized['count'], 42)

    def test_token_like_string_detection(self):
        """Test that long alphanumeric strings are detected as tokens."""
        # Long alphanumeric string (looks like token)
        token_like = 'a' * 50  # 50 chars, all alphanumeric
        sanitized = self.sanitizer.sanitize({'token': token_like})
        # Should be masked (first 4 + last 4)
        self.assertTrue('...' in sanitized['token'])
        
        # Short string (not token-like)
        short_string = 'normal_text'
        sanitized = self.sanitizer.sanitize({'text': short_string})
        self.assertEqual(sanitized['text'], 'normal_text')
        
        # Long string with spaces (not token-like)
        long_text = 'This is a long text that is not a token because it has spaces'
        sanitized = self.sanitizer.sanitize({'text': long_text})
        self.assertEqual(sanitized['text'], long_text)

    def test_case_insensitive_key_matching(self):
        """Test that sensitive key detection is case-insensitive."""
        data = {
            'PASSWORD': 'secret',
            'Api_Key': 'key123',
            'SMTP_PASSWORD': 'email_pass',
            'AccessToken': 'token123'
        }
        sanitized = self.sanitizer.sanitize(data)
        
        self.assertEqual(sanitized['PASSWORD'], '***REDACTED***')
        self.assertEqual(sanitized['Api_Key'], '***REDACTED***')
        self.assertEqual(sanitized['SMTP_PASSWORD'], '***REDACTED***')
        self.assertEqual(sanitized['AccessToken'], '***REDACTED***')

    def test_all_sensitive_key_patterns(self):
        """Test that all SENSITIVE_KEYS patterns are detected."""
        data = {
            'password': 'pass1',
            'token': 'token1',
            'api_key': 'key1',
            'secret': 'secret1',
            'credential': 'cred1',
            'auth': 'auth1',
            'bearer': 'bearer1',
            'smtp_password': 'smtp1',
            'access_token': 'access1',
            'refresh_token': 'refresh1',
            'private_key': 'private1',
            'client_secret': 'client1',
            'authorization': 'authz1'
        }
        sanitized = self.sanitizer.sanitize(data)
        
        # All should be redacted
        for key in data.keys():
            self.assertEqual(sanitized[key], '***REDACTED***', f"Key {key} was not sanitized")

    def test_zero_credential_leaks(self):
        """Test comprehensive scenario to ensure zero credential leaks."""
        # Simulate 100 sample entries with various credential formats
        sample_entries = []
        for i in range(100):
            entry = {
                'action_type': 'email_send',
                'parameters': {
                    'to': f'user{i}@example.com',
                    'subject': f'Email {i}',
                    'smtp_password': f'password{i}',
                    'api_key': f'key_{i}_' + 'x' * 30,  # Long token-like string
                    'nested': {
                        'access_token': f'token{i}',
                        'config': {
                            'secret': f'secret{i}'
                        }
                    }
                }
            }
            sample_entries.append(entry)
        
        # Sanitize all entries
        sanitized_entries = [self.sanitizer.sanitize(entry) for entry in sample_entries]
        
        # Verify no credentials leaked
        for i, sanitized in enumerate(sanitized_entries):
            # Check top-level sensitive keys
            self.assertEqual(sanitized['parameters']['smtp_password'], '***REDACTED***',
                           f"Entry {i}: smtp_password leaked")
            self.assertNotEqual(sanitized['parameters']['api_key'], f'key_{i}_' + 'x' * 30,
                              f"Entry {i}: api_key leaked")
            
            # Check nested sensitive keys
            self.assertEqual(sanitized['parameters']['nested']['access_token'], '***REDACTED***',
                           f"Entry {i}: nested access_token leaked")
            self.assertEqual(sanitized['parameters']['nested']['config']['secret'], '***REDACTED***',
                           f"Entry {i}: nested secret leaked")
            
            # Verify non-sensitive data preserved
            self.assertEqual(sanitized['parameters']['to'], f'user{i}@example.com',
                           f"Entry {i}: to field corrupted")
            self.assertEqual(sanitized['parameters']['subject'], f'Email {i}',
                           f"Entry {i}: subject field corrupted")

    def test_empty_and_none_values(self):
        """Test that empty and None values are handled correctly."""
        data = {
            'password': None,
            'api_key': '',
            'token': '   ',
            'normal_field': None
        }
        sanitized = self.sanitizer.sanitize(data)
        
        # None/empty sensitive keys should still be redacted
        self.assertEqual(sanitized['password'], '***REDACTED***')
        self.assertEqual(sanitized['api_key'], '***REDACTED***')
        self.assertEqual(sanitized['token'], '***REDACTED***')
        self.assertIsNone(sanitized['normal_field'])


if __name__ == '__main__':
    unittest.main()

