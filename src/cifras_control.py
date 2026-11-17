"""
StreamView Analytics - EP5 Visualizacion de Datos
Cifras de control para verificar el dashboard de Power BI.

Calcula, con pandas y directamente sobre los datos procesados, el valor que debe mostrar cada
medida del dashboard (dashboard/medidas_dax.dax) para los filtros mas importantes, y las compara
con `kpis_resumen.csv` (que calcula src/kpis.py con otro codigo). Si las dos fuentes no coinciden,
el script falla: asi se sabe que la cifra de referencia es confiable antes de compararla con Power BI.

Uso (desde la raiz del proyecto):
    python src/cifras_control.py     # escribe dashboard/cifras_de_control.csv

Requiere haber ejecutado antes `python src/data_prep.py`.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from traducciones import SIN_GENERO  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
SALIDA = ROOT / "dashboard" / "cifras_de_control.csv"
GENEROS_CONTROL = ["Animación", "Drama", "Documental"]  # Documental tiene < 30 películas válidas: debe quedar fuera del gráfico de ROI


def medidas(d: pd.DataFrame) -> dict:
    """Valor de cada medida DAX para el subconjunto `d` (misma lógica que dashboard/medidas_dax.dax)."""
    fin = d[d["financiero_valido"]]
    conf = d[d["rating_confiable"]]
    return {
        "Total de títulos": len(d),
        "Títulos con rating confiable": len(conf),
        "Rating promedio (0-10)": round(conf["rating"].mean(), 2),
        "Popularidad promedio (índice)": round(d["popularidad"].mean(), 2),
        "Películas con datos financieros": len(fin),
        "ROI mediano (x)": round(fin["roi"].median(), 2) if len(fin) else None,
        "Presupuesto total (USD millones)": round(fin["presupuesto_usd"].sum() / 1e6) if len(fin) else None,
        "Ingreso total (USD millones)": round(fin["ingresos_usd"].sum() / 1e6) if len(fin) else None,
    }


def construir(df: pd.DataFrame, bridge: pd.DataFrame) -> pd.DataFrame:
    filas = []

    def agregar(filtro, dic):
        for medida, valor in dic.items():
            filas.append({"filtro": filtro, "medida": medida, "valor_esperado": "" if valor is None or pd.isna(valor) else valor})

    agregar("Tipo = Todos", medidas(df))
    agregar("Tipo = Película", medidas(df[df["tipo"] == "Película"]))
    agregar("Tipo = Serie", medidas(df[df["tipo"] == "Serie"]))
    g = bridge[bridge["genero"] != SIN_GENERO]
    for genero in GENEROS_CONTROL:
        ids = g.loc[g["genero"] == genero, "id_contenido"]
        agregar(f"Género = {genero}", medidas(df[df["id_contenido"].isin(ids)]))
    return pd.DataFrame(filas)


def verificar_con_kpis(controles: pd.DataFrame, kpis: pd.DataFrame) -> list:
    """Compara con kpis_resumen.csv (calculado en src/kpis.py). Devuelve las diferencias."""
    cruces = [("Total de títulos", "K01"), ("Rating promedio (0-10)", "K03"), ("Popularidad promedio (índice)", "K04"),
              ("Películas con datos financieros", "F01"), ("ROI mediano (x)", "F04")]
    difs = []
    for tipo in ["Todos", "Película", "Serie"]:
        for medida, kid in cruces:
            esperado = controles[(controles["filtro"] == f"Tipo = {tipo}") & (controles["medida"] == medida)]["valor_esperado"].iloc[0]
            k = kpis[(kpis["kpi_id"] == kid) & (kpis["tipo_contenido"] == tipo)]["valor"].iloc[0]
            if str(k) == "No aplica":  # KPIs financieros de series: kpis.py escribe "No aplica"; en Power BI queda en blanco o 0
                continue
            if abs(float(esperado) - float(k)) > 1e-9:
                difs.append((tipo, medida, esperado, k))
    # ROI por genero (F06) y rating por genero (K21 usa >= 100 titulos: se compara solo si el genero entra)
    f06 = kpis[(kpis["kpi_id"] == "F06") & (kpis["tipo_contenido"] == "Todos")].set_index("dimension")["valor"].astype(float)
    for genero in GENEROS_CONTROL:
        fila = controles[(controles["filtro"] == f"Género = {genero}") & (controles["medida"] == "ROI mediano (x)")]["valor_esperado"].iloc[0]
        if genero in f06.index and abs(float(fila) - f06[genero]) > 1e-9:
            difs.append((genero, "ROI mediano (x)", fila, f06[genero]))
        if genero not in f06.index:
            print(f"   {genero}: no aparece en F06 (menos de 30 películas válidas), como corresponde.")
    return difs


def main():
    df = pd.read_csv(PROCESSED / "streamview_content_clean.csv")
    bridge = pd.read_csv(PROCESSED / "genero_puente.csv")
    kpis = pd.read_csv(PROCESSED / "kpis_resumen.csv")
    controles = construir(df, bridge)
    difs = verificar_con_kpis(controles, kpis)
    if difs:
        raise SystemExit(f"Las cifras de control no coinciden con kpis_resumen.csv: {difs}")
    SALIDA.parent.mkdir(exist_ok=True)
    controles.to_csv(SALIDA, index=False, encoding="utf-8")
    print(f"{len(controles)} cifras de control guardadas en {SALIDA} (coinciden con kpis_resumen.csv)")


if __name__ == "__main__":
    main()
