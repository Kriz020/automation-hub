# Automation Hub — Plan completo paso a paso

Servicio FastAPI orquestado por Power Automate Desktop, con bot de Telegram, scheduler interno y todo dockerizado. Pensado para 4–7 hrs/semana, ~8 semanas.

---

## 0. Decisiones estratégicas (léelo primero)

### ¿Necesitas un VPS?

**No al principio. Probablemente no nunca durante la fase de aprendizaje.** Te explico por qué y cuándo sí.

**Cómo van a hablarse las piezas:**

```
Tu PC Windows
├── PAD (Windows nativo)        ──► HTTP ──► WSL: http://localhost:8000
├── WSL (Ubuntu)
│   └── FastAPI corriendo
└── Telegram Bot (corre dentro de WSL, polling a Telegram)
```

PAD y FastAPI viven en la misma máquina. PAD le pega a `http://localhost:8000` (o `http://172.x.x.x` que es la IP de WSL — te la encuentro al llegar ahí). **Cero VPS, cero ngrok, cero deploy.**

**¿Cuándo entra un VPS?**
1. Cuando quieras que el bot de Telegram siga respondiendo aunque apagues tu PC.
2. Cuando quieras que tu API sea consumible desde fuera (ej. un PAD corriendo en otra computadora del trabajo).
3. Cuando quieras mostrar en entrevista una URL viva (`https://automation-hub.tudominio.com`).

**Si llega ese momento, recomendación honesta:**

| Opción | Costo | Cuándo |
|---|---|---|
| **Cloudflare Tunnel** (gratis) | $0 | Para demos puntuales. URL pública sin abrir puertos. |
| **Railway** / **Fly.io** (free tier) | $0–5/mes | Para tener la API viva 24/7 sin server. Despliega Docker directo desde GitHub. |
| **Hetzner CX22** | ~€4/mes | Si quieres un VPS real para aprender Linux server, nginx, systemd. La mejor relación calidad/precio. |
| **DigitalOcean droplet** | $6/mes | Más popular para portafolio, documentación amplia. |
| **AWS Lightsail** | $3.50/mes | Si quieres aprender ecosistema AWS. |

**Mi recomendación específica para ti:** Cloudflare Tunnel cuando llegues a la fase 7. Es gratis, te da HTTPS público sin tocar firewall, y es lo más cercano a "deploy real" sin pagar.

### Stack final del proyecto

```
Lenguaje:      Python 3.12
Framework:     FastAPI + Pydantic
Datos:         pandas + openpyxl
Scheduling:    APScheduler
Bot:           python-telegram-bot
HTTP client:   httpx
Tests:         pytest + httpx (TestClient)
Logging:       loguru (más amigable que stdlib)
Config:        pydantic-settings (.env)
DB local:      SQLite (logs de ejecuciones)
Container:     Docker + docker-compose
Orquestador:   Power Automate Desktop (cliente)
Dev env:       WSL2 Ubuntu en Windows
```

---

## 1. Estructura final del repo (a dónde vamos)

Antes de empezar a construir, mírala. Cada fase agrega algo a esta estructura:

```
automation-hub/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Punto de entrada FastAPI
│   ├── config.py                  # Settings (lee .env)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── reportes.py            # Endpoints /reportes/*
│   │   ├── facturas.py            # Endpoints /facturas/*
│   │   └── scraper.py             # Endpoints /scraper/*
│   ├── services/
│   │   ├── __init__.py
│   │   ├── excel_writer.py        # Lógica de generar xlsx
│   │   ├── pdf_extractor.py       # Lógica de leer PDFs
│   │   └── notifier.py            # Telegram + email
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── reportes.py            # Modelos Pydantic
│   ├── scheduler.py               # APScheduler config
│   └── bot.py                     # Telegram bot
├── pad_flows/
│   ├── README.md                  # Cómo importar los flujos
│   └── reporte_diario.txt         # Export de PAD (.txt)
├── data/
│   └── ventas_tienda.csv
├── output/                        # Excels generados (gitignored)
├── tests/
│   ├── __init__.py
│   ├── test_reportes.py
│   └── conftest.py
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml                 # o requirements.txt + requirements-dev.txt
├── README.md
└── PLAN.md                        # este archivo
```

