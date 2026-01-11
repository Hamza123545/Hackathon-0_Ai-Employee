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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from .config import Config


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

        # Build Silver tier section
        silver_section = self._build_silver_section(
            pending_approval=pending_approval,
            mcp_health=mcp_health,
            watcher_statuses=all_watchers,
            recent_audit=recent_audit
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
        Get MCP server health status from config.

        Returns:
            List of server status dicts with 'name', 'status', 'status_emoji',
            'last_action', 'error_count'.
        """
        mcp_config = self.config.get_mcp_servers_config()
        servers = mcp_config.get('servers', [])

        results = []
        for server in servers:
            status = server.get('status', 'unknown')
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
                'name': server.get('server_name', 'unknown'),
                'status': status,
                'status_emoji': status_emoji,
                'last_action': last_action,
                'error_count': server.get('error_count', 0)
            })

        return results

    def get_all_watcher_statuses(self) -> list[dict[str, Any]]:
        """
        Get status of all configured watchers.

        Note: This is a placeholder that returns data from PM2 or
        stored watcher state. In production, this would query PM2
        process list or read from a state file.

        Returns:
            List of watcher status dicts.
        """
        # Placeholder - in production, query PM2 or read state file
        # For now, return empty list (to be populated by caller)
        return []

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
        recent_audit: list[dict[str, Any]]
    ) -> str:
        """
        Build the Silver Tier Metrics section content.

        Args:
            pending_approval: Pending approval count and age data.
            mcp_health: List of MCP server health dicts.
            watcher_statuses: List of watcher status dicts.
            recent_audit: List of recent audit entries.

        Returns:
            Markdown string for Silver tier section.
        """
        now = datetime.now()
        section = []

        # Section header
        section.append("\n## Silver Tier Metrics\n")
        section.append(f"**Last Updated**: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")

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

        return ''.join(section)

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
