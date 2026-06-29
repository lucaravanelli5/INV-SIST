# Prompts reutilizables para análisis

Dos prompts para usar en chats del proyecto cuando quiera traer información nueva.
La parte de análisis se hace en el chat; el resultado (candidatos) lo verifico
después en el screener / módulo de bonos del tablero.

---

## 0) Rutina diaria (esto es lo que mando cada día)

Adjunto al chat un .zip con toda la data del día + pego abajo la salida de
daily_digest.py. Mensaje que acompaña: 
Te adjunto un .zip con la data del día (prensa internacional y/o outlooks de casas, y a veces algún informe macro AR) y abajo pego la salida de daily_digest.py (precios ya actualizados). Hacé un informe diario en Markdown con el formato del proyecto (informe_research_AAAAMMDD.md, fecha = la del material):
Abrí el .zip e inventariá cada archivo; si alguno está escaneado, OCRizalo.
Clasificá cada fuente como TEMÁTICA o MACRO ARGENTINA. No inventes el contenido de un archivo que no puedas leer: avisame.
PARTE A: aplicá el prompt (1) temático a las fuentes internacionales.
PARTE B: si hay informe AR-específico, aplicá el prompt (2) macro argentino.
Si NO hay, hacé solo lectura de backdrop global (USD, tasas US, oil, EM) y decí explícitamente que no hay driver AR nuevo y que NO movés la tesis de la curva con este lote.
PARTE C: armá el seguimiento de carteras con el digest de abajo (ver formato más abajo en este archivo).
DIGEST DE HOY:
[pego la salida de daily_digest.py]


## 1) Análisis temático (prensa: FT / WSJ / Bloomberg → CEDEARs)

Para cuando traigo titulares, un artículo o notas de prensa y quiero candidatos
dentro de mi universo de CEDEARs.

```
Sos mi asistente de research para una cartera PERSONAL de CEDEARs (invierto
desde Argentina; solo puedo comprar lo que tiene CEDEAR). Abajo te pego
titulares, un artículo o mis notas de prensa u outlooks de casas (FT / WSJ / Bloomberg, o gestoras tipo JPM / Invesco / DB / HSBC / Standard Chartered).

Tu tarea:
1. Identificá los 2–4 temas o tendencias DE FONDO que aparecen (no la noticia
   del día, sino los movimientos estructurales).
2. Para cada tema, mapeá la cadena de valor: qué tipo de empresas se benefician,
   incluyendo la lógica de "picos y palas" (proveedores, no solo los nombres
   obvios).
3. Traducilo a tickers concretos que tengan CEDEAR. Si un candidato fuerte NO
   tiene CEDEAR, marcámelo igual y aclaralo.
4. Para cada candidato dame: ticker, tema asociado, la tesis en 1–2 líneas
   (por qué el tema lo beneficia) y qué ratios debería chequear yo en mi
   screener antes de decidir (P/E, ROE, deuda, margen, etc.).
5. Cerrá con una lista corta priorizada (máximo 5–7) y, aparte, qué riesgos o
   señales en contra ves.

Reglas:
- No me digas "comprá"; dame candidatos razonados para que yo decida.
- Si algo ya parece descontado en el precio o es pura especulación, decímelo.
- Sé explícito con la incertidumbre. No inventes tickers ni datos que no tengas.

INFO:
[acá pego la información]
```

---

## 2) Análisis macro argentino (JPM / FMI / Banco Mundial / BCRA → bonos + acciones)

Para cuando subo un informe macro sobre Argentina y quiero leer qué implica para
los bonos soberanos/ONs y las acciones argentinas.

```
Sos mi asistente de research macro para mi cartera personal en Argentina.
Abajo te pego un informe o extractos (JPM, FMI, Banco Mundial, BCRA, etc.).

Tu tarea:
1. Resumí los 3–5 drivers macro clave que aparecen (fiscal, reservas, programa
   con el FMI, inflación, política, tipo de cambio).
2. Decime qué implican para el RIESGO PAÍS: ¿presión a la baja (compresión) o a
   la suba? ¿Por qué?
3. Bajalo a los bonos: si la tesis es de compresión, qué tramo de la curva se
   beneficia más (cortos tipo GD30/AL30 vs largos tipo GD35/GD41) y por qué
   (duration, convexidad). Si es de deterioro, lo mismo al revés.
4. Bajalo a las acciones argentinas / CEDEARs de empresas argentinas: qué
   sectores y nombres concretos (bancos, energía, utilities) se beneficiarían o
   sufrirían con ese escenario.
5. Cerrá con los principales riesgos y señales en contra de la tesis.

Reglas:
- No me digas "comprá"; dame el razonamiento para que yo decida.
- Sé explícito con la incertidumbre: la deuda argentina es de alta volatilidad
  y con historial de reestructuraciones.
- No inventes datos ni cifras que no estén en el informe.

INFORME:
[acá pego el texto]
```

## Seguimiento de carteras simuladas (al AAAA-MM-DD)
(se arma con la salida de daily_digest.py; precios ya actualizados)

| Cartera | Inicio | Retorno | SPY (ventana) | Alpha | Mejor / Peor |
|---|---|---|---|---|---|
| Tesis research jun-26 | 2026-06-26 | +X% | +Y% | +Z% | TCK / TCK |
| Agresiva 3M jun-26    | 2026-06-26 | +X% | +Y% | +Z% | TCK / TCK |

**Evolución (vs. informe anterior):** ¿el alpha mejora o empeora día a día? ¿qué
posición es el driver/drag persistente? ¿qué tesis gana en el tiempo, la
diversificada o la agresiva?
**Lectura del día:** ¿qué tesis del Parte A se reflejó hoy en las carteras?
**Señales (TP/STOP):** las que marcó el digest (no son órdenes).
**Decisión (la tomo yo):** qué miro; nada mecánico.