"""
screener_score.py — Score compuesto 0–10 para el Screener.

Idea tomada del ScoringEngine de la "quant platform" (6 dimensiones, pesos por
estilo + multiplicadores por horizonte), mapeado a los ratios que la herramienta
baja de yfinance. No inventa datos: si un ratio falta, la dimensión queda N/A y
se re-normalizan los pesos por fila.

v3: dos modos de scoring (parámetro `mode`):
  - "sector"   : cada ratio se puntúa por su PERCENTIL DENTRO DEL SECTOR
                 (un banco se compara con bancos, etc.). Si el sector tiene
                 menos de MIN_PEERS empresas, o falta el sector, cae a umbrales.
  - "absolute" : umbrales fijos (la lógica de la v2).

Datos usados:
  Quality   <- ROE% , Margen%
  Valuation <- P/E (fwd si está, si no trailing) , P/BV , FV/EBITDA   (menor=mejor)
  Income    <- Div.Yield
  Growth    <- CrecVtas% , CrecGan%   (fallback: P/E fwd vs trailing)
  Safety    <- Deuda/Eq (menor=mejor) , Liq.Corr (mayor=mejor)  (fallback: MktCap)
  Momentum  <- opcional, columna externa (ret. 12m)

NADA de esto es asesoramiento. Es un ranking heurístico sobre datos públicos.
"""

import numpy as np
import pandas as pd

MIN_PEERS = 5   # mínimo de empresas en un sector para usar percentiles

STYLE_WEIGHTS = {
    "growth":    {"quality": 0.15, "growth": 0.35, "valuation": 0.10, "safety": 0.10, "momentum": 0.20, "income": 0.10},
    "value":     {"quality": 0.15, "growth": 0.10, "valuation": 0.35, "safety": 0.20, "momentum": 0.05, "income": 0.15},
    "quality":   {"quality": 0.35, "growth": 0.15, "valuation": 0.15, "safety": 0.20, "momentum": 0.05, "income": 0.10},
    "GARP":      {"quality": 0.20, "growth": 0.25, "valuation": 0.25, "safety": 0.15, "momentum": 0.05, "income": 0.10},
    "dividend":  {"quality": 0.15, "growth": 0.05, "valuation": 0.10, "safety": 0.25, "momentum": 0.05, "income": 0.40},
    "defensive": {"quality": 0.20, "growth": 0.05, "valuation": 0.15, "safety": 0.35, "momentum": 0.05, "income": 0.20},
}
HORIZON_MULT = {
    "short-term":  {"quality": 0.7, "growth": 0.9, "valuation": 0.8, "safety": 0.8, "momentum": 1.6, "income": 0.8},
    "medium-term": {"quality": 1.0, "growth": 1.0, "valuation": 1.0, "safety": 1.0, "momentum": 1.0, "income": 1.0},
    "long-term":   {"quality": 1.4, "growth": 1.0, "valuation": 1.1, "safety": 1.2, "momentum": 0.3, "income": 1.1},
}
DIMS = ["quality", "growth", "valuation", "safety", "momentum", "income"]


def _weights(style, horizon):
    base = STYLE_WEIGHTS.get(style, STYLE_WEIGHTS["quality"]).copy()
    mult = HORIZON_MULT.get(horizon, HORIZON_MULT["medium-term"])
    w = {k: base[k] * mult[k] for k in base}
    s = sum(w.values())
    return {k: v / s for k, v in w.items()} if s else base


def _isna(x):
    return x is None or (isinstance(x, float) and np.isnan(x))

def _r1(x):
    return None if _isna(x) else round(float(x), 1)


# ── Umbrales absolutos (también sirven de fallback en modo sector) ───────────
def _bucket(value, thresholds, higher_is_better=True):
    if _isna(value):
        return None
    for cut, pts in thresholds:
        if (higher_is_better and value > cut) or (not higher_is_better and value < cut):
            return pts
    return thresholds[-1][1]

