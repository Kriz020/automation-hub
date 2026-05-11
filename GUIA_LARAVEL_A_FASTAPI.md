# Automation Hub: Guia de Funcionamiento (Explicado con Manzanas y Peras)

## La Idea General

Imagina que tienes una fruteria. Todos los dias registras ventas en una libreta: que fruta vendiste, a quien, en que ciudad, cuanto cobraste. Al final del mes quieres saber: **¿en que ciudad vendi mas? ¿cuanto dinero hice por ciudad?**

Este proyecto automatiza exactamente eso. En vez de hacer las cuentas a mano, un programa:
1. Lee la libreta (un archivo CSV)
2. Filtra por lo que te interesa (fechas, ciudad)
3. Hace las sumas y los conteos
4. Te entrega un Excel limpio con el resumen

Y no solo eso: puede hacerlo **cuando tu quieras** (desde un navegador), **automaticamente cada dia a las 8am**, o **cuando le pides por Telegram**.

---

## Las Piezas del Proyecto

Piensa en el proyecto como una **fabrica de mermelada**:

| Pieza de la fabrica | Que hace | Archivo en el proyecto |
|---|---|---|
| El **mostrador** donde llegan los pedidos | Recibe solicitudes HTTP y las reparte a quien corresponda | `app/main.py` |
| Los **formularios** que rellena el cliente | Define que datos puede pedir (fechas, ciudad) | `app/schemas/reportes.py` |
| La **cocina** donde se procesa la fruta | Lee el CSV, filtra, agrupa, genera el Excel | `app/routers/reportes.py` |
| La **receta** secreta de la mermelada | La funcion que agarra los datos y los convierte en Excel | `app/services/excel_writer.py` |
| El **cuaderno** donde anotas cada pedido | Guarda un historial de cada ejecucion | `app/services/audit.py` |
| El **temporizador** que cuece solo | Ejecuta tareas a una hora fija todos los dias | `app/scheduler.py` |
| El **mensajero** que recibe encargos por telefono | Bot de Telegram que acepta comandos | `app/bot.py` |
| Las **recetas escritas** (datos de entrada) | El archivo CSV con las ventas | `data/ventas_tienda.csv` |
| El **archivo de configuracion** | Variables de entorno (puertos, tokens, carpetas) | `app/config.py` + `.env` |

---

## Recorrido Paso a Paso: Que Pasa Cuando Alguien Pide un Reporte

Vamos a seguir el camino de una solicitud, como si siguieramos una manzana desde que entra a la fabrica hasta que sale convertida en mermelada envasada.

---

### PASO 1 — Arranca la Fabrica

**Archivo: `app/main.py`**

Este es el punto de entrada. Cuando ejecutas el proyecto, este archivo:

```python
app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
```

**Que hace esta linea:** Crea la aplicacion web. Es como encender el letrero de "ABIERTO" de la tienda. FastAPI es el framework que maneja las solicitudes HTTP (las peticiones que llegan por internet).

Luego viene el `lifespan`. Es un bloque que se ejecuta al abrir y al cerrar:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()              # Prepara el cuaderno de registro (crea la BD si no existe)
    scheduler.start()      # Enciende el temporizador de tareas automaticas
    logger.info("Automation Hub iniciado")
    yield                  # <--- la fabrica trabaja aqui
    scheduler.shutdown()   # Apaga el temporizador al cerrar
    logger.info("Automation Hub detenido")
```

**En lenguaje manzana:** Abres la tienda, preparas la caja registradora (`init_db`), pones el temporizador de la coccion automatica (`scheduler.start`), abres al publico (`yield`). Cuando cierras, apagas el temporizador (`scheduler.shutdown`).

Luego el archivo "cuelga" los mostradores donde se atienden los pedidos:

```python
app.include_router(reportes.router)   # Mostrador de reportes
app.include_router(admin.router)     # Mostrador de administracion
```

Y define la puerta principal:

```python
@app.get("/")
def root():
    return {"app": settings.app_name, "status": "ok"}
