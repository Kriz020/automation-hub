import json
import time
from datetime import datetime
from functools import wraps

from loguru import logger
from sqlmodel import Field, Session, SQLModel, create_engine, select

DB_PATH = "audit.db"
engine = create_engine(f"sqlite:///{DB_PATH}")


class Ejecucion(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    endpoint: str
    fecha: datetime = Field(default_factory=datetime.now)
    parametros: str
    resultado: str
    duracion_ms: int


def init_db():
    SQLModel.metadata.create_all(engine)


def registrar(endpoint: str, parametros: dict, resultado: str, duracion_ms: int):
    with Session(engine) as session:
        session.add(
            Ejecucion(
                endpoint=endpoint,
                parametros=json.dumps(parametros, default=str),
                resultado=resultado,
                duracion_ms=duracion_ms,
            )
        )
        session.commit()


def auditar(endpoint_name: str):
    """Decorator que mide tiempo y registra cada llamada en audit.db."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            resultado = "ok"
            try:
                return func(*args, **kwargs)
            except Exception as e:
                resultado = f"error: {e}"
                raise
            finally:
                duracion_ms = int((time.perf_counter() - start) * 1000)
                params = {k: v for k, v in kwargs.items() if k != "req"}
                logger.info(f"{endpoint_name} → {resultado} ({duracion_ms}ms)")
                registrar(endpoint_name, params, resultado, duracion_ms)
        return wrapper
    return decorator


def obtener_historial(limit: int = 50) -> list[Ejecucion]:
    with Session(engine) as session:
        return session.exec(
            select(Ejecucion).order_by(Ejecucion.id.desc()).limit(limit)
        ).all()
