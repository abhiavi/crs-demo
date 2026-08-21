# Autonomous Continuous Replenishment System (CRS)
### FMCG Beverages — Vendor-Managed Inventory Demo

> A production-architecture demonstration of an autonomous supply chain replenishment engine for 5 Australian beverage distributors. Built to show how Vendor-Managed Inventory (VMI), probabilistic ML forecasting, and operations research eliminate the bullwhip effect at scale.

---

## What This Demonstrates

| Capability | Technology |
|---|---|
| Demand classification & routing | ADI / CV² → ETS / SBA / TFT selection |
| Intermittent demand forecasting | Syntetos-Boylan Approximation (SBA) |
| Probabilistic forecast bands | P10 / P50 / P90 quantile outputs |
| Safety stock optimization | TSL formula with lead-time variance decomposition |
| Credit-constrained allocation | Google OR-Tools MILP (SCIP backend) |
| Distributed saga orchestration | Temporal.io with compensating transactions |
| Multi-persona dashboards | React + Recharts (4 user roles) |

---

## Architecture

```
POS Data → Ingestion → ML Forecasting Engine → Replenishment Math
                                                       ↓
                               OR-Tools MILP Solver ← Credit Check
                                       ↓
                          Temporal.io Saga Orchestrator
                                       ↓
                              ERP Release (simulated)
                                       ↓
                         React Frontend (4 persona views)
```

---

## Quick Start

### Prerequisites
- Docker Desktop / Docker Engine with Compose v2+
- 8 GB RAM available for containers
- Ports free: 3000, 5433, 7233, 8000, 8080

### 1. Clone & Configure

```bash
git clone https://github.com/abhiavi/crs-demo.git
cd crs-demo
cp .env.example .env
```

### 2. Start the Stack

```bash
docker compose up -d
```

This starts 6 containers:
| Container | Purpose | URL |
|---|---|---|
| `postgres` | CRS data store | localhost:5433 |
| `temporal` | Workflow orchestrator | localhost:7233 |
| `temporal-ui` | Temporal web UI | http://localhost:8080 |
| `api` | FastAPI backend | http://localhost:8000 |
| `worker` | Temporal workflow worker | — |
| `frontend` | React dashboard | **http://localhost:3000** |

### 3. Seed Demo Data

```bash
docker compose exec api python -c "
import asyncio, asyncpg, os
async def seed():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    # Seed files are loaded automatically via postgres init scripts
    print('Data seeded — 5 tenants, 30 SKUs, 52 weeks history')
asyncio.run(seed())
"
```

### 4. Open the Dashboard

Navigate to **http://localhost:3000** and choose your persona:

| Persona | What You See |
|---|---|
| **Demand Planner** | Exception triage grid, TFT attention weights, forecast P10/P50/P90 bands |
| **Sales / Executive** | Revenue target simulator, network DOS health, credit utilization |
| **Distributor Portal** | In-transit shipments, projected Days of Supply depletion curves |
| **Credit Admin** | Credit utilization by distributor, OR-Tools solver output, manual release |

---

## Demo Data

**5 Australian beverage distributors:**
- Sydney Beverage Distributors Pty Ltd (credit: AUD 750K)
- Melbourne Drinks Co Pty Ltd (credit: AUD 1.2M)
- Brisbane Refreshments Group (credit: AUD 550K — in Credit Hold for demo)
- Perth Liquid Assets Pty Ltd (credit: AUD 480K)
- Adelaide Premium Beverages (credit: AUD 320K — in Credit Hold for demo)

**30 SKUs across 3 demand profiles:**
- 10 Carbonated Soft Drinks → SMOOTH demand → ETS model → ABC class A/X
- 10 Juice & Nectars → SEASONAL demand → ARIMA/HW model → ABC class B/Y
- 10 Energy & Sports drinks → INTERMITTENT demand → SBA model → ABC class C/Z

