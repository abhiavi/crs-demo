import os
import structlog
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncpg
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://crs_user:crs_secret_2024@localhost:5433/crs_demo"
    temporal_address: str = "localhost:7233"
    litellm_base_url: str = ""
    litellm_key: str = ""
    secret_key: str = "crs-demo-secret"
    version: str = "1.0.0"

    class Config:
        env_file = ".env"


settings = Settings()


def configure_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.render_to_log_kwargs,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    app.state.db = await asyncpg.create_pool(dsn=settings.database_url)
    yield
    await app.state.db.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_current_persona(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return "planner"
    
    if auth_header.startswith("Bearer demo-"):
        persona = auth_header.split("Bearer demo-")[1]
        valid_personas = {"planner", "executive", "distributor", "credit_admin"}
        if persona in valid_personas:
            return persona
    
    return "planner"


@app.get("/health")
async def health_check(request: Request):
    try:
        async with request.app.state.db.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_connected = True
    except Exception:
        db_connected = False
        
    return {
        "status": "ok",
        "db_connected": db_connected,
        "version": settings.version,
        "demo_mode": True
    }


@app.get("/")
async def root():
    return {
        "message": "CRS Demo API",
        "version": settings.version,
        "docs": "/docs"
    }

from routers import forecast, solver, overrides, credit

app.include_router(forecast.router)
app.include_router(solver.router)
app.include_router(overrides.router)
app.include_router(credit.router)