```

Si alguien toca a la puerta principal (`GET /`), le respondes "estoy abierto, todo bien".

---

### PASO 2 — El Cliente Hace un Pedido

Imagina que Power Automate Desktop (un programa de Microsoft que automatiza tareas en Windows) envia esto por internet:

```
POST http://localhost:8000/reportes/ventas
Body: {"ciudad": "Guatemala"}
```

**Traduccion:** "Hola fabrica, quiero un reporte de ventas, pero solo de la ciudad de Guatemala."

Ese pedido llega a `app/main.py`, que ve la URL `/reportes/...` y dice: "esto es para el mostrador de reportes". Lo envia a:

**Archivo: `app/routers/reportes.py`**

Aqui esta definido el mostrador de reportes:

```python
router = APIRouter(prefix="/reportes", tags=["reportes"])
```

**Que hace:** `APIRouter` es un agrupador de rutas. Todo lo que llegue a `/reportes/...` se atiende aqui. Es como decir: "si el pedido es sobre reportes, pasen por esta ventanilla".

Dentro de este mostrador hay dos ventanillas:

**Ventanilla 1 — Solo para ver que hay disponible:**
```python
@router.get("/")
def listar_reportes():
    return {"disponibles": ["ventas-por-ciudad"]}
```

Si alguien pregunta `GET /reportes/`, le respondes: "tengo estos reportes: ventas-por-ciudad". Como un menu de restaurante.

**Ventanilla 2 — Para pedir un reporte de verdad:**
```python
@router.post("/ventas")
@auditar("POST /reportes/ventas")
def reporte_ventas(req: ReporteRequest):
```

Esta es la ventanilla importante. Vamos a desglosarla por partes.

---

### PASO 3 — El Formulario de Pedido (Validacion de Datos)

Antes de cocinar, hay que revisar que el pedido tenga sentido.

**Archivo: `app/schemas/reportes.py`**

```python
class ReporteRequest(BaseModel):
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    ciudad: str | None = None
```

**Que hace:** Define el formulario que el cliente debe llenar. Tres campos, todos opcionales:

| Campo | Tipo | Significado | Ejemplo |
|---|---|---|---|
| `fecha_inicio` | fecha o nada | "desde que fecha quieres el reporte" | `"2026-04-01"` |
| `fecha_fin` | fecha o nada | "hasta que fecha" | `"2026-04-30"` |
| `ciudad` | texto o nada | "de que ciudad" | `"Guatemala"` |

`date | None = None` significa: "esto puede ser una fecha, o puede ser nada. Si no me dices nada, lo dejo vacio."

Si el cliente manda `{"ciudad": 123}` (un numero en vez de texto), FastAPI **automaticamente** rechaza el pedido con un error "datos invalidos". No tuviste que escribir codigo de validacion — Pydantic lo hace por ti.

**En lenguaje pera:** El cliente rellena un formulario pidiendo peras. Si en vez de "Quito" escribe "12345" en el campo ciudad, le decimos "ese pedido no tiene sentido, corrijelo".

---

### PASO 4 — El Cuaderno de Registro (Auditoria)

**Archivo: `app/services/audit.py`**

Fijate en esta linea del mostrador:

```python
@auditar("POST /reportes/ventas")
```

El `@auditar` es un **decorador**. Un decorador es una funcion que envuelve a otra funcion para agregarle comportamiento extra, sin modificar la funcion original.

**En lenguaje manzana:** Imagina que cada vez que alguien pide mermelada, el encargado automaticamente anota en un cuaderno: que pidio, a que hora, cuanto tardo en prepararse, y si salio bien o no. El cocinero ni se entera — el encargado lo hace por el.

El decorador hace esto:

```
1. Mira el reloj y anota la hora de inicio
2. Deja que el cocinero trabaje
3. Cuando el cocinero termina (o si algo sale mal):
   - Mira el reloj otra vez y calcula cuanto tardo
   - Anota en el cuaderno: que endpoint, que parametros, resultado, duracion
   - Escribe en el log: "POST /reportes/ventas -> ok (150ms)"
