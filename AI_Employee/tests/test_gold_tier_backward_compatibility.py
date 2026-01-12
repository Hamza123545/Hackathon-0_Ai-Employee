"""
Gold Tier Backward Compatibility Tests (Phase 9)

Tests to verify Bronze and Silver tier functionality still works after Gold tier additions.
"""

import unittest
from unittest.mock import Mock, patch
from pathlib import Path
import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.config import Config
from models.action_item import ActionItem, create_action_file
from models.approval_request import ApprovalRequest, create_approval_file


class TestBackwardCompatibility(unittest.TestCase):
    """Backward compatibility tests for Bronze and Silver tiers."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_vault = Path(__file__).parent / 'test_vault_compat'
        self.test_vault.mkdir(exist_ok=True)
        
        # Create Bronze tier folders
        self.needs_action_path = self.test_vault / 'Needs_Action'
        self.plans_path = self.test_vault / 'Plans'
        self.done_path = self.test_vault / 'Done'
        
        # Create Silver tier folders
        self.pending_approval_path = self.test_vault / 'Pending_Approval'
        self.approved_path = self.test_vault / 'Approved'
        self.rejected_path = self.test_vault / 'Rejected'
        self.logs_path = self.test_vault / 'Logs'
        
        for path in [
            self.needs_action_path, self.plans_path, self.done_path,
            self.pending_approval_path, self.approved_path, self.rejected_path,
            self.logs_path
        ]:
            path.mkdir(parents=True, exist_ok=True)
        
        os.environ['VAULT_PATH'] = str(self.test_vault)
        self.config = Config()
        self.config.vault_path = self.test_vault

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.test_vault.exists():
            shutil.rmtree(self.test_vault)

    def test_bronze_tier_manual_skill_invocation(self):
        """
        T094: Verify Bronze tier compatibility - manual skill invocation still works.
        
        Bronze tier allows manual invocation of @process-action-items skill.
        This should still work after Gold tier additions.
        """
        # Create action item (Bronze tier)
        action_item = ActionItem(
            title="Test Action Item",
            content="Test content for manual processing",
            source="test",
            priority="normal",
            category="test"
        )
        action_file = create_action_file(action_item, self.needs_action_path)
        
        # Verify file created (Bronze tier functionality)
        self.assertTrue(action_file.exists())
        self.assertEqual(action_file.parent, self.needs_action_path)
        
        # Verify action item can be parsed (Bronze tier functionality)
        from models.action_item import parse_action_file
        parsed = parse_action_file(action_file)
        self.assertEqual(parsed.title, "Test Action Item")
        self.assertEqual(parsed.source, "test")
        
        # Bronze tier: Manual skill invocation should still work
        # (In real usage, user would invoke @process-action-items skill manually)
        # For test, we verify the file structure is compatible
        self.assertTrue(action_file.exists())

    def test_silver_tier_mcp_servers_functional(self):
        """
        T095: Verify Silver tier compatibility - existing MCP servers still functional.
        
        Silver tier MCP servers (Gmail, WhatsApp, LinkedIn, Browser) should still work
        after Gold tier additions.
        """
        # Test that Silver tier MCP servers can be imported
        try:
            from mcp_servers.email_mcp import send_email, health_check as email_health
            from mcp_servers.linkedin_mcp import create_post, health_check as linkedin_health
            from mcp_servers.playwright_mcp import browser_action, health_check as playwright_health
            
            # Verify functions exist
            self.assertTrue(callable(send_email))
            self.assertTrue(callable(email_health))
            self.assertTrue(callable(create_post))
            self.assertTrue(callable(linkedin_health))
            self.assertTrue(callable(browser_action))
            self.assertTrue(callable(playwright_health))
            
        except ImportError as e:
            self.fail(f"Silver tier MCP servers should be importable: {e}")

    def test_silver_tier_approval_workflow(self):
        """
        T095: Verify Silver tier approval workflow still works.
        
        Silver tier approval workflow (Pending_Approval → Approved → Done)
        should still function correctly.
        """
        # Create approval request (Silver tier)
        approval = ApprovalRequest(
            action_type='email_send',
            target='test@example.com',
            parameters={'subject': 'Test', 'body': 'Test body'},
            risk_level='low',
            rationale='Backward compatibility test',
            mcp_server='email-mcp',
            mcp_tool='send_email'
        )
        
        # Create approval file in Pending_Approval (Silver tier workflow)
        approval_file = create_approval_file(approval, self.pending_approval_path)
        self.assertTrue(approval_file.exists())
        self.assertEqual(approval_file.parent, self.pending_approval_path)
        
        # Simulate approval (move to Approved)
        approved_file = self.approved_path / approval_file.name
        approval_file.rename(approved_file)
        self.assertTrue(approved_file.exists())
        self.assertFalse(approval_file.exists())
        
        # Simulate execution (move to Done)
        done_file = self.done_path / approved_file.name
        approved_file.rename(done_file)
        self.assertTrue(done_file.exists())
        self.assertFalse(approved_file.exists())

    def test_gold_tier_extends_silver(self):
        """
        Verify Gold tier extends Silver tier without breaking it.
        
        Gold tier adds new features but should not break existing Silver tier functionality.
        """
        # Silver tier: Create approval request
        approval = ApprovalRequest(
            action_type='email_send',
            target='test@example.com',
            parameters={'subject': 'Test', 'body': 'Test body'},
            risk_level='low',
            rationale='Test',
            mcp_server='email-mcp',
            mcp_tool='send_email'
        )
        approval_file = create_approval_file(approval, self.pending_approval_path)
        
        # Gold tier: Add domain classification (should not break Silver tier)
        from utils.classifier import Classifier, default_classifier
        domain = default_classifier.classify(
            title=approval.target,
            content=approval.parameters.get('body', ''),
            source='email'
        )
        
        # Verify both work together
        self.assertTrue(approval_file.exists())
        self.assertIn(domain, ['personal', 'business', 'accounting', 'social_media'])


if __name__ == '__main__':
    unittest.main()

