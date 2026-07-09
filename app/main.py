import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.routers import agenda, auth, content, dashboard, finance, members, repertoire, study, tasks, timelogs
from app.seed import seed_members

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        await seed_members(session)
    yield


app = FastAPI(
    title="Forró Ruby — API",
    description="API do sistema de gestão da banda Forró Ruby",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (
    auth.router,
    members.router,
    tasks.router,
    agenda.router,
    finance.router,
    timelogs.router,
    study.router,
    content.router,
    repertoire.router,
    dashboard.router,
):
    app.include_router(router)


@app.get("/api/health", tags=["health"])
async def health():
    return {"status": "ok", "app": "forro-ruby-api"}