```

El modelo de datos del cuaderno es esta clase:

```python
class Ejecucion(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    endpoint: str                    # Que ventanilla se uso
    fecha: datetime                  # Cuando
    parametros: str                  # Que pidio el cliente (guardado como texto JSON)
    resultado: str                   # "ok" o "error: no hay datos"
    duracion_ms: int                 # Cuantos milisegundos tardo
```

**Traduccion:** Cada fila del cuaderno tiene: numero de pedido, ventanilla usada, fecha y hora, que pidio el cliente, como salio, y cuanto tardo en milisegundos.

El archivo tambien contiene las funciones para usar ese cuaderno:

```python
def init_db():
    SQLModel.metadata.create_all(engine)
```
**Que hace:** Si el cuaderno no existe, lo crea. Es como comprar una libreta nueva el primer dia.

```python
def registrar(endpoint, parametros, resultado, duracion_ms):
    with Session(engine) as session:
        session.add(Ejecucion(...))
        session.commit()
```
**Que hace:** Escribe una linea nueva en el cuaderno. `Session` es como abrir la libreta, `add` es escribir, `commit` es cerrar y guardar.

```python
def obtener_historial(limit=50):
    with Session(engine) as session:
        return session.exec(
            select(Ejecucion).order_by(Ejecucion.id.desc()).limit(limit)
        ).all()
```
**Que hace:** Lee las ultimas 50 lineas del cuaderno, las mas recientes primero.

---

### PASO 5 — Leer los Datos de Ventas

Volviendo al mostrador (`app/routers/reportes.py`), ahora si entramos a la funcion principal:

```python
def reporte_ventas(req: ReporteRequest):
    df = pd.read_csv(f"{settings.data_dir}/ventas_tienda.csv")
```

**Que hace esta linea:** Abre el archivo `data/ventas_tienda.csv` y carga todas las ventas en memoria. El resultado `df` es un **DataFrame** de pandas.

**¿Que es un DataFrame?** Es una tabla en memoria, como una hoja de Excel dentro del programa. Tiene filas y columnas. Puedes hacerle preguntas como "dame solo las filas de Guatemala" o "suma la columna total".

El archivo CSV que se lee tiene esta pinta:

```
id, fecha, ciudad, cliente, producto, cantidad, precio_unitario, total
1, 2026-04-01, Guatemala, Cliente A, Manzana, 2, 100, 200
2, 2026-04-02, Mixco, Cliente B, Pera, 1, 50, 50
3, 2026-04-03, Guatemala, Cliente C, Manzana, 3, 100, 300
...50 filas en total...
```

**En lenguaje manzana:** Agarras la libreta de ventas del mes y la abres sobre la mesa. Todas las anotaciones estan ahi: 50 ventas de manzanas, peras, naranjas en 5 ciudades diferentes.

---

### PASO 6 — Filtrar los Datos

```python
    df["fecha"] = pd.to_datetime(df["fecha"])    # Convierte "2026-04-01" a fecha real

    if req.fecha_inicio:                          # Si el cliente pidio "desde tal fecha"
        df = df[df["fecha"] >= pd.Timestamp(req.fecha_inicio)]
    if req.fecha_fin:                             # Si el cliente pidio "hasta tal fecha"
        df = df[df["fecha"] <= pd.Timestamp(req.fecha_fin)]
    if req.ciudad:                                # Si el cliente pidio "solo tal ciudad"
        df = df[df["ciudad"].str.lower() == req.ciudad.lower()]
```

**Que hace cada linea:**

1. Convierte la columna `fecha` de texto a fechas reales, para poder comparar ("mayor que", "menor que").
2. Si el cliente dijo `fecha_inicio`, descarta todas las ventas anteriores a esa fecha.
3. Si el cliente dijo `fecha_fin`, descarta todas las posteriores.
4. Si el cliente dijo `ciudad`, descarta todas las que no sean de esa ciudad (comparando en minusculas para que "Guatemala" y "guatemala" sean lo mismo).
5. Si despues de todo el filtrado no quedo nada:

```python
    if df.empty:
        return {"error": "Sin datos para los filtros aplicados"}
```

**En lenguaje manzana:** De la libreta abierta sobre la mesa, tachas todas las filas que no te interesan. "Solo quiero abril", tachas las de marzo. "Solo Guatemala", tachas Mixco, Quetzaltenango, etc. Si al final no quedo nada, le dices al cliente: "con esos filtros no hay ventas, prueba con otros".

---

### PASO 7 — Hacer las Cuentas y Generar el Excel

```python
    output = Path(settings.output_dir) / "reporte_ventas.xlsx"
    generar_reporte_ventas(df, output)
```

Esto llama a la funcion en **`app/services/excel_writer.py`**:

```python
def generar_reporte_ventas(df: pd.DataFrame, output_path: Path) -> Path:
    resumen = (
        df.groupby("ciudad")                        # Agrupa todas las filas por ciudad
          .agg(total=("total", "sum"),               # Para cada ciudad, SUMA la columna "total"
               num_ventas=("id", "count"))           # Para cada ciudad, CUENTA cuantas ventas hubo
          .sort_values("total", ascending=False)     # Ordena: la ciudad que mas vendio primero
          .reset_index()                             # Limpia el indice para que quede bonito
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)  # Crea la carpeta output/ si no existe
    resumen.to_excel(output_path, index=False, sheet_name="Ventas por Ciudad")  # Escribe el Excel
    return output_path
```

**Que hace, paso a paso:**

1. **`df.groupby("ciudad")`** — Junta todas las filas que son de la misma ciudad. Si habia 10 ventas en Guatemala, 7 en Mixco y 3 en Quetzaltenango, ahora tienes 3 grupos.

2. **`.agg(total=("total", "sum"), num_ventas=("id", "count"))`** — Para cada grupo (ciudad), calcula dos cosas:
   - `total`: suma todos los valores de la columna "total" (cuanto dinero se hizo)
   - `num_ventas`: cuenta cuantas filas hay (cuantas ventas se hicieron)

3. **`.sort_values("total", ascending=False)`** — Ordena de mayor a menor. La ciudad que mas dinero genero aparece primero.

4. **`.reset_index()`** — Limpieza tecnica para que la tabla quede con columnas normales.

5. **`resumen.to_excel(output_path, ...)`** — Escribe el resultado a un archivo `.xlsx` (Excel) en la carpeta `output/`. Le pone como titulo de hoja "Ventas por Ciudad".

**En lenguaje manzana:** Agarras la libreta ya filtrada y haces montoncitos por ciudad. Para cada monton, cuentas cuantas ventas hay y sumas el dinero. Luego ordenas los montones: el que mas dinero tiene va primero. Pasas todo eso a una hoja de Excel limpia, con su titulo y todo.

---

### PASO 8 — Entregar el Excel al Cliente

```python
    return FileResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="reporte_ventas.xlsx",
    )
