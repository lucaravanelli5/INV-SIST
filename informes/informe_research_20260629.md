# Informe de research — Síntesis temática, macro AR y carteras (29/06/2026)

**Fuentes (lote 29/06).** Prensa internacional: **WSJ** (29/06). Estrategia de casa internacional: **One618 / J. Echagüe** *Weekly Report* ("La rotación que no se ve"), **HSBC AM** *Semanal de Inversiones* ("Magnificent margins", datos al 26/06, leído por rasterización porque el texto venía en imágenes). Macro AR: **BCRA — V. Werning** *Fase 4 del programa económico* (presentación, Fund. Mediterránea, 24/06), **GRIT / W. Stoeppelwerth** *Argentina Stuff #241*, **Balanz** *Estrategia semanal local*, **1816** *Especial: inyectar pesos el día de la subasta*, **PPI/desk** *Resultado de la licitación* (24553), **Balanz** *Lo que viene en la semana*, **IEB / R. Ullúa** *Análisis técnico*. Y un `.docx` ("extras…") con el daily de **1816**, el resumen de **Mariva**, el monitor de **Balanz Research** y una nota internacional de **Regla del 40** (SaaS).

> **Nota.** Herramienta personal de apoyo a la decisión. *No es asesoramiento financiero.* Todo lo que sigue son candidatos razonados para verificar en el screener y el módulo de bonos; no hay llamados a comprar. Las cifras de los desks se reproducen como **referencia** y deben validarse con datos propios. Todos los candidatos se chequean contra `universe_cedears.csv` / `ratios_cedears.csv`.

> **Lo más importante de este lote (leer esto primero).**
> 1. **Por primera vez en varios días, hay informe macro-AR de peso → se activa la Parte B.** Los lotes 24–28/06 eran solo outlooks globales y el cierre era "no muevo la tesis de la curva". Hoy tenemos al **BCRA oficial (Werning)**, **GRIT** y **Balanz local**: hay lectura argentina propia. El sesgo del lote es **de compresión** (ver Parte B).
> 2. **El día político corre a favor del crédito AR.** Renunció **Adorni** (Jefe de Gabinete, investigado por su patrimonio) y asume **Santilli**. Según GRIT, los soberanos abrieron **+15 a +50 pb liderados por el tramo largo**. El riesgo país lleva **dos semanas debajo de 450 pb** (retorno total).
> 3. **El mensaje de equity del lote es "rotación / broadening 2.0", no risk-off.** Junio fue malo para los índices pero **no** fue venta indiscriminada: funcionó la duration, lideraron defensivos (salud, utilities, industriales, bancos) y el equal-weight/quality, mientras se castigó lo más poblado (Mag 7 −9,3%, tech −6,6%). El capex de IA sigue, pero **el mejor riesgo-retorno está en la infraestructura/energía que habilita el ciclo, no en los nombres obvios**.
> 4. **Corrección de un dato del informe del 23/06:** allí dije que las generadoras/utilities puras (VST, CEG, NEE) "no tienen CEDEAR". **Sí lo tienen** — están en `universe_cedears.csv` (VST, CEG, NEE) con ratios cargados, y de hecho ya hay una cartera simulada con VST. Eso hace que el flanco más fuerte de la tesis de IA (la energía como límite) sea **mucho más accesible** de lo que decía aquel informe.
> 5. **Aviso estructural (tapa del WSJ):** el complejo de **ETFs apalancados de un solo nombre / semis** es hoy un acelerador procíclico. ~USD 220 bn de activos (récord), ~USD 300 bn en derivados desde fin de marzo, Direxion 3X semis **+700%** mar–jun, y en Corea el Kospi llegó a **−31% en una sola rueda**. El trade de memoria/semis más crowded es el más expuesto a un *unwind* violento.

---

## Parte A — Análisis temático (WSJ + One618 + HSBC + Regla del 40 → CEDEARs)

### Temas de fondo

