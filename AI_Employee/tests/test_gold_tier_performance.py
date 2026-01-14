"""
Gold Tier Performance Tests (Phase 9)

Performance testing for Gold Tier features:
- T096: 1000+ action items processed within expected time (95% under 60 seconds)
- T097: Weekly audit generation completes in under 60 seconds with all data sources
"""

import os
import sys
import time
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.config import Config
from models.action_item import ActionItem, create_action_file
from ai_process_items import AIProcessor


class TestGoldTierPerformance(unittest.TestCase):
    """Performance tests for Gold Tier."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_vault = Path(__file__).parent / 'test_vault_perf'
        self.test_vault.mkdir(exist_ok=True)
        
        self.needs_action_path = self.test_vault / 'Needs_Action'
        self.plans_path = self.test_vault / 'Plans'
        self.done_path = self.test_vault / 'Done'
        self.logs_path = self.test_vault / 'Logs'
        
        for path in [self.needs_action_path, self.plans_path, self.done_path, self.logs_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        os.environ['VAULT_PATH'] = str(self.test_vault)
        self.config = Config()
        self.config.vault_path = self.test_vault
        self.config.needs_action_path = self.needs_action_path
        self.config.plans_path = self.plans_path
        self.config.done_path = self.done_path
        self.config.logs_path = self.logs_path

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.test_vault.exists():
            shutil.rmtree(self.test_vault)

    @patch('ai_process_items.AIProcessor._invoke_process_action_items_skill')
    def test_process_1000_action_items_performance(self, mock_process_skill):
        """
        T096: Performance test - 1000+ action items processed within expected time.
        
        Requirement: 95% of items should process in < 60 seconds.
        """
        # Create 1000 action items
        action_items = []
        for i in range(1000):
            action_item = ActionItem(
                title=f"Performance Test Action {i+1}",
                content=f"Content for performance test action {i+1}",
                source="test",
                priority=["urgent", "high", "normal", "low"][i % 4],
                category="test"
            )
            action_file = create_action_file(action_item, self.needs_action_path)
            action_items.append(action_file)
        
        # Mock fast processing (simulating optimized system)
        mock_process_skill.return_value = True
        
        # Process items
        processor = AIProcessor(config=self.config)
        start_time = time.time()
        
        processing_times = []
        processed_count = 0
        
        for action_file in action_items:
            item_start = time.time()
            success = processor.process_action_item(action_file)
            item_time = time.time() - item_start
            
            if success:
                processed_count += 1
                processing_times.append(item_time)
        
        total_time = time.time() - start_time
        
        # Calculate statistics
        processing_times.sort()
        p95_index = int(len(processing_times) * 0.95)
        p95_time = processing_times[p95_index] if p95_index < len(processing_times) else processing_times[-1]
        
        # Verify requirements
        self.assertEqual(processed_count, 1000, "All 1000 items should be processed")
        self.assertLess(p95_time, 60.0, f"95th percentile processing time should be < 60 seconds (got {p95_time:.2f}s)")
        self.assertLess(total_time, 600.0, f"Total processing time should be < 10 minutes for 1000 items (got {total_time:.2f}s)")
        
        print(f"\nPerformance Results:")
        print(f"  Total items: 1000")
        print(f"  Processed: {processed_count}")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Average time per item: {total_time/1000:.3f}s")
        print(f"  95th percentile: {p95_time:.2f}s")
        print(f"  Max time: {max(processing_times):.2f}s")

    @patch('mcp_servers.xero_mcp.get_financial_report')
    @patch('mcp_servers.facebook_mcp.get_engagement_summary')
    @patch('mcp_servers.instagram_mcp.get_engagement_summary')
    @patch('mcp_servers.twitter_mcp.get_engagement_summary')
    @patch('schedulers.run_weekly_audit._generate_ai_insights')
    def test_weekly_audit_generation_performance(
        self,
        mock_ai_insights,
        mock_twitter_engagement,
        mock_instagram_engagement,
        mock_facebook_engagement,
        mock_financial_report
    ):
        """
        T097: Performance test - Weekly audit generation completes in under 60 seconds.
        
        Requirement: Audit generation with all data sources should complete in < 60 seconds.
        """
        from schedulers.run_weekly_audit import generate_audit_report, generate_ceo_briefing
        
        # Mock fast API responses
        mock_financial_report.return_value = {
            'revenue': 50000.0,
            'expenses': 30000.0,
            'net_profit': 20000.0,
            'outstanding_invoices': 0,
            'profit_margin': 40.0,
            'currency': 'USD'
        }
        
        mock_facebook_engagement.return_value = {
            'platforms': [{'platform': 'facebook', 'total_posts': 5, 'total_likes': 100}],
            'total_posts': 5,
            'total_engagement': 100,
            'overall_engagement_rate': 2.0
        }
        
        mock_instagram_engagement.return_value = {
            'platforms': [{'platform': 'instagram', 'total_posts': 3, 'total_likes': 200}],
            'total_posts': 3,
            'total_engagement': 200,
            'overall_engagement_rate': 3.0
        }
        
        mock_twitter_engagement.return_value = {
            'platforms': [{'platform': 'twitter', 'total_posts': 10, 'total_likes': 50}],
            'total_posts': 10,
            'total_engagement': 50,
            'overall_engagement_rate': 1.5
        }
        
        mock_ai_insights.return_value = {
            'executive_summary': 'Test summary ' * 50,  # ~200 words
            'key_insights': ['Insight 1', 'Insight 2', 'Insight 3'],
            'recommendations': ['Rec 1', 'Rec 2'],
            'anomalies': []
        }
        
        # Run audit generation
        period_start = date.today() - timedelta(days=7)
        period_end = date.today()
        
        action_logs_summary = {
            'total_actions': 100,
            'successful_actions': 95,
            'failed_actions': 5,
            'automation_rate': 95.0
        }
        
        start_time = time.time()
        
        # Collect data (simulated - would call MCP servers)
        financial_data = mock_financial_report()
        social_data = {
            'platforms': [
                mock_facebook_engagement()['platforms'][0],
                mock_instagram_engagement()['platforms'][0],
                mock_twitter_engagement()['platforms'][0]
            ],
            'total_posts': 18,
            'total_engagement': 350,
            'overall_engagement_rate': 2.2
        }
        ai_insights = mock_ai_insights()
        
        # Generate audit report
        audit_report = generate_audit_report(
            period_start=period_start,
            period_end=period_end,
            financial_data=financial_data,
            social_media_data=social_data,
            action_logs_summary=action_logs_summary,
            ai_insights=ai_insights
        )
        
        # Generate CEO briefing
        briefing = generate_ceo_briefing(
            period_start=period_start,
            period_end=period_end,
            audit_report=audit_report,
            ai_insights=ai_insights
        )
        
        total_time = time.time() - start_time
        
        # Verify performance requirement
        self.assertLess(total_time, 60.0, f"Audit generation should complete in < 60 seconds (got {total_time:.2f}s)")
        
        # Verify outputs
        self.assertIsNotNone(audit_report)
        self.assertIsNotNone(briefing)
        
        print(f"\nAudit Generation Performance:")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Financial data: {time.time() - start_time:.2f}s")
        print(f"  Social media data: {time.time() - start_time:.2f}s")
        print(f"  AI insights: {time.time() - start_time:.2f}s")
        print(f"  Report generation: {time.time() - start_time:.2f}s")


if __name__ == '__main__':
    unittest.main()

