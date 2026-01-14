"""
Weekly Business & Accounting Audit with CEO Briefing (Gold Tier)

Automatically generates comprehensive weekly audit (Monday 9 AM) and CEO briefing (Monday 10 AM)
with AI-generated insights from Xero, social media, and action logs.

Usage:
    # Run audit phase (9 AM)
    python schedulers/run_weekly_audit.py --phase audit

    # Run CEO briefing phase (10 AM)
    python schedulers/run_weekly_audit.py --phase briefing

    # Run both phases (for testing)
    python schedulers/run_weekly_audit.py --phase all

    # Run with specific date range (for testing)
    python schedulers/run_weekly_audit.py --phase all --start-date 2026-01-06 --end-date 2026-01-12
"""

import argparse
import json
import logging
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from groq import Groq

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from AI_Employee.models.audit_report import Anomaly, AuditReport
from AI_Employee.models.ceo_briefing import CEOBriefing, GoalProgress
from AI_Employee.models.financial_summary import FinancialSummary
from AI_Employee.models.social_media_engagement import PlatformEngagement, SocialMediaEngagement
from AI_Employee.utils.config import Config
from AI_Employee.utils.health_checker import HealthChecker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize config
config = Config()


def get_week_period(today: Optional[date] = None) -> tuple[date, date]:
    """
    Get Monday-Sunday period for the week containing the given date.
    
    Args:
        today: Reference date (defaults to today)
    
    Returns:
        Tuple of (monday_date, sunday_date)
    """
    if today is None:
        today = date.today()
    
    # Get Monday of the week
    days_since_monday = today.weekday()
    monday = today - timedelta(days=days_since_monday)
    
    # Get Sunday of the week
    sunday = monday + timedelta(days=6)
    
    return monday, sunday


def get_xero_financial_data(period_start: date, period_end: date) -> Optional[dict[str, Any]]:
    """
    Get financial data from Xero MCP server.
    
    Args:
        period_start: Start date for financial report
        period_end: End date for financial report
    
    Returns:
        Financial data dictionary or None if unavailable
    """
    try:
        # Import Xero MCP tools
        from AI_Employee.mcp_servers.xero_mcp import get_financial_report
        
        # Get Profit & Loss report
        report = get_financial_report(
            report_type="profit_and_loss",
            from_date=period_start.isoformat(),
            to_date=period_end.isoformat()
        )
        
        # Get invoices for outstanding calculation
        from AI_Employee.mcp_servers.xero_mcp import get_invoices
        invoices = get_invoices(
            status="AUTHORISED",
            date_from=period_start.isoformat(),
            date_to=period_end.isoformat()
        )
        
        # Calculate outstanding invoices
        outstanding_count = 0
        outstanding_amount = 0.0
        for inv in invoices.get('invoices', []):
            amount_due = inv.get('amount_due', 0.0)
            if amount_due > 0:
                outstanding_count += 1
                outstanding_amount += amount_due
        
        # Build financial summary
        financial_data = {
            'revenue': report.get('revenue', 0.0),
            'expenses': report.get('expenses', 0.0),
            'net_profit': report.get('net_profit', 0.0),
            'outstanding_invoices': outstanding_count,
            'outstanding_invoice_amount': outstanding_amount,
            'currency': 'USD',  # Default, should come from Xero config
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat()
        }
        
        # Calculate profit margin
        revenue = financial_data['revenue']
        if revenue > 0:
            financial_data['profit_margin'] = (financial_data['net_profit'] / revenue) * 100.0
        else:
            financial_data['profit_margin'] = 0.0
        
        return financial_data
        
    except Exception as e:
        logger.error(f"Failed to get Xero financial data: {e}")
        return None


