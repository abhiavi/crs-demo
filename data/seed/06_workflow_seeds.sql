-- CRS Demo: Workflow runs and credit ledger seeds

INSERT INTO workflow_runs
  (run_id, tenant_id, run_date, state, started_at, completed_at, dry_run)
VALUES
  ('00000000-0000-0000-0000-000000000003', (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-SYD' LIMIT 1), '2026-08-20', 'COMPLETED', '2026-08-20 01:00:00+00', '2026-08-20 01:01:49+00', FALSE),
  ('00000000-0000-0000-0000-000000000004', (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-MEL' LIMIT 1), '2026-08-19', 'COMPLETED', '2026-08-19 01:00:00+00', '2026-08-19 01:02:08+00', FALSE),
  ('00000000-0000-0000-0000-000000000005', (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-BNE' LIMIT 1), '2026-08-18', 'COMPLETED', '2026-08-18 01:00:00+00', '2026-08-18 01:01:35+00', FALSE),
  ('00000000-0000-0000-0000-000000000006', (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-PER' LIMIT 1), '2026-08-17', 'COMPLETED', '2026-08-17 01:00:00+00', '2026-08-17 01:01:46+00', FALSE),
  ('00000000-0000-0000-0000-000000000007', (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-ADL' LIMIT 1), '2026-08-16', 'SENSING', '2026-08-16 01:00:00+00', NULL, FALSE),
  ('00000000-0000-0000-0000-000000000008', (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-SYD' LIMIT 1), '2026-08-15', 'APPROVAL_WAIT', '2026-08-15 01:00:00+00', NULL, FALSE),
  ('00000000-0000-0000-0000-000000000009', (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-MEL' LIMIT 1), '2026-08-14', 'COMPLETED', '2026-08-14 01:00:00+00', '2026-08-14 01:01:59+00', FALSE),
  ('00000000-0000-0000-0000-000000000010', (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-BNE' LIMIT 1), '2026-08-13', 'COMPLETED', '2026-08-13 01:00:00+00', '2026-08-13 01:02:46+00', FALSE),
  ('00000000-0000-0000-0000-000000000011', (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-PER' LIMIT 1), '2026-08-12', 'FAIR_SHARE_ALLOCATION', '2026-08-12 01:00:00+00', NULL, FALSE),
  ('00000000-0000-0000-0000-000000000012', (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-ADL' LIMIT 1), '2026-08-11', 'COMPLETED', '2026-08-11 01:00:00+00', '2026-08-11 01:01:22+00', FALSE);

INSERT INTO credit_allocation_ledger
  (ledger_id, tenant_id, workflow_run_id, credit_total, ar_outstanding,
   unbilled_pipeline, proposed_order_val, solver_status, solver_run_ms, allocated_order_val)
VALUES
  (gen_random_uuid(), (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-SYD' LIMIT 1), '00000000-0000-0000-0000-000000000003', 750000.00, 225000.0, 75000.0, 360000.0, 'WITHIN_LIMIT', NULL, 360000.0),
  (gen_random_uuid(), (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-MEL' LIMIT 1), '00000000-0000-0000-0000-000000000004', 1200000.00, 300000.0, 96000.0, 660000.0, 'WITHIN_LIMIT', NULL, 660000.0),
  (gen_random_uuid(), (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-BNE' LIMIT 1), '00000000-0000-0000-0000-000000000005', 550000.00, 220000.0, 82500.0, 412500.0, 'FAIR_SHARE_APPLIED', 1243, 338250.0),
  (gen_random_uuid(), (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-PER' LIMIT 1), '00000000-0000-0000-0000-000000000006', 480000.00, 216000.0, 57600.0, 408000.0, 'FAIR_SHARE_APPLIED', 967, 301920.0),
  (gen_random_uuid(), (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-ADL' LIMIT 1), '00000000-0000-0000-0000-000000000007', 320000.00, 64000.0, 16000.0, 112000.0, 'WITHIN_LIMIT', NULL, 112000.0);

INSERT INTO audit_override_log
  (override_id, tenant_id, product_id, workflow_run_id, override_ts,
   persona, user_id, reason_code, reason_description,
   original_qty, overridden_qty, fva_naive_mape, fva_adjusted_mape, is_auto_approved)
VALUES
  (gen_random_uuid(), (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-SYD' LIMIT 1), (SELECT product_id FROM dim_product WHERE sku_code='CSD-001' LIMIT 1), '00000000-0000-0000-0000-000000000003', NOW() - INTERVAL '0 hours', 'DEMAND_PLANNER', 'user-dema-001', 'PROMOTIONAL_UPLIFT', 'Auto-generated demo override 1', 769, 807, 13.01, 17.52, FALSE),
  (gen_random_uuid(), (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-MEL' LIMIT 1), (SELECT product_id FROM dim_product WHERE sku_code='CSD-002' LIMIT 1), '00000000-0000-0000-0000-000000000004', NOW() - INTERVAL '3 hours', 'SALES', 'user-sale-002', 'SEASONAL_PRE_BUILD', 'Auto-generated demo override 2', 229, 253, 12.97, 16.89, FALSE),
  (gen_random_uuid(), (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-BNE' LIMIT 1), (SELECT product_id FROM dim_product WHERE sku_code='JUI-001' LIMIT 1), '00000000-0000-0000-0000-000000000005', NOW() - INTERVAL '6 hours', 'EXECUTIVE', 'user-exec-003', 'COMPETITOR_DISRUPTION', 'Auto-generated demo override 3', 395, 401, 16.36, 14.19, FALSE),
  (gen_random_uuid(), (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-PER' LIMIT 1), (SELECT product_id FROM dim_product WHERE sku_code='JUI-003' LIMIT 1), '00000000-0000-0000-0000-000000000006', NOW() - INTERVAL '9 hours', 'DISTRIBUTOR', 'user-dist-004', 'ERRONEOUS_FORECAST', 'Auto-generated demo override 4', 529, 482, 13.51, 12.11, FALSE),
  (gen_random_uuid(), (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-ADL' LIMIT 1), (SELECT product_id FROM dim_product WHERE sku_code='ENE-001' LIMIT 1), '00000000-0000-0000-0000-000000000007', NOW() - INTERVAL '12 hours', 'DEMAND_PLANNER', 'user-dema-005', 'CUSTOMER_COMMITMENT', 'Auto-generated demo override 5', 680, 636, 9.92, 6.73, FALSE),
  (gen_random_uuid(), (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-SYD' LIMIT 1), (SELECT product_id FROM dim_product WHERE sku_code='CSD-001' LIMIT 1), '00000000-0000-0000-0000-000000000008', NOW() - INTERVAL '15 hours', 'SALES', 'user-sale-006', 'PROMOTIONAL_UPLIFT', 'Auto-generated demo override 6', 404, 431, 17.01, 18.96, FALSE),
  (gen_random_uuid(), (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-MEL' LIMIT 1), (SELECT product_id FROM dim_product WHERE sku_code='CSD-002' LIMIT 1), '00000000-0000-0000-0000-000000000009', NOW() - INTERVAL '18 hours', 'EXECUTIVE', 'user-exec-007', 'SEASONAL_PRE_BUILD', 'Auto-generated demo override 7', 751, 676, 16.39, 22.21, FALSE),
  (gen_random_uuid(), (SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-BNE' LIMIT 1), (SELECT product_id FROM dim_product WHERE sku_code='JUI-001' LIMIT 1), '00000000-0000-0000-0000-000000000010', NOW() - INTERVAL '21 hours', 'DISTRIBUTOR', 'user-dist-008', 'COMPETITOR_DISRUPTION', 'Auto-generated demo override 8', 417, 450, 16.5, 13.45, FALSE);
