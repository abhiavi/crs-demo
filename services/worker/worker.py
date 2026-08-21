import asyncio, logging, os
from temporalio.client import Client
from temporalio.worker import Worker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

async def main():
    address = os.getenv("TEMPORAL_ADDRESS", "temporal:7233")
    client = await Client.connect(address)
    from workflows import CRSReplenishmentWorkflow
    from activities import (
        ingest_pos_data, run_stockout_imputation, classify_and_forecast,
        compute_roq_batch, query_erp_credit, run_fair_share_solver_activity,
        release_orders_to_erp, reverse_erp_credit_hold,
    )
    worker = Worker(
        client, task_queue="crs-replenishment",
        workflows=[CRSReplenishmentWorkflow],
        activities=[ingest_pos_data, run_stockout_imputation, classify_and_forecast,
                    compute_roq_batch, query_erp_credit, run_fair_share_solver_activity,
                    release_orders_to_erp, reverse_erp_credit_hold],
    )
    logging.info("CRS Worker started — task queue: crs-replenishment")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