---

## 2. Plan por fases (8 fases, una por semana)

Cada fase tiene: **objetivo**, **tareas concretas**, **entregable**, **commit message** y **qué testear**.

### Fase 1 — Estructura profesional + config (Semana 1)

**Estado actual:** tienes un `main.py` con tres endpoints sueltos. Vamos a profesionalizar.

**Objetivo:** mover todo a estructura modular. Aprender cómo FastAPI escala.

**Tareas:**

1. Crear la estructura de carpetas de arriba (solo `app/` y subcarpetas, vacías por ahora).
2. Mover el contenido de `main.py` a `app/main.py`.
3. Crear `app/routers/reportes.py` y mover los endpoints ahí usando `APIRouter`:
   ```python
   from fastapi import APIRouter
   router = APIRouter(prefix="/reportes", tags=["reportes"])

   @router.get("/")
   def listar_reportes():
       return {"disponibles": ["ventas-por-ciudad"]}
   ```
4. En `app/main.py`:
   ```python
   from fastapi import FastAPI
   from app.routers import reportes

   app = FastAPI(title="Automation Hub", version="0.1.0")
   app.include_router(reportes.router)
   ```
5. Crear `app/config.py` con pydantic-settings:
   ```python
   from pydantic_settings import BaseSettings

   class Settings(BaseSettings):
       app_name: str = "Automation Hub"
       debug: bool = True
       data_dir: str = "data"
       output_dir: str = "output"

       class Config:
           env_file = ".env"

   settings = Settings()
   ```
6. Crear `.env` (gitignored) y `.env.example` (versionado).
7. Correr: `uvicorn app.main:app --reload` (nota el cambio: `app.main` no `main`).

**Entregable:** servidor corre con la nueva estructura, `/docs` muestra los endpoints organizados por tag.

**Commit:** `refactor: estructura modular con routers y config centralizada`

**Cómo testear manualmente:**
- `http://localhost:8000/docs` debe mostrar el tag "reportes".
- Cambiar `app_name` en `.env` y verificar que se reflejó (vas a usar `settings.app_name` en `FastAPI(title=...)`).

---

### Fase 2 — Endpoint real con pandas + Excel (Semana 2)

**Objetivo:** primer endpoint útil. Recibe parámetros, procesa CSV con pandas, devuelve Excel.

**Tareas:**

1. Mover `ventas_tienda.csv` a `data/`.
2. Crear `app/services/excel_writer.py` con una función pura:
   ```python
   from pathlib import Path
   import pandas as pd

   def generar_reporte_ventas(df: pd.DataFrame, output_path: Path) -> Path:
       resumen = (
           df.groupby("ciudad")
             .agg(total=("total", "sum"), num=("id", "count"))
             .sort_values("total", ascending=False)
             .reset_index()
       )
       output_path.parent.mkdir(parents=True, exist_ok=True)
       resumen.to_excel(output_path, index=False)
       return output_path
   ```
3. Crear `app/schemas/reportes.py`:
   ```python
   from pydantic import BaseModel
   from datetime import date

   class ReporteRequest(BaseModel):
       fecha_inicio: date | None = None
       fecha_fin: date | None = None
       ciudad: str | None = None
   ```
4. En `app/routers/reportes.py` agregar:
   ```python
   from fastapi.responses import FileResponse
   from pathlib import Path
   import pandas as pd
   from app.config import settings
   from app.services.excel_writer import generar_reporte_ventas
   from app.schemas.reportes import ReporteRequest

   @router.post("/ventas")
   def reporte_ventas(req: ReporteRequest):
       df = pd.read_csv(f"{settings.data_dir}/ventas_tienda.csv")
       # filtros opcionales aquí
       output = Path(settings.output_dir) / "reporte_ventas.xlsx"
       generar_reporte_ventas(df, output)
       return FileResponse(output, filename="reporte_ventas.xlsx")
   ```

**Entregable:** POST a `/reportes/ventas` con body JSON descarga un Excel real.

**Commit:** `feat: endpoint /reportes/ventas con filtros opcionales y export a Excel`

