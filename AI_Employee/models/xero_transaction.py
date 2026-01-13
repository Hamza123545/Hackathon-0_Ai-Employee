"""
Xero Transaction Model (Gold Tier)

Represents a financial transaction synced from Xero accounting system.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class LineItem(BaseModel):
    """Line item for invoices or expenses."""
    
    description: str = Field(..., description="Line item description")
    quantity: float = Field(default=1.0, description="Quantity")
    unit_amount: float = Field(..., description="Unit price/amount")
    account_code: str = Field(default="", description="Xero account code")
    
    @field_validator('quantity', 'unit_amount')
    @classmethod
    def validate_positive(cls, v: float) -> float:
        """Ensure quantity and unit_amount are positive."""
        if v < 0:
            raise ValueError("Quantity and unit_amount must be positive")
        return v
    
    @property
    def total_amount(self) -> float:
        """Calculate total amount for this line item."""
        return self.quantity * self.unit_amount


class XeroTransaction(BaseModel):
    """
    Xero Transaction entity for Gold Tier.
    
    File Location: /Accounting/Transactions/<transaction-id>.json
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier (Xero transaction ID)")
    synced_at: dt.datetime = Field(default_factory=dt.datetime.now, description="When transaction was synced")
    transaction_type: str = Field(
        ...,
        description="Transaction type",
        pattern="^(invoice|expense|bank_transaction|payment)$"
    )
    date: dt.date = Field(..., description="Transaction date")
    amount: float = Field(..., description="Transaction amount")
    currency: str = Field(default="USD", description="Currency code (ISO 4217)")
    status: str = Field(default="", description="Xero transaction status")
    contact_name: str = Field(default="", description="Customer/vendor name")
    description: str = Field(default="", description="Transaction description")
    category: str = Field(default="", description="Expense category or account code")
    line_items: list[LineItem] = Field(default_factory=list, description="Invoice/expense line items")
    metadata: dict = Field(default_factory=dict, description="Additional Xero metadata")
    approval_request_id: Optional[str] = Field(default=None, description="If created via HITL")
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: float, info) -> float:
        """Ensure amount is positive for expenses/invoices."""
        transaction_type = info.data.get('transaction_type', '')
        if transaction_type in ['expense', 'invoice'] and v <= 0:
            raise ValueError("Amount must be positive for expenses and invoices")
        return v
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate ISO 4217 currency code (basic validation)."""
        if len(v) != 3:
            raise ValueError("Currency must be a 3-letter ISO 4217 code")
        return v.upper()
    
    @field_validator('transaction_type')
    @classmethod
    def validate_transaction_type(cls, v: str) -> str:
        """Validate transaction type enum."""
        valid_types = ["invoice", "expense", "bank_transaction", "payment"]
        if v not in valid_types:
            raise ValueError(f"transaction_type must be one of {valid_types}")
        return v
    
    def model_dump_json(self, **kwargs) -> str:
        """Serialize to JSON string."""
        from json import dumps
        return dumps(self.model_dump(**kwargs), default=str, indent=2)
    
    @classmethod
    def model_validate_json(cls, json_data: str | bytes) -> "XeroTransaction":
        """Deserialize from JSON string."""
        from json import loads
        data = loads(json_data) if isinstance(json_data, bytes) else loads(json_data)
        return cls.model_validate(data)
    
    def calculate_total(self) -> float:
        """Calculate total amount from line items if available, otherwise use amount."""
        if self.line_items:
            return sum(item.total_amount for item in self.line_items)
        return self.amount

