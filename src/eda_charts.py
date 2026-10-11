"""
StreamView Analytics - EP3 Visualizacion de Datos
Graficos estaticos del analisis exploratorio (EDA).

Cada funcion `g_*` construye un grafico y, si `guardar=True`, lo exporta a images/.
Todos los titulos indican el periodo (anios de estreno) y el tamano de la muestra (n),
y los titulos, ejes y leyendas estan en espanol. Los graficos por genero usan la
tabla puente titulo-genero (genero_puente.csv): un titulo cuenta una vez por cada genero.

Uso:
    python src/eda_charts.py          # regenera todos los PNG de images/
    # o, desde el notebook:  import eda_charts as ec; ec.g_top_generos(df, bridge)

Requiere haber ejecutado antes `python src/data_prep.py`.
"""

import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import FuncFormatter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from genre_map import SIN_GENERO  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "processed" / "streamview_content_clean.csv"
BRIDGE_FILE = ROOT / "data" / "processed" / "genero_puente.csv"
IMAGES = ROOT / "images"

RED = "#E50914"
BLACK = "#221F1F"
TIPO_ES = {"Movie": "Película", "TV Show": "Serie"}
PALETTE_TIPO = {"Película": RED, "Serie": BLACK}
SIN_PAIS = "Sin pais informado"

sns.set_theme(style="whitegrid", context="notebook")


# --------------------------------------------------------------------------- utilidades
def load_data():
    """Dataset limpio (con columna `tipo` en espanol) y tabla puente titulo-genero."""
    df = pd.read_csv(DATA_FILE)
    df["tipo"] = df["type"].map(TIPO_ES)
    bridge = pd.read_csv(BRIDGE_FILE)
    return df, bridge


def fmt(n) -> str:
    """Entero con separador de miles en formato chileno (31.991)."""
    return f"{int(n):,}".replace(",", ".")


def dec(x, n: int = 2) -> str:
    """Numero con coma decimal (6,62)."""
    return f"{x:.{n}f}".replace(".", ",")


def _miles(ax, eje: str = "y"):
    """Separador de miles (1.000) en los ticks del eje indicado."""
    formato = FuncFormatter(lambda v, _: fmt(v))
    (ax.yaxis if eje == "y" else ax.xaxis).set_major_formatter(formato)


def periodo(d: pd.DataFrame) -> str:
    return f"Estrenos {int(d['release_year'].min())}–{int(d['release_year'].max())}"


def titulo(base: str, d: pd.DataFrame, n=None, unidad: str = "títulos") -> str:
    """Titulo de dos lineas: nombre del grafico + periodo y tamano de la muestra."""
    n = len(d) if n is None else n
    return f"{base}\n{periodo(d)} · n = {fmt(n)} {unidad}"


def _guardar(fig, nombre: str, guardar: bool):
    fig.tight_layout()
    if guardar:
        IMAGES.mkdir(exist_ok=True)
        fig.savefig(IMAGES / nombre, dpi=150)
    return fig


def _genero_titulos(bridge: pd.DataFrame, df: pd.DataFrame, cols) -> pd.DataFrame:
    """Une la puente con columnas del dataset y excluye 'sin genero' (no entra a rankings)."""
    g = bridge.merge(df[["content_id", *cols]], on="content_id", how="left")
    return g[g["genero"] != SIN_GENERO]


def correlacion_rating_popularidad(df: pd.DataFrame):
    """(Pearson, Spearman) entre vote_average y popularity, sobre todos los titulos."""
    # Spearman = Pearson sobre los rangos (evita depender de scipy)
    return (df["vote_average"].corr(df["popularity"]),
            df["vote_average"].rank().corr(df["popularity"].rank()))


