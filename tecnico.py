"""
tecnico.py  —  Solapa "📈 Técnico / Tendencia"
================================================
Segunda lente sobre el MISMO universo de CEDEARs del tablero: en vez de mirar
fundamentals, mira TENDENCIA (Weinstein / Wyckoff simplificado). Tres piezas:

  1. Scanner técnico   : Stage de Weinstein (WMA), fuerza relativa vs SPY, ATR,
                         niveles de stop/TP por ATR, ratio de volumen y distancia
                         al stop — para cada ticker del universo.
  2. Convergencia      : el mismo Stage/RS calculado en SEMANAL y en DIARIO, con
                         un flag ⭐ cuando coinciden (la señal más robusta).
  3. Calculadora sizing: tamaño de posición por riesgo fijo (2% del capital),
                         acotado por límite de diversificación. Pura aritmética.

REGLA DEL PROYECTO (respetada): NO se inventan datos. Todos los indicadores se
calculan a partir del OHLCV real que baja yfinance. Si a un ticker le falta
historia, se saltea y se avisa (como hacen los scripts de carteras).

ESTO NO ES ASESORAMIENTO. Los "setups" son disparadores mecánicos para revisar,
no órdenes de compra. Las decisiones las toma el usuario.

El OHLCV se cachea en research.db en tablas nuevas (ohlc_tec / ohlc_tec_meta),
separadas de la tabla `prices` del resto del tablero: esta solapa no toca nada
de lo que ya existe. Si un día no te gusta, borrás esta solapa y listo.

Requisitos: los que ya tenés (streamlit, yfinance, pandas, numpy).
"""

import datetime as _dt
import sqlite3

import numpy as np
import pandas as pd
import streamlit as st

import portfolio_research as pr  # reutilizamos universo, benchmark y la DB

# --- Constantes --------------------------------------------------------------
BENCH = getattr(pr, "BENCHMARK", "SPY")   # benchmark de RS (el SPY del tablero)
PERIOD = "2y"                             # historia diaria a bajar (da ~100 semanas)
CHUNK = 40                                # lotes de descarga (igual que update_prices)

# Parámetros por horizonte. "largo" corre sobre barras SEMANALES; "corto" sobre
# DIARIAS. Son los multiplicadores del manual de Weinstein.
HORIZ = {
    "largo": {  # semanal — WMA30
        "wma_main": 30, "slope_lb": 4,
        "atr_mult_stop": 2.0, "atr_mult_tp1": 3.5, "atr_mult_tp2": 5.5,
        "rs_window": 26,          # ~6 meses en semanas
    },
    "corto": {  # diario — WMA20
        "wma_main": 20, "slope_lb": 5,
        "atr_mult_stop": 1.5, "atr_mult_tp1": 2.5, "atr_mult_tp2": 4.0,
        "rs_window": 63,          # ~3 meses en ruedas
    },
}

SLOPE_FLAT = 0.3   # umbral de pendiente "plana" (%) del manual
PCT_FLAT = 3.0     # umbral precio-vs-WMA "alrededor de" (%) del manual
VOL_MIN = 1.5      # ratio de volumen que confirma señal


