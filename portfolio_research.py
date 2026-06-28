"""
portfolio_research.py  —  MOTOR de datos
========================================
Ahora trabaja sobre un UNIVERSO de tickers cargado desde universe_cedears.csv
(una columna 'ticker'). Editá ese archivo para agregar o sacar acciones.

Terminal:
  pip install yfinance pandas
  python portfolio_research.py update   # baja precios de TODO el universo (en lotes)
  python portfolio_research.py funds      # baja ratios (reanudable; podés cortar y seguir)
  python portfolio_research.py track      # imprime el scorecard

NOVEDAD (26/06/2026): módulo de Carteras Simuladas.
  Tablas nuevas: sim_portfolios, sim_positions.
  Funciones: create_portfolio, list_portfolios, delete_portfolio,
             add_position, remove_position, list_positions,
             compute_portfolio_snapshot, portfolio_history_df.
"""

import os
import sqlite3
import sys
import time
from datetime import datetime

DB_PATH = "research.db"
UNIVERSE_FILE = "data/universe_cedears.csv"
UNIVERSE_BONDS_FILE = "data/universe_bonds.csv"
CASHFLOWS_FILE = "data/cashflows.csv"
BENCHMARK = "SPY"

# Watchlist mínima de respaldo si no está el CSV del universo.
WATCHLIST = ["SPY", "NVDA", "MELI", "YPF", "VIST"]

SEED_RECOMMENDATIONS = [
    ("Allaria CEDEARS",     "2026-06-12", "NVDA", "Buy", 213.5,  None),
    ("Allaria CEDEARS",     "2026-06-12", "GLOB", "Buy", 39.2,   None),
    ("Allaria CEDEARS",     "2026-06-12", "ORCL", "Buy", 202.8,  None),
    ("Allaria CEDEARS",     "2026-06-12", "NU",   "Buy", 13.2,   None),
    ("Allaria CEDEARS",     "2026-06-12", "TSLA", "Buy", 442.5,  None),
    ("Allaria CEDEARS",     "2026-06-12", "MELI", "Buy", 1705.6, None),
    ("Allaria CEDEARS",     "2026-06-12", "TCOM", "Buy", 47.5,   None),
    ("Allaria CEDEARS",     "2026-06-12", "PBR",  "Buy", 18.9,   None),
    ("Allaria CEDEARS",     "2026-06-12", "ISRG", "Buy", 424.6,  None),
    ("Allaria CEDEARS",     "2026-06-12", "TMUS", "Buy", 189.2,  None),
    ("Allaria Equity Val.", "2026-06-16", "YPF",  "Buy", 52.6,   80.0),
    ("Allaria Equity Val.", "2026-06-16", "VIST", "Buy", 68.6,   118.0),
]


# --- Universo ----------------------------------------------------------------
def load_universe():
    """Lee los tickers del CSV. Siempre incluye el benchmark (SPY)."""
    if not os.path.exists(UNIVERSE_FILE):
        return list(WATCHLIST)
    tickers = []
    with open(UNIVERSE_FILE, encoding="utf-8") as f:
        for line in f:
            t = line.split(",")[0].strip().upper()
            if t and t != "TICKER":
                tickers.append(t)
    if BENCHMARK not in tickers:
        tickers.insert(0, BENCHMARK)
    # dedup preservando orden
    seen, out = set(), []
    for t in tickers:
        if t not in seen:
            seen.add(t); out.append(t)
    return out


