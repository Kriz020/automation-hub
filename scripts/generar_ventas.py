"""Genera ventas_tienda.csv con datos sintéticos para desarrollo."""
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)  # reproducible

CIUDADES = ["Guatemala", "Quetzaltenango", "Antigua", "Escuintla", "Huehuetenango"]
PRODUCTOS = [
    ("Café molido", 45.00),
    ("Pan dulce", 8.50),
    ("Chocolate", 25.00),
    ("Tortillas", 5.00),
    ("Frijol negro", 18.00),
    ("Azúcar", 12.00),
    ("Aceite", 35.00),
    ("Arroz", 15.00),
]
CLIENTES = [
    "María López", "Juan Pérez", "Ana García", "Carlos Ruiz",
    "Sofía Hernández", "Diego Morales", "Lucía Castro", "Pedro Ramírez",
    "Isabel Méndez", "Andrés Vásquez",
]

def generar(n_filas=50):
    rows = []
    fecha_base = datetime(2026, 4, 1)
    for i in range(1, n_filas + 1):
        producto, precio = random.choice(PRODUCTOS)
        cantidad = random.randint(1, 10)
        fecha = fecha_base + timedelta(days=random.randint(0, 30))
        rows.append({
            "id": i,
            "fecha": fecha.strftime("%Y-%m-%d"),
            "ciudad": random.choice(CIUDADES),
            "cliente": random.choice(CLIENTES),
            "producto": producto,
            "cantidad": cantidad,
            "precio_unitario": precio,
            "total": round(cantidad * precio, 2),
        })
    return rows

if __name__ == "__main__":
    output = Path(__file__).parent.parent / "data" / "ventas_tienda.csv"
    output.parent.mkdir(exist_ok=True)
    rows = generar()
    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"✓ Generado {output} con {len(rows)} filas")
