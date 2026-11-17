# Guía Power BI — de EP3 a EP5

Para hacer en **Power BI Desktop**, sobre una copia de `Visualizacion_EP3.pbix`. El `.pbix` es binario y no se puede editar desde fuera, así que esta guía, la consulta de Power Query, las medidas DAX y las cifras de control están preparadas para que el cambio sea mecánico.

| Archivo | Para qué sirve |
|---|---|
| `consulta_powerquery.m` | Consultas que leen los CSV traducidos (paso 3) |
| `medidas_dax.dax` | Las 7 medidas existentes reescritas y 8 medidas nuevas (paso 4) |
| `mapa_nombres.csv` | Nombre actual → nombre nuevo de tablas, columnas y medidas (paso 2) |
| `cifras_de_control.csv` | Valor que debe mostrar cada medida con distintos filtros (paso 5). Se regenera con `python src/cifras_control.py` y se calcula dos veces con código distinto: el script falla si no coinciden |

## Estado final del dashboard (lo que realmente se aplicó)

El dashboard se construyó siguiendo esta guía con algunas diferencias, que son las que valen para el informe.

**Aplicado:** nombres en español en el modelo; origen en los CSV traducidos (la consulta entrega los nombres en español; el paso `CompatModelo` no sirve en Power BI Desktop 2026.10); relación `genero_puente` → `contenido` con filtro cruzado «Ambas»; medidas renombradas y nuevas; `ROI_Calculo` eliminada; colores de película y serie; ROI por género con mínimo de 30 películas, línea en 1 y color por regla; rating por género con color por regla y línea del promedio; rankings Top 10 por título único; dispersiones con escala logarítmica; marcadores «Borrar filtros» por página; página Storytelling con la narrativa y tres gráficos de apoyo.

**Diferencias respecto de lo que dice la guía más abajo:**
- Las páginas se llaman **Gerencia General, Gerencia de Contenidos, Contenidos y Marketing, Contenidos y Adquisición y Storytelling**. No se creó una página «Decisiones»: la página **Storytelling** cuenta la historia en cinco preguntas, con tres gráficos de apoyo.
- El rating por género exige **500** títulos con rating confiable (no 100): con 100, Telenovela (154 títulos) quedaría primera.
- Se conservaron las medidas originales `ROI_Mediano` y `Rating_Promedio`, que calculan lo mismo que las propuestas.
- Los rankings por título usan la columna calculada `titulo_visual` y, en el de rating, la medida `Rating para ordenar` para desempatar por votos. Las fórmulas están al final de `medidas_dax.dax`.
- `Títulos con país informado` usa `KEEPFILTERS`; sin él, todas las barras daban el mismo valor.

**Pendiente (mejoras futuras):** texto alternativo en los gráficos, orden de lectura, sincronización de los filtros entre páginas, prueba con un simulador de daltonismo, información sobre herramientas con el n y la prueba de usabilidad.

---

Orden recomendado y tiempo estimado: pasos 1–5 (datos y medidas, 30–40 min), 6–7 (gráficos y navegación, 60–90 min), 8–9 (accesibilidad y entrega, 30 min). Una sola persona edita el `.pbix` a la vez.

---

## 0. Lo que se encontró en el `.pbix`

Se revisó la definición del reporte (páginas, visuales, filtros, marcadores). **No** se pudo leer el código DAX de las medidas actuales ni los metadatos del modelo; por eso las medidas se reemplazan en lugar de editarse.

