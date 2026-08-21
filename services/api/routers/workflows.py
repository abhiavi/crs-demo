"""Workflow trigger and status endpoints."""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from temporalio.client import Client
import uuid, os

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])


class TriggerRequest(BaseModel):
    tenant_id: str
    run_date: str | None = None
    dry_run: bool = True


@router.post("/trigger")
async def trigger_workflow(body: TriggerRequest, request: Request):
    from datetime import date
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    run_date = body.run_date or str(date.today())
    try:
        client = await Client.connect(temporal_address)
        handle = await client.start_workflow(
            "CRSReplenishmentWorkflow",
            args=[{"tenant_id": body.tenant_id, "run_date": run_date, "dry_run": body.dry_run}],
            id=f"crs-{body.tenant_id}-{run_date}-{uuid.uuid4().hex[:8]}",
            task_queue="crs-replenishment",
        )
        return {"workflow_id": handle.id, "run_id": handle.result_run_id,
                "tenant_id": body.tenant_id, "run_date": run_date,
                "temporal_ui_url": f"http://localhost:8080/namespaces/default/workflows/{handle.id}"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Temporal unavailable: {str(e)}")


@router.get("/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    try:
        client = await Client.connect(temporal_address)
        handle = client.get_workflow_handle(workflow_id)
        desc = await handle.describe()
        return {"workflow_id": workflow_id, "status": str(desc.status),
                "start_time": str(desc.start_time), "close_time": str(desc.close_time)}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