**Cómo testear manualmente:**
- Desde `/docs` mandar body vacío `{}` → debe devolver Excel con todas las ventas agrupadas.
- Mandar `{"ciudad": "Guatemala"}` → debe filtrar.

---

### Fase 3 — Logging + SQLite para historial (Semana 3)

**Objetivo:** que cada ejecución quede registrada. Esto es lo que distingue un "script" de un "servicio".

**Tareas:**

1. Instalar: `pip install loguru sqlmodel`
2. Crear `app/services/audit.py` que escribe en SQLite cada vez que se ejecuta un endpoint:
   ```python
   from sqlmodel import SQLModel, Field, create_engine, Session
   from datetime import datetime

   class Ejecucion(SQLModel, table=True):
       id: int | None = Field(default=None, primary_key=True)
       endpoint: str
       fecha: datetime = Field(default_factory=datetime.now)
       parametros: str  # JSON string
       resultado: str   # 'ok' | 'error'
       duracion_ms: int

   engine = create_engine("sqlite:///audit.db")
   SQLModel.metadata.create_all(engine)
   ```
3. Crear un decorator o middleware que mida tiempo y guarde la ejecución.
4. Loguear todo con `loguru`:
   ```python
   from loguru import logger
   logger.add("logs/app.log", rotation="10 MB", retention="30 days")
   ```
5. Agregar endpoint `GET /admin/historial` que devuelve las últimas 50 ejecuciones.

**Entregable:** cada llamada queda en `audit.db` y en `logs/app.log`. Endpoint para verlas.

**Commit:** `feat: auditoría de ejecuciones en SQLite + logging estructurado con loguru`

**Cómo testear:**
- Llamar `/reportes/ventas` 3 veces.
- `GET /admin/historial` debe devolver 3 registros con timestamps y duración.
- Abrir `audit.db` con DBeaver o `sqlite3 audit.db` en terminal.

---

### Fase 4 — APScheduler (Semana 4)

**Objetivo:** que el endpoint de reporte se ejecute solo todos los días a las 8am.

**Tareas:**

1. `pip install apscheduler`
2. Crear `app/scheduler.py`:
   ```python
   from apscheduler.schedulers.background import BackgroundScheduler
   from apscheduler.triggers.cron import CronTrigger
   from app.services.excel_writer import generar_reporte_ventas
   import pandas as pd
   from pathlib import Path

   scheduler = BackgroundScheduler()

   def job_reporte_diario():
       df = pd.read_csv("data/ventas_tienda.csv")
       generar_reporte_ventas(df, Path("output/reporte_diario.xlsx"))

   scheduler.add_job(
       job_reporte_diario,
       CronTrigger(hour=8, minute=0),
       id="reporte_diario",
   )
   ```
3. En `app/main.py`, arrancar el scheduler con el lifespan de FastAPI:
   ```python
   from contextlib import asynccontextmanager
   from app.scheduler import scheduler

   @asynccontextmanager
   async def lifespan(app: FastAPI):
       scheduler.start()
       yield
       scheduler.shutdown()

   app = FastAPI(lifespan=lifespan, ...)
   ```
4. Para testear sin esperar 24h: agregar un job que corre cada 1 minuto temporalmente.

**Entregable:** servidor arranca y agenda jobs solo. Verás en logs cuando se ejecuten.

**Commit:** `feat: scheduler con APScheduler para reporte diario`

**Cómo testear:**
- Configurar un job de prueba a `IntervalTrigger(seconds=30)`.
- Arrancar servidor, esperar y revisar `output/` y `logs/app.log`.

---

### Fase 5 — Power Automate Desktop como cliente (Semana 5)

**Esta es la fase que te diferencia en entrevista.** PAD no es el centro — es un cliente de tu API.

**Objetivo:** un flujo PAD que dispara el endpoint y mueve el Excel resultante a una carpeta específica.

**Tareas:**

1. **Instalar PAD** desde Microsoft Store (Windows 10/11, gratis).
2. Encontrar la IP de WSL para que PAD le pegue:
   ```bash
   # Dentro de WSL
   ip addr show eth0 | grep inet
   ```
   Te da algo como `172.27.x.x`. PAD usará `http://172.27.x.x:8000/reportes/ventas`.
   
   **Truco:** alternativamente, en WSL2 reciente puedes usar `localhost` directo desde Windows si tienes la opción `localhostForwarding=true` en `.wslconfig`.

