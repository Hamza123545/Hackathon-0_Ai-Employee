"""
LinkedIn posting rules enforcement for Silver Tier Personal AI Employee.

Implements T054 and T055 requirements:
- Daily post limit enforcement (max_posts_per_day)
- Posting schedule enforcement (business hours 9am-5pm)
- Queue management for posts that violate rules
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

from .audit_logger import AuditLogger


class LinkedInPostingRules:
    """
    Enforces LinkedIn posting rules from Company_Handbook.md.

    Features:
    - Counts LinkedIn posts from audit logs
    - Enforces daily post limit (default: 3)
    - Enforces posting schedule (business hours 9am-5pm)
    - Queues posts when limits/schedule violated
    """

    def __init__(
        self,
        logs_path: Path,
        max_posts_per_day: int = 3,
        posting_schedule_start: int = 9,  # 9 AM
        posting_schedule_end: int = 17,   # 5 PM
        timezone_name: str = 'local'
    ):
        """
        Initialize LinkedIn posting rules enforcer.

        Args:
            logs_path: Path to the Logs folder.
            max_posts_per_day: Maximum posts allowed per day.
            posting_schedule_start: Start hour of posting window (24h format).
            posting_schedule_end: End hour of posting window (24h format).
            timezone_name: Timezone for schedule ('local' or timezone name).
        """
        self.logs_path = Path(logs_path)
        self.max_posts_per_day = max_posts_per_day
        self.posting_schedule_start = posting_schedule_start
        self.posting_schedule_end = posting_schedule_end
        self.timezone_name = timezone_name

    def count_linkedin_posts_today(self) -> int:
        """
        Count LinkedIn posts in today's audit log.

        Returns:
            Number of LinkedIn posts made today.
        """
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs_path / f"{today}.json"

        if not log_file.exists():
            return 0

        try:
            content = log_file.read_text(encoding='utf-8')
            data = json.loads(content)
            entries = data.get('entries', [])

            # Count entries with action_type: linkedin_post and result: success
            count = sum(
                1 for entry in entries
                if entry.get('action_type') == 'linkedin_post'
                and entry.get('result') == 'success'
            )
            return count

        except (json.JSONDecodeError, OSError):
            return 0

    def count_linkedin_posts_week(self) -> int:
        """
        Count LinkedIn posts in the last 7 days from audit logs.

        Returns:
            Number of LinkedIn posts in the last 7 days.
        """
        total = 0
        today = datetime.now()

        for days_ago in range(7):
            date = (today - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            log_file = self.logs_path / f"{date}.json"

            if not log_file.exists():
                continue

            try:
                content = log_file.read_text(encoding='utf-8')
                data = json.loads(content)
                entries = data.get('entries', [])

                count = sum(
                    1 for entry in entries
                    if entry.get('action_type') == 'linkedin_post'
                    and entry.get('result') == 'success'
                )
                total += count

            except (json.JSONDecodeError, OSError):
                continue

        return total

    def get_last_post_timestamp(self) -> str | None:
        """
        Get the timestamp of the most recent LinkedIn post.

        Returns:
            ISO timestamp string or None if no posts found.
        """
        today = datetime.now()

        # Check last 7 days for most recent post
        for days_ago in range(7):
            date = (today - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            log_file = self.logs_path / f"{date}.json"

            if not log_file.exists():
                continue

            try:
                content = log_file.read_text(encoding='utf-8')
                data = json.loads(content)
                entries = data.get('entries', [])

                # Find most recent linkedin_post entry
                linkedin_posts = [
                    entry for entry in entries
                    if entry.get('action_type') == 'linkedin_post'
                    and entry.get('result') == 'success'
                ]

                if linkedin_posts:
                    # Return most recent (last in list for same day)
                    return linkedin_posts[-1].get('timestamp')

            except (json.JSONDecodeError, OSError):
                continue

        return None

    def get_recent_post_urls(self, limit: int = 5) -> list[dict[str, str]]:
        """
        Get URLs of recent LinkedIn posts from audit logs.

        Args:
            limit: Maximum number of posts to return.

        Returns:
            List of dicts with 'timestamp', 'post_url', 'post_id'.
        """
        posts = []
        today = datetime.now()

        for days_ago in range(7):
            date = (today - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            log_file = self.logs_path / f"{date}.json"

            if not log_file.exists():
                continue

            try:
                content = log_file.read_text(encoding='utf-8')
                data = json.loads(content)
                entries = data.get('entries', [])

                for entry in reversed(entries):
                    if (entry.get('action_type') == 'linkedin_post'
                            and entry.get('result') == 'success'):
                        post_url = entry.get('post_url', '')
                        post_id = entry.get('post_id', '')

                        # Also check in extra fields or metadata
                        if not post_url:
                            post_url = entry.get('metadata', {}).get('post_url', '')
                        if not post_id:
                            post_id = entry.get('metadata', {}).get('post_id', '')

                        posts.append({
                            'timestamp': entry.get('timestamp', ''),
                            'post_url': post_url,
                            'post_id': post_id
                        })

                        if len(posts) >= limit:
                            return posts

            except (json.JSONDecodeError, OSError):
                continue

        return posts

    def is_within_posting_schedule(self) -> bool:
        """
        Check if current time is within posting schedule.

        Returns:
            True if within business hours, False otherwise.
        """
        now = datetime.now()
        current_hour = now.hour

        return self.posting_schedule_start <= current_hour < self.posting_schedule_end

    def get_next_posting_window(self) -> datetime:
        """
        Get the next available posting window start time.

        Returns:
            Datetime of next available posting time.
        """
        now = datetime.now()
        current_hour = now.hour

        if current_hour < self.posting_schedule_start:
            # Today, at schedule start
            return now.replace(
                hour=self.posting_schedule_start,
                minute=0,
                second=0,
                microsecond=0
            )
        elif current_hour >= self.posting_schedule_end:
            # Tomorrow, at schedule start
            tomorrow = now + timedelta(days=1)
            return tomorrow.replace(
                hour=self.posting_schedule_start,
                minute=0,
                second=0,
                microsecond=0
            )
        else:
            # Within schedule, return now
            return now

    def can_post_now(self) -> tuple[bool, str | None]:
        """
        Check if a LinkedIn post can be made right now.

        Checks both daily limit and schedule constraints.

        Returns:
            Tuple of (can_post, reason_if_blocked).
        """
        # Check daily limit
        posts_today = self.count_linkedin_posts_today()
        if posts_today >= self.max_posts_per_day:
            return False, f"rate_limit_daily_exceeded: {posts_today}/{self.max_posts_per_day} posts today"

        # Check posting schedule
        if not self.is_within_posting_schedule():
            next_window = self.get_next_posting_window()
            return False, f"outside_posting_schedule: next window at {next_window.strftime('%Y-%m-%d %H:%M')}"

        return True, None

    def check_and_enforce(
        self,
        logger: AuditLogger | None = None
    ) -> dict[str, Any]:
        """
        Check posting rules and return enforcement status.

        Args:
            logger: Optional AuditLogger to log rate limit events.

        Returns:
            Dict with 'can_post', 'reason', 'posts_today', 'next_window', etc.
        """
        can_post, reason = self.can_post_now()
        posts_today = self.count_linkedin_posts_today()
        posts_this_week = self.count_linkedin_posts_week()

        result = {
            'can_post': can_post,
            'reason': reason,
            'posts_today': posts_today,
            'posts_this_week': posts_this_week,
            'max_posts_per_day': self.max_posts_per_day,
            'within_schedule': self.is_within_posting_schedule(),
            'current_hour': datetime.now().hour,
            'schedule_start': self.posting_schedule_start,
            'schedule_end': self.posting_schedule_end
        }

        if not can_post:
            result['next_window'] = self.get_next_posting_window().isoformat()
            result['queue_until'] = result['next_window']

            # Log rate limit event if logger provided
            if logger and 'rate_limit_daily_exceeded' in (reason or ''):
                logger.log_execution(
                    action_type='linkedin_post',
                    actor='system',
                    target='LinkedIn',
                    parameters={'posts_today': posts_today, 'limit': self.max_posts_per_day},
                    approval_status='not_required',
                    result='failure',
                    error=reason,
                    error_code='RATE_LIMIT_DAILY_EXCEEDED'
                )

        return result


def count_queued_linkedin_posts(pending_approval_path: Path) -> int:
    """
    Count LinkedIn posts currently queued in Pending_Approval.

    Args:
        pending_approval_path: Path to Pending_Approval folder.

    Returns:
        Number of queued LinkedIn post approval requests.
    """
    if not pending_approval_path.exists():
        return 0

    count = 0
    for file_path in pending_approval_path.glob('APPROVAL_linkedin_post_*.md'):
        try:
            content = file_path.read_text(encoding='utf-8')
            # Check if it has status: queued or is a linkedin_post type
            if 'action_type: linkedin_post' in content or 'action: linkedin_post' in content:
                count += 1
        except OSError:
            continue

    return count


def get_linkedin_metrics(
    logs_path: Path,
    pending_approval_path: Path,
    max_posts_per_day: int = 3
) -> dict[str, Any]:
    """
    Get comprehensive LinkedIn metrics for dashboard display.

    Args:
        logs_path: Path to Logs folder.
        pending_approval_path: Path to Pending_Approval folder.
        max_posts_per_day: Maximum posts allowed per day.

    Returns:
        Dict with posts_this_week, last_post_timestamp, queued_posts_count,
        recent_posts (with URLs), posts_today, can_post_now.
    """
    rules = LinkedInPostingRules(
        logs_path=logs_path,
        max_posts_per_day=max_posts_per_day
    )

    can_post, block_reason = rules.can_post_now()

    return {
        'posts_this_week': rules.count_linkedin_posts_week(),
        'posts_today': rules.count_linkedin_posts_today(),
        'max_posts_per_day': max_posts_per_day,
        'last_post_timestamp': rules.get_last_post_timestamp(),
        'queued_posts_count': count_queued_linkedin_posts(pending_approval_path),
        'recent_posts': rules.get_recent_post_urls(limit=5),
        'can_post_now': can_post,
        'block_reason': block_reason,
        'within_schedule': rules.is_within_posting_schedule(),
        'next_posting_window': rules.get_next_posting_window().isoformat() if not can_post else None
    }


def handle_linkedin_auth_expired(
    needs_action_path: Path,
    approval_file_path: Path | None = None,
    error_message: str = 'LinkedIn OAuth token has expired'
) -> Path:
    """
    Handle LinkedIn AUTH_EXPIRED error by creating a notification.

    Implements T057 requirements:
    - Create notification in /Needs_Action/ with refresh instructions
    - Post remains in /Approved/ for retry after credential refresh

    Args:
        needs_action_path: Path to Needs_Action folder.
        approval_file_path: Path to the approval file that failed (optional).
        error_message: Error message from LinkedIn API.

    Returns:
        Path to the created notification file.
    """
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    filename = f"action-linkedin-auth-expired-{timestamp}.md"
    file_path = needs_action_path / filename

    # Build notification content
    approval_ref = ''
    if approval_file_path:
        approval_ref = f"\n- **Failed Approval**: [[{approval_file_path.name}]]"

    content = f"""---
