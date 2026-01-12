"""
Social Media Engagement Model (Gold Tier)

Represents aggregated social media engagement metrics across platforms.
"""

from datetime import date, datetime
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class PlatformEngagement(BaseModel):
    """Engagement metrics for a specific platform."""
    
    platform: str = Field(
        ...,
        description="Platform name",
        pattern="^(facebook|instagram|twitter)$"
    )
    total_posts: int = Field(default=0, description="Total posts in period")
    total_likes: int = Field(default=0, description="Total likes")
    total_comments: int = Field(default=0, description="Total comments")
    total_shares: int = Field(default=0, description="Total shares/retweets")
    total_impressions: int = Field(default=0, description="Total impressions")
    total_reach: int = Field(default=0, description="Total reach")
    engagement_rate: float = Field(default=0.0, description="Overall engagement rate percentage")
    follower_growth: int = Field(default=0, description="Follower growth in period")
    
    @field_validator('platform')
    @classmethod
    def validate_platform(cls, v: str) -> str:
        """Validate platform enum."""
        valid_platforms = ["facebook", "instagram", "twitter"]
        if v not in valid_platforms:
            raise ValueError(f"platform must be one of {valid_platforms}")
        return v
    
    @field_validator('total_posts', 'total_likes', 'total_comments', 'total_shares', 'total_impressions', 'total_reach', 'follower_growth')
    @classmethod
    def validate_non_negative(cls, v: int) -> int:
        """Ensure counts are non-negative."""
        if v < 0:
            raise ValueError("Counts must be non-negative")
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
        if self.total_impressions > 0:
            total_engagements = self.total_likes + self.total_comments + self.total_shares
            return (total_engagements / self.total_impressions) * 100.0
        return 0.0


class SocialMediaEngagement(BaseModel):
    """
    Social Media Engagement entity for Gold Tier.
    
    Used in Audit Reports and CEO Briefings.
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    period_start: date = Field(..., description="Engagement period start")
    period_end: date = Field(..., description="Engagement period end")
    platform_engagement: list[PlatformEngagement] = Field(
        default_factory=list,
        description="Engagement per platform"
    )
    total_posts: int = Field(default=0, description="Total posts across all platforms")
    total_engagement: int = Field(default=0, description="Total engagements (likes + comments + shares)")
    overall_engagement_rate: float = Field(default=0.0, description="Overall engagement rate percentage")
    created_at: datetime = Field(default_factory=datetime.now, description="Summary creation timestamp")
    metadata: dict = Field(default_factory=dict, description="Additional engagement data")
    
    @field_validator('period_end')
    @classmethod
    def validate_period_end(cls, v: date, info) -> date:
        """Ensure period_end is after period_start."""
        period_start = info.data.get('period_start')
        if period_start and v < period_start:
            raise ValueError("period_end must be after period_start")
        return v
    
    @field_validator('overall_engagement_rate')
    @classmethod
    def validate_engagement_rate(cls, v: float) -> float:
        """Ensure engagement rate is between 0 and 100."""
        if not 0.0 <= v <= 100.0:
            raise ValueError("overall_engagement_rate must be between 0.0 and 100.0")
        return v
    
    def calculate_totals(self) -> tuple[int, int, float]:
        """
        Calculate total posts, total engagement, and overall engagement rate.
        
        Returns:
            Tuple of (total_posts, total_engagement, overall_engagement_rate)
        """
        total_posts = sum(p.total_posts for p in self.platform_engagement)
        total_likes = sum(p.total_likes for p in self.platform_engagement)
        total_comments = sum(p.total_comments for p in self.platform_engagement)
        total_shares = sum(p.total_shares for p in self.platform_engagement)
        total_impressions = sum(p.total_impressions for p in self.platform_engagement)
        
        total_engagement = total_likes + total_comments + total_shares
        
        if total_impressions > 0:
            overall_rate = (total_engagement / total_impressions) * 100.0
        else:
            overall_rate = 0.0
        
        return (total_posts, total_engagement, overall_rate)
    
    def model_dump_json(self, **kwargs) -> str:
        """Serialize to JSON string."""
        from json import dumps
        return dumps(self.model_dump(**kwargs), default=str, indent=2)
    
    @classmethod
    def model_validate_json(cls, json_data: str | bytes) -> "SocialMediaEngagement":
        """Deserialize from JSON string."""
        from json import loads
        data = loads(json_data) if isinstance(json_data, bytes) else loads(json_data)
        return cls.model_validate(data)

