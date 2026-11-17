"""
StreamView Analytics - EP5 Visualizacion de Datos
Calculo de los KPIs definidos en docs/ficha_kpis.md.

`build_kpis(df, bridge)` devuelve una tabla en formato largo (una fila por valor):

    kpi_id, kpi, tipo_contenido, dimension, posicion, valor, unidad

- tipo_contenido: "Todos", "Película" o "Serie" (los mismos valores que el filtro de tipo
  del dashboard), para poder comparar cada tarjeta de Power BI con el filtro aplicado.
- dimension / posicion: vacios en los KPIs de un solo valor; en los rankings y series
  traen la etiqueta (genero, pais, anio...) y el lugar en el ranking.
- Los KPIs financieros solo existen para películas: con el filtro "Serie" valen
  "No aplica"; con "Todos" coinciden con "Película" (las series no aportan datos).
"""

import pandas as pd

from traducciones import SIN_GENERO, SIN_PAIS

MIN_PELICULAS_GENERO_ROI = 30  # géneros con menos películas válidas tienen ROI poco estable
MIN_TITULOS_PROMEDIO = 100  # grupos (genero, pais, idioma) con menos títulos no entran a rankings de promedios
TIPOS = ["Todos", "Película", "Serie"]
NO_APLICA = "No aplica"


def _subset(df: pd.DataFrame, tipo: str) -> pd.DataFrame:
    return df if tipo == "Todos" else df[df["tipo"] == tipo]


