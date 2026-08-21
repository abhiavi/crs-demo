"""Forecast router — classify demand and compute ROQ."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.forecasting.engine import classify_demand, sba_forecast, ets_forecast, compute_tsl, compute_roq
import numpy as np

router = APIRouter(prefix="/api/v1/forecast", tags=["forecast"])


class ClassifyRequest(BaseModel):
    tenant_id: str
    product_id: str
    sales_data: list[float]


class BatchSKU(BaseModel):
    product_id: str
    sales_data: list[float]
    avg_daily_demand: float = 0.0
    review_period: int = 7
    lead_time: int = 7
    lead_time_std: float = 1.0
    service_level: float = 0.95
    nip: int = 0
    moq: int = 1
    case_pack: int = 1
    pallet_qty: int = 120
    max_dos: int = 90
    unit_cost: float = 10.0
    abc_class: str = "B"
    xyz_class: str = "Y"


class BatchRequest(BaseModel):
    tenant_id: str
    skus: list[BatchSKU]


@router.post("/classify")
async def classify_sku(body: ClassifyRequest):
    arr = np.array(body.sales_data, dtype=float)
    profile = classify_demand(arr)
    if profile["routed_model"] == "SBA":
        fc = sba_forecast(arr)
        p50 = fc["sba_forecast"]
    else:
        fc = ets_forecast(arr)
        p50 = fc["forecast_p50"]
    return {
        "product_id": body.product_id,
        "demand_class": profile["demand_class"],
        "model_used": profile["routed_model"],
        "adi": round(profile["adi"], 4),
        "cv2": round(profile["cv2"], 4),
        "forecast_p50": round(p50, 2),
        "forecast_p10": round(p50 * 0.75, 2),
        "forecast_p90": round(p50 * 1.35, 2),
    }


@router.post("/batch")
async def batch_roq(body: BatchRequest):
    results = []
    for sku in body.skus:
        arr = np.array(sku.sales_data, dtype=float)
        profile = classify_demand(arr)
        demand = sku.avg_daily_demand or (float(np.mean(arr[arr > 0])) / 7 if np.any(arr > 0) else 1.0)
        demand_std = float(np.std(arr)) / 7 if len(arr) > 1 else demand * 0.3

        if profile["routed_model"] == "SBA":
            fc = sba_forecast(arr)
            p50 = fc["sba_forecast"]
        else:
            fc = ets_forecast(arr)
            p50 = fc["forecast_p50"]

        tsl_result = compute_tsl(demand, sku.review_period, sku.lead_time,
                                 sku.lead_time_std, demand_std, sku.service_level)
        roq_result = compute_roq(tsl_result["tsl"], sku.nip, sku.moq, sku.case_pack,
                                 sku.pallet_qty, sku.max_dos, demand)
        results.append({
            "product_id": sku.product_id,
            "demand_class": profile["demand_class"],
            "model_used": profile["routed_model"],
            "forecast_p50": round(p50, 2),
            "tsl": round(tsl_result["tsl"], 2),
            "safety_stock": round(tsl_result["safety_stock"], 2),
            "nip": sku.nip,
            "roq_raw": roq_result["roq_raw"],
            "roq_final": roq_result["roq_final"],
            "projected_dos": roq_result["projected_dos"],
            "unit_cost": sku.unit_cost,
            "abc_class": sku.abc_class,
            "xyz_class": sku.xyz_class,
            "priority_tier": 1 if sku.abc_class in ("A","B") and sku.xyz_class in ("X","Y") else
                             (2 if sku.xyz_class != "Z" else 3),
            "anomaly_flag": roq_result["projected_dos"] > sku.max_dos * 0.9,
        })
    return results


@router.get("/history/{tenant_id}/{product_id}")
async def forecast_history(tenant_id: str, product_id: str):
    # Returns mock forecast history — in production queries fact_forecast
    from datetime import date, timedelta
    import random
    base = 450.0
    return [
        {"target_date": str(date.today() - timedelta(days=i)),
         "p10": base * 0.75, "p50": base, "p90": base * 1.35,
         "model_used": "ETS"}
        for i in range(30)
    ]
