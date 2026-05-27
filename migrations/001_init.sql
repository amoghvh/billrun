-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Idempotent events table (immutable log)
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    idempotency_key VARCHAR(255) NOT NULL UNIQUE,
    customer_id VARCHAR(100) NOT NULL,
    meter_name VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Materialized counters (optimized for billing queries)
CREATE TABLE counters (
    customer_id VARCHAR(100) NOT NULL,
    meter_name VARCHAR(100) NOT NULL,
    billing_month DATE NOT NULL, -- First day of month
    total_quantity BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (customer_id, meter_name, billing_month)
);

-- Bills table
CREATE TABLE bills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(100) NOT NULL,
    billing_month DATE NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    line_items JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, finalized, paid
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    finalized_at TIMESTAMP WITH TIME ZONE
);

-- Webhook delivery queue
CREATE TABLE webhook_deliveries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bill_id UUID REFERENCES bills(id),
    customer_id VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, delivered, failed
    retry_count INTEGER DEFAULT 0,
    last_attempt TIMESTAMP WITH TIME ZONE,
    next_retry TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_events_customer_id ON events (customer_id);
CREATE INDEX idx_events_timestamp ON events (timestamp);
CREATE INDEX idx_counters_billing_month ON counters (billing_month);
CREATE INDEX idx_bills_customer_month ON bills (customer_id, billing_month);
CREATE INDEX idx_webhook_status_retry ON webhook_deliveries (status, next_retry);