def get_social_media_data(period_start: date, period_end: date) -> Optional[dict[str, Any]]:
    """
    Get social media engagement data from Facebook, Instagram, Twitter MCP servers.
    
    Args:
        period_start: Start date for engagement metrics
        period_end: End date for engagement metrics
    
    Returns:
        Social media engagement data dictionary or None if unavailable
    """
    platforms = []
    unavailable_platforms = []
    
    # Facebook
    try:
        from AI_Employee.mcp_servers.facebook_mcp import get_engagement_summary
        
        page_id = os.getenv('FACEBOOK_PAGE_ID', '')
        if page_id:
            fb_data = get_engagement_summary(
                page_id=page_id,
                since=datetime.combine(period_start, datetime.min.time()).isoformat(),
                until=datetime.combine(period_end, datetime.max.time()).isoformat()
            )
            
            platforms.append(PlatformEngagement(
                platform='facebook',
                total_posts=0,  # Would need to get from get_page_posts
                total_likes=fb_data.get('total_likes', 0),
                total_comments=fb_data.get('total_comments', 0),
                total_shares=fb_data.get('total_shares', 0),
                total_impressions=fb_data.get('total_reach', 0),
                total_reach=fb_data.get('total_reach', 0),
                engagement_rate=fb_data.get('engagement_rate', 0.0),
                follower_growth=0  # Would need separate API call
            ))
    except Exception as e:
        logger.warning(f"Facebook data unavailable: {e}")
        unavailable_platforms.append('facebook')
    
    # Instagram
    try:
        from AI_Employee.mcp_servers.instagram_mcp import get_insights
        
        instagram_business_id = os.getenv('INSTAGRAM_BUSINESS_ID', '')
        if instagram_business_id:
            ig_insights = get_insights(
                instagram_business_id=instagram_business_id,
                metric="impressions,reach",
                period="week",
                since=datetime.combine(period_start, datetime.min.time()).isoformat(),
                until=datetime.combine(period_end, datetime.max.time()).isoformat()
            )
            
            # Get media for engagement
            from AI_Employee.mcp_servers.instagram_mcp import get_media
            media = get_media(
                instagram_business_id=instagram_business_id,
                limit=100
            )
            
            total_likes = sum(m.get('like_count', 0) for m in media.get('media', []))
            total_comments = sum(m.get('comments_count', 0) for m in media.get('media', []))
            
            platforms.append(PlatformEngagement(
                platform='instagram',
                total_posts=len(media.get('media', [])),
                total_likes=total_likes,
                total_comments=total_comments,
                total_shares=0,  # Instagram doesn't have shares
                total_impressions=0,  # Would come from insights
                total_reach=0,  # Would come from insights
                engagement_rate=0.0,
                follower_growth=0
            ))
    except Exception as e:
        logger.warning(f"Instagram data unavailable: {e}")
        unavailable_platforms.append('instagram')
    
    # Twitter
    try:
        from AI_Employee.mcp_servers.twitter_mcp import get_engagement_summary
        
        user_id = os.getenv('TWITTER_USER_ID', '')
        if user_id:
            twitter_data = get_engagement_summary(
                user_id=user_id,
                start_time=datetime.combine(period_start, datetime.min.time()).isoformat(),
                end_time=datetime.combine(period_end, datetime.max.time()).isoformat()
            )
            
            platforms.append(PlatformEngagement(
                platform='twitter',
                total_posts=twitter_data.get('total_tweets', 0),
                total_likes=twitter_data.get('total_likes', 0),
                total_comments=twitter_data.get('total_replies', 0),
                total_shares=twitter_data.get('total_retweets', 0),
                total_impressions=twitter_data.get('total_impressions', 0),
                total_reach=twitter_data.get('total_impressions', 0),  # Twitter uses impressions
                engagement_rate=twitter_data.get('engagement_rate', 0.0),
                follower_growth=0  # Would need separate API call
            ))
    except Exception as e:
        logger.warning(f"Twitter data unavailable: {e}")
        unavailable_platforms.append('twitter')
    
    if not platforms:
        return None
    
    # Build social media engagement summary
    engagement = SocialMediaEngagement(
        period_start=period_start,
        period_end=period_end,
        platform_engagement=platforms
    )
    
    total_posts, total_engagement, overall_rate = engagement.calculate_totals()
    engagement.total_posts = total_posts
    engagement.total_engagement = total_engagement
    engagement.overall_engagement_rate = overall_rate
    
    return {
        'platforms': [p.model_dump() for p in platforms],
        'total_posts': total_posts,
        'total_engagement': total_engagement,
        'overall_engagement_rate': overall_rate,
        'unavailable_platforms': unavailable_platforms
    }


