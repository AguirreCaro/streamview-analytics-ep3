// StreamView Analytics - EP5 - Consultas de Power Query para el dashboard
//
// Uso (ver dashboard/GUIA_Power_BI_EP5.md, paso 3):
//   1. Inicio > Transformar datos > Administrar parámetros > Nuevo parámetro
//        Nombre: RutaDatos   Tipo: Texto   Valor actual: la carpeta data\processed de este proyecto, CON la barra final
//        Ejemplo: C:\Users\...\streamview-analytics-ep3-main\data\processed\
//   2. En el Editor de Power Query abre cada consulta existente > Editor avanzado y reemplaza TODO su contenido por
//      la consulta de este archivo que le corresponde. No cambies el nombre de las consultas.
//
// Las consultas entregan las columnas ya con los nombres en español (los mismos que se pusieron en el modelo
// en el paso 2). En Power BI Desktop 2026.10, renombrar una columna en el panel Datos cambia también su nombre
// de origen; por eso la consulta NO debe devolver los nombres antiguos en inglés (si lo hace, Power BI elimina
// las columnas en español, agrega las inglesas y los gráficos se rompen).
//
// Importante: los decimales del CSV usan punto (6.62). El tipo se convierte con la cultura "en-US"; si Power BI lo
// interpretara con la configuración regional de Chile, 6.62 se leería como 662.


// ===================== Consulta de la tabla contenido =====================
let
    Origen = Csv.Document(
        File.Contents(RutaDatos & "streamview_powerbi.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(
        Encabezados,
        {
            {"id_contenido", type text}, {"id_fuente", Int64.Type}, {"tipo", type text}, {"titulo", type text},
            {"genero_principal", type text}, {"pais_principal", type text}, {"idioma", type text},
            {"anio_estreno", Int64.Type}, {"anio_incorporacion", type number}, {"decada", Int64.Type},
            {"rating", type number}, {"votos", Int64.Type}, {"popularidad", type number},
            {"presupuesto_usd", type number}, {"ingresos_usd", type number}, {"roi", type number},
            {"financiero_valido", type logical}, {"rating_confiable", type logical}, {"temporadas", type number}
        },
        "en-US"
    )
in
    Tipos


// ===================== Consulta: genero_puente =====================
let
    Origen = Csv.Document(
        File.Contents(RutaDatos & "genero_puente.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(
        Encabezados,
        {{"id_contenido", type text}, {"tipo", type text}, {"genero", type text}},
        "en-US"
    )
in
    Tipos