```

**Que hace:** Toma el archivo Excel recien creado y se lo envia al cliente como respuesta HTTP. El `media_type` le dice al cliente: "te estoy mandando un archivo Excel, no una pagina web ni un JSON".

**En lenguaje pera:** El cocinero le pasa la mermelada envasada al mostrador, y el mostrador se la entrega al cliente en una bolsa con etiqueta.

El cliente (Power Automate Desktop, Telegram, o el navegador) recibe el archivo y lo guarda donde corresponda.

---

## Las Demas Piezas de la Fabrica

### El Temporizador Automatico

**Archivo: `app/scheduler.py`**

```python
scheduler = BackgroundScheduler()

def job_reporte_diario():
    logger.info("Ejecutando job_reporte_diario")
    df = pd.read_csv("data/ventas_tienda.csv")                     # Lee el CSV
    generar_reporte_ventas(df, Path("output/reporte_diario.xlsx")) # Genera el Excel
    logger.info("job_reporte_diario completado")

scheduler.add_job(
    job_reporte_diario,
    CronTrigger(hour=8, minute=0),   # Dispara a las 8:00 AM cada dia
    id="reporte_diario",
)
```

**Que hace:** Todos los dias a las 8:00 AM, sin que nadie se lo pida, el temporizador:
1. Lee el archivo de ventas
2. Llama a la misma funcion `generar_reporte_ventas()` que usa el mostrador
3. Guarda el Excel en `output/reporte_diario.xlsx`

**En lenguaje manzana:** Es como un temporizador de cocina. Todas las mananas a las 8am, automaticamente prepara un lote de mermelada sin que nadie venga al mostrador a pedirla. Usa la misma receta — lo unico que cambia es quien la dispara (el reloj en vez de un cliente).

---

### El Mensajero de Telegram

**Archivo: `app/bot.py`**

Este es un programa independiente. No es parte del mostrador — corre por separado. Su trabajo es escuchar Telegram y reenviar pedidos al mostrador.

```python
async def reporte(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Generando reporte...")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{API_BASE}/reportes/ventas", json={})
    if r.status_code == 200:
        await update.message.reply_document(
            document=r.content, filename="reporte_ventas.xlsx"
        )
```

**Que hace:** Cuando alguien escribe `/reporte` en Telegram:
1. El bot contesta: "Generando reporte..."
2. El bot **llama a su propio mostrador** — hace un `POST` HTTP a `http://localhost:8000/reportes/ventas` (usa `httpx`, que es una libreria para hacer llamadas HTTP desde Python)
3. Si el mostrador responde con exito, agarra los bytes del Excel y los manda al chat de Telegram como un archivo adjunto
4. Si falla, manda un mensaje de error

El bot tambien tiene el comando `/historial`:

```python
async def historial(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_BASE}/admin/historial")
    registros = r.json()[:10]
    # formatea y envia las ultimas 10 ejecuciones
```

**Que hace:** Le pide al mostrador de administracion las ultimas ejecuciones y las muestra formateadas en el chat.