def _q_roe(x):      return _bucket(x, [(25, 10), (18, 8), (12, 6), (8, 4), (4, 2), (-1e9, 1)])
def _q_margin(x):   return _bucket(x, [(25, 10), (18, 8), (12, 6), (7, 4), (3, 2), (-1e9, 1)])
def _v_pe(x):
    if _isna(x) or x <= 0: return None
    return _bucket(x, [(12, 10), (16, 8), (20, 6), (26, 4), (35, 2), (1e9, 1)], higher_is_better=False)
def _v_pbv(x):
    if _isna(x) or x <= 0: return None
    return _bucket(x, [(1.5, 10), (2.5, 8), (4, 6), (6, 4), (9, 2), (1e9, 1)], higher_is_better=False)
def _v_evebitda(x):
    if _isna(x) or x <= 0: return None
    return _bucket(x, [(8, 10), (11, 8), (14, 6), (18, 4), (25, 2), (1e9, 1)], higher_is_better=False)
def _income(y):     return _bucket(y, [(6, 10), (4, 8), (2.5, 6), (1.5, 4), (0.5, 2), (0, 1), (-1e9, 0)])
def _g_revenue(x):  return _bucket(x, [(25, 10), (15, 8), (8, 6), (3, 4), (0, 2), (-1e9, 1)])
def _g_earnings(x): return _bucket(x, [(30, 10), (18, 8), (8, 6), (0, 4), (-10, 2), (-1e9, 1)])
def _g_proxy(pe, fwd):
    if _isna(pe) or _isna(fwd) or pe <= 0 or fwd <= 0: return None
    return _bucket(fwd / pe, [(0.80, 9), (0.90, 7), (1.00, 6), (1.10, 5), (1.25, 3), (1e9, 2)], higher_is_better=False)
def _s_debt(de):
    if _isna(de): return None
    if de < 0:    return 1
    return _bucket(de, [(30, 10), (60, 8), (100, 6), (150, 4), (250, 2), (1e9, 1)], higher_is_better=False)
def _s_current(cr): return _bucket(cr, [(2.5, 10), (2, 8), (1.5, 6), (1, 4), (0.7, 2), (-1e9, 1)])
def _safety_size(m):return _bucket(m, [(2e11, 9), (5e10, 8), (1e10, 6), (2e9, 4), (-1e9, 2)])
def _mom(x):        return _bucket(x, [(40, 10), (20, 8), (8, 6), (0, 5), (-10, 3), (-1e9, 1)])


def _normalize_div_yield(col):
    pos = col[col.notna() & (col > 0)]
    if len(pos) and pos.median() < 1.5:
        return col * 100.0
    return col


# ── Núcleo modo sector: percentil dentro del sector con fallback a umbral ─────
def _sector_metric(df, series, higher_better, abs_fn, valid_mask=None):
    """Devuelve una Serie 0–10 alineada a df.index.
       Percentil dentro del sector si hay >= MIN_PEERS pares válidos;
       si no, cae al puntaje por umbral (abs_fn)."""
    s = pd.to_numeric(series, errors="coerce")
    if valid_mask is not None:
        s = s.where(valid_mask)             # inválidos -> NaN
    sec = df["Sector"] if "Sector" in df.columns else pd.Series(index=df.index, dtype=object)

    out = pd.Series(np.nan, index=df.index, dtype=float)
    for _, idx in df.groupby(sec, dropna=True).groups.items():
        sub = s.loc[idx].dropna()
        if len(sub) >= MIN_PEERS:
            pr = sub.rank(pct=True, ascending=higher_better)   # 0..1, mejor=1
            out.loc[sub.index] = 1.0 + 9.0 * pr                # escala 1..10
    # fallback por umbral para lo que quedó sin percentil
    falt = out.isna()
    if falt.any():
        out.loc[falt] = pd.to_numeric(series, errors="coerce").loc[falt].apply(
            lambda v: np.nan if abs_fn(v) is None else abs_fn(v))
    return out


