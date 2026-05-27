from sqlalchemy import Column, String, Integer, DateTime, Float, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from src.database import Base
import uuid

class Event(Base):
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idempotency_key = Column(String(255), unique=True, nullable=False)
    customer_id = Column(String(100), nullable=False)
    meter_name = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), server_default=func.now())

class Counter(Base):
    __tablename__ = "counters"
    
    customer_id = Column(String(100), primary_key=True)
    meter_name = Column(String(100), primary_key=True)
    billing_month = Column(DateTime(timezone=True), primary_key=True)
    total_quantity = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Bill(Base):
    __tablename__ = "bills"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(100), nullable=False)
    billing_month = Column(DateTime(timezone=True), nullable=False)
    total_amount = Column(Float, nullable=False)
    line_items = Column(JSON, nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    finalized_at = Column(DateTime(timezone=True))

class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True))
    customer_id = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(20), default="pending")
    retry_count = Column(Integer, default=0)
    last_attempt = Column(DateTime(timezone=True))
    next_retry = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())