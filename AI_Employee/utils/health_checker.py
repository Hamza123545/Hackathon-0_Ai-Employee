"""
MCP Server Health Checker (Gold Tier)

Monitors health and availability of MCP servers.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional

from ..models.mcp_server_status import MCPServerStatus


class HealthChecker:
    """
    Checks health of MCP servers and updates status files.
    
    Health check interval: 5 minutes (configurable)
    """
    
    def __init__(
        self,
        status_dir: Path,
        check_interval_seconds: int = 300  # 5 minutes
    ):
        """
        Initialize HealthChecker.
        
        Args:
            status_dir: Directory to store MCP server status files
            check_interval_seconds: Interval between health checks (default: 300 = 5 minutes)
        """
        self.status_dir = Path(status_dir)
        self.status_dir.mkdir(parents=True, exist_ok=True)
        self.check_interval_seconds = check_interval_seconds
    
    def check_server_health(
        self,
        server_name: str,
        health_check_func: Optional[Callable] = None,
        **kwargs
    ) -> MCPServerStatus:
        """
        Check health of a specific MCP server.
        
        Args:
            server_name: Name of MCP server (e.g., 'xero-mcp', 'facebook-mcp')
            health_check_func: Optional function to perform actual health check.
                             Should return (success: bool, response_time_ms: float, error: Optional[str])
            **kwargs: Additional arguments to pass to health_check_func
        
        Returns:
            MCPServerStatus object with updated health information
        """
        status_file = self.status_dir / f"{server_name}.json"
        
        # Load existing status or create new
        if status_file.exists():
            try:
                status_data = json.loads(status_file.read_text(encoding='utf-8'))
                status = MCPServerStatus.model_validate(status_data)
            except Exception as e:
                # If loading fails, create new status
                print(f"Warning: Failed to load status for {server_name}: {e}")
                status = MCPServerStatus(server_name=server_name)
        else:
            status = MCPServerStatus(server_name=server_name)
        
        # Perform health check
        if health_check_func:
            start_time = time.time()
            try:
                success, response_time_ms, error = health_check_func(**kwargs)
                actual_response_time = (time.time() - start_time) * 1000.0
                if response_time_ms == 0.0:
                    response_time_ms = actual_response_time
            except Exception as e:
                success = False
                response_time_ms = (time.time() - start_time) * 1000.0
                error = str(e)
        else:
            # Default health check: just update timestamp
            success = True
            response_time_ms = 0.0
            error = None
        
        # Update status
        status.update_status(success, response_time_ms, error)
        
        # Save status to file
        self._save_status(status)
        
        return status
    
    def _save_status(self, status: MCPServerStatus) -> None:
        """Save MCP server status to file."""
        status_file = self.status_dir / f"{status.server_name}.json"
        status_file.write_text(status.model_dump_json(), encoding='utf-8')
    
    def get_server_status(self, server_name: str) -> Optional[MCPServerStatus]:
        """
        Get current status of an MCP server.
        
        Args:
            server_name: Name of MCP server
        
        Returns:
            MCPServerStatus object or None if not found
        """
        status_file = self.status_dir / f"{server_name}.json"
        
        if not status_file.exists():
            return None
        
        try:
            status_data = json.loads(status_file.read_text(encoding='utf-8'))
            return MCPServerStatus.model_validate(status_data)
        except Exception as e:
            print(f"Warning: Failed to load status for {server_name}: {e}")
            return None
    
    def get_all_server_statuses(self) -> dict[str, MCPServerStatus]:
        """
        Get status of all MCP servers.
        
        Returns:
            Dictionary mapping server name to MCPServerStatus
        """
        statuses = {}
        
        if not self.status_dir.exists():
            return statuses
        
        for status_file in self.status_dir.glob("*.json"):
            server_name = status_file.stem
            status = self.get_server_status(server_name)
            if status:
                statuses[server_name] = status
        
        return statuses
    
    def is_server_healthy(self, server_name: str) -> bool:
        """
        Check if an MCP server is healthy.
        
        Args:
            server_name: Name of MCP server
        
        Returns:
            True if server is healthy, False otherwise
        """
        status = self.get_server_status(server_name)
        if status is None:
            return False
        
        return status.status == "healthy"
    
    def get_degraded_servers(self) -> list[str]:
        """
        Get list of degraded MCP servers.
        
        Returns:
            List of server names with degraded status
        """
        all_statuses = self.get_all_server_statuses()
        return [
            name for name, status in all_statuses.items()
            if status.status == "degraded"
        ]
    
    def get_down_servers(self) -> list[str]:
        """
        Get list of down MCP servers.
        
        Returns:
            List of server names with down status
        """
        all_statuses = self.get_all_server_statuses()
        return [
            name for name, status in all_statuses.items()
            if status.status == "down"
        ]
    
    def should_check_server(self, server_name: str) -> bool:
        """
        Determine if a server should be checked based on check interval.
        
        Args:
            server_name: Name of MCP server
        
        Returns:
            True if server should be checked, False if too soon
        """
        status = self.get_server_status(server_name)
        if status is None:
            return True
        
        time_since_update = datetime.now() - status.updated_at
        return time_since_update.total_seconds() >= self.check_interval_seconds


# Default health checker instance
def get_default_health_checker(vault_path: Optional[Path] = None) -> HealthChecker:
    """
    Get default HealthChecker instance.
    
    Args:
        vault_path: Path to vault. If None, uses Config to find it.
    
    Returns:
        HealthChecker instance
    """
    if vault_path is None:
        from utils.config import Config
        config = Config()
        vault_path = config.vault_path
    
    status_dir = vault_path / "System" / "MCP_Status"
    return HealthChecker(status_dir=status_dir)

