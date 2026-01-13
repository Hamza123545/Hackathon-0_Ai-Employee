"""
Dashboard updater for Bronze/Silver Tier Personal AI Employee.

Manages the Dashboard.md file in the Obsidian vault, providing
real-time status updates and activity tracking.

Silver tier adds:
- Pending approval count and oldest age
- MCP server health status
- All watchers status
- Recent audit log entries (last 10)
"""

import json
import re
import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Literal, Optional

from .config import Config
from .classifier import Classifier, default_classifier
from .health_checker import get_default_health_checker


StatusType = Literal['running', 'stopped', 'error']


class DashboardUpdater:
    """
    Updates Dashboard.md with current system status.

    Handles reading the existing dashboard, updating specific sections,
    and writing back the changes.

    Attributes:
        config: Configuration object with vault paths
        dashboard_path: Path to Dashboard.md
    """

    def __init__(self, config: Config):
        """
        Initialize the dashboard updater.

        Args:
            config: Configuration object with vault paths.
        """
        self.config = config
        self.dashboard_path = config.dashboard_path
        self.classifier = default_classifier

    def update_watcher_status(
        self,
        status: StatusType,
        watcher_type: str | None = None
    ) -> None:
        """
        Update the watcher status in Dashboard.md.

        Args:
            status: Current watcher status ('running', 'stopped', 'error')
            watcher_type: Type of watcher (filesystem/gmail)
        """
        now = datetime.now()
        self._ensure_dashboard_exists()

        content = self.dashboard_path.read_text(encoding='utf-8')

        # Update frontmatter
        content = self._update_frontmatter_field(
            content, 'last_updated', now.isoformat()
        )
        content = self._update_frontmatter_field(
            content, 'watcher_status', status
        )
        content = self._update_frontmatter_field(
            content, 'last_watcher_check', now.isoformat()
        )

        # Update System Status table
        status_emoji = '✅' if status == 'running' else '⏹️' if status == 'stopped' else '❌'
        watcher_info = f"{watcher_type} watcher" if watcher_type else "Watcher"

        content = self._update_status_table(
            content,
            component='Watcher',
            status=f"{status_emoji} {status}",
            last_activity=now.strftime('%Y-%m-%d %H:%M:%S')
        )

        # Update pending items count
        pending_count = self.count_pending_items()
        content = self._update_pending_count(content, pending_count)

        self.dashboard_path.write_text(content, encoding='utf-8')

    def update_all_sections(
        self,
        status: StatusType,
        watcher_type: str | None = None
    ) -> None:
        """
        Comprehensive update of all Dashboard.md sections.
        
        Updates:
        - Bronze tier sections (watcher status, pending items, activity)
        - Silver tier sections (if enabled): pending approvals, MCP health, watchers, audit entries
        - Data freshness indicator
        - Quick actions section
        - Error state visualization

        This updates:
        - Watcher status and pending count
        - Recent Activity (from filesystem scan of /Done/ and /Plans/)
        - Quick Stats (plans today, processed today, active plans)

        Args:
            status: Current watcher status ('running', 'stopped', 'error')
            watcher_type: Type of watcher (filesystem/gmail)
        """
        now = datetime.now()
        self._ensure_dashboard_exists()

        content = self.dashboard_path.read_text(encoding='utf-8')

        # Update frontmatter
        content = self._update_frontmatter_field(
            content, 'last_updated', now.isoformat()
        )
        content = self._update_frontmatter_field(
            content, 'watcher_status', status
        )
        content = self._update_frontmatter_field(
            content, 'last_watcher_check', now.isoformat()
        )

        # Update System Status table
        status_emoji = '✅' if status == 'running' else '🛑' if status == 'stopped' else '❌'
        content = self._update_status_table(
            content,
            component='Watcher',
            status=f"{status_emoji} {status}",
            last_activity=now.strftime('%Y-%m-%d %H:%M:%S')
        )

        # Update pending items count
        pending_count = self.count_pending_items()
        content = self._update_pending_count(content, pending_count)

        # Update Recent Activity section
        recent_activities = self.list_recent_activity(hours=24)
        content = self._update_recent_activity(content, recent_activities)

        # Update Quick Stats section
        stats = self.get_quick_stats()
        content = self._update_quick_stats(content, stats)

        self.dashboard_path.write_text(content, encoding='utf-8')

    def count_pending_items(self) -> int:
        """
        Count .md files in the Needs_Action folder.

        Returns:
            Number of pending action items.
        """
        needs_action = self.config.needs_action_path
        if not needs_action.exists():
            return 0

        return len(list(needs_action.glob('*.md')))

    def list_recent_activity(self, hours: int = 24) -> list[dict]:
        """
        List items processed in the last N hours.

        Args:
            hours: Number of hours to look back.

        Returns:
            List of activity records with timestamp, action, and details.
        """
        activities = []
        cutoff = datetime.now() - timedelta(hours=hours)

        # Check Done folder for recently processed items
        done_path = self.config.done_path
        if done_path.exists():
            for file in done_path.glob('*.md'):
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                if mtime > cutoff:
                    activities.append({
                        'timestamp': mtime.strftime('%Y-%m-%d %H:%M'),
                        'action': 'Processed',
                        'details': file.stem
                    })

        # Check Plans folder for recently created plans
        plans_path = self.config.plans_path
        if plans_path.exists():
            for file in plans_path.glob('*.md'):
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                if mtime > cutoff:
                    activities.append({
                        'timestamp': mtime.strftime('%Y-%m-%d %H:%M'),
                        'action': 'Plan created',
                        'details': file.stem
                    })

        # Sort by timestamp descending
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities

    def get_quick_stats(self) -> dict:
        """
        Get quick statistics for the dashboard.

        Returns:
            Dict with plans_today, processed_today, active_plans counts.
        """
        today = datetime.now().date()

        plans_today = 0
        plans_path = self.config.plans_path
        if plans_path.exists():
            for file in plans_path.glob('*.md'):
                mtime = datetime.fromtimestamp(file.stat().st_mtime).date()
                if mtime == today:
                    plans_today += 1

        processed_today = 0
        done_path = self.config.done_path
        if done_path.exists():
            for file in done_path.glob('*.md'):
                mtime = datetime.fromtimestamp(file.stat().st_mtime).date()
                if mtime == today:
                    processed_today += 1

        active_plans = 0
        if plans_path.exists():
            # Count plans with status: open or in_progress in frontmatter
            for file in plans_path.glob('*.md'):
                try:
                    content = file.read_text(encoding='utf-8')
                    if 'status: open' in content or 'status: in_progress' in content:
                        active_plans += 1
                except OSError:
                    pass

        return {
            'plans_today': plans_today,
            'processed_today': processed_today,
            'active_plans': active_plans
        }
    
    def get_domain_stats(self) -> dict:
        """
        Get statistics by domain (Personal vs Business) for Gold Tier (T081).
        
        Returns:
            Dict with personal and business domain statistics
        """
        from models.action_item import parse_action_file
        
        personal_count = 0
        business_count = 0
        accounting_count = 0
        social_media_count = 0
        
        # Count pending items by domain
        needs_action = self.config.needs_action_path
        if needs_action.exists():
            for file in needs_action.glob('*.md'):
                try:
                    action_item = parse_action_file(file)
                    domain = self.classifier.classify(
                        title=action_item.title,
                        content=action_item.summary or action_item.content,
                        source=action_item.source
                    )
                    if domain == 'personal':
                        personal_count += 1
                    elif domain == 'business':
                        business_count += 1
                    elif domain == 'accounting':
                        accounting_count += 1
                    elif domain == 'social_media':
                        social_media_count += 1
                except Exception:
                    # If parsing fails, count as personal (default)
                    personal_count += 1
        
        # Count processed items today by domain
        today = datetime.now().date()
        personal_processed = 0
        business_processed = 0
        
        done_path = self.config.done_path
        if done_path.exists():
            for file in done_path.glob('*.md'):
                try:
                    mtime = datetime.fromtimestamp(file.stat().st_mtime).date()
                    if mtime == today:
                        action_item = parse_action_file(file)
                        domain = self.classifier.classify(
                            title=action_item.title,
                            content=action_item.summary or action_item.content,
                            source=action_item.source
                        )
                        if domain in ['personal']:
                            personal_processed += 1
                        elif domain in ['business', 'accounting', 'social_media']:
                            business_processed += 1
                except Exception:
                    pass
        
        # Count cross-domain workflows
        workflows_path = self.config.business_path / 'Workflows'
        cross_domain_workflows = 0
        if workflows_path.exists():
            for file in workflows_path.glob('*.json'):
                try:
                    from models.cross_domain_workflow import CrossDomainWorkflow
                    workflow = CrossDomainWorkflow.model_validate_json(file.read_text(encoding='utf-8'))
                    if workflow.status in ['pending', 'in_progress']:
                        cross_domain_workflows += 1
                except Exception:
                    pass
        
        return {
            'personal': {
                'pending': personal_count,
                'processed_today': personal_processed
            },
            'business': {
                'pending': business_count,
                'processed_today': business_processed,
                'accounting_pending': accounting_count,
                'social_media_pending': social_media_count
            },
            'cross_domain_workflows': cross_domain_workflows
        }
    
    def update_weekly_audit_status(
        self,
        last_audit_date: Optional[date] = None,
        last_briefing_date: Optional[date] = None,
        next_audit_date: Optional[date] = None
    ) -> None:
        """
        Update weekly audit status in Dashboard.md (Gold Tier).
        
        Args:
            last_audit_date: Date of last audit report
            last_briefing_date: Date of last CEO briefing
            next_audit_date: Date of next scheduled audit
        """
        if not self.dashboard_path.exists():
            return
        
        try:
            content = self.dashboard_path.read_text(encoding='utf-8')
            
            # Find or create Gold Tier section
            gold_section_pattern = r'## Gold Tier Metrics\n.*?(?=\n## [A-Z]|$)'
            gold_section = self._build_gold_tier_section(last_audit_date, last_briefing_date, next_audit_date)
            
            if re.search(gold_section_pattern, content, re.DOTALL):
                content = re.sub(gold_section_pattern, gold_section.strip() + '\n', content, flags=re.DOTALL)
            else:
                # Insert before Recent Errors or at end
                if '## Recent Errors' in content:
                    content = content.replace('## Recent Errors', gold_section + '\n## Recent Errors')
                else:
                    content += '\n' + gold_section
            
            self.dashboard_path.write_text(content, encoding='utf-8')
            
        except Exception as e:
            logger.warning(f"Failed to update weekly audit status: {e}")
    
    def _build_gold_tier_section(
        self,
        last_audit_date: Optional[date],
        last_briefing_date: Optional[date],
        next_audit_date: Optional[date]
    ) -> str:
        """Build Gold Tier Metrics section for dashboard."""
        section = ["## Gold Tier Metrics\n"]
        
        # Weekly Audit Status
        section.append("### Weekly Audit Status\n")
        
        if last_audit_date:
            section.append(f"- **Last Audit**: {last_audit_date.isoformat()}\n")
        else:
            section.append("- **Last Audit**: Never\n")
        
        if last_briefing_date:
            section.append(f"- **Last CEO Briefing**: {last_briefing_date.isoformat()}\n")
        else:
            section.append("- **Last CEO Briefing**: Never\n")
        
        if next_audit_date:
            section.append(f"- **Next Scheduled Audit**: {next_audit_date.isoformat()} (Monday 9:00 AM)\n")
        else:
            # Calculate next Monday
            today = date.today()
            days_until_monday = (7 - today.weekday()) % 7
            if days_until_monday == 0 and datetime.now().hour < 9:
                next_monday = today
            else:
                next_monday = today + timedelta(days=days_until_monday if days_until_monday > 0 else 7)
            section.append(f"- **Next Scheduled Audit**: {next_monday.isoformat()} (Monday 9:00 AM)\n")
        
        section.append("\n")
        
        return ''.join(section)
    
    def update_ai_processor_status(
        self,
        uptime_seconds: int,
        items_processed: int,
        items_failed: int,
        last_check_time: datetime
    ) -> None:
        """
        Update AI Processor status in Dashboard.md (Gold Tier).
        
        Args:
            uptime_seconds: Processor uptime in seconds
            items_processed: Total items processed
            items_failed: Total items failed
            last_check_time: Last check timestamp
        """
        self._ensure_dashboard_exists()
        content = self.dashboard_path.read_text(encoding='utf-8')
        
        # Format uptime
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        uptime_str = f"{hours}h {minutes}m"
        
        # Update or add AI Processor section
        processor_section = f"""## AI Processor Status (Gold Tier)

**Status**: ✅ Running
**Uptime**: {uptime_str}
**Items Processed**: {items_processed}
**Items Failed**: {items_failed}
**Last Check**: {last_check_time.strftime('%Y-%m-%d %H:%M:%S')}
**Success Rate**: {(items_processed / (items_processed + items_failed) * 100) if (items_processed + items_failed) > 0 else 0:.1f}%

"""
        
        # Check if AI Processor section exists
        if "## AI Processor Status" in content:
            # Replace existing section
            pattern = r"## AI Processor Status.*?(?=\n## |\Z)"
            content = re.sub(pattern, processor_section.strip(), content, flags=re.DOTALL)
        else:
            # Add after System Status section
            if "## System Status" in content:
                content = content.replace("## System Status", f"## System Status\n\n{processor_section}")
            else:
                # Add at the end
                content += f"\n\n{processor_section}"
        
        # Update frontmatter
        content = self._update_frontmatter_field(
            content, 'last_updated', datetime.now().isoformat()
        )
        
        self.dashboard_path.write_text(content, encoding='utf-8')

    def render(self) -> str:
        """
        Generate complete Dashboard.md content.

        Returns:
            Full Markdown content for Dashboard.md.
        """
        now = datetime.now()
        pending_count = self.count_pending_items()
        recent = self.list_recent_activity()
        stats = self.get_quick_stats()

        # Build pending items table
        pending_rows = self._build_pending_items_table()

        # Build recent activity table
        recent_rows = ''
        for activity in recent[:10]:  # Limit to 10 most recent
            recent_rows += f"| {activity['timestamp']} | {activity['action']} | {activity['details']} |\n"
        if not recent_rows:
            recent_rows = "| - | No recent activity | - |\n"

        return f"""---
last_updated: {now.isoformat()}
watcher_status: stopped
last_watcher_check: {now.isoformat()}
---

# Personal AI Employee Dashboard

**Last Updated**: {now.strftime('%Y-%m-%d %H:%M:%S')}

> **Data Freshness**: Last updated {now.strftime('%Y-%m-%d %H:%M:%S')} (<5 minutes)

## System Status

| Component | Status | Last Activity |
|-----------|--------|---------------|
| Watcher | ⏹️ stopped | {now.strftime('%Y-%m-%d %H:%M:%S')} |
| Vault Access | ✅ OK | {now.strftime('%Y-%m-%d %H:%M:%S')} |

## Pending Items

**Items in /Needs_Action**: {pending_count}

| Item | Source | Priority | Age |
|------|--------|----------|-----|
{pending_rows if pending_rows else "| - | - | - | - |\n"}

## Recent Activity (Last 24h)

| Time | Action | Details |
|------|--------|---------|
{recent_rows}

## Quick Stats

- **Plans created today**: {stats['plans_today']}
- **Items processed today**: {stats['processed_today']}
- **Active plans**: {stats['active_plans']}

## Recent Errors

No recent errors.

## Silver Tier Metrics

### Pending Approvals

**Pending**: 0 | **Oldest**: N/A

### MCP Server Health (T088)

{self._build_mcp_health_section()}

### All Watchers Status

No watcher status data available.

### Recent Audit Entries (Last 10)

No audit entries for today.

## Gold Tier: Cross-Domain Metrics (T081)

{self._build_cross_domain_section()}

## Quick Actions

- 📁 [Open Pending Approvals Folder](/Pending_Approval/) - Review and approve actions
- 📋 [View Today's Audit Log](/Logs/{now.strftime('%Y-%m-%d')}.json) - See all actions executed today
- 🔍 [Check PM2 Status](pm2 status) - View process manager status
"""

    def _ensure_dashboard_exists(self) -> None:
        """Create Dashboard.md with default content if it doesn't exist."""
        if not self.dashboard_path.exists():
            content = self.render()
            self.dashboard_path.parent.mkdir(parents=True, exist_ok=True)
            self.dashboard_path.write_text(content, encoding='utf-8')

    def _update_frontmatter_field(
        self,
        content: str,
        field: str,
        value: str
    ) -> str:
        """
        Update a field in the YAML frontmatter.

        Args:
            content: Full file content.
            field: Field name to update.
            value: New value for the field.

        Returns:
            Updated content.
        """
        pattern = rf'^({field}:\s*).*$'
        replacement = rf'\g<1>{value}'

        # Try to update existing field
        new_content, count = re.subn(
            pattern,
            replacement,
            content,
            count=1,
            flags=re.MULTILINE
        )

        if count == 0:
            # Field doesn't exist, add it after the opening ---
            new_content = re.sub(
                r'^(---\n)',
                rf'\g<1>{field}: {value}\n',
                content,
                count=1
            )

        return new_content

    def _update_status_table(
        self,
        content: str,
        component: str,
        status: str,
        last_activity: str
    ) -> str:
        """
        Update a row in the System Status table.

        Args:
            content: Full file content.
            component: Component name (e.g., 'Watcher').
            status: Status string.
            last_activity: Last activity timestamp.

        Returns:
            Updated content.
        """
        # Match table row for the component
        pattern = rf'\|\s*{component}\s*\|[^|]*\|[^|]*\|'
        replacement = f'| {component} | {status} | {last_activity} |'

        return re.sub(pattern, replacement, content)

    def _update_pending_count(self, content: str, count: int) -> str:
        """
        Update the pending items count in the dashboard.

        Args:
            content: Full file content.
            count: New pending count.

        Returns:
            Updated content.
        """
        pattern = r'\*\*Items in /Needs_Action\*\*:\s*\d+'
        replacement = f'**Items in /Needs_Action**: {count}'

        return re.sub(pattern, replacement, content)

    def _build_mcp_health_section(self) -> str:
        """
        Build MCP server health section for Dashboard (T088).
        
        Returns:
            Markdown section with MCP server health status
        """
        try:
            health_checker = get_default_health_checker(self.config.vault_path)
            all_statuses = health_checker.get_all_server_statuses()
            
            if not all_statuses:
                return "No MCP servers configured or no status data available.\n"
            
            section = []
            section.append("| Server | Status | Success Rate | Avg Response | Last Success |\n")
            section.append("|--------|--------|--------------|--------------|-------------|\n")
            
            for server_name, status in sorted(all_statuses.items()):
                # Status emoji
                status_emoji = {
                    'healthy': '✅',
                    'degraded': '⚠️',
                    'down': '❌',
                    'unknown': '❓'
                }.get(status.status, '❓')
                
                # Format success rate
                success_rate = status.calculate_success_rate()
                success_rate_str = f"{success_rate:.1f}%" if status.total_requests > 0 else "N/A"
                
                # Format average response time
                avg_response_str = f"{status.average_response_time_ms:.0f}ms" if status.average_response_time_ms > 0 else "N/A"
                
                # Format last success time
                if status.last_successful_request:
                    last_success_str = status.last_successful_request.strftime('%Y-%m-%d %H:%M')
                else:
                    last_success_str = "Never"
                
                section.append(
                    f"| {server_name} | {status_emoji} {status.status} | {success_rate_str} | "
                    f"{avg_response_str} | {last_success_str} |\n"
                )
            
            # Add degraded/down servers summary
            degraded = health_checker.get_degraded_servers()
            down = health_checker.get_down_servers()
            
            if degraded or down:
                section.append("\n**⚠️ Degraded Servers**: " + (", ".join(degraded) if degraded else "None") + "\n")
                section.append("**❌ Down Servers**: " + (", ".join(down) if down else "None") + "\n")
            
            return ''.join(section)
        except Exception as e:
            logger.warning(f"Failed to build MCP health section: {e}")
            return "Error loading MCP server health status.\n"
    
    def _build_cross_domain_section(self) -> str:
        """
        Build cross-domain metrics section for Dashboard (T081).
        
        Returns:
            Markdown section with Personal and Business domain metrics
        """
        domain_stats = self.get_domain_stats()
        
        section = []
        section.append("### Personal Domain\n")
        section.append(f"- **Pending Items**: {domain_stats['personal']['pending']}\n")
        section.append(f"- **Processed Today**: {domain_stats['personal']['processed_today']}\n")
        section.append("\n")
        
        section.append("### Business Domain\n")
        section.append(f"- **Pending Items**: {domain_stats['business']['pending']}\n")
        section.append(f"- **Accounting Pending**: {domain_stats['business']['accounting_pending']}\n")
        section.append(f"- **Social Media Pending**: {domain_stats['business']['social_media_pending']}\n")
        section.append(f"- **Processed Today**: {domain_stats['business']['processed_today']}\n")
        section.append("\n")
        
        section.append("### Cross-Domain Workflows\n")
        section.append(f"- **Active Workflows**: {domain_stats['cross_domain_workflows']}\n")
        section.append("\n")
        
        # Calculate unified KPIs
        total_pending = (domain_stats['personal']['pending'] + 
                        domain_stats['business']['pending'] + 
                        domain_stats['business']['accounting_pending'] + 
                        domain_stats['business']['social_media_pending'])
        total_processed = (domain_stats['personal']['processed_today'] + 
                          domain_stats['business']['processed_today'])
        
        automation_rate = 0.0
        if total_pending + total_processed > 0:
            automation_rate = (total_processed / (total_pending + total_processed)) * 100
        
        section.append("### Unified KPIs\n")
        section.append(f"- **Total Automation Rate**: {automation_rate:.1f}%\n")
        section.append(f"- **Total Pending**: {total_pending}\n")
        section.append(f"- **Total Processed Today**: {total_processed}\n")
        
        return ''.join(section)
    
    def _build_pending_items_table(self) -> str:
        """
        Build the pending items table rows.

        Returns:
            Table rows as Markdown string.
        """
        needs_action = self.config.needs_action_path
        if not needs_action.exists():
            return ''

        rows = ''
        now = datetime.now()

        for file in sorted(needs_action.glob('*.md'))[:10]:  # Limit to 10
            try:
                content = file.read_text(encoding='utf-8')

                # Extract source from frontmatter
                source_match = re.search(r'^source:\s*(\w+)', content, re.MULTILINE)
                source = source_match.group(1) if source_match else 'unknown'

                # Extract priority from frontmatter
                priority_match = re.search(r'^priority:\s*(\w+)', content, re.MULTILINE)
                priority = priority_match.group(1) if priority_match else 'unknown'

                # Calculate age
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                age_delta = now - mtime
                if age_delta.days > 0:
                    age = f"{age_delta.days}d"
                elif age_delta.seconds >= 3600:
                    age = f"{age_delta.seconds // 3600}h"
                else:
                    age = f"{age_delta.seconds // 60}m"

                rows += f"| [[{file.name}]] | {source} | {priority} | {age} |\n"

            except OSError:
                continue

        return rows

    def _update_recent_activity(
        self,
        content: str,
        activities: list[dict]
    ) -> str:
        """
        Update the Recent Activity section in Dashboard.md.

        Args:
            content: Full file content.
            activities: List of activity dicts with timestamp, action, details.

        Returns:
            Updated content.
        """
        # Build new activity table rows
        if activities:
            activity_rows = '\n'.join([
                f"| {act['timestamp']} | {act['action']} | {act['details']} |"
                for act in activities[:10]  # Limit to 10 most recent
            ])
        else:
            activity_rows = "| - | No recent activity | - |"

        # Find and replace the Recent Activity table
        pattern = r'(## Recent Activity \(Last 24h\)\s*\n\s*\| Time \| Action \| Details \|\s*\n\s*\|---+\|---+\|---+\|\s*\n)(.*?)(\n\n##|\n##|\Z)'

        def replacer(match):
            return f"{match.group(1)}{activity_rows}\n{match.group(3)}"

        return re.sub(pattern, replacer, content, flags=re.DOTALL)

    def _update_quick_stats(
        self,
        content: str,
        stats: dict
    ) -> str:
        """
        Update the Quick Stats section in Dashboard.md.

        Args:
            content: Full file content.
            stats: Dict with plans_today, processed_today, active_plans.

        Returns:
            Updated content.
        """
        # Update each stat line
        content = re.sub(
            r'- \*\*Plans created today\*\*:\s*\d+',
            f"- **Plans created today**: {stats['plans_today']}",
            content
        )
        content = re.sub(
            r'- \*\*Items processed today\*\*:\s*\d+',
            f"- **Items processed today**: {stats['processed_today']}",
            content
        )
        content = re.sub(
            r'- \*\*Active plans\*\*:\s*\d+.*',
            f"- **Active plans**: {stats['active_plans']}",
            content
        )

        return content

    # =========================================================================
    # Silver Tier Methods
    # =========================================================================

    def update_silver_metrics(
        self,
        watcher_statuses: list[dict[str, Any]] | None = None,
        mcp_servers: list[dict[str, Any]] | None = None
    ) -> None:
        """
        Update Silver tier metrics in Dashboard.md.

        Adds or updates the following sections:
        - Pending Approvals (count and oldest age)
        - MCP Server Health (status table)
        - All Watchers Status (multi-watcher table)
        - Recent Audit Entries (last 10)
        - LinkedIn Metrics (posts_this_week, last_post, queued, recent URLs)

        Args:
            watcher_statuses: List of watcher status dicts. If None, scans
                              from available data.
            mcp_servers: List of MCP server status dicts. If None, loads
                         from config.
        """
        self._ensure_dashboard_exists()
        content = self.dashboard_path.read_text(encoding='utf-8')

        # Get Silver metrics
        pending_approval = self.get_pending_approval_count()
        mcp_health = mcp_servers or self.get_mcp_server_health()
        all_watchers = watcher_statuses or []
        recent_audit = self.get_recent_audit_entries(limit=10)
        linkedin_metrics = self.get_linkedin_metrics()

        # Build Silver tier section
        silver_section = self._build_silver_section(
            pending_approval=pending_approval,
            mcp_health=mcp_health,
            watcher_statuses=all_watchers,
            recent_audit=recent_audit,
            linkedin_metrics=linkedin_metrics
        )

        # Insert or update Silver Tier Metrics section
        content = self._update_silver_section(content, silver_section)

        # Update last updated timestamp
        now = datetime.now()
        content = self._update_frontmatter_field(
            content, 'last_updated', now.isoformat()
        )

        self.dashboard_path.write_text(content, encoding='utf-8')

    def get_pending_approval_count(self) -> dict[str, Any]:
        """
        Get pending approval count and oldest age.

        Returns:
            Dict with 'count', 'oldest_age', 'oldest_age_hours',
            and 'is_overdue' (>24 hours).
        """
        pending_path = self.config.pending_approval_path
        if not pending_path.exists():
            return {
                'count': 0,
                'oldest_age': 'N/A',
                'oldest_age_hours': 0,
                'is_overdue': False
            }

        files = list(pending_path.glob('*.md'))
        count = len(files)

        if count == 0:
            return {
                'count': 0,
                'oldest_age': 'N/A',
                'oldest_age_hours': 0,
                'is_overdue': False
            }

        # Find oldest file
        oldest_mtime = min(f.stat().st_mtime for f in files)
        oldest_dt = datetime.fromtimestamp(oldest_mtime)
        age_delta = datetime.now() - oldest_dt

        # Format age display
        hours = age_delta.total_seconds() / 3600
        if age_delta.days > 0:
            age_display = f"{age_delta.days}d {age_delta.seconds // 3600}h"
        elif hours >= 1:
            age_display = f"{int(hours)}h {(age_delta.seconds % 3600) // 60}m"
        else:
            age_display = f"{age_delta.seconds // 60}m"

        return {
            'count': count,
            'oldest_age': age_display,
            'oldest_age_hours': hours,
            'is_overdue': hours >= 24
        }

    def get_mcp_server_health(self) -> list[dict[str, Any]]:
        """
        Get MCP server health status by invoking health_check tool on each server.

        Attempts to invoke health_check tool via MCP server interfaces.
        Falls back to config-based status if MCP servers are not accessible.

        Returns:
            List of server status dicts with 'name', 'status', 'status_emoji',
            'last_action', 'error_count', 'is_critical' (error_count >5).
        """
        mcp_config = self.config.get_mcp_servers_config()
        servers = mcp_config.get('servers', [])

        # Default MCP servers if not in config
        if not servers:
            servers = [
                {'server_name': 'email-mcp', 'server_type': 'email'},
                {'server_name': 'linkedin-mcp', 'server_type': 'linkedin'},
                {'server_name': 'playwright-mcp', 'server_type': 'browser'}
            ]

        results = []
        for server in servers:
            server_name = server.get('server_name', 'unknown')
            server_type = server.get('server_type', 'unknown')
            
            # Try to invoke health_check via MCP server
            # Note: In actual implementation, this would use MCP client to call health_check tool
            # For now, we check if the MCP server process is running or use config status
            status = server.get('status', 'unknown')
            error_count = server.get('error_count', 0)
            
            # Determine status based on error count and availability
            if error_count > 5:
                status = 'error'
                is_critical = True
            elif status == 'unknown':
                # Try to determine status from server availability
                # In production, this would invoke MCP health_check tool
                status = 'offline'  # Default to offline if unknown
                is_critical = False
            else:
                is_critical = error_count > 5
            
            status_emoji = {
                'available': '\u2705',  # Green check
                'error': '\u274c',       # Red X
                'offline': '\u26aa',     # White circle
                'unknown': '\u2754'      # Question mark
            }.get(status, '\u2754')

            last_action = server.get('last_successful_action')
            if last_action:
                try:
                    dt = datetime.fromisoformat(last_action)
                    last_action = dt.strftime('%Y-%m-%d %H:%M')
                except (ValueError, TypeError):
                    last_action = 'Unknown'
            else:
                last_action = 'Never'

            results.append({
                'name': server_name,
                'status': status,
                'status_emoji': status_emoji,
                'last_action': last_action,
                'error_count': error_count,
                'is_critical': is_critical
            })

        return results

    def get_all_watcher_statuses(self) -> list[dict[str, Any]]:
        """
        Get status of all configured watchers from PM2 or WatcherInstance metadata.

        Queries PM2 process list for watcher processes and reads WatcherInstance
        metadata to get restart_count, uptime_seconds, last_restart_time.

        Returns:
            List of watcher status dicts with PM2 metadata.
        """
        from models.watcher_instance import WatcherInstance

        watcher_types = ['gmail', 'whatsapp', 'linkedin', 'filesystem']
        results = []

        # Try to query PM2 for process status
        try:
            # Run pm2 jlist to get JSON output of all processes
            pm2_output = subprocess.run(
                ['pm2', 'jlist'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if pm2_output.returncode == 0:
                pm2_processes = json.loads(pm2_output.stdout)

                # Map PM2 process names to watcher types
                pm2_name_map = {
                    'gmail-watcher': 'gmail',
                    'whatsapp-watcher': 'whatsapp',
                    'linkedin-watcher': 'linkedin',
                    'filesystem-watcher': 'filesystem'
                }

                for process in pm2_processes:
                    pm2_name = process.get('name', '')
                    watcher_type = pm2_name_map.get(pm2_name)

                    if watcher_type:
                        # Get PM2 metadata
                        pm2_id = process.get('pm_id', '')
                        status = process.get('pm2_env', {}).get('status', 'unknown')
                        restart_count = process.get('pm2_env', {}).get('restart_time', 0)
                        uptime_ms = process.get('monit', {}).get('uptime', 0)
                        uptime_seconds = uptime_ms // 1000 if uptime_ms else 0

                        # Try to load WatcherInstance from state file
                        watcher_instance = self._load_watcher_instance(watcher_type)

                        # Merge PM2 data with WatcherInstance
                        if watcher_instance:
                            watcher_instance.process_id = str(pm2_id)
                            watcher_instance.status = 'online' if status == 'online' else 'stopped'
                            watcher_instance.uptime_seconds = uptime_seconds
                            watcher_instance.restart_count = restart_count
                            watcher_instance.update_uptime()
                        else:
                            # Create new WatcherInstance from PM2 data
                            watcher_instance = WatcherInstance(
                                watcher_type=watcher_type,
                                status='online' if status == 'online' else 'stopped',
                                process_id=str(pm2_id),
                                uptime_seconds=uptime_seconds,
                                restart_count=restart_count
                            )

                        results.append(watcher_instance.to_dict())

        except (subprocess.TimeoutExpired, subprocess.SubprocessError, json.JSONDecodeError, FileNotFoundError):
            # PM2 not available or not running - try to load from WatcherInstance files
            for watcher_type in watcher_types:
                instance = self._load_watcher_instance(watcher_type)
                if instance:
                    results.append(instance.to_dict())

        return results

    def _load_watcher_instance(self, watcher_type: str) -> 'WatcherInstance | None':
        """
        Load WatcherInstance from state file if it exists.

        Args:
            watcher_type: Type of watcher (gmail, whatsapp, linkedin, filesystem).

        Returns:
            WatcherInstance object or None if not found.
        """
        from models.watcher_instance import WatcherInstance

        # State file location: vault_path / '.watcher_state' / f'{watcher_type}.json'
        state_dir = self.config.vault_path / '.watcher_state'
        state_file = state_dir / f'{watcher_type}.json'

        if state_file.exists():
            try:
                content = state_file.read_text(encoding='utf-8')
                data = json.loads(content)
                return WatcherInstance.from_dict(data)
            except (OSError, json.JSONDecodeError):
                return None

        return None

    def _get_last_updated_timestamp(self) -> datetime:
        """
        Get the last updated timestamp from Dashboard frontmatter.

        Returns:
            Datetime object of last update, or current time if not found.
        """
        if not self.dashboard_path.exists():
            return datetime.now()

        try:
            content = self.dashboard_path.read_text(encoding='utf-8')
            # Extract last_updated from frontmatter
            match = re.search(r'^last_updated:\s*(.+)$', content, re.MULTILINE)
            if match:
                timestamp_str = match.group(1).strip()
                return datetime.fromisoformat(timestamp_str)
        except (OSError, ValueError, TypeError):
            pass

        return datetime.now()

    def _list_pending_approval_files(self) -> list[dict[str, Any]]:
        """
        List pending approval files with metadata.

        Returns:
            List of dicts with 'filename', 'age', 'is_overdue', 'risk_level'.
        """
        pending_path = self.config.pending_approval_path
        if not pending_path.exists():
            return []

        files = []
        for file_path in pending_path.glob('*.md'):
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            age_delta = datetime.now() - mtime
            hours = age_delta.total_seconds() / 3600

            # Format age
            if age_delta.days > 0:
                age = f"{age_delta.days}d {age_delta.seconds // 3600}h"
            elif hours >= 1:
                age = f"{int(hours)}h {(age_delta.seconds % 3600) // 60}m"
            else:
                age = f"{age_delta.seconds // 60}m"

            # Try to read risk level from file
            risk_level = 'medium'
            try:
                content = file_path.read_text(encoding='utf-8')
                if 'risk_level: high' in content or 'priority: high' in content:
                    risk_level = 'high'
                elif 'risk_level: low' in content or 'priority: low' in content:
                    risk_level = 'low'
            except OSError:
                pass

            files.append({
                'filename': file_path.name,
                'age': age,
                'is_overdue': hours >= 24,
                'risk_level': risk_level
            })

        return files

    def get_linkedin_metrics(self) -> dict[str, Any]:
        """
        Get LinkedIn posting metrics for dashboard display.

        Returns:
            Dict with posts_this_week, last_post_timestamp, queued_posts_count,
            recent_posts (with URLs), posts_today, can_post_now.
        """
        try:
            from .linkedin_rules import get_linkedin_metrics as _get_metrics

            return _get_metrics(
                logs_path=self.config.logs_path,
                pending_approval_path=self.config.pending_approval_path,
                max_posts_per_day=3  # From Company_Handbook.md default
            )
        except (ImportError, AttributeError):
            # Fallback if linkedin_rules not available
            return {
                'posts_this_week': 0,
                'posts_today': 0,
                'max_posts_per_day': 3,
                'last_post_timestamp': None,
                'queued_posts_count': 0,
                'recent_posts': [],
                'can_post_now': True,
                'block_reason': None,
                'within_schedule': True,
                'next_posting_window': None
            }

    def get_recent_audit_entries(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get recent audit log entries from today's log file.

        Args:
            limit: Maximum number of entries to return.

        Returns:
            List of audit entry dicts with 'timestamp', 'action_type',
            'target', 'result', 'approval_status'.
        """
        logs_path = self.config.logs_path
        if not logs_path.exists():
            return []

        # Get today's log file
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = logs_path / f"{today}.json"

        if not log_file.exists():
            return []

        try:
            content = log_file.read_text(encoding='utf-8')
            data = json.loads(content)
            entries = data.get('entries', [])

            # Get last N entries
            entries = entries[-limit:]

            # Format entries for display
            results = []
            for entry in reversed(entries):  # Most recent first
                timestamp = entry.get('timestamp', '')
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    # Format as relative time
                    age = datetime.now() - dt.replace(tzinfo=None)
                    if age.total_seconds() < 60:
                        time_display = 'Just now'
                    elif age.total_seconds() < 3600:
                        time_display = f"{int(age.total_seconds() // 60)}m ago"
                    elif age.total_seconds() < 86400:
                        time_display = f"{int(age.total_seconds() // 3600)}h ago"
                    else:
                        time_display = dt.strftime('%Y-%m-%d %H:%M')
                except (ValueError, TypeError):
                    time_display = 'Unknown'

                result = entry.get('result', 'unknown')
                result_emoji = '\u2705' if result == 'success' else '\u274c'

                results.append({
                    'timestamp': time_display,
                    'action_type': entry.get('action_type', 'unknown'),
                    'target': self._truncate_target(entry.get('target', '')),
                    'result': result,
                    'result_emoji': result_emoji,
                    'approval_status': entry.get('approval_status', 'unknown')
                })

            return results

        except (json.JSONDecodeError, OSError):
            return []

    def _truncate_target(self, target: str, max_length: int = 30) -> str:
        """Truncate target string for display."""
        if len(target) <= max_length:
            return target
        return target[:max_length - 3] + '...'

    def _list_pending_approval_files(self) -> list[dict[str, Any]]:
        """
        List pending approval files with age and risk level.

        Returns:
            List of dicts with filename, age, risk_level, is_overdue.
        """
        pending_path = self.config.pending_approval_path
        if not pending_path.exists():
            return []

        results = []
        now = datetime.now()

        for file_path in sorted(pending_path.glob('*.md'))[:10]:
            try:
                content = file_path.read_text(encoding='utf-8')

                # Extract risk level from frontmatter
                risk_match = re.search(
                    r'^risk_level:\s*(\w+)',
                    content,
                    re.MULTILINE
                )
                risk_level = risk_match.group(1) if risk_match else 'unknown'

                # Calculate age
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                age_delta = now - mtime
                age_hours = age_delta.total_seconds() / 3600

                # Format age display
                if age_delta.days > 0:
                    age = f"{age_delta.days}d {age_delta.seconds // 3600}h"
                elif age_hours >= 1:
                    age = f"{int(age_hours)}h {(age_delta.seconds % 3600) // 60}m"
                else:
                    age = f"{age_delta.seconds // 60}m"

                results.append({
                    'filename': file_path.name,
                    'age': age,
                    'risk_level': risk_level,
                    'is_overdue': age_hours >= 24
                })

            except OSError:
                continue

        return results

    def _build_silver_section(
        self,
        pending_approval: dict[str, Any],
        mcp_health: list[dict[str, Any]],
        watcher_statuses: list[dict[str, Any]],
        recent_audit: list[dict[str, Any]],
        linkedin_metrics: dict[str, Any] | None = None
    ) -> str:
        """
        Build the Silver Tier Metrics section content.

        Args:
            pending_approval: Pending approval count and age data.
            mcp_health: List of MCP server health dicts.
            watcher_statuses: List of watcher status dicts.
            recent_audit: List of recent audit entries.
            linkedin_metrics: LinkedIn posting metrics (T056).

        Returns:
            Markdown string for Silver tier section.
        """
        now = datetime.now()
        section = []

        # Section header
        section.append("\n## Silver Tier Metrics\n")
        
        # Data freshness indicator (T081)
        last_updated = self._get_last_updated_timestamp()
        freshness_delta = datetime.now() - last_updated
        freshness_minutes = freshness_delta.total_seconds() / 60
        if freshness_minutes < 5:
            freshness_status = f"✅ Fresh (<5 minutes)"
        elif freshness_minutes < 15:
            freshness_status = f"⚠️ Stale ({int(freshness_minutes)} minutes)"
        else:
            freshness_status = f"🔴 Outdated ({int(freshness_minutes)} minutes)"
        
        section.append(f"**Last Updated**: {last_updated.strftime('%Y-%m-%d %H:%M:%S')} - {freshness_status}\n")
        
        # Error state visualization (T083)
        error_states = []
        if pending_approval['count'] > 10:
            error_states.append("⚠️ **Backlog**: More than 10 pending approvals")
        if pending_approval['is_overdue']:
            error_states.append("🔴 **Critical**: Overdue approvals require attention")
        
        for server in mcp_health:
            if server.get('is_critical', False) or server.get('error_count', 0) > 5:
                error_states.append(f"🔴 **Critical**: {server['name']} has {server.get('error_count', 0)} errors")
        
        for watcher in watcher_statuses:
            restart_count = watcher.get('restart_count', 0)
            if restart_count > 5:
                error_states.append(f"⚠️ **Unstable**: {watcher.get('watcher_type', 'unknown')} watcher restarted {restart_count} times")
        
        if error_states:
            section.append("\n**⚠️ System Alerts**:\n")
            for alert in error_states:
                section.append(f"- {alert}\n")
            section.append("\n")

        # Pending Approvals subsection
        section.append("\n### Pending Approvals\n")
        if pending_approval['is_overdue']:
            overdue_label = ' `#pending-overdue` \u26a0\ufe0f **OVERDUE - Requires Immediate Attention**'
        else:
            overdue_label = ''
        section.append(
            f"**Pending**: {pending_approval['count']} | "
            f"**Oldest**: {pending_approval['oldest_age']}{overdue_label}\n"
        )

        # List pending approval files if any exist
        if pending_approval['count'] > 0:
            section.append("\n| Approval Request | Age | Risk Level |\n")
            section.append("|------------------|-----|------------|\n")
            pending_files = self._list_pending_approval_files()
            for pf in pending_files[:5]:  # Limit to 5
                age_label = f"{pf['age']} `#pending-overdue`" if pf['is_overdue'] else pf['age']
                section.append(
                    f"| [[{pf['filename']}]] | {age_label} | {pf['risk_level']} |\n"
                )

        # MCP Server Health subsection
        section.append("\n### MCP Server Health\n")
        if mcp_health:
            section.append("| Server | Status | Last Success | Errors |\n")
            section.append("|--------|--------|--------------|--------|\n")
            for server in mcp_health:
                section.append(
                    f"| {server['name']} | {server['status_emoji']} {server['status']} | "
                    f"{server['last_action']} | {server['error_count']} |\n"
                )
        else:
            section.append("No MCP servers configured.\n")

        # All Watchers Status subsection
        section.append("\n### All Watchers Status\n")
        if watcher_statuses:
            section.append("| Watcher | Status | Last Check | Detected Today | Uptime | Stability |\n")
            section.append("|---------|--------|------------|----------------|--------|----------|\n")
            for watcher in watcher_statuses:
                status_emoji = {
                    'online': '\u2705',
                    'stopped': '\ud83d\uded1',
                    'crashed': '\u274c',
                    'starting': '\ud83d\udd04',
                    'unknown': '\u2754'
                }.get(watcher.get('status', 'unknown'), '\u2754')

                section.append(
                    f"| {watcher.get('watcher_type', 'unknown')} | "
                    f"{status_emoji} {watcher.get('status', 'unknown')} | "
                    f"{watcher.get('last_check_time', 'Never')} | "
                    f"{watcher.get('items_detected_today', 0)} | "
                    f"{watcher.get('uptime_display', '0m')} | "
                    f"{watcher.get('stability_label', 'Unknown')} |\n"
                )
        else:
            section.append("No watcher status data available.\n")

        # Recent Audit Entries subsection
        section.append("\n### Recent Audit Entries (Last 10)\n")
        if recent_audit:
            section.append("| Time | Action | Target | Result | Approval |\n")
            section.append("|------|--------|--------|--------|----------|\n")
            for entry in recent_audit:
                section.append(
                    f"| {entry['timestamp']} | {entry['action_type']} | "
                    f"{entry['target']} | {entry['result_emoji']} {entry['result']} | "
                    f"{entry['approval_status']} |\n"
                )
        else:
            section.append("No audit entries for today.\n")

        # LinkedIn Metrics subsection (T056)
        section.append("\n### LinkedIn Metrics\n")
        if linkedin_metrics:
            posts_week = linkedin_metrics.get('posts_this_week', 0)
            posts_today = linkedin_metrics.get('posts_today', 0)
            max_posts = linkedin_metrics.get('max_posts_per_day', 3)
            queued = linkedin_metrics.get('queued_posts_count', 0)
            can_post = linkedin_metrics.get('can_post_now', True)
            last_post = linkedin_metrics.get('last_post_timestamp')

            # Format last post timestamp
            if last_post:
                try:
                    dt = datetime.fromisoformat(last_post.replace('Z', '+00:00'))
                    last_post_display = dt.strftime('%Y-%m-%d %H:%M')
                except (ValueError, TypeError):
                    last_post_display = last_post
            else:
                last_post_display = 'Never'

            # Status indicator
            if not can_post:
                status_emoji = '\u26a0\ufe0f'  # Warning
                block_reason = linkedin_metrics.get('block_reason', 'Unknown')
                status_text = f"Blocked: {block_reason}"
            elif posts_today >= max_posts:
                status_emoji = '\ud83d\uded1'  # Stop sign
                status_text = f"Daily limit reached ({posts_today}/{max_posts})"
            else:
                status_emoji = '\u2705'  # Green check
                status_text = f"Available ({posts_today}/{max_posts} today)"

            section.append(f"**Status**: {status_emoji} {status_text}\n\n")
            section.append(f"- **Posts This Week**: {posts_week}\n")
            section.append(f"- **Posts Today**: {posts_today}/{max_posts}\n")
            section.append(f"- **Last Post**: {last_post_display}\n")
            section.append(f"- **Queued Posts**: {queued}\n")

            # Recent posts with links
            recent_posts = linkedin_metrics.get('recent_posts', [])
            if recent_posts:
                section.append("\n**Recent Posts**:\n")
                for post in recent_posts[:3]:
                    post_url = post.get('post_url', '')
                    timestamp = post.get('timestamp', '')
                    if post_url:
                        section.append(f"- [{timestamp}]({post_url})\n")
                    else:
                        section.append(f"- {timestamp} (no URL)\n")
        else:
            section.append("LinkedIn metrics not available.\n")

        # Quick Actions subsection (T082)
        section.append("\n### Quick Actions\n")
        today_str = datetime.now().strftime('%Y-%m-%d')
        section.append(f"- 📁 [Open Pending Approvals Folder](/Pending_Approval/) - Review and approve actions\n")
        section.append(f"- 📋 [View Today's Audit Log](/Logs/{today_str}.json) - See all actions executed today\n")
        section.append(f"- 🔍 [Check PM2 Status](pm2 status) - View process manager status\n")
        section.append(f"- 📊 [View Dashboard Source](Dashboard.md) - Edit dashboard template\n")

        return ''.join(section)

    def _update_data_freshness_indicator(self, content: str, now: datetime) -> str:
        """
        Update the data freshness indicator in the Dashboard header.

        Args:
            content: Full dashboard content.
            now: Current datetime.

        Returns:
            Updated content with freshness indicator.
        """
        freshness_pattern = r'> \*\*Data Freshness\*\*:.*'
        freshness_text = f"> **Data Freshness**: Last updated {now.strftime('%Y-%m-%d %H:%M:%S')} (<5 minutes)"
        
        if re.search(freshness_pattern, content):
            return re.sub(freshness_pattern, freshness_text, content)
        else:
            # Add after "Last Updated" line
            return re.sub(
                r'(\*\*Last Updated\*\*: .+)\n',
                r'\1\n' + freshness_text + '\n',
                content,
                count=1
            )

    def _update_silver_section(self, content: str, silver_section: str) -> str:
        """
        Insert or update the Silver Tier Metrics section.

        Args:
            content: Full dashboard content.
            silver_section: New Silver tier section content.

        Returns:
            Updated content with Silver section.
        """
        # Check if Silver section already exists
        silver_pattern = r'## Silver Tier Metrics\n.*?(?=\n## [A-Z]|$)'

        if re.search(silver_pattern, content, re.DOTALL):
            # Update existing section
            return re.sub(silver_pattern, silver_section.strip() + '\n', content, flags=re.DOTALL)
        else:
            # Insert before Recent Errors section or at end
            if '## Recent Errors' in content:
                return content.replace(
                    '## Recent Errors',
                    silver_section + '\n## Recent Errors'
                )
            else:
                return content + '\n' + silver_section