# --------------------------------------------------------------------------- graficos
def g_valores_faltantes(df, bridge=None, guardar=True):
    nulos = df.drop(columns=["tipo"], errors="ignore").isna().sum()
    pct = (nulos[nulos > 0] / len(df) * 100).round(1).sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(pct.index[::-1], pct.values[::-1], color=BLACK)
    ax.set_xlabel("% de filas con valor nulo")
    for i, v in enumerate(pct.values[::-1]):
        ax.text(v, i, f" {dec(v, 1)}%", va="center", fontsize=10)
    ax.set_xlim(0, 112)
    ax.set_title(titulo("Valores faltantes por columna", df))
    return _guardar(fig, "00_valores_faltantes.png", guardar)


def g_distribucion_votos(df, bridge=None, guardar=True):
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.histplot(df["vote_count"].clip(upper=df["vote_count"].quantile(0.95)), bins=40, color=RED, ax=ax)
    ax.axvline(20, color=BLACK, linestyle="--", linewidth=2, label="Umbral elegido: 20 votos")
    ax.set_xlabel("Cantidad de votos (recortado al percentil 95)")
    ax.set_ylabel("Cantidad de títulos")
    ax.set_title(titulo("Distribución de la cantidad de votos", df))
    _miles(ax, "x")
    _miles(ax, "y")
    ax.legend()
    return _guardar(fig, "10_distribucion_votos.png", guardar)


def g_distribucion_rating(df, bridge=None, guardar=True):
    sub = df[df["rating_confiable"]]
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.histplot(sub["vote_average"], bins=40, kde=True, color=RED, ax=ax)
    ax.axvline(sub["vote_average"].mean(), color=BLACK, linestyle="--",
               label=f"Media: {dec(sub['vote_average'].mean())}")
    ax.axvline(sub["vote_average"].median(), color="#666666", linestyle=":",
               label=f"Mediana: {dec(sub['vote_average'].median())}")
    ax.set_xlabel("Rating promedio (escala 0-10)")
    ax.set_ylabel("Cantidad de títulos")
    ax.set_title(titulo("Distribución del rating (títulos con ≥ 20 votos)", sub))
    _miles(ax, "y")
    ax.legend()
    return _guardar(fig, "11_distribucion_rating.png", guardar)


def g_mix_tipo(df, bridge=None, guardar=True):
    counts = df["tipo"].value_counts()
    fig, ax = plt.subplots(figsize=(6, 6))
    _, _, porcentajes = ax.pie(counts.values, labels=counts.index, autopct=lambda p: f"{dec(p, 1)}%",
                               colors=[PALETTE_TIPO[t] for t in counts.index], startangle=90,
                               textprops={"fontsize": 12})
    for texto in porcentajes:  # legibles sobre el rojo y el negro
        texto.set_color("white")
        texto.set_fontweight("bold")
    ax.set_title(titulo("Composición del catálogo por tipo de contenido", df))
    return _guardar(fig, "07_mix_tipo_contenido.png", guardar)


def g_volumen_anio(df, bridge=None, guardar=True):
    d = df[df["release_year"].between(2010, 2025)]
    vol = d.groupby(["release_year", "tipo"]).size().unstack()
    fig, ax = plt.subplots(figsize=(11, 5))
    vol.plot(kind="bar", color=[PALETTE_TIPO[c] for c in vol.columns], ax=ax)
    ax.set_title(titulo("Cantidad de títulos por año de estreno y tipo", d))
    ax.set_ylabel("Cantidad de títulos")
    ax.set_xlabel("Año de estreno")
    _miles(ax, "y")
    ax.legend(title="Tipo", loc="upper left", bbox_to_anchor=(1.01, 1))
    return _guardar(fig, "00b_volumen_por_anio.png", guardar)


def g_evolucion_rating(df, bridge=None, guardar=True):
    d = df[df["rating_confiable"]]
    evol = d.groupby(["release_year", "tipo"])["vote_average"].mean().unstack()
    fig, ax = plt.subplots(figsize=(11, 5))
    evol.plot(marker="o", color=[PALETTE_TIPO[c] for c in evol.columns], ax=ax)
    ax.set_title(titulo("Evolución del rating promedio por año de estreno (≥ 20 votos)", d))
    ax.set_ylabel("Rating promedio (escala 0-10)")
    ax.set_xlabel("Año de estreno")
    ax.legend(title="Tipo")
    return _guardar(fig, "01_evolucion_catalogo.png", guardar)


