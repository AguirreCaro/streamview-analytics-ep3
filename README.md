# StreamView Analytics — Proyecto EP5

Proyecto de la **Evaluación Parcial N°5** (continuación de EP3) de *ADY1104 — Visualización de Datos* (Duoc UC). Caso: **StreamView Analytics**.
Integra dos fuentes (películas y series), calcula los KPIs del catálogo, genera los gráficos del análisis exploratorio y contiene el dashboard de Power BI y los documentos del proyecto. **Todo el proyecto está en esta carpeta.**

**Grupo 5:** Carolina Aguirre · Javier Albornoz.

## Estructura

```
StreamView_EP5/
├── data/
│   ├── raw/                       # 2 CSV oficiales entregados por StreamView (Netflix Movies & TV Shows), sin modificar
│   └── processed/                 # generado por src/data_prep.py
│       ├── streamview_content_clean.csv   # dataset unificado, una fila por título (31.991 filas, todas las columnas)
│       ├── streamview_powerbi.csv         # misma data sin texto libre, para importar en Power BI
│       ├── genero_puente.csv              # tabla puente título–género (una fila por género de cada título)
│       ├── validacion_datos.csv           # filas por paso, nulos, decisiones, unidades y traducción
│       └── kpis_resumen.csv               # valores de los KPIs de la ficha (para Todos / Película / Serie)
├── src/
│   ├── data_prep.py               # integración de las 2 fuentes, limpieza, tabla puente, validación
│   ├── genre_map.py               # taxonomía unificada de géneros (películas y series)
│   ├── traducciones.py            # traducción al español: tipo, géneros, países, idiomas y nombres de columna
│   ├── hipotesis.py               # hipótesis del EDA y su validación (cifras recalculadas; tabla de la sección 3.17)
│   ├── kpis.py                    # cálculo de los KPIs de la ficha
│   ├── cifras_control.py          # cifras esperadas de las medidas del dashboard (genera dashboard/cifras_de_control.csv)
│   └── eda_charts.py              # gráficos estáticos (exporta los PNG de images/)
├── notebooks/01_EDA_StreamView.ipynb   # análisis exploratorio completo
├── dashboard/
│   ├── Visualizacion_EP5.pbix     # dashboard de Power BI (5 páginas)
│   ├── GUIA_Power_BI_EP5.md       # cómo se construyó, estado final y pendientes
│   ├── consulta_powerquery.m      # consultas de Power Query a los CSV traducidos
│   ├── medidas_dax.dax            # medidas y columna calculada del modelo
│   ├── mapa_nombres.csv           # nombre antiguo → nombre nuevo de tablas, columnas y medidas
│   └── cifras_de_control.csv      # valor que debe mostrar cada medida con distintos filtros
├── images/                        # 17 gráficos del análisis exploratorio (PNG, con período y n en el título)
├── docs/
│   ├── Informe_Ejecutivo_EP5.docx # informe ejecutivo (exportar a PDF para la entrega)
│   ├── Resumen_Ejecutivo_EP5.docx # resumen ejecutivo (Decision Brief de una página)
│   ├── Diseño_Visualizacion_EP5.docx
│   ├── Presentacion_EP6.pptx      # presentación (10 min + 5 de preguntas)
│   ├── Guion_Presentacion_EP6.md  # guion, demostración y preguntas probables
│   ├── Plan_EP5_EP6.md            # plan de trabajo y reparto entre los dos integrantes
│   └── ficha_kpis.md / .csv       # ficha de los 36 KPIs
├── requirements.txt               # versiones exactas de las librerías
└── README.md
```

## Cómo ejecutar

Requiere **Python 3.11 o superior** (probado con 3.13) y conexión a internet solo para instalar las librerías. Desde la carpeta del proyecto:

| Paso | Comando | Resultado esperado |
|---|---|---|
| 1. Crear y activar un entorno | `python -m venv .venv` y luego `.venv\Scripts\activate` (Windows) o `source .venv/bin/activate` (macOS/Linux) | El prompt muestra `(.venv)` |
| 2. Instalar librerías | `pip install -r requirements.txt` | Instala pandas 3.0.2, numpy 2.4.4, matplotlib 3.10.8, seaborn 0.13.2, notebook 7.6.3, nbconvert 7.17.1, ipykernel 7.4.0 sin errores |
| 3. Preparar los datos | `python src/data_prep.py` | Imprime **31.991 filas** (limpio y Power BI), **70.521 filas** en la tabla puente, 52 filas de validación y **631 filas / 36 KPIs** |
| 4. Generar los gráficos | `python src/eda_charts.py` | Imprime `17 graficos exportados` y deja 17 PNG en `images/` |
| 5. Abrir el análisis | `jupyter notebook notebooks/01_EDA_StreamView.ipynb` (o ejecutarlo sin abrirlo: `jupyter nbconvert --to notebook --execute --inplace notebooks/01_EDA_StreamView.ipynb`) | Todas las celdas corren sin errores |
| 6. Ver el dashboard | Abrir `dashboard/Visualizacion_EP5.pbix` con Power BI Desktop | Power BI abre el dashboard; si pide ubicar los datos, apuntar a `data/processed/streamview_powerbi.csv` y `genero_puente.csv` |

Los pasos 3 y 4 son deterministas: ejecutarlos de nuevo produce archivos idénticos.

Para el dashboard de EP5: `python src/cifras_control.py` genera `dashboard/cifras_de_control.csv` (valor esperado de cada medida; se calcula dos veces con código distinto y falla si no coinciden), y `dashboard/GUIA_Power_BI_EP5.md` explica los cambios en Power BI, con la consulta de Power Query (`consulta_powerquery.m`), las medidas (`medidas_dax.dax`) y el mapa de nombres (`mapa_nombres.csv`).

Opcional: `python src/hipotesis.py` imprime la tabla de hipótesis y validación del EDA (sección 3.17 del notebook), con cada cifra recalculada. Las pruebas de permutación y los intervalos bootstrap usan semilla fija, así que la salida es idéntica en cada ejecución; si la evidencia dejara de respaldar una hipótesis, el veredicto cambia a «Revisar».

## Fuentes de datos

- `netflix_movies_detailed_up_to_2025.csv` (16.000 películas) y `netflix_tv_shows_detailed_up_to_2025.csv` (16.000 series).
- Variables relevantes: `type`, `title`, `country`, `release_year`, `genres`, `language`, `popularity`, `vote_count`, `vote_average`, `budget` y `revenue` (solo películas), `duration` (temporadas en series).

## Traducción al español

Los CSV de `data/raw/` no se modifican (son la fuente oficial, en inglés). La traducción se aplica **una sola vez** en `src/traducciones.py`, desde `data_prep.py`, y todo lo que viene después (KPIs, gráficos, notebook, Power BI) lee los datos ya en español. La traducción **solo cambia etiquetas**: se verificó que dataset, tabla puente y KPIs mantienen las mismas cifras (31.991 títulos, 3.386 películas con datos financieros, ROI mediano 1,68x, rating promedio 6,62).

| Qué | Antes | Ahora |
|---|---|---|
| Tipo | `Movie` / `TV Show` | `Película` / `Serie` |
| Géneros (23, más «sin género») | `Action`, `Science Fiction`, `Horror`, `Thriller`… | `Acción`, `Ciencia ficción`, `Terror`, `Suspenso`… |
| Países (122 como país principal, más «sin país») | `United States of America`, `South Korea`… | `Estados Unidos`, `Corea del Sur`… |
| Idiomas (83) | códigos ISO (`en`, `zh`, `ja`…) | `Inglés`, `Chino mandarín`, `Japonés`… |
| Sin dato | `Sin pais informado`, `Sin genero informado` | `Sin país informado`, `Sin género informado` |
| Columnas | `main_genre`, `main_country`, `vote_average`, `vote_count`, `popularity`, `budget`, `revenue`, `release_year`, `year_added`, `content_id`, `show_id`, `title`, `cast`… | `genero_principal`, `pais_principal`, `rating`, `votos`, `popularidad`, `presupuesto_usd`, `ingresos_usd`, `anio_estreno`, `anio_incorporacion`, `id_contenido`, `id_fuente`, `titulo`, `reparto`… |

Notas:

