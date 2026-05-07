from pydantic import BaseModel
from datetime import date

class ReporteRequest(BaseModel):
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    ciudad: str | None = None
