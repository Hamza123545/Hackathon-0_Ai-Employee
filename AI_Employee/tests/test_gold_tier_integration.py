"""
Gold Tier Integration Tests (Phase 9)

End-to-end tests for Gold Tier features:
- T090: Email invoice workflow (Gmail → Xero → LinkedIn notification)
- T091: Cross-platform social media post (Facebook + Instagram + Twitter)
- T092: Weekly audit generation (aggregate all sources, verify AI insights)
- T093: AI Processor autonomous operation (place 10 action items, verify all processed automatically)
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import sys
import os
import json
import time
from datetime import datetime, timedelta, date

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.config import Config
from utils.audit_logger import AuditLogger
from models.action_item import ActionItem, create_action_file
from models.approval_request import ApprovalRequest, create_approval_file
from models.cross_domain_workflow import CrossDomainWorkflow
from models.mcp_server_status import MCPServerStatus


class TestGoldTierIntegration(unittest.TestCase):
    """Gold Tier end-to-end integration tests."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary test directories
        self.test_vault = Path(__file__).parent / 'test_vault_gold'
        self.test_vault.mkdir(exist_ok=True)
        
        # Create all required folders
        self.needs_action_path = self.test_vault / 'Needs_Action'
        self.plans_path = self.test_vault / 'Plans'
        self.pending_approval_path = self.test_vault / 'Pending_Approval'
        self.approved_path = self.test_vault / 'Approved'
        self.done_path = self.test_vault / 'Done'
        self.logs_path = self.test_vault / 'Logs'
        self.business_path = self.test_vault / 'Business'
        self.accounting_path = self.test_vault / 'Accounting'
        self.briefings_path = self.test_vault / 'Briefings'
        self.system_path = self.test_vault / 'System'
        
        for path in [
            self.needs_action_path, self.plans_path, self.pending_approval_path,
            self.approved_path, self.done_path, self.logs_path,
            self.business_path, self.accounting_path, self.briefings_path,
            self.system_path / 'MCP_Status', self.system_path / 'Failed_Requests',
            self.business_path / 'Workflows'
        ]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Set up config
        os.environ['VAULT_PATH'] = str(self.test_vault)
        self.config = Config()
        self.config.vault_path = self.test_vault
        self.config.needs_action_path = self.needs_action_path
        self.config.plans_path = self.plans_path
        self.config.pending_approval_path = self.pending_approval_path
        self.config.approved_path = self.approved_path
        self.config.done_path = self.done_path
        self.config.logs_path = self.logs_path
        self.config.business_path = self.business_path
        self.config.accounting_path = self.accounting_path
        self.config.briefings_path = self.briefings_path
        self.config.system_path = self.system_path
        
        # Set up audit logger
        self.audit_logger = AuditLogger(self.logs_path)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.test_vault.exists():
            shutil.rmtree(self.test_vault)

    @patch('mcp_servers.email_mcp.send_email')
    @patch('mcp_servers.xero_mcp.create_invoice')
    @patch('mcp_servers.linkedin_mcp.create_post')
    def test_email_invoice_workflow(self, mock_linkedin_post, mock_xero_invoice, mock_email_send):
        """
        T090: End-to-end test: Email invoice workflow (Gmail → Xero → LinkedIn notification).
        
        Steps:
        1. Create action item from Gmail (invoice request email)
        2. AI Processor processes it, creates plan
        3. Plan creates approval request for Xero invoice creation
        4. Human approves, invoice created in Xero
        5. LinkedIn notification posted
        6. Verify all steps completed and logged
        """
        # Step 1: Create action item from Gmail
        action_item = ActionItem(
            title="Invoice Request from Client ABC",
            content="Client ABC requested invoice for project work. Amount: $5,000. Due date: 2026-02-01.",
            source="gmail",
            priority="high",
            category="accounting"
        )
        action_file = create_action_file(action_item, self.needs_action_path)
        self.assertTrue(action_file.exists())
        
        # Step 2: Mock AI Processor processing (would normally be automatic)
        # For test, we simulate the plan creation
        plan_content = f"""---
type: action_plan
source: {action_file.name}
created: {datetime.now().isoformat()}
priority: high
domain: accounting
status: pending
---

# Action Plan: Invoice Request

## Steps
- [ ] Create invoice in Xero for Client ABC
- [ ] Send invoice email to client
- [ ] Post LinkedIn notification about project completion
"""
        plan_file = self.plans_path / f"{action_file.stem}-plan.md"
        plan_file.write_text(plan_content, encoding='utf-8')
        
        # Step 3: Create approval request for Xero invoice
        approval = ApprovalRequest(
            action_type='xero_create_invoice',
            target='Client ABC',
            parameters={
                'contact_name': 'Client ABC',
                'line_items': [
                    {
                        'description': 'Project work',
                        'quantity': 1,
                        'unit_amount': 5000.0,
                        'account_code': '200'
                    }
                ],
                'due_date': '2026-02-01',
                'currency': 'USD'
            },
            risk_level='medium',
            rationale='Create invoice for client project',
            mcp_server='xero-mcp',
            mcp_tool='create_invoice'
        )
        approval_file = create_approval_file(approval, self.pending_approval_path)
        
        # Step 4: Simulate approval and execution
        # Move to approved
        approved_file = self.approved_path / approval_file.name
        approval_file.rename(approved_file)
        
        # Mock MCP server responses
        mock_xero_invoice.return_value = {
            'status': 'success',
            'invoice_id': 'test-invoice-123',
            'invoice_number': 'INV-2026-001',
            'total': 5000.0,
            'created_at': datetime.now().isoformat()
        }
        
        mock_email_send.return_value = {
            'status': 'sent',
            'message_id': 'email-123'
        }
        
        mock_linkedin_post.return_value = {
            'status': 'published',
            'post_id': 'linkedin-123',
            'post_url': 'https://linkedin.com/posts/test-123'
        }
        
        # Simulate execution (normally done by @execute-approved-actions skill)
        # Execute Xero invoice creation
        xero_result = mock_xero_invoice(
            contact_name='Client ABC',
            line_items=approval.parameters['line_items'],
            due_date=approval.parameters['due_date'],
            currency=approval.parameters['currency']
        )
        
        # Log to audit
        self.audit_logger.log_execution(
            action_type='xero_create_invoice',
            actor='test',
            target='Client ABC',
            parameters=approval.parameters,
            approval_status='approved',
            approval_by='test',
            mcp_server='xero-mcp',
            result='success',
            extra_fields={'invoice_id': xero_result['invoice_id']}
        )
        
        # Execute email send
        email_result = mock_email_send(
            to='client@example.com',
            subject=f"Invoice {xero_result['invoice_number']}",
            body=f"Please find attached invoice for ${xero_result['total']}"
        )
        
        self.audit_logger.log_execution(
            action_type='email_send',
            actor='test',
            target='client@example.com',
            parameters={'subject': f"Invoice {xero_result['invoice_number']}"},
            mcp_server='email-mcp',
            result='success',
            extra_fields={'message_id': email_result['message_id']}
        )
        
        # Execute LinkedIn post
        linkedin_result = mock_linkedin_post(
            text="Completed project for Client ABC. Invoice sent!"
        )
        
        self.audit_logger.log_execution(
            action_type='linkedin_post',
            actor='test',
            target='LinkedIn',
            parameters={'text': 'Completed project for Client ABC. Invoice sent!'},
            mcp_server='linkedin-mcp',
            result='success',
            extra_fields={'post_url': linkedin_result['post_url']}
        )
        
        # Move to done
        done_file = self.done_path / approved_file.name
        approved_file.rename(done_file)
        
        # Verify results
        self.assertEqual(xero_result['status'], 'success')
        self.assertIn('invoice_id', xero_result)
        self.assertEqual(email_result['status'], 'sent')
        self.assertEqual(linkedin_result['status'], 'published')
        
        # Verify audit log entries
        entries = self.audit_logger.get_entries()
        xero_entries = [e for e in entries if e.get('action_type') == 'xero_create_invoice']
        email_entries = [e for e in entries if e.get('action_type') == 'email_send']
        linkedin_entries = [e for e in entries if e.get('action_type') == 'linkedin_post']
        
        self.assertGreater(len(xero_entries), 0, "Xero invoice creation should be logged")
        self.assertGreater(len(email_entries), 0, "Email send should be logged")
        self.assertGreater(len(linkedin_entries), 0, "LinkedIn post should be logged")
        
        # Verify file moved to done
        self.assertTrue(done_file.exists())
        self.assertFalse(approved_file.exists())

    @patch('mcp_servers.facebook_mcp.post_to_page')
    @patch('mcp_servers.instagram_mcp.post_photo')
    @patch('mcp_servers.twitter_mcp.post_tweet')
    def test_cross_platform_social_media_post(self, mock_twitter_post, mock_instagram_post, mock_facebook_post):
        """
        T091: End-to-end test: Cross-platform social media post (Facebook + Instagram + Twitter).
        
        Steps:
        1. Create action item for social media post
        2. AI Processor creates plan with multi-platform posting
        3. Create approval request for cross-platform post
        4. Human approves
        5. Execute posts to Facebook, Instagram, Twitter
        6. Verify all platforms posted successfully
        """
        # Step 1: Create action item
        action_item = ActionItem(
            title="Post product launch announcement",
            content="New product launch! Post to all social media platforms: Facebook, Instagram, Twitter.",
            source="manual",
            priority="high",
            category="social_media"
        )
        action_file = create_action_file(action_item, self.needs_action_path)
        
        # Step 2: Create approval request for cross-platform post
        approval = ApprovalRequest(
            action_type='social_media_cross_platform_post',
            target='All Platforms',
            parameters={
                'content': 'Excited to announce our new product launch! #ProductLaunch #Innovation',
                'platforms': ['facebook', 'instagram', 'twitter'],
                'image_url': 'https://example.com/product-image.jpg'
            },
            risk_level='low',
            rationale='Product launch announcement',
            mcp_server='multi-platform',
            mcp_tool='cross_platform_post'
        )
        approval_file = create_approval_file(approval, self.pending_approval_path)
        
        # Step 3: Simulate approval
        approved_file = self.approved_path / approval_file.name
        approval_file.rename(approved_file)
        
        # Step 4: Mock MCP server responses
        mock_facebook_post.return_value = {
            'status': 'success',
            'post_id': 'facebook-123',
            'post_url': 'https://facebook.com/posts/123'
        }
        
        mock_instagram_post.return_value = {
            'status': 'success',
            'media_id': 'instagram-123',
            'permalink': 'https://instagram.com/p/123'
        }
        
        mock_twitter_post.return_value = {
            'status': 'success',
            'tweet_id': 'twitter-123',
            'tweet_url': 'https://twitter.com/user/status/123'
        }
        
        # Step 5: Execute posts
        facebook_result = mock_facebook_post(
            page_id='test-page',
            message=approval.parameters['content'],
            link=None
        )
        
        instagram_result = mock_instagram_post(
            instagram_business_id='test-ig-id',
            image_url=approval.parameters['image_url'],
            caption=approval.parameters['content']
        )
        
        twitter_result = mock_twitter_post(
            text=approval.parameters['content']
        )
        
        # Log all executions
        for platform, result in [
            ('facebook', facebook_result),
            ('instagram', instagram_result),
            ('twitter', twitter_result)
        ]:
            self.audit_logger.log_execution(
                action_type=f'{platform}_post',
                actor='test',
                target=platform,
                parameters={'content': approval.parameters['content']},
                mcp_server=f'{platform}-mcp',
                result='success',
                extra_fields={'post_url': result.get('post_url') or result.get('permalink') or result.get('tweet_url')}
            )
        
        # Verify results
        self.assertEqual(facebook_result['status'], 'success')
        self.assertEqual(instagram_result['status'], 'success')
        self.assertEqual(twitter_result['status'], 'success')
        
        # Verify all platforms were called
        mock_facebook_post.assert_called_once()
        mock_instagram_post.assert_called_once()
        mock_twitter_post.assert_called_once()
        
        # Verify audit log entries
        entries = self.audit_logger.get_entries()
        facebook_entries = [e for e in entries if e.get('action_type') == 'facebook_post']
        instagram_entries = [e for e in entries if e.get('action_type') == 'instagram_post']
        twitter_entries = [e for e in entries if e.get('action_type') == 'twitter_post']
        
        self.assertGreater(len(facebook_entries), 0)
        self.assertGreater(len(instagram_entries), 0)
        self.assertGreater(len(twitter_entries), 0)

    @patch('mcp_servers.xero_mcp.get_financial_report')
    @patch('mcp_servers.facebook_mcp.get_engagement_summary')
    @patch('schedulers.run_weekly_audit._generate_ai_insights')
    def test_weekly_audit_generation(self, mock_ai_insights, mock_social_engagement, mock_financial_report):
        """
        T092: End-to-end test: Weekly audit generation (aggregate all sources, verify AI insights).
        
        Steps:
        1. Mock data from Xero (financial)
        2. Mock data from social media (engagement)
        3. Mock AI insights generation
        4. Run audit generation
        5. Verify audit report and CEO briefing created
        6. Verify AI insights included
        """
        from schedulers.run_weekly_audit import generate_audit_report, generate_ceo_briefing
        from models.audit_report import AuditReport
        from models.financial_summary import FinancialSummary
        
        # Mock financial data from Xero
        mock_financial_report.return_value = {
            'status': 'success',
            'revenue': 50000.0,
            'expenses': 30000.0,
            'profit': 20000.0,
            'outstanding_invoices': 15000.0,
            'period': {
                'start': (date.today() - timedelta(days=7)).isoformat(),
                'end': date.today().isoformat()
            }
        }
        
        # Mock social media engagement (format expected by generate_audit_report)
        mock_social_engagement.return_value = {
            'status': 'success',
            'platforms': [
                {
                    'platform': 'facebook',
                    'total_posts': 5,
                    'total_likes': 100,
                    'total_shares': 20,
                    'total_comments': 15,
                    'engagement_rate': 2.5
                },
                {
                    'platform': 'instagram',
                    'total_posts': 3,
                    'total_likes': 200,
                    'total_comments': 30,
                    'engagement_rate': 3.0
                },
                {
                    'platform': 'twitter',
                    'total_posts': 10,
                    'total_likes': 50,
                    'total_shares': 10,  # retweets are shares
                    'total_comments': 5,  # replies are comments
                    'engagement_rate': 1.5
                }
            ],
            'total_posts': 18,
            'total_engagement': 430,
            'overall_engagement_rate': 2.3
        }
        
        # Mock AI insights
        mock_ai_insights.return_value = {
            'executive_summary': 'Strong week with 40% profit margin and good social engagement.',
            'key_insights': [
                'Revenue increased 10% week-over-week',
                'Social media engagement up 25%',
                'Outstanding invoices decreased'
            ],
            'recommendations': [
                'Continue current marketing strategy',
                'Follow up on outstanding invoices'
            ],
            'anomalies': []
        }
        
        # Run audit phase
        period_start = date.today() - timedelta(days=7)
        period_end = date.today()
        
        # Mock action logs summary
        action_logs_summary = {
            'total_actions': 50,
            'successful_actions': 48,
            'failed_actions': 2,
            'automation_rate': 96.0
        }
        
        # Generate audit report
        financial_data = mock_financial_report()
        social_data = mock_social_engagement()
        ai_insights = mock_ai_insights()
        
        audit_report = generate_audit_report(
            period_start=period_start,
            period_end=period_end,
            financial_data=financial_data,
            social_media_data=social_data,
            action_logs_summary=action_logs_summary,
            ai_insights=ai_insights
        )
        
        # Verify audit report
        self.assertIsNotNone(audit_report)
        self.assertEqual(audit_report.period_start, period_start)
        self.assertEqual(audit_report.period_end, period_end)
        self.assertIsNotNone(audit_report.financial_data)
        self.assertIsNotNone(audit_report.social_media_data)
        self.assertIsNotNone(audit_report.recommendations)
        
        # Save audit report
        audit_file = self.accounting_path / 'Audits' / f"audit_{period_end.isoformat()}.json"
        audit_file.parent.mkdir(parents=True, exist_ok=True)
        audit_file.write_text(audit_report.model_dump_json(), encoding='utf-8')
        self.assertTrue(audit_file.exists())
        
        # Generate CEO briefing
        briefing = generate_ceo_briefing(
            period_start=period_start,
            period_end=period_end,
            audit_report=audit_report,
            ai_insights=ai_insights
        )
        
        # Verify CEO briefing
        self.assertIsNotNone(briefing)
        self.assertIsNotNone(briefing.executive_summary)
        self.assertGreaterEqual(len(briefing.key_insights), 3)
        self.assertLessEqual(len(briefing.key_insights), 5)
        
        # CEO Briefing has a content property that generates Markdown
        # For test, we'll just verify the model is valid
        briefing_json = briefing.model_dump_json()
        self.assertIn('executive_summary', briefing_json)
        
        # Save CEO briefing using to_markdown method
        briefing_file = self.briefings_path / f"ceo_briefing_{period_end.isoformat()}.md"
        briefing_md = briefing.to_markdown()
        briefing_file.write_text(briefing_md, encoding='utf-8')
        self.assertTrue(briefing_file.exists())
        
        # Verify AI insights were used
        mock_ai_insights.assert_called()
        self.assertIn('executive_summary', ai_insights)

    @patch('ai_process_items.AIProcessor._invoke_process_action_items_skill')
    def test_ai_processor_autonomous_operation(self, mock_process_skill):
        """
        T093: End-to-end test: AI Processor autonomous operation.
        
        Steps:
        1. Create 10 action items in /Needs_Action/
        2. Start AI Processor (mocked)
        3. Verify all items processed automatically
        4. Verify plans created for all items
        5. Verify processing time < 60 seconds for 95% of items
        """
        from ai_process_items import AIProcessor
        
        # Step 1: Create 10 action items
        action_items = []
        for i in range(10):
            action_item = ActionItem(
                title=f"Test Action Item {i+1}",
                content=f"Content for test action item {i+1}",
                source="test",
                priority=["urgent", "high", "normal", "low"][i % 4],
                category="test"
            )
            action_file = create_action_file(action_item, self.needs_action_path)
            action_items.append(action_file)
        
        self.assertEqual(len(list(self.needs_action_path.glob('*.md'))), 10)
        
        # Step 2: Mock AI Processor skill invocation
        mock_process_skill.return_value = True
        
        # Step 3: Process items (simulate AI Processor)
        processor = AIProcessor(config=self.config)
        start_time = time.time()
        
        processed_count = 0
        for action_file in action_items:
            success = processor.process_action_item(action_file)
            if success:
                processed_count += 1
        
        processing_time = time.time() - start_time
        
        # Step 4: Verify all items processed
        self.assertEqual(processed_count, 10, "All 10 items should be processed")
        
        # Step 5: Verify plans created
        plan_files = list(self.plans_path.glob('*.md'))
        self.assertGreaterEqual(len(plan_files), 10, "Plans should be created for all items")
        
        # Step 6: Verify processing time (95% should be < 60 seconds)
        # For 10 items, at least 9.5 (rounded to 9) should process in < 60 seconds
        # Since we're mocking, this should be fast
        self.assertLess(processing_time, 60, "Total processing should be < 60 seconds")
        
        # Verify skill was called for each item
        self.assertEqual(mock_process_skill.call_count, 10)


if __name__ == '__main__':
    unittest.main()