# --- Base de datos -----------------------------------------------------------
def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS prices (
            ticker TEXT NOT NULL, date TEXT NOT NULL, close REAL NOT NULL,
            PRIMARY KEY (ticker, date))""")
        c.execute("""CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL, rec_date TEXT NOT NULL, ticker TEXT NOT NULL,
            action TEXT NOT NULL, price_at_call REAL, target_price REAL,
            UNIQUE (source, rec_date, ticker))""")
        c.execute("""CREATE TABLE IF NOT EXISTS fundamentals (
            ticker TEXT PRIMARY KEY, updated_at TEXT, name TEXT, sector TEXT,
            market_cap REAL, pe REAL, forward_pe REAL, pb REAL, ev_ebitda REAL,
            roe REAL, profit_margin REAL, dividend_yield REAL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS bonds (
            ticker TEXT PRIMARY KEY, name TEXT, currency TEXT, law TEXT,
            maturity TEXT, price REAL, tir REAL, parity REAL, duration REAL,
            updated_at TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS macro (
            metric TEXT, date TEXT, value REAL, PRIMARY KEY (metric, date))""")
        c.execute("""CREATE TABLE IF NOT EXISTS bond_quotes (
            symbol TEXT PRIMARY KEY, price REAL, pct_change REAL,
            updated_at TEXT)""")

        # --- Migración: columnas nuevas de fundamentals (score v2) -----------
        for _col in ("revenue_growth", "earnings_growth",
                     "debt_to_equity", "current_ratio"):
            try:
                c.execute(f"ALTER TABLE fundamentals ADD COLUMN {_col} REAL")
            except Exception:
                pass  # ya existe

        # --- Carteras simuladas ----------------------------------------------
        c.execute("""CREATE TABLE IF NOT EXISTS sim_portfolios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            label TEXT,
            start_date TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS sim_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio_id INTEGER NOT NULL REFERENCES sim_portfolios(id),
            ticker TEXT NOT NULL,
            entry_date TEXT NOT NULL,
            shares REAL,
            amount_usd REAL,
            price_entry REAL NOT NULL,
            note TEXT)""")


def seed_recommendations():
    with get_conn() as c:
        for row in SEED_RECOMMENDATIONS:
            c.execute("""INSERT OR IGNORE INTO recommendations
                (source, rec_date, ticker, action, price_at_call, target_price)
                VALUES (?, ?, ?, ?, ?, ?)""", row)


# --- Descarga de precios EN LOTES (rápido y suave) ---------------------------
def update_prices(tickers=None, period="1y", chunk=40):
    try:
        import yfinance as yf
    except ImportError:
        print("Falta yfinance:  pip install yfinance pandas"); return
    tickers = tickers or load_universe()
    total = len(tickers)
    for i in range(0, total, chunk):
        batch = tickers[i:i + chunk]
        try:
            data = yf.download(batch, period=period, auto_adjust=True,
                               progress=False, group_by="ticker", threads=True)
            for t in batch:
                try:
                    sub = data[t] if len(batch) > 1 else data
                    closes = sub["Close"].dropna()
                    rows = [(t, idx.strftime("%Y-%m-%d"), float(v))
                            for idx, v in closes.items()]
                    if rows:
                        with get_conn() as c:
                            c.executemany(
                                "INSERT OR REPLACE INTO prices VALUES (?,?,?)", rows)
                except Exception as e:
                    print(f"  [skip] {t}: {e}")
            print(f"  precios {min(i + chunk, total)}/{total}")
        except Exception as e:
            print(f"  [error lote] {batch[:3]}...: {e}")
        time.sleep(1)


# --- Descarga de ratios REANUDABLE -------------------------------------------
def update_fundamentals(tickers=None, limit=None, skip_recent=True):
    """Trae ratios. Reanudable: salteá los ya bajados hoy. 'limit' corta tras N
    nuevos (para hacerlo de a tandas)."""
    try:
        import yfinance as yf
    except ImportError:
        print("Falta yfinance:  pip install yfinance pandas"); return
    tickers = tickers or [t for t in load_universe() if t != BENCHMARK]
    today = datetime.now().strftime("%Y-%m-%d")
    done = 0
    for ticker in tickers:
        if skip_recent:
            with get_conn() as c:
                r = c.execute("SELECT updated_at FROM fundamentals WHERE ticker=?",
                              (ticker,)).fetchone()
            if r and r[0] and r[0].startswith(today):
                continue
        try:
            info = yf.Ticker(ticker).info
            row = (ticker, datetime.now().strftime("%Y-%m-%d %H:%M"),
                   info.get("longName") or info.get("shortName"),
                   info.get("sector"), info.get("marketCap"),
                   info.get("trailingPE"), info.get("forwardPE"),
                   info.get("priceToBook"), info.get("enterpriseToEbitda"),
                   info.get("returnOnEquity"), info.get("profitMargins"),
                   info.get("dividendYield"),
                   info.get("revenueGrowth"), info.get("earningsGrowth"),
                   info.get("debtToEquity"), info.get("currentRatio"))
            with get_conn() as c:
                c.execute("""INSERT OR REPLACE INTO fundamentals
                    (ticker, updated_at, name, sector, market_cap, pe, forward_pe,
                     pb, ev_ebitda, roe, profit_margin, dividend_yield,
                     revenue_growth, earnings_growth, debt_to_equity, current_ratio)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", row)
            done += 1
            print(f"  [ok] {ticker} ({done})")
        except Exception as e:
            print(f"  [error] {ticker}: {e}")
        if limit and done >= limit:
            print(f"  corte tras {limit}. Volvé a correr para seguir.")
            break
        time.sleep(1)
    if not (limit and done >= limit):
        print(f"  listo. Ratios nuevos en esta corrida: {done}")


# --- Consultas auxiliares ----------------------------------------------------
def price_on_or_before(conn, ticker, d):
    r = conn.execute("SELECT close FROM prices WHERE ticker=? AND date<=? "
                     "ORDER BY date DESC LIMIT 1", (ticker, d)).fetchone()
    return r[0] if r else None


def latest_price(conn, ticker):
    return conn.execute("SELECT date, close FROM prices WHERE ticker=? "
                        "ORDER BY date DESC LIMIT 1", (ticker,)).fetchone()


def compute_scorecard(conn):
    bench = latest_price(conn, BENCHMARK)
    bench_now = bench[1] if bench else None
    recs = conn.execute("""SELECT source, rec_date, ticker, action,
        price_at_call, target_price FROM recommendations
        ORDER BY rec_date, ticker""").fetchall()
    out = []
    for source, rec_date, ticker, action, p0, target in recs:
        now = latest_price(conn, ticker)
        if now is None or not p0:
            out.append(dict(Fuente=source, Fecha=rec_date, Ticker=ticker,
                            PrecioRec=p0, Actual=None))
            continue
        p_now = now[1]
        ret = (p_now / p0 - 1) * 100
        bench0 = price_on_or_before(conn, BENCHMARK, rec_date)
        if bench0 and bench_now:
            bench_ret = (bench_now / bench0 - 1) * 100
            alpha = ret - bench_ret
        else:
            bench_ret = alpha = None
        to_target = ((p_now - p0) / (target - p0) * 100) if (target and target != p0) else None
        out.append(dict(
            Fuente=source, Fecha=rec_date, Ticker=ticker,
            PrecioRec=round(p0, 2), Actual=round(p_now, 2),
            **{"Ret%": round(ret, 1),
               "Bench%": round(bench_ret, 1) if bench_ret is not None else None,
               "Alpha%": round(alpha, 1) if alpha is not None else None,
               "aObj%": round(to_target, 0) if to_target is not None else None}))
    return out


def track_recommendations():
    with get_conn() as c:
        rows = compute_scorecard(c)
    if not rows:
        print("Sin datos. Corre primero:  python portfolio_research.py update"); return
    for r in rows:
        print(r)


# --- Helpers DataFrame (para el tablero) -------------------------------------
def scorecard_df():
    import pandas as pd
    with get_conn() as c:
        return pd.DataFrame(compute_scorecard(c))


def fundamentals_df():
    import pandas as pd
    with get_conn() as c:
        df = pd.read_sql("SELECT * FROM fundamentals", c)
    if not df.empty:
        for col in ("roe", "profit_margin", "revenue_growth", "earnings_growth"):
            if col in df:
                df[col] = (df[col] * 100).round(1)
        for col in ("pe", "forward_pe", "pb", "ev_ebitda",
                    "debt_to_equity", "current_ratio"):
            if col in df:
                df[col] = df[col].round(2)
        df = df.rename(columns={
            "ticker": "Ticker", "name": "Empresa", "sector": "Sector",
            "market_cap": "MktCap", "pe": "P/E", "forward_pe": "P/E fwd",
            "pb": "P/BV", "ev_ebitda": "FV/EBITDA", "roe": "ROE%",
            "profit_margin": "Margen%", "dividend_yield": "Div.Yield",
            "revenue_growth": "CrecVtas%", "earnings_growth": "CrecGan%",
            "debt_to_equity": "Deuda/Eq", "current_ratio": "Liq.Corr",
            "updated_at": "Actualizado"})
    return df


def price_history_df(ticker):
    import pandas as pd
    with get_conn() as c:
        df = pd.read_sql("SELECT date, close FROM prices WHERE ticker=? "
                         "ORDER BY date", c, params=(ticker,))
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


def list_price_tickers():
    with get_conn() as c:
        return [r[0] for r in c.execute(
            "SELECT DISTINCT ticker FROM prices ORDER BY ticker")]


def momentum_df(skip_days=21, lookback_days=252, min_days=100):
    """Momentum 12-1 meses por ticker, calculado desde la tabla `prices`.
    Retorno (%) entre el precio de ~12 meses atrás y el de ~1 mes atrás
    (se saltea el último mes: es el estándar para evitar reversión de corto plazo).
    Si un ticker no tiene al menos `min_days` ruedas, no aparece (queda N/A en el
    score). Devuelve DataFrame [Ticker, Mom%]."""
    import pandas as pd
    with get_conn() as c:
        df = pd.read_sql(
            "SELECT ticker, date, close FROM prices ORDER BY ticker, date", c)
    if df.empty:
        return pd.DataFrame(columns=["Ticker", "Mom%"])
    rows = []
    for t, g in df.groupby("ticker"):
        closes = g["close"].dropna().tolist()
        n = len(closes)
        if n < min_days:
            continue
        recent_pos = n - 1 - skip_days if n > skip_days else n - 1
        base_pos = max(0, n - 1 - lookback_days)
        if base_pos >= recent_pos:
            continue
        base, recent = closes[base_pos], closes[recent_pos]
        if base and base > 0:
            rows.append((t, round((recent / base - 1) * 100, 1)))
    return pd.DataFrame(rows, columns=["Ticker", "Mom%"])


def coverage():
    """Cuántos tickers del universo ya tienen ratios cargados."""
    uni = [t for t in load_universe() if t != BENCHMARK]
    with get_conn() as c:
        have = c.execute("SELECT COUNT(*) FROM fundamentals").fetchone()[0]
    return have, len(uni)


# --- Bonos -------------------------------------------------------------------
def _num(v):
    import math
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def load_bond_universe():
    import csv
    if not os.path.exists(UNIVERSE_BONDS_FILE):
        return []
    rows = []
    with open(UNIVERSE_BONDS_FILE, encoding="utf-8") as f:
        for d in csv.DictReader(f):
            rows.append({k: (v.strip() if isinstance(v, str) else v)
                         for k, v in d.items()})
    return rows


def seed_bonds():
    with get_conn() as c:
        for b in load_bond_universe():
            c.execute("""INSERT OR IGNORE INTO bonds
                (ticker, name, currency, law, maturity) VALUES (?,?,?,?,?)""",
                (b.get("ticker", "").upper(), b.get("name"), b.get("currency"),
                 b.get("law"), b.get("maturity")))


def bonds_df():
    import pandas as pd
    with get_conn() as c:
        return pd.read_sql(
            "SELECT ticker, name, currency, law, maturity, price, tir, parity, "
            "duration, updated_at FROM bonds ORDER BY maturity, ticker", c)


def save_bonds(df):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_conn() as c:
        for _, r in df.iterrows():
            c.execute("""UPDATE bonds SET price=?, tir=?, parity=?, duration=?,
                         updated_at=? WHERE ticker=?""",
                      (_num(r.get("price")), _num(r.get("tir")),
                       _num(r.get("parity")), _num(r.get("duration")),
                       now, r["ticker"]))


def add_riesgo_pais(date, value):
    with get_conn() as c:
        c.execute("INSERT OR REPLACE INTO macro (metric, date, value) "
                  "VALUES (?,?,?)", ("riesgo_pais", date, float(value)))


def riesgo_pais_df():
    import pandas as pd
    with get_conn() as c:
        df = pd.read_sql("SELECT date, value FROM macro WHERE metric='riesgo_pais' "
                         "ORDER BY date", c)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


# --- Precios de bonos vía data912 (API pública gratis) -----------------------
def fetch_data912_panel(panel="arg_bonds"):
    """Devuelve la lista de instrumentos del panel. Sin auth. Hobby/no real-time."""
    import json, urllib.request
    url = f"https://data912.com/live/{panel}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def update_bond_prices():
    """Baja los paneles de bonos, deuda corporativa (ONs) y letras de data912
    y los guarda. Devuelve cuántas cotizaciones guardó."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = []
    for panel in ("arg_bonds", "arg_corp", "arg_notes"):
        try:
            data = fetch_data912_panel(panel)
        except Exception as e:
            print(f"  [error data912 {panel}] {e}")
            continue
        for d in data:
            sym = d.get("symbol")
            if sym:
                rows.append((sym, _num(d.get("c")), _num(d.get("pct_change")), now))
    if rows:
        with get_conn() as c:
            c.executemany("INSERT OR REPLACE INTO bond_quotes "
                          "(symbol, price, pct_change, updated_at) VALUES (?,?,?,?)", rows)
    return len(rows)


def bond_quotes_df():
    import pandas as pd
    with get_conn() as c:
        return pd.read_sql("SELECT symbol, price, pct_change, updated_at "
                           "FROM bond_quotes ORDER BY symbol", c)


def bonds_with_quotes_df():
    """bonds_df + precios auto de data912 (en ARS y la variante D = dólar MEP)."""
    b = bonds_df()
    q = bond_quotes_df()
    if not b.empty and not q.empty:
        price_map = dict(zip(q["symbol"], q["price"]))
        b["data912_ARS"] = b["ticker"].map(price_map)
        b["data912_USD"] = b["ticker"].map(lambda t: price_map.get(str(t) + "D"))
    return b


def _http_get_json(url, timeout=20):
    import json, urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


# --- Riesgo país automático (ArgentinaDatos, gratis sin clave) ---------------
def update_riesgo_pais_auto():
    """Baja la serie histórica de riesgo país y la guarda. Devuelve cuántos puntos."""
    try:
        data = _http_get_json(
            "https://argentinadatos.com/v1/finanzas/indices/riesgo-pais")
    except Exception as e:
        print(f"  [error riesgo pais] {e}")
        return 0
    rows = []
    for d in data:
        f, v = d.get("fecha"), d.get("valor")
        if f is not None and v is not None:
            rows.append(("riesgo_pais", str(f)[:10], float(v)))
    with get_conn() as c:
        c.executemany("INSERT OR REPLACE INTO macro (metric, date, value) "
                      "VALUES (?,?,?)", rows)
    return len(rows)


# --- Motor de bonos: TIR, duration ------------------------------------------
def bond_metrics(price, flows):
    """price = precio sucio por 100 VN. flows = lista de (años, monto por 100 VN).
    Devuelve (TIR_%, duration_modificada_años) o (None, None)."""
    flows = [(t, a) for t, a in flows if t and t > 0 and a]
    if not flows or not price or price <= 0:
        return None, None

    def pv(y):
        return sum(a / (1 + y) ** t for t, a in flows)

    lo, hi = -0.99, 5.0
    f_lo = pv(lo) - price
    if (pv(hi) - price) * f_lo > 0:
        return None, None  # sin raíz en el rango
    for _ in range(200):
        mid = (lo + hi) / 2
        f_mid = pv(mid) - price
        if abs(f_mid) < 1e-7:
            break
        if f_lo * f_mid < 0:
            hi = mid
        else:
            lo, f_lo = mid, f_mid
    y = (lo + hi) / 2
    p = pv(y)
    mac = sum(t * a / (1 + y) ** t for t, a in flows) / p
    return round(y * 100, 2), round(mac / (1 + y), 2)


def load_cashflows():
    """Lee cashflows.csv (ticker, date, coupon, amort por 100 VN)."""
    import csv
    if not os.path.exists(CASHFLOWS_FILE):
        return {}
    out = {}
    with open(CASHFLOWS_FILE, encoding="utf-8") as f:
        for d in csv.DictReader(f):
            t = (d.get("ticker") or "").strip().upper()
            dt = (d.get("date") or "").strip()
            coup = _num(d.get("coupon"))
            amort = _num(d.get("amort"))
            if t and dt and coup is not None and amort is not None:
                out.setdefault(t, []).append((dt, coup, amort))
    return out


def _d30(d1, d2):
    """Días entre fechas con convención 30/360."""
    dd1 = min(d1.day, 30)
    dd2 = d2.day
    if dd1 == 30 and dd2 == 31:
        dd2 = 30
    return 360 * (d2.year - d1.year) + 30 * (d2.month - d1.month) + (dd2 - dd1)


def _clean_bond_price(price):
    """Devuelve un precio USD/100 usable, o None si es implausible. data912
    entrega el precio ya en base 'por 100 de nominal original' (la misma base
    que los flujos de cashflows.csv), así que NO hay que reescalarlo. El único
    cuidado es descartar una cotización en ARS que se cuela cuando falta el
    símbolo USD/MEP (...D) del bono: un precio USD/100 sano va ~20-130."""
    if price is None:
        return None
    if price < 5:        # data912 a veces da la variante "D" por 1 VN
        price *= 100
    if price > 1000:     # esto NO es un precio USD/100: es ARS colado -> descartar
        return None
    return price


def _clear_bond_metrics(ticker, drop_price=False):
    """Limpia TIR/paridad/duration (y opcionalmente el precio) de un bono que no
    se pudo precoár en USD esta corrida, para que no quede basura vieja en la
    tabla ni en la curva."""
    cols = "tir=NULL, parity=NULL, duration=NULL"
    if drop_price:
        cols = "price=NULL, " + cols
    with get_conn() as c:
        c.execute(f"UPDATE bonds SET {cols}, updated_at=? WHERE ticker=?",
                  (datetime.now().strftime("%Y-%m-%d %H:%M"), ticker))


def update_bond_metrics(settle=None):
    """Calcula y guarda precio (data912), TIR, duration y paridad de cada bono
    que tenga flujo cargado. Todo automático. Devuelve cuántos calculó.

    El precio de data912 ya viene 'por 100 de nominal original' (misma base que
    los flujos), así que se usa crudo. Si el precio que llega es implausible
    (una cotización en ARS colada) o la TIR resultante es un disparate, en vez
    de ensuciar la tabla/curva limpiamos los valores viejos de ese bono."""
    from datetime import date, datetime as _dtm
    settle = settle or date.today()
    cf = load_cashflows()
    qdf = bond_quotes_df()
    pmap = dict(zip(qdf["symbol"], qdf["price"])) if not qdf.empty else {}
    with get_conn() as c:
        bonds = c.execute("SELECT ticker, price FROM bonds").fetchall()
    n = 0
    for ticker, manual_price in bonds:
        rows = cf.get(ticker.upper())
        if not rows:
            continue
        raw = pmap.get(ticker + "D") or pmap.get(ticker) or manual_price
        price = _clean_bond_price(raw)
        if price is None:
            # no hay precio USD usable (p.ej. solo cotización en ARS): borramos
            # lo viejo para que muestre None y se caiga de la curva
            _clear_bond_metrics(ticker, drop_price=bool(raw))
            if raw:
                print(f"  [skip precio sospechoso] {ticker}: {raw}")
            continue
        fut = []
        for dt, coup, amort in rows:
            try:
                d0 = _dtm.strptime(dt, "%Y-%m-%d").date()
            except ValueError:
                continue
            if d0 > settle:
                fut.append((d0, coup, amort))
        if not fut:
            continue
        flows = [((d0 - settle).days / 365.0, coup + amort) for d0, coup, amort in fut]
        tir, dur = bond_metrics(price, flows)   # precio crudo: data912 ya está en base original
        if tir is None or tir < -5 or tir > 60:  # disparate -> limpiamos
            _clear_bond_metrics(ticker, drop_price=False)
            if tir is not None:
                print(f"  [skip TIR implausible] {ticker}: {tir}")
            continue
        # paridad = precio / valor técnico (residual + intereses corridos, 30/360)
        residual = sum(a for _, _, a in fut)
        nd, ncoup = fut[0][0], fut[0][1]
        pm, py = nd.month - 6, nd.year
        if pm <= 0:
            pm += 12
            py -= 1
        prev = date(py, pm, min(nd.day, 28))
        denom = _d30(prev, nd)
        frac = _d30(prev, settle) / denom if denom else 0.0
        vtec = residual + ncoup * frac
        paridad = round(price / vtec * 100, 2) if vtec else None
        with get_conn() as c:
            c.execute("UPDATE bonds SET price=?, tir=?, parity=?, duration=?, "
                      "updated_at=? WHERE ticker=?",
                      (round(price, 2), tir, paridad, dur,
                       _dtm.now().strftime("%Y-%m-%d %H:%M"), ticker))
        n += 1
    return n


def cashflow_coverage():
    """Cuántos bonos del universo tienen flujo de fondos cargado."""
    cf = load_cashflows()
    bonds = [b.get("ticker", "").upper() for b in load_bond_universe()]
    have = sum(1 for t in bonds if cf.get(t))
    return have, len(bonds)


# --- CEDEARs: ratios de conversión + CCL (precio en pesos) -------------------
# El precio del CEDEAR en pesos = precio de la acción (USD) * CCL / ratio.
# 'ratio' = cuántos CEDEARs equivalen a 1 acción (X en "X:1"); para "1:Y" es 1/Y.
# Los ratios se editan en RATIOS_FILE (validá contra Comafi/BYMA; cambian por splits).
RATIOS_FILE = "data/ratios_cedears.csv"


def load_cedear_ratios():
    """Lee ticker -> ratio (CEDEARs por acción) desde RATIOS_FILE."""
    import csv
    out = {}
    if not os.path.exists(RATIOS_FILE):
        return out
    with open(RATIOS_FILE, encoding="utf-8") as f:
        for d in csv.DictReader(f):
            t = (d.get("ticker") or "").strip().upper()
            r = _num(d.get("ratio"))
            if t and r and r > 0:
                out[t] = r
    return out


def cedear_ratio_coverage():
    ratios = load_cedear_ratios()
    uni = [t for t in load_universe() if t != BENCHMARK]
    have = sum(1 for t in uni if t in ratios)
    return have, len(uni)


def fetch_ccl():
    """Trae el CCL (contado con liqui) de fuentes públicas gratis. None si falla."""
    sources = [
        ("https://dolarapi.com/v1/dolares/contadoconliqui", ("venta", "compra")),
        ("https://api.argentinadatos.com/v1/cotizaciones/dolares/contadoconliqui",
         ("venta", "compra")),
    ]
    for url, keys in sources:
        try:
            d = _http_get_json(url)
            if isinstance(d, list) and d:
                d = d[-1]
            for k in keys:
                v = d.get(k)
                if v:
                    return float(v)
        except Exception:
            continue
    return None


# --- Informes (bitácora de research) -----------------------------------------
# Los informes diarios viven como archivos .md en la carpeta REPORTS_DIR, al lado
# de la app. El formato canónico es Markdown (se lee dentro del tablero); si al
# lado hay un .pdf o .tex con el MISMO nombre, se ofrecen como descarga.
REPORTS_DIR = "informes"


def _ensure_reports_dir():
    os.makedirs(REPORTS_DIR, exist_ok=True)


def _parse_report_date(filename):
    """Saca una fecha AAAA-MM-DD del nombre (busca 8 dígitos tipo 20260623)."""
    import re
    m = re.search(r"(20\d{6})", filename)
    if m:
        s = m.group(1)
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return None


def _report_title(path, fallback):
    """Primer encabezado markdown (# ...) o primera línea no vacía como título."""
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                t = line.strip()
                if t.startswith("#"):
                    return t.lstrip("#").strip()
                if t:
                    return t[:80]
    except Exception:
        pass
    return fallback


def list_reports():
    """Lista los informes .md de la carpeta, el más nuevo primero. Cada item es
    dict(file, path, date, dated, title, has_pdf, has_tex)."""
    _ensure_reports_dir()
    out = []
    for fn in sorted(os.listdir(REPORTS_DIR)):
        if not fn.lower().endswith(".md"):
            continue
        path = os.path.join(REPORTS_DIR, fn)
        base = os.path.splitext(path)[0]
        date = _parse_report_date(fn)
        out.append({
            "file": fn, "path": path,
            "date": date or datetime.fromtimestamp(
                os.path.getmtime(path)).strftime("%Y-%m-%d"),
            "dated": bool(date),
            "title": _report_title(path, fn),
            "has_pdf": os.path.exists(base + ".pdf"),
            "has_tex": os.path.exists(base + ".tex"),
        })
    out.sort(key=lambda r: (r["date"], r["file"]), reverse=True)
    return out


def read_report(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def save_report(filename, data):
    """Guarda un informe en la carpeta. data: str (texto) o bytes. Si el nombre
    no trae extensión conocida, asume .md. Devuelve la ruta guardada."""
    _ensure_reports_dir()
    name = os.path.basename(filename)
    if not name.lower().endswith((".md", ".pdf", ".tex")):
        name += ".md"
    path = os.path.join(REPORTS_DIR, name)
    if isinstance(data, (bytes, bytearray)):
        with open(path, "wb") as f:
            f.write(data)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)
    return path


def search_reports(query, context=140):
    """Devuelve [(item, snippet)] de los informes cuyo texto contiene query."""
    q = (query or "").strip().lower()
    if not q:
        return []
    res = []
    for item in list_reports():
        try:
            text = read_report(item["path"])
        except Exception:
            continue
        i = text.lower().find(q)
        if i >= 0:
            a = max(0, i - context // 2)
            b = min(len(text), i + len(q) + context // 2)
            snippet = (("…" if a > 0 else "")
                       + text[a:b].replace("\n", " ").strip()
                       + ("…" if b < len(text) else ""))
            res.append((item, snippet))
    return res


# =============================================================================
# --- Carteras simuladas ------------------------------------------------------
# =============================================================================
#
# Modelo de datos:
#   sim_portfolios: una cartera = nombre + etiqueta + fecha de inicio + notas.
#   sim_positions:  cada posición = ticker, fecha de entrada, precio de entrada,
#                   y CANTIDAD (shares) O MONTO (amount_usd). Ambos son opcionales
#                   pero al menos uno debe estar presente.
#
# Mecánica de cálculo:
#   - Si la posición tiene shares: valor_actual = shares * precio_actual
#     costo_base = shares * price_entry
#   - Si la posición tiene amount_usd (y no shares): se infieren shares implícitas
#     shares_impl = amount_usd / price_entry
#     valor_actual = shares_impl * precio_actual
#   - Alpha = retorno_posicion% - retorno_SPY%(misma ventana)
#   - Peso% = valor_actual / suma_valor_actual * 100
#
# Las posiciones usan los mismos precios históricos de la tabla `prices`
# (yfinance). Si el ticker no tiene precios descargados, aparece como N/D.

def create_portfolio(name, label="", start_date=None, notes=""):
    """Crea una nueva cartera simulada. Devuelve el id."""
    start_date = start_date or datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_conn() as c:
        cur = c.execute(
            "INSERT INTO sim_portfolios (name, label, start_date, notes, created_at) "
            "VALUES (?,?,?,?,?)", (name, label, start_date, notes, now))
        return cur.lastrowid


def list_portfolios():
    """Devuelve lista de dicts con info de cada cartera."""
    with get_conn() as c:
        rows = c.execute(
            "SELECT id, name, label, start_date, notes, created_at "
            "FROM sim_portfolios ORDER BY start_date DESC, id DESC").fetchall()
    return [{"id": r[0], "name": r[1], "label": r[2],
             "start_date": r[3], "notes": r[4], "created_at": r[5]}
            for r in rows]


def delete_portfolio(portfolio_id):
    """Elimina una cartera y todas sus posiciones."""
    with get_conn() as c:
        c.execute("DELETE FROM sim_positions WHERE portfolio_id=?", (portfolio_id,))
        c.execute("DELETE FROM sim_portfolios WHERE id=?", (portfolio_id,))


def update_portfolio_meta(portfolio_id, name, label, start_date, notes):
    """Actualiza los metadatos de una cartera (no toca posiciones)."""
    with get_conn() as c:
        c.execute("UPDATE sim_portfolios SET name=?, label=?, start_date=?, notes=? "
                  "WHERE id=?", (name, label, start_date, notes, portfolio_id))


def add_position(portfolio_id, ticker, price_entry, entry_date=None,
                 shares=None, amount_usd=None, note=""):
    """Agrega una posición a una cartera.

    Exactamente uno de 'shares' o 'amount_usd' debe ser no-None.
    price_entry: precio de entrada del subyacente en USD (acción, no CEDEAR).
    """
    if shares is None and amount_usd is None:
        raise ValueError("Especificá shares o amount_usd.")
    entry_date = entry_date or datetime.now().strftime("%Y-%m-%d")
    with get_conn() as c:
        c.execute(
            "INSERT INTO sim_positions "
            "(portfolio_id, ticker, entry_date, shares, amount_usd, price_entry, note) "
            "VALUES (?,?,?,?,?,?,?)",
            (portfolio_id, ticker.upper(), entry_date,
             _num(shares), _num(amount_usd), float(price_entry), note))


def remove_position(position_id):
    """Elimina una posición por su id."""
    with get_conn() as c:
        c.execute("DELETE FROM sim_positions WHERE id=?", (position_id,))


def list_positions(portfolio_id):
    """Devuelve las posiciones de una cartera como lista de dicts."""
    with get_conn() as c:
        rows = c.execute(
            "SELECT id, ticker, entry_date, shares, amount_usd, price_entry, note "
            "FROM sim_positions WHERE portfolio_id=? ORDER BY entry_date, ticker",
            (portfolio_id,)).fetchall()
    return [{"id": r[0], "ticker": r[1], "entry_date": r[2],
             "shares": r[3], "amount_usd": r[4], "price_entry": r[5], "note": r[6]}
            for r in rows]


def compute_portfolio_snapshot(portfolio_id):
    """Calcula el estado actual de una cartera. Devuelve lista de dicts por posición
    más un dict de totales.

    Cada posición:
        ticker, entry_date, shares_eff, cost_basis, price_entry, price_now,
        value_now, ret_pct, alpha_pct, weight_pct, note
    Totales:
        total_cost, total_value, total_ret_pct, total_alpha_pct
    """
    positions = list_positions(portfolio_id)
    if not positions:
        return [], {}

    with get_conn() as c:
        rows = []
        bench_now_row = latest_price(c, BENCHMARK)
        bench_now = bench_now_row[1] if bench_now_row else None

        for p in positions:
            ticker = p["ticker"]
            price_entry = p["price_entry"]
            entry_date = p["entry_date"]

            # shares efectivas
            if p["shares"] is not None:
                shares_eff = p["shares"]
            else:
                shares_eff = p["amount_usd"] / price_entry if price_entry else None

            cost_basis = shares_eff * price_entry if shares_eff else None

            # precio actual
            pnow_row = latest_price(c, ticker)
            price_now = pnow_row[1] if pnow_row else None
            value_now = shares_eff * price_now if (shares_eff and price_now) else None

            # retorno de la posición
            ret_pct = ((price_now / price_entry) - 1) * 100 if (price_now and price_entry) else None

            # alpha vs SPY (misma ventana)
            bench0 = price_on_or_before(c, BENCHMARK, entry_date)
            if bench0 and bench_now and ret_pct is not None:
                bench_ret = (bench_now / bench0 - 1) * 100
                alpha_pct = ret_pct - bench_ret
            else:
                alpha_pct = None

            rows.append({
                "pos_id": p["id"],
                "Ticker": ticker,
                "Entrada": entry_date,
                "Shares": round(shares_eff, 4) if shares_eff else None,
                "Costo base": round(cost_basis, 2) if cost_basis else None,
                "P. entrada": round(price_entry, 2),
                "P. actual": round(price_now, 2) if price_now else None,
                "Valor USD": round(value_now, 2) if value_now else None,
                "Ret%": round(ret_pct, 1) if ret_pct is not None else None,
                "Alpha%": round(alpha_pct, 1) if alpha_pct is not None else None,
                "Peso%": None,   # se calcula abajo
                "Nota": p["note"] or "",
            })

    # calcular pesos
    total_value = sum(r["Valor USD"] for r in rows if r["Valor USD"] is not None)
    total_cost = sum(r["Costo base"] for r in rows if r["Costo base"] is not None)
    for r in rows:
        if r["Valor USD"] is not None and total_value:
            r["Peso%"] = round(r["Valor USD"] / total_value * 100, 1)

    # retorno total (ponderado por valor)
    total_ret = ((total_value / total_cost) - 1) * 100 if (total_cost and total_value) else None

    # alpha total: comparar cartera completa con SPY desde la fecha más antigua
    totals = {
        "total_cost": round(total_cost, 2) if total_cost else None,
        "total_value": round(total_value, 2) if total_value else None,
        "total_ret_pct": round(total_ret, 1) if total_ret is not None else None,
        "n_positions": len(rows),
    }
    return rows, totals


def portfolio_history_df(portfolio_id, freq="W"):
    """Calcula el valor histórico de la cartera semana a semana (freq='W')
    o día a día (freq='D'). Devuelve un DataFrame con columnas date, value_usd,
    spy_value (normalizado a la inversión inicial para comparar evolución).

    Requiere que los precios de todos los tickers estén en la tabla prices.
    """
    import pandas as pd

    positions = list_positions(portfolio_id)
    if not positions:
        return pd.DataFrame()

    tickers = list({p["ticker"] for p in positions})
    tickers_needed = tickers + [BENCHMARK]

    # traer historial de todos los tickers necesarios
    with get_conn() as c:
        ph = pd.read_sql(
            f"SELECT ticker, date, close FROM prices "
            f"WHERE ticker IN ({','.join('?' * len(tickers_needed))}) "
            f"ORDER BY date",
            c, params=tickers_needed)

    if ph.empty:
        return pd.DataFrame()

    ph["date"] = pd.to_datetime(ph["date"])
    pivot = ph.pivot(index="date", columns="ticker", values="close")

    # resamplear
    pivot = pivot.resample(freq).last().ffill()

    # filtrar: solo fechas desde la posición más antigua
    min_date = min(p["entry_date"] for p in positions)
    pivot = pivot[pivot.index >= pd.Timestamp(min_date)]

    if pivot.empty:
        return pd.DataFrame()

    # calcular valor de cartera día a día
    values = []
    for date_ts, row in pivot.iterrows():
        total = 0.0
        for p in positions:
            if pd.Timestamp(p["entry_date"]) > date_ts:
                continue  # posición no abierta todavía
            ticker = p["ticker"]
            price_entry = p["price_entry"]
            if p["shares"] is not None:
                shares_eff = p["shares"]
            else:
                shares_eff = p["amount_usd"] / price_entry if price_entry else 0

            price_now = row.get(ticker)
            if price_now and not pd.isna(price_now):
                total += shares_eff * price_now
        values.append({"date": date_ts, "value_usd": round(total, 2)})

    result = pd.DataFrame(values)
    if result.empty or "value_usd" not in result.columns:
        return result

    # normalizar SPY a la inversión inicial para comparar curvas
    first_value = result["value_usd"].iloc[0]
    if BENCHMARK in pivot.columns and first_value:
        spy_start = pivot[BENCHMARK].iloc[0]
        if spy_start:
            result["spy_norm"] = (pivot[BENCHMARK].values / spy_start) * first_value

    return result


def portfolios_summary_df():
    """DataFrame con una fila por cartera y columnas de resumen (para el selector)."""
    import pandas as pd
    pfls = list_portfolios()
    rows = []
    for pf in pfls:
        _, totals = compute_portfolio_snapshot(pf["id"])
        rows.append({
            "id": pf["id"],
            "Nombre": pf["name"],
            "Etiqueta": pf["label"] or "",
            "Inicio": pf["start_date"],
            "Posiciones": totals.get("n_positions", 0),
            "Costo USD": totals.get("total_cost"),
            "Valor USD": totals.get("total_value"),
            "Ret%": totals.get("total_ret_pct"),
            "Notas": pf["notes"] or "",
        })
    return pd.DataFrame(rows)


# =============================================================================
# --- Main --------------------------------------------------------------------
# =============================================================================
def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    init_db(); seed_recommendations()
    if cmd in ("update", "all"):
        print("Bajando precios del universo..."); update_prices()
    if cmd in ("funds", "all"):
        print("Bajando ratios (reanudable)..."); update_fundamentals()
    if cmd in ("track", "all"):
        print("\n=== SCORECARD ==="); track_recommendations()


if __name__ == "__main__":
    main()
