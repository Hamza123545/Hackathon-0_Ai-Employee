"""
Business Goal Model (Gold Tier)

Represents a business objective tracked across multiple actions.
"""

from datetime import date, datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class Metric(BaseModel):
    """Success metric for a business goal."""
    
    metric_name: str = Field(..., description="Name of the metric")
    target_value: float = Field(..., description="Target value to achieve")
    current_value: float = Field(default=0.0, description="Current value")
    unit: str = Field(default="", description="Unit of measurement (e.g., 'USD', 'count', '%')")
    
    @field_validator('target_value', 'current_value')
    @classmethod
    def validate_values(cls, v: float) -> float:
        """Ensure values are non-negative."""
        if v < 0:
            raise ValueError("Metric values must be non-negative")
        return v


class BusinessGoal(BaseModel):
    """
    Business Goal entity for Gold Tier.
    
    File Location: /Business/Goals/<goal-id>.json
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    created_at: datetime = Field(default_factory=datetime.now, description="Goal creation timestamp")
    title: str = Field(..., min_length=1, max_length=200, description="Goal title")
    description: str = Field(default="", description="Detailed goal description")
    target_date: date = Field(..., description="Target completion date")
    status: str = Field(
        default="active",
        description="Goal status",
        pattern="^(active|completed|deferred|cancelled)$"
    )
    priority: str = Field(
        default="normal",
        description="Goal priority",
        pattern="^(critical|high|normal|low)$"
    )
    metrics: list[Metric] = Field(..., min_length=1, description="Success metrics")
    related_actions: list[str] = Field(default_factory=list, description="Action item IDs contributing to goal")
    owner: str = Field(default="", description="Goal owner (e.g., 'CEO', 'CFO')")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")
    
    @field_validator('target_date')
    @classmethod
    def validate_target_date(cls, v: date) -> date:
        """Ensure target_date is a future date."""
        if v < date.today():
            raise ValueError("target_date must be a future date")
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status_transition(cls, v: str, info) -> str:
        """Validate status transitions (active → completed/deferred/cancelled)."""
        # Note: Full transition validation would require previous state
        # This is a basic validation
        valid_statuses = ["active", "completed", "deferred", "cancelled"]
        if v not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")
        return v
    
    def model_dump_json(self, **kwargs) -> str:
        """Serialize to JSON string."""
        from json import dumps
        return dumps(self.model_dump(**kwargs), default=str, indent=2)
    
    @classmethod
    def model_validate_json(cls, json_data: str | bytes) -> "BusinessGoal":
        """Deserialize from JSON string."""
        from json import loads
        data = loads(json_data) if isinstance(json_data, bytes) else loads(json_data)
        return cls.model_validate(data)
    
    def calculate_completion_percentage(self) -> float:
        """Calculate overall goal completion percentage based on metrics."""
        if not self.metrics:
            return 0.0
        
        total_completion = 0.0
        for metric in self.metrics:
            if metric.target_value > 0:
                completion = min(metric.current_value / metric.target_value, 1.0)
                total_completion += completion
        
        return (total_completion / len(self.metrics)) * 100.0

