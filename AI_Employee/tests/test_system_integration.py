"""
System integration tests for Silver Tier.

These tests require a running system with PM2, MCP servers, and watchers.
Run these tests manually after system setup.

T088: Multi-watcher detection test
T089: Approval workflow integration test
T090: 24-hour uptime test (manual)
T092: LinkedIn end-to-end test
"""

import unittest
from pathlib import Path
import sys
import os
import time
import subprocess
import json
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.config import Config
from utils.audit_logger import AuditLogger


class TestSystemIntegration(unittest.TestCase):
    """System integration tests (require running system)."""

    @classmethod
    def setUpClass(cls):
        """Set up test class - check if system is running."""
        cls.config = Config()
        cls.vault_path = cls.config.vault_path
        cls.needs_action_path = cls.config.needs_action_path
        cls.pending_approval_path = cls.config.pending_approval_path
        cls.approved_path = cls.config.approved_path
        cls.logs_path = cls.config.logs_path
        
        # Check if PM2 is running
        try:
            result = subprocess.run(
                ['pm2', 'jlist'],
                capture_output=True,
                text=True,
                timeout=5
            )
            cls.pm2_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            cls.pm2_available = False

    def test_multi_watcher_detection(self):
        """
        T088: Test multi-watcher detection.
        
        Prerequisites:
        - All watchers running via PM2
        - Test items available on platforms
        
        Steps:
        1. Trigger test items (email, WhatsApp, LinkedIn)
        2. Wait up to 5 minutes
        3. Verify action files created in /Needs_Action/
        4. Monitor for 1 hour, verify no missed items
        """
        if not self.pm2_available:
            self.skipTest("PM2 not available - system test requires running watchers")
        
        # Check PM2 status
        result = subprocess.run(
            ['pm2', 'jlist'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            self.skipTest("PM2 processes not running")
        
        processes = json.loads(result.stdout)
        watcher_names = [p.get('name', '') for p in processes]
        
        # Verify at least 2 watchers are running
        watcher_count = sum(1 for name in watcher_names if 'watcher' in name)
        self.assertGreaterEqual(
            watcher_count, 2,
            "At least 2 watchers should be running for multi-watcher test"
        )
        
        # Count initial action files
        initial_count = len(list(self.needs_action_path.glob('*.md')))
        
        # Note: Actual test would trigger items and wait
        # This is a framework for manual testing
        print(f"\nInitial action files: {initial_count}")
        print("Trigger test items on platforms and wait up to 5 minutes...")
        print("Then verify new action files appear in /Needs_Action/")

    def test_approval_workflow_integration(self):
        """
        T089: Test approval workflow integration.
        
        Steps:
        1. Create test approval request
        2. Verify it appears in /Pending_Approval/
        3. Manually move to /Approved/
        4. Wait up to 1 minute for execution
        5. Verify audit log entry
        6. Verify file moved to /Done/
        7. Verify related plan updated
        """
        from models.approval_request import ApprovalRequest, create_approval_file
        
        # Create test approval
        approval = ApprovalRequest(
            action_type='email_send',
            target='test@example.com',
            parameters={'subject': 'Integration Test', 'body': 'Test body'},
            risk_level='low',
            rationale='Integration test approval',
            mcp_server='email-mcp',
            mcp_tool='send_email'
        )
        
        # Create approval file
        pending_file = create_approval_file(approval, self.pending_approval_path)
        
        # Verify created
        self.assertTrue(pending_file.exists())
        self.assertEqual(pending_file.parent, self.pending_approval_path)
        
        print(f"\nApproval request created: {pending_file.name}")
        print("Manual step: Move file to /Approved/ folder")
        print("Then wait up to 1 minute for execution...")
        
        # After manual approval, check audit log
        audit_logger = AuditLogger(self.logs_path)
        entries = audit_logger.get_entries()
        
        # Look for execution entry
        execution_entries = [
            e for e in entries
            if e.get('approval_request_id') == approval.id
            and e.get('action_type') == 'email_send'
        ]
        
        if execution_entries:
            print(f"✓ Execution logged: {len(execution_entries)} entry(ies) found")
        else:
            print("⚠ No execution entry found yet (may need to wait or check manually)")

    def test_24_hour_uptime(self):
        """
        T090: Test 24-hour uptime with PM2 auto-restart.
        
        This is a manual long-running test.
        
        Steps:
        1. Start watchers via PM2
        2. Monitor for 24+ hours
        3. Simulate crash (kill -9 process)
        4. Verify PM2 auto-restart within 10 seconds
        5. Check Dashboard uptime "24h+"
        6. Verify no unexpected restarts
        7. Validate uptime >99.5%
        """
        if not self.pm2_available:
            self.skipTest("PM2 not available")
        
        # Get PM2 process list
        result = subprocess.run(
            ['pm2', 'jlist'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            self.skipTest("PM2 processes not running")
        
        processes = json.loads(result.stdout)
        
        # Check restart counts and uptime
        for process in processes:
            if 'watcher' in process.get('name', ''):
                restart_count = process.get('pm2_env', {}).get('restart_time', 0)
                uptime_ms = process.get('monit', {}).get('uptime', 0)
                uptime_hours = uptime_ms / (1000 * 3600)
                
                print(f"\n{process.get('name')}:")
                print(f"  Uptime: {uptime_hours:.2f} hours")
                print(f"  Restart count: {restart_count}")
                
                # For 24-hour test, uptime should be >24 hours
                if uptime_hours >= 24:
                    print(f"  ✓ Uptime >24 hours")
                else:
                    print(f"  ⚠ Uptime <24 hours (test requires 24+ hours)")
        
        print("\nFor full 24-hour test:")
        print("1. Monitor for 24+ hours")
        print("2. Simulate crash: kill -9 <pid>")
        print("3. Verify PM2 restarts within 10 seconds")
        print("4. Check Dashboard shows '24h+' uptime")
        print("5. Calculate uptime percentage (should be >99.5%)")

    def test_linkedin_end_to_end(self):
        """
        T092: Test LinkedIn end-to-end workflow.
        
        Steps:
        1. Configure posting rules in Company_Handbook.md
        2. Trigger content generation
        3. Verify draft in /Pending_Approval/
        4. Approve draft
        5. Verify post appears on LinkedIn within 5 minutes
        6. Check Dashboard shows "Posts this week: 1"
        7. Verify audit log has post_url
        """
        # Check if LinkedIn MCP is configured
        if not os.getenv('LINKEDIN_ACCESS_TOKEN'):
            self.skipTest("LinkedIn not configured")
        
        # Check for pending LinkedIn approvals
        linkedin_approvals = list(
            self.pending_approval_path.glob('*linkedin*.md')
        )
        
        print(f"\nLinkedIn pending approvals: {len(linkedin_approvals)}")
        
        # Check audit log for LinkedIn posts
        audit_logger = AuditLogger(self.logs_path)
        entries = audit_logger.get_entries()
        
        linkedin_posts = [
            e for e in entries
            if e.get('action_type') == 'linkedin_post'
            and e.get('result') == 'success'
        ]
        
        print(f"LinkedIn posts in audit log: {len(linkedin_posts)}")
        
        if linkedin_posts:
            latest_post = linkedin_posts[-1]
            print(f"Latest post: {latest_post.get('timestamp')}")
            print(f"Post URL: {latest_post.get('parameters', {}).get('post_url', 'N/A')}")
        
        print("\nFor full end-to-end test:")
        print("1. Configure posting rules")
        print("2. Trigger content generation")
        print("3. Approve draft")
        print("4. Verify post on LinkedIn")
        print("5. Check Dashboard metrics")


if __name__ == '__main__':
    unittest.main()

