"""
MCP Server model for Silver Tier Personal AI Employee.

Defines the MCPServer dataclass for tracking MCP server metadata,
status, and capabilities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


ServerType = Literal['email', 'linkedin', 'playwright', 'custom']
ServerStatus = Literal['available', 'error', 'offline', 'unknown']


@dataclass
class MCPServer:
    """
    Represents an MCP server for external action execution.

    An MCP (Model Context Protocol) server is an external action execution
    backend that implements the MCP standard for tool invocation.

    Attributes:
        server_name: Unique identifier (e.g., 'email-mcp', 'linkedin-mcp').
        server_type: Type of server (email, linkedin, playwright, custom).
        status: Current server status.
        command: Startup command for the server process.
        transport: MCP transport protocol (usually 'stdio').
        capabilities: List of supported tool names.
        last_successful_action: Timestamp of last successful tool invocation.
        last_health_check: Timestamp of last health check.
        error_count: Count of consecutive failures (reset on success).
        environment: Environment variables for server process.
        config: Server-specific configuration.
    """

    server_name: str
    server_type: ServerType = 'custom'
    status: ServerStatus = 'unknown'
    command: str = ''
    transport: str = 'stdio'
    capabilities: list[str] = field(default_factory=list)
    last_successful_action: datetime | None = None
    last_health_check: datetime | None = None
    error_count: int = 0
    environment: dict[str, str] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)

    def is_available(self) -> bool:
        """
        Check if the server is available for tool invocation.

        Returns:
            True if status is 'available'.
        """
        return self.status == 'available'

    def is_healthy(self) -> bool:
        """
        Check if the server is healthy (available and low error count).

        Returns:
            True if available and error_count < 5.
        """
        return self.is_available() and self.error_count < 5

    def record_success(self) -> None:
        """
        Record a successful tool invocation.

        Updates last_successful_action timestamp and resets error_count.
        """
        self.last_successful_action = datetime.now()
        self.error_count = 0
        self.status = 'available'

    def record_failure(self, max_errors: int = 5) -> None:
        """
        Record a failed tool invocation.

        Increments error_count and sets status to 'error' if threshold reached.

        Args:
            max_errors: Error count threshold for marking server as errored.
        """
        self.error_count += 1
        if self.error_count >= max_errors:
            self.status = 'error'

    def record_health_check(self, is_healthy: bool) -> None:
        """
        Record a health check result.

        Args:
            is_healthy: Whether the health check passed.
        """
        self.last_health_check = datetime.now()
        if is_healthy:
            self.status = 'available'
        else:
            self.status = 'error'

    def has_capability(self, tool_name: str) -> bool:
        """
        Check if the server supports a specific tool.

        Args:
            tool_name: Name of the tool to check.

        Returns:
            True if the tool is in the capabilities list.
        """
        return tool_name in self.capabilities

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the MCP server.
        """
        return {
            'server_name': self.server_name,
            'server_type': self.server_type,
            'status': self.status,
            'command': self.command,
            'transport': self.transport,
            'capabilities': self.capabilities,
            'last_successful_action': (
                self.last_successful_action.isoformat()
                if self.last_successful_action else None
            ),
            'last_health_check': (
                self.last_health_check.isoformat()
                if self.last_health_check else None
            ),
            'error_count': self.error_count,
            'environment': self.environment,
            'config': self.config
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'MCPServer':
        """
        Create an MCPServer from a dictionary.

        Args:
            data: Dictionary with server data.

        Returns:
            MCPServer instance.
        """
        last_action = data.get('last_successful_action')
        last_check = data.get('last_health_check')

        return cls(
            server_name=data.get('server_name', ''),
            server_type=data.get('server_type', 'custom'),
            status=data.get('status', 'unknown'),
            command=data.get('command', ''),
            transport=data.get('transport', 'stdio'),
            capabilities=data.get('capabilities', []),
            last_successful_action=(
                datetime.fromisoformat(last_action)
                if last_action else None
            ),
            last_health_check=(
                datetime.fromisoformat(last_check)
                if last_check else None
            ),
            error_count=data.get('error_count', 0),
            environment=data.get('environment', {}),
            config=data.get('config', {})
        )

    def get_status_emoji(self) -> str:
        """
        Get status emoji for dashboard display.

        Returns:
            Emoji representing the current status.
        """
        status_emojis = {
            'available': '\u2705',  # Green check
            'error': '\u274c',       # Red X
            'offline': '\u26aa',     # White circle
            'unknown': '\u2754'      # Question mark
        }
        return status_emojis.get(self.status, '\u2754')

    def get_health_summary(self) -> str:
        """
        Get a human-readable health summary.

        Returns:
            Summary string for dashboard display.
        """
        emoji = self.get_status_emoji()
        last_action = 'Never'
        if self.last_successful_action:
            last_action = self.last_successful_action.strftime('%Y-%m-%d %H:%M')

        return f"{emoji} {self.status} | Last success: {last_action} | Errors: {self.error_count}"
