"""
CEO Briefing Model (Gold Tier)

Represents a weekly executive summary with AI-generated insights.
"""

from datetime import date, datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class GoalProgress(BaseModel):
    """Business goal progress information."""
    
    goal_id: str = Field(..., description="Business goal ID")
    goal_title: str = Field(..., description="Goal title")
    completion_percentage: float = Field(..., description="Completion percentage (0.0-100.0)")
    status: str = Field(..., description="Goal status")
    
    @field_validator('completion_percentage')
    @classmethod
    def validate_percentage(cls, v: float) -> float:
        """Ensure completion_percentage is between 0 and 100."""
        if not 0.0 <= v <= 100.0:
            raise ValueError("completion_percentage must be between 0.0 and 100.0")
        return v


class CEOBriefing(BaseModel):
    """
    CEO Briefing entity for Gold Tier.
    
    File Location: /Briefings/<YYYY-MM-DD>-ceo-briefing.md
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    generated_at: datetime = Field(default_factory=datetime.now, description="Briefing generation timestamp")
    period_start: date = Field(..., description="Reporting period start (Monday)")
    period_end: date = Field(..., description="Reporting period end (Sunday)")
    executive_summary: str = Field(..., min_length=200, max_length=300, description="AI-generated high-level summary (200-300 words)")
    key_insights: list[str] = Field(..., min_length=3, max_length=5, description="3-5 AI-generated insights")
    financial_summary: Optional[dict] = Field(default=None, description="Xero financial data (FinancialSummary)")
    social_media_summary: Optional[dict] = Field(default=None, description="Aggregated engagement (SocialMediaEngagement)")
    action_items_summary: dict = Field(
        default_factory=dict,
        description="Processed actions breakdown"
    )
    goal_progress: list[GoalProgress] = Field(default_factory=list, description="Business goal status")
    risks_and_alerts: list[str] = Field(default_factory=list, description="Identified risks or anomalies")
    recommendations: list[str] = Field(default_factory=list, description="AI-generated recommendations")
    attachments: list[str] = Field(default_factory=list, description="Links to detailed reports")
    
    @field_validator('period_start')
    @classmethod
    def validate_period_start(cls, v: date) -> date:
        """Ensure period_start is a Monday."""
        if v.weekday() != 0:  # Monday is 0
            raise ValueError("period_start must be a Monday")
        return v
    
    @field_validator('period_end')
    @classmethod
    def validate_period_end(cls, v: date, info) -> date:
        """Ensure period_end is a Sunday and after period_start."""
        if v.weekday() != 6:  # Sunday is 6
            raise ValueError("period_end must be a Sunday")
        
        period_start = info.data.get('period_start')
        if period_start and v < period_start:
            raise ValueError("period_end must be after period_start")
        return v
    
    @field_validator('key_insights')
    @classmethod
    def validate_key_insights(cls, v: list[str]) -> list[str]:
        """Ensure key_insights has 3-5 items."""
        if not 3 <= len(v) <= 5:
            raise ValueError("key_insights must have 3-5 items")
        return v
    
    @field_validator('executive_summary')
    @classmethod
    def validate_executive_summary_length(cls, v: str) -> str:
        """Ensure executive_summary is 200-300 words."""
        word_count = len(v.split())
        if not 200 <= word_count <= 300:
            raise ValueError(f"executive_summary must be 200-300 words (got {word_count})")
        return v
    
    def model_dump_json(self, **kwargs) -> str:
        """Serialize to JSON string."""
        from json import dumps
        return dumps(self.model_dump(**kwargs), default=str, indent=2)
    
    @classmethod
    def model_validate_json(cls, json_data: str | bytes) -> "CEOBriefing":
        """Deserialize from JSON string."""
        from json import loads
        data = loads(json_data) if isinstance(json_data, bytes) else loads(json_data)
        return cls.model_validate(data)
    
    def to_markdown(self) -> str:
        """Convert CEO Briefing to Markdown format for file storage."""
        lines = [
            f"# CEO Briefing - {self.period_start} to {self.period_end}",
            "",
            f"**Generated:** {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Executive Summary",
            "",
            self.executive_summary,
            "",
            "## Key Insights",
            ""
        ]
        
        for i, insight in enumerate(self.key_insights, 1):
            lines.append(f"{i}. {insight}")
        
        if self.financial_summary:
            lines.extend([
                "",
                "## Financial Summary",
                "",
                f"See attached financial summary for details."
            ])
        
        if self.social_media_summary:
            lines.extend([
                "",
                "## Social Media Performance",
                "",
                f"See attached social media engagement summary for details."
            ])
        
        if self.goal_progress:
            lines.extend([
                "",
                "## Goal Progress",
                ""
            ])
            for goal in self.goal_progress:
                lines.append(f"- **{goal.goal_title}**: {goal.completion_percentage:.1f}% complete ({goal.status})")
        
        if self.risks_and_alerts:
            lines.extend([
                "",
                "## Risks and Alerts",
                ""
            ])
            for risk in self.risks_and_alerts:
                lines.append(f"- ⚠️ {risk}")
        
        if self.recommendations:
            lines.extend([
                "",
                "## Recommendations",
                ""
            ])
            for i, rec in enumerate(self.recommendations, 1):
                lines.append(f"{i}. {rec}")
        
        if self.attachments:
            lines.extend([
                "",
                "## Attachments",
                ""
            ])
            for attachment in self.attachments:
                lines.append(f"- {attachment}")
        
        return "\n".join(lines)

