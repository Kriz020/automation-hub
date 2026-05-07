import pandas as pd
import pytest
from pathlib import Path

from app.services.excel_writer import generar_reporte_ventas


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_listar_reportes(client):
    r = client.get("/reportes/")
    assert r.status_code == 200
    assert "disponibles" in r.json()


def test_generar_reporte_ventas_sin_filtros(client):
    r = client.post("/reportes/ventas", json={})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith(
        "application/vnd.openxmlformats"
    )


def test_generar_reporte_ventas_con_ciudad(client):
    r = client.post("/reportes/ventas", json={"ciudad": "Guatemala"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith(
        "application/vnd.openxmlformats"
    )


def test_generar_reporte_ventas_ciudad_inexistente(client):
    r = client.post("/reportes/ventas", json={"ciudad": "CiudadQueNoExiste"})
    assert r.status_code == 200
    assert "error" in r.json()


def test_generar_excel_unitario(tmp_path):
    df = pd.DataFrame({
        "ciudad": ["A", "A", "B"],
        "total": [100, 200, 50],
        "id": [1, 2, 3],
    })
    output = tmp_path / "test.xlsx"
    generar_reporte_ventas(df, output)
    assert output.exists()
    assert output.stat().st_size > 0


def test_historial(client):
    client.post("/reportes/ventas", json={})
    r = client.get("/admin/historial")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
