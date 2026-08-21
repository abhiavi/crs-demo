import asyncio
import logging
from temporalio.client import Client
from temporalio.worker import Worker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    import os
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    # Retry connecting until Temporal is fully initialized (auto-setup takes ~30s)
    for attempt in range(30):
        try:
            client = await Client.connect(temporal_address)
            break
        except Exception as e:
            logger.info(f"Waiting for Temporal ({attempt+1}/30): {e}")
            await asyncio.sleep(5)
    else:
        raise RuntimeError(f"Temporal at {temporal_address} never became ready")
    logger.info(f"Connected to Temporal at {temporal_address}")

    from workflows import CRSReplenishmentWorkflow
    from activities import (
        ingest_pos_data, run_stockout_imputation,
        classify_and_forecast, compute_roq_batch,
        query_erp_credit, run_fair_share_solver_activity,
        release_orders_to_erp, reverse_erp_credit_hold
    )

    worker = Worker(
        client,
        task_queue="crs-replenishment",
        workflows=[CRSReplenishmentWorkflow],
        activities=[
            ingest_pos_data, run_stockout_imputation,
            classify_and_forecast, compute_roq_batch,
            query_erp_credit, run_fair_share_solver_activity,
            release_orders_to_erp, reverse_erp_credit_hold
        ]
    )
    logger.info("CRS Worker started — listening on task queue: crs-replenishment")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
