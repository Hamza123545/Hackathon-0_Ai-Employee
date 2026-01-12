"""
Financial Summary Model (Gold Tier)

Represents aggregated financial data from Xero for weekly audits.
"""

from datetime import date, datetime
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class FinancialSummary(BaseModel):
    """
    Financial Summary entity for Gold Tier.
    
    Used in Audit Reports and CEO Briefings.
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    period_start: date = Field(..., description="Financial period start")
    period_end: date = Field(..., description="Financial period end")
    revenue: float = Field(default=0.0, description="Total revenue")
    expenses: float = Field(default=0.0, description="Total expenses")
    net_profit: float = Field(default=0.0, description="Net profit (revenue - expenses)")
    outstanding_invoices: int = Field(default=0, description="Number of outstanding invoices")
    outstanding_invoice_amount: float = Field(default=0.0, description="Total amount of outstanding invoices")
    cash_flow: float = Field(default=0.0, description="Cash flow for period")
    currency: str = Field(default="USD", description="Currency code (ISO 4217)")
    profit_margin: float = Field(default=0.0, description="Profit margin percentage")
    created_at: datetime = Field(default_factory=datetime.now, description="Summary creation timestamp")
    metadata: dict = Field(default_factory=dict, description="Additional financial data")
    
    @field_validator('period_end')
    @classmethod
    def validate_period_end(cls, v: date, info) -> date:
        """Ensure period_end is after period_start."""
        period_start = info.data.get('period_start')
        if period_start and v < period_start:
            raise ValueError("period_end must be after period_start")
        return v
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate ISO 4217 currency code."""
        if len(v) != 3:
            raise ValueError("Currency must be a 3-letter ISO 4217 code")
        return v.upper()
    
    @field_validator('revenue', 'expenses', 'net_profit', 'outstanding_invoice_amount', 'cash_flow')
    @classmethod
    def validate_amounts(cls, v: float) -> float:
        """Amounts can be negative (for losses/deficits)."""
        return v
    
    @field_validator('outstanding_invoices')
    @classmethod
    def validate_non_negative(cls, v: int) -> int:
        """Ensure outstanding_invoices is non-negative."""
        if v < 0:
            raise ValueError("outstanding_invoices must be non-negative")
        return v
    
    def calculate_profit_margin(self) -> float:
        """Calculate profit margin percentage."""
        if self.revenue == 0:
            return 0.0
        return (self.net_profit / self.revenue) * 100.0
    
    def calculate_net_profit(self) -> float:
        """Calculate net profit from revenue and expenses."""
        return self.revenue - self.expenses
    
    def model_dump_json(self, **kwargs) -> str:
        """Serialize to JSON string."""
        from json import dumps
        return dumps(self.model_dump(**kwargs), default=str, indent=2)
    
    @classmethod
    def model_validate_json(cls, json_data: str | bytes) -> "FinancialSummary":
        """Deserialize from JSON string."""
        from json import loads
        data = loads(json_data) if isinstance(json_data, bytes) else loads(json_data)
        return cls.model_validate(data)

