"""
StreamView Analytics - EP5 Visualizacion de Datos
Capa unica de traduccion al espanol de los datos procesados.

Los CSV de data/raw/ no se modifican (son la fuente oficial). La traduccion se aplica una sola
vez, dentro de `data_prep.py`, y todo lo que viene despues (KPIs, graficos, notebook, Power BI)
lee el resultado ya en espanol:

- valores categoricos: tipo (Pelicula / Serie), generos, paises e idiomas;
- nombres de columnas (ver COLUMNAS_ES), con la unidad en el nombre cuando aplica
  (presupuesto_usd, ingresos_usd).

No se traducen los nombres propios: titulos, directores y reparto.

La traduccion no cambia ningun calculo: solo cambian las etiquetas. `python src/data_prep.py`
falla con un mensaje claro si aparece un valor sin traducir (por ejemplo, un pais nuevo).
"""

import pandas as pd

SIN_GENERO = "Sin género informado"
SIN_PAIS = "Sin país informado"

TIPO_ES = {"Movie": "Película", "TV Show": "Serie"}

# Generos canonicos (salida de genre_map.GENRE_MAP) -> espanol
GENERO_ES = {
    "Action": "Acción",
    "Adventure": "Aventura",
    "Animation": "Animación",
    "Comedy": "Comedia",
    "Crime": "Crimen",
    "Documentary": "Documental",
    "Drama": "Drama",
    "Family": "Familia",
    "Fantasy": "Fantasía",
    "History": "Historia",
    "Horror": "Terror",
    "Music": "Música",
    "Mystery": "Misterio",
    "News": "Noticias",
    "Reality": "Reality",
    "Romance": "Romance",
    "Science Fiction": "Ciencia ficción",
    "Soap": "Telenovela",
    "Talk": "Talk show",
    "Thriller": "Suspenso",
    "TV Movie": "Película para TV",
    "War": "Bélica",
    "Western": "Wéstern",
}

# Etiquetas originales de las fuentes que genre_map unifica o descarta (columna generos_fuente)
GENERO_FUENTE_ES = {
    **GENERO_ES,
    "Action & Adventure": "Acción y aventura",
    "Sci-Fi & Fantasy": "Ciencia ficción y fantasía",
    "War & Politics": "Bélica y política",
    "Kids": "Infantil",
    "Unknown": "Desconocido",
}