**52 weeks of realistic demand history** with:
- Seasonal peaks (Australian summer Dec–Feb)
- ~5% stockout events on A-class items, ~15% on C-class
- Promotional uplift periods (footy finals, Easter, Christmas)

---

## Key Mathematical Components

### Demand Classification
```
ADI = mean inter-demand interval
CV² = (σ_demand / μ_demand)²

ADI < 1.32, CV² < 0.49  →  SMOOTH  →  ETS
ADI ≥ 1.32, CV² < 0.49  →  INTERMITTENT  →  SBA
ADI < 1.32, CV² ≥ 0.49  →  ERRATIC  →  ARIMA
ADI ≥ 1.32, CV² ≥ 0.49  →  LUMPY  →  SBA
Covariate R² > 0.35      →  COMPLEX  →  TFT
```

### Target Stock Level
```
TSL = D × (T + L) + Z × √(L·σ_D² + D²·σ_L²)
```

### Fair-Share MILP Objective
```
maximize Z_min
subject to: (NIP_i + x_i) / D_i ≥ Z_min  ∀i
            Σ x_i · c_i ≤ Credit_available
            x_i ≤ ROQ_raw_i
            x_i ∈ ℤ≥0
```

---

## API Reference

Base URL: `http://localhost:8000`

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Stack health check |
| `/api/v1/forecast/classify` | POST | Classify SKU demand pattern |
| `/api/v1/forecast/batch` | POST | Batch ROQ calculation |
| `/api/v1/solver/fair-share` | POST | Run MILP allocation solver |
| `/api/v1/overrides` | POST | Submit human override |
| `/api/v1/credit/status/{tenant_id}` | GET | Real-time credit position |
| `/api/v1/credit/release/{tenant_id}` | POST | Inject manual credit release |
| `/docs` | GET | Interactive Swagger UI |

---

## Temporal Workflow

Open the Temporal UI at **http://localhost:8080** to watch the saga execute in real time:

```
SENSING → ROQ_CALCULATION → CONSTRAINT_CHECK
    → [if credit OK] → APPROVAL_WAIT → ERP_RELEASE
    → [if credit breach] → FAIR_SHARE_ALLOCATION → APPROVAL_WAIT → ERP_RELEASE
```

Trigger a workflow run:
```bash
curl -X POST http://localhost:8000/api/v1/workflows/trigger \
  -H "Authorization: Bearer demo-planner" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "DIST-AU-BNE", "dry_run": true}'
```

---

## Project Structure

```
crs-demo/
├── docker-compose.yml          # Full stack definition
├── services/
│   ├── api/                    # FastAPI backend
│   │   ├── main.py             # App entry point + auth
│   │   ├── routers/            # forecast, solver, overrides, credit
│   │   └── services/
│   │       ├── forecasting/    # SBA, ETS, ADI/CV² classifier
│   │       └── solver.py       # OR-Tools MILP solver
│   ├── worker/                 # Temporal workflow worker
│   │   ├── workflows.py        # CRSReplenishmentWorkflow saga
│   │   └── activities.py       # All Temporal activities
│   └── frontend/               # React + Vite + TypeScript
│       └── src/views/          # 4 persona dashboards
├── infra/
│   └── postgres/               # DDL + seed scripts
└── data/
    ├── seed/                   # SQL seed data (5 tenants, 30 SKUs)
    └── generator/              # Synthetic data generation scripts
```

---

## Deployment on Oracle Cloud (Nomad)

This stack is deployed on `adraca-oracle-03` (${OLLAMA_HOST}) via Nomad:

```bash
# From azure-01
ssh oracle-03
cd /opt/crs-demo
docker compose up -d
```

Access via Tailscale: `http://${OLLAMA_HOST}:3000`

---

*Built on the Adraca Sovereign AI Fleet — LiteLLM gateway powering all ML inference.*
*Architecture: qwen3-coder-480b (code) · deepseek-v4-pro (math) · nemotron-super-120b (frontend) · gemini-2.5-flash (data)*