| # | Hallazgo | Dónde | Efecto |
|---|---|---|---|
| 1 | Los botones «P P P P S» son el **navegador de páginas** (277 px de ancho), que usa el nombre de cada página: «Página 1»…«Página 4» y «Storytelling». Solo cabe la inicial | todas las páginas | El usuario no sabe a dónde lleva cada botón |
| 2 | **«BORRAR FILTROS» de la Página 2 usa el marcador de la Página 1**; el marcador «Reset Filtros Pag2» existe pero apunta a una página que ya no existe | Página 2 | Al borrar filtros, el usuario probablemente salta a la Página 1 (comprobable haciendo clic en el botón) |
| 3 | Página 1 **sí tiene tarjetas de KPI**; el PDF exportado no las muestra | Página 1 | `dashboard/Visualizacion_EP3.pdf` está desactualizado |
| 4 | El archivo no tiene configurada la sincronización de segmentadores (tipo, género, país, año) entre páginas | todas | Probablemente se pierde el filtro al cambiar de página. Comprobar en Vista > Sincronizar segmentadores |
| 5 | Página 4 y «Storytelling» tienen filtro de página `tipo = Movie`; la Página 4 conserva el segmentador «tipo» | Páginas 4 y 5 | Elegir «TV Show» deja la Página 4 vacía |
| 6 | «Rating promedio por género»: sin orden y **sin excluir «Sin género informado»** (los otros tres gráficos por género sí lo excluyen) | Página 3 | Barras desordenadas e incluye una categoría sin sentido |
| 7 | «ROI mediano por género»: **sin mínimo de películas**. Documental (28 películas) aparece primero con 2,83x y «Película para TV» (2 películas) también entra. La ficha de KPIs exige ≥ 30 | Páginas 1 y 4 | El gráfico contradice a la ficha y a la presentación (Animación 2,29x) |
| 8 | «Rating Promedio» y «Popularidad Promedio» agrupan por **nombre** del título: 2.434 filas comparten nombre con otro título. En el PDF, «Rating Promedio» coincide con 8 de los 10 títulos de K15; «Popularidad Promedio» muestra la lista completa con barra de desplazamiento | Página 3 | Promedios de títulos distintos mezclados; ranking sin límite de 10 |
| 9 | Dispersión rating vs popularidad: el eje llega a ~6.400 por **un solo título** (máximo real 6.421,9; el percentil 98 es 228,1) | Página 3 | Casi todos los puntos quedan aplastados abajo. No era un error de sumas |
| 10 | Dispersión presupuesto vs ingresos: ejes lineales en «mil M» (miles de millones) | Página 4 | 3.386 puntos amontonados abajo a la izquierda |
| 11 | Ningún visual tiene **texto alternativo**; en la Página 1 las tarjetas de KPI quedan después de los gráficos en el orden de tabulación | todas | Accesibilidad |
| 12 | El subtítulo del gráfico de líneas está oculto y dice «n=31.991», pero el gráfico usa solo títulos con ≥ 20 votos (18.371) | Página 1 | n incorrecto si se activa |
| 13 | Valores en inglés escritos dentro del reporte: `'Movie'` y `'TV Show'` (colores de 4 gráficos, filtros de página de 2 páginas y un marcador) y `'Sin genero informado'` (4 filtros de visual y un marcador) | ver paso 6 | **Al traducir los datos, estos filtros dejan de funcionar** y los colores vuelven a los predeterminados |
| 14 | «Storytelling» es texto fijo que menciona «Crime» y «Thriller» y está bajo un filtro de página de películas | Página 5 | Texto en inglés y desconectado de los filtros |

---

## 1. Preparación

1. Copia `Visualizacion_EP3.pbix` como `Visualizacion_EP5.pbix`. Trabaja solo sobre la copia.
2. Ejecuta `python src/data_prep.py` y `python src/cifras_control.py` para tener los CSV y las cifras de control al día.
3. Ten abierto `mapa_nombres.csv` y `medidas_dax.dax`.

## 2. Renombrar en el modelo (los gráficos se actualizan solos)

En la **vista de datos** (o en el panel Datos), renombra cada tabla, columna y medida con **clic derecho > Cambiar nombre** (o F2), siguiendo `mapa_nombres.csv`. Power BI actualiza todos los gráficos, filtros y fórmulas que usan ese campo, así que no hay que volver a arrastrar nada. No cambies todavía las expresiones de las medidas.

## 3. Cambiar el origen de datos

