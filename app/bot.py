import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from app.config import settings

API_BASE = "http://localhost:8000"


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hola! Comandos disponibles:\n"
        "/reporte — genera reporte de ventas\n"
        "/historial — últimas ejecuciones"
    )


async def reporte(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Generando reporte...")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{API_BASE}/reportes/ventas", json={})
    if r.status_code == 200:
        await update.message.reply_document(
            document=r.content, filename="reporte_ventas.xlsx"
        )
    else:
        await update.message.reply_text(f"Error al generar reporte: {r.status_code}")


async def historial(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_BASE}/admin/historial")
    if r.status_code != 200:
        await update.message.reply_text("Error obteniendo historial")
        return
    registros = r.json()[:10]
    if not registros:
        await update.message.reply_text("No hay ejecuciones registradas aún.")
        return
    lines = [f"📋 Últimas {len(registros)} ejecuciones:"]
    for e in registros:
        lines.append(f"• {e['endpoint']} — {e['resultado']} ({e['duracion_ms']}ms) — {e['fecha'][:19]}")
    await update.message.reply_text("\n".join(lines))


def run_bot():
    if not settings.telegram_token:
        raise ValueError("TELEGRAM_TOKEN no configurado en .env")
    app = Application.builder().token(settings.telegram_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reporte", reporte))
    app.add_handler(CommandHandler("historial", historial))
    app.run_polling()


if __name__ == "__main__":
    run_bot()