def parse_action_logs(period_start: date, period_end: date) -> dict[str, Any]:
    """
    Parse action logs from /Logs/ for the specified period.
    
    Args:
        period_start: Start date for log parsing
        period_end: End date for log parsing
    
    Returns:
        Action logs summary dictionary
    """
    logs_path = config.logs_path
    total_actions = 0
    successful_actions = 0
    failed_actions = 0
    actions_by_domain = {}
    actions_by_type = {}
    total_processing_time = 0.0
    
    # Iterate through log files in the period
    current_date = period_start
    while current_date <= period_end:
        log_file = logs_path / f"{current_date.isoformat()}.json"
        
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                    
                    if isinstance(log_data, list):
                        for entry in log_data:
                            total_actions += 1
                            
                            # Track by result
                            result = entry.get('result', 'unknown')
                            if result == 'success':
                                successful_actions += 1
                            elif result == 'failure':
                                failed_actions += 1
                            
                            # Track by domain
                            domain = entry.get('domain', 'unknown')
                            actions_by_domain[domain] = actions_by_domain.get(domain, 0) + 1
                            
                            # Track by type
                            action_type = entry.get('action_type', 'unknown')
                            actions_by_type[action_type] = actions_by_type.get(action_type, 0) + 1
                            
                            # Track processing time
                            duration = entry.get('execution_duration_ms', 0)
                            if duration:
                                total_processing_time += duration / 1000.0  # Convert to seconds
            except Exception as e:
                logger.warning(f"Failed to parse log file {log_file}: {e}")
        
        current_date += timedelta(days=1)
    
    # Calculate success rate
    success_rate = (successful_actions / total_actions * 100.0) if total_actions > 0 else 0.0
    avg_processing_time = (total_processing_time / total_actions) if total_actions > 0 else 0.0
    
    return {
        'total_actions': total_actions,
        'actions_by_domain': actions_by_domain,
        'actions_by_type': actions_by_type,
        'success_rate': success_rate,
        'failed_actions': failed_actions,
        'average_processing_time_seconds': avg_processing_time
    }