1. **"La rotación que no se ve": el mercado no se va, pide otro liderazgo.** El hilo de One618 (Echagüe) y HSBC. Junio fue malo en índices (MSCI World −2,5%, S&P −2,8%, EM ~−5%, Corea −11,5%, QQQ −3,6%, Mag 7 −9,3%), **pero** subieron Dow +2,0%, small caps +2,7%, equal-weight +1,6%, quality +2,6%, low-vol +5,9%; y por sector salud +8,7%, utilities +6,3%, industriales +5,6%, bancos +4,9%. En bonos funcionó la duration (TLT +2,0%). Lectura: fue **toma de ganancia en lo más exigido + búsqueda de rezagados**, no salida del riesgo. Si fuera lo segundo, la duration y los defensivos no habrían liderado.

2. **El capex de IA sigue, pero la mejor pata es la infraestructura/energía — y ahora es comprable.** One618 lo dice explícito ("dejar de comprar IA solo por la vía más obvia y poblada… el mejor riesgo-retorno está en utilities, industriales selectivos, semis de calidad, energía eléctrica, data centers y compañías con pricing power"). HSBC dedica el *Foco del mercado* a "Hormigón, cables y flujos de caja": las infraestructuras tras la rotación rinden ~**3,8% de dividendo**, cerca del techo de su rango de 10 años, con ingresos regulados/atados a inflación y vientos de cola estructurales (digitalización, electrificación, desglobalización). **Esta es la corrección clave del lote:** VST/CEG/NEE **sí** están en mi universo, así que el tema se puede expresar directo y no solo vía megacap u OKLO.

3. **El apalancamiento como acelerador procíclico (riesgo, no tesis).** La tapa del WSJ: los ETFs apalancados de un solo nombre/semis movieron el mercado. Micron vía productos apalancados +300%, Direxion 3X semis +700% (mar–jun); ~USD 300 bn en derivados ligados a *single stocks/índices* desde fin de marzo; activos récord ~USD 220 bn; en Corea ~92% son retail y el Kospi cayó −31% en una rueda el 5/06. Es el contrapunto del Tema 1: el **trade de memoria/semis más poblado y extendido** es el que puede deshacerse de golpe.

4. **Régimen de tasas: Fed Warsh dura, pero el petróleo abre la puerta a no subir.** Warsh quitó *forward guidance*; el mercado pricea una **suba antes de fin de 2026** (la mitad de los *dots* ya la anota) y el DXY tocó **máximo de 13 meses** (~101,3). UST 2a ~4,09% / 10a ~4,37%. **La contracara:** el crudo cayó por tercera semana (WTI USD 69,23 −3,7%; Brent USD 71,99 −4,3%), lo cual es desinflacionario y podría evitar la suba (el *bull case* de las casas). La tensión: el USD fuerte sugiere que el mercado prioriza el riesgo de tightening sobre la mejora de inflación.

5. **China resetea la carrera de IA + economía a dos velocidades.** WSJ: el modelo de **Zhipu (GLM)** acorta distancia con los modelos de EE.UU. (todavía rezagado en hallar bugs de seguridad, pero la brecha se achica). HSBC: China "de los ladrillos a los bytes" — IA, nuevas energías y manufactura avanzada lideran; la vieja economía (inmobiliario) queda rezagada. Riesgo geopolítico para equipos/semis y, a la vez, oportunidad en la nueva economía china barata.

6. **(Overlay de calidad) La Regla del 40 en SaaS.** Del `.docx`: combina crecimiento + rentabilidad. Sirve para rankear el *sleeve* de software por **calidad de crecimiento**, no por crecer porque sí.

### Candidatos con CEDEAR (todos a validar en el screener)