3. Levantar FastAPI con bind a todas las interfaces (no solo localhost):
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
   Sin `--host 0.0.0.0` no llega desde Windows.

4. **Construir el flujo PAD:**
   - Acción: `Invoke web service`
   - URL: `http://localhost:8000/reportes/ventas`
   - Method: POST
   - Headers: `Content-Type: application/json`
   - Body: `{"ciudad": "Guatemala"}`
   - Save response to file: `C:\reportes\reporte_diario.xlsx`
   - Acción siguiente: `Move file` a una carpeta organizada por fecha.
   - Acción siguiente: `Send Outlook email` (opcional) con el Excel adjunto.

5. **Exportar el flujo PAD** (ícono "···" → Export). Guardarlo en `pad_flows/reporte_diario.txt` y commitear.

6. **Schedule el flujo PAD** desde el Console:
   - Trigger: cada día 8:30am (después de tu APScheduler para tener Excel fresco).

**Entregable:** flujo PAD funcionando + archivo `.txt` exportado en el repo.

**Commit:** `feat: flujo PAD que consume /reportes/ventas y archiva el Excel`

**Cómo testear:**
- Correr el flujo manualmente desde PAD ("Run").
- Verificar que llegó al endpoint (verás el log en FastAPI).
- Verificar que el archivo aparece en `C:\reportes\`.
- Verificar que `audit.db` tiene una nueva fila.

**Frase para entrevista:** *"Diseñé PAD como cliente de un servicio Python centralizado. Esto resuelve el problema clásico de RPA: bots dispersos sin observabilidad ni reuso. Cualquier nuevo bot que necesite generar reportes solo llama un endpoint."*

---

### Fase 6 — Bot de Telegram (Semana 6)

**Objetivo:** interfaz humana. Le escribes y dispara endpoints.

**Tareas:**

1. Crear bot con [@BotFather](https://t.me/botfather) en Telegram. Te da un `TOKEN`.
2. Agregar a `.env`: `TELEGRAM_TOKEN=123456:abc...`
3. `pip install python-telegram-bot httpx`
4. Crear `app/bot.py`:
   ```python
   from telegram.ext import Application, CommandHandler, ContextTypes
   from telegram import Update
   import httpx
   from app.config import settings

   API_BASE = "http://localhost:8000"

   async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
       await update.message.reply_text(
           "Hola! Comandos:\n/reporte - genera reporte\n/historial - últimas ejecuciones"
       )

   async def reporte(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
       async with httpx.AsyncClient() as client:
           r = await client.post(f"{API_BASE}/reportes/ventas", json={})
       # Telegram puede mandar archivos directamente
       await update.message.reply_document(r.content, filename="reporte.xlsx")

   def run_bot():
       app = Application.builder().token(settings.telegram_token).build()
       app.add_handler(CommandHandler("start", start))
       app.add_handler(CommandHandler("reporte", reporte))
       app.run_polling()

   if __name__ == "__main__":
       run_bot()
   ```
5. Arrancar el bot en una terminal aparte: `python -m app.bot`

**Entregable:** bot responde a `/start` y `/reporte` mandando el Excel.

**Commit:** `feat: bot de Telegram que dispara endpoints y entrega resultados`

**Cómo testear:**
- Abrir tu bot en Telegram, mandar `/start` → debe responder.
- Mandar `/reporte` → debe mandar el Excel.

---

### Fase 7 — Tests con pytest (Semana 7)

**Objetivo:** demostrar que sabes testear. Es lo que separa juniors de mid-level.

**Tareas:**

1. `pip install pytest pytest-asyncio httpx`
2. Crear `tests/conftest.py`:
   ```python
   import pytest
   from fastapi.testclient import TestClient
   from app.main import app

   @pytest.fixture
   def client():
       return TestClient(app)
   ```
3. Crear `tests/test_reportes.py`:
   ```python
   def test_listar_reportes(client):
       r = client.get("/reportes/")
       assert r.status_code == 200
       assert "disponibles" in r.json()

   def test_generar_reporte_ventas(client):
       r = client.post("/reportes/ventas", json={})
       assert r.status_code == 200
       assert r.headers["content-type"].startswith(
           "application/vnd.openxmlformats"
       )
   ```
4. Test unitario de `excel_writer.py`:
   ```python
   import pandas as pd
   from pathlib import Path
   from app.services.excel_writer import generar_reporte_ventas

   def test_generar_excel(tmp_path):
       df = pd.DataFrame({
           "ciudad": ["A", "A", "B"],
           "total": [100, 200, 50],
           "id": [1, 2, 3],
       })
       output = tmp_path / "test.xlsx"
       generar_reporte_ventas(df, output)
       assert output.exists()
       assert output.stat().st_size > 0
   ```
5. Correr: `pytest -v`
6. Agregar badge al README.

**Entregable:** suite de tests verde. Mínimo 5 tests cubriendo los 3 endpoints + helpers.

**Commit:** `test: suite inicial con pytest y TestClient`

**Cómo testear:**
- `pytest -v` debe mostrar todos en verde.
- Romper algo a propósito y ver el test fallar.

---

### Fase 8 — Docker + README + Deploy (Semana 8)

**Objetivo:** todo dockerizado, README impecable, opcionalmente deployed.

**Tareas:**

1. Crear `Dockerfile`:
   ```dockerfile
   FROM python:3.12-slim

   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY . .
   EXPOSE 8000
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```
2. Crear `docker-compose.yml`:
   ```yaml
   services:
     api:
       build: .
       ports:
         - "8000:8000"
       env_file:
         - .env
       volumes:
         - ./data:/app/data
         - ./output:/app/output
         - ./logs:/app/logs
     bot:
       build: .
       command: python -m app.bot
       env_file:
         - .env
       depends_on:
         - api
   ```
3. Probar: `docker-compose up --build`
4. README pro:
   - Diagrama de arquitectura (usa [excalidraw.com](https://excalidraw.com), exporta como PNG, súbelo a `docs/`).
   - Sección "Cómo correr" con docker-compose.
   - Sección "Endpoints" con curl examples.
   - Sección "Flujos PAD" con screenshots.
   - GIF/video de 30 seg del bot funcionando ([Loom](https://loom.com) gratis).
5. **Deploy opcional con Cloudflare Tunnel:**
   ```bash
   # En tu WSL
   curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
   chmod +x cloudflared
   ./cloudflared tunnel --url http://localhost:8000
   ```
   Te da una URL `https://random-words.trycloudflare.com` pública. **Solo úsala para demos** — la gratis es efímera. Para una URL fija, Cloudflare Tunnel + dominio propio (también gratis si tienes dominio).

**Entregable:** repo público listo para mostrar en entrevista.

**Commit:** `chore: dockerización completa + README con diagrama y demo`

---

## 3. Workflow de Git (cómo manejar el repo)

**Branching mínimo:**

```
main          ← código estable, lo que se "demuestra"
├── feat/*    ← cada fase nueva
├── fix/*     ← correcciones
└── docs/*    ← cambios solo de docs
```

**Por cada fase:**
```bash
git checkout -b feat/fase-2-pandas
# ...trabajas...
git add .
git commit -m "feat: endpoint /reportes/ventas con filtros"
git push -u origin feat/fase-2-pandas
# Abrir PR en GitHub, hacer self-review, merge a main
```

Te da history limpio y se ve profesional para reclutadores que abren tu repo.

**Conventional commits** (úsalo siempre):
- `feat:` nueva funcionalidad
- `fix:` corrige bug
- `refactor:` reorganiza sin cambiar comportamiento
- `test:` agrega/modifica tests
- `docs:` solo documentación
- `chore:` config, deps, infra

---

## 4. Estrategia de testing por nivel

| Nivel | Qué testeas | Herramienta | Cuándo |
|---|---|---|---|
| **Manual** | Que el endpoint responda | Swagger UI / curl | Mientras desarrollas |
| **Unit** | Funciones puras (excel_writer, parsers) | pytest | Cada PR |
| **Integration** | Endpoints completos | TestClient (httpx) | Cada PR |
| **End-to-end** | Flujo PAD → API → Excel → email | Manual + checklist | Antes de demo |

**Regla:** si una función no tiene side effects (no escribe archivos, no llama APIs), test unitario. Si los tiene, test de integración con TestClient o `tmp_path` de pytest.

---

## 5. Configuración de tu entorno (checklist)

Marca lo que ya tienes:

- [x] WSL2 + Ubuntu funcionando
- [x] Python 3.12 instalado
- [x] zsh + spaceship
- [x] Git + GitHub configurado (SSH)
- [x] Repo `automation-hub` creado
- [x] Primer endpoint FastAPI corriendo
- [ ] `venv` con todas las deps de `requirements.txt`
- [ ] VSCode con extensiones: Python, Pylance, Ruff (linter), Even Better TOML
- [ ] DBeaver o TablePlus para inspeccionar SQLite
- [ ] Power Automate Desktop instalado en Windows
- [ ] Bot de Telegram creado con BotFather
- [ ] Cloudflare account (para fase 8, opcional)

---

## 6. Vocabulario de entrevista (úsalo cuando te pregunten qué construiste)

- **Idempotencia:** que llamar al endpoint dos veces no genere efectos duplicados.
- **Observabilidad:** logs + métricas + auditoría = "puedo saber qué pasó".
- **Orquestación:** quién manda. En tu caso, APScheduler interno + PAD externo.
- **Reusabilidad:** PAD no replica lógica, llama al endpoint que ya tiene la lógica.
- **Separation of concerns:** routers manejan HTTP, services manejan lógica, schemas validan datos.
- **Async vs sync:** FastAPI permite ambos. Usa async cuando hagas I/O (httpx, DB), sync para CPU-bound (pandas).

**Frase de cierre para entrevistas:**
> "Construí Automation Hub porque vi que la mayoría de implementaciones RPA terminan en bots dispersos, sin tests, sin logs centralizados, sin reuso. Mi diseño centraliza la lógica en un servicio Python y deja al RPA tradicional como cliente — así obtengo lo mejor de ambos mundos: la interfaz visual de PAD para sistemas legacy + la robustez de un backend testeado."

---

## 7. Lo que NO vas a hacer (y por qué)

Para no perderte:
- ❌ **Auth completa** (JWT, OAuth) — overkill para un proyecto local. Si quieres, agrega un `API_KEY` simple en header.
- ❌ **PostgreSQL** — SQLite es suficiente y simplifica deploy.
- ❌ **Frontend** — `/docs` es tu UI. Frontend es otra cosa.
- ❌ **Kubernetes** — ni de broma para un proyecto de 1 servicio.
- ❌ **CI/CD** — agrégalo solo en fase 8 si te sobra tiempo (GitHub Actions corriendo `pytest`).
- ❌ **Microservicios** — un solo servicio bien hecho > tres servicios mal hechos.

---

## 8. Cuándo dar el salto al VPS (señales)

Si después de la fase 8 sigues motivado y quieres aprender deploy real, las señales que te dicen "ya estás listo":

1. Tu API funciona estable >2 semanas en local.
2. Quieres demos en vivo en entrevistas.
3. Quieres que tu bot Telegram responda 24/7 aunque apagues la PC.
4. Quieres aprender nginx, systemd, certbot.

**Setup recomendado entonces:**
- Hetzner CX22 Ubuntu 24 (€4/mes).
- Dominio en Cloudflare (~$10/año).
- Docker + docker-compose en el VPS.
- Cloudflare proxy → nginx → tu app.
- GitHub Actions para CI/CD: push a main → deploy automático.

Eso te abre conversaciones de "deploy" y "infra" en entrevistas que valen oro.

---

## 9. Métricas de progreso (qué medir)

Cada domingo, anota:
- Horas invertidas esta semana
- Fase completada (sí/no)
- Bloqueos encontrados
- Una cosa nueva que aprendiste

Si una fase te toma >2 semanas, **reduce scope, no aumentes tiempo**. Es preferible terminar el proyecto al 70% completo que abandonarlo al 90%.
