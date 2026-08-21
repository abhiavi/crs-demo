CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS dim_tenant (
    tenant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_code VARCHAR(32) UNIQUE NOT NULL,
    tenant_name VARCHAR(255) NOT NULL,
    credit_limit DECIMAL(18,4) NOT NULL CHECK (credit_limit >= 0),
    currency CHAR(3) DEFAULT 'USD',
    timezone VARCHAR(64) DEFAULT 'UTC',
    status VARCHAR(32) CHECK (status IN ('ACTIVE','SUSPENDED','CREDIT_HOLD','TERMINATED')) DEFAULT 'ACTIVE',
    review_period_days SMALLINT DEFAULT 7,
    default_service_lvl DECIMAL(5,4) DEFAULT 0.95,
    erp_account_code VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES dim_tenant(tenant_id),
    sku_code VARCHAR(64),
    sku_description VARCHAR(512),
    brand_code VARCHAR(64),
    price_tier SMALLINT CHECK (price_tier BETWEEN 1 AND 5),
    unit_cost DECIMAL(14,4) NOT NULL CHECK (unit_cost > 0),
    shelf_life_days SMALLINT,
    pkg_config VARCHAR(64),
    moq INTEGER DEFAULT 1 CHECK (moq >= 1),
    case_pack_qty INTEGER DEFAULT 1,
    pallet_tie SMALLINT DEFAULT 10,
    pallet_high SMALLINT DEFAULT 12,
    lead_time_days SMALLINT DEFAULT 7,
    lead_time_std_dev DECIMAL(6,2) DEFAULT 1.0,
    max_dos_ceiling SMALLINT DEFAULT 90,
    abc_class CHAR(1) CHECK (abc_class IN ('A','B','C')),
    xyz_class CHAR(1) CHECK (xyz_class IN ('X','Y','Z')),
    demand_model VARCHAR(32) CHECK (demand_model IN ('ETS','ARIMA','SBA','TFT','MANUAL')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, sku_code)
);

CREATE TABLE IF NOT EXISTS fact_sales (
    sales_id UUID DEFAULT uuid_generate_v4(),
    tenant_id UUID,
    product_id UUID,
    location_id VARCHAR(64),
    sale_date DATE NOT NULL,
    raw_qty INTEGER DEFAULT 0 CHECK (raw_qty >= 0),
    imputed_qty DECIMAL(12,4) DEFAULT 0,
    is_stockout BOOLEAN DEFAULT FALSE,
    is_cold_start BOOLEAN DEFAULT FALSE,
    source_system VARCHAR(64),
    idempotency_key VARCHAR(255) UNIQUE,
    PRIMARY KEY(sales_id, sale_date)
) PARTITION BY RANGE (sale_date);

CREATE INDEX IF NOT EXISTS idx_fact_sales_lookup ON fact_sales (tenant_id, product_id, sale_date DESC);

CREATE TABLE IF NOT EXISTS fact_sales_2024 PARTITION OF fact_sales FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
CREATE TABLE IF NOT EXISTS fact_sales_2025 PARTITION OF fact_sales FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE IF NOT EXISTS fact_sales_2026 PARTITION OF fact_sales FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

CREATE TABLE IF NOT EXISTS fact_inventory (
    inv_id UUID DEFAULT uuid_generate_v4(),
    tenant_id UUID,
    product_id UUID,
    snapshot_date DATE NOT NULL,
    warehouse_code VARCHAR(64),
    on_hand INTEGER DEFAULT 0 CHECK (on_hand >= 0),
    in_transit INTEGER DEFAULT 0 CHECK (in_transit >= 0),
    allocated_qty INTEGER DEFAULT 0 CHECK (allocated_qty >= 0),
    net_inventory_pos INTEGER GENERATED ALWAYS AS (on_hand - allocated_qty + in_transit) STORED,
    PRIMARY KEY(inv_id, snapshot_date)
) PARTITION BY RANGE (snapshot_date);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fact_inventory ON fact_inventory (tenant_id, product_id, warehouse_code, snapshot_date);

CREATE TABLE IF NOT EXISTS fact_inventory_2024 PARTITION OF fact_inventory FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
CREATE TABLE IF NOT EXISTS fact_inventory_2025 PARTITION OF fact_inventory FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE IF NOT EXISTS fact_inventory_2026 PARTITION OF fact_inventory FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

CREATE TABLE IF NOT EXISTS fact_forecast (
    forecast_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID,
    product_id UUID,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    target_date DATE NOT NULL,
    horizon_days SMALLINT,
    p10 DECIMAL(14,4) CHECK (p10 >= 0),
    p50 DECIMAL(14,4) CHECK (p50 >= 0),
    p90 DECIMAL(14,4) CHECK (p90 >= 0),
    model_used VARCHAR(32),
    model_version VARCHAR(64),
    adi_score DECIMAL(8,4),
    cv2_score DECIMAL(8,4),
    run_id UUID
);

CREATE INDEX IF NOT EXISTS idx_fact_forecast_lookup ON fact_forecast (tenant_id, product_id, target_date DESC);

CREATE TABLE IF NOT EXISTS audit_override_log (
    override_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID,
    product_id UUID,
    workflow_run_id VARCHAR(255),
    override_ts TIMESTAMPTZ DEFAULT NOW(),
    persona VARCHAR(32) CHECK (persona IN ('DEMAND_PLANNER','SALES','EXECUTIVE','DISTRIBUTOR','CREDIT_ADMIN')),
    user_id VARCHAR(255),
    reason_code VARCHAR(64),
    reason_description TEXT,
    original_qty DECIMAL(14,4),
    overridden_qty DECIMAL(14,4),
    pct_change DECIMAL(8,4) GENERATED ALWAYS AS (
        CASE WHEN original_qty = 0 THEN NULL ELSE (overridden_qty - original_qty) / original_qty * 100 END
    ) STORED,
    fva_naive_mape DECIMAL(8,4),
    fva_adjusted_mape DECIMAL(8,4),
    is_auto_approved BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS credit_allocation_ledger (
    ledger_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID,
    workflow_run_id VARCHAR(255),
    ledger_ts TIMESTAMPTZ DEFAULT NOW(),
    credit_total DECIMAL(18,4),
    ar_outstanding DECIMAL(18,4) DEFAULT 0,
    unbilled_pipeline DECIMAL(18,4) DEFAULT 0,
    credit_available DECIMAL(18,4) GENERATED ALWAYS AS (credit_total - ar_outstanding - unbilled_pipeline) STORED,
    proposed_order_val DECIMAL(18,4),
    solver_status VARCHAR(32) CHECK (solver_status IN ('WITHIN_LIMIT','CREDIT_HOLD','FAIR_SHARE_APPLIED','MANUAL_RELEASE')),
    solver_run_ms INTEGER,
    allocated_order_val DECIMAL(18,4)
);

CREATE INDEX IF NOT EXISTS idx_credit_allocation_ledger ON credit_allocation_ledger (tenant_id, ledger_ts DESC);

CREATE TABLE IF NOT EXISTS workflow_runs (
    run_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID,
    run_date DATE,
    state VARCHAR(32) DEFAULT 'SENSING',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    dry_run BOOLEAN DEFAULT FALSE
);