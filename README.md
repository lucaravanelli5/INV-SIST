# Tablero de research financiero

Herramienta **personal** de research para un inversor minorista argentino (broker: Balanz).
Es un tablero local en Python + Streamlit con base SQLite que ayuda a **generar y razonar
ideas de inversión** sobre un universo propio de CEDEARs y bonos argentinos.

> ⚠️ **Esto no es asesoramiento financiero.** Es una herramienta de análisis para uso
> propio. Las decisiones de inversión las toma el usuario. Los datos pueden tener delay
> y no se garantiza su exactitud.

## Qué hace

El tablero (`app.py`) tiene cuatro solapas:

1. **Scorecard** — mide el rendimiento de recomendaciones de analistas (cargadas a mano)
   contra el SPY como benchmark.
2. **Screener** — filtra y rankea ~200 CEDEARs por ratios fundamentales (P/E, ROE, etc.)
   con presets de estrategia.
3. **Precio** — gráfico de precio de una acción/CEDEAR.
4. **Bonos** — 24 bonos argentinos (11 soberanos GD/AL + 6 BOPREAL + 7 ONs) con precio,
   TIR, paridad y duration calculados por la herramienta, curva TIR-vs-duration y riesgo país.

## De dónde salen los datos

- **Acciones / CEDEARs:** precios y ratios vía `yfinance`.
- **Bonos:** precio automático de [data912.com](https://data912.com) (API pública gratuita,
  delay ~2 h). La **TIR, paridad y duration no se descargan**: las calcula la propia
  herramienta a partir del flujo de fondos de cada bono (`cashflows.csv`) más el precio.
- **Riesgo país:** automático desde ArgentinaDatos (gratis, sin clave).
- **Dólar CCL:** dolarapi / ArgentinaDatos.

No se usan claves de API: todas las fuentes son públicas y gratuitas.

## Regla de trabajo

**Nunca inventar datos financieros** (flujos, tickers, TIR). El flujo de fondos de cada
bono se carga una sola vez a partir de la pestaña *Cashflow* de Balanz y se valida: la TIR
que calcula la herramienta tiene que coincidir con la de Balanz (siempre dentro de 1–3 pb).

## Instalación

Requiere Python 3.10+.

```bash
# 1. Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 2. Instalar dependencias
pip install -r requirements.txt
```

## Uso

```bash
# Levantar el tablero
streamlit run app.py

# Actualizar precios/ratios desde la línea de comandos
python portfolio_research.py update
```

La base `research.db` se crea sola la primera vez. Los precios se actualizan con el botón
"Actualizar precios" del tablero o con el comando de arriba.

## Estructura del proyecto

| Archivo | Qué es |
|---|---|
| `app.py` | Tablero Streamlit (UI, las 4 solapas) |
| `portfolio_research.py` | Lógica de datos: DB, descarga de precios, cálculo de TIR/paridad/duration, riesgo país |
| `screener_score.py` | Scoring del screener de CEDEARs |
| `score_cartera.py` | Scoring de carteras |
| `seed_cartera_*.py` | Scripts para sembrar carteras simuladas de ejemplo |
| `daily_digest.py` | Resumen diario |
| `cashflows.csv` | Flujos de fondos de los bonos (validados contra Balanz) |
| `universe_cedears.csv` | Universo de CEDEARs |
| `universe_bonds.csv` | Universo de bonos (24) |
| `ratios_cedears.csv` | Ratios de CEDEARs |
| `prompts_analisis.md` | Prompts reutilizables para el análisis temático/macro |
| `manual_tablero.tex` | Manual del tablero |
| `informe_research_*.md/.tex` | Informes de research generados |

## Nota

Lo que **no** está en el repo (ver `.gitignore`): la base `research.db` y las capturas de
Balanz, por ser datos locales/personales.
