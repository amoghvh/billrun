from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select  # ← ADD THIS LINE
from src.database import get_db
from src.schemas import BillRunRequest, BillResponse
from src.services.billing import run_bill
from src.services.webhook import deliver_webhook
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/run-bill", response_model=BillResponse)
async def run_bill_endpoint(
    request: BillRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Run billing for a customer for a specific month.
    Generates invoice and queues webhook delivery.
    """
    bill = await run_bill(
        session=db,
        customer_id=request.customer_id,
        billing_month=request.billing_month
    )
    
    if not bill:
        raise HTTPException(status_code=404, detail="No usage found or bill already exists")
    
    # Queue webhook delivery in background
    from src.models import WebhookDelivery
    result = await db.execute(
        select(WebhookDelivery).where(WebhookDelivery.bill_id == bill.id)
    )
    delivery = result.scalar_one()
    
    background_tasks.add_task(deliver_webhook, db, str(delivery.id))
    
    return BillResponse(
        id=bill.id,
        customer_id=bill.customer_id,
        billing_month=request.billing_month,
        total_amount=bill.total_amount,
        line_items=bill.line_items,
        status=bill.status,
        finalized_at=bill.finalized_at
    )

@router.get("/bills/{customer_id}")
async def get_customer_bills(customer_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from src.models import Bill
    
    result = await db.execute(
        select(Bill).where(Bill.customer_id == customer_id).order_by(Bill.billing_month.desc())
    )
    bills = result.scalars().all()
    return bills