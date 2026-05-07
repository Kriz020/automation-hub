from fastapi import FastAPI
from app.config import settings
from app.routers import reportes

app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(reportes.router)

@app.get("/")
def root():
    return {"app": settings.app_name, "status": "ok"}