def g_rating_por_tipo(df, bridge=None, guardar=True):
    d = df[df["rating_confiable"]]
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.boxplot(data=d, x="tipo", y="vote_average", hue="tipo", palette=PALETTE_TIPO,
                legend=False, ax=ax)
    ax.set_title(titulo("Distribución del rating por tipo de contenido (≥ 20 votos)", d))
    ax.set_xlabel("")
    ax.set_ylabel("Rating promedio (escala 0-10)")
    return _guardar(fig, "12_rating_por_tipo.png", guardar)


def g_top_generos(df, bridge, guardar=True):
    g = bridge[bridge["genero"] != SIN_GENERO]
    top = g["genero"].value_counts().head(10).sort_values()
    n_titulos = g["content_id"].nunique()
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(top.index, top.values, color=RED)
    for i, v in enumerate(top.values):
        ax.text(v, i, f" {fmt(v)}", va="center")
    ax.set_title(titulo("Top 10 géneros por cantidad de títulos", df, n=n_titulos,
                        unidad="títulos con género"))
    ax.set_xlabel("Cantidad de títulos (un título cuenta una vez por cada género)")
    _miles(ax, "x")
    ax.margins(x=0.1)
    return _guardar(fig, "02_top_generos.png", guardar)


def g_rating_por_genero(df, bridge, guardar=True):
    g = _genero_titulos(bridge, df, ["vote_average", "rating_confiable", "tipo"])
    top10 = g["genero"].value_counts().head(10).index
    sub = g[g["genero"].isin(top10) & g["rating_confiable"]]
    order = sub.groupby("genero")["vote_average"].mean().sort_values(ascending=False).index
    fig, ax = plt.subplots(figsize=(11, 6))
    sns.barplot(data=sub, x="genero", y="vote_average", order=order, hue="tipo",
                palette=PALETTE_TIPO, errorbar=None, ax=ax)
    ax.set_title(titulo("Rating promedio por género (10 más frecuentes, ≥ 20 votos)", df,
                        n=sub["content_id"].nunique()))
    ax.set_xlabel("Género")
    ax.set_ylabel("Rating promedio (escala 0-10)")
    ax.tick_params(axis="x", rotation=35)
    ax.legend(title="Tipo", loc="upper left", bbox_to_anchor=(1.01, 1))
    return _guardar(fig, "03_rating_por_genero.png", guardar)


def g_correlacion(df, bridge=None, guardar=True):
    cols = {"vote_average": "rating", "popularity": "popularidad", "vote_count": "votos",
            "budget": "presupuesto", "revenue": "ingresos", "roi": "ROI"}
    corr = df[list(cols)].rename(columns=cols).corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(7, 6))
    etiquetas = corr.apply(lambda col: col.map(dec))  # coma decimal
    sns.heatmap(corr, annot=etiquetas, fmt="", cmap="RdBu_r", center=0, vmin=-1, vmax=1, ax=ax)
    ax.set_title(titulo("Correlación de Pearson entre variables numéricas", df)
                 + "\n(presupuesto, ingresos y ROI: solo películas con datos válidos)")
    return _guardar(fig, "08_correlacion_variables.png", guardar)


def g_popularidad_vs_rating(df, bridge=None, guardar=True):
    pearson, spearman = correlacion_rating_popularidad(df)
    sub = df[df["rating_confiable"] & (df["popularity"] < df["popularity"].quantile(0.98))]
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.scatterplot(data=sub, x="vote_average", y="popularity", hue="tipo",
                    palette=PALETTE_TIPO, alpha=0.3, s=20, ax=ax)
    ax.set_title(titulo("Relación entre rating y popularidad (≥ 20 votos, sin el 2 % más popular)", sub)
                 + f"\nCorrelación sobre todo el catálogo: Spearman {dec(spearman)} · Pearson {dec(pearson)}")
    ax.set_xlabel("Rating promedio (escala 0-10)")
    ax.set_ylabel("Popularidad (índice relativo)")
    ax.legend(title="Tipo")
    return _guardar(fig, "04_popularidad_vs_rating.png", guardar)


