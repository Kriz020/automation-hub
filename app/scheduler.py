from pathlib import Path

import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from app.services.excel_writer import generar_reporte_ventas

scheduler = BackgroundScheduler()


def job_reporte_diario():
    logger.info("Ejecutando job_reporte_diario")
    df = pd.read_csv("data/ventas_tienda.csv")
    generar_reporte_ventas(df, Path("output/reporte_diario.xlsx"))
    logger.info("job_reporte_diario completado → output/reporte_diario.xlsx")


scheduler.add_job(
    job_reporte_diario,
    CronTrigger(hour=8, minute=0),
    id="reporte_diario",
)