Los comandos se registran asi:

```python
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reporte", reporte))
app.add_handler(CommandHandler("historial", historial))
app.run_polling()  # Se queda escuchando Telegram para siempre
```

**En lenguaje manzana:** Imagina que tienes un mensajero con un telefono. Cuando alguien llama y dice "dame mermelada", el mensajero va al mostrador, pide la mermelada, y se la lleva al cliente. El cliente nunca tuvo que ir a la tienda — el mensajero hizo de intermediario.

---

### La Configuracion

**Archivo: `app/config.py`**

```python
class Settings(BaseSettings):
    app_name: str = "Automation Hub"
    debug: bool = True
    data_dir: str = "data"
    output_dir: str = "output"
    telegram_token: str = ""

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
```

**Que hace:** Define todas las configuraciones del proyecto:
- `app_name` — el nombre de la aplicacion
- `debug` — si esta en modo depuracion
- `data_dir` — carpeta donde estan los datos de entrada (el CSV)
- `output_dir` — carpeta donde se guardan los Excel generados
- `telegram_token` — la contraseña del bot de Telegram

`SettingsConfigDict(env_file=".env")` le dice: "lee estas configuraciones del archivo `.env`". Si no estan en `.env`, usa los valores por defecto.

La variable `settings` es un **singleton** — se crea una sola vez y se importa desde cualquier archivo con `from app.config import settings`.

**En lenguaje manzana:** Es la lista de parametros de la fabrica: donde esta la bodega de fruta, donde se guarda la mermelada terminada, la clave del telefono del mensajero. Esta en un solo lugar para que si hay que cambiar algo, se cambia ahi y toda la fabrica se entera.

---

### La Administracion

**Archivo: `app/routers/admin.py`**

```python
router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/historial", response_model=list[Ejecucion])
def historial():
    return obtener_historial()
```

**Que hace:** Es otro mostrador, este para tareas administrativas. Tiene una sola ventanilla:
- `GET /admin/historial` — devuelve las ultimas 50 ejecuciones registradas en el cuaderno de auditoria

`response_model=list[Ejecucion]` le dice a FastAPI: "la respuesta va a ser una lista de objetos tipo Ejecucion". FastAPI usa esto para:
1. Validar que la respuesta tiene el formato correcto
2. Generar la documentacion automatica en `/docs`

---

### La Generacion de Datos de Prueba

**Archivo: `scripts/generar_ventas.py`**

Este script crea el archivo `data/ventas_tienda.csv` con datos sinteticos (inventados pero realistas):
- 50 ventas
- 5 ciudades de Guatemala
- 8 productos (manzana, pera, naranja, uva, platano, mango, fresa, sandia)
- Fechas entre el 1 y el 30 de abril de 2026
- Usa una **semilla** (`seed=42`) para que siempre genere los mismos datos

Se ejecuta una sola vez: `python scripts/generar_ventas.py`

---

## Resumen: El Flujo Completo Visual

```
                           QUIEN DISPARA EL PROCESO
                                        |
            +---------------------------+---------------------------+
            |                           |                           |
            v                           v                           v
     Power Automate              Navegador/Swagger            Bot de Telegram
     (POST HTTP)                 (http://localhost:8000)      (comando /reporte)
            |                           |                           |
            +---------------------------+---------------------------+
                                        |
                                        v
                            +-----------------------+
                            |    app/main.py        |
                            |    La puerta de la    |
                            |    fabrica. Recibe    |
                            |    el pedido HTTP     |
                            +-----------------------+        
                                        |
                            Que URL pidieron?
                            /reportes/... -> mostrador de reportes
                            /admin/...    -> mostrador de admin
                            /             -> "estoy vivo"
                                        |
                                        v
                            +-----------------------+
                            | app/routers/          |
                            | reportes.py           |
                            |                       |
                            | @router.post("/ventas")|
                            | def reporte_ventas()  |
                            +-----------------------+
                                        |
            +---------------------------+---------------------------+
            |                           |                           |
            v                           v                           v
    +------------------+     +------------------+     +------------------+
    | VALIDAR PEDIDO   |     | INICIAR REGISTRO |     | LEER CSV        |
    | ReporteRequest   |     | @auditar toma    |     | pd.read_csv()   |
    | ¿fechas? ¿ciudad?|     | la hora inicial  |     | 50 filas de     |
    | schemas/         |     | audit.py         |     | ventas en memoria|
    | reportes.py      |     |                  |     |                  |
    +------------------+     +------------------+     +--------+---------+
                                                                |
                                                                v
                                                     +------------------+
                                                     | FILTRAR DATOS    |
                                                     | ¿fecha_inicio?   |
                                                     | ¿fecha_fin?      |
                                                     | ¿ciudad?         |
                                                     | Descartar lo que |
                                                     | no interesa      |
                                                     +--------+---------+
                                                              |
                                                              v
                                                     +------------------+
                                                     | TRANSFORMAR      |
                                                     | groupby("ciudad")|
                                                     | suma totales     |
                                                     | cuenta ventas    |
                                                     | ordena ranking   |
                                                     | excel_writer.py  |
                                                     +--------+---------+
                                                              |
                                                              v
                                                     +------------------+
                                                     | ENTREGAR         |
                                                     | FileResponse     |
                                                     | manda el .xlsx   |
                                                     | al cliente       |
                                                     +--------+---------+
                                                              |
            +---------------------------+---------------------------+
            |                           |                           |
            v                           v                           v
    Power Automate              El navegador                Telegram
    guarda en                   descarga el                 recibe el Excel
    C:\reportes\                archivo                     en el chat


    ADEMAS (en paralelo, al final):
    
    +------------------------------------------------------+
    | @auditar termina su trabajo                           |
    | - Calcula cuanto tardo (duracion_ms)                  |
    | - Escribe en audit.db: endpoint, params, resultado    |
    | - Escribe en logs/app.log con loguru                  |
    +------------------------------------------------------+
```

