#!/usr/bin/env python3
"""
Generate 52 weeks of realistic FMCG beverage sales history for CRS demo.
Outputs INSERT INTO fact_sales SQL statements to stdout.
Date range: 2025-09-01 to 2026-08-20
5 tenants x 30 products x 364 days = ~54,600 rows
"""

import numpy as np
import random
import uuid
from datetime import date, timedelta

rng = np.random.default_rng(42)
random.seed(42)

# Tenant placeholder UUIDs (will be resolved via subquery in prod)
TENANTS = [
    ("DIST-AU-SYD", "a1000000-0000-0000-0000-000000000001"),
    ("DIST-AU-MEL", "a1000000-0000-0000-0000-000000000002"),
    ("DIST-AU-BNE", "a1000000-0000-0000-0000-000000000003"),
    ("DIST-AU-PER", "a1000000-0000-0000-0000-000000000004"),
    ("DIST-AU-ADL", "a1000000-0000-0000-0000-000000000005"),
]

# Products: (sku_code, product_uuid, demand_class, base_weekly_demand, abc_class)
PRODUCTS = [
    # CSD — SMOOTH, A/X
    ("CSD-001", "b0000001-0000-0000-0000-000000000000", "SMOOTH", 480, "A"),
    ("CSD-002", "b0000002-0000-0000-0000-000000000000", "SMOOTH", 420, "A"),
    ("CSD-003", "b0000003-0000-0000-0000-000000000000", "SMOOTH", 360, "A"),
    ("CSD-004", "b0000004-0000-0000-0000-000000000000", "SMOOTH", 300, "A"),
    ("CSD-005", "b0000005-0000-0000-0000-000000000000", "SMOOTH", 240, "A"),
    ("CSD-006", "b0000006-0000-0000-0000-000000000000", "SMOOTH", 220, "A"),
    ("CSD-007", "b0000007-0000-0000-0000-000000000000", "SMOOTH", 200, "A"),
    ("CSD-008", "b0000008-0000-0000-0000-000000000000", "SMOOTH", 180, "A"),
    ("CSD-009", "b0000009-0000-0000-0000-000000000000", "SMOOTH", 160, "A"),
    ("CSD-010", "b0000010-0000-0000-0000-000000000000", "SMOOTH", 140, "A"),
    # Juice — SEASONAL, B/Y
    ("JUI-001", "b0000011-0000-0000-0000-000000000000", "SEASONAL", 120, "B"),
    ("JUI-002", "b0000012-0000-0000-0000-000000000000", "SEASONAL", 100, "B"),
    ("JUI-003", "b0000013-0000-0000-0000-000000000000", "SEASONAL", 90, "B"),
    ("JUI-004", "b0000014-0000-0000-0000-000000000000", "SEASONAL", 80, "B"),
    ("JUI-005", "b0000015-0000-0000-0000-000000000000", "SEASONAL", 70, "B"),
    ("JUI-006", "b0000016-0000-0000-0000-000000000000", "SEASONAL", 65, "B"),
    ("JUI-007", "b0000017-0000-0000-0000-000000000000", "SEASONAL", 55, "B"),
    ("JUI-008", "b0000018-0000-0000-0000-000000000000", "SEASONAL", 75, "B"),
    ("JUI-009", "b0000019-0000-0000-0000-000000000000", "SEASONAL", 50, "B"),
    ("JUI-010", "b0000020-0000-0000-0000-000000000000", "SEASONAL", 60, "B"),
    # Energy — INTERMITTENT, C/Z
    ("ENE-001", "b0000021-0000-0000-0000-000000000000", "INTERMITTENT", 72, "C"),
    ("ENE-002", "b0000022-0000-0000-0000-000000000000", "INTERMITTENT", 60, "C"),
    ("ENE-003", "b0000023-0000-0000-0000-000000000000", "INTERMITTENT", 48, "C"),
    ("ENE-004", "b0000024-0000-0000-0000-000000000000", "INTERMITTENT", 42, "C"),
    ("ENE-005", "b0000025-0000-0000-0000-000000000000", "INTERMITTENT", 36, "C"),
    ("ENE-006", "b0000026-0000-0000-0000-000000000000", "INTERMITTENT", 30, "C"),
    ("ENE-007", "b0000027-0000-0000-0000-000000000000", "INTERMITTENT", 28, "C"),
    ("ENE-008", "b0000028-0000-0000-0000-000000000000", "INTERMITTENT", 24, "C"),
    ("ENE-009", "b0000029-0000-0000-0000-000000000000", "INTERMITTENT", 22, "C"),
    ("ENE-010", "b0000030-0000-0000-0000-000000000000", "INTERMITTENT", 18, "C"),
]

