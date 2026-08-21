-- =============================================================================
-- CRS Demo Seed Runner
-- Represents 5 Australian FMCG beverage distributors with 30 SKUs and
-- 52 weeks of realistic sales history (smooth/seasonal/intermittent demand).
-- Run order: tenants -> products -> sales -> inventory snapshots -> forecasts
-- =============================================================================

-- Tenants and products are loaded via docker-entrypoint-initdb.d file ordering.
-- This file adds inventory snapshots and audit bootstrap data.

-- ── Current inventory snapshots (as of 2026-08-20) ──────────────────────────
INSERT INTO fact_inventory
  (inv_id, tenant_id, product_id, snapshot_date, warehouse_code, on_hand, in_transit, allocated_qty)
VALUES
  -- Sydney: CSD-001 (Coca-Cola Classic 375mL) — healthy stock
  (gen_random_uuid(),
   (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-SYD' LIMIT 1),
   (SELECT product_id FROM dim_product WHERE sku_code='CSD-001' LIMIT 1),
   '2026-08-20', 'WH-SYD-001', 1440, 480, 240),

  -- Sydney: JUI-001 (Golden Circle Orange Juice) — low stock, reorder pending
  (gen_random_uuid(),
   (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-SYD' LIMIT 1),
   (SELECT product_id FROM dim_product WHERE sku_code='JUI-001' LIMIT 1),
   '2026-08-20', 'WH-SYD-001', 120, 180, 60),

  -- Sydney: ENE-001 (Red Bull Original) — normal intermittent position
  (gen_random_uuid(),
   (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-SYD' LIMIT 1),
   (SELECT product_id FROM dim_product WHERE sku_code='ENE-001' LIMIT 1),
   '2026-08-20', 'WH-SYD-001', 96, 0, 24),

  -- Melbourne: CSD-001 — high stock (pre-summer build)
  (gen_random_uuid(),
   (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-MEL' LIMIT 1),
   (SELECT product_id FROM dim_product WHERE sku_code='CSD-001' LIMIT 1),
   '2026-08-20', 'WH-MEL-001', 2880, 960, 480),

  -- Melbourne: JUI-003 (Juice Bros Tropical) — near stockout, critical reorder
  (gen_random_uuid(),
   (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-MEL' LIMIT 1),
   (SELECT product_id FROM dim_product WHERE sku_code='JUI-003' LIMIT 1),
   '2026-08-20', 'WH-MEL-001', 30, 90, 30),

  -- Brisbane: CSD-002 (Pepsi Max) — normal
  (gen_random_uuid(),
   (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-BNE' LIMIT 1),
   (SELECT product_id FROM dim_product WHERE sku_code='CSD-002' LIMIT 1),
   '2026-08-20', 'WH-BNE-001', 840, 360, 120),

  -- Perth: ENE-002 (Monster Energy) — credit hold, no in-transit
  (gen_random_uuid(),
   (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-PER' LIMIT 1),
   (SELECT product_id FROM dim_product WHERE sku_code='ENE-002' LIMIT 1),
   '2026-08-20', 'WH-PER-001', 48, 0, 0),

  -- Adelaide: CSD-003 (Solo Lemon) — adequate
  (gen_random_uuid(),
   (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-ADL' LIMIT 1),
   (SELECT product_id FROM dim_product WHERE sku_code='CSD-003' LIMIT 1),
   '2026-08-20', 'WH-ADL-001', 600, 120, 60);

-- ── Seed workflow_runs bootstrap row ─────────────────────────────────────────
-- The application will create workflow_runs at runtime; this one row provides
-- a reference for the credit_allocation_ledger demo record below.
INSERT INTO workflow_runs (run_id, tenant_id, run_date, state, started_at, completed_at, dry_run)
VALUES
  ('00000000-0000-0000-0000-000000000001',
   (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-SYD' LIMIT 1),
   '2026-08-20', 'COMPLETED', '2026-08-20 01:00:00+00', '2026-08-20 01:02:14+00', FALSE),
  ('00000000-0000-0000-0000-000000000002',
   (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-PER' LIMIT 1),
   '2026-08-20', 'COMPLETED', '2026-08-20 01:00:00+00', '2026-08-20 01:03:41+00', FALSE);

-- ── Seed credit_allocation_ledger rows ───────────────────────────────────────
INSERT INTO credit_allocation_ledger
  (ledger_id, tenant_id, workflow_run_id, credit_total, ar_outstanding, unbilled_pipeline,
   proposed_order_val, solver_status, solver_run_ms, allocated_order_val)
VALUES
  -- SYD: within limit — no solver needed
  (gen_random_uuid(),
   (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-SYD' LIMIT 1),
   '00000000-0000-0000-0000-000000000001',
   750000.00, 225000.00, 75000.00, 387500.00, 'WITHIN_LIMIT', NULL, 387500.00),

  -- PER: credit breach — fair-share applied
  (gen_random_uuid(),
   (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-PER' LIMIT 1),
   '00000000-0000-0000-0000-000000000002',
   480000.00, 192000.00, 48000.00, 285000.00, 'FAIR_SHARE_APPLIED', 847, 240000.00);