PAIS_ES = {
    "Afghanistan": "Afganistán",
    "Albania": "Albania",
    "Algeria": "Argelia",
    "Angola": "Angola",
    "Argentina": "Argentina",
    "Armenia": "Armenia",
    "Aruba": "Aruba",
    "Australia": "Australia",
    "Austria": "Austria",
    "Azerbaijan": "Azerbaiyán",
    "Bahamas": "Bahamas",
    "Bangladesh": "Bangladés",
    "Belarus": "Bielorrusia",
    "Belgium": "Bélgica",
    "Bhutan": "Bután",
    "Bolivia": "Bolivia",
    "Bosnia and Herzegovina": "Bosnia y Herzegovina",
    "Botswana": "Botsuana",
    "Brazil": "Brasil",
    "Brunei Darussalam": "Brunéi",
    "Bulgaria": "Bulgaria",
    "Cambodia": "Camboya",
    "Cameroon": "Camerún",
    "Canada": "Canadá",
    "Cayman Islands": "Islas Caimán",
    "Central African Republic": "República Centroafricana",
    "Chile": "Chile",
    "China": "China",
    "Colombia": "Colombia",
    "Congo": "Congo",
    "Cote D'Ivoire": "Costa de Marfil",
    "Croatia": "Croacia",
    "Cuba": "Cuba",
    "Cyprus": "Chipre",
    "Czech Republic": "República Checa",
    "Denmark": "Dinamarca",
    "Dominican Republic": "República Dominicana",
    "Ecuador": "Ecuador",
    "Egypt": "Egipto",
    "Estonia": "Estonia",
    "Ethiopia": "Etiopía",
    "Faeroe Islands": "Islas Feroe",
    "Fiji": "Fiyi",
    "Finland": "Finlandia",
    "France": "Francia",
    "French Polynesia": "Polinesia Francesa",
    "Georgia": "Georgia",
    "Germany": "Alemania",
    "Ghana": "Ghana",
    "Greece": "Grecia",
    "Greenland": "Groenlandia",
    "Guadaloupe": "Guadalupe",
    "Guatemala": "Guatemala",
    "Hong Kong": "Hong Kong",
    "Hungary": "Hungría",
    "Iceland": "Islandia",
    "India": "India",
    "Indonesia": "Indonesia",
    "Iran": "Irán",
    "Iraq": "Irak",
    "Ireland": "Irlanda",
    "Israel": "Israel",
    "Italy": "Italia",
    "Japan": "Japón",
    "Jordan": "Jordania",
    "Kazakhstan": "Kazajistán",
    "Kenya": "Kenia",
    "Kosovo": "Kosovo",
    "Kuwait": "Kuwait",
    "Kyrgyz Republic": "Kirguistán",
    "Lao People's Democratic Republic": "Laos",
    "Latvia": "Letonia",
    "Lebanon": "Líbano",
    "Liechtenstein": "Liechtenstein",
    "Lithuania": "Lituania",
    "Luxembourg": "Luxemburgo",
    "Macao": "Macao",
    "Macedonia": "Macedonia del Norte",
    "Malawi": "Malaui",
    "Malaysia": "Malasia",
    "Malta": "Malta",
    "Mauritania": "Mauritania",
    "Mauritius": "Mauricio",
    "Mexico": "México",
    "Monaco": "Mónaco",
    "Mongolia": "Mongolia",
    "Montenegro": "Montenegro",
    "Morocco": "Marruecos",
    "Myanmar": "Myanmar",
    "Namibia": "Namibia",
    "Nepal": "Nepal",
    "Netherlands": "Países Bajos",
    "Netherlands Antilles": "Antillas Neerlandesas",
    "New Caledonia": "Nueva Caledonia",
    "New Zealand": "Nueva Zelanda",
    "Nicaragua": "Nicaragua",
    "Nigeria": "Nigeria",
    "Norway": "Noruega",
    "Palau": "Palaos",
    "Palestinian Territory": "Territorios Palestinos",
    "Panama": "Panamá",
    "Pakistan": "Pakistán",
    "Paraguay": "Paraguay",
    "Peru": "Perú",
    "Philippines": "Filipinas",
    "Poland": "Polonia",
    "Portugal": "Portugal",
    "Puerto Rico": "Puerto Rico",
    "Qatar": "Catar",
    "Romania": "Rumania",
    "Russia": "Rusia",
    "Rwanda": "Ruanda",
    "Saudi Arabia": "Arabia Saudita",
    "Senegal": "Senegal",
    "Serbia": "Serbia",
    "Singapore": "Singapur",
    "Slovakia": "Eslovaquia",
    "Slovenia": "Eslovenia",
    "Solomon Islands": "Islas Salomón",
    "South Africa": "Sudáfrica",
    "South Korea": "Corea del Sur",
    "Spain": "España",
    "Sri Lanka": "Sri Lanka",
    "St. Kitts and Nevis": "San Cristóbal y Nieves",
    "St. Lucia": "Santa Lucía",
    "St. Pierre and Miquelon": "San Pedro y Miquelón",
    "Sweden": "Suecia",
    "Switzerland": "Suiza",
    "Syrian Arab Republic": "Siria",
    "Taiwan": "Taiwán",
    "Tanzania": "Tanzania",
    "Thailand": "Tailandia",
    "Tunisia": "Túnez",
    "Turkey": "Turquía",
    "US Virgin Islands": "Islas Vírgenes de EE. UU.",
    "Uganda": "Uganda",
    "Ukraine": "Ucrania",
    "United Arab Emirates": "Emiratos Árabes Unidos",
    "United Kingdom": "Reino Unido",
    "United States Minor Outlying Islands": "Islas Ultramarinas Menores de EE. UU.",
    "United States of America": "Estados Unidos",
    "Uruguay": "Uruguay",
    "Uzbekistan": "Uzbekistán",
    "Vanuatu": "Vanuatu",
    "Venezuela": "Venezuela",
    "Vietnam": "Vietnam",
    "Zambia": "Zambia",
}