def build_kpis(df: pd.DataFrame, bridge: pd.DataFrame) -> pd.DataFrame:
    rows = []

    def add(kpi_id, kpi, tipo, valor, unidad, dimension="", posicion=""):
        rows.append({"kpi_id": kpi_id, "kpi": kpi, "tipo_contenido": tipo,
                     "dimension": dimension, "posicion": posicion, "valor": valor, "unidad": unidad})

    def add_ranking(kpi_id, kpi, tipo, serie: pd.Series, unidad):
        for pos, (etiqueta, valor) in enumerate(serie.items(), start=1):
            add(kpi_id, kpi, tipo, valor, unidad, dimension=etiqueta, posicion=pos)

    # tabla titulo-genero con las metricas necesarias (excluye "sin genero" de los rankings)
    gen = bridge.merge(df[["id_contenido", "rating", "rating_confiable", "popularidad", "roi",
                           "financiero_valido"]], on="id_contenido", how="left")
    gen = gen[gen["genero"] != SIN_GENERO]
    total_catalogo = len(df)

    for tipo in TIPOS:
        d = _subset(df, tipo)
        g = gen if tipo == "Todos" else gen[gen["tipo"] == tipo]
        conf = d[d["rating_confiable"]]
        con_pais = d[d["pais_principal"] != SIN_PAIS]
        con_idioma = d["idioma"].dropna()

        # --- Catalogo ---
        add("K01", "Total de títulos", tipo, len(d), "títulos")
        add("K02", "Participación en el catalogo", tipo, round(len(d) / total_catalogo * 100, 1), "% del catalogo")
        add("K03", "Rating promedio (≥ 20 votos)", tipo, round(conf["rating"].mean(), 2), "escala 0-10")
        add("K04", "Popularidad promedio", tipo, round(d["popularidad"].mean(), 2), "índice relativo")
        add("K05", "Paises distintos", tipo, con_pais["pais_principal"].nunique(), "países")
        add("K06", "Idiomas distintos", tipo, con_idioma.nunique(), "idiomas")

        # --- Generos (sobre la tabla puente) ---
        conteo_gen = g["genero"].value_counts()
        top10_gen = conteo_gen.head(10)
        add("K07", "Género con más títulos", tipo, conteo_gen.idxmax(), "género")
        rating_gen = (g[g["rating_confiable"] & g["genero"].isin(top10_gen.index)]
                      .groupby("genero")["rating"].mean())
        add("K08", "Género con mejor rating promedio (entre los 10 más frecuentes)", tipo,
            rating_gen.idxmax(), "género")
        add_ranking("K11", "Top 10 géneros por títulos", tipo, top10_gen, "títulos")

        # --- Paises e idiomas ---
        conteo_pais = con_pais["pais_principal"].value_counts()
        conteo_idioma = con_idioma.value_counts()
        add("K09", "País con más títulos", tipo, conteo_pais.idxmax(), "país")
        add("K10", "Idioma con más títulos", tipo, conteo_idioma.idxmax(), "idioma")
        add_ranking("K12", "Top 10 países por títulos", tipo, conteo_pais.head(10), "títulos")
        add_ranking("K13", "Top 10 idiomas por títulos", tipo, conteo_idioma.head(10), "títulos")

        # --- Titulos destacados y evolucion ---
        top_pop = d.nlargest(10, "popularidad").set_index("titulo")["popularidad"].round(2)
        add_ranking("K14", "Top 10 títulos por popularidad", tipo, top_pop, "índice relativo")
        top_rat = (conf.sort_values(["rating", "votos"], ascending=False)
                   .head(10).set_index("titulo")["rating"])
        add_ranking("K15", "Top 10 títulos por rating (≥ 20 votos)", tipo, top_rat, "escala 0-10")
        por_anio = d["anio_incorporacion"].dropna().astype(int).value_counts().sort_index()
        for anio, n in por_anio.items():
            add("K16", "Incorporaciones por año", tipo, int(n), "títulos", dimension=anio)

        estrenos = d["anio_estreno"].dropna().astype(int).value_counts().sort_index()
        for anio, n in estrenos.items():
            add("K24", "Estrenos por año", tipo, int(n), "títulos", dimension=anio)

        # --- Popularidad y valoracion por genero, pais e idioma (grupos con >= 100 títulos) ---
        add("K17", "Cantidad de géneros", tipo, g["genero"].nunique(), "géneros")

        def promedio_top(tabla, grupo, columna, redondeo=2):
            s = tabla.groupby(grupo)[columna].agg(["mean", "size"])
            return s[s["size"] >= MIN_TITULOS_PROMEDIO]["mean"].sort_values(ascending=False).head(10).round(redondeo)

        add_ranking("K18", f"Top 10 géneros por popularidad promedio (≥ {MIN_TITULOS_PROMEDIO} títulos)", tipo,
                    promedio_top(g, "genero", "popularidad"), "índice relativo")
        add_ranking("K19", f"Top 10 países por popularidad promedio (≥ {MIN_TITULOS_PROMEDIO} títulos)", tipo,
                    promedio_top(con_pais, "pais_principal", "popularidad"), "índice relativo")
        add_ranking("K20", f"Top 10 idiomas por popularidad promedio (≥ {MIN_TITULOS_PROMEDIO} títulos)", tipo,
                    promedio_top(d.dropna(subset=["idioma"]), "idioma", "popularidad"), "índice relativo")
        add_ranking("K21", f"Top 10 géneros por rating promedio (≥ {MIN_TITULOS_PROMEDIO} títulos con ≥ 20 votos)",
                    tipo, promedio_top(g[g["rating_confiable"]], "genero", "rating"), "escala 0-10")
        add_ranking("K22", f"Top 10 países por rating promedio (≥ {MIN_TITULOS_PROMEDIO} títulos con ≥ 20 votos)",
                    tipo, promedio_top(con_pais[con_pais["rating_confiable"]], "pais_principal", "rating"),
                    "escala 0-10")
        mas_votos = d.nlargest(10, "votos").set_index("titulo")["votos"].astype(int)
        add_ranking("K23", "Top 10 títulos con más votos", tipo, mas_votos, "votos")

        # --- Produccion: directores y actores (los campos traen listas separadas por coma) ---
        directores = d["director"].dropna().str.split(",").explode().str.strip().value_counts().head(10)
        actores = d["reparto"].dropna().str.split(",").explode().str.strip().value_counts().head(10)
        add_ranking("K25", "Top 10 directores por títulos", tipo, directores, "títulos")
        add_ranking("K26", "Top 10 actores por títulos", tipo, actores, "títulos")

        # --- Financieros (solo películas con presupuesto >= 1M USD e ingresos > 0) ---
        if tipo == "Serie":
            for kid, nombre, unidad in [
                ("F01", "Películas con datos financieros válidos", "películas"),
                ("F02", "Ingreso total (películas válidas)", "USD"),
                ("F03", "Presupuesto total (películas válidas)", "USD"),
                ("F04", "ROI mediano (ingresos / presupuesto)", "razón (x)"),
                ("F05", "Género con mejor ROI mediano", "género"),
                ("F07", "Presupuesto promedio (películas válidas)", "USD"),
                ("F08", "Top 10 películas por ingresos", "USD"),
                ("F09", "Top 10 películas por ROI", "razón (x)"),
                ("F10", "Top 10 películas por ROI con presupuesto reducido", "razón (x)"),
            ]:
                add(kid, nombre, tipo, NO_APLICA, unidad)
            continue

        fin = d[d["financiero_valido"]]
        add("F01", "Películas con datos financieros válidos", tipo, len(fin), "películas")
        add("F02", "Ingreso total (películas válidas)", tipo, int(fin["ingresos_usd"].sum()), "USD")
        add("F03", "Presupuesto total (películas válidas)", tipo, int(fin["presupuesto_usd"].sum()), "USD")
        add("F04", "ROI mediano (ingresos / presupuesto)", tipo, round(fin["roi"].median(), 2), "razón (x)")
        add("F07", "Presupuesto promedio (películas válidas)", tipo, int(round(fin["presupuesto_usd"].mean())), "USD")
        add_ranking("F08", "Top 10 películas por ingresos", tipo,
                    fin.nlargest(10, "ingresos_usd").set_index("titulo")["ingresos_usd"].astype(int), "USD")
        add_ranking("F09", "Top 10 películas por ROI", tipo,
                    fin.nlargest(10, "roi").set_index("titulo")["roi"].round(2), "razón (x)")
        # exitosas con presupuesto reducido: presupuesto <= mediana del presupuesto de las películas válidas
        bajo = fin[fin["presupuesto_usd"] <= fin["presupuesto_usd"].median()]
        add_ranking("F10", "Top 10 películas por ROI con presupuesto reducido", tipo,
                    bajo.nlargest(10, "roi").set_index("titulo")["roi"].round(2), "razón (x)")

        gf = g[g["financiero_valido"] == True]  # noqa: E712 (columna booleana con NaN tras el merge)
        n_por_gen = gf["genero"].value_counts()
        relevantes = n_por_gen[n_por_gen >= MIN_PELICULAS_GENERO_ROI].index
        roi_gen = (gf[gf["genero"].isin(relevantes)].groupby("genero")["roi"].median()
                   .sort_values(ascending=False))
        add("F05", "Género con mejor ROI mediano", tipo, roi_gen.idxmax(), "género")
        add_ranking("F06", f"ROI mediano por genero (≥ {MIN_PELICULAS_GENERO_ROI} películas válidas)",
                    tipo, roi_gen.round(2), "razón (x)")

    return pd.DataFrame(rows)
