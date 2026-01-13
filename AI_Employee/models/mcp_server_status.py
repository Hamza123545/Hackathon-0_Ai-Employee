"""
MCP Server Status Model (Gold Tier)

Represents health and status information for an MCP server.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class MCPServerStatus(BaseModel):
    """
    MCP Server Status entity for Gold Tier.
    
    File Location: /System/MCP_Status/<server-name>.json
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    server_name: str = Field(..., description="MCP server name (e.g., 'xero-mcp', 'facebook-mcp')")
    status: str = Field(
        default="unknown",
        description="Server health status",
        pattern="^(healthy|degraded|down|unknown)$"
    )
    last_successful_request: Optional[datetime] = Field(
        default=None,
        description="Timestamp of last successful request"
    )
    last_failed_request: Optional[datetime] = Field(
        default=None,
        description="Timestamp of last failed request"
    )
    consecutive_failures: int = Field(default=0, description="Number of consecutive failures")
    total_requests: int = Field(default=0, description="Total number of requests made")
    successful_requests: int = Field(default=0, description="Number of successful requests")
    failed_requests: int = Field(default=0, description="Number of failed requests")
    average_response_time_ms: float = Field(default=0.0, description="Average response time in milliseconds")
    last_error: Optional[str] = Field(default=None, description="Last error message")
    rate_limit_remaining: Optional[int] = Field(default=None, description="Remaining rate limit quota")
    rate_limit_reset_at: Optional[datetime] = Field(default=None, description="When rate limit resets")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last status update timestamp")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status enum."""
        valid_statuses = ["healthy", "degraded", "down", "unknown"]
        if v not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")
        return v
    
    @field_validator('consecutive_failures', 'total_requests', 'successful_requests', 'failed_requests')
    @classmethod
    def validate_non_negative(cls, v: int) -> int:
        """Ensure counts are non-negative."""
        if v < 0:
            raise ValueError("Counts must be non-negative")
        return v
    
    @field_validator('average_response_time_ms')
    @classmethod
    def validate_response_time(cls, v: float) -> float:
        """Ensure response time is non-negative."""
        if v < 0:
            raise ValueError("average_response_time_ms must be non-negative")
        return v
    
    def calculate_success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100.0
    
    def update_status(self, success: bool, response_time_ms: float = 0.0, error: Optional[str] = None) -> None:
        """Update status based on request result."""
        self.total_requests += 1
        self.updated_at = datetime.now()
        
        if success:
            self.successful_requests += 1
            self.last_successful_request = datetime.now()
            self.consecutive_failures = 0
            
            # Update average response time
            if self.total_requests == 1:
                self.average_response_time_ms = response_time_ms
            else:
                # Exponential moving average
                alpha = 0.3
                self.average_response_time_ms = (
                    alpha * response_time_ms + (1 - alpha) * self.average_response_time_ms
                )
            
            # Determine status based on success rate
            success_rate = self.calculate_success_rate()
            if success_rate >= 95.0:
                self.status = "healthy"
            elif success_rate >= 80.0:
                self.status = "degraded"
            else:
                self.status = "down"
        else:
            self.failed_requests += 1
            self.last_failed_request = datetime.now()
            self.consecutive_failures += 1
            self.last_error = error
            
            # Determine status based on consecutive failures
            if self.consecutive_failures >= 5:
                self.status = "down"
            elif self.consecutive_failures >= 2:
                self.status = "degraded"
            else:
                # Keep current status if it's already degraded/down
                if self.status == "healthy":
                    self.status = "degraded"
    
    def model_dump_json(self, **kwargs) -> str:
        """Serialize to JSON string."""
        from json import dumps
        return dumps(self.model_dump(**kwargs), default=str, indent=2)
    
    @classmethod
    def model_validate_json(cls, json_data: str | bytes) -> "MCPServerStatus":
        """Deserialize from JSON string."""
        from json import loads
        data = loads(json_data) if isinstance(json_data, bytes) else loads(json_data)
        return cls.model_validate(data)

