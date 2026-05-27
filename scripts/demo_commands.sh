#!/bin/bash

echo "=== BillRun Demo ==="
echo ""

# Wait for services
sleep 5

echo "1. Ingestion (idempotent test)"
echo "Sending first request..."
curl -X POST http://localhost:8000/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "idempotency_key": "demo-key-001",
    "customer_id": "cust_123",
    "meter_name": "api_calls",
    "quantity": 100
  }' | jq .

echo ""
echo "Sending same idempotency_key again..."
curl -X POST http://localhost:8000/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "idempotency_key": "demo-key-001",
    "customer_id": "cust_123",
    "meter_name": "api_calls",
    "quantity": 100
  }' | jq .

echo ""
echo "2. Add more usage"
curl -X POST http://localhost:8000/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "idempotency_key": "demo-key-002",
    "customer_id": "cust_123",
    "meter_name": "api_calls",
    "quantity": 50
  }' | jq .

echo ""
echo "3. Run billing for May 2026"
curl -X POST http://localhost:8000/v1/run-bill \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust_123",
    "billing_month": "2026-05"
  }' | jq .

echo ""
echo "4. View customer events"
curl -s http://localhost:8000/v1/events/cust_123 | jq .

echo ""
echo "Demo complete!"