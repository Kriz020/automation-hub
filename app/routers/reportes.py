from pathlib import Path

import pandas as pd
from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.config import settings
from app.schemas.reportes import ReporteRequest
from app.services.audit import auditar
from app.services.excel_writer import generar_reporte_ventas

router = APIRouter(prefix="/reportes", tags=["reportes"])


@router.get("/")
def listar_reportes():
    return {"disponibles": ["ventas-por-ciudad"]}


@router.post("/ventas")
@auditar("POST /reportes/ventas")
def reporte_ventas(req: ReporteRequest):
    df = pd.read_csv(f"{settings.data_dir}/ventas_tienda.csv")
    df["fecha"] = pd.to_datetime(df["fecha"])

    if req.fecha_inicio:
        df = df[df["fecha"] >= pd.Timestamp(req.fecha_inicio)]
    if req.fecha_fin:
        df = df[df["fecha"] <= pd.Timestamp(req.fecha_fin)]
    if req.ciudad:
        df = df[df["ciudad"].str.lower() == req.ciudad.lower()]

    if df.empty:
        return {"error": "Sin datos para los filtros aplicados"}

    output = Path(settings.output_dir) / "reporte_ventas.xlsx"
    generar_reporte_ventas(df, output)
    return FileResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="reporte_ventas.xlsx",
    )
