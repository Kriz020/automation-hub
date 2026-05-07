# Automation Hub

Servicio FastAPI que centraliza automatizaciones (reportes, scraping, procesamiento de documentos)
y se orquesta desde Power Automate Desktop, Telegram y schedulers internos.

🚧 En construcción. Ver `PLAN.md` para la hoja de ruta.

## Stack
Python 3.12 · FastAPI · pandas · APScheduler · python-telegram-bot · Docker

## Quick start
\`\`\`bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
\`\`\`
