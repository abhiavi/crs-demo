"""
CRS Replenishment Workflow — Temporal.io Saga Pattern
Orchestrates: SENSING → ROQ_CALCULATION → CONSTRAINT_CHECK →
              [FAIR_SHARE_ALLOCATION] → APPROVAL_WAIT → ERP_RELEASE
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError

logger = logging.getLogger(__name__)

RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=5),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=10),
    maximum_attempts=5,
)


@dataclass
class WorkflowInput:
    tenant_id: str
    run_date: str
    dry_run: bool = False


@dataclass
class ApprovalSignal:
    approved: bool
    override_qty_map: dict
    approver_user_id: str
    reason_code: str
    notes: str = ""


@dataclass
class WorkflowOutput:
    tenant_id: str
    run_date: str
    state_reached: str
    erp_order_ids: list
    total_order_value: float
    min_dos_achieved: float
    solver_status: str


@workflow.defn(name="CRSReplenishmentWorkflow")
class CRSReplenishmentWorkflow:
    def __init__(self):
        self._approval_signal: Optional[ApprovalSignal] = None
        self._current_state = "INITIALIZED"
        self._credit_hold_ref: Optional[str] = None

    @workflow.signal
    async def approval_decision(self, signal: ApprovalSignal) -> None:
        self._approval_signal = signal
        workflow.logger.info(
            f"Approval signal received: approved={signal.approved} by {signal.approver_user_id}"
        )

    @workflow.query
    def current_state(self) -> str:
        return self._current_state

    @workflow.run
    async def run(self, wf_input: WorkflowInput) -> WorkflowOutput:
        opts = {
            "start_to_close_timeout": timedelta(minutes=5),
            "retry_policy": RETRY,
        }

        # ── State 0: SENSING ─────────────────────────────────────────
        self._current_state = "SENSING"
        workflow.logger.info(f"[{wf_input.tenant_id}] SENSING started for {wf_input.run_date}")

        from activities import ingest_pos_data, run_stockout_imputation
        await workflow.execute_activity(ingest_pos_data, wf_input.tenant_id, wf_input.run_date, **opts)
        await workflow.execute_activity(run_stockout_imputation, wf_input.tenant_id, wf_input.run_date, **opts)

        # ── State 1: ROQ_CALCULATION ──────────────────────────────────
        self._current_state = "ROQ_CALCULATION"
        from activities import classify_and_forecast, compute_roq_batch
        forecasts = await workflow.execute_activity(classify_and_forecast, wf_input.tenant_id, wf_input.run_date, **opts)
        roqs = await workflow.execute_activity(compute_roq_batch, wf_input.tenant_id, forecasts, **opts)

        # ── State 2: CONSTRAINT_CHECK ─────────────────────────────────
        self._current_state = "CONSTRAINT_CHECK"
        from activities import query_erp_credit
        credit = await workflow.execute_activity(query_erp_credit, wf_input.tenant_id, **opts)

        proposed_value = sum(float(r.get("roq_final", 0)) * float(r.get("unit_cost", 0)) for r in roqs)
        solver_result = None

        # ── State 3: FAIR_SHARE_ALLOCATION (conditional) ──────────────
        if proposed_value > credit["credit_available"]:
            self._current_state = "FAIR_SHARE_ALLOCATION"
            workflow.logger.warning(
                f"[{wf_input.tenant_id}] Credit breach: need ${proposed_value:.2f}, "
                f"available ${credit['credit_available']:.2f}"
            )
            self._credit_hold_ref = f"HOLD-{wf_input.tenant_id}-{wf_input.run_date}"

            from activities import run_fair_share_solver_activity
            solver_result = await workflow.execute_activity(
                run_fair_share_solver_activity,
                {"skus": roqs, "credit_available": credit["credit_available"], "tenant_id": wf_input.tenant_id},
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RETRY,
            )
            final_roqs = solver_result.get("allocations", roqs)
        else:
            final_roqs = roqs

        # ── State 4: APPROVAL_WAIT ────────────────────────────────────
        self._current_state = "APPROVAL_WAIT"
        anomalies = [r for r in final_roqs if r.get("anomaly_flag")]

        if anomalies:
            workflow.logger.info(f"[{wf_input.tenant_id}] {len(anomalies)} anomalies — awaiting human approval")
            approved = await workflow.wait_condition(
                lambda: self._approval_signal is not None,
                timeout=timedelta(hours=4),
            )
            if self._approval_signal and self._approval_signal.approved:
                for item in final_roqs:
                    pid = item.get("product_id")
                    if pid and pid in self._approval_signal.override_qty_map:
                        item["roq_final"] = self._approval_signal.override_qty_map[pid]
            elif not approved:
                workflow.logger.warning(f"[{wf_input.tenant_id}] Approval timeout — auto-approving conservative quantities")

        # ── State 5: ERP_RELEASE ──────────────────────────────────────
        self._current_state = "ERP_RELEASE"
        from activities import release_orders_to_erp, reverse_erp_credit_hold

        if wf_input.dry_run:
            erp_order_ids = [f"DRY-{r.get('product_id', 'UNKNOWN')[:8]}" for r in final_roqs]
        else:
            try:
                erp_order_ids = await workflow.execute_activity(
                    release_orders_to_erp,
                    wf_input.tenant_id, final_roqs,
                    start_to_close_timeout=timedelta(minutes=2),
                    retry_policy=RETRY,
                )
            except ApplicationError as exc:
                # ── COMPENSATING TRANSACTION ──────────────────────────
                if self._credit_hold_ref:
                    workflow.logger.error(f"ERP release failed — reversing credit hold {self._credit_hold_ref}")
                    await workflow.execute_activity(
                        reverse_erp_credit_hold, wf_input.tenant_id, self._credit_hold_ref, **opts
                    )
                raise

        self._current_state = "COMPLETED"
        total_value = sum(float(r.get("roq_final", 0)) * float(r.get("unit_cost", 0)) for r in final_roqs)

        return WorkflowOutput(
            tenant_id=wf_input.tenant_id,
            run_date=wf_input.run_date,
            state_reached="ERP_RELEASE",
            erp_order_ids=erp_order_ids,
            total_order_value=round(total_value, 2),
            min_dos_achieved=solver_result.get("min_dos_achieved", 0.0) if solver_result else 0.0,
            solver_status=solver_result.get("status", "WITHIN_LIMIT") if solver_result else "WITHIN_LIMIT",
        )
