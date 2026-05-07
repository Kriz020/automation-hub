from fastapi import APIRouter

router = APIRouter(prefix="/reportes", tags=["reportes"])

@router.get("/")
def listar_reportes():
    return {"disponibles": ["ventas-por-ciudad"]}
