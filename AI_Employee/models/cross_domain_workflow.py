"""
Cross-Domain Workflow Model (Gold Tier)

Represents a workflow spanning Personal and Business domains.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class WorkflowStep(BaseModel):
    """A single step in a cross-domain workflow."""
    
    step_number: int = Field(..., description="Step sequence number")
    description: str = Field(..., description="Step description")
    domain: str = Field(
        ...,
        description="Domain for this step",
        pattern="^(personal|business|accounting|social_media)$"
    )
    action_type: str = Field(..., description="Type of action (e.g., 'email', 'xero_expense', 'social_post')")
    status: str = Field(
        default="pending",
        description="Step status",
        pattern="^(pending|in_progress|completed|failed)$"
    )
    mcp_server: Optional[str] = Field(default=None, description="MCP server used for this step")
    result: Optional[dict] = Field(default=None, description="Step execution result")
    error: Optional[str] = Field(default=None, description="Error message if step failed")
    completed_at: Optional[datetime] = Field(default=None, description="Step completion timestamp")
    
    @field_validator('step_number')
    @classmethod
    def validate_step_number(cls, v: int) -> int:
        """Ensure step_number is positive."""
        if v < 1:
            raise ValueError("step_number must be >= 1")
        return v


class CrossDomainWorkflow(BaseModel):
    """
    Cross-Domain Workflow entity for Gold Tier.
    
    File Location: /Business/Workflows/<workflow-id>.json
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    created_at: datetime = Field(default_factory=datetime.now, description="Workflow creation timestamp")
    title: str = Field(..., min_length=1, max_length=200, description="Workflow title")
    description: str = Field(default="", description="Workflow description")
    source_domain: str = Field(
        ...,
        description="Domain where workflow originated",
        pattern="^(personal|business)$"
    )
    target_domain: str = Field(
        ...,
        description="Domain where workflow completes",
        pattern="^(personal|business|accounting|social_media)$"
    )
    steps: list[WorkflowStep] = Field(..., min_length=1, description="Ordered list of workflow steps")
    status: str = Field(
        default="pending",
        description="Overall workflow status",
        pattern="^(pending|in_progress|completed|failed|cancelled)$"
    )
    trigger_action_id: str = Field(..., description="Action item ID that triggered this workflow")
    related_approval_ids: list[str] = Field(default_factory=list, description="Approval request IDs")
    metadata: dict = Field(default_factory=dict, description="Additional workflow metadata")
    
    @field_validator('source_domain', 'target_domain')
    @classmethod
    def validate_domains(cls, v: str) -> str:
        """Validate domain enum."""
        valid_domains = ["personal", "business", "accounting", "social_media"]
        if v not in valid_domains:
            raise ValueError(f"domain must be one of {valid_domains}")
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status enum."""
        valid_statuses = ["pending", "in_progress", "completed", "failed", "cancelled"]
        if v not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")
        return v
    
    def get_current_step(self) -> Optional[WorkflowStep]:
        """Get the current step being executed."""
        for step in self.steps:
            if step.status in ["pending", "in_progress"]:
                return step
        return None
    
    def calculate_completion_percentage(self) -> float:
        """Calculate workflow completion percentage."""
        if not self.steps:
            return 0.0
        
        completed_steps = sum(1 for step in self.steps if step.status == "completed")
        return (completed_steps / len(self.steps)) * 100.0
    
    def model_dump_json(self, **kwargs) -> str:
        """Serialize to JSON string."""
        from json import dumps
        return dumps(self.model_dump(**kwargs), default=str, indent=2)
    
    @classmethod
    def model_validate_json(cls, json_data: str | bytes) -> "CrossDomainWorkflow":
        """Deserialize from JSON string."""
        from json import loads
        data = loads(json_data) if isinstance(json_data, bytes) else loads(json_data)
        return cls.model_validate(data)

