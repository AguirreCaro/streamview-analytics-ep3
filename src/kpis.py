"""
StreamView Analytics - EP3 Visualizacion de Datos
Calculo de los KPIs definidos en docs/ficha_kpis.md.

`build_kpis(df, bridge)` devuelve una tabla en formato largo (una fila por valor):

    kpi_id, kpi, tipo_contenido, dimension, posicion, valor, unidad

- tipo_contenido: "Todos", "Movie" o "TV Show" (los mismos valores que el filtro de tipo
  del dashboard), para poder comparar cada tarjeta de Power BI con el filtro aplicado.
- dimension / posicion: vacios en los KPIs de un solo valor; en los rankings y series
  traen la etiqueta (genero, pais, anio...) y el lugar en el ranking.
- Los KPIs financieros solo existen para peliculas: con el filtro "TV Show" valen
  "No aplica"; con "Todos" coinciden con "Movie" (las series no aportan datos).
"""

import pandas as pd

from genre_map import SIN_GENERO

SIN_PAIS = "Sin pais informado"
MIN_PELICULAS_GENERO_ROI = 30  # generos con menos peliculas validas tienen ROI poco estable
MIN_TITULOS_PROMEDIO = 100  # grupos (genero, pais, idioma) con menos titulos no entran a rankings de promedios
TIPOS = ["Todos", "Movie", "TV Show"]
NO_APLICA = "No aplica"


def _subset(df: pd.DataFrame, tipo: str) -> pd.DataFrame:
    return df if tipo == "Todos" else df[df["type"] == tipo]


