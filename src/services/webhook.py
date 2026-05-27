import httpx
import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from src.models import WebhookDelivery

logger = logging.getLogger(__name__)

# Mock webhook endpoints - in production, fetch from customer config
CUSTOMER_WEBHOOKS = {
    "cust_123": "https://webhook.site/your-test-endpoint",
    "cust_456": "https://httpbin.org/post"
}

async def deliver_webhook(session: AsyncSession, delivery_id: str):
    """Deliver webhook with retry logic"""
    
    # Fetch delivery record
    result = await session.execute(
        select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
    )
    delivery = result.scalar_one_or_none()
    
    if not delivery or delivery.status != "pending":
        return
    
    webhook_url = CUSTOMER_WEBHOOKS.get(delivery.customer_id)
    if not webhook_url:
        logger.warning(f"No webhook URL for {delivery.customer_id}")
        delivery.status = "failed"
        await session.commit()
        return
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=False
    )
    async def send():
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                webhook_url,
                json=delivery.payload,
                headers={"Idempotency-Key": str(delivery.bill_id)}
            )
            response.raise_for_status()
            return response
    
    try:
        response = await send()
        delivery.status = "delivered"
        delivery.last_attempt = datetime.now(timezone.utc)
        await session.commit()
        logger.info(f"Webhook delivered for bill {delivery.bill_id}")
        
    except Exception as e:
        delivery.retry_count += 1
        delivery.last_attempt = datetime.now(timezone.utc)
        
        if delivery.retry_count >= 3:
            delivery.status = "failed"
            logger.error(f"Webhook failed permanently for {delivery.bill_id}: {e}")
        else:
            # Exponential backoff: 1s, 4s, 16s
            delay = 2 ** delivery.retry_count
            delivery.next_retry = datetime.now(timezone.utc) + timedelta(seconds=delay)
        
        await session.commit()

async def retry_failed_webhooks(session: AsyncSession):
    """Background worker to retry failed webhooks"""
    now = datetime.now(timezone.utc)
    
    result = await session.execute(
        select(WebhookDelivery).where(
            WebhookDelivery.status == "pending",
            WebhookDelivery.next_retry <= now
        )
    )
    
    deliveries = result.scalars().all()
    
    for delivery in deliveries:
        asyncio.create_task(deliver_webhook(session, str(delivery.id)))
    
    if deliveries:
        logger.info(f"Queued {len(deliveries)} webhooks for retry")