| Tema | Tickers (con CEDEAR) | Tesis y qué chequear |
|---|---|---|
| **Energía / "el límite de la IA"** | **VST, CEG, NEE**, GE, ENB, **XLU**, **XLI**, OKLO, NXE, CCJ, URA | El flanco más fuerte del lote y **ahora comprable** (VST/CEG/NEE están en el universo). Generación + eléctrica + nuclear para data centers. Chequear que la corrida no las dejó caras: P/E fwd, FV/EBITDA, deuda. OKLO/NXE = pre-ingresos, especulativos. |
| IA — semis de calidad | TSM, AVGO, MRVL, **ALAB**, AMAT, ASML | La parte de infra que "merece" el capex. **Ojo con lo más crowded (MU)** por el riesgo de *unwind* apalancado del Tema 3. Chequear P/E fwd vs. crecimiento, margen, FV/EBITDA, exposición China. |
| Megacap quality (Regla del 40) | MSFT (79), ORCL (81), GOOGL (72), PLTR (108), CRM (43), NOW (44), INTU (44), PANW (47), ADBE (49) | "Dueños del capex" + monetización de IA, varios con de-rating. Rankear por P/E fwd vs. su historia; mirar ROE y margen. *(Los Rule-of-40 fuertes **sin** CEDEAR quedan abajo.)* |
| Rotación a rezagados/defensivos | salud (JNJ, UNH, MRK, ABBV, LLY), bancos (JPM, BAC, C, GS, MS), industriales (CAT, DE, HON, GE), quality/low-vol (SPHQ, VIG, RSP) | El liderazgo de junio. Chequear Div.Yield (salud/bancos), P/E fwd, ROE. |
| China nueva economía | BABA, BIDU, PDD, JD, NTES | Barata, opcionalidad de IA local; riesgo regulatorio/geopolítico. Chequear P/E y caja neta. |
| **AR equity (puente con Parte B)** | YPF, VIST, PAM, TGS, GGAL, BMA, BBAR, SUPV, CEPU, EDN | **YPF**: ingreso de **Eni + XRG** al proyecto **Argentina GNL** (32% c/u, YPF 36%) valida Vaca Muerta = tesis de **volumen**. *Caveat:* crudo bajo pega al margen del *equity/crédito*. Bancos/utilities se benefician si comprime el riesgo país (ver Parte B). |

**Rule-of-40 fuertes SIN CEDEAR** (no comprables en tu universo, los marco igual): **ADSK** (41), **AXON** (44), **FTNT** (50), **VEEV** (52), **FICO** (74), **DOCN** (74), **APP** (123). *(Verificado contra `universe_cedears.csv`.)*

### Shortlist priorizada (máx. 7)

1. **VST / CEG / NEE** — la pata de "energía para IA", ahora **con CEDEAR**. Expresión más limpia del Tema 2 (One618 + HSBC). Chequear que el rally previo no las dejó caras.
2. **TSM / AVGO** — semis de calidad, menos *crowded* que MU; capturan el capex sin el riesgo de *unwind* apalancado del Tema 3.
3. **MSFT / ORCL** — megacap quality (Regla del 40 alta) con de-rating; "dueños del capex".
4. **Sleeve defensivo/rotación: JNJ o UNH (salud) + JPM (bancos)** — el liderazgo real de junio; el broadening que piden las casas.
5. **GOOGL** — de-rating + Regla del 40 72%; banca el riesgo de fuga de talento ya marcado.
6. **YPF** — único puente Parte A↔B: el deal de GNL con Eni/XRG es tesis de volumen. *Caveat* crudo bajo.
7. **BABA o PDD** — nueva economía china, barata; riesgo geopolítico, tamaño chico de posición.

### Riesgos y señales en contra