def build_kpis(df: pd.DataFrame, bridge: pd.DataFrame) -> pd.DataFrame:
    rows = []

    def add(kpi_id, kpi, tipo, valor, unidad, dimension="", posicion=""):
        rows.append({"kpi_id": kpi_id, "kpi": kpi, "tipo_contenido": tipo,
                     "dimension": dimension, "posicion": posicion, "valor": valor, "unidad": unidad})

    def add_ranking(kpi_id, kpi, tipo, serie: pd.Series, unidad):
        for pos, (etiqueta, valor) in enumerate(serie.items(), start=1):
            add(kpi_id, kpi, tipo, valor, unidad, dimension=etiqueta, posicion=pos)

    # tabla titulo-genero con las metricas necesarias (excluye "sin genero" de los rankings)
    gen = bridge.merge(df[["content_id", "vote_average", "rating_confiable", "popularity", "roi",
                           "financiero_valido"]], on="content_id", how="left")
    gen = gen[gen["genero"] != SIN_GENERO]
    total_catalogo = len(df)

    for tipo in TIPOS:
        d = _subset(df, tipo)
        g = gen if tipo == "Todos" else gen[gen["type"] == tipo]
        conf = d[d["rating_confiable"]]
        con_pais = d[d["main_country"] != SIN_PAIS]
        con_idioma = d["language"].dropna()

        # --- Catalogo ---
        add("K01", "Total de titulos", tipo, len(d), "titulos")
        add("K02", "Participacion en el catalogo", tipo, round(len(d) / total_catalogo * 100, 1), "% del catalogo")
        add("K03", "Rating promedio (>=20 votos)", tipo, round(conf["vote_average"].mean(), 2), "escala 0-10")
        add("K04", "Popularidad promedio", tipo, round(d["popularity"].mean(), 2), "indice relativo")
        add("K05", "Paises distintos", tipo, con_pais["main_country"].nunique(), "paises")
        add("K06", "Idiomas distintos", tipo, con_idioma.nunique(), "idiomas")

        # --- Generos (sobre la tabla puente) ---
        conteo_gen = g["genero"].value_counts()
        top10_gen = conteo_gen.head(10)
        add("K07", "Genero con mas titulos", tipo, conteo_gen.idxmax(), "genero")
        rating_gen = (g[g["rating_confiable"] & g["genero"].isin(top10_gen.index)]
                      .groupby("genero")["vote_average"].mean())
        add("K08", "Genero con mejor rating promedio (entre los 10 mas frecuentes)", tipo,
            rating_gen.idxmax(), "genero")
        add_ranking("K11", "Top 10 generos por titulos", tipo, top10_gen, "titulos")

        # --- Paises e idiomas ---
        conteo_pais = con_pais["main_country"].value_counts()
        conteo_idioma = con_idioma.value_counts()
        add("K09", "Pais con mas titulos", tipo, conteo_pais.idxmax(), "pais")
        add("K10", "Idioma con mas titulos", tipo, conteo_idioma.idxmax(), "idioma")
        add_ranking("K12", "Top 10 paises por titulos", tipo, conteo_pais.head(10), "titulos")
        add_ranking("K13", "Top 10 idiomas por titulos", tipo, conteo_idioma.head(10), "titulos")

        # --- Titulos destacados y evolucion ---
        top_pop = d.nlargest(10, "popularity").set_index("title")["popularity"].round(2)
        add_ranking("K14", "Top 10 titulos por popularidad", tipo, top_pop, "indice relativo")
        top_rat = (conf.sort_values(["vote_average", "vote_count"], ascending=False)
                   .head(10).set_index("title")["vote_average"])
        add_ranking("K15", "Top 10 titulos por rating (>=20 votos)", tipo, top_rat, "escala 0-10")
        por_anio = d["year_added"].dropna().astype(int).value_counts().sort_index()
        for anio, n in por_anio.items():
            add("K16", "Incorporaciones por anio", tipo, int(n), "titulos", dimension=anio)

        estrenos = d["release_year"].dropna().astype(int).value_counts().sort_index()
        for anio, n in estrenos.items():
            add("K24", "Estrenos por anio", tipo, int(n), "titulos", dimension=anio)

        # --- Popularidad y valoracion por genero, pais e idioma (grupos con >= 100 titulos) ---
        add("K17", "Cantidad de generos", tipo, g["genero"].nunique(), "generos")

        def promedio_top(tabla, grupo, columna, redondeo=2):
            s = tabla.groupby(grupo)[columna].agg(["mean", "size"])
            return s[s["size"] >= MIN_TITULOS_PROMEDIO]["mean"].sort_values(ascending=False).head(10).round(redondeo)

        add_ranking("K18", f"Top 10 generos por popularidad promedio (>={MIN_TITULOS_PROMEDIO} titulos)", tipo,
                    promedio_top(g, "genero", "popularity"), "indice relativo")
        add_ranking("K19", f"Top 10 paises por popularidad promedio (>={MIN_TITULOS_PROMEDIO} titulos)", tipo,
                    promedio_top(con_pais, "main_country", "popularity"), "indice relativo")
        add_ranking("K20", f"Top 10 idiomas por popularidad promedio (>={MIN_TITULOS_PROMEDIO} titulos)", tipo,
                    promedio_top(d.dropna(subset=["language"]), "language", "popularity"), "indice relativo")
        add_ranking("K21", f"Top 10 generos por rating promedio (>={MIN_TITULOS_PROMEDIO} titulos con >=20 votos)",
                    tipo, promedio_top(g[g["rating_confiable"]], "genero", "vote_average"), "escala 0-10")
        add_ranking("K22", f"Top 10 paises por rating promedio (>={MIN_TITULOS_PROMEDIO} titulos con >=20 votos)",
                    tipo, promedio_top(con_pais[con_pais["rating_confiable"]], "main_country", "vote_average"),
                    "escala 0-10")
        mas_votos = d.nlargest(10, "vote_count").set_index("title")["vote_count"].astype(int)
        add_ranking("K23", "Top 10 titulos con mas votos", tipo, mas_votos, "votos")

        # --- Produccion: directores y actores (los campos traen listas separadas por coma) ---
        directores = d["director"].dropna().str.split(",").explode().str.strip().value_counts().head(10)
        actores = d["cast"].dropna().str.split(",").explode().str.strip().value_counts().head(10)
        add_ranking("K25", "Top 10 directores por titulos", tipo, directores, "titulos")
        add_ranking("K26", "Top 10 actores por titulos", tipo, actores, "titulos")

        # --- Financieros (solo peliculas con presupuesto >= 1M USD e ingresos > 0) ---
        if tipo == "TV Show":
            for kid, nombre, unidad in [
                ("F01", "Peliculas con datos financieros validos", "peliculas"),
                ("F02", "Ingreso total (peliculas validas)", "USD"),
                ("F03", "Presupuesto total (peliculas validas)", "USD"),
                ("F04", "ROI mediano (ingresos / presupuesto)", "razon (x)"),
                ("F05", "Genero con mejor ROI mediano", "genero"),
                ("F07", "Presupuesto promedio (peliculas validas)", "USD"),
                ("F08", "Top 10 peliculas por ingresos", "USD"),
                ("F09", "Top 10 peliculas por ROI", "razon (x)"),
                ("F10", "Top 10 peliculas por ROI con presupuesto reducido", "razon (x)"),
            ]:
                add(kid, nombre, tipo, NO_APLICA, unidad)
            continue

        fin = d[d["financiero_valido"]]
        add("F01", "Peliculas con datos financieros validos", tipo, len(fin), "peliculas")
        add("F02", "Ingreso total (peliculas validas)", tipo, int(fin["revenue"].sum()), "USD")
        add("F03", "Presupuesto total (peliculas validas)", tipo, int(fin["budget"].sum()), "USD")
        add("F04", "ROI mediano (ingresos / presupuesto)", tipo, round(fin["roi"].median(), 2), "razon (x)")
        add("F07", "Presupuesto promedio (peliculas validas)", tipo, int(round(fin["budget"].mean())), "USD")
        add_ranking("F08", "Top 10 peliculas por ingresos", tipo,
                    fin.nlargest(10, "revenue").set_index("title")["revenue"].astype(int), "USD")
        add_ranking("F09", "Top 10 peliculas por ROI", tipo,
                    fin.nlargest(10, "roi").set_index("title")["roi"].round(2), "razon (x)")
        # exitosas con presupuesto reducido: presupuesto <= mediana del presupuesto de las peliculas validas
        bajo = fin[fin["budget"] <= fin["budget"].median()]
        add_ranking("F10", "Top 10 peliculas por ROI con presupuesto reducido", tipo,
                    bajo.nlargest(10, "roi").set_index("title")["roi"].round(2), "razon (x)")

        gf = g[g["financiero_valido"] == True]  # noqa: E712 (columna booleana con NaN tras el merge)
        n_por_gen = gf["genero"].value_counts()
        relevantes = n_por_gen[n_por_gen >= MIN_PELICULAS_GENERO_ROI].index
        roi_gen = (gf[gf["genero"].isin(relevantes)].groupby("genero")["roi"].median()
                   .sort_values(ascending=False))
        add("F05", "Genero con mejor ROI mediano", tipo, roi_gen.idxmax(), "genero")
        add_ranking("F06", f"ROI mediano por genero (>={MIN_PELICULAS_GENERO_ROI} peliculas validas)",
                    tipo, roi_gen.round(2), "razon (x)")

    return pd.DataFrame(rows)