type: notification
source: linkedin-mcp
priority: high
created: {datetime.now().isoformat()}
status: pending
category: credential_expiration
---

## LinkedIn OAuth Token Expired

**Error**: {error_message}

**Action Required**: Refresh LinkedIn OAuth credentials

### Instructions to Refresh Credentials

1. **Navigate to LinkedIn Developer Portal**:
   - Go to https://www.linkedin.com/developers/apps
   - Select your application

2. **Generate New Access Token**:
   - Go to "Auth" tab
   - Click "Generate token" or use OAuth 2.0 flow
   - Ensure these scopes are selected:
     - `openid`
     - `profile`
     - `email`
     - `w_member_social` (for posting)

3. **Update Environment Variable**:
   - Copy the new access token
   - Update `LINKEDIN_ACCESS_TOKEN` in `.env` file:
     ```
     LINKEDIN_ACCESS_TOKEN=AQV...your_new_token...
     ```

4. **Verify Token**:
   - Run health check on linkedin-mcp
   - Verify token_valid: true in response

5. **Retry Failed Posts**:
   - Any posts in `/Approved/` will be retried automatically
   - Check Dashboard for queued posts status

### Token Expiration Notes

- LinkedIn OAuth tokens expire after **60 days**
- Set a calendar reminder to refresh before expiration
- Consider implementing OAuth refresh token flow for auto-renewal

### Related Files
{approval_ref}
- **MCP Server**: `AI_Employee/mcp_servers/linkedin_mcp.py`
- **Config**: `.env` (LINKEDIN_ACCESS_TOKEN)

### Metadata

- **Generated At**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Error Code**: AUTH_EXPIRED
- **Recovery**: Manual credential refresh required
"""

    # Ensure directory exists and write file
    needs_action_path.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding='utf-8')

    return file_path


def check_linkedin_auth_error(error_code: str | None, error_message: str | None) -> bool:
    """
    Check if an error indicates LinkedIn authentication has expired.

    Args:
        error_code: Error code from MCP server.
        error_message: Error message from MCP server.

    Returns:
        True if this is an auth expiration error.
    """
    if error_code == 'AUTH_EXPIRED':
        return True

    if error_message:
        auth_keywords = [
            'token expired',
            'invalid token',
            'unauthorized',
            'authentication failed',
            '401',
            '403'
        ]
        error_lower = error_message.lower()
        return any(kw in error_lower for kw in auth_keywords)

    return False
