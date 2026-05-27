cat > /mnt/d/billrun/src/services/billing.py << 'EOF'
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, and_
from datetime import datetime, timezone
from uuid import uuid4
import logging
from src.models import Bill, WebhookDelivery

logger = logging.getLogger(__name__)

# Pricing: $0.01 per unit
PRICE_PER_UNIT = 0.01

async def run_bill(session: AsyncSession, customer_id: str, billing_month: str):
    """
    Generate bill for a customer for a specific month.
    billing_month format: 'YYYY-MM' (e.g., '2026-05')
    """
    # Parse month - create date range for the entire month
    year, month = map(int, billing_month.split('-'))
    
    # First day of the month at UTC
    month_start = datetime(year, month, 1, tzinfo=timezone.utc)
    
    # Last day of the month (next month minus 1 day)
    if month == 12:
        month_end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        month_end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    
    logger.info(f"Looking for bills for {customer_id} between {month_start} and {month_end}")
    
    # Check if bill already exists
    existing_bill = await session.execute(
        select(Bill).where(
            and_(
                Bill.customer_id == customer_id,
                Bill.billing_month >= month_start,
                Bill.billing_month < month_end
            )
        )
    )
    existing = existing_bill.scalar_one_or_none()
    if existing:
        logger.warning(f"Bill already exists for {customer_id} - {billing_month}")
        return None
    
    # Get counters for this customer for the month
    # Use month_start as the exact date (since counters store first day of month)
    counters_result = await session.execute(
        text("""
            SELECT meter_name, total_quantity 
            FROM counters 
            WHERE customer_id = :cid AND billing_month = :month
        """),
        {"cid": customer_id, "month": month_start}
    )
    
    counters = counters_result.fetchall()
    
    logger.info(f"Found {len(counters)} meters for {customer_id} in {billing_month}")
    
    if not counters:
        logger.info(f"No usage for {customer_id} in {billing_month}")
        return None
    
    # Calculate bill
    line_items = {}
    total_amount = 0.0
    
    for meter_name, quantity in counters:
        amount = quantity * PRICE_PER_UNIT
        line_items[meter_name] = {
            "quantity": quantity,
            "rate": PRICE_PER_UNIT,
            "amount": round(amount, 2)
        }
        total_amount += amount
    
    total_amount = round(total_amount, 2)
    
    # Create bill
    bill = Bill(
        id=uuid4(),
        customer_id=customer_id,
        billing_month=month_start,
        total_amount=total_amount,
        line_items=line_items,
        status="finalized",
        finalized_at=datetime.now(timezone.utc)
    )
    session.add(bill)
    await session.flush()
    
    # Queue webhook delivery
    webhook = WebhookDelivery(
        bill_id=bill.id,
        customer_id=customer_id,
        payload={
            "event": "bill.finalized",
            "bill_id": str(bill.id),
            "customer_id": customer_id,
            "total_amount": total_amount,
            "billing_month": billing_month,
            "line_items": line_items,
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        next_retry=datetime.now(timezone.utc)
    )
    session.add(webhook)
    
    await session.commit()
    logger.info(f"Bill {bill.id} generated for {customer_id}: ${total_amount}")
    
    return bill
EOF