def _abs_metric(series, abs_fn):
    return pd.to_numeric(series, errors="coerce").apply(
        lambda v: np.nan if abs_fn(v) is None else abs_fn(v))


def _col(df, name):
    return df[name] if name in df.columns else pd.Series(np.nan, index=df.index)


def score(df, style="quality", horizon="long-term", mode="sector", momentum_col=None):
    """Copia de df con: Score, Rating, Cobertura y subscores Q/Val/Inc/Gro/Saf[/Mom].
       mode: 'sector' (percentil intra-sector, recomendado) o 'absolute' (umbrales)."""
    if df is None or df.empty:
        return df
    out = df.copy()
    w = _weights(style, horizon)
    n = len(out)

    dy = _normalize_div_yield(out["Div.Yield"]) if "Div.Yield" in out else pd.Series(np.nan, index=out.index)
    # P/E efectivo: forward si está, si no trailing
    pe_eff = _col(out, "P/E fwd").copy()
    pe_eff = pe_eff.where(pe_eff.notna(), _col(out, "P/E"))

    if mode == "sector":
        m_roe  = _sector_metric(out, _col(out, "ROE%"),    True,  _q_roe)
        m_mar  = _sector_metric(out, _col(out, "Margen%"), True,  _q_margin)
        m_pe   = _sector_metric(out, pe_eff,               False, _v_pe,        valid_mask=(pe_eff > 0))
        m_pbv  = _sector_metric(out, _col(out, "P/BV"),    False, _v_pbv,       valid_mask=(_col(out, "P/BV") > 0))
        m_ev   = _sector_metric(out, _col(out, "FV/EBITDA"),False,_v_evebitda,  valid_mask=(_col(out, "FV/EBITDA") > 0))
        m_inc  = _sector_metric(out, dy,                   True,  _income)
        m_rev  = _sector_metric(out, _col(out, "CrecVtas%"),True, _g_revenue)
        m_ear  = _sector_metric(out, _col(out, "CrecGan%"), True, _g_earnings)
        m_debt = _sector_metric(out, _col(out, "Deuda/Eq"),False,_s_debt,       valid_mask=(_col(out, "Deuda/Eq") >= 0))
        m_cur  = _sector_metric(out, _col(out, "Liq.Corr"),True, _s_current)
        m_mom  = (_sector_metric(out, _col(out, momentum_col), True, _mom)
                  if momentum_col else pd.Series(np.nan, index=out.index))
    else:  # absolute
        m_roe, m_mar = _abs_metric(_col(out, "ROE%"), _q_roe), _abs_metric(_col(out, "Margen%"), _q_margin)
        m_pe   = _abs_metric(pe_eff, _v_pe)
        m_pbv  = _abs_metric(_col(out, "P/BV"), _v_pbv)
        m_ev   = _abs_metric(_col(out, "FV/EBITDA"), _v_evebitda)
        m_inc  = _abs_metric(dy, _income)
        m_rev  = _abs_metric(_col(out, "CrecVtas%"), _g_revenue)
        m_ear  = _abs_metric(_col(out, "CrecGan%"), _g_earnings)
        m_debt = _abs_metric(_col(out, "Deuda/Eq"), _s_debt)
        m_cur  = _abs_metric(_col(out, "Liq.Corr"), _s_current)
        m_mom  = _abs_metric(_col(out, momentum_col), _mom) if momentum_col else pd.Series(np.nan, index=out.index)

    def rowmean(*series):
        return pd.concat(series, axis=1).mean(axis=1, skipna=True)

    quality   = rowmean(m_roe, m_mar)
    valuation = rowmean(m_pe, m_pbv, m_ev)
    income    = m_inc
    growth    = rowmean(m_rev, m_ear)
    safety    = rowmean(m_debt, m_cur)
    momentum  = m_mom

    # Fallbacks de dimensión (cuando no hubo NINGÚN dato real)
    pe_t, pe_f = _col(out, "P/E"), _col(out, "P/E fwd")
    gproxy = pd.Series([_g_proxy(pe_t.iloc[i], pe_f.iloc[i]) for i in range(n)], index=out.index, dtype=float)
    growth = growth.where(growth.notna(), gproxy)
    ssize  = _abs_metric(_col(out, "MktCap"), _safety_size)
    safety = safety.where(safety.notna(), ssize)

    dimdf = pd.DataFrame({"quality": quality, "growth": growth, "valuation": valuation,
                          "safety": safety, "momentum": momentum, "income": income})

    rows = []
    for i in range(n):
        dim = {k: (None if pd.isna(dimdf[k].iloc[i]) else float(dimdf[k].iloc[i])) for k in DIMS}
        avail = {k: v for k, v in dim.items() if v is not None}
        wsub = {k: w[k] for k in avail}
        wsum = sum(wsub.values())
        total = (sum(avail[k] * wsub[k] for k in avail) / wsum) if wsum else None
        cov = len(avail) / len(DIMS)
        rows.append({
            "Score": round(total, 2) if total is not None else None,
            "Rating": _rating(total, cov),
            "Cobertura": f"{len(avail)}/{len(DIMS)}",
            "Q": _r1(dim["quality"]), "Val": _r1(dim["valuation"]),
            "Inc": _r1(dim["income"]), "Gro": _r1(dim["growth"]),
            "Saf": _r1(dim["safety"]), "Mom": _r1(dim["momentum"]),
        })

    extra = pd.DataFrame(rows, index=out.index)
    if momentum_col is None:
        extra = extra.drop(columns=["Mom"])
    return pd.concat([out, extra], axis=1)


