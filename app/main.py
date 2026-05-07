from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.config import settings
from app.routers import admin, reportes
from app.scheduler import scheduler
from app.services.audit import init_db

logger.add("logs/app.log", rotation="10 MB", retention="30 days", level="INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.start()
    logger.info("Automation Hub iniciado")
    yield
    scheduler.shutdown()
    logger.info("Automation Hub detenido")


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.include_router(reportes.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {"app": settings.app_name, "status": "ok"}
