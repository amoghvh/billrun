from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

class EventIngest(BaseModel):
    idempotency_key: str = Field(..., min_length=1, max_length=255)
    customer_id: str = Field(..., min_length=1, max_length=100)
    meter_name: str = Field(..., min_length=1, max_length=100)
    quantity: int = Field(..., gt=0, le=1000000)
    timestamp: Optional[datetime] = None
    
    @validator('idempotency_key')
    def validate_key(cls, v):
        if not v.strip():
            raise ValueError('Idempotency key cannot be empty')
        return v

class EventResponse(BaseModel):
    id: UUID
    idempotency_key: str
    customer_id: str
    meter_name: str
    quantity: int
    processed_at: datetime

class BillRunRequest(BaseModel):
    customer_id: str
    billing_month: str  # YYYY-MM format

class BillResponse(BaseModel):
    id: UUID
    customer_id: str
    billing_month: str
    total_amount: float
    line_items: Dict[str, Any]
    status: str
    finalized_at: Optional[datetime]

class WebhookPayload(BaseModel):
    event: str
    bill_id: UUID
    customer_id: str
    total_amount: float
    billing_month: str