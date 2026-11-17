"""
StreamView Analytics - EP5 Visualizacion de Datos
Taxonomia unificada de generos para peliculas y series.

Las dos fuentes usan etiquetas distintas (peliculas: "Action", "Science Fiction";
series: "Action & Adventure", "Sci-Fi & Fantasy"). GENRE_MAP lleva cada etiqueta
de origen a una o mas etiquetas canonicas, de modo que ambos tipos de contenido
sean comparables. La salida de `canonical_genres` ya esta en espanol
(traduccion en `traducciones.GENERO_ES`).
"""

import pandas as pd

from traducciones import GENERO_ES, SIN_GENERO

# etiqueta de origen -> lista de generos canonicos (en ingles; se traducen al devolverlos)
# Solo se listan las etiquetas que cambian; el resto se mantiene tal cual.
_SIN_GENERO_CANONICO = "__sin_genero__"
GENRE_MAP = {
    "Action & Adventure": ["Action", "Adventure"],
    "Sci-Fi & Fantasy": ["Science Fiction", "Fantasy"],
    "War & Politics": ["War"],
    "Kids": ["Family"],
    "Unknown": [_SIN_GENERO_CANONICO],
}


def _es(genero: str) -> str:
    return SIN_GENERO if genero == _SIN_GENERO_CANONICO else GENERO_ES.get(genero, genero)


def canonical_genres(value) -> list:
    """Devuelve la lista de generos canonicos en espanol (sin repetir, en orden) de un campo
    `genres` separado por comas. Si esta vacio devuelve [SIN_GENERO]."""
    if pd.isna(value) or not str(value).strip():
        return [SIN_GENERO]
    out = []
    for token in str(value).split(","):
        token = token.strip()
        if not token:
            continue
        for g in GENRE_MAP.get(token, [token]):
            if g not in out:
                out.append(g)
    # "Unknown" junto a generos reales no debe sumar una fila extra de "sin genero"
    if len(out) > 1 and _SIN_GENERO_CANONICO in out:
        out.remove(_SIN_GENERO_CANONICO)
    out = [_es(g) for g in out]
    return out or [SIN_GENERO]


def main_genre(value) -> str:
    """Primer genero canonico (genero principal del titulo)."""
    return canonical_genres(value)[0]
