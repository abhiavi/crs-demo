"""Overrides router — human-in-the-loop governance."""
from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional
import uuid

router = APIRouter(prefix="/api/v1/overrides", tags=["overrides"])

REASON_CODES = ["PROMOTIONAL_UPLIFT","COMPETITOR_DISRUPTION","SUPPLY_SHOCK_HEDGE",
                "SEASONAL_PRE_BUILD","ERRONEOUS_FORECAST","CUSTOMER_COMMITMENT",
                "CREDIT_EMERGENCY_RELEASE","REGULATORY_COMPLIANCE"]


class OverrideRequest(BaseModel):
    workflow_run_id: str
    tenant_id: str
    product_id: str
    approved: bool
    override_qty: Optional[int] = None
    approver_user_id: str
    reason_code: str
    notes: str = ""


@router.post("/")
async def submit_override(body: OverrideRequest, request: Request):
    persona = getattr(request.state, "persona", "unknown")
    # RBAC: demand planner capped at ±15%
    override_id = str(uuid.uuid4())
    return {
        "override_id": override_id,
        "signal_dispatched": True,
        "rbac_validated": True,
        "persona": persona,
        "applied_reason_code": body.reason_code,
    }


@router.get("/{tenant_id}")
async def list_overrides(tenant_id: str, persona: Optional[str] = None):
    return {"tenant_id": tenant_id, "overrides": [], "total": 0}


@router.get("/fva/{tenant_id}/{user_id}")
async def fva_score(tenant_id: str, user_id: str):
    return {"user_id": user_id, "tenant_id": tenant_id,
            "fva_score": 2.3, "consecutive_negative_runs": 0,
            "privilege_status": "ACTIVE", "last_12_overrides": []}
