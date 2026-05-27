-- Additional performance indexes
CREATE INDEX CONCURRENTLY idx_events_idempotency ON events (idempotency_key);
CREATE INDEX CONCURRENTLY idx_counters_lookup ON counters (customer_id, billing_month);
CREATE INDEX CONCURRENTLY idx_bills_status ON bills (status);