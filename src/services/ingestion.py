from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, and_
from datetime import datetime, timezone
import logging
from src.models import Event, Counter

logger = logging.getLogger(__name__)

async def ingest_event(
    session: AsyncSession,
    idempotency_key: str,
    customer_id: str,
    meter_name: str,
    quantity: int,
    event_time: datetime = None
) -> dict:
    """
    Idempotent event ingestion using SERIALIZABLE isolation.
    Returns: {'status': 'created'|'already_processed', 'event_id': uuid}
    """
    if event_time is None:
        event_time = datetime.now(timezone.utc)
    
    billing_month = event_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Try to insert event (unique constraint on idempotency_key prevents duplicates)
    try:
        # Begin SERIALIZABLE transaction
        await session.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
        
        # Insert event
        event = Event(
            idempotency_key=idempotency_key,
            customer_id=customer_id,
            meter_name=meter_name,
            quantity=quantity,
            timestamp=event_time
        )
        session.add(event)
        await session.flush()
        
        # Update counter (upsert)
        counter_stmt = text("""
            INSERT INTO counters (customer_id, meter_name, billing_month, total_quantity, updated_at)
            VALUES (:cid, :meter, :month, :qty, NOW())
            ON CONFLICT (customer_id, meter_name, billing_month)
            DO UPDATE SET 
                total_quantity = counters.total_quantity + :qty,
                updated_at = NOW()
            WHERE counters.customer_id = :cid 
              AND counters.meter_name = :meter 
              AND counters.billing_month = :month
        """)
        
        await session.execute(counter_stmt, {
            "cid": customer_id,
            "meter": meter_name,
            "month": billing_month,
            "qty": quantity
        })
        
        await session.commit()
        logger.info(f"Event ingested: {idempotency_key} for {customer_id}")
        return {"status": "created", "event_id": str(event.id)}
        
    except Exception as e:
        await session.rollback()
        
        # Check if duplicate (unique violation)
        if "duplicate key" in str(e).lower():
            # Fetch existing event
            result = await session.execute(
                select(Event).where(Event.idempotency_key == idempotency_key)
            )
            existing = result.scalar_one()
            logger.info(f"Duplicate event rejected: {idempotency_key}")
            return {"status": "already_processed", "event_id": str(existing.id)}
        
        logger.error(f"Failed to ingest event {idempotency_key}: {e}")
        raise