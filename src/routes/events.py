from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.schemas import EventIngest, EventResponse
from src.services.ingestion import ingest_event
from src.metrics import track_request
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/ingest", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
@track_request("ingest")
async def ingest_event_endpoint(event: EventIngest, db: AsyncSession = Depends(get_db)):
    """
    Ingest a usage event.
    Idempotent: same idempotency_key returns same result without double-counting.
    """
    try:
        result = await ingest_event(
            session=db,
            idempotency_key=event.idempotency_key,
            customer_id=event.customer_id,
            meter_name=event.meter_name,
            quantity=event.quantity,
            event_time=event.timestamp
        )
        
        if result["status"] == "already_processed":
            # Return 200 for duplicate (idempotent)
            return {
                "status": "already_processed",
                "event_id": result["event_id"],
                "message": "This event was already ingested"
            }
        else:
            return {
                "status": "created",
                "event_id": result["event_id"],
                "message": "Event ingested successfully"
            }
            
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest event"
        )

@router.get("/events/{customer_id}", response_model=list[EventResponse])
async def get_customer_events(customer_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve events for a customer"""
    from sqlalchemy import select
    from src.models import Event
    
    result = await db.execute(
        select(Event).where(Event.customer_id == customer_id).limit(100)
    )
    events = result.scalars().all()
    return events