def g_top_paises(df, bridge=None, guardar=True):
    d = df[df["main_country"] != SIN_PAIS]
    top = d["main_country"].value_counts().head(10).sort_values()
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(top.index, top.values, color=BLACK)
    for i, v in enumerate(top.values):
        ax.text(v, i, f" {fmt(v)}", va="center")
    ax.set_title(titulo("Top 10 países con más títulos (país principal)", d, unidad="títulos con país"))
    ax.set_xlabel("Cantidad de títulos")
    _miles(ax, "x")
    ax.margins(x=0.1)
    return _guardar(fig, "05_top_paises.png", guardar)


def g_presupuesto_ingresos(df, bridge=None, guardar=True):
    fin = df[df["financiero_valido"]]
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(fin["budget"], fin["revenue"], alpha=0.25, s=15, color=RED)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Presupuesto (USD, escala logarítmica)")
    ax.set_ylabel("Ingresos (USD, escala logarítmica)")
    ax.set_title(titulo("Presupuesto vs. ingresos (películas con presupuesto ≥ 1 M USD)", fin,
                        unidad="películas"))
    return _guardar(fig, "09_presupuesto_vs_ingresos.png", guardar)


def g_roi_genero(df, bridge, guardar=True):
    fin = df[df["financiero_valido"]]
    g = _genero_titulos(bridge, fin, ["roi"])
    g = g[g["roi"] <= g["roi"].quantile(0.95)]
    # 12 generos con mas peliculas validas (incluye Animation y Horror, los de mayor ROI mediano)
    top = g["genero"].value_counts().head(12).index
    d = g[g["genero"].isin(top)]
    order = d.groupby("genero")["roi"].median().sort_values(ascending=False).index
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.boxplot(data=d, x="genero", y="roi", order=order, color=RED, fliersize=2, ax=ax)
    ax.axhline(1, color=BLACK, linestyle="--", linewidth=1, label="ROI = 1 (recupera lo invertido)")
    ax.set_title(titulo("ROI por género, 12 géneros con más películas (extremos acotados al percentil 95)",
                        fin, unidad="películas"))
    ax.set_xlabel("Género (ordenado por mediana de ROI)")
    ax.set_ylabel("ROI (ingresos / presupuesto, veces)")
    ax.tick_params(axis="x", rotation=35)
    ax.legend(loc="upper right", framealpha=0.95)
    return _guardar(fig, "06_roi_peliculas_genero.png", guardar)


def _peor_razon(fila, lado):
    s = sum(fila)
    return max(max(lado * lado * a / (s * s), s * s / (lado * lado * a)) for a in fila)


def _treemap(valores, x, y, w, h):
    """Rectangulos (x, y, ancho, alto) de un treemap 'squarified' para valores ordenados de mayor a menor."""
    total = sum(valores)
    areas = [v / total * w * h for v in valores]
    rects, i = [], 0
    while i < len(areas):
        lado = min(w, h)
        fila, j = [areas[i]], i + 1
        while j < len(areas) and _peor_razon(fila + [areas[j]], lado) <= _peor_razon(fila, lado):
            fila.append(areas[j])
            j += 1
        s = sum(fila)
        if w >= h:  # la fila ocupa una columna a la izquierda
            ancho, yy = s / h, y
            for a in fila:
                rects.append((x, yy, ancho, a / ancho))
                yy += a / ancho
            x, w = x + ancho, w - ancho
        else:  # la fila ocupa una franja arriba
            alto, xx = s / w, x
            for a in fila:
                rects.append((xx, y, a / alto, alto))
                xx += a / alto
            y, h = y + alto, h - alto
        i = j
    return rects


def g_treemap_generos(df, bridge, guardar=True):
    g = bridge[bridge["genero"] != SIN_GENERO]
    conteo = g["genero"].value_counts()
    principales = conteo.head(14)
    otros = conteo.iloc[14:].sum()
    etiquetas = list(principales.index) + [f"Otros ({len(conteo) - 14} géneros)"]
    valores = list(principales.values) + [otros]
    rects = _treemap(valores, 0, 0, 100, 60)
    fig, ax = plt.subplots(figsize=(11, 6.4))
    cmap = plt.get_cmap("Reds")
    maximo = max(valores)
    for (x, y, w, h), nombre, v in zip(rects, etiquetas, valores):
        gris = nombre.startswith("Otros")
        color = "#8C8C8C" if gris else cmap(0.35 + 0.6 * v / maximo)
        ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=color, edgecolor="white", linewidth=2))
        ax.text(x + w / 2, y + h / 2, f"{nombre}\n{fmt(v)}", ha="center", va="center", color="white",
                fontsize=10 if w * h > 120 else 8, fontweight="bold")
    ax.set_xlim(0, 100)
    ax.set_ylim(60, 0)
    ax.axis("off")
    ax.set_title(titulo("Composición del catálogo por género (el área indica la cantidad de títulos)", df,
                        n=g["content_id"].nunique(), unidad="títulos con género"))
    return _guardar(fig, "13_treemap_generos.png", guardar)


def g_area_popularidad(df, bridge=None, guardar=True):
    pop = df.groupby(["release_year", "tipo"])["popularity"].mean().unstack()
    fig, ax = plt.subplots(figsize=(11, 5))
    for tipo in pop.columns:
        ax.fill_between(pop.index, pop[tipo], alpha=0.3, color=PALETTE_TIPO[tipo], label=tipo)
        ax.plot(pop.index, pop[tipo], color=PALETTE_TIPO[tipo], linewidth=2)
    ax.set_xlim(pop.index.min(), pop.index.max())
    ax.set_title(titulo("Popularidad promedio por año de estreno y tipo", df))
    ax.set_xlabel("Año de estreno")
    ax.set_ylabel("Popularidad promedio (índice relativo)")
    ax.legend(title="Tipo")
    return _guardar(fig, "14_area_popularidad_anio.png", guardar)


def g_directores_actores(df, bridge=None, guardar=True):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6))
    for ax, columna, nombre, color in [(ax1, "director", "directores", BLACK), (ax2, "cast", "actores", RED)]:
        d = df.dropna(subset=[columna])
        top = d[columna].str.split(",").explode().str.strip().value_counts().head(10).sort_values()
        ax.barh(top.index, top.values, color=color)
        for i, v in enumerate(top.values):
            ax.text(v, i, f" {fmt(v)}", va="center")
        ax.set_title(titulo(f"Top 10 {nombre} por cantidad de títulos", d, unidad=f"títulos con {nombre[:-2]}"
                            if nombre == "actores" else "títulos con director"))
        ax.set_xlabel("Cantidad de títulos")
        ax.margins(x=0.12)
    return _guardar(fig, "15_directores_actores.png", guardar)


TODOS = [g_valores_faltantes, g_distribucion_votos, g_distribucion_rating, g_mix_tipo,
         g_volumen_anio, g_evolucion_rating, g_rating_por_tipo, g_top_generos,
         g_rating_por_genero, g_correlacion, g_popularidad_vs_rating, g_top_paises,
         g_presupuesto_ingresos, g_roi_genero, g_treemap_generos, g_area_popularidad, g_directores_actores]


def main():
    matplotlib.use("Agg")
    df, bridge = load_data()
    for fn in TODOS:
        fig = fn(df, bridge, guardar=True)
        plt.close(fig)
        print(f"OK  {fn.__name__}")
    print(f"{len(TODOS)} graficos exportados a {IMAGES}")


if __name__ == "__main__":
    main()
