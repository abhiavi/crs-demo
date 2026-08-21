import numpy as np
from scipy import stats
import math

__all__ = ["classify_demand", "sba_forecast", "ets_forecast", "compute_tsl", "compute_roq"]


def classify_demand(sales_array: np.ndarray, covariate_r2: float = 0.0, revenue_tier: str = "C") -> dict:
    """Classify demand pattern using Syntetos-Boylan ADI/CV2 matrix."""
    # Override to TFT for high-value or covariate-rich SKUs
    if covariate_r2 > 0.35 or revenue_tier == "A":
        return {"adi": 0.0, "cv2": 0.0, "demand_class": "COMPLEX", "routed_model": "TFT"}

    nonzero_idx = np.where(sales_array > 0)[0]
    if len(nonzero_idx) < 2:
        return {"adi": 999.0, "cv2": 999.0, "demand_class": "LUMPY", "routed_model": "SBA"}

    intervals = np.diff(nonzero_idx)
    adi = float(np.mean(intervals))

    nonzero_vals = sales_array[nonzero_idx]
    cv2 = float((np.std(nonzero_vals) / np.mean(nonzero_vals)) ** 2) if np.mean(nonzero_vals) > 0 else 0.0

    if adi < 1.32 and cv2 < 0.49:
        cls, model = "SMOOTH", "ETS"
    elif adi >= 1.32 and cv2 < 0.49:
        cls, model = "INTERMITTENT", "SBA"
    elif adi < 1.32 and cv2 >= 0.49:
        cls, model = "ERRATIC", "ARIMA"
    else:
        cls, model = "LUMPY", "SBA"

    return {"adi": round(adi, 4), "cv2": round(cv2, 4), "demand_class": cls, "routed_model": model}


def sba_forecast(sales_array: np.ndarray, alpha: float = 0.15) -> dict:
    """Syntetos-Boylan Approximation correcting Croston positive bias by (1 - alpha/2)."""
    z, p = 0.0, 1.0
    last_t = -1
    periods_evaluated = 0

    for t, d in enumerate(sales_array):
        if d > 0:
            # Inter-demand interval since last positive observation
            q = t - last_t if last_t >= 0 else 1
            # Update positive demand size estimate
            z = alpha * d + (1 - alpha) * z if z > 0 else float(d)
            # Update inter-demand interval estimate
            p = alpha * q + (1 - alpha) * p
            last_t = t
            periods_evaluated += 1

    if p == 0 or z == 0:
        return {"z": 0.0, "p": 1.0, "croston_forecast": 0.0, "sba_forecast": 0.0, "alpha": alpha, "periods_evaluated": 0}

    croston = z / p
    sba = (1 - alpha / 2) * croston

    return {"z": round(z, 4), "p": round(p, 4), "croston_forecast": round(croston, 4),
            "sba_forecast": round(sba, 4), "alpha": alpha, "periods_evaluated": periods_evaluated}


def ets_forecast(sales_array: np.ndarray, alpha: float = 0.2, horizon: int = 14) -> dict:
    """Simple exponential smoothing with symmetric quantile bands."""
    if len(sales_array) == 0:
        return {"forecast_p50": 0.0, "forecast_p10": 0.0, "forecast_p90": 0.0, "alpha": alpha}

    s = float(sales_array[0])
    for y in sales_array[1:]:
        s = alpha * y + (1 - alpha) * s

    p50 = round(s, 4)
    return {"forecast_p50": p50, "forecast_p10": round(p50 * 0.75, 4),
            "forecast_p90": round(p50 * 1.35, 4), "alpha": alpha}


def compute_tsl(avg_daily_demand: float, review_period: int, lead_time: int,
                lead_time_std: float, demand_std: float, service_level: float = 0.95) -> dict:
    """Target Stock Level with lead-time variance decomposition (full formula from BRD)."""
    z = float(stats.norm.ppf(service_level))

    cycle_stock = avg_daily_demand * (review_period + lead_time)
    safety_stock = z * math.sqrt(lead_time * demand_std**2 + avg_daily_demand**2 * lead_time_std**2)
    tsl = cycle_stock + safety_stock

    return {"tsl": round(tsl, 2), "safety_stock": round(safety_stock, 2),
            "z_score": round(z, 4), "cycle_stock": round(cycle_stock, 2)}


def compute_roq(tsl: float, net_inventory_pos: int, moq: int = 1, case_pack: int = 1,
                pallet_qty: int = 120, max_dos: int = 90, avg_daily_demand: float = 1.0) -> dict:
    """Apply logistics constraints to raw ROQ: MOQ floor, case rounding, pallet heuristic, DOS ceiling."""
    roq_raw = max(0.0, tsl - net_inventory_pos)

    was_moq = False
    roq = roq_raw

    # Minimum order quantity floor
    if 0 < roq < moq:
        roq = float(moq)
        was_moq = True

    # Round to case pack
    if case_pack > 1:
        roq = math.ceil(roq / case_pack) * case_pack

    # Pallet rounding heuristic: round up if remainder > 40% of pallet, else round down
    if pallet_qty > 1 and roq > 0:
        remainder = roq % pallet_qty
        if remainder > 0:
            if remainder / pallet_qty >= 0.4:
                roq = math.ceil(roq / pallet_qty) * pallet_qty
            else:
                roq = math.floor(roq / pallet_qty) * pallet_qty
                roq = max(roq, float(moq))

    # Hard DOS ceiling — prevent hoarding effect
    dos_capped = False
    if avg_daily_demand > 0:
        projected_dos = (net_inventory_pos + roq) / avg_daily_demand
        if projected_dos > max_dos:
            roq = max(0.0, max_dos * avg_daily_demand - net_inventory_pos)
            if pallet_qty > 1:
                roq = math.floor(roq / pallet_qty) * pallet_qty
            dos_capped = True

    roq_final = max(0, int(roq))
    projected_dos_final = (net_inventory_pos + roq_final) / avg_daily_demand if avg_daily_demand > 0 else 0.0

    return {
        "roq_raw": int(roq_raw),
        "roq_final": roq_final,
        "projected_dos": round(projected_dos_final, 1),
        "was_dos_capped": dos_capped,
        "was_moq_applied": was_moq,
    }