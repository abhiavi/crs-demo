"""Solver router — OR-Tools MILP fair-share allocation."""
from fastapi import APIRouter
from pydantic import BaseModel
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.solver import run_fair_share_solver, SKUInput

router = APIRouter(prefix="/api/v1/solver", tags=["solver"])


class SolverRequest(BaseModel):
    tenant_id: str
    credit_available: float
    tier1_reservation_pct: float = 0.90
    solver_time_limit_ms: int = 1800
    skus: list[dict]


@router.post("/fair-share")
async def fair_share(body: SolverRequest):
    sku_inputs = [
        SKUInput(
            product_id=s["product_id"],
            roq_raw=int(s.get("roq_raw", 0)),
            nip=int(s.get("nip", 0)),
            daily_demand=float(s.get("daily_demand", s.get("forecast_p50", 1.0))),
            unit_cost=float(s.get("unit_cost", 10.0)),
            priority_tier=int(s.get("priority_tier", 2)),
            abc_class=s.get("abc_class", "B"),
            xyz_class=s.get("xyz_class", "Y"),
        )
        for s in body.skus
        if int(s.get("roq_raw", 0)) > 0
    ]
    result = run_fair_share_solver(
        sku_inputs, body.credit_available,
        body.tier1_reservation_pct, body.solver_time_limit_ms
    )
    return {
        "status": result.status,
        "min_dos_achieved": result.min_dos_achieved,
        "total_budget_used": result.total_budget_used,
        "solver_wall_ms": result.solver_wall_ms,
        "objective_value": result.objective_value,
        "allocations": [
            {"product_id": a.product_id, "allocated_qty": a.allocated_qty,
             "projected_dos": a.projected_dos, "budget_consumed": a.budget_consumed,
             "was_capped": a.was_capped}
            for a in result.allocations
        ],
    }


@router.get("/runs/{tenant_id}")
async def solver_runs(tenant_id: str):
    return {"tenant_id": tenant_id, "runs": []}
