"""
StreamView Analytics - EP5 Visualizacion de Datos
Hipotesis del EDA y como se validaron (ciclo Visual Analytics: patron -> hipotesis -> validacion).

`tabla_hipotesis(df, bridge)` recalcula cada cifra con los datos procesados, de modo que el
texto no se desactualiza: si la evidencia deja de respaldar una hipotesis, el veredicto pasa a
"Revisar" en vez de repetir una conclusion vieja. Las pruebas de permutacion y los intervalos
bootstrap usan semilla fija (resultados reproducibles).

Uso:
    python src/hipotesis.py                    # imprime la tabla en Markdown
    # o, desde el notebook:  import hipotesis as hp; hp.tabla_hipotesis(df, bridge)

Requiere haber ejecutado antes `python src/data_prep.py`.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from traducciones import SIN_GENERO  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SEMILLA = 42
UMBRALES_VOTOS = [1, 10, 20, 50, 100]
MARGEN_ROI = 0.10  # separacion minima entre intervalos para considerarlos distintos con claridad
SE_SOSTIENE = "Se sostiene"
REVISAR = "Revisar: la evidencia cambió"


# --------------------------------------------------------------------------- utilidades
def _fmt(n) -> str:
    return f"{int(round(n)):,}".replace(",", ".")


def _dec(x, n: int = 2) -> str:
    return f"{x:.{n}f}".replace(".", ",")


def _rango(minimo, maximo) -> str:
    """'1.000' si no hay variacion; '991–1.000' en otro caso."""
    return _fmt(minimo) if minimo == maximo else f"{_fmt(minimo)}–{_fmt(maximo)}"


def _lista(items) -> str:
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " y " + items[-1]


def _rho_permutacion(x: pd.Series, y: pd.Series, n: int = 10_000):
    """Spearman (Pearson sobre rangos) y p-valor de permutacion de dos colas."""
    rx, ry = x.rank().to_numpy(), y.rank().to_numpy()
    rho = float(np.corrcoef(rx, ry)[0, 1])
    rng = np.random.default_rng(SEMILLA)
    perm = np.array([np.corrcoef(rx, rng.permutation(ry))[0, 1] for _ in range(n)])
    return rho, float((np.abs(perm) >= abs(rho)).mean())


def _ic_mediana(valores, n: int = 5_000):
    """Mediana e intervalo bootstrap del 95 %."""
    v = np.asarray(valores, dtype=float)
    rng = np.random.default_rng(SEMILLA)
    medianas = np.median(rng.choice(v, size=(n, len(v))), axis=1)
    return float(np.median(v)), float(np.percentile(medianas, 2.5)), float(np.percentile(medianas, 97.5))


def _tabla_genero(df: pd.DataFrame, bridge: pd.DataFrame) -> pd.DataFrame:
    g = bridge[bridge["genero"] != SIN_GENERO]
    return g.merge(df[["id_contenido", "rating", "rating_confiable", "roi", "financiero_valido"]],
                   on="id_contenido", how="left")


# --------------------------------------------------------------------------- hipotesis
def _h_volumen_uniforme(df):
    d = df[df["anio_estreno"].between(2010, 2025)]
    v = d.groupby(["anio_estreno", "tipo"]).size().unstack()
    pel, ser = v["Película"], v["Serie"]
    ok = min(pel.min(), ser.min()) >= 990 and max(pel.max(), ser.max()) <= 1000
    return {
        "hipotesis": "El volumen por año de estreno es uniforme porque el dataset es una muestra, no el catálogo real.",
        "patron": "Tendencia",
        "como_se_valido": "Conteo de títulos por año de estreno y tipo, 2010–2025.",
        "resultado": (f"Películas: {_rango(pel.min(), pel.max())} por año; series: {_rango(ser.min(), ser.max())} "
                      f"({len(v)} años). Un catálogo real no tiene cifras tan parejas."),
        "veredicto": SE_SOSTIENE if ok else REVISAR,
        "implicancia": "No analizar tendencia de volumen; la tendencia se mide con rating y popularidad.",
    }


def _h_volumen_rating(df, gen):
    vol = gen["genero"].value_counts()
    conf = gen[gen["rating_confiable"]].groupby("genero")["rating"].mean()
    comunes = vol.index.intersection(conf.index)
    rho, p = _rho_permutacion(vol[comunes], conf[comunes])
    top10 = vol.head(10).index
    mejor = conf[top10].idxmax()
    ok = p > 0.05
    return {
        "hipotesis": "Más títulos en un género no implica mejor rating.",
        "patron": "Comparación",
        "como_se_valido": "Spearman entre títulos por género y rating promedio (≥ 20 votos), con prueba de permutación.",
        "resultado": (f"ρ = {_dec(rho)} (p = {_dec(p)}; {len(comunes)} géneros). Entre los 10 más frecuentes, "
                      f"{vol.idxmax()} tiene el mayor volumen (rating {_dec(conf[vol.idxmax()])}) y {mejor} el mejor rating "
                      f"({_dec(conf[mejor])})."),
        "veredicto": SE_SOSTIENE if ok else REVISAR,
        "implicancia": "No elegir géneros por volumen; mirar calidad percibida.",
    }


def _h_volumen_roi(df, gen):
    vol = gen["genero"].value_counts()
    fin = gen[gen["financiero_valido"] == True]  # noqa: E712 (booleana con NaN tras el merge)
    n_fin = fin["genero"].value_counts()
    roi = fin[fin["genero"].isin(n_fin[n_fin >= 30].index)].groupby("genero")["roi"].median()
    rho, p = _rho_permutacion(vol[roi.index], roi)
    glob = float(df.loc[df["financiero_valido"], "roi"].median())
    g_max = vol.idxmax()
    concluyente = p <= 0.05
    return {
        "hipotesis": "Más títulos en un género no implica mejor retorno financiero (ROI).",
        "patron": "Comparación",
        "como_se_valido": "Spearman entre títulos por género y ROI mediano (géneros con ≥ 30 películas válidas), con permutación.",
        "resultado": (f"ρ = {_dec(rho)} (p = {_dec(p)}; solo {len(roi)} géneros). Caso extremo: {g_max}, el de mayor volumen, "
                      f"tiene ROI mediano {_dec(roi[g_max])}x frente a {_dec(glob)}x global."),
        "veredicto": "No concluyente" if not concluyente else REVISAR,
        "implicancia": f"Con {len(roi)} géneros no se puede afirmar ni descartar la relación: presentar el ROI por género con su n, sin generalizar.",
    }


def _h_rating_popularidad(df):
    pearson = df["rating"].corr(df["popularidad"])
    spearman = df["rating"].rank().corr(df["popularidad"].rank())
    c = df[df["rating_confiable"]]
    bajo, alto = c[c["rating"] < 5], c[c["rating"] >= 6]
    p_bajo, p_alto = bajo["popularidad"].quantile(0.95), alto["popularidad"].quantile(0.95)
    ok = spearman > pearson and p_alto > 2 * p_bajo
    return {
        "hipotesis": "Rating y popularidad se asocian de forma débil y no lineal: un rating bajo limita la popularidad máxima.",
        "patron": "Relación",
        "como_se_valido": "Pearson y Spearman en todo el catálogo; percentil 95 de popularidad según tramo de rating (≥ 20 votos).",
        "resultado": (f"Spearman {_dec(spearman)} · Pearson {_dec(pearson)}. Percentil 95 de popularidad: {_dec(p_bajo, 1)} con rating < 5 "
                      f"({_fmt(len(bajo))} títulos) frente a {_dec(p_alto, 1)} con rating ≥ 6 ({_fmt(len(alto))} títulos)."),
        "veredicto": SE_SOSTIENE if ok else REVISAR,
        "implicancia": "Es una asociación, no una causa: un buen rating no garantiza popularidad; no usarla para predecir.",
    }


def _h_rating_tendencia(df):
    c = df[df["rating_confiable"]]
    m = c.groupby(["anio_estreno", "tipo"])["rating"].agg(["mean", "size"]).unstack()
    pel, ser = m["mean"]["Película"], m["mean"]["Serie"]
    n_pel, n_ser = m["size"]["Película"], m["size"]["Serie"]
    x = pel.loc[2010:2024]
    pendiente = float(np.polyfit(x.index, x.values, 1)[0])
    meseta = pel.loc[2020:2024]
    ok = pendiente > 0 and (meseta.max() - meseta.min()) < 0.15 and (ser.max() - ser.min()) < 0.5
    return {
        "hipotesis": "El rating de las películas mejora con los años y el de las series se mantiene estable.",
        "patron": "Tendencia",
        "como_se_valido": "Rating promedio por año y tipo (≥ 20 votos), pendiente 2010–2024 y tamaño de muestra por año.",
        "resultado": (f"Películas: {_dec(pel[2010])} (2010) → {_dec(pel[2019])} (2019) → {_dec(pel[2024])} (2024); pendiente {_dec(pendiente, 3)} por año; "
                      f"2020–2024 entre {_dec(meseta.min())} y {_dec(meseta.max())}. Series: entre {_dec(ser.min())} y {_dec(ser.max())}. "
                      f"2025 ({_dec(pel[2025])} y {_dec(ser[2025])}) se calcula con solo {_fmt(n_pel[2025])} películas y {_fmt(n_ser[2025])} series "
                      f"(años anteriores: {_fmt(n_pel.loc[:2024].min())}+ y {_fmt(n_ser.loc[:2024].min())}+)."),
        "veredicto": ("Se sostiene con matices" if ok else REVISAR),
        "implicancia": "Presentar la mejora como 2010–2019 y luego meseta, y no usar 2025 como punto de llegada sin mostrar su n.",
    }


def _h_umbral(df, gen):
    filas = []
    for u in UMBRALES_VOTOS:
        s = df[df["votos"] >= u]
        por_anio = s.groupby(["anio_estreno", "tipo"])["rating"].mean().unstack()
        g = gen[["id_contenido", "genero"]].merge(s[["id_contenido", "rating"]], on="id_contenido")
        estad = g.groupby("genero")["rating"].agg(["mean", "size"])
        top3 = list(estad[estad["size"] >= 100]["mean"].sort_values(ascending=False).index[:3])
        filas.append({
            "u": u, "retiene": len(s) / len(df) * 100,
            "pel": por_anio["Película"][2024] - por_anio["Película"][2010],
            "ser": por_anio["Serie"][2024] - por_anio["Serie"][2010],
            "animacion_top3": "Animación" in top3,
        })
    t = pd.DataFrame(filas)
    ref = t[t["u"] == 20].iloc[0]
    ok = (t["pel"] > 0).all() and t["animacion_top3"].all()
    series_sensibles = (t["ser"].max() - t["ser"].min()) > 0.3
    return {
        "hipotesis": "El umbral de 20 votos para el rating confiable no cambia las conclusiones.",
        "patron": "Comparación",
        "como_se_valido": f"Se repite el análisis con umbrales de {', '.join(map(str, UMBRALES_VOTOS))} votos (cambio 2010 → 2024 y géneros mejor evaluados).",
        "resultado": (f"Con ≥ 20 votos se conserva el {_dec(ref['retiene'], 1)} % de los títulos (se descarta el {_dec(100 - ref['retiene'], 1)} %). "
                      f"Películas: el cambio 2010 → 2024 va de {_dec(t['pel'].min())} a {_dec(t['pel'].max())} puntos según el umbral (siempre positivo). "
                      f"Series: de {_dec(t['ser'].min())} a {_dec(t['ser'].max())} (con ≥ 20 votos: {_dec(ref['ser'])}); depende mucho del umbral. "
                      f"Animación queda entre los 3 mejores géneros en {int(t['animacion_top3'].sum())} de {len(t)} umbrales."),
        "veredicto": ("Se sostiene para películas y Animación; no para «series estables»" if ok and series_sensibles else
                      (SE_SOSTIENE if ok else REVISAR)),
        "implicancia": "Informar el umbral y el % descartado; presentar las series como estables solo con el umbral de 20 votos.",
    }


def _h_roi_genero(df, gen):
    fin = gen[gen["financiero_valido"] == True]  # noqa: E712
    n_fin = fin["genero"].value_counts()
    validos = n_fin[n_fin >= 30].index
    vol = gen["genero"].value_counts()
    med = fin[fin["genero"].isin(validos)].groupby("genero")["roi"].median()
    mejores = list(med.sort_values(ascending=False).index[:3])
    grandes = [g for g in vol.index[:10] if g in med.index]
    peores = list(med[grandes].sort_values().index[:3])
    ic = {g: _ic_mediana(fin.loc[fin["genero"] == g, "roi"]) for g in mejores + peores}
    glob = _ic_mediana(df.loc[df["financiero_valido"], "roi"])
    techo_peores = max(ic[g][2] for g in peores)
    separados = [g for g in mejores if ic[g][1] > techo_peores + MARGEN_ROI]
    al_limite = [g for g in mejores if techo_peores < ic[g][1] <= techo_peores + MARGEN_ROI]

    def fila(g):
        m, lo, hi = ic[g]
        return f"{g} {_dec(m)}x [{_dec(lo)}–{_dec(hi)}] (n = {_fmt(n_fin[g])})"

    ok = len(separados) >= 2
    return {
        "hipotesis": "Los géneros con mayor ROI mediano (Animación, Familia) superan de verdad a los de menor ROI entre los más frecuentes.",
        "patron": "Comparación",
        "como_se_valido": "Mediana de ROI con intervalo bootstrap del 95 % (5.000 remuestreos, semilla fija); se comparan los 3 mejores contra los 3 peores entre los 10 géneros más frecuentes.",
        "resultado": ("Mejores: " + "; ".join(fila(g) for g in mejores) + ". Peores entre los grandes: " + "; ".join(fila(g) for g in peores)
                      + f". Global: {_dec(glob[0])}x [{_dec(glob[1])}–{_dec(glob[2])}]. "
                      f"Separados con claridad de los peores: {_lista(separados) if separados else 'ninguno'}"
                      + (f"; al límite: {_lista(al_limite)} (intervalo amplio)." if al_limite else ".")),
        "veredicto": ("Se sostiene para " + _lista(separados) + (f"; {_lista(al_limite)} queda al límite" if al_limite else "") if ok else REVISAR),
        "implicancia": "Recomendar con los intervalos a la vista; no ordenar géneros cuyos intervalos se solapan.",
    }


def _h_sesgo_seleccion(df):
    pel = df[df["tipo"] == "Película"]
    a, b = pel[pel["financiero_valido"]], pel[~pel["financiero_valido"]]
    ok = a["votos"].median() > 5 * b["votos"].median()
    return {
        "hipotesis": "Las películas con datos financieros válidos no representan al catálogo (sesgo de selección).",
        "patron": "Segmentación",
        "como_se_valido": "Se comparan las películas con financieros válidos con el resto de las películas: votos, popularidad y rating confiable.",
        "resultado": (f"Votos medianos: {_fmt(a['votos'].median())} frente a {_fmt(b['votos'].median())}. Popularidad mediana: {_dec(a['popularidad'].median(), 1)} "
                      f"frente a {_dec(b['popularidad'].median(), 1)}. Con rating confiable: {_dec(a['rating_confiable'].mean() * 100, 1)} % frente a "
                      f"{_dec(b['rating_confiable'].mean() * 100, 1)} % ({_fmt(len(a))} y {_fmt(len(b))} películas)."),
        "veredicto": SE_SOSTIENE if ok else REVISAR,
        "implicancia": "El ROI describe películas mucho más conocidas que el promedio: no extrapolarlo a todo el catálogo; decisiones con confianza media.",
    }


def _h_popularidad_reciente(df):
    y = df.groupby("anio_estreno").agg(votos=("votos", "median"), pop=("popularidad", "mean"))
    ok = y.loc[2025, "votos"] < y.loc[2024, "votos"] < y.loc[2023, "votos"]
    return {
        "hipotesis": "La caída de popularidad de 2025 se debe a que los títulos recientes acumulan menos interacción.",
        "patron": "Anomalía",
        "como_se_valido": "Votos medianos y popularidad promedio por año de estreno (2018–2025).",
        "resultado": (f"Votos medianos: {_dec(y.loc[2018, 'votos'], 1)} (2018), {_dec(y.loc[2023, 'votos'], 1)} (2023), {_dec(y.loc[2024, 'votos'], 1)} (2024), "
                      f"{_dec(y.loc[2025, 'votos'], 1)} (2025). Popularidad promedio: {_dec(y.loc[2023, 'pop'], 1)} (2023), {_dec(y.loc[2024, 'pop'], 1)} (2024), "
                      f"{_dec(y.loc[2025, 'pop'], 1)} (2025)."),
        "veredicto": "Plausible, no confirmado" if ok else REVISAR,
        "implicancia": "Los votos sí caen, pero la popularidad sube en 2024 y no sigue la misma curva: tratar 2024–2025 como años incompletos y no concluir sobre ellos.",
    }


def tabla_hipotesis(df: pd.DataFrame, bridge: pd.DataFrame) -> pd.DataFrame:
    """Una fila por hipotesis: patron, como se valido, resultado (con cifras), veredicto e implicancia."""
    gen = _tabla_genero(df, bridge)
    filas = [
        _h_volumen_uniforme(df),
        _h_volumen_rating(df, gen),
        _h_volumen_roi(df, gen),
        _h_rating_popularidad(df),
        _h_rating_tendencia(df),
        _h_umbral(df, gen),
        _h_roi_genero(df, gen),
        _h_sesgo_seleccion(df),
        _h_popularidad_reciente(df),
    ]
    t = pd.DataFrame(filas)
    t.insert(0, "n", range(1, len(t) + 1))
    return t


COLUMNAS_MD = {"n": "H", "hipotesis": "Hipótesis", "patron": "Patrón", "como_se_valido": "Cómo se validó",
               "resultado": "Resultado", "veredicto": "Veredicto", "implicancia": "Qué implica"}


def a_markdown(t: pd.DataFrame) -> str:
    cab = "| " + " | ".join(COLUMNAS_MD.values()) + " |\n|" + "---|" * len(COLUMNAS_MD) + "\n"
    cuerpo = "\n".join("| " + " | ".join(str(r[c]).replace("|", "/") for c in COLUMNAS_MD) + " |" for _, r in t.iterrows())
    return cab + cuerpo


def main():
    df = pd.read_csv(ROOT / "data" / "processed" / "streamview_content_clean.csv")
    bridge = pd.read_csv(ROOT / "data" / "processed" / "genero_puente.csv")
    print(a_markdown(tabla_hipotesis(df, bridge)))


if __name__ == "__main__":
    main()
