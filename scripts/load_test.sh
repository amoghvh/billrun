#!/bin/bash

echo "Running load test with 1000 requests..."

# Install hey if not present
if ! command -v hey &> /dev/null; then
    echo "Installing hey..."
    go install github.com/rakyll/hey@latest
fi

# Generate unique idempotency keys
hey -n 1000 -c 50 \
  -m POST \
  -H "Content-Type: application/json" \
  -d '{
    "idempotency_key": "load-test-{{.Iteration}}",
    "customer_id": "load_cust",
    "meter_name": "test_meter",
    "quantity": 1
  }' \
  http://localhost:8000/v1/ingest

echo ""
echo "Check metrics at http://localhost:9090"