- **El *unwind* apalancado (WSJ) es el riesgo nº1 del mes.** Un nombre que sube +16% en una rueda (ver ALAB en las carteras, Parte C) es exactamente lo que puede deshacerse igual de rápido. Las **agresivas concentradas** son las más expuestas.
- **Régimen Fed hawkish:** si no aparece la desinflación que justifique "no subir", growth + duration + EM sufren juntos. DXY en máximos.
- **El Merval está en corrección técnica (IEB):** Merval USD falló la salida alcista (cayó de 2272 a 1996 USD); riesgo a 1840–1750, incluso 1630–1600. El S&P500 también lo ven corrigiendo a 7000–6750. **La cinta de corto juega en contra aunque la lectura estructural sea constructiva.**
- **Sesgo de fuente:** One618/HSBC son outlooks de casa (hablan su libro). Direccionalmente útiles; **cada ratio se valida en el screener**.
- **Las utilities/infra ya corrieron con este tema**: el riesgo de comprar el pico está; chequear valuación antes de perseguir.

---

## Parte B — Macro argentino (BCRA / GRIT / Balanz → bonos + acciones)

> **Se activa la Parte B** (a diferencia de los lotes 24–28/06): hay informe AR-específico, y de peso (BCRA oficial). Sesgo del lote: **compresión**, con el matiz cíclico de un USD fuerte y una cinta global de corto adversa.

### Drivers macro

1. **Ancla fiscal → ancla externa (la tesis central del BCRA, Fase 4).** Werning: el equilibrio fiscal es "el ancla del equilibrio externo (cuenta corriente)", lo que elimina estructuralmente la "restricción externa". El "crowding in" impositivo liberó **>2,5 p.p. del PIB** (DEX, aranceles, PAIS, Bienes Personales) y el crédito bancario al privado se **duplicó**.
2. **Sector externo fuerte y progresando más rápido de lo esperado.** Superávit comercial base caja **USD 4.322 mn** en mayo (récord desde sep-25), el BCRA compró **USD 2.601 mn** y las reservas subieron a la zona de **USD 47–48 mil mn** (GRIT cita USD 48.193 mn; Mariva USD 47.081 mn — distintas definiciones/fechas, ambas como referencia). Compra de RRII **>USD 11 mil mn** en 2026. La demanda de USD del retail sigue, pero **~90% queda onshore** (alimenta intermediación, no drena reservas).
3. **"Capacidad de fuego" patrimonial reseteada.** Encajes: respaldo en efectivo de depósitos de **4% (2023) → 11/12%** (histórico). Resultado del BCRA 2025 el mayor en 20 años; PN +66%. Además de la compra spot, **>USD 20 mil mn** de liquidez cambiaria extra (libro de futuros desarmado desde el pico de USD 8 mil mn, swaps disponibles a mediados de 2026, refinanciación de repos por USD 6 mil mn).
4. **Desinflación consolidándose.** Expectativas a 12 meses ancladas en **~23%** (REM); GRIT estima IPC junio **~1,8%** ayudado por el desplome de alimentos y commodities. El BCRA insiste en que los saltos recientes (carne, combustibles) son **temporarios**.
5. **Política a favor del crédito.** Renuncia de **Adorni** y ascenso de **Santilli** a Jefe de Gabinete: GRIT lo lee como *upgrade* (operador político, mejor "pegamento" PRO–LLA de cara a 2027) y los soberanos abrieron **+15/+50 pb, liderados por el tramo largo**.

### Implicancia para el RIESGO PAÍS

**Presión a la baja (compresión).** Riesgo país **< 450 pb** dos semanas seguidas (retorno total); el BCRA muestra el diferencial **EMBIG argentino − LATAM** estrechándose. Drivers a favor: fiscal + externo + patrimonio del BCRA + el *trigger* político de hoy. **Contras (cíclicos):** DXY en máximo de 13 meses → viento de frente para EM; ampliación de spreads de crédito EM; el Merval en corrección y la cinta global risk-off de corto.

### Bajada a los bonos (mi universo: 11 soberanos GD/AL + 6 BOPREAL + 7 ONs)

