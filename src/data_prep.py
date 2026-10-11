"""
StreamView Analytics - EP3 Visualizacion de Datos
Preparacion e integracion de fuentes de datos (peliculas y series).

Ejecutar desde la raiz del proyecto:
    python src/data_prep.py

Genera en data/processed/:
    streamview_content_clean.csv   -> dataset unificado y limpio (una fila por titulo)
    streamview_powerbi.csv         -> misma data sin texto libre, para Power BI
    genero_puente.csv              -> tabla puente titulo-genero (una fila por genero)
    validacion_datos.csv           -> trazabilidad: filas por paso, nulos, unidades
    kpis_resumen.csv               -> KPIs de la ficha (docs/ficha_kpis.md)
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from genre_map import SIN_GENERO, canonical_genres, main_genre  # noqa: E402
from kpis import build_kpis  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)

MOVIES_FILE = RAW / "netflix_movies_detailed_up_to_2025.csv"
TV_FILE = RAW / "netflix_tv_shows_detailed_up_to_2025.csv"

# Criterio unico de "dato financiero valido" (codigo, ficha de KPIs, informe y Power BI)
MIN_BUDGET_USD = 1_000_000
MIN_VOTES = 20  # votos minimos para considerar confiable un rating


def load_raw():
    movies = pd.read_csv(MOVIES_FILE)
    tv = pd.read_csv(TV_FILE)
    return movies, tv


def first_token(value):
    """Devuelve el primer elemento de una lista separada por comas (pais principal)."""
    if pd.isna(value):
        return np.nan
    return str(value).split(",")[0].strip()


def clean_and_unify(movies: pd.DataFrame, tv: pd.DataFrame) -> pd.DataFrame:
    # --- Peliculas ---
    m = movies.copy()
    m["seasons"] = np.nan
    m["duration_min"] = np.nan  # el dataset no trae duracion en minutos para peliculas

    # --- Series ---
    t = tv.copy()
    t["seasons"] = t["duration"].str.extract(r"(\d+)").astype(float)
    t["duration_min"] = np.nan
    for col in ["budget", "revenue"]:
        if col not in t.columns:
            t[col] = np.nan

    common_cols = [
        "show_id", "type", "title", "director", "cast", "country", "date_added",
        "release_year", "rating", "genres", "language", "description",
        "popularity", "vote_count", "vote_average", "budget", "revenue",
        "seasons", "duration_min",
    ]
    m = m.reindex(columns=common_cols)
    t = t.reindex(columns=common_cols)

    df = pd.concat([m, t], ignore_index=True)

    # Limpieza basica
    df = df.drop_duplicates(subset=["show_id", "title", "type"]).reset_index(drop=True)
    df["date_added"] = pd.to_datetime(df["date_added"], errors="coerce")
    df["year_added"] = df["date_added"].dt.year
    df["decade"] = (df["release_year"] // 10 * 10).astype("Int64")

    # show_id viene de TMDB y se repite entre peliculas y series (406 casos):
    # la clave unica del titulo es tipo + show_id.
    df["content_id"] = df["type"].map({"Movie": "M", "TV Show": "S"}) + "_" + df["show_id"].astype(str)

    # Genero y pais principal. El genero usa la taxonomia unificada (genre_map.py).
    df["main_genre"] = df["genres"].apply(main_genre)
    df["main_country"] = df["country"].apply(first_token).fillna("Sin pais informado")

    # Datos financieros: solo peliculas con presupuesto >= 1M USD e ingresos > 0
    # (evita ROI extremos por presupuestos simbolicos). Un unico criterio para todo el proyecto.
    df["financiero_valido"] = (
        (df["type"] == "Movie") & (df["budget"] >= MIN_BUDGET_USD) & (df["revenue"] > 0)
    )
    # ROI = ingresos / presupuesto (razon: 1,0 = recupera lo invertido)
    df["roi"] = np.where(df["financiero_valido"], df["revenue"] / df["budget"], np.nan)

    # Rating confiable: vote_count minimo para evitar promedios poco representativos
    df["rating_confiable"] = df["vote_count"] >= MIN_VOTES

    return df


def build_genre_bridge(df: pd.DataFrame) -> pd.DataFrame:
    """Tabla puente titulo-genero: una fila por cada genero canonico del titulo
    (los titulos sin genero quedan con SIN_GENERO)."""
    rows = []
    for content_id, tipo, genres in zip(df["content_id"], df["type"], df["genres"]):
        for g in canonical_genres(genres):
            rows.append((content_id, tipo, g))
    return pd.DataFrame(rows, columns=["content_id", "type", "genero"])


def build_validation_table(movies: pd.DataFrame, tv: pd.DataFrame,
                           df: pd.DataFrame, bridge: pd.DataFrame) -> pd.DataFrame:
    """Tabla de trazabilidad: filas por paso, nulos por columna, filas afectadas por
    decisiones de limpieza y unidades de cada variable."""
    rows = []

    def add(seccion, metrica, valor, detalle=""):
        rows.append({"seccion": seccion, "metrica": metrica, "valor": valor, "detalle": detalle})

    n_raw = len(movies) + len(tv)
    n_clean = len(df)
    add("1_filas_por_paso", "Peliculas (fuente 1)", len(movies), "netflix_movies_detailed_up_to_2025.csv")
    add("1_filas_por_paso", "Series (fuente 2)", len(tv), "netflix_tv_shows_detailed_up_to_2025.csv")
    add("1_filas_por_paso", "Union de ambas fuentes", n_raw, "concat con columnas comunes")
    add("1_filas_por_paso", "Duplicados eliminados", n_raw - n_clean,
        "mismo show_id + titulo + tipo")
    add("1_filas_por_paso", "Dataset limpio (una fila por titulo)", n_clean, "streamview_content_clean.csv")
    add("1_filas_por_paso", "Filas de la tabla puente titulo-genero", len(bridge),
        "genero_puente.csv (un titulo puede tener varios generos)")

    for col, pct in (df.isna().mean() * 100).round(1).items():
        add("2_nulos_por_columna_%", col, pct, "% de filas con valor nulo")

    sin_gen = bridge[bridge["genero"] == SIN_GENERO].groupby("type").size()
    for tipo in ["Movie", "TV Show"]:
        add("3_decisiones", f"Titulos sin genero informado ({tipo})", int(sin_gen.get(tipo, 0)),
            "genres vacio en la fuente: se mantienen en conteos de catalogo, se excluyen de rankings por genero")
    add("3_decisiones", "Titulos sin pais informado", int((df["main_country"] == "Sin pais informado").sum()),
        "se mantienen en el catalogo; se excluyen del ranking de paises")
    add("3_decisiones", "Titulos con rating confiable (>=20 votos)", int(df["rating_confiable"].sum()),
        "solo ellos entran al rating promedio")
    peliculas = df[df["type"] == "Movie"]
    add("3_decisiones", "Peliculas con financieros validos", int(df["financiero_valido"].sum()),
        f"presupuesto >= {MIN_BUDGET_USD:,} USD e ingresos > 0, de {len(peliculas):,} peliculas".replace(",", "."))
    add("3_decisiones", "Peliculas con presupuesto/ingresos > 0 pero bajo el umbral",
        int(((peliculas["budget"] > 0) & (peliculas["revenue"] > 0)).sum() - df["financiero_valido"].sum()),
        "se descartan del analisis financiero")

    unidades = [
        ("budget / revenue", "USD"),
        ("vote_average / rating", "escala 0-10 (promedio de votos TMDB; no es clasificacion etaria)"),
        ("vote_count", "numero de votos"),
        ("popularity", "indice relativo TMDB (sin unidad)"),
        ("roi", "razon ingresos / presupuesto (sin unidad; 1,0 = recupera lo invertido)"),
        ("release_year / year_added", "anio calendario"),
        ("seasons", "numero de temporadas (solo series)"),
    ]
    for var, unidad in unidades:
        add("4_unidades", var, unidad)

    return pd.DataFrame(rows)


POWERBI_COLUMNS = [
    "content_id", "show_id", "type", "title", "main_genre", "main_country", "language",
    "release_year", "year_added", "decade", "vote_average", "vote_count", "popularity",
    "budget", "revenue", "roi", "financiero_valido", "rating_confiable", "seasons",
]


def save_powerbi_dataset(df: pd.DataFrame) -> Path:
    """Guarda una version del dataset sin columnas de texto libre (description,
    cast, director), que no se usan en el dashboard y suelen causar errores de
    parseo (comas, comillas y saltos de linea dentro del texto) al importar el
    CSV directamente en Power BI."""
    out = df[POWERBI_COLUMNS].copy()
    out["financiero_valido"] = out["financiero_valido"].map({True: "True", False: "False"})
    out["rating_confiable"] = out["rating_confiable"].map({True: "True", False: "False"})
    out_file = PROCESSED / "streamview_powerbi.csv"
    out.to_csv(out_file, index=False)
    return out_file


def main():
    movies, tv = load_raw()
    df = clean_and_unify(movies, tv)
    out_file = PROCESSED / "streamview_content_clean.csv"
    df.to_csv(out_file, index=False)
    print(f"Dataset unificado guardado en: {out_file} ({len(df):,} filas)")

    powerbi_file = save_powerbi_dataset(df)
    print(f"Dataset para Power BI (sin texto libre) guardado en: {powerbi_file} ({len(df):,} filas)")

    bridge = build_genre_bridge(df)
    bridge_file = PROCESSED / "genero_puente.csv"
    bridge.to_csv(bridge_file, index=False)
    print(f"Tabla puente titulo-genero guardada en: {bridge_file} ({len(bridge):,} filas)")

    validation = build_validation_table(movies, tv, df, bridge)
    validation_file = PROCESSED / "validacion_datos.csv"
    validation.to_csv(validation_file, index=False)
    print(f"Tabla de validacion guardada en: {validation_file} ({len(validation)} filas)")

    kpis = build_kpis(df, bridge)
    kpis_file = PROCESSED / "kpis_resumen.csv"
    kpis.to_csv(kpis_file, index=False)
    print(f"KPIs guardados en: {kpis_file} ({len(kpis)} filas, {kpis['kpi_id'].nunique()} KPIs)")


if __name__ == "__main__":
    main()