---

## Glosario de Terminos Tecnicos

| Termino | Que significa |
|---|---|
| **FastAPI** | El framework web. Maneja las solicitudes HTTP. Es el edificio de la fabrica. |
| **APIRouter** | Agrupa rutas relacionadas. Como poner todas las ventanillas de reportes en un mismo pasillo. |
| **Endpoint** | Una URL especifica + el verbo HTTP. `POST /reportes/ventas` es un endpoint. |
| **Pydantic** | Libreria de validacion de datos. Revisa que los formularios tengan sentido. |
| **DataFrame** | Tabla en memoria de pandas. Como una hoja de Excel dentro del programa. |
| **pandas** | La libreria principal para manipulacion de datos en Python. Lee CSVs, filtra, agrupa, calcula. |
| **Decorador** | Una funcion que envuelve a otra para agregarle comportamiento. Se escribe con `@`. |
| **SQLModel** | Combina Pydantic (validacion) + SQLAlchemy (base de datos). Define tablas y las consulta. |
| **SQLite** | Base de datos ligera que vive en un solo archivo (`audit.db`). No necesita servidor aparte. |
| **APScheduler** | Temporizador que ejecuta tareas a horas programadas. |
| **httpx** | Cliente HTTP. Sirve para hacer llamadas a otras URLs desde Python. |
| **loguru** | Libreria de logging. Escribe mensajes de registro en archivos. |
| **uvicorn** | El servidor que ejecuta FastAPI. Como Apache/Nginx pero para Python. |
| **lifespan** | Eventos que ocurren al iniciar y al apagar la aplicacion. |
| **FileResponse** | Respuesta HTTP que envia un archivo al cliente. |
| **openpyxl** | Libreria que genera archivos Excel (.xlsx). Pandas la usa internamente. |

---

## Para Tu Entrevista de RPA

Cuando te pregunten por este proyecto, enfocate en estos puntos:

1. **El proyecto es un BACKEND que centraliza automatizaciones.** Power Automate Desktop es el CLIENTE que consume este servicio.

2. **El patron es siempre:** disparador -> HTTP request -> procesamiento -> archivo de salida.

3. **Tres formas de disparar el mismo proceso:**
   - Manual: alguien llama al endpoint desde el navegador o Swagger
   - Programado: el scheduler interno lo hace a las 8am
   - Bot: un usuario de Telegram pide `/reporte`

4. **Separacion de responsabilidades:** La logica de generar el Excel (`excel_writer.py`) esta separada de quien la llama (el endpoint HTTP, el scheduler, o el bot). Todos usan la misma funcion.

5. **Trazabilidad:** Cada ejecucion queda registrada en `audit.db` con endpoint, parametros, resultado y duracion. Sabes exactamente que paso, cuando, y cuanto tardo.

6. **Stack tecnologico:** FastAPI (framework web), pandas (datos), openpyxl (Excel), APScheduler (temporizador), SQLModel+SQLite (historial), httpx (llamadas HTTP entre servicios), python-telegram-bot (bot).