1. **Inicio > Transformar datos > Administrar parámetros > Nuevo parámetro**: nombre `RutaDatos`, tipo Texto, valor la carpeta `data\processed\` de este proyecto con la barra final.
2. En el Editor de Power Query abre la consulta `streamview_powerbi (1)` > **Editor avanzado**, reemplaza todo por la primera consulta de `consulta_powerquery.m`. Repite con `genero_puente`.
3. **Cerrar y aplicar**. Las consultas deben entregar los nombres **en español** (los del paso 2). En Power BI Desktop 2026.10 renombrar una columna en el panel Datos cambia también su nombre de origen: si la consulta devolviera los nombres antiguos en inglés, Power BI eliminaría las columnas en español y los gráficos se romperían («Hubo un problema con uno o más campos»).
3b. **Revisar la relación** en la Vista de modelo: `genero_puente[id_contenido]` → `contenido[id_contenido]`, muchos a uno, con dirección del filtro cruzado **Ambas**. Si quedó en «Única», todos los géneros muestran el total del catálogo (31.991).
4. Convierte el campo `pais_principal` en **Categoría de datos: País o región** (Herramientas de columna), para que el mapa no confunda, por ejemplo, Georgia con el estado de EE. UU.

## 4. Reemplazar las medidas

Para cada medida de la tabla `contenido` listada en `mapa_nombres.csv` («medida»), selecciónala, pega la expresión de `medidas_dax.dax` y aplica el formato indicado en el comentario. Luego crea las 8 medidas nuevas. Las dos de dinero ahora muestran **millones de USD**.

## 5. Verificar con las cifras de control

Con el segmentador «tipo» y sin otros filtros, las tarjetas deben mostrar:

| Medida | Todos | Película | Serie |
|---|---|---|---|
| Total de títulos | 31.991 | 16.000 | 15.991 |
| Rating promedio (0-10) | 6,62 | 6,36 | 7,39 |
| Popularidad promedio (índice) | 42,63 | 20,38 | 64,88 |
| Películas con datos financieros | 3.386 | 3.386 | 0 |
| ROI mediano (x) | 1,68 | 1,68 | (en blanco) |
| Presupuesto total (USD millones) | 125.908 | 125.908 | (en blanco) |
| Ingreso total (USD millones) | 366.585 | 366.585 | (en blanco) |

Con el segmentador de género: Animación → ROI 2,29x con 280 películas y rating 7,24; Drama → ROI 1,23x con 1.567 películas; Documental → ROI 2,83x con **28** películas (debe desaparecer del gráfico cuando agregues el filtro del paso 6). La lista completa está en `cifras_de_control.csv`. **Si una cifra no coincide, no sigas: revisa el paso 3 (cultura `en-US`) y las expresiones DAX.**

---

## 6. Cambios por gráfico

### 6.1 Valores traducidos que hay que corregir (si no, los filtros fallan sin avisar)

| Qué | Dónde | Cambio |
|---|---|---|
| Filtro de página `tipo = Movie` | Página 4 y «Storytelling» | Cambiar a `Película`. En la Página 4 además **elimina el segmentador «tipo»** y deja el texto «Solo películas» |
| Filtro de visual `genero` distinto de `Sin genero informado` | «ROI mediano por género» (Págs. 1 y 4), «Top 10 géneros por volumen» (Pág. 1), «Composición del catálogo por género» (Pág. 2) | Cambiar el valor a `Sin género informado` |
| Falta ese mismo filtro | «Rating promedio por género» (Pág. 3) | Agregarlo |
| Colores por serie `Movie` / `TV Show` | Líneas (Pág. 1), circular (Pág. 2), área y dispersión (Pág. 3) | Reasignar: **Película `#E50914`, Serie `#221F1F`** en Formato > Colores de datos |
| Marcadores | «Reset Filtros» y «Reset Filtros Pag4» | Volver a crearlos (paso 7.3) |

### 6.2 Por página

**Página 1 · Panorama** (Gerencia General)
- Tarjetas: títulos con la medida y unidad; formato con separador de miles.
- «Evolución del rating por año» → título **«Rating promedio por año de estreno y tipo»**; activa el subtítulo con la medida `Subtítulo rating`. Además de las líneas, activa etiquetas de datos en el último punto o una leyenda directa, para no depender solo del color. Los años 2024–2025 tienen poca interacción acumulada (H5, H9): nómbralo en el texto del análisis.
- «Producción por país» → título «Títulos por país principal»; subtítulo `Subtítulo catálogo`.
- «Mediana de ROI por género» → título **«ROI mediano por género (películas con ≥ 30 datos válidos)»**; filtro del visual: medida `Películas con datos financieros` **es mayor o igual que 30**; orden descendente; **Análisis > Línea constante en 1** con etiqueta «ROI = 1: recupera lo invertido»; etiquetas de datos; color por regla con `Color ROI por género`; subtítulo `Subtítulo ROI`.
- «Top 10 géneros por volumen» → título «Top 10 géneros por títulos (un título cuenta en cada género)»; **Filtro Top N: 10 por `Total de títulos`**.

**Página 2 · Catálogo** (Gerencia de contenidos)
- «Principales idiomas del catálogo» → **Filtro Top N: 10 por `Total de títulos`** (hoy lista todos los idiomas).
- El circular «Catálogo por tipo» se mantiene: son solo 2 categorías (ver 3.3 del notebook).
- Mapa y treemap: títulos con unidad y subtítulo `Subtítulo catálogo`.

