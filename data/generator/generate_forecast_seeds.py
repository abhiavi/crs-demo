#!/usr/bin/env python3
"""Generate 30 days of probabilistic forecast seeds (p10/p50/p90) for CRS demo."""

from datetime import date, timedelta
import random
import math

random.seed(99)

START = date(2026, 8, 21)

TENANTS = [
    "DIST-AU-SYD", "DIST-AU-MEL", "DIST-AU-BNE", "DIST-AU-PER", "DIST-AU-ADL"
]

FORECAST_CONFIGS = [
    # (sku_code, demand_class, base_daily, model)
    ("CSD-001", "SMOOTH",       68.6, "ETS"),
    ("CSD-002", "SMOOTH",       60.0, "ETS"),
    ("JUI-001", "SEASONAL",     17.1, "ARIMA"),
    ("JUI-003", "SEASONAL",     12.9, "ARIMA"),
    ("ENE-001", "INTERMITTENT", 10.3, "SBA"),
    ("ENE-002", "INTERMITTENT",  8.6, "SBA"),
]

AUS_SEASONAL = {
    8: 0.88, 9: 1.00, 10: 1.10, 11: 1.20, 12: 1.40, 1: 1.35,
    2: 1.25, 3: 1.10, 4: 0.95, 5: 0.85, 6: 0.75, 7: 0.78
}

print("-- CRS Demo: 30-day forward forecast seeds")
print("-- 6 SKUs x 5 tenants x 30 days = 900 rows")
print()
print("INSERT INTO fact_forecast")
print("  (forecast_id, tenant_id, product_id, generated_at, target_date, horizon_days,")
print("   p10, p50, p90, model_used, model_version)")
print("VALUES")

rows = []
for tenant_code in TENANTS:
    for sku_code, demand_class, base_daily, model in FORECAST_CONFIGS:
        for h in range(30):
            target = START + timedelta(days=h)
            sf = AUS_SEASONAL.get(target.month, 1.0)
            noise = random.uniform(0.95, 1.05)
            p50 = round(base_daily * sf * noise, 2)

            if demand_class == "SMOOTH":
                p10 = round(p50 * 0.80, 2)
                p90 = round(p50 * 1.20, 2)
            elif demand_class == "SEASONAL":
                p10 = round(p50 * 0.65, 2)
                p90 = round(p50 * 1.45, 2)
            else:  # INTERMITTENT
                p10 = 0.0
                p90 = round(p50 * 1.80, 2)

            rows.append(
                f"  (gen_random_uuid(), "
                f"(SELECT tenant_id FROM dim_tenant WHERE tenant_code='{tenant_code}' LIMIT 1), "
                f"(SELECT product_id FROM dim_product WHERE sku_code='{sku_code}' LIMIT 1), "
                f"NOW(), '{target}', {h+1}, "
                f"{p10}, {p50}, {p90}, '{model}', 'demo-v1.0')"
            )

print(",\n".join(rows) + ";")