# Codigos ISO 639-1 (TMDB) -> nombre del idioma. 'xx' = sin idioma (TMDB); 'cn' = cantones;
# 'no' y 'nb' se mantienen separados para no alterar el conteo de idiomas distintos.
IDIOMA_ES = {
    "af": "Afrikáans", "am": "Amárico", "ar": "Árabe", "as": "Asamés", "az": "Azerí",
    "bg": "Búlgaro", "bn": "Bengalí", "bs": "Bosnio", "ca": "Catalán", "cn": "Cantonés",
    "cs": "Checo", "cy": "Galés", "da": "Danés", "de": "Alemán", "dz": "Dzongkha",
    "el": "Griego", "en": "Inglés", "es": "Español", "et": "Estonio", "eu": "Vasco",
    "fa": "Persa", "fi": "Finés", "fr": "Francés", "ga": "Irlandés", "gl": "Gallego",
    "he": "Hebreo", "hi": "Hindi", "hr": "Croata", "ht": "Criollo haitiano", "hu": "Húngaro",
    "hy": "Armenio", "id": "Indonesio", "is": "Islandés", "it": "Italiano", "ja": "Japonés",
    "ka": "Georgiano", "kk": "Kazajo", "kl": "Groenlandés", "km": "Jemer", "kn": "Canarés",
    "ko": "Coreano", "ku": "Kurdo", "ky": "Kirguís", "la": "Latín", "lb": "Luxemburgués",
    "lt": "Lituano", "lv": "Letón", "mi": "Maorí", "mk": "Macedonio", "ml": "Malayalam",
    "mn": "Mongol", "mr": "Maratí", "ms": "Malayo", "mt": "Maltés", "nb": "Noruego (bokmål)",
    "ne": "Nepalí", "nl": "Neerlandés", "no": "Noruego", "or": "Odia", "pa": "Panyabí",
    "pl": "Polaco", "ps": "Pastún", "pt": "Portugués", "ro": "Rumano", "ru": "Ruso",
    "si": "Cingalés", "sk": "Eslovaco", "sl": "Esloveno", "sr": "Serbio", "sv": "Sueco",
    "ta": "Tamil", "te": "Telugu", "th": "Tailandés", "tl": "Tagalo", "tr": "Turco",
    "uk": "Ucraniano", "ur": "Urdu", "vi": "Vietnamita", "xx": "Sin idioma", "yo": "Yoruba",
    "za": "Zhuang", "zh": "Chino mandarín", "zu": "Zulú",
}

# nombre original (o derivado en data_prep) -> nombre en espanol. `genres` no esta aqui: se
# reemplaza por `generos` (taxonomia unificada) y `generos_fuente` (etiquetas originales).
COLUMNAS_ES = {
    "content_id": "id_contenido",
    "show_id": "id_fuente",
    "type": "tipo",
    "title": "titulo",
    "director": "director",
    "cast": "reparto",
    "country": "paises",
    "date_added": "fecha_incorporacion",
    "release_year": "anio_estreno",
    "rating": "rating_fuente",  # la fuente repite vote_average; no se usa en el analisis
    "genres": "generos_fuente",
    "language": "idioma",
    "description": "descripcion",
    "popularity": "popularidad",
    "vote_count": "votos",
    "vote_average": "rating",  # puntaje 0-10 (TMDB)
    "budget": "presupuesto_usd",
    "revenue": "ingresos_usd",
    "seasons": "temporadas",
    "duration_min": "duracion_min",
    "year_added": "anio_incorporacion",
    "decade": "decada",
    "main_genre": "genero_principal",
    "main_country": "pais_principal",
}


def _valor(mapa: dict, valor):
    """Traduce un valor; los nulos y lo que no esta en el diccionario quedan igual."""
    if pd.isna(valor):
        return valor
    return mapa.get(valor, valor)


def _lista(mapa: dict, valor, sep: str = ", "):
    """Traduce cada elemento de una lista separada por comas (paises, generos de la fuente)."""
    if pd.isna(valor):
        return valor
    return sep.join(mapa.get(t.strip(), t.strip()) for t in str(valor).split(",") if t.strip())


def traducir_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve el dataset con valores categoricos y nombres de columnas en espanol.
    Espera las columnas en ingles que produce `data_prep.clean_and_unify` (mas `generos`,
    `main_genre` y `main_country`, que ya salen en espanol de genre_map y data_prep)."""
    out = df.copy()
    out["type"] = out["type"].map(TIPO_ES)
    out["main_country"] = out["main_country"].map(lambda v: _valor(PAIS_ES, v))
    out["country"] = out["country"].map(lambda v: _lista(PAIS_ES, v))
    out["genres"] = out["genres"].map(lambda v: _lista(GENERO_FUENTE_ES, v))
    out["language"] = out["language"].map(lambda v: _valor(IDIOMA_ES, v))
    out = out.rename(columns=COLUMNAS_ES)
    verificar_traduccion(out)
    return out


def pendientes_de_traducir(df: pd.DataFrame) -> dict:
    """Valores categoricos que siguen sin traducir (vacio = todo traducido)."""
    validos = {
        "tipo": set(TIPO_ES.values()),
        "genero_principal": set(GENERO_ES.values()) | {SIN_GENERO},
        "pais_principal": set(PAIS_ES.values()) | {SIN_PAIS},
        "idioma": set(IDIOMA_ES.values()),
    }
    pendientes = {}
    for col, ok in validos.items():
        faltan = sorted(set(df[col].dropna().unique()) - ok)
        if faltan:
            pendientes[col] = faltan
    return pendientes


def verificar_traduccion(df: pd.DataFrame) -> None:
    pendientes = pendientes_de_traducir(df)
    if pendientes:
        raise ValueError(
            "Valores sin traducir (agregarlos a src/traducciones.py): "
            + "; ".join(f"{col}: {vals}" for col, vals in pendientes.items())
        )