def generate_ai_insights(
    financial_data: Optional[dict],
    social_media_data: Optional[dict],
    action_logs_summary: dict,
    period_start: date,
    period_end: date
) -> dict[str, Any]:
    """
    Generate AI insights using Groq API.

    Args:
        financial_data: Financial data from Xero
        social_media_data: Social media engagement data
        action_logs_summary: Action logs summary
        period_start: Period start date
        period_end: Period end date

    Returns:
        Dictionary with executive_summary, key_insights, recommendations, risks_and_alerts
    """
    api_key = os.getenv('GROQ_API_KEY', '')
    if not api_key:
        logger.warning("GROQ_API_KEY not configured, skipping AI insights")
        return {
            'executive_summary': f"Week of {period_start} to {period_end}: Business operations summary. [AI insights unavailable - GROQ_API_KEY not configured]",
            'key_insights': [
                "AI insights generation requires GROQ_API_KEY configuration",
                "Financial and social media data collected successfully",
                "Action logs processed for the reporting period"
            ],
            'recommendations': [],
            'risks_and_alerts': []
        }

    try:
        client = Groq(api_key=api_key)

        # Build prompt
        prompt = f"""Analyze this business week data ({period_start} to {period_end}) and generate:

1. Executive Summary (200-300 words): High-level overview of business performance, key achievements, and concerns
2. Key Insights (3-5 bullet points): Most important findings from the data
3. Recommendations (3-5 actionable items): Specific recommendations for improvement
4. Risks and Alerts (list any critical issues): Any anomalies, overdue items, or concerns requiring attention

Data:
- Financial: {json.dumps(financial_data, default=str) if financial_data else '[DATA UNAVAILABLE: Xero]'}
- Social Media: {json.dumps(social_media_data, default=str) if social_media_data else '[DATA UNAVAILABLE: Social Media]'}
- Action Logs: {json.dumps(action_logs_summary, default=str)}

Format your response as JSON:
{{
    "executive_summary": "200-300 word summary...",
    "key_insights": ["insight 1", "insight 2", ...],
    "recommendations": ["recommendation 1", "recommendation 2", ...],
    "risks_and_alerts": ["alert 1", "alert 2", ...]
}}
"""

        response = client.chat.completions.create(
            model=os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile'),
            messages=[
                {
                    "role": "system",
                    "content": "You are a business analyst AI assistant. Analyze data and provide actionable insights in JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.5,
            max_tokens=2000
        )

        # Parse JSON response
        response_text = response.choices[0].message.content
        # Extract JSON from markdown code blocks if present
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        insights = json.loads(response_text)

        return {
            'executive_summary': insights.get('executive_summary', ''),
            'key_insights': insights.get('key_insights', []),
            'recommendations': insights.get('recommendations', []),
            'risks_and_alerts': insights.get('risks_and_alerts', [])
        }

    except Exception as e:
        logger.error(f"Failed to generate AI insights: {e}")
        return {
            'executive_summary': f"Week of {period_start} to {period_end}: Business operations summary. [AI insights generation failed: {str(e)}]",
            'key_insights': [
                "AI insights generation encountered an error",
                "Manual review of data recommended"
            ],
            'recommendations': [],
            'risks_and_alerts': ["AI insights generation failed - manual review required"]
        }


def generate_audit_report(
    period_start: date,
    period_end: date,
    financial_data: Optional[dict],
    social_media_data: Optional[dict],
    action_logs_summary: dict,
    ai_insights: dict
) -> AuditReport:
    """
    Generate Audit Report from collected data.
    
    Args:
        period_start: Period start date
        period_end: Period end date
        financial_data: Financial data from Xero
        social_media_data: Social media engagement data
        action_logs_summary: Action logs summary
        ai_insights: AI-generated insights
    
    Returns:
        AuditReport object
    """
    # Determine report status
    status = "complete"
    if not financial_data or not social_media_data:
        status = "partial"
    
    # Build financial summary
    financial_summary = None
    if financial_data:
        financial_summary = FinancialSummary(
            period_start=period_start,
            period_end=period_end,
            revenue=financial_data.get('revenue', 0.0),
            expenses=financial_data.get('expenses', 0.0),
            net_profit=financial_data.get('net_profit', 0.0),
            outstanding_invoices=financial_data.get('outstanding_invoices', 0),
            outstanding_invoice_amount=financial_data.get('outstanding_invoice_amount', 0.0),
            profit_margin=financial_data.get('profit_margin', 0.0),
            currency=financial_data.get('currency', 'USD')
        )
    
    # Build social media engagement
    social_media_engagement = None
    if social_media_data:
        platforms = [
            PlatformEngagement(**p) for p in social_media_data.get('platforms', [])
        ]
        social_media_engagement = SocialMediaEngagement(
            period_start=period_start,
            period_end=period_end,
            platform_engagement=platforms,
            total_posts=social_media_data.get('total_posts', 0),
            total_engagement=social_media_data.get('total_engagement', 0),
            overall_engagement_rate=social_media_data.get('overall_engagement_rate', 0.0)
        )
    
    # Detect anomalies
    anomalies = []
    
    # Financial anomalies
    if financial_data:
        if financial_data.get('outstanding_invoice_amount', 0) > 1000:
            anomalies.append(Anomaly(
                severity='high',
                type='financial',
                description=f"Outstanding invoices total ${financial_data.get('outstanding_invoice_amount', 0):.2f}",
                detected_at=datetime.now()
            ))
        
        if financial_data.get('profit_margin', 0) < 0:
            anomalies.append(Anomaly(
                severity='critical',
                type='financial',
                description="Negative profit margin detected",
                detected_at=datetime.now()
            ))
    
    # Social media anomalies
    if social_media_data:
        unavailable = social_media_data.get('unavailable_platforms', [])
        if unavailable:
            anomalies.append(Anomaly(
                severity='medium',
                type='social',
                description=f"Social media data unavailable for: {', '.join(unavailable)}",
                detected_at=datetime.now()
            ))
    
    # Operational anomalies
    if action_logs_summary.get('success_rate', 100) < 80:
        anomalies.append(Anomaly(
            severity='medium',
            type='operational',
            description=f"Action success rate below target: {action_logs_summary.get('success_rate', 0):.1f}%",
            detected_at=datetime.now()
        ))
    
    # Get MCP server health
    mcp_server_health = {}
    try:
        health_checker = HealthChecker(
            mcp_servers_config_path=config.vault_path / "mcp_servers.json",
            status_dir=config.system_path / "MCP_Status"
        )
        # This would check all MCP servers, simplified here
        mcp_server_health = {}  # Would be populated from health_checker
    except Exception as e:
        logger.warning(f"Failed to get MCP server health: {e}")
    
    # Build audit report
    report = AuditReport(
        period_start=period_start,
        period_end=period_end,
        financial_data=financial_summary.model_dump() if financial_summary else None,
        social_media_data=social_media_engagement.model_dump() if social_media_engagement else None,
        action_logs_summary=action_logs_summary,
        cross_domain_workflows=[],  # Would be populated from logs
        anomalies=anomalies,
        mcp_server_health=mcp_server_health,
        recommendations=ai_insights.get('recommendations', []),
        status=status
    )
    
    return report


def generate_ceo_briefing(
    period_start: date,
    period_end: date,
    audit_report: AuditReport,
    ai_insights: dict
) -> CEOBriefing:
    """
    Generate CEO Briefing from audit report and AI insights.
    
    Args:
        period_start: Period start date
        period_end: Period end date
        audit_report: Generated audit report
        ai_insights: AI-generated insights
    
    Returns:
        CEOBriefing object
    """
    # Get business goals (simplified - would read from /Business/Goals/)
    goal_progress = []
    goals_path = config.business_path / 'Goals'
    if goals_path.exists():
        for goal_file in goals_path.glob("*.json"):
            try:
                with open(goal_file, 'r') as f:
                    goal_data = json.load(f)
                    goal_progress.append(GoalProgress(
                        goal_id=goal_data.get('id', ''),
                        goal_title=goal_data.get('title', ''),
                        completion_percentage=0.0,  # Would calculate from metrics
                        status=goal_data.get('status', 'active')
                    ))
            except Exception as e:
                logger.warning(f"Failed to parse goal file {goal_file}: {e}")
    
    # Build financial summary for briefing
    financial_summary = None
    if audit_report.financial_data:
        financial_summary = audit_report.financial_data
    
    # Build social media summary for briefing
    social_media_summary = None
    if audit_report.social_media_data:
        social_media_summary = audit_report.social_media_data
    
    # Build action items summary
    action_items_summary = {
        'total_processed': audit_report.action_logs_summary.get('total_actions', 0),
        'by_category': audit_report.action_logs_summary.get('actions_by_type', {})
    }
    
    # Build risks and alerts from anomalies
    risks_and_alerts = ai_insights.get('risks_and_alerts', [])
    critical_anomalies = audit_report.get_critical_anomalies()
    for anomaly in critical_anomalies:
        risks_and_alerts.append(f"[{anomaly.severity.upper()}] {anomaly.description}")
    
    # Build attachments
    attachments = [
        f"/Accounting/Audits/{period_start.isoformat()}-audit-report.json"
    ]
    
    # Build CEO briefing
    briefing = CEOBriefing(
        period_start=period_start,
        period_end=period_end,
        executive_summary=ai_insights.get('executive_summary', ''),
        key_insights=ai_insights.get('key_insights', [])[:5],  # Ensure max 5
        financial_summary=financial_summary,
        social_media_summary=social_media_summary,
        action_items_summary=action_items_summary,
        goal_progress=goal_progress,
        risks_and_alerts=risks_and_alerts,
        recommendations=ai_insights.get('recommendations', []),
        attachments=attachments
    )
    
    return briefing


def run_audit_phase(period_start: date, period_end: date) -> AuditReport:
    """
    Run the audit phase (9 AM).
    
    Args:
        period_start: Period start date
        period_end: Period end date
    
    Returns:
        Generated AuditReport
    """
    logger.info(f"Starting audit phase for period {period_start} to {period_end}")
    
    # Collect data
    logger.info("Collecting financial data from Xero...")
    financial_data = get_xero_financial_data(period_start, period_end)
    if financial_data:
        logger.info("✅ Financial data collected")
    else:
        logger.warning("⚠️ Financial data unavailable")
    
    logger.info("Collecting social media data...")
    social_media_data = get_social_media_data(period_start, period_end)
    if social_media_data:
        logger.info("✅ Social media data collected")
    else:
        logger.warning("⚠️ Social media data unavailable")
    
    logger.info("Parsing action logs...")
    action_logs_summary = parse_action_logs(period_start, period_end)
    logger.info(f"✅ Processed {action_logs_summary.get('total_actions', 0)} action log entries")
    
    logger.info("Generating AI insights...")
    ai_insights = generate_ai_insights(
        financial_data,
        social_media_data,
        action_logs_summary,
        period_start,
        period_end
    )
    logger.info("✅ AI insights generated")
    
    logger.info("Generating audit report...")
    audit_report = generate_audit_report(
        period_start,
        period_end,
        financial_data,
        social_media_data,
        action_logs_summary,
        ai_insights
    )
    
    # Save audit report
    audit_file = config.accounting_path / 'Audits' / f"{period_start.isoformat()}-audit-report.json"
    audit_file.parent.mkdir(parents=True, exist_ok=True)
    audit_file.write_text(audit_report.model_dump_json(), encoding='utf-8')
    logger.info(f"✅ Audit report saved to {audit_file}")
    
    # Update dashboard
    try:
        from AI_Employee.utils.dashboard import DashboardUpdater
        dashboard = DashboardUpdater(config)
        dashboard.update_weekly_audit_status(
            last_audit_date=period_start,
            next_audit_date=period_start + timedelta(days=7)  # Next Monday
        )
    except Exception as e:
        logger.warning(f"Failed to update dashboard: {e}")
    
    return audit_report


def run_briefing_phase(period_start: date, period_end: date, audit_report: Optional[AuditReport] = None) -> CEOBriefing:
    """
    Run the CEO briefing phase (10 AM).
    
    Args:
        period_start: Period start date
        period_end: Period end date
        audit_report: Optional pre-generated audit report
    
    Returns:
        Generated CEOBriefing
    """
    logger.info(f"Starting CEO briefing phase for period {period_start} to {period_end}")
    
    # Load audit report if not provided
    if audit_report is None:
        audit_file = config.accounting_path / 'Audits' / f"{period_start.isoformat()}-audit-report.json"
        if audit_file.exists():
            audit_report = AuditReport.model_validate_json(audit_file.read_text())
        else:
            logger.warning("Audit report not found, running audit phase first...")
            audit_report = run_audit_phase(period_start, period_end)
    
    # Regenerate AI insights for briefing (may have different focus)
    financial_data = audit_report.financial_data
    social_media_data = audit_report.social_media_data
    action_logs_summary = audit_report.action_logs_summary
    
    logger.info("Generating AI insights for CEO briefing...")
    ai_insights = generate_ai_insights(
        financial_data,
        social_media_data,
        action_logs_summary,
        period_start,
        period_end
    )
    
    logger.info("Generating CEO briefing...")
    briefing = generate_ceo_briefing(
        period_start,
        period_end,
        audit_report,
        ai_insights
    )
    
    # Save CEO briefing
    briefing_file = config.briefings_path / f"{period_start.isoformat()}-ceo-briefing.md"
    briefing_file.parent.mkdir(parents=True, exist_ok=True)
    briefing_file.write_text(briefing.to_markdown(), encoding='utf-8')
    logger.info(f"✅ CEO briefing saved to {briefing_file}")
    
    # Update dashboard
    try:
        from AI_Employee.utils.dashboard import DashboardUpdater
        dashboard = DashboardUpdater(config)
        dashboard.update_weekly_audit_status(
            last_briefing_date=period_start,
            next_audit_date=period_start + timedelta(days=7)  # Next Monday
        )
    except Exception as e:
        logger.warning(f"Failed to update dashboard: {e}")
    
    return briefing


def main():
    """Main entry point for weekly audit scheduler."""
    parser = argparse.ArgumentParser(description='Weekly Business & Accounting Audit')
    parser.add_argument(
        '--phase',
        choices=['audit', 'briefing', 'all'],
        default='all',
        help='Which phase to run (default: all)'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        help='Period start date (YYYY-MM-DD, defaults to Monday of current week)'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='Period end date (YYYY-MM-DD, defaults to Sunday of current week)'
    )
    
    args = parser.parse_args()
    
    # Determine period
    if args.start_date and args.end_date:
        period_start = date.fromisoformat(args.start_date)
        period_end = date.fromisoformat(args.end_date)
    else:
        period_start, period_end = get_week_period()
    
    logger.info(f"Weekly audit scheduler started - Phase: {args.phase}, Period: {period_start} to {period_end}")
    
    try:
        if args.phase in ['audit', 'all']:
            audit_report = run_audit_phase(period_start, period_end)
        else:
            audit_report = None
        
        if args.phase in ['briefing', 'all']:
            briefing = run_briefing_phase(period_start, period_end, audit_report)
        
        logger.info("✅ Weekly audit completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Weekly audit failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

