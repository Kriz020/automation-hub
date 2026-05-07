# PAD Flows

## Cómo importar

1. Abrir Power Automate Desktop → Console
2. Click en "Import" → seleccionar el archivo `.txt`
3. Configurar la URL según tu entorno (ver abajo)

## URL de la API

Desde Windows hacia WSL2:

```
http://localhost:8000
```

Si localhost no funciona, obtener la IP de WSL con:

```bash
ip addr show eth0 | grep inet
```

Y usar `http://172.x.x.x:8000`.

**Requisito:** arrancar FastAPI con `--host 0.0.0.0`:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Flujos disponibles

| Archivo | Descripción |
|---|---|
| `reporte_diario.txt` | Llama a POST /reportes/ventas y guarda el Excel en C:\reportes\ |

## Schedule recomendado

- APScheduler genera el Excel a las **8:00am**
- PAD descarga y archiva a las **8:30am** (margen para que esté listo)
