from fastapi import APIRouter
from app.services.audit import obtener_historial, Ejecucion

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/historial", response_model=list[Ejecucion])
def historial():
    return obtener_historial()