**Página 3 · Desempeño** (Contenidos y Marketing)
- «Rating promedio por género» → orden descendente; filtro: excluir `Sin género informado` y **`Títulos con rating confiable` ≥ 500** (el mismo mínimo con que el informe afirma que Animación lidera; con 100, Telenovela, de solo 154 títulos con rating confiable y 7,29 de rating, quedaría primera); etiquetas de datos; color por regla con `Color rating por género`; **Análisis > Línea constante** con el valor de `Rating promedio de referencia` (no se acorta el eje: las barras parten de 0 para no exagerar diferencias, y las etiquetas muestran la diferencia).
- «Popularidad promedio por año de estreno» → transparencia de las áreas en 50 % para que se vea la serie de atrás.
- «Rating Promedio» y «Popularidad Promedio» → **categoría `id_contenido`** en lugar de `titulo` (muestra `titulo` en información sobre herramientas); **Filtro Top N: 10**; en el de rating, filtro adicional `rating_confiable` = True. Comprueba que el resultado coincide con la lista K15 de `data/processed/kpis_resumen.csv`. Títulos: «Top 10 títulos por rating (≥ 20 votos)» y «Top 10 títulos por popularidad».
- «Relación entre rating y popularidad» → categoría `id_contenido`; **X = columna `rating`, Y = columna `popularidad`** (no las medidas); filtro `rating_confiable` = True; **eje Y en escala logarítmica** (la popularidad mínima es 2,3: no hay ceros); título «Rating y popularidad por título (≥ 20 votos, eje vertical logarítmico)».

**Página 4 · Retorno financiero** (Contenidos y Adquisición)
- Tarjetas con `Presupuesto total (USD millones)` e `Ingreso total (USD millones)`.
- «ROI mediano por género» → igual que en la Página 1.
- «Presupuesto vs Ingresos» → **escala logarítmica en ambos ejes**, unidades en millones; ejes «Presupuesto (USD)» e «Ingresos (USD)» (como `09_presupuesto_vs_ingresos.png`); categoría `id_contenido`.
- «Ingreso Total» → título **«Top 10 películas por ingresos (USD millones)»**; eje en millones.

**Página 5 · Decisiones** (reemplaza «Storytelling»)
Reemplaza el texto fijo por una vista ligada a los filtros, con la tabla de decisiones del plan (C2). Una fila por decisión, cada una con un visual, una etiqueta de **confianza** y un riesgo:

| Decisión | Visual | Confianza | Riesgo que se nombra |
|---|---|---|---|
| Reasignar presupuesto hacia Animación y Familia | Barras de `ROI mediano (x)` con filtro de género (Animación, Familia, Drama, Crimen, Suspenso) y `n` visible | Media | El ROI se calcula en el 21 % de las películas, que son más conocidas que el resto (H8) |
| Terror, con cautela | Tarjetas `ROI mediano (x)` y `Rating promedio (0-10)` con filtro de género = Terror | Media-baja | Intervalo de ROI muy amplio (H7) y rating bajo |
| Priorizar adquisición por calidad y popularidad | Barras de `Rating promedio (0-10)` por género (≥ 500 títulos con rating confiable) | Media | Popularidad no es reproducciones |
| Enfocar 5 mercados | Mapa o barras de `Total de títulos` por país | Media | Muestra uniforme por año |
| Adoptar el dashboard | Texto con el resultado de la prueba de usabilidad | — | Sin datos de suscripción ni retención |

Quita el filtro de página `tipo = Película` de esta página.

---

## 7. Navegación