START_DATE = date(2025, 9, 1)
END_DATE = date(2026, 8, 20)


def aus_seasonal_factor(d: date) -> float:
    """Australian seasonal index — peaks Dec-Jan (summer), dips Jun-Jul (winter)."""
    month = d.month
    factors = {1: 1.35, 2: 1.25, 3: 1.10, 4: 0.95, 5: 0.85, 6: 0.75,
               7: 0.78, 8: 0.88, 9: 1.00, 10: 1.10, 11: 1.20, 12: 1.40}
    return factors.get(month, 1.0)


def generate_daily_qty(demand_class: str, base_weekly: int, d: date, abc_class: str) -> tuple:
    """Returns (raw_qty, imputed_qty, is_stockout)."""
    base_daily = base_weekly / 7.0
    stockout_prob = 0.05 if abc_class == "A" else (0.10 if abc_class == "B" else 0.18)

    if demand_class == "SMOOTH":
        noise = float(rng.uniform(0.85, 1.15))
        qty = max(0, int(round(base_daily * noise)))

    elif demand_class == "SEASONAL":
        sf = aus_seasonal_factor(d)
        noise = float(rng.uniform(0.80, 1.20))
        qty = max(0, int(round(base_daily * sf * noise)))

    else:  # INTERMITTENT
        if rng.random() < 0.40:  # 40% zero-demand weeks
            qty = 0
        else:
            noise = float(rng.uniform(0.5, 2.0))
            qty = max(0, int(round(base_daily * noise)))

    # Stockout injection
    is_stockout = False
    imputed_qty = qty
    if qty > 0 and rng.random() < stockout_prob / 7:  # per-day probability
        is_stockout = True
        imputed_qty = qty  # keep imputed = what demand would have been
        qty = 0

    return qty, float(imputed_qty), is_stockout


print("-- CRS Demo: FMCG Beverages sales history 2025-09-01 to 2026-08-20")
print("-- 5 tenants x 30 SKUs x ~354 days = ~53,100 rows")
print("-- Stockout events included with is_stockout=TRUE and imputed_qty preserved")
print()

current = START_DATE
all_dates = []
while current <= END_DATE:
    all_dates.append(current)
    current += timedelta(days=1)

batch = []
BATCH_SIZE = 500

def flush(batch):
    if not batch:
        return
    print("INSERT INTO fact_sales (sales_id, tenant_id, product_id, location_id, sale_date, raw_qty, imputed_qty, is_stockout, is_cold_start, source_system) VALUES")
    rows = []
    for row in batch:
        rows.append(
            f"  (gen_random_uuid(), "
            f"(SELECT tenant_id FROM dim_tenant WHERE tenant_code='{row[0]}' LIMIT 1), "
            f"'{row[1]}', '{row[2]}', '{row[3]}', "
            f"{row[4]}, {row[5]}, {str(row[6]).upper()}, FALSE, 'POS_SYNTHETIC')"
        )
    print(",\n".join(rows) + ";")
    print()

for tenant_code, tenant_uuid in TENANTS:
    loc_id = f"WH-{tenant_code.split('-')[2]}-001"
    for sku_code, prod_uuid, demand_class, base_weekly, abc_class in PRODUCTS:
        for d in all_dates:
            raw, imputed, is_stockout = generate_daily_qty(demand_class, base_weekly, d, abc_class)
            batch.append((tenant_code, prod_uuid, loc_id, str(d), raw, round(imputed, 4), is_stockout))
            if len(batch) >= BATCH_SIZE:
                flush(batch)
                batch = []

flush(batch)
