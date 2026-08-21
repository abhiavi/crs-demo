#!/usr/bin/env python3
"""Generate workflow_runs and credit_allocation_ledger seed rows for CRS demo."""

from datetime import datetime, timedelta
import random

random.seed(77)

TENANTS = [
    "DIST-AU-SYD", "DIST-AU-MEL", "DIST-AU-BNE", "DIST-AU-PER", "DIST-AU-ADL"
]

STATES = [
    "COMPLETED", "COMPLETED", "COMPLETED", "COMPLETED",
    "SENSING", "APPROVAL_WAIT", "COMPLETED", "COMPLETED",
    "FAIR_SHARE_ALLOCATION", "COMPLETED",
]

BASE_DT = datetime(2026, 8, 20, 1, 0, 0)

print("-- CRS Demo: Workflow runs and credit ledger seeds")
print()

# workflow_runs (skip the 2 already seeded in 02_seed_runner.sql — start from index 3)
wf_rows = []
wf_ids = []
for i in range(3, 13):
    run_id = f"00000000-0000-0000-0000-{i:012d}"
    tenant = TENANTS[(i - 3) % 5]
    state = STATES[i - 3]
    started = BASE_DT - timedelta(days=(i - 3))
    duration_s = random.randint(45, 180)
    completed = started + timedelta(seconds=duration_s) if state == "COMPLETED" else None
    completed_sql = f"'{completed.strftime('%Y-%m-%d %H:%M:%S+00')}'" if completed else "NULL"
    run_date = started.date()
    wf_rows.append(
        f"  ('{run_id}', "
        f"(SELECT tenant_id FROM dim_tenant WHERE tenant_code='{tenant}' LIMIT 1), "
        f"'{run_date}', '{state}', '{started.strftime('%Y-%m-%d %H:%M:%S+00')}', "
        f"{completed_sql}, FALSE)"
    )
    wf_ids.append((run_id, tenant))

print("INSERT INTO workflow_runs")
print("  (run_id, tenant_id, run_date, state, started_at, completed_at, dry_run)")
print("VALUES")
print(",\n".join(wf_rows) + ";")
print()

# credit_allocation_ledger (5 additional rows beyond the 2 in 02_seed_runner.sql)
CREDIT_SCENARIOS = [
    ("DIST-AU-SYD", 750000, 0.30, 0.10, 0.48, "WITHIN_LIMIT",      None,  1.0),
    ("DIST-AU-MEL", 1200000, 0.25, 0.08, 0.55, "WITHIN_LIMIT",     None,  1.0),
    ("DIST-AU-BNE", 550000, 0.40, 0.15, 0.75, "FAIR_SHARE_APPLIED", 1243, 0.82),
    ("DIST-AU-PER", 480000, 0.45, 0.12, 0.85, "FAIR_SHARE_APPLIED", 967,  0.74),
    ("DIST-AU-ADL", 320000, 0.20, 0.05, 0.35, "WITHIN_LIMIT",      None,  1.0),
]

ledger_rows = []
for idx, (tc, credit, ar_pct, unbilled_pct, prop_pct, status, solver_ms, alloc_ratio) in enumerate(CREDIT_SCENARIOS):
    run_id = wf_ids[idx][0]
    ar = round(credit * ar_pct, 2)
    ub = round(credit * unbilled_pct, 2)
    avail = credit - ar - ub
    proposed = round(credit * prop_pct, 2)
    allocated = round(proposed * alloc_ratio, 2)
    solver_sql = str(solver_ms) if solver_ms else "NULL"
    ledger_rows.append(
        f"  (gen_random_uuid(), "
        f"(SELECT tenant_id FROM dim_tenant WHERE tenant_code='{tc}' LIMIT 1), "
        f"'{run_id}', {credit}.00, {ar}, {ub}, "
        f"{proposed}, '{status}', {solver_sql}, {allocated})"
    )

print("INSERT INTO credit_allocation_ledger")
print("  (ledger_id, tenant_id, workflow_run_id, credit_total, ar_outstanding,")
print("   unbilled_pipeline, proposed_order_val, solver_status, solver_run_ms, allocated_order_val)")
print("VALUES")
print(",\n".join(ledger_rows) + ";")
print()

# audit_override_log — 8 sample overrides
REASONS = [
    "PROMOTIONAL_UPLIFT", "SEASONAL_PRE_BUILD", "COMPETITOR_DISRUPTION",
    "ERRONEOUS_FORECAST", "CUSTOMER_COMMITMENT"
]
PERSONAS = ["DEMAND_PLANNER", "SALES", "EXECUTIVE", "DISTRIBUTOR"]
SKUS = ["CSD-001", "CSD-002", "JUI-001", "JUI-003", "ENE-001"]

override_rows = []
for i in range(8):
    tenant = TENANTS[i % 5]
    sku = SKUS[i % 5]
    persona = PERSONAS[i % 4]
    reason = REASONS[i % 5]
    orig = random.randint(200, 800)
    pct_change = random.uniform(-0.12, 0.15)
    override_qty = int(orig * (1 + pct_change))
    user_id = f"user-{persona.lower()[:4]}-{i+1:03d}"
    naive_mape = round(random.uniform(8, 18), 2)
    adjusted_mape = round(naive_mape + random.uniform(-4, 6), 2)
    run_id = wf_ids[i % len(wf_ids)][0]
    override_rows.append(
        f"  (gen_random_uuid(), "
        f"(SELECT tenant_id FROM dim_tenant WHERE tenant_code='{tenant}' LIMIT 1), "
        f"(SELECT product_id FROM dim_product WHERE sku_code='{sku}' LIMIT 1), "
        f"'{run_id}', NOW() - INTERVAL '{i*3} hours', '{persona}', '{user_id}', "
        f"'{reason}', 'Auto-generated demo override {i+1}', "
        f"{orig}, {override_qty}, {naive_mape}, {adjusted_mape}, FALSE)"
    )

print("INSERT INTO audit_override_log")
print("  (override_id, tenant_id, product_id, workflow_run_id, override_ts,")
print("   persona, user_id, reason_code, reason_description,")
print("   original_qty, overridden_qty, fva_naive_mape, fva_adjusted_mape, is_auto_approved)")
print("VALUES")
print(",\n".join(override_rows) + ";")
