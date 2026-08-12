from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.core.config import settings
from app.core.database import SessionLocal, create_database
from app.services.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    await create_database()
    async with SessionLocal() as session:
        await seed_database(session)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="YYGlobal P0 留学申请 Agent API",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    return {"name": "YYGlobal", "docs": "/docs", "health": "/api/health"}
