"""
AI Employee Models Package

This package contains data models and utilities for managing
action items and tracking processed items.

Bronze Tier Models:
- ActionItem: Represents a detected item requiring attention
- ProcessedTracker: Tracks processed item IDs to prevent duplicates

Silver Tier Models:
- ApprovalRequest: External action awaiting human approval
- create_approval_file: Helper to create approval request files
- parse_approval_file: Helper to parse approval request files
- MCPServer: MCP server metadata and status tracking
- WatcherInstance: Watcher process status and metrics
- WatcherConfig: Watcher configuration settings
- WatcherHealth: Watcher health metrics

Gold Tier Models:
- BusinessGoal: Business objective tracked across multiple actions
- XeroTransaction: Financial transaction synced from Xero
- SocialMediaPost: Social media post created via MCP servers
- CrossDomainWorkflow: Workflow spanning Personal and Business domains
- MCPServerStatus: Health and status information for MCP servers
- CEOBriefing: Weekly executive summary with AI-generated insights
- AuditReport: Weekly business and accounting audit
- BusinessMetric: Business KPIs tracked over time
- FinancialSummary: Aggregated financial data from Xero
- SocialMediaEngagement: Aggregated social media engagement metrics
"""

from .action_item import ActionItem, create_action_file, parse_action_file
from .processed_tracker import ProcessedTracker
from .approval_request import (
    ApprovalRequest,
    create_approval_file as create_approval_request_file,
    parse_approval_file,
)
from .mcp_server import MCPServer
from .watcher_instance import WatcherInstance, WatcherConfig, WatcherHealth

# Gold Tier Models
from .business_goal import BusinessGoal, Metric
from .xero_transaction import XeroTransaction, LineItem
from .social_media_post import SocialMediaPost, EngagementMetrics
from .cross_domain_workflow import CrossDomainWorkflow, WorkflowStep
from .mcp_server_status import MCPServerStatus
from .ceo_briefing import CEOBriefing, GoalProgress
from .audit_report import AuditReport, Anomaly
from .business_metric import BusinessMetric
from .financial_summary import FinancialSummary
from .social_media_engagement import SocialMediaEngagement, PlatformEngagement

__all__ = [
    # Bronze tier
    'ActionItem',
    'create_action_file',
    'ProcessedTracker',
    # Silver tier
    'ApprovalRequest',
    'create_approval_request_file',
    'parse_approval_file',
    'MCPServer',
    'WatcherInstance',
    'WatcherConfig',
    'WatcherHealth',
    # Gold tier
    'BusinessGoal',
    'Metric',
    'XeroTransaction',
    'LineItem',
    'SocialMediaPost',
    'EngagementMetrics',
    'CrossDomainWorkflow',
    'WorkflowStep',
    'MCPServerStatus',
    'CEOBriefing',
    'GoalProgress',
    'AuditReport',
    'Anomaly',
    'BusinessMetric',
    'FinancialSummary',
    'SocialMediaEngagement',
    'PlatformEngagement',
]