- **Si manda la compresión, el tramo largo se beneficia más** por duration/convexidad. GRIT lo confirma hoy: el *rally* por Adorni lo lideró el **bucket de duration larga**. En mi módulo, eso apunta a **GD35 / GD38 / GD41** sobre GD30/AL30 *si* el riesgo país sigue perforando 450. El monitor de Balanz (en el `.docx`) prefiere **GD38** en ley extranjera y ve **AL30/AE38** con spread de legislación atractivo (ley local descontando un escenario "excesivamente pesimista").
- **BOPREAL con respaldo de fundamento:** el BCRA dice que con el último pago quedó **saneado el 50%** del problema de deuda comercial privada de dic-2023 → constructivo para el crédito BOPREAL.
- **ONs:** el ciclo de crédito corporativo "arrancó en el segmento de dólares" (BCRA). Las ONs de energía (YPF y cía.) se apoyan en el volumen de Vaca Muerta (deal GNL Eni/XRG), con el *caveat* del crudo bajo sobre los márgenes.
- **Matiz de timing:** la compresión es la tesis de fondo; la **cinta de corto** (USD fuerte, EM con spreads más anchos, Merval corrigiendo) puede dar mejor punto de entrada. No es señal de vender la tesis, sí de no perseguir.

> **Higiene de datos (regla del proyecto):** cualquier bono fuera de los 24 del universo que aparezca en estos informes (p. ej. los hard-dollar **AO27/AO28/Bonar 28** que el Tesoro está colocando, o provinciales **SFD34/BA37** que menciona Balanz) requiere **captura del Cashflow + Datos técnicos de Balanz y validación de TIR** antes de cargarse. Las TIR/spreads citados arriba son **referencias de los desks**, no datos propios.

### Bajada a las acciones AR

- **Bancos (GGAL, BMA, BBAR, SUPV):** los más apalancados a la compresión de riesgo país y al renacer del crédito en pesos (el BCRA dice que la mora bancaria **tocó pico en 2T26**). Chequear P/BV y ROE.
- **Energía (YPF, VIST, PAM, TGS):** tesis de **volumen** (Vaca Muerta/GNL), no de precio. Crudo bajo es viento en contra del *equity*. Mirar deuda/capex y sensibilidad al Brent.
- **Utilities/reguladas (CEPU, EDN):** se benefician de tasas reales más normales y compresión; mirar Div.Yield y FV/EBITDA.
- **Ojo margen (micro del BCRA):** los márgenes que existían con riesgo país >2.000 pb **no se preservan** con riesgo país <500 pb. El *equity* AR pasa de "ganar por inflación/financiero" a "ganar por volumen/productividad" — sesga hacia compañías con capacidad operativa real, no a las que vivían de la remarcación.

---

## Parte C — Seguimiento de carteras simuladas

> **Caveats importantes.** (1) Precios **actualizados** desde la app antes de correr el digest. El aviso que imprime el script ("los precios son el último cierre en tu DB…") es **fijo**: sale siempre, hayas actualizado o no, así que **no** significa que estén viejos. Única salvedad de *timing*: "último cierre" = el más reciente disponible — si corriste el digest el lunes antes del cierre de EE.UU. es el del **viernes 26**, si fue después es el del **lunes 29** (ambos son dato fresco). (2) Las **ventanas no son idénticas** (inicios 26, 27 y 29/06): comparar retornos absolutos entre carteras no es 1:1; el alpha vs. SPY de cada ventana sí. (3) Es una **simulación**. No invento números: uso los del digest.

| Cartera | Inicio | Retorno | SPY (ventana) | Alpha | Mejor / Peor |
|---|---|---|---|---|---|
| **Agresiva 3M jun-26(CP)** (IA infra, v2 score) | 27/06 | **+3,8%** | +1,6% | **+2,2%** | ALAB +16,4% / YPF −0,2% |
| **Agresiva 3M jun-26** (IA infra) | 26/06 | **+3,2%** | +1,6% | **+1,6%** | ALAB +16,4% / CRWV −1,1% |
| **Tesis research jun-26** (temático + macro AR) | 26/06 | **+2,7%** | +1,6% | **+1,1%** | ALAB +16,4% / MSFT −1,2% |
| Agresiva 3M jun-26(CP+VST) (IA infra + energía) | 29/06 | −0,0% | +0,0% | −0,0% | ALAB +0,0% / VST −0,1% |
| Personal Balanz (real, privada · USD 894) | 29/06 | −0,0% | +0,0% | −0,0% | MRVL +3,1% / MELI −1,2% |

