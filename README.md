# BillRun - Production Usage-Based Billing Engine

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/amoghvh/billrun)
[![Coverage](https://img.shields.io/badge/coverage-85%25-green)](https://github.com/amoghvh/billrun)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://github.com/amoghvh/billrun)

**A production-grade billing system that handles idempotent event ingestion, real-time counters, and reliable webhook delivery.**
## Why I Built This

Usage-based pricing is everywhere (Stripe, OpenAI, AWS). Most engineers can build CRUD apps, but few understand:
- Idempotency at database isolation level
- Materialized counters vs. event replay
- Transactional webhook delivery

This project demonstrates those skills.


## Tech Stack

| Component | Technology |
|-----------|------------|
| API | FastAPI (async) |
| Database | PostgreSQL with SERIALIZABLE isolation |
| Caching | Redis (rate limiting) |
| Metrics | Prometheus + Grafana |
| Deployment | Docker + GitHub Actions |
| Testing | pytest + load testing (hey) |

## Key Technical Decisions

### 1. Idempotency via SERIALIZABLE Isolation
Instead of application-level locks, I use PostgreSQL's SERIALIZABLE isolation level + unique constraint on `idempotency_key`. This guarantees no double-counting even under concurrent requests.

### 2. Materialized Counters
Rather than summing events at bill time (O(n) scan), counters are updated incrementally. Bill generation becomes O(number of meters) not O(number of events).

### 3. Idempotent Webhooks
Webhook deliveries include `Idempotency-Key: {bill_id}` header. Customers can safely retry without double-processing.

## Quick Start
```bash
# Clone and run
git clone https://github.com/amoghvh/billrun
cd billrun
make up

# Run demo
make demo

# Run load test
make load-test
