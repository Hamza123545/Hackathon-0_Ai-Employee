"""
Social Media Post Model (Gold Tier)

Represents a social media post created via MCP servers (Facebook, Instagram, Twitter).
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class EngagementMetrics(BaseModel):
    """Engagement metrics for a social media post."""
    
    likes: int = Field(default=0, description="Number of likes")
    comments: int = Field(default=0, description="Number of comments")
    shares: int = Field(default=0, description="Number of shares/retweets")
    impressions: int = Field(default=0, description="Number of impressions")
    reach: int = Field(default=0, description="Number of unique users reached")
    engagement_rate: float = Field(default=0.0, description="Engagement rate percentage")
    
    @field_validator('likes', 'comments', 'shares', 'impressions', 'reach')
    @classmethod
    def validate_non_negative(cls, v: int) -> int:
        """Ensure engagement counts are non-negative."""
        if v < 0:
            raise ValueError("Engagement counts must be non-negative")
        return v
    
    @field_validator('engagement_rate')
    @classmethod
    def validate_engagement_rate(cls, v: float) -> float:
        """Ensure engagement rate is between 0 and 100."""
        if not 0.0 <= v <= 100.0:
            raise ValueError("engagement_rate must be between 0.0 and 100.0")
        return v
    
    def calculate_engagement_rate(self) -> float:
        """Calculate engagement rate if impressions > 0."""
        if self.impressions > 0:
            total_engagements = self.likes + self.comments + self.shares
            return (total_engagements / self.impressions) * 100.0
        return 0.0


class SocialMediaPost(BaseModel):
    """
    Social Media Post entity for Gold Tier.
    
    File Location: /Business/Social_Media/<platform>/<post-id>.json
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier (platform post ID)")
    posted_at: datetime = Field(default_factory=datetime.now, description="Post publication timestamp")
    platform: str = Field(
        ...,
        description="Social media platform",
        pattern="^(facebook|instagram|twitter)$"
    )
    platform_post_id: str = Field(..., description="Platform-specific post ID")
    content: str = Field(..., description="Post text content")
    media_urls: list[str] = Field(default_factory=list, description="Attached media URLs")
    post_type: str = Field(
        default="text",
        description="Post type",
        pattern="^(text|photo|video|link)$"
    )
    status: str = Field(
        default="published",
        description="Post status",
        pattern="^(published|draft|deleted)$"
    )
    engagement_metrics: EngagementMetrics = Field(
        default_factory=EngagementMetrics,
        description="Post engagement data"
    )
    approval_request_id: str = Field(..., description="Reference to approval request")
    created_by: str = Field(default="ai_employee", description="Always 'ai_employee'")
    metadata: dict = Field(default_factory=dict, description="Platform-specific metadata")
    
    @field_validator('platform')
    @classmethod
    def validate_platform(cls, v: str) -> str:
        """Validate platform enum."""
        valid_platforms = ["facebook", "instagram", "twitter"]
        if v not in valid_platforms:
            raise ValueError(f"platform must be one of {valid_platforms}")
        return v
    
    @field_validator('post_type')
    @classmethod
    def validate_post_type(cls, v: str) -> str:
        """Validate post type enum."""
        valid_types = ["text", "photo", "video", "link"]
        if v not in valid_types:
            raise ValueError(f"post_type must be one of {valid_types}")
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status enum."""
        valid_statuses = ["published", "draft", "deleted"]
        if v not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")
        return v
    
    def model_dump_json(self, **kwargs) -> str:
        """Serialize to JSON string."""
        from json import dumps
        return dumps(self.model_dump(**kwargs), default=str, indent=2)
    
    @classmethod
    def model_validate_json(cls, json_data: str | bytes) -> "SocialMediaPost":
        """Deserialize from JSON string."""
        from json import loads
        data = loads(json_data) if isinstance(json_data, bytes) else loads(json_data)
        return cls.model_validate(data)