- No se traducen los nombres propios: títulos, directores y reparto.
- `generos` es la lista de géneros con la taxonomía unificada (de ahí sale la tabla puente); `generos_fuente` conserva las etiquetas originales de la fuente, traducidas (`Infantil`, `Acción y aventura`…). `rating_fuente` es la columna `rating` original (repite el puntaje) y no se usa en el análisis; el puntaje 0-10 se llama ahora `rating`.
- Si aparece un valor sin traducir (por ejemplo un país nuevo), `python src/data_prep.py` se detiene con un mensaje que indica qué agregar a `src/traducciones.py`.
- Con el cambio de nombres, el `.pbix` debe volver a apuntar a las columnas nuevas de `data/processed/streamview_powerbi.csv` y `genero_puente.csv`.

## Qué hace `data_prep.py`

1. Carga las dos fuentes y unifica las columnas comunes (películas aportan `budget`/`revenue`; series, `seasons`).
2. Combina ambas y elimina **9 duplicados** (32.000 → **31.991** títulos). Crea `content_id` (tipo + `show_id`), porque `show_id` se repite entre películas y series.
3. **Unifica la taxonomía de géneros** (`genre_map.py`) y genera la **tabla puente** `genero_puente.csv`: una fila por género de cada título. Un título con varios géneros cuenta una vez en cada uno.
4. Calcula las variables derivadas: género y país principal, década, año de incorporación, rating confiable (`vote_count` ≥ 20), **`financiero_valido`** (película con presupuesto ≥ 1 M USD e ingresos > 0: **3.386**) y **ROI = ingresos / presupuesto**.
5. **Traduce al español** valores y nombres de columnas (`traducciones.py`; ver sección anterior).
6. Guarda el dataset completo, el dataset para Power BI, la tabla puente, la tabla de validación y los KPIs.

## KPIs

Los 36 KPIs del proyecto (cubren la lista de KPIs del caso semestral que los datos permiten calcular; la distribución por clasificación etaria no es posible porque `rating_fuente` repite el puntaje `vote_average`) (fórmula, filtro, unidad, tipo de contenido y decisión que apoyan) están en **`docs/ficha_kpis.md`** (y `.csv`). `data/processed/kpis_resumen.csv` trae el valor de cada uno para los filtros `Todos`, `Movie` y `TV Show`; el dashboard debe coincidir con esos valores. Los KPIs financieros no aplican a series.

## Validación de los datos

`data/processed/validacion_datos.csv` (y la sección «Validación de la integración» del notebook) documenta: filas por paso (16.000 + 16.000 = 32.000 → 9 duplicados → 31.991), % de nulos por columna, títulos sin género (974 series, 107 películas) y sin país (2.261), películas con financieros válidos (3.386) las unidades de cada variable (USD, escala 0-10, índice relativo, razón) y la traducción aplicada (sección `5_traduccion`, sin valores pendientes).

## Limitaciones de los datos

- **Muestra, no volumen real:** ~1.000 películas y ~1.000 series por año de estreno (2010–2025); el dataset es una muestra estratificada y no refleja el volumen real de estrenos.
- **`rating_fuente` = `rating`:** la fuente repite `vote_average` en su columna `rating`; en los datos procesados el puntaje se llama `rating`. Es un puntaje 0–10 tipo TMDB; no es una clasificación etaria (G, PG-13, etc.).
- **`duration`:** sin información útil (100 % nulo en películas; «1 Seasons» en el 100 % de las series).
- **Datos financieros:** solo el 21 % de las películas (3.386 de 16.000) tiene presupuesto ≥ 1 M USD e ingresos válidos; el análisis de ROI se restringe a ese subconjunto y no aplica a series.
- **Sin género / sin país:** 974 series y 107 películas sin género; 2.261 títulos sin país. Se mantienen en los totales del catálogo y se excluyen de los rankings por género o país.
- **Taxonomías de género distintas:** el mapeo entre películas y series es una decisión del proyecto; algunos géneros existen en un solo tipo (p. ej. Thriller solo en películas).
- **Géneros múltiples:** los conteos por género no suman el total de títulos.
- **Correlación:** la relación rating–popularidad es positiva débil y no lineal (Spearman 0,21; Pearson 0,03).
