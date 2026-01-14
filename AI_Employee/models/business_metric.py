"""
Business Metric Model (Gold Tier)

Tracks specific business KPIs over time with trend calculation.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class BusinessMetric(BaseModel):
    """
    Business Metric entity for Gold Tier.
    
    File Location: /Business/Metrics/<YYYY-MM-DD>-<metric-name>.json
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    metric_name: str = Field(..., description="Metric name (e.g., 'monthly_revenue', 'social_engagement')")
    date: dt.date = Field(..., description="Metric date")
    value: float = Field(..., description="Metric value")
    unit: str = Field(default="", description="Metric unit (USD, percentage, count, etc.)")
    source: str = Field(
        default="manual",
        description="Data source",
        pattern="^(xero|facebook|instagram|twitter|manual)$"
    )
    category: str = Field(
        default="operational",
        description="Metric category",
        pattern="^(financial|social|operational|growth)$"
    )
    trend: str = Field(
        default="stable",
        description="Trend direction",
        pattern="^(up|down|stable)$"
    )
    change_percentage: float = Field(default=0.0, description="Percentage change from previous period")
    target_value: float | None = Field(default=None, description="Target value if applicable")
    metadata: dict = Field(default_factory=dict, description="Additional context")
    created_at: dt.datetime = Field(default_factory=dt.datetime.now, description="Metric creation timestamp")
    
    @field_validator('source')
    @classmethod
    def validate_source(cls, v: str) -> str:
        """Validate source enum."""
        valid_sources = ["xero", "facebook", "instagram", "twitter", "manual"]
        if v not in valid_sources:
            raise ValueError(f"source must be one of {valid_sources}")
        return v
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate category enum."""
        valid_categories = ["financial", "social", "operational", "growth"]
        if v not in valid_categories:
            raise ValueError(f"category must be one of {valid_categories}")
        return v
    
    @field_validator('trend')
    @classmethod
    def validate_trend(cls, v: str) -> str:
        """Validate trend enum."""
        valid_trends = ["up", "down", "stable"]
        if v not in valid_trends:
            raise ValueError(f"trend must be one of {valid_trends}")
        return v
    
    def calculate_trend(self, previous_value: float | None) -> tuple[str, float]:
        """
        Calculate trend and change percentage from previous value.
        
        Returns:
            Tuple of (trend, change_percentage)
        """
        if previous_value is None or previous_value == 0:
            return ("stable", 0.0)
        
        change = ((self.value - previous_value) / previous_value) * 100.0
        
        if change > 5.0:
            trend = "up"
        elif change < -5.0:
            trend = "down"
        else:
            trend = "stable"
        
        return (trend, change)
    
    def model_dump_json(self, **kwargs) -> str:
        """Serialize to JSON string."""
        from json import dumps
        return dumps(self.model_dump(**kwargs), default=str, indent=2)
    
    @classmethod
    def model_validate_json(cls, json_data: str | bytes) -> "BusinessMetric":
        """Deserialize from JSON string."""
        from json import loads
        data = loads(json_data) if isinstance(json_data, bytes) else loads(json_data)
        return cls.model_validate(data)

