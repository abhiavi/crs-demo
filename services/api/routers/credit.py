"""Credit router — financial constraint management."""
from fastapi import APIRouter, Request
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/api/v1/credit", tags=["credit"])

# Demo credit data (mirrors dim_tenant seed)
DEMO_CREDIT = {
    "DIST-AU-SYD": {"credit_limit": 750000, "ar_factor": 0.30, "unbilled_factor": 0.10},
    "DIST-AU-MEL": {"credit_limit": 1200000, "ar_factor": 0.40, "unbilled_factor": 0.10},
    "DIST-AU-BNE": {"credit_limit": 550000, "ar_factor": 0.70, "unbilled_factor": 0.10},
    "DIST-AU-PER": {"credit_limit": 480000, "ar_factor": 0.40, "unbilled_factor": 0.10},
    "DIST-AU-ADL": {"credit_limit": 320000, "ar_factor": 0.80, "unbilled_factor": 0.10},
}


@router.get("/status/{tenant_id}")
async def credit_status(tenant_id: str):
    cfg = DEMO_CREDIT.get(tenant_id, {"credit_limit": 500000, "ar_factor": 0.3, "unbilled_factor": 0.1})
    limit = cfg["credit_limit"]
    ar = round(limit * cfg["ar_factor"], 2)
    unbilled = round(limit * cfg["unbilled_factor"], 2)
    available = round(limit - ar - unbilled, 2)
    return {
        "tenant_id": tenant_id,
        "credit_total": limit,
        "ar_outstanding": ar,
        "unbilled_pipeline": unbilled,
        "credit_available": available,
        "utilization_pct": round((ar + unbilled) / limit * 100, 1),
        "status": "CREDIT_HOLD" if (ar + unbilled) / limit > 0.75 else "ACTIVE",
    }


class ReleaseRequest(BaseModel):
    workflow_run_id: str
    notes: str = ""


@router.post("/release/{tenant_id}")
async def release_credit(tenant_id: str, body: ReleaseRequest):
    ledger_id = str(uuid.uuid4())
    return {"released": True, "ledger_id": ledger_id,
            "tenant_id": tenant_id, "workflow_run_id": body.workflow_run_id}


@router.get("/ledger/{tenant_id}")
async def credit_ledger(tenant_id: str):
    return {"tenant_id": tenant_id, "entries": []}
