"""
Temporal Activities — CRS Replenishment Pipeline
Each activity is independently retryable with exponential backoff.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import asyncpg
import httpx
from temporalio import activity

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://crs_user:crs_secret_2024@postgres:5432/crs_demo")
API_BASE = os.getenv("API_BASE_URL", "http://api:8000")


async def _get_db() -> asyncpg.Connection:
    return await asyncpg.connect(DATABASE_URL)


# ── Activity: Ingest POS data ─────────────────────────────────────────────────
@activity.defn(name="ingest_pos_data")
async def ingest_pos_data(tenant_id: str, run_date: str) -> dict:
    activity.logger.info(f"Ingesting POS data for tenant={tenant_id} date={run_date}")
    async with httpx.AsyncClient(base_url=API_BASE, timeout=30) as client:
        resp = await client.post("/api/v1/internal/ingest/pos", json={"tenant_id": tenant_id, "run_date": run_date})
        resp.raise_for_status()
        result = resp.json()
    activity.logger.info(f"POS ingestion complete: {result.get('records_processed', 0)} records")
    return result


# ── Activity: Stockout imputation ────────────────────────────────────────────
@activity.defn(name="run_stockout_imputation")
async def run_stockout_imputation(tenant_id: str, run_date: str) -> dict:
    activity.logger.info(f"Running stockout imputation for tenant={tenant_id}")
    async with httpx.AsyncClient(base_url=API_BASE, timeout=60) as client:
        resp = await client.post("/api/v1/internal/impute", json={"tenant_id": tenant_id, "run_date": run_date})
        resp.raise_for_status()
    return {"status": "ok", "tenant_id": tenant_id}


# ── Activity: Classify demand and run forecasting ────────────────────────────
@activity.defn(name="classify_and_forecast")
async def classify_and_forecast(tenant_id: str, run_date: str) -> list[dict]:
    activity.logger.info(f"Running demand classification + forecasting for tenant={tenant_id}")
    conn = await _get_db()
    try:
        # Pull active SKUs for this tenant
        skus = await conn.fetch(
            "SELECT p.product_id, p.sku_code, p.moq, p.case_pack_qty, p.pallet_tie, "
            "p.pallet_high, p.lead_time_days, p.lead_time_std_dev, p.max_dos_ceiling, "
            "p.unit_cost, p.abc_class, p.xyz_class "
            "FROM dim_product p WHERE p.tenant_id = $1::uuid AND p.is_active = TRUE",
            tenant_id,
        )
        results = []
        for sku in skus:
            # Pull 52 weeks of sales history
            sales_rows = await conn.fetch(
                "SELECT imputed_qty FROM fact_sales "
                "WHERE tenant_id = $1::uuid AND product_id = $2::uuid "
                "ORDER BY sale_date DESC LIMIT 364",
                tenant_id, str(sku["product_id"]),
            )
            sales_data = [float(r["imputed_qty"]) for r in sales_rows]
            if not sales_data:
                sales_data = [0.0] * 52

            async with httpx.AsyncClient(base_url=API_BASE, timeout=60) as client:
                resp = await client.post("/api/v1/forecast/classify", json={
                    "tenant_id": tenant_id,
                    "product_id": str(sku["product_id"]),
                    "sales_data": sales_data,
                })
                if resp.status_code == 200:
                    forecast = resp.json()
                    forecast.update({
                        "moq": sku["moq"],
                        "case_pack_qty": sku["case_pack_qty"],
                        "pallet_qty": sku["pallet_tie"] * sku["pallet_high"] * sku["case_pack_qty"],
                        "lead_time_days": sku["lead_time_days"],
                        "lead_time_std_dev": float(sku["lead_time_std_dev"]),
                        "max_dos_ceiling": sku["max_dos_ceiling"],
                        "unit_cost": float(sku["unit_cost"]),
                        "abc_class": sku["abc_class"],
                        "xyz_class": sku["xyz_class"],
                    })
                    results.append(forecast)
        activity.logger.info(f"Forecasted {len(results)} SKUs for tenant={tenant_id}")
        return results
    finally:
        await conn.close()


# ── Activity: Compute ROQ batch ───────────────────────────────────────────────
@activity.defn(name="compute_roq_batch")
async def compute_roq_batch(tenant_id: str, forecasts: list[dict]) -> list[dict]:
    activity.logger.info(f"Computing ROQ for {len(forecasts)} SKUs, tenant={tenant_id}")
    async with httpx.AsyncClient(base_url=API_BASE, timeout=120) as client:
        resp = await client.post("/api/v1/forecast/batch", json={"tenant_id": tenant_id, "skus": forecasts})
        resp.raise_for_status()
    return resp.json()


# ── Activity: Query ERP credit ────────────────────────────────────────────────
@activity.defn(name="query_erp_credit")
async def query_erp_credit(tenant_id: str) -> dict:
    activity.logger.info(f"Querying ERP credit for tenant={tenant_id}")
    async with httpx.AsyncClient(base_url=API_BASE, timeout=10) as client:
        resp = await client.get(f"/api/v1/credit/status/{tenant_id}",
                                headers={"Authorization": "Bearer demo-credit_admin"})
        resp.raise_for_status()
    return resp.json()


# ── Activity: Run OR-Tools fair-share solver ──────────────────────────────────
@activity.defn(name="run_fair_share_solver_activity")
async def run_fair_share_solver_activity(payload: dict) -> dict:
    activity.logger.info(f"Running MILP solver: {len(payload.get('skus', []))} SKUs, "
                         f"budget=${payload.get('credit_available', 0):,.2f}")
    async with httpx.AsyncClient(base_url=API_BASE, timeout=30) as client:
        resp = await client.post("/api/v1/solver/fair-share", json=payload)
        resp.raise_for_status()
    result = resp.json()
    activity.logger.info(f"Solver: status={result.get('status')}, "
                         f"min_dos={result.get('min_dos_achieved')}, "
                         f"wall_ms={result.get('solver_wall_ms')}")
    return result


# ── Activity: Release orders to ERP ──────────────────────────────────────────
@activity.defn(name="release_orders_to_erp")
async def release_orders_to_erp(tenant_id: str, orders: list[dict]) -> list[str]:
    activity.logger.info(f"Releasing {len(orders)} orders to ERP for tenant={tenant_id}")
    order_ids = []
    conn = await _get_db()
    try:
        for i, order in enumerate(orders):
            if order.get("roq_final", 0) > 0:
                run_id = await conn.fetchval(
                    "INSERT INTO workflow_runs (tenant_id, run_date, state) "
                    "VALUES ($1::uuid, CURRENT_DATE, 'ERP_RELEASE') RETURNING run_id::text",
                    tenant_id,
                )
                order_ids.append(f"ERP-{tenant_id[:8]}-{str(run_id)[:8]}")
    finally:
        await conn.close()
    activity.logger.info(f"ERP release complete: {len(order_ids)} orders")
    return order_ids


# ── Activity: Compensating transaction — reverse credit hold ──────────────────
@activity.defn(name="reverse_erp_credit_hold")
async def reverse_erp_credit_hold(tenant_id: str, credit_hold_ref: str) -> bool:
    activity.logger.warning(f"COMPENSATING TRANSACTION: reversing credit hold {credit_hold_ref} for {tenant_id}")
    conn = await _get_db()
    try:
        await conn.execute(
            "INSERT INTO credit_allocation_ledger "
            "(tenant_id, workflow_run_id, credit_total, ar_outstanding, unbilled_pipeline, "
            "proposed_order_val, solver_status, notes) "
            "SELECT credit_limit, 0, 0, 0, 'MANUAL_RELEASE', "
            "       'Compensating transaction: ERP failure — credit hold reversed' "
            "FROM dim_tenant WHERE tenant_id = $1::uuid",
            tenant_id,
        )
    finally:
        await conn.close()
    return True