def _rating(total, coverage):
    if total is None: return "s/d"
    if total >= 7.5:   base = "Fuerte"
    elif total >= 5.5: base = "Bueno"
    elif total >= 3.5: base = "Regular"
    else:              base = "Flojo"
    if coverage < 0.5: base += " (poca data)"
    return base


if __name__ == "__main__":
    rng = np.random.default_rng(7)
    sectors = (["Technology"] * 8) + (["Financial Services"] * 7) + (["Energy"] * 3)
    n = len(sectors)
    demo = pd.DataFrame({
        "Ticker": [f"T{i:02d}" for i in range(n)],
        "Sector": sectors,
        "P/E":      np.round(rng.uniform(8, 40, n), 1),
        "P/E fwd":  np.round(rng.uniform(7, 35, n), 1),
        "P/BV":     np.round(rng.uniform(0.8, 9, n), 2),
        "FV/EBITDA":np.round(rng.uniform(5, 25, n), 1),
        "ROE%":     np.round(rng.uniform(-5, 35, n), 1),
        "Margen%":  np.round(rng.uniform(-3, 30, n), 1),
        "Div.Yield":np.round(rng.uniform(0, 0.06, n), 3),
        "MktCap":   rng.uniform(2e9, 3e11, n),
        "CrecVtas%":np.round(rng.uniform(-10, 30, n), 1),
        "CrecGan%": np.round(rng.uniform(-20, 40, n), 1),
        "Deuda/Eq": np.round(rng.uniform(10, 300, n), 0),
        "Liq.Corr": np.round(rng.uniform(0.5, 3, n), 2),
    })
    print("== MODO SECTOR ==")
    rs = score(demo, style="quality", horizon="long-term", mode="sector")
    print(rs[["Ticker","Sector","Score","Rating","Cobertura","Q","Val","Gro","Saf"]].to_string(index=False))
    print("\n== MODO ABSOLUTO (mismas empresas) ==")
    ra = score(demo, style="quality", horizon="long-term", mode="absolute")
    print(ra[["Ticker","Sector","Score","Rating"]].to_string(index=False))
