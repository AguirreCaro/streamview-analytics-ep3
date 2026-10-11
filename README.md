# StreamView Analytics — Proyecto EP3

Proyecto de la **Evaluación Parcial N°3** de *ADY1104 — Visualización de Datos* (Duoc UC). Caso: **StreamView Analytics**.
Integra dos fuentes (películas y series), calcula los KPIs del catálogo, genera los gráficos del análisis exploratorio y contiene el dashboard de Power BI y los documentos del proyecto. **Todo el proyecto está en esta carpeta.**

**Grupo 5:** Carolina Aguirre · Javier Albornoz.

## Estructura

```
StreamView_EP3/
├── data/
│   ├── raw/                       # 2 CSV oficiales entregados por StreamView (Netflix Movies & TV Shows), sin modificar
│   └── processed/                 # generado por src/data_prep.py
│       ├── streamview_content_clean.csv   # dataset unificado, una fila por título (31.991 filas, todas las columnas)
│       ├── streamview_powerbi.csv         # misma data sin texto libre, para importar en Power BI
│       ├── genero_puente.csv              # tabla puente título–género (una fila por género de cada título)
│       ├── validacion_datos.csv           # filas por paso, nulos, decisiones y unidades
│       └── kpis_resumen.csv               # valores de los KPIs de la ficha (para Todos / Movie / TV Show)
├── src/
│   ├── data_prep.py               # integración de las 2 fuentes, limpieza, tabla puente, validación
│   ├── genre_map.py               # taxonomía unificada de géneros (películas y series)
│   ├── kpis.py                    # cálculo de los KPIs de la ficha
│   └── eda_charts.py              # gráficos estáticos (exporta los PNG de images/)
├── notebooks/01_EDA_StreamView.ipynb   # análisis exploratorio completo
├── dashboard/                     # dashboard de Power BI (.pbix)
├── images/                        # gráficos exportados (PNG, con período y n en el título)
├── docs/                          # informe ejecutivo (docx y PDF), resumen, diseño, PDF del dashboard, ficha de KPIs
│   └── EP1_referencia/            # versión anterior del informe (EP1), solo como referencia
├── requirements.txt               # versiones exactas de las librerías
└── README.md
```

## Cómo ejecutar

Requiere **Python 3.11 o superior** (probado con 3.13) y conexión a internet solo para instalar las librerías. Desde la carpeta del proyecto:

| Paso | Comando | Resultado esperado |
|---|---|---|
| 1. Crear y activar un entorno | `python -m venv .venv` y luego `.venv\Scripts\activate` (Windows) o `source .venv/bin/activate` (macOS/Linux) | El prompt muestra `(.venv)` |
| 2. Instalar librerías | `pip install -r requirements.txt` | Instala pandas 3.0.2, numpy 2.4.4, matplotlib 3.10.8, seaborn 0.13.2, notebook 7.6.3, nbconvert 7.17.1, ipykernel 7.4.0 sin errores |
| 3. Preparar los datos | `python src/data_prep.py` | Imprime **31.991 filas** (limpio y Power BI), **70.521 filas** en la tabla puente, 46 filas de validación y **631 filas / 36 KPIs** |
| 4. Generar los gráficos | `python src/eda_charts.py` | Imprime `17 graficos exportados` y deja 17 PNG en `images/` |
| 5. Abrir el análisis | `jupyter notebook notebooks/01_EDA_StreamView.ipynb` (o ejecutarlo sin abrirlo: `jupyter nbconvert --to notebook --execute --inplace notebooks/01_EDA_StreamView.ipynb`) | Todas las celdas corren sin errores |
| 6. Ver el dashboard | Abrir `dashboard/Visualizacion_streamview.pbix` con Power BI Desktop (los PDF de cada página están en `docs/`) | Power BI abre el dashboard; si pide ubicar los datos, apuntar a `data/processed/streamview_powerbi.csv` y `genero_puente.csv` |

Los pasos 3 y 4 son deterministas: ejecutarlos de nuevo produce archivos idénticos.

## Fuentes de datos

- `netflix_movies_detailed_up_to_2025.csv` (16.000 películas) y `netflix_tv_shows_detailed_up_to_2025.csv` (16.000 series).
- Variables relevantes: `type`, `title`, `country`, `release_year`, `genres`, `language`, `popularity`, `vote_count`, `vote_average`, `budget` y `revenue` (solo películas), `duration` (temporadas en series).

## Qué hace `data_prep.py`

1. Carga las dos fuentes y unifica las columnas comunes (películas aportan `budget`/`revenue`; series, `seasons`).
2. Combina ambas y elimina **9 duplicados** (32.000 → **31.991** títulos). Crea `content_id` (tipo + `show_id`), porque `show_id` se repite entre películas y series.
3. **Unifica la taxonomía de géneros** (`genre_map.py`) y genera la **tabla puente** `genero_puente.csv`: una fila por género de cada título. Un título con varios géneros cuenta una vez en cada uno.
4. Calcula las variables derivadas: género y país principal, década, año de incorporación, rating confiable (`vote_count` ≥ 20), **`financiero_valido`** (película con presupuesto ≥ 1 M USD e ingresos > 0: **3.386**) y **ROI = ingresos / presupuesto**.
5. Guarda el dataset completo, el dataset para Power BI, la tabla puente, la tabla de validación y los KPIs.

## KPIs

Los 36 KPIs del proyecto (cubren la lista de KPIs del caso semestral que los datos permiten calcular; la distribución por clasificación etaria no es posible porque `rating` repite `vote_average`) (fórmula, filtro, unidad, tipo de contenido y decisión que apoyan) están en **`docs/ficha_kpis.md`** (y `.csv`). `data/processed/kpis_resumen.csv` trae el valor de cada uno para los filtros `Todos`, `Movie` y `TV Show`; el dashboard debe coincidir con esos valores. Los KPIs financieros no aplican a series.

## Validación de los datos

`data/processed/validacion_datos.csv` (y la sección «Validación de la integración» del notebook) documenta: filas por paso (16.000 + 16.000 = 32.000 → 9 duplicados → 31.991), % de nulos por columna, títulos sin género (974 series, 107 películas) y sin país (2.261), películas con financieros válidos (3.386) y las unidades de cada variable (USD, escala 0-10, índice relativo, razón).

## Limitaciones de los datos

- **Muestra, no volumen real:** ~1.000 películas y ~1.000 series por año de estreno (2010–2025); el dataset es una muestra estratificada y no refleja el volumen real de estrenos.
- **`rating` = `vote_average`:** puntaje 0–10 tipo TMDB; no es una clasificación etaria (G, PG-13, etc.).
- **`duration`:** sin información útil (100 % nulo en películas; «1 Seasons» en el 100 % de las series).
- **Datos financieros:** solo el 21 % de las películas (3.386 de 16.000) tiene presupuesto ≥ 1 M USD e ingresos válidos; el análisis de ROI se restringe a ese subconjunto y no aplica a series.
- **Sin género / sin país:** 974 series y 107 películas sin género; 2.261 títulos sin país. Se mantienen en los totales del catálogo y se excluyen de los rankings por género o país.
- **Taxonomías de género distintas:** el mapeo entre películas y series es una decisión del proyecto; algunos géneros existen en un solo tipo (p. ej. Thriller solo en películas).
- **Géneros múltiples:** los conteos por género no suman el total de títulos.
- **Correlación:** la relación rating–popularidad es positiva débil y no lineal (Spearman 0,21; Pearson 0,03).
