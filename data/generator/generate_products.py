#!/usr/bin/env python3
"""Generate INSERT statements for 30 FMCG beverage SKUs across 3 demand categories."""

import sys

# Fixed tenant UUIDs aligned with seed order
TENANT_SYD = "a1000000-0000-0000-0000-000000000001"
TENANT_MEL = "a1000000-0000-0000-0000-000000000002"
TENANT_BNE = "a1000000-0000-0000-0000-000000000003"
TENANT_PER = "a1000000-0000-0000-0000-000000000004"
TENANT_ADL = "a1000000-0000-0000-0000-000000000005"

# All products assigned to SYD tenant for simplicity in seed; real distribution via fact_sales
TENANT_ID = TENANT_SYD

SKUS = [
    # ── Category 1: Carbonated Soft Drinks — SMOOTH/ETS, abc=A, xyz=X ──
    {
        "sku_code": "CSD-001", "sku_description": "Coca-Cola Classic 375mL Can 24pk",
        "brand_code": "COCA-COLA", "price_tier": 2, "unit_cost": 12.50,
        "shelf_life_days": 270, "pkg_config": "MULTI_24", "moq": 120,
        "case_pack_qty": 24, "pallet_tie": 10, "pallet_high": 12,
        "lead_time_days": 7, "lead_time_std_dev": 1.0, "max_dos_ceiling": 90,
        "abc_class": "A", "xyz_class": "X", "demand_model": "ETS",
    },
    {
        "sku_code": "CSD-002", "sku_description": "Pepsi Max 375mL Can 30pk",
        "brand_code": "PEPSI", "price_tier": 2, "unit_cost": 11.80,
        "shelf_life_days": 270, "pkg_config": "MULTI_30", "moq": 120,
        "case_pack_qty": 30, "pallet_tie": 10, "pallet_high": 12,
        "lead_time_days": 7, "lead_time_std_dev": 1.0, "max_dos_ceiling": 90,
        "abc_class": "A", "xyz_class": "X", "demand_model": "ETS",
    },
    {
        "sku_code": "CSD-003", "sku_description": "Solo Lemon 375mL Can 24pk",
        "brand_code": "SOLO", "price_tier": 1, "unit_cost": 9.90,
        "shelf_life_days": 270, "pkg_config": "MULTI_24", "moq": 120,
        "case_pack_qty": 24, "pallet_tie": 10, "pallet_high": 12,
        "lead_time_days": 7, "lead_time_std_dev": 1.0, "max_dos_ceiling": 90,
        "abc_class": "A", "xyz_class": "X", "demand_model": "ETS",
    },
    {
        "sku_code": "CSD-004", "sku_description": "Sprite Zero 600mL PET 24pk",
        "brand_code": "SPRITE", "price_tier": 2, "unit_cost": 14.20,
        "shelf_life_days": 365, "pkg_config": "MULTI_24", "moq": 120,
        "case_pack_qty": 24, "pallet_tie": 10, "pallet_high": 10,
        "lead_time_days": 7, "lead_time_std_dev": 1.2, "max_dos_ceiling": 90,
        "abc_class": "A", "xyz_class": "X", "demand_model": "ETS",
    },
    {
        "sku_code": "CSD-005", "sku_description": "Fanta Orange 1.25L PET 12pk",
        "brand_code": "FANTA", "price_tier": 2, "unit_cost": 13.40,
        "shelf_life_days": 365, "pkg_config": "MULTI_12", "moq": 120,
        "case_pack_qty": 12, "pallet_tie": 10, "pallet_high": 12,
        "lead_time_days": 7, "lead_time_std_dev": 1.0, "max_dos_ceiling": 90,
        "abc_class": "A", "xyz_class": "X", "demand_model": "ETS",
    },
    {
        "sku_code": "CSD-006", "sku_description": "Bundaberg Ginger Beer 375mL 24pk",
        "brand_code": "BUNDABERG", "price_tier": 3, "unit_cost": 13.20,
        "shelf_life_days": 365, "pkg_config": "MULTI_24", "moq": 120,
        "case_pack_qty": 24, "pallet_tie": 10, "pallet_high": 10,
        "lead_time_days": 7, "lead_time_std_dev": 1.0, "max_dos_ceiling": 90,
        "abc_class": "A", "xyz_class": "X", "demand_model": "ETS",
    },
    {
        "sku_code": "CSD-007", "sku_description": "Schweppes Lemonade 1.1L 12pk",
        "brand_code": "SCHWEPPES", "price_tier": 2, "unit_cost": 10.80,
        "shelf_life_days": 365, "pkg_config": "MULTI_12", "moq": 120,
        "case_pack_qty": 12, "pallet_tie": 10, "pallet_high": 12,
        "lead_time_days": 7, "lead_time_std_dev": 1.0, "max_dos_ceiling": 90,
        "abc_class": "A", "xyz_class": "X", "demand_model": "ETS",
    },
    {
        "sku_code": "CSD-008", "sku_description": "Mountain Dew 600mL PET 24pk",
        "brand_code": "MTN-DEW", "price_tier": 2, "unit_cost": 14.00,
        "shelf_life_days": 365, "pkg_config": "MULTI_24", "moq": 120,
        "case_pack_qty": 24, "pallet_tie": 10, "pallet_high": 10,
        "lead_time_days": 7, "lead_time_std_dev": 1.2, "max_dos_ceiling": 90,
        "abc_class": "A", "xyz_class": "X", "demand_model": "ETS",
    },
    {
        "sku_code": "CSD-009", "sku_description": "Kirks Creaming Soda 375mL 24pk",
        "brand_code": "KIRKS", "price_tier": 1, "unit_cost": 8.60,
        "shelf_life_days": 270, "pkg_config": "MULTI_24", "moq": 120,
        "case_pack_qty": 24, "pallet_tie": 10, "pallet_high": 12,
        "lead_time_days": 7, "lead_time_std_dev": 1.0, "max_dos_ceiling": 90,
        "abc_class": "A", "xyz_class": "X", "demand_model": "ETS",
    },
    {
        "sku_code": "CSD-010", "sku_description": "Coca-Cola No Sugar 2L PET 9pk",
        "brand_code": "COCA-COLA", "price_tier": 2, "unit_cost": 11.20,
        "shelf_life_days": 270, "pkg_config": "MULTI_9", "moq": 120,
        "case_pack_qty": 9, "pallet_tie": 10, "pallet_high": 12,
        "lead_time_days": 7, "lead_time_std_dev": 1.0, "max_dos_ceiling": 90,
        "abc_class": "A", "xyz_class": "X", "demand_model": "ETS",
    },

    # ── Category 2: Juice & Nectars — SEASONAL/ARIMA, abc=B, xyz=Y ──
    {
        "sku_code": "JUI-001", "sku_description": "Golden Circle Orange Juice 2L 6pk",
        "brand_code": "GOLDEN-CIRCLE", "price_tier": 3, "unit_cost": 17.40,
        "shelf_life_days": 90, "pkg_config": "MULTI_6", "moq": 60,
        "case_pack_qty": 6, "pallet_tie": 8, "pallet_high": 10,
        "lead_time_days": 10, "lead_time_std_dev": 2.0, "max_dos_ceiling": 60,
        "abc_class": "B", "xyz_class": "Y", "demand_model": "ARIMA",
    },
    {
        "sku_code": "JUI-002", "sku_description": "Berri Apple Juice 1L 12pk",
        "brand_code": "BERRI", "price_tier": 2, "unit_cost": 14.80,
        "shelf_life_days": 120, "pkg_config": "MULTI_12", "moq": 60,
        "case_pack_qty": 12, "pallet_tie": 8, "pallet_high": 10,
        "lead_time_days": 10, "lead_time_std_dev": 2.0, "max_dos_ceiling": 60,
        "abc_class": "B", "xyz_class": "Y", "demand_model": "ARIMA",
    },
    {
        "sku_code": "JUI-003", "sku_description": "Juice Bros Tropical Blend 300mL 24pk",
        "brand_code": "JUICE-BROS", "price_tier": 3, "unit_cost": 19.20,
        "shelf_life_days": 60, "pkg_config": "MULTI_24", "moq": 60,
        "case_pack_qty": 24, "pallet_tie": 8, "pallet_high": 10,
        "lead_time_days": 10, "lead_time_std_dev": 2.5, "max_dos_ceiling": 45,
        "abc_class": "B", "xyz_class": "Y", "demand_model": "ARIMA",
    },
    {
        "sku_code": "JUI-004", "sku_description": "Daily Juice Mango Nectar 1L 12pk",
        "brand_code": "DAILY-JUICE", "price_tier": 3, "unit_cost": 16.50,
        "shelf_life_days": 90, "pkg_config": "MULTI_12", "moq": 60,
        "case_pack_qty": 12, "pallet_tie": 8, "pallet_high": 10,
        "lead_time_days": 10, "lead_time_std_dev": 2.0, "max_dos_ceiling": 60,
        "abc_class": "B", "xyz_class": "Y", "demand_model": "ARIMA",
    },
    {
        "sku_code": "JUI-005", "sku_description": "Nudie Nothing But Juice Orange 1L 6pk",
        "brand_code": "NUDIE", "price_tier": 4, "unit_cost": 21.60,
        "shelf_life_days": 21, "pkg_config": "MULTI_6", "moq": 60,
        "case_pack_qty": 6, "pallet_tie": 6, "pallet_high": 8,
        "lead_time_days": 7, "lead_time_std_dev": 1.5, "max_dos_ceiling": 30,
        "abc_class": "B", "xyz_class": "Y", "demand_model": "ARIMA",
    },
    {
        "sku_code": "JUI-006", "sku_description": "Nippy's Cranberry Juice 2L 6pk",
        "brand_code": "NIPPYS", "price_tier": 3, "unit_cost": 15.90,
        "shelf_life_days": 90, "pkg_config": "MULTI_6", "moq": 60,
        "case_pack_qty": 6, "pallet_tie": 8, "pallet_high": 10,
        "lead_time_days": 10, "lead_time_std_dev": 2.0, "max_dos_ceiling": 60,
        "abc_class": "B", "xyz_class": "Y", "demand_model": "ARIMA",
    },
    {
        "sku_code": "JUI-007", "sku_description": "Preshafood Pressed Juice Green 350mL 12pk",
        "brand_code": "PRESHAFOOD", "price_tier": 5, "unit_cost": 22.00,
        "shelf_life_days": 14, "pkg_config": "MULTI_12", "moq": 60,
        "case_pack_qty": 12, "pallet_tie": 6, "pallet_high": 8,
        "lead_time_days": 5, "lead_time_std_dev": 1.0, "max_dos_ceiling": 21,
        "abc_class": "B", "xyz_class": "Y", "demand_model": "ARIMA",
    },
    {
        "sku_code": "JUI-008", "sku_description": "Golden Circle Pineapple Juice 1L 12pk",
        "brand_code": "GOLDEN-CIRCLE", "price_tier": 3, "unit_cost": 14.40,
        "shelf_life_days": 120, "pkg_config": "MULTI_12", "moq": 60,
        "case_pack_qty": 12, "pallet_tie": 8, "pallet_high": 10,
        "lead_time_days": 10, "lead_time_std_dev": 2.0, "max_dos_ceiling": 60,
        "abc_class": "B", "xyz_class": "Y", "demand_model": "ARIMA",
    },
    {
        "sku_code": "JUI-009", "sku_description": "Ceres Organics Pomegranate Juice 330mL 12pk",
        "brand_code": "CERES", "price_tier": 4, "unit_cost": 19.80,
        "shelf_life_days": 180, "pkg_config": "MULTI_12", "moq": 60,
        "case_pack_qty": 12, "pallet_tie": 8, "pallet_high": 10,
        "lead_time_days": 14, "lead_time_std_dev": 3.0, "max_dos_ceiling": 90,
        "abc_class": "B", "xyz_class": "Y", "demand_model": "ARIMA",
    },
    {
        "sku_code": "JUI-010", "sku_description": "Angas Park Tomato Juice 1L 12pk",
        "brand_code": "ANGAS-PARK", "price_tier": 2, "unit_cost": 12.60,
        "shelf_life_days": 180, "pkg_config": "MULTI_12", "moq": 60,
        "case_pack_qty": 12, "pallet_tie": 8, "pallet_high": 10,
        "lead_time_days": 10, "lead_time_std_dev": 2.0, "max_dos_ceiling": 60,
        "abc_class": "B", "xyz_class": "Y", "demand_model": "ARIMA",
    },

    # ── Category 3: Energy Drinks & Sports — INTERMITTENT/SBA, abc=C, xyz=Z ──
    {
        "sku_code": "ENE-001", "sku_description": "Red Bull Original 250mL Can 24pk",
        "brand_code": "RED-BULL", "price_tier": 4, "unit_cost": 28.80,
        "shelf_life_days": 730, "pkg_config": "MULTI_24", "moq": 24,
        "case_pack_qty": 24, "pallet_tie": 6, "pallet_high": 8,
        "lead_time_days": 14, "lead_time_std_dev": 3.0, "max_dos_ceiling": 120,
        "abc_class": "C", "xyz_class": "Z", "demand_model": "SBA",
    },
    {
        "sku_code": "ENE-002", "sku_description": "Monster Energy Green 500mL Can 24pk",
        "brand_code": "MONSTER", "price_tier": 4, "unit_cost": 30.00,
        "shelf_life_days": 730, "pkg_config": "MULTI_24", "moq": 24,
        "case_pack_qty": 24, "pallet_tie": 6, "pallet_high": 8,
        "lead_time_days": 14, "lead_time_std_dev": 3.0, "max_dos_ceiling": 120,
        "abc_class": "C", "xyz_class": "Z", "demand_model": "SBA",
    },
    {
        "sku_code": "ENE-003", "sku_description": "Powerade Mountain Blast 600mL 12pk",
        "brand_code": "POWERADE", "price_tier": 3, "unit_cost": 19.20,
        "shelf_life_days": 365, "pkg_config": "MULTI_12", "moq": 24,
        "case_pack_qty": 12, "pallet_tie": 6, "pallet_high": 10,
        "lead_time_days": 14, "lead_time_std_dev": 2.5, "max_dos_ceiling": 90,
        "abc_class": "C", "xyz_class": "Z", "demand_model": "SBA",
    },
    {
        "sku_code": "ENE-004", "sku_description": "V Energy Original 250mL Can 24pk",
        "brand_code": "V-ENERGY", "price_tier": 3, "unit_cost": 24.00,
        "shelf_life_days": 365, "pkg_config": "MULTI_24", "moq": 24,
        "case_pack_qty": 24, "pallet_tie": 6, "pallet_high": 8,
        "lead_time_days": 14, "lead_time_std_dev": 3.0, "max_dos_ceiling": 120,
        "abc_class": "C", "xyz_class": "Z", "demand_model": "SBA",
    },
    {
        "sku_code": "ENE-005", "sku_description": "Gatorade Blue Bolt 600mL 12pk",
        "brand_code": "GATORADE", "price_tier": 3, "unit_cost": 18.50,
        "shelf_life_days": 365, "pkg_config": "MULTI_12", "moq": 24,
        "case_pack_qty": 12, "pallet_tie": 6, "pallet_high": 10,
        "lead_time_days": 14, "lead_time_std_dev": 2.5, "max_dos_ceiling": 90,
        "abc_class": "C", "xyz_class": "Z", "demand_model": "SBA",
    },
    {
        "sku_code": "ENE-006", "sku_description": "Rockstar Original Energy 500mL 24pk",
        "brand_code": "ROCKSTAR", "price_tier": 4, "unit_cost": 27.60,
        "shelf_life_days": 730, "pkg_config": "MULTI_24", "moq": 24,
        "case_pack_qty": 24, "pallet_tie": 6, "pallet_high": 8,
        "lead_time_days": 14, "lead_time_std_dev": 3.5, "max_dos_ceiling": 120,
        "abc_class": "C", "xyz_class": "Z", "demand_model": "SBA",
    },
    {
        "sku_code": "ENE-007", "sku_description": "Mother Energy Original 500mL 24pk",
        "brand_code": "MOTHER", "price_tier": 3, "unit_cost": 23.40,
        "shelf_life_days": 365, "pkg_config": "MULTI_24", "moq": 24,
        "case_pack_qty": 24, "pallet_tie": 6, "pallet_high": 8,
        "lead_time_days": 14, "lead_time_std_dev": 3.0, "max_dos_ceiling": 120,
        "abc_class": "C", "xyz_class": "Z", "demand_model": "SBA",
    },
    {
        "sku_code": "ENE-008", "sku_description": "Mizone Activ+ Orange 500mL 12pk",
        "brand_code": "MIZONE", "price_tier": 2, "unit_cost": 18.00,
        "shelf_life_days": 365, "pkg_config": "MULTI_12", "moq": 24,
        "case_pack_qty": 12, "pallet_tie": 6, "pallet_high": 10,
        "lead_time_days": 14, "lead_time_std_dev": 2.5, "max_dos_ceiling": 90,
        "abc_class": "C", "xyz_class": "Z", "demand_model": "SBA",
    },
    {
        "sku_code": "ENE-009", "sku_description": "Red Bull Sugar Free 250mL 24pk",
        "brand_code": "RED-BULL", "price_tier": 4, "unit_cost": 29.40,
        "shelf_life_days": 730, "pkg_config": "MULTI_24", "moq": 24,
        "case_pack_qty": 24, "pallet_tie": 6, "pallet_high": 8,
        "lead_time_days": 14, "lead_time_std_dev": 3.0, "max_dos_ceiling": 120,
        "abc_class": "C", "xyz_class": "Z", "demand_model": "SBA",
    },
    {
        "sku_code": "ENE-010", "sku_description": "Hydralyte Sports Lemon Lime 500mL 12pk",
        "brand_code": "HYDRALYTE", "price_tier": 4, "unit_cost": 34.80,
        "shelf_life_days": 730, "pkg_config": "MULTI_12", "moq": 24,
        "case_pack_qty": 12, "pallet_tie": 6, "pallet_high": 8,
        "lead_time_days": 14, "lead_time_std_dev": 4.0, "max_dos_ceiling": 120,
        "abc_class": "C", "xyz_class": "Z", "demand_model": "SBA",
    },
]