1. **Nombres de página** (clic derecho en la pestaña > Cambiar nombre): `Panorama`, `Catálogo`, `Desempeño`, `Retorno financiero`, `Decisiones`. Cada página mantiene su subtítulo de audiencia (Gerencia General, etc.).
2. **Navegador de páginas:** aumenta su alto a ~270 px (cabe en el panel izquierdo: termina en y ≈ 1.040 de 1.080) y en Formato > Diseño de cuadrícula elige orientación **vertical**, una columna. Así se lee el nombre completo de cada página.
3. **«BORRAR FILTROS»:** con cada página sin filtros ni selecciones, crea su marcador (Marcadores > Agregar, con las opciones Datos, Pantalla y Página actual activadas) y asígnalo al botón de esa página (Formato del botón > Acción > Marcador). Hoy el de la Página 2 usa el de la Página 1. Elimina «Reset Filtros Pag2» (apunta a una página inexistente) y vuelve a crear «Reset Filtros» y «Reset Filtros Pag4», que guardan los valores en inglés. Prueba cada botón después de crearlo.
4. **Sincronizar segmentadores:** Vista > Sincronizar segmentadores; sincroniza `tipo`, `genero`, `pais_principal` y `anio_estreno` en las Páginas 1–3 (casilla «Sincronizar» y «Visible» solo donde se muestra). En la Página 4 no se sincroniza `tipo`.
5. **Tooltips con `n`:** agrega `Títulos con rating confiable` o `Películas con datos financieros` como información de las barras por género.

## 8. Accesibilidad

- **Texto alternativo** en cada visual (Formato > General > Texto alternativo). Propuestas:

| Visual | Texto alternativo |
|---|---|
| Tarjetas | Cuatro indicadores del catálogo con los filtros activos: total de títulos, popularidad promedio, ROI mediano y rating promedio. |
| Líneas de rating | Rating promedio por año de estreno, películas y series. Las películas suben hasta 2019 y luego se estabilizan; las series se mantienen entre 7,2 y 7,5. |
| Mapa / barras de países | Cantidad de títulos por país principal. Estados Unidos concentra la mayor cantidad. |
| ROI por género | ROI mediano por género de las películas con datos válidos, con línea en ROI igual a 1. Animación y Familia lideran. |
| Top 10 géneros / treemap | Cantidad de títulos por género; un título cuenta en cada uno de sus géneros. |
| Rating por género | Rating promedio por género con 20 o más votos, con línea del promedio global. Animación lidera. |
| Dispersión rating-popularidad | Relación débil entre rating y popularidad; un rating bajo limita la popularidad máxima. Eje vertical logarítmico. |
| Presupuesto vs ingresos | Relación positiva con mucha dispersión entre presupuesto e ingresos de las películas, ambos ejes logarítmicos. |

- **Orden de lectura** (Vista > Panel de selección > flechas, o Formato > Orden de tabulación): título → segmentadores → tarjetas de KPI → gráficos de izquierda a derecha y de arriba abajo → botón borrar filtros → navegador. En la Página 1 mueve las tarjetas antes de los gráficos.
- **Color:** no depender solo del rojo y el negro. Leyenda con nombres, etiquetas de datos y, en las barras, color neutro (`#595959`) con el rojo (`#E50914`) solo en lo destacado. Ambos tienen contraste ≥ 3:1 sobre blanco.
- **Texto:** tamaño mínimo 12 pt en etiquetas y ejes; sin etiquetas truncadas («Docume…»): ensancha el eje o usa barras horizontales.
- **Prueba rápida:** pasa una captura de cada página a escala de grises o por un simulador de daltonismo externo, comprueba que película y serie se distinguen sin el color, y anota el resultado en la lista de cotejo (paso 9).

## 9. Entrega

1. Exporta **todas** las páginas a PDF (Archivo > Exportar > PDF) como `dashboard/Visualizacion_EP5.pdf`, con la Página 1 mostrando sus tarjetas, y guarda el `.pbix` como `dashboard/Visualizacion_EP5.pbix`. Elimina los archivos EP3 solo cuando los EP5 estén verificados.
2. En el `README.md`, cambia la ruta del dashboard a `dashboard/Visualizacion_EP5.pbix` (hoy dice `Visualizacion_streamview.pbix`, que no existe).
3. Completa y guarda la **lista de control antes de publicar** (clase 3.3.1) sobre el dashboard final:
   - [ ] El objetivo y el usuario están claros en cada página.
   - [ ] Cada métrica y su denominador están definidos (ficha de KPIs; `n` visible).
   - [ ] Datos, período y cobertura son adecuados (≥ 20 votos, ≥ 30 películas, 2010–2025).
   - [ ] Escalas y comparaciones no distorsionan (ejes con unidad; log donde hay valores extremos).
   - [ ] Hechos e hipótesis se distinguen (página «Decisiones», con confianza).
   - [ ] Cada mejora apoya una decisión concreta.
   - [ ] Las tarjetas coinciden con `cifras_de_control.csv`.
   - [ ] Texto alternativo, orden de lectura y prueba de daltonismo hechos.