# =============================================================================
# --- Cache de OHLCV en research.db (tablas propias) --------------------------
# =============================================================================
def _ensure_tables(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS ohlc_tec (
        ticker TEXT NOT NULL, date TEXT NOT NULL,
        open REAL, high REAL, low REAL, close REAL, volume REAL,
        PRIMARY KEY (ticker, date))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS ohlc_tec_meta (
        ticker TEXT PRIMARY KEY, updated_at TEXT)""")


def update_ohlc(tickers=None, period=PERIOD, chunk=CHUNK, force=False, log=print):
    """Baja OHLCV diario del universo (batched) y lo cachea. Reanudable: saltea
    lo ya bajado hoy salvo force=True. Devuelve (bajados, salteados, fallidos)."""
    try:
        import yfinance as yf
    except ImportError:
        log("Falta yfinance:  pip install yfinance"); return (0, 0, 0)

    tickers = tickers or pr.load_universe()   # incluye el benchmark
    today = _dt.date.today().isoformat()
    bajados = salteados = fallidos = 0

    with pr.get_conn() as c:
        _ensure_tables(c)
        if not force:
            done = {r[0] for r in c.execute(
                "SELECT ticker FROM ohlc_tec_meta WHERE updated_at LIKE ?",
                (today + "%",)).fetchall()}
        else:
            done = set()

    pend = [t for t in tickers if t not in done]
    salteados = len(tickers) - len(pend)

    for i in range(0, len(pend), chunk):
        batch = pend[i:i + chunk]
        try:
            data = yf.download(batch, period=period, auto_adjust=True,
                               progress=False, group_by="ticker", threads=True)
        except Exception as e:
            log(f"  [error lote] {batch[:3]}...: {e}"); fallidos += len(batch); continue

        for t in batch:
            try:
                sub = data[t] if len(batch) > 1 else data
                sub = sub[["Open", "High", "Low", "Close", "Volume"]].dropna(
                    subset=["Close"])
                rows = [(t, idx.strftime("%Y-%m-%d"),
                         _f(r.Open), _f(r.High), _f(r.Low),
                         _f(r.Close), _f(r.Volume))
                        for idx, r in sub.iterrows()]
                if not rows:
                    fallidos += 1; continue
                with pr.get_conn() as c:
                    c.executemany(
                        "INSERT OR REPLACE INTO ohlc_tec VALUES (?,?,?,?,?,?,?)", rows)
                    c.execute("INSERT OR REPLACE INTO ohlc_tec_meta VALUES (?,?)",
                              (t, _dt.datetime.now().strftime("%Y-%m-%d %H:%M")))
                bajados += 1
            except Exception as e:
                log(f"  [skip] {t}: {e}"); fallidos += 1
        log(f"  OHLCV {min(i + chunk, len(pend))}/{len(pend)}")
    return (bajados, salteados, fallidos)


def _f(x):
    try:
        v = float(x)
        return v if np.isfinite(v) else None
    except Exception:
        return None


def load_ohlc(conn, ticker):
    """DataFrame OHLCV (index=fecha) del cache. Vacío si no hay datos."""
    df = pd.read_sql_query(
        "SELECT date, open, high, low, close, volume FROM ohlc_tec "
        "WHERE ticker=? ORDER BY date", conn, params=(ticker,))
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")


# =============================================================================
# --- Indicadores (matemática pura sobre el OHLCV) ----------------------------
# =============================================================================
def wma(series, n):
    """Media móvil ponderada lineal (pesos 1..n, más peso a lo reciente)."""
    w = np.arange(1, n + 1)
    return series.rolling(n).apply(lambda x: np.dot(x, w) / w.sum(), raw=True)


def atr(df, n=14):
    """Average True Range de n períodos sobre un DataFrame con high/low/close."""
    h, l, cprev = df["high"], df["low"], df["close"].shift(1)
    tr = pd.concat([(h - l).abs(),
                    (h - cprev).abs(),
                    (l - cprev).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def to_weekly(df):
    """Resamplea barras diarias a semanales (viernes)."""
    if df.empty:
        return df
    w = df.resample("W-FRI").agg({"open": "first", "high": "max",
                                  "low": "min", "close": "last",
                                  "volume": "sum"}).dropna(subset=["close"])
    return w


def classify_stage(pct_vs_wma, slope):
    """Etapa de Weinstein a partir de (precio vs WMA en %) y pendiente WMA en %.
    Simplificación fiel a los umbrales del manual (±0.3% slope, ±3% precio)."""
    if pct_vs_wma is None or slope is None or np.isnan(pct_vs_wma) or np.isnan(slope):
        return "s/d"
    if pct_vs_wma > 0 and slope > SLOPE_FLAT:
        # Avance. "Early" = recién por encima y momentum aún tibio.
        if pct_vs_wma < PCT_FLAT and slope <= 1.0:
            return "2 Early"
        return "2 Avance"
    if pct_vs_wma < 0 and slope < -SLOPE_FLAT:
        return "4 Declive"
    if abs(slope) <= SLOPE_FLAT and abs(pct_vs_wma) <= PCT_FLAT:
        return "1 Base"
    return "3 Techo"


def _slope_pct(wma_series, lb):
    """Pendiente de la WMA en % entre la última barra y lb barras atrás."""
    s = wma_series.dropna()
    if len(s) <= lb or s.iloc[-1 - lb] == 0:
        return np.nan
    return (s.iloc[-1] / s.iloc[-1 - lb] - 1) * 100


def _ret_window(close, window):
    """Retorno % de las últimas `window` barras."""
    s = close.dropna()
    if len(s) <= window or s.iloc[-1 - window] == 0:
        return np.nan
    return (s.iloc[-1] / s.iloc[-1 - window] - 1) * 100


def _horizon_metrics(bars, bench_bars, cfg):
    """Calcula Stage / slope / RS para un horizonte (barras diarias o semanales).
    Devuelve dict o None si no hay historia suficiente."""
    p = cfg["wma_main"]
    if bars is None or len(bars) < p + cfg["slope_lb"] + 1:
        return None
    close = bars["close"]
    wma_main = wma(close, p)
    price = close.iloc[-1]
    wma_last = wma_main.iloc[-1]
    if np.isnan(wma_last) or wma_last == 0:
        return None
    pct_vs = (price / wma_last - 1) * 100
    slope = _slope_pct(wma_main, cfg["slope_lb"])
    stage = classify_stage(pct_vs, slope)

    rs = np.nan
    if bench_bars is not None and len(bench_bars) > cfg["rs_window"]:
        r_act = _ret_window(close, cfg["rs_window"])
        r_bch = _ret_window(bench_bars["close"], cfg["rs_window"])
        if not (np.isnan(r_act) or np.isnan(r_bch)):
            rs = r_act - r_bch
    return {"stage": stage, "slope": slope, "pct_vs_wma": pct_vs, "rs": rs,
            "price": price}


def scan_universe(tickers=None):
    """Recorre el universo y arma la tabla técnica. NO baja datos: usa el cache.
    Los tickers sin OHLCV o sin historia suficiente se saltean (se cuentan aparte)."""
    tickers = tickers or [t for t in pr.load_universe() if t != BENCH]
    with pr.get_conn() as c:
        _ensure_tables(c)
        bench_d = load_ohlc(c, BENCH)
        bench_w = to_weekly(bench_d) if not bench_d.empty else bench_d

        rows, sin_datos = [], 0
        for t in tickers:
            d = load_ohlc(c, t)
            if d.empty:
                sin_datos += 1; continue
            w = to_weekly(d)
            m_sem = _horizon_metrics(w, bench_w, HORIZ["largo"])
            m_dia = _horizon_metrics(d, bench_d, HORIZ["corto"])
            if m_dia is None:            # sin diario no hay nada que mostrar
                sin_datos += 1; continue

            price = m_dia["price"]
            atr_d = atr(d, 14).iloc[-1]
            cfg = HORIZ["corto"]
            stop = tp1 = tp2 = dist = np.nan
            if not np.isnan(atr_d):
                stop = price - atr_d * cfg["atr_mult_stop"]
                tp1 = price + atr_d * cfg["atr_mult_tp1"]
                tp2 = price + atr_d * cfg["atr_mult_tp2"]
                dist = (price - stop) / price * 100 if price else np.nan

            vol = d["volume"]
            vol_ratio = np.nan
            if vol.notna().sum() > 20 and vol.tail(20).mean():
                vol_ratio = vol.iloc[-1] / vol.tail(20).mean()

            st_sem = m_sem["stage"] if m_sem else "s/d"
            rs_sem = m_sem["rs"] if m_sem else np.nan
            st_dia, rs_dia = m_dia["stage"], m_dia["rs"]

            conv = (str(st_sem).startswith("2") and str(st_dia).startswith("2")
                    and (rs_sem or 0) > 0 and (rs_dia or 0) > 0)

            # Flag de setup — SOLO para revisar, no es una orden.
            if conv and (vol_ratio or 0) >= VOL_MIN:
                setup = "⭐ Convergente + Vol OK — revisar"
            elif conv:
                setup = "⭐ Convergente — revisar"
            elif str(st_dia).startswith("2 Avance"):
                setup = "Stage 2 diario — mirar"
            else:
                setup = "—"

            score = (1 if conv else 0) * 1000 + (rs_dia if not np.isnan(rs_dia) else -999)

            rows.append({
                "Ticker": t, "Precio": price,
                "Stage_sem": st_sem, "Stage_día": st_dia,
                "RS_sem": rs_sem, "RS_día": rs_dia, "Conv": "⭐" if conv else "",
                "ATR_día": atr_d, "Stop": stop, "TP1": tp1, "TP2": tp2,
                "DistStop%": dist, "VolRatio": vol_ratio, "Setup": setup,
                "_score": score,
            })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("_score", ascending=False).drop(columns="_score")
    return df, sin_datos


# =============================================================================
# --- Sizing por riesgo (aritmética pura, sin datos externos) -----------------
# =============================================================================
def position_size(capital, price, stop, risk_pct=2.0, max_weight_pct=10.0):
    """Tamaño de posición del manual de Weinstein:
       - riesgo máx en $ = capital * risk_pct%
       - capital que permite el riesgo = riesgo$ / (distancia % al stop)
       - tope de diversificación = capital * max_weight_pct%
       - capital efectivo = el MENOR de los dos
    Devuelve dict con el desglose. No decide nada: solo calcula."""
    out = {"ok": False, "msg": ""}
    if price <= 0 or stop <= 0 or stop >= price:
        out["msg"] = "El stop tiene que ser positivo y menor al precio."
        return out
    dist_pct = (price - stop) / price          # fracción, ej 0.06
    riesgo_ars = capital * risk_pct / 100
    cap_por_riesgo = riesgo_ars / dist_pct
    cap_por_divers = capital * max_weight_pct / 100
    cap_efectivo = min(cap_por_riesgo, cap_por_divers)
    manda = "riesgo" if cap_por_riesgo <= cap_por_divers else "diversificación"
    shares = int(cap_efectivo // price)
    out.update(ok=True, dist_pct=dist_pct * 100, riesgo_ars=riesgo_ars,
               cap_por_riesgo=cap_por_riesgo, cap_por_divers=cap_por_divers,
               cap_efectivo=cap_efectivo, manda=manda, shares=shares,
               perdida_max=shares * (price - stop))
    return out


# =============================================================================
# --- UI (Streamlit) ----------------------------------------------------------
# =============================================================================
@st.cache_data(show_spinner=False)
def _scan_cached(token):
    """token = fecha + Nº de tickers; cambia => recalcula. Botón 'Recalcular' abajo."""
    return scan_universe()


def _fmt(df):
    """Formato de números para la tabla (sin romper el orden ni el filtrado)."""
    style = {
        "Precio": "{:,.2f}", "RS_sem": "{:+.1f}", "RS_día": "{:+.1f}",
        "ATR_día": "{:,.2f}", "Stop": "{:,.2f}", "TP1": "{:,.2f}",
        "TP2": "{:,.2f}", "DistStop%": "{:.1f}", "VolRatio": "{:.2f}",
    }
    return df.style.format({k: v for k, v in style.items() if k in df.columns},
                           na_rep="—")


def render():
    st.subheader("📈 Técnico / Tendencia (Weinstein / Wyckoff)")
    st.caption("Segunda lente sobre el universo de CEDEARs: mira TENDENCIA, no "
               "fundamentals. Todo se calcula del OHLCV real de yfinance. "
               "**No es asesoramiento**: los setups son disparadores para revisar.")

    # --- Barra de datos ---
    c1, c2, c3 = st.columns([1.3, 1, 1.4])
    with c1:
        if st.button("⬇️ Bajar / actualizar OHLCV del universo"):
            box = st.empty(); logs = []

            def _log(m):
                logs.append(str(m)); box.code("\n".join(logs[-12:]))
            with st.spinner("Bajando OHLCV de yfinance (tarda un rato)..."):
                baj, salt, fail = update_ohlc(log=_log)
            _scan_cached.clear()
            st.success(f"OHLCV: {baj} bajados · {salt} ya estaban de hoy · {fail} sin datos")
    with c2:
        if st.button("🔄 Recalcular tabla"):
            _scan_cached.clear()
    with c3:
        st.info("La 1ª vez, apretá **Bajar OHLCV** (usa su propio cache en "
                "research.db; no toca la tabla de precios del tablero).")

    token = _dt.date.today().isoformat() + f"·{len(pr.load_universe())}"
    df, sin_datos = _scan_cached(token)

    st.divider()
    st.markdown("### 1 · Scanner técnico + convergencia")

    if df.empty:
        st.warning("Todavía no hay OHLCV en el cache. Apretá **Bajar / actualizar "
                   "OHLCV del universo** arriba.")
    else:
        f1, f2, f3 = st.columns(3)
        with f1:
            solo_conv = st.checkbox("Solo convergentes ⭐ (Stage 2 en semanal y "
                                    "diario + RS>0)", value=False)
        with f2:
            solo_st2 = st.checkbox("Solo Stage 2 diario", value=False)
        with f3:
            vol_ok = st.checkbox(f"Solo con volumen ≥ {VOL_MIN}x", value=False)

        view = df.copy()
        if solo_conv:
            view = view[view["Conv"] == "⭐"]
        if solo_st2:
            view = view[view["Stage_día"].astype(str).str.startswith("2")]
        if vol_ok:
            view = view[view["VolRatio"] >= VOL_MIN]

        st.caption(f"{len(view)} de {len(df)} tickers · {sin_datos} salteados por "
                   "falta de OHLCV/historia. Ordenado: convergentes primero, luego "
                   "por RS diario. Niveles Stop/TP calculados con ATR diario "
                   "(×1.5 / ×2.5 / ×4.0).")
        st.dataframe(_fmt(view), use_container_width=True, height=520)

        with st.expander("¿Qué significa cada columna? (y las advertencias)"):
            st.markdown(
                "- **Stage_sem / Stage_día**: etapa de Weinstein (1 Base · 2 Early · "
                "2 Avance · 3 Techo · 4 Declive) calculada sobre la WMA30 semanal y "
                "la WMA20 diaria. Solo se opera LONG en Stage 2.\n"
                "- **RS_sem / RS_día**: fuerza relativa vs SPY (retorno del papel − "
                "retorno del SPY, en puntos %). Positiva = le gana al mercado.\n"
                "- **Conv ⭐**: Stage 2 en AMBOS horizontes y RS>0 en ambos. Es la "
                "señal más robusta (convergencia de temporalidades).\n"
                "- **Stop / TP1 / TP2**: niveles por ATR diario. El stop es "
                "referencia de riesgo, no una orden.\n"
                "- **DistStop%**: cuánto caería el precio hasta el stop.\n"
                "- **VolRatio**: volumen de hoy / promedio 20 ruedas. ≥1.5x confirma.\n\n"
                "**Ojo**: el Stage es una simplificación de los umbrales del manual "
                "(±0.3% de pendiente, ±3% de precio vs WMA); no detecta fases "
                "Wyckoff finas (Spring, etc.). Y RS/Stage describen el pasado "
                "reciente: son contexto, no predicción.")

    st.divider()
    st.markdown("### 2 · Calculadora de tamaño de posición (por riesgo)")
    st.caption("El tamaño sale del riesgo máximo por operación, no de cuánto creés "
               "que va a subir. Es aritmética: no usa ni inventa datos de mercado.")

    s1, s2, s3 = st.columns(3)
    with s1:
        capital = st.number_input("Capital total", min_value=0.0,
                                  value=20_000_000.0, step=100_000.0, format="%.0f")
        risk = st.number_input("Riesgo máx por trade (%)", 0.1, 10.0, 2.0, 0.1)
    with s2:
        price = st.number_input("Precio de entrada", min_value=0.0,
                                value=14_000.0, step=100.0, format="%.2f")
        maxw = st.number_input("Tope por posición (% del capital)", 1.0, 100.0, 10.0, 1.0)
    with s3:
        stop = st.number_input("Stop loss", min_value=0.0,
                               value=13_100.0, step=100.0, format="%.2f")

    r = position_size(capital, price, stop, risk, maxw)
    if not r["ok"]:
        st.error(r["msg"])
    else:
        m1, m2, m3 = st.columns(3)
        m1.metric("Distancia al stop", f"{r['dist_pct']:.1f}%")
        m2.metric("Riesgo en $", f"{r['riesgo_ars']:,.0f}")
        m3.metric("Manda el límite de", r["manda"])
        m4, m5, m6 = st.columns(3)
        m4.metric("Capital efectivo a invertir", f"{r['cap_efectivo']:,.0f}")
        m5.metric("Acciones (aprox.)", f"{r['shares']:,}")
        m6.metric("Pérdida máx si salta el stop", f"{r['perdida_max']:,.0f}")
        st.caption(f"Permite el riesgo: {r['cap_por_riesgo']:,.0f} · "
                   f"Tope diversificación: {r['cap_por_divers']:,.0f} · "
                   "se invierte el MENOR de los dos.")

    st.divider()
    st.caption("Metodología: Weinstein (Stage Analysis) + gestión por ATR. "
               "Herramienta personal de research — no es asesoramiento financiero.")
