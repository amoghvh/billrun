from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import time
import logging
from src.routes import events, bills
from src.database import engine
from src.models import Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="BillRun API", version="1.0.0")

# CORS for international recruiters to test your API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    response.headers["X-Request-Duration-MS"] = str(int(duration_ms))
    
    # Log slow requests (>500ms)
    if duration_ms > 500:
        logger.warning(f"Slow request: {request.method} {request.url.path} - {int(duration_ms)}ms")
    
    return response

# Routes
app.include_router(events.router, prefix="/v1", tags=["events"])
app.include_router(bills.router, prefix="/v1", tags=["bills"])

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "billrun"}

# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    from src.metrics import REQUEST_COUNT, REQUEST_LATENCY
    return generate_latest()

@app.on_event("startup")
async def startup():
    logger.info("Starting BillRun API...")
    # Create tables (in production, use Alembic migrations)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down BillRun API...")
    await engine.dispose()