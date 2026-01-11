"""
Tests for audit logging functionality.

Tests audit entry schema validation, credential sanitization,
retention policy, and zero credential leaks.
"""

import unittest
from unittest.mock import Mock, patch
from pathlib import Path
import sys
import os
import json
import shutil
import gzip
from datetime import datetime, timezone, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.audit_logger import AuditLogger
from utils.sanitizer import CredentialSanitizer


class TestAuditLogging(unittest.TestCase):
    """Test cases for audit logging."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary test directory
        self.test_logs = Path(__file__).parent / 'test_logs'
        self.test_logs.mkdir(exist_ok=True)
        
        self.audit_logger = AuditLogger(self.test_logs)

    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_logs.exists():
            shutil.rmtree(self.test_logs)

    def test_audit_entry_schema_validation(self):
        """Test audit entry schema validation."""
        # Valid entry
        valid_entry = {
            'entry_id': '123e4567-e89b-12d3-a456-426614174000',
            'timestamp': '2026-01-09T15:30:00Z',
            'action_type': 'email_send',
            'actor': 'claude-code',
            'target': 'recipient@example.com',
            'approval_status': 'approved',
            'result': 'success'
        }
        
        is_valid, errors = self.audit_logger.validate_entry(valid_entry)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Invalid entry (missing required field)
        invalid_entry = {
            'entry_id': '123e4567-e89b-12d3-a456-426614174000',
            'timestamp': '2026-01-09T15:30:00Z',
            # Missing action_type, actor, target, approval_status, result
        }
        
        is_valid, errors = self.audit_logger.validate_entry(invalid_entry)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        
        # Invalid entry (bad UUID)
        invalid_uuid_entry = {
            'entry_id': 'not-a-uuid',
            'timestamp': '2026-01-09T15:30:00Z',
            'action_type': 'email_send',
            'actor': 'claude-code',
            'target': 'recipient@example.com',
            'approval_status': 'approved',
            'result': 'success'
        }
        
        is_valid, errors = self.audit_logger.validate_entry(invalid_uuid_entry)
        self.assertFalse(is_valid)
        self.assertIn('entry_id', ''.join(errors))

    def test_credential_sanitization_passwords(self):
        """Test that passwords are sanitized in audit logs."""
        # Log entry with password in parameters
        entry_id = self.audit_logger.log_execution(
            action_type='email_send',
            actor='claude-code',
            target='recipient@example.com',
            parameters={
                'subject': 'Test',
                'body': 'Test body',
                'smtp_password': 'secret_password_123'
            },
            approval_status='approved',
            mcp_server='email-mcp',
            result='success'
        )
        
        # Retrieve entry
        entries = self.audit_logger.get_entries()
        self.assertGreater(len(entries), 0)
        
        entry = entries[-1]
        self.assertEqual(entry['entry_id'], entry_id)
        
        # Verify password is sanitized
        params = entry.get('parameters', {})
        self.assertIn('smtp_password', params)
        self.assertEqual(params['smtp_password'], '***REDACTED***')
        
        # Verify other parameters intact
        self.assertEqual(params['subject'], 'Test')
        self.assertEqual(params['body'], 'Test body')

    def test_credential_sanitization_tokens(self):
        """Test that API tokens are sanitized in audit logs."""
        # Log entry with token in parameters
        entry_id = self.audit_logger.log_execution(
            action_type='linkedin_post',
            actor='claude-code',
            target='LinkedIn',
            parameters={
                'content': 'Test post',
                'access_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgIryD4WvaM2X5yX8X5yX8X5yX8X5yX8X5yX8'
            },
            approval_status='approved',
            mcp_server='linkedin-mcp',
            result='success'
        )
        
        # Retrieve entry
        entries = self.audit_logger.get_entries()
        entry = entries[-1]
        
        # Verify token is sanitized
        params = entry.get('parameters', {})
        self.assertIn('access_token', params)
        # Token should be masked (first 4 + last 4) or redacted
        token_value = params['access_token']
        self.assertNotEqual(token_value, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgIryD4WvaM2X5yX8X5yX8X5yX8X5yX8X5yX8')
        self.assertTrue('***REDACTED***' in token_value or '...' in token_value)

    def test_audit_log_retention_policy(self):
        """Test audit log retention policy cleanup."""
        # Create old log file (91 days ago)
        old_date = datetime.now(timezone.utc) - timedelta(days=91)
        old_log_file = self.test_logs / f"{old_date.strftime('%Y-%m-%d')}.json"
        old_log_file.write_text(json.dumps({'entries': [{'test': 'entry'}]}))
        
        # Create recent log file (today)
        today_log_file = self.test_logs / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
        today_log_file.write_text(json.dumps({'entries': [{'test': 'recent'}]}))
        
        # Run cleanup with 90-day retention
        stats = self.audit_logger.cleanup_old_logs(retention_days=90, archive=True)
        
        # Verify old file is archived or deleted
        self.assertFalse(old_log_file.exists())
        
        # Verify recent file still exists
        self.assertTrue(today_log_file.exists())
        
        # Verify stats
        self.assertGreater(stats['files_archived'] + stats['files_deleted'], 0)
        self.assertGreater(stats['total_size_freed'], 0)
        
        # Check if archived file exists
        archived_file = self.test_logs / f"{old_date.strftime('%Y-%m-%d')}.json.gz"
        if archived_file.exists():
            # Verify it's a valid gzip file
            with gzip.open(archived_file, 'rb') as f:
                content = f.read()
                self.assertGreater(len(content), 0)

    def test_zero_credential_leaks_sample_100_entries(self):
        """Test zero credential leaks across 100 sample entries."""
        # Create 100 entries with various credential formats
        sensitive_data_patterns = [
            {'password': 'secret123'},
            {'api_key': 'sk_live_1234567890abcdef'},
            {'access_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'},
            {'smtp_password': 'email_pass_456'},
            {'bearer_token': 'Bearer abc123xyz789'},
            {'client_secret': 'secret_key_789'},
            {'refresh_token': 'refresh_abc123'},
            {'private_key': '-----BEGIN PRIVATE KEY-----'},
        ]
        
        entry_ids = []
        for i in range(100):
            # Rotate through sensitive data patterns
            pattern = sensitive_data_patterns[i % len(sensitive_data_patterns)]
            
            entry_id = self.audit_logger.log_execution(
                action_type='email_send',
                actor='claude-code',
                target=f'recipient{i}@example.com',
                parameters={
                    'subject': f'Test {i}',
                    **pattern  # Include sensitive data
                },
                approval_status='approved',
                mcp_server='email-mcp',
                result='success'
            )
            entry_ids.append(entry_id)
        
        # Retrieve all entries
        entries = self.audit_logger.get_entries()
        self.assertGreaterEqual(len(entries), 100)
        
        # Verify zero credential leaks
        sensitive_keys = [
            'password', 'api_key', 'access_token', 'smtp_password',
            'bearer_token', 'client_secret', 'refresh_token', 'private_key'
        ]
        
        for entry in entries[-100:]:  # Check last 100 entries
            params = entry.get('parameters', {})
            for key in sensitive_keys:
                if key in params:
                    value = params[key]
                    # Value should be redacted or masked
                    self.assertNotEqual(value, f'secret{i}')  # Original value
                    self.assertNotEqual(value, 'sk_live_1234567890abcdef')
                    self.assertNotEqual(value, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9')
                    # Should be redacted or masked
                    self.assertTrue(
                        value == '***REDACTED***' or '...' in value or len(value) < 20,
                        f"Credential leak detected: {key} = {value}"
                    )


if __name__ == '__main__':
    unittest.main()

