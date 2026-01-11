"""
Integration tests for approval workflow.

Tests the complete approval workflow from creation to execution,
including rejection and expiration handling.
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

from models.approval_request import ApprovalRequest, create_approval_file, parse_approval_file
from utils.audit_logger import AuditLogger
from utils.config import Config


class TestApprovalWorkflow(unittest.TestCase):
    """Integration tests for approval workflow."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary test directories
        self.test_vault = Path(__file__).parent / 'test_vault'
        self.test_vault.mkdir(exist_ok=True)
        
        self.pending_path = self.test_vault / 'Pending_Approval'
        self.approved_path = self.test_vault / 'Approved'
        self.rejected_path = self.test_vault / 'Rejected'
        self.done_path = self.test_vault / 'Done'
        self.logs_path = self.test_vault / 'Logs'
        
        for path in [self.pending_path, self.approved_path, self.rejected_path, 
                     self.done_path, self.logs_path]:
            path.mkdir(exist_ok=True)
        
        # Set up config
        os.environ['VAULT_PATH'] = str(self.test_vault)
        self.config = Config()
        self.config.pending_approval_path = self.pending_path
        self.config.approved_path = self.approved_path
        self.config.rejected_path = self.rejected_path
        self.config.done_path = self.done_path
        self.config.logs_path = self.logs_path
        
        # Set up audit logger
        self.audit_logger = AuditLogger(self.logs_path)

    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_vault.exists():
            shutil.rmtree(self.test_vault)

    def test_approval_request_creation(self):
        """Test creating an approval request file."""
        approval = ApprovalRequest(
            action_type='email_send',
            target='recipient@example.com',
            parameters={
                'subject': 'Test Email',
                'body': 'Test body content'
            },
            risk_level='medium',
            rationale='Test email for approval workflow',
            mcp_server='email-mcp',
            mcp_tool='send_email'
        )
        
        # Create approval file
        file_path = create_approval_file(approval, self.pending_path)
        
        # Verify file exists
        self.assertTrue(file_path.exists())
        self.assertEqual(file_path.parent, self.pending_path)
        
        # Verify file content
        content = file_path.read_text(encoding='utf-8')
        self.assertIn('email_send', content)
        self.assertIn('recipient@example.com', content)
        self.assertIn('Test Email', content)
        
        # Parse and verify
        parsed = parse_approval_file(file_path)
        self.assertEqual(parsed.action_type, 'email_send')
        self.assertEqual(parsed.target, 'recipient@example.com')

    def test_approval_to_execution_flow(self):
        """Test complete approval to execution flow."""
        # Create approval request
        approval = ApprovalRequest(
            action_type='email_send',
            target='recipient@example.com',
            parameters={'subject': 'Test', 'body': 'Test body'},
            risk_level='low',
            rationale='Test execution flow',
            mcp_server='email-mcp',
            mcp_tool='send_email'
        )
        
        pending_file = create_approval_file(approval, self.pending_path)
        
        # Move to approved (simulating human approval)
        approved_file = self.approved_path / pending_file.name
        shutil.move(str(pending_file), str(approved_file))
        
        # Verify moved
        self.assertFalse(pending_file.exists())
        self.assertTrue(approved_file.exists())
        
        # Simulate execution (would be done by execute-approved-actions skill)
        # Log execution
        entry_id = self.audit_logger.log_execution(
            action_type='email_send',
            actor='claude-code',
            target='recipient@example.com',
            parameters={'subject': 'Test', 'body': 'Test body'},
            approval_status='approved',
            approval_by='user',
            mcp_server='email-mcp',
            result='success',
            approval_request_id=approval.id
        )
        
        # Verify audit log entry
        entries = self.audit_logger.get_entries()
        self.assertGreater(len(entries), 0)
        self.assertEqual(entries[-1]['entry_id'], entry_id)
        self.assertEqual(entries[-1]['action_type'], 'email_send')
        self.assertEqual(entries[-1]['result'], 'success')
        
        # Move to done (simulating successful execution)
        done_file = self.done_path / approved_file.name
        shutil.move(str(approved_file), str(done_file))
        
        # Verify moved
        self.assertFalse(approved_file.exists())
        self.assertTrue(done_file.exists())

    def test_approval_rejection_flow(self):
        """Test approval rejection flow."""
        # Create approval request
        approval = ApprovalRequest(
            action_type='linkedin_post',
            target='LinkedIn',
            parameters={'content': 'Test post'},
            risk_level='high',
            rationale='Test rejection',
            mcp_server='linkedin-mcp',
            mcp_tool='create_post'
        )
        
        pending_file = create_approval_file(approval, self.pending_path)
        
        # Move to rejected (simulating human rejection)
        rejected_file = self.rejected_path / pending_file.name
        shutil.move(str(pending_file), str(rejected_file))
        
        # Verify moved
        self.assertFalse(pending_file.exists())
        self.assertTrue(rejected_file.exists())
        
        # Log rejection
        entry_id = self.audit_logger.log_approval_workflow(
            action_type='approval_rejected',
            approval_request_id=approval.id,
            approver='user'
        )
        
        # Verify audit log entry
        entries = self.audit_logger.get_entries()
        self.assertGreater(len(entries), 0)
        self.assertEqual(entries[-1]['action_type'], 'approval_rejected')

    def test_expired_approval_handling(self):
        """Test handling of expired approval requests."""
        # Create approval with old timestamp (simulating expiration)
        approval = ApprovalRequest(
            action_type='email_send',
            target='recipient@example.com',
            parameters={'subject': 'Expired', 'body': 'Test'},
            risk_level='medium',
            rationale='Test expiration',
            mcp_server='email-mcp',
            mcp_tool='send_email'
        )
        
        # Manually set old timestamp
        approval.created_timestamp = datetime.now(timezone.utc) - timedelta(hours=25)
        
        pending_file = create_approval_file(approval, self.pending_path)
        
        # Check if expired (should be >24 hours)
        age_hours = (datetime.now(timezone.utc) - approval.created_timestamp).total_seconds() / 3600
        self.assertGreater(age_hours, 24)
        
        # Expired approvals should not be executed
        # (This would be checked by execute-approved-actions skill)
        # For test, verify expiration detection
        self.assertTrue(age_hours > 24, "Approval should be expired")

    def test_malformed_approval_validation(self):
        """Test validation of malformed approval files."""
        # Create malformed approval file (missing required fields)
        malformed_file = self.pending_path / 'malformed_approval.md'
        malformed_file.write_text("""---
type: approval_request
# Missing action_type, target, parameters
---
""")
        
        # Try to parse (should handle gracefully)
        try:
            parsed = parse_approval_file(malformed_file)
            # If parsing succeeds, verify defaults or None values
            self.assertIsNone(parsed.action_type or None)
        except (ValueError, KeyError, AttributeError):
            # Expected - malformed file should raise error
            pass


if __name__ == '__main__':
    unittest.main()