lines = ["-- 30 FMCG beverage SKUs: 10 CSD (A/X), 10 Juice (B/Y), 10 Energy (C/Z)"]
lines.append("-- tenant_id references are placeholder UUIDs; replaced via JOIN in production")
lines.append("")

for i, sku in enumerate(SKUS, 1):
    product_uuid = f"b{i:07d}-0000-0000-0000-000000000000"
    sql = (
        f"INSERT INTO dim_product (product_id, tenant_id, sku_code, sku_description, brand_code, "
        f"price_tier, unit_cost, shelf_life_days, pkg_config, moq, case_pack_qty, pallet_tie, pallet_high, "
        f"lead_time_days, lead_time_std_dev, max_dos_ceiling, abc_class, xyz_class, demand_model, is_active) VALUES ("
        f"'{product_uuid}', "
        f"(SELECT tenant_id FROM dim_tenant WHERE tenant_code='DIST-AU-SYD' LIMIT 1), "
        f"'{sku['sku_code']}', '{sku['sku_description']}', '{sku['brand_code']}', "
        f"{sku['price_tier']}, {sku['unit_cost']}, {sku['shelf_life_days']}, '{sku['pkg_config']}', "
        f"{sku['moq']}, {sku['case_pack_qty']}, {sku['pallet_tie']}, {sku['pallet_high']}, "
        f"{sku['lead_time_days']}, {sku['lead_time_std_dev']}, {sku['max_dos_ceiling']}, "
        f"'{sku['abc_class']}', '{sku['xyz_class']}', '{sku['demand_model']}', TRUE"
        f");"
    )
    lines.append(sql)

print("\n".join(lines))
