"""
Audit Report Model (Gold Tier)

Represents a weekly business and accounting audit with cross-domain analysis.
"""

from datetime import date, datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class Anomaly(BaseModel):
    """Detected anomaly in audit data."""
    
    severity: str = Field(
        ...,
        description="Anomaly severity",
        pattern="^(low|medium|high|critical)$"
    )
    type: str = Field(
        ...,
        description="Anomaly type",
        pattern="^(financial|social|operational)$"
    )
    description: str = Field(..., description="Anomaly description")
    detected_at: datetime = Field(default_factory=datetime.now, description="When anomaly was detected")
    
    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Validate severity enum."""
        valid_severities = ["low", "medium", "high", "critical"]
        if v not in valid_severities:
            raise ValueError(f"severity must be one of {valid_severities}")
        return v
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate type enum."""
        valid_types = ["financial", "social", "operational"]
        if v not in valid_types:
            raise ValueError(f"type must be one of {valid_types}")
        return v


class AuditReport(BaseModel):
    """
    Audit Report entity for Gold Tier.
    
    File Location: /Accounting/Audits/<YYYY-MM-DD>-audit-report.json
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    generated_at: datetime = Field(default_factory=datetime.now, description="Audit generation timestamp")
    period_start: date = Field(..., description="Audit period start")
    period_end: date = Field(..., description="Audit period end")
    financial_data: Optional[dict] = Field(default=None, description="Xero financial summary (FinancialSummary)")
    social_media_data: Optional[dict] = Field(default=None, description="Social media metrics (SocialMediaEngagement)")
    action_logs_summary: dict = Field(
        default_factory=dict,
        description="Summary of action logs"
    )
    cross_domain_workflows: list[dict] = Field(
        default_factory=list,
        description="Cross-domain actions (CrossDomainWorkflow)"
    )
    anomalies: list[Anomaly] = Field(default_factory=list, description="Detected anomalies")
    mcp_server_health: dict[str, dict] = Field(
        default_factory=dict,
        description="Health per MCP server (MCPServerStatus)"
    )
    recommendations: list[str] = Field(default_factory=list, description="AI-generated recommendations")
    status: str = Field(
        default="complete",
        description="Report status",
        pattern="^(complete|partial|failed)$"
    )
    
    @field_validator('period_end')
    @classmethod
    def validate_period_end(cls, v: date, info) -> date:
        """Ensure period_end is after period_start."""
        period_start = info.data.get('period_start')
        if period_start and v < period_start:
            raise ValueError("period_end must be after period_start")
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status enum."""
        valid_statuses = ["complete", "partial", "failed"]
        if v not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")
        return v
    
    def calculate_success_rate(self) -> float:
        """Calculate success rate from action_logs_summary."""
        if 'success_rate' in self.action_logs_summary:
            return float(self.action_logs_summary['success_rate'])
        
        total = self.action_logs_summary.get('total_actions', 0)
        if total == 0:
            return 0.0
        
        # Calculate from breakdown if available
        successful = self.action_logs_summary.get('successful_actions', 0)
        return (successful / total) * 100.0
    
    def get_critical_anomalies(self) -> list[Anomaly]:
        """Get anomalies with critical or high severity."""
        return [a for a in self.anomalies if a.severity in ["critical", "high"]]
    
    def model_dump_json(self, **kwargs) -> str:
        """Serialize to JSON string."""
        from json import dumps
        return dumps(self.model_dump(**kwargs), default=str, indent=2)
    
    @classmethod
    def model_validate_json(cls, json_data: str | bytes) -> "AuditReport":
        """Deserialize from JSON string."""
        from json import loads
        data = loads(json_data) if isinstance(json_data, bytes) else loads(json_data)
        return cls.model_validate(data)

