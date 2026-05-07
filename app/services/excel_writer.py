from pathlib import Path
import pandas as pd

def generar_reporte_ventas(df: pd.DataFrame, output_path: Path) -> Path:
    resumen = (
        df.groupby("ciudad")
          .agg(total=("total", "sum"), num_ventas=("id", "count"))
          .sort_values("total", ascending=False)
          .reset_index()
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    resumen.to_excel(output_path, index=False, sheet_name="Ventas por Ciudad")
    return output_path
