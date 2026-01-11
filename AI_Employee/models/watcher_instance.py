"""
Watcher instance model for Silver Tier Personal AI Employee.

Defines the WatcherInstance dataclass for tracking running watcher
processes, their status, and runtime metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Literal


WatcherType = Literal['gmail', 'whatsapp', 'linkedin', 'filesystem']
WatcherStatus = Literal['online', 'stopped', 'crashed', 'starting', 'unknown']


@dataclass
class WatcherHealth:
    """
    Health metrics for a watcher instance.

    Attributes:
        last_error: Last error message (None if healthy).
        last_error_time: When the last error occurred.
        consecutive_errors: Count of consecutive errors (0 if healthy).
    """

    last_error: str | None = None
    last_error_time: datetime | None = None
    consecutive_errors: int = 0

    def record_error(self, error: str) -> None:
        """Record an error occurrence."""
        self.last_error = error
        self.last_error_time = datetime.now()
        self.consecutive_errors += 1

    def clear_errors(self) -> None:
        """Clear error state after successful operation."""
        self.consecutive_errors = 0

    def is_healthy(self) -> bool:
        """Check if the watcher is in a healthy state."""
        return self.consecutive_errors == 0


@dataclass
class WatcherConfig:
    """
    Configuration for a watcher instance.

    Attributes:
        check_interval_seconds: How often to poll (default: 5 minutes).
        enabled: Whether the watcher is enabled.
        source_specific_config: Source-specific settings.
    """

    check_interval_seconds: int = 300
    enabled: bool = True
    source_specific_config: dict[str, Any] = field(default_factory=dict)


@dataclass
class WatcherInstance:
    """
    Represents a running watcher process.

    Tracks the status, metrics, and health of a watcher that monitors
    a specific source (Gmail, WhatsApp, LinkedIn, filesystem) for
    new action items.

    Attributes:
        watcher_type: Type of watcher (gmail, whatsapp, linkedin, filesystem).
        status: Current watcher status.
        process_id: PM2 process ID or OS PID.
        last_check_time: When watcher last polled source.
        items_detected_today: Count of items detected since midnight.
        items_detected_total: Total count since watcher start.
        uptime_seconds: How long watcher has been running.
        restart_count: Number of times PM2 has restarted this watcher.
        last_restart_time: When last restart occurred.
        last_restart_reason: Why watcher restarted.
        config: Watcher configuration.
        health: Health metrics.
        start_time: When the watcher was started.
    """

    watcher_type: WatcherType
    status: WatcherStatus = 'unknown'
    process_id: str = ''
    last_check_time: datetime | None = None
    items_detected_today: int = 0
    items_detected_total: int = 0
    uptime_seconds: int = 0
    restart_count: int = 0
    last_restart_time: datetime | None = None
    last_restart_reason: str | None = None
    config: WatcherConfig = field(default_factory=WatcherConfig)
    health: WatcherHealth = field(default_factory=WatcherHealth)
    start_time: datetime | None = None

    def is_online(self) -> bool:
        """
        Check if the watcher is currently running.

        Returns:
            True if status is 'online'.
        """
        return self.status == 'online'

    def is_healthy(self) -> bool:
        """
        Check if the watcher is healthy (online with no recent errors).

        Returns:
            True if online and health.is_healthy().
        """
        return self.is_online() and self.health.is_healthy()

    def update_uptime(self) -> None:
        """
        Update the uptime based on start_time.

        Should be called periodically to keep uptime current.
        """
        if self.start_time:
            delta = datetime.now() - self.start_time
            self.uptime_seconds = int(delta.total_seconds())

    def get_uptime_display(self) -> str:
        """
        Get human-readable uptime string.

        Returns:
            Uptime in format like "24h 15m" or "2d 3h".
        """
        if self.uptime_seconds <= 0:
            return '0m'

        delta = timedelta(seconds=self.uptime_seconds)
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes = remainder // 60

        if days > 0:
            return f"{days}d {hours}h"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    def record_check(self, items_detected: int = 0) -> None:
        """
        Record a successful check cycle.

        Args:
            items_detected: Number of items detected in this cycle.
        """
        self.last_check_time = datetime.now()
        self.items_detected_today += items_detected
        self.items_detected_total += items_detected
        self.health.clear_errors()
        self.update_uptime()

    def record_restart(self, reason: str = 'unknown') -> None:
        """
        Record a restart event.

        Args:
            reason: Why the watcher restarted.
        """
        self.restart_count += 1
        self.last_restart_time = datetime.now()
        self.last_restart_reason = reason
        self.status = 'starting'

    def record_start(self, process_id: str = '') -> None:
        """
        Record watcher start.

        Args:
            process_id: PM2 process ID or OS PID.
        """
        self.status = 'online'
        self.process_id = process_id
        self.start_time = datetime.now()
        self.uptime_seconds = 0

    def record_stop(self) -> None:
        """Record watcher stop."""
        self.status = 'stopped'
        self.update_uptime()

    def record_crash(self, error: str = '') -> None:
        """
        Record watcher crash.

        Args:
            error: Error message from the crash.
        """
        self.status = 'crashed'
        self.health.record_error(error)
        self.update_uptime()

    def reset_daily_count(self) -> None:
        """Reset the daily items counter (call at midnight)."""
        self.items_detected_today = 0

    def get_status_emoji(self) -> str:
        """
        Get status emoji for dashboard display.

        Returns:
            Emoji representing the current status.
        """
        status_emojis = {
            'online': '\u2705',      # Green check
            'stopped': '\ud83d\uded1',  # Stop sign
            'crashed': '\u274c',     # Red X
            'starting': '\ud83d\udd04',  # Rotating arrows
            'unknown': '\u2754'      # Question mark
        }
        return status_emojis.get(self.status, '\u2754')

    def get_stability_label(self) -> str:
        """
        Get stability label based on restart count.

        Returns:
            Stability label string.
        """
        if self.restart_count == 0:
            return 'Stable'
        elif self.restart_count <= 3:
            return 'Minor restarts'
        elif self.restart_count <= 5:
            return '\u26a0\ufe0f Unstable'
        else:
            return '\ud83d\udd34 Critical'

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the watcher instance.
        """
        return {
            'watcher_type': self.watcher_type,
            'status': self.status,
            'process_id': self.process_id,
            'last_check_time': (
                self.last_check_time.isoformat()
                if self.last_check_time else None
            ),
            'items_detected_today': self.items_detected_today,
            'items_detected_total': self.items_detected_total,
            'uptime_seconds': self.uptime_seconds,
            'uptime_display': self.get_uptime_display(),
            'restart_count': self.restart_count,
            'last_restart_time': (
                self.last_restart_time.isoformat()
                if self.last_restart_time else None
            ),
            'last_restart_reason': self.last_restart_reason,
            'config': {
                'check_interval_seconds': self.config.check_interval_seconds,
                'enabled': self.config.enabled,
                'source_specific_config': self.config.source_specific_config
            },
            'health': {
                'last_error': self.health.last_error,
                'last_error_time': (
                    self.health.last_error_time.isoformat()
                    if self.health.last_error_time else None
                ),
                'consecutive_errors': self.health.consecutive_errors
            }
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'WatcherInstance':
        """
        Create a WatcherInstance from a dictionary.

        Args:
            data: Dictionary with watcher data.

        Returns:
            WatcherInstance object.
        """
        config_data = data.get('config', {})
        health_data = data.get('health', {})

        config = WatcherConfig(
            check_interval_seconds=config_data.get('check_interval_seconds', 300),
            enabled=config_data.get('enabled', True),
            source_specific_config=config_data.get('source_specific_config', {})
        )

        health = WatcherHealth(
            last_error=health_data.get('last_error'),
            last_error_time=(
                datetime.fromisoformat(health_data['last_error_time'])
                if health_data.get('last_error_time') else None
            ),
            consecutive_errors=health_data.get('consecutive_errors', 0)
        )

        last_check = data.get('last_check_time')
        last_restart = data.get('last_restart_time')

        return cls(
            watcher_type=data.get('watcher_type', 'filesystem'),
            status=data.get('status', 'unknown'),
            process_id=data.get('process_id', ''),
            last_check_time=(
                datetime.fromisoformat(last_check)
                if last_check else None
            ),
            items_detected_today=data.get('items_detected_today', 0),
            items_detected_total=data.get('items_detected_total', 0),
            uptime_seconds=data.get('uptime_seconds', 0),
            restart_count=data.get('restart_count', 0),
            last_restart_time=(
                datetime.fromisoformat(last_restart)
                if last_restart else None
            ),
            last_restart_reason=data.get('last_restart_reason'),
            config=config,
            health=health
        )

    def get_dashboard_row(self) -> str:
        """
        Get a formatted row for dashboard display.

        Returns:
            Markdown table row string.
        """
        emoji = self.get_status_emoji()
        last_check = 'Never'
        if self.last_check_time:
            last_check = self.last_check_time.strftime('%H:%M:%S')

        stability = self.get_stability_label()

        return (
            f"| {self.watcher_type} | {emoji} {self.status} | "
            f"{last_check} | {self.items_detected_today} | "
            f"{self.get_uptime_display()} | {stability} |"
        )
