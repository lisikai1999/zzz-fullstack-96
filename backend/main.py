"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .catalog.seed import seed_catalog
from .routers import locations, targets, ephemeris, planning, equipment


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_catalog()
    yield


app = FastAPI(
    title="Deep Sky Observation Planner",
    description="Astronomy observation planning API with ephemeris calculations",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(locations.router)
app.include_router(targets.router)
app.include_router(ephemeris.router)
app.include_router(planning.router)
app.include_router(equipment.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
