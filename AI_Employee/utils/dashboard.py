"""
Dashboard updater for Bronze Tier Personal AI Employee.

Manages the Dashboard.md file in the Obsidian vault, providing
real-time status updates and activity tracking.
"""

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

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