*(Las dos últimas arrancaron hoy: ventana ~0, no se leen todavía.)*

### Evolución (vs. informe del 27-28/06)

- **Se dio vuelta el cuadro: ahora las tres tienen alpha POSITIVO y las agresivas lideran.** En el informe anterior, "Tesis research" era la única con alpha positivo (+0,2%) y las agresivas perdían (−1,6% / −1,3%) por MU (−6,3%, el peor en las tres). Hoy: **CP +2,2%, base +1,6%, Tesis +1,1%** de alpha, y el orden se invirtió — **gana la concentrada**.
- **El driver es uno solo: ALAB +16,4%, mejor en las tres.** El nombre de infraestructura/networking de IA ripeó y se llevó puestas a las carteras que más lo pesan (las agresivas). **MU desapareció del puesto de "peor"**: los nuevos peores (MSFT −1,2%, CRWV −1,1%, YPF −0,2%) son ruido. O sea, el *drag* de memoria del informe pasado se revirtió y lo reemplazó el *push* del acelerador (ALAB).
- **Con precios actualizados, el vuelco es real, no artefacto.** El aviso "último cierre" del script es fijo y no implica datos viejos. La única salvedad es de *timing*: según corrieras el digest antes o después del cierre de EE.UU. del lunes, el rebote de ALAB / la recuperación de MU son de **una** sesión (viernes 26) o **dos** (hasta el lunes 29). En ambos casos el dato es fresco y la reversión de alpha es genuina.

### Lectura del día

La tesis del Parte A que se reflejó es **literal**: el capex de IA premiando a la **infraestructura** (ALAB) por encima de los nombres obvios. Pero hay una ironía que conecta con el WSJ: **la cartera que más gana hoy (la agresiva concentrada) es justo la más expuesta al riesgo nº1 del lote** — el *unwind* apalancado de un solo nombre. El mensaje de One618/HSBC es **broadening**: la cartera "CP+VST" (que suma energía) y un eventual *sleeve* defensivo/rezagado van en esa dirección.

### Señales (TP/STOP)

**Ninguna** marcó el digest hoy (en ninguna cartera). No son órdenes; son disparadores para revisar.

### Decisión (la tomo yo)

- **El vuelco de alpha es real** (precios actualizados): la agresiva concentrada gana esta ventana. Pero es la **más expuesta al riesgo nº1 del lote** — el *unwind* apalancado de un solo nombre (WSJ). Esa es la tensión a vigilar, no un problema de datos.
- Mirar si **ALAB sostiene** o si es la clase de movida que el WSJ advierte que se deshace rápido. Si la concentración en un nombre +16% me incomoda, **el broadening (VST/CEG/NEE + defensivos)** es la cobertura natural.
- Del lado AR: con la Parte B activada en modo compresión, **chequear en el módulo de bonos** dónde quedó la curva GD/AL hoy tras la noticia de Santilli (el tramo largo es el que más se movería) — y, si me interesa sumar algún hard-dollar nuevo del Tesoro (AO28/Bonar 28), **capturar Cashflow + validar TIR** antes de cargarlo. Nada mecánico.

---

> *Recordatorio: herramienta personal de apoyo a la decisión. No es asesoramiento financiero. Las señales del digest son disparadores para revisar, no órdenes; el score del screener es un ranking heurístico; las carteras son simulaciones. Las decisiones de inversión las tomo yo.*
