from dataclasses import dataclass, field
from typing import List
import math, time, logging
from ortools.linear_solver import pywraplp

logger = logging.getLogger(__name__)

@dataclass
class SKUInput:
    product_id: str
    roq_raw: int
    nip: int
    daily_demand: float
    unit_cost: float
    priority_tier: int  # 1=critical, 2=strategic, 3=expendable
    abc_class: str
    xyz_class: str

@dataclass
class SKUResult:
    product_id: str
    allocated_qty: int
    projected_dos: float
    budget_consumed: float
    was_capped: bool
    priority_tier: int = 1

@dataclass
class SolverOutput:
    status: str
    min_dos_achieved: float
    total_budget_used: float
    allocations: List[SKUResult]
    solver_wall_ms: int
    objective_value: float

def run_fair_share_solver(
    skus: List[SKUInput],
    credit_available: float,
    tier1_reservation_pct: float = 0.90,
    time_limit_ms: int = 1800,
) -> SolverOutput:
    """MILP: maximize minimum DOS across all eligible SKUs subject to credit budget.
    
    Objective: max Z_min
    Constraints:
      (1) x_i - Z_min * D_i >= -NIP_i  (every SKU DOS >= Z_min)
      (2) sum(x_i * c_i) <= credit_available
      (3) x_i >= floor(0.9 * ROQ_i) for Tier1 SKUs (reservation)
    """
    start_time = time.time()
    
    # Filter eligible SKUs
    eligible_skus = [sku for sku in skus if sku.priority_tier != 3 and sku.daily_demand > 0]
    
    if not eligible_skus:
        return SolverOutput(
            status="INFEASIBLE",
            min_dos_achieved=0.0,
            total_budget_used=0.0,
            allocations=[],
            solver_wall_ms=int((time.time() - start_time) * 1000),
            objective_value=0.0
        )
    
    # Create solver
    solver = pywraplp.Solver.CreateSolver("SCIP")
    if not solver:
        raise Exception("SCIP solver unavailable")
        
    solver.set_time_limit(time_limit_ms)
    
    # Create variables
    x = {}  # allocation variables
    for sku in eligible_skus:
        x[sku.product_id] = solver.IntVar(0, sku.roq_raw, f"x_{sku.product_id}")
        
    z_min = solver.NumVar(0, solver.infinity(), "z_min")
    
    # Constraint (1): x_i - Z_min * D_i >= -NIP_i
    for sku in eligible_skus:
        solver.Add(x[sku.product_id] - z_min * sku.daily_demand >= -sku.nip)
    
    # Constraint (2): Budget constraint
    budget_expr = sum(sku.unit_cost * x[sku.product_id] for sku in eligible_skus)
    solver.Add(budget_expr <= credit_available)
    
    # Constraint (3): Tier1 reservation
    for sku in eligible_skus:
        if sku.priority_tier == 1:
            min_allocation = math.floor(tier1_reservation_pct * sku.roq_raw)
            solver.Add(x[sku.product_id] >= min_allocation)
    
    # Objective: Maximize z_min
    solver.Maximize(z_min)
    
    # Solve
    status = solver.Solve()
    
    end_time = time.time()
    wall_time_ms = int((end_time - start_time) * 1000)
    
    # Map status
    status_map = {
        pywraplp.Solver.OPTIMAL: "OPTIMAL",
        pywraplp.Solver.FEASIBLE: "FEASIBLE",
        pywraplp.Solver.INFEASIBLE: "INFEASIBLE",
    }
    result_status = status_map.get(status, "ERROR")
    
    if status not in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
        return SolverOutput(
            status=result_status,
            min_dos_achieved=0.0,
            total_budget_used=0.0,
            allocations=[],
            solver_wall_ms=wall_time_ms,
            objective_value=0.0
        )
    
    # Extract results
    min_dos = z_min.solution_value()
    total_budget_used = sum(sku.unit_cost * x[sku.product_id].solution_value() for sku in eligible_skus)
    
    allocations = []
    for sku in eligible_skus:
        allocated_qty = int(round(x[sku.product_id].solution_value()))
        projected_dos = (allocated_qty + sku.nip) / sku.daily_demand if sku.daily_demand > 0 else 0
        budget_consumed = sku.unit_cost * allocated_qty
        was_capped = allocated_qty >= sku.roq_raw
        
        allocations.append(SKUResult(
            product_id=sku.product_id,
            allocated_qty=allocated_qty,
            projected_dos=projected_dos,
            budget_consumed=budget_consumed,
            was_capped=was_capped,
            priority_tier=sku.priority_tier
        ))
    
    return SolverOutput(
        status=result_status,
        min_dos_achieved=min_dos,
        total_budget_used=total_budget_used,
        allocations=allocations,
        solver_wall_ms=wall_time_ms,
        objective_value=min_dos
    )

def demo_run():
    """Demo with 5 FMCG beverage SKUs: 2 Tier1 (Cola 2L, Energy Drink), 2 Tier2 (Juice 1L, Water 500ml), 1 Tier3 (Specialty Import)"""
    skus = [
        SKUInput("COLA_2L", 1000, 200, 50.0, 1.50, 1, "A", "X"),
        SKUInput("ENERGY_DRINK", 500, 100, 25.0, 2.00, 1, "B", "Y"),
        SKUInput("JUICE_1L", 800, 150, 40.0, 1.75, 2, "A", "Z"),
        SKUInput("WATER_500ML", 1200, 300, 60.0, 0.50, 2, "C", "X"),
        SKUInput("SPECIALTY_IMPORT", 200, 50, 5.0, 5.00, 3, "B", "Y")  # Will be filtered out
    ]
    
    credit_available = 2000.0
    
    print("Running Fair-Share MILP Allocation Solver Demo...")
    print(f"Total SKUs input: {len(skus)}")
    print(f"Credit available: ${credit_available:.2f}")
    print("-" * 50)
    
    result = run_fair_share_solver(skus, credit_available)
    
    print(f"Solver Status: {result.status}")
    print(f"Solve Time: {result.solver_wall_ms} ms")
    print(f"Minimum DOS Achieved: {result.min_dos_achieved:.2f} days")
    print(f"Total Budget Used: ${result.total_budget_used:.2f}")
    print(f"Objective Value: {result.objective_value:.2f}")
    print("-" * 50)
    print(f"{'Product ID':<20} {'Allocated':<10} {'DOS':<8} {'Budget':<10} {'Capped':<8} {'Tier':<6}")
    print("-" * 50)
    
    for alloc in result.allocations:
        print(f"{alloc.product_id:<20} {alloc.allocated_qty:<10} {alloc.projected_dos:<8.2f} "
              f"${alloc.budget_consumed:<9.2f} {str(alloc.was_capped):<8} {alloc.priority_tier:<6}")

if __name__ == "__main__":
    demo_run()