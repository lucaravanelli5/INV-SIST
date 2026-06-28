"""
daily_digest.py — Resumen diario de las carteras simuladas
==========================================================
Imprime, para CADA cartera (la conservadora y la agresiva), su retorno total,
el alpha vs SPY, mejor/peor posición y las señales de disparador (take-profit /
stop) que se hayan activado. Pensado para correrlo todos los días y pegar la
salida en el chat para analizarla juntos.

Uso:
    1) Actualizá precios en el tablero (o `python portfolio_research.py update`)
    2) python daily_digest.py

Las señales son disparadores MECÁNICOS para revisar, NO órdenes de compra/venta.
Las decisiones las tomás vos. Esto no es asesoramiento financiero.
"""

import datetime as dt
import portfolio_research as pr

# --- Disparadores: (take_profit_%, stop_review_%). Editá a gusto. ------------
# Tres tiers segun volatilidad / tipo de apuesta:
TRIGGERS_CORE = (25.0, -15.0)     # core AI-infra (NVDA, MU, AVGO, AMD, TSM...)
TRIGGERS_SPEC = (40.0, -25.0)     # speculativos de alto octanaje (mas volatiles)
TRIGGERS_AR   = (35.0, -20.0)     # sleeve contrarian Argentina (bet de rebote)
SPEC_TICKERS  = {"OKLO", "ALAB", "IREN", "CRWV", "SMCI"}
AR_TICKERS    = {"YPF", "GGAL", "BMA", "BBAR", "PAM", "VIST", "CEPU", "EDN",
                 "SUPV", "TGS", "LOMA"}


def _spy_return_since(c, start_date):
    p0 = pr.price_on_or_before(c, pr.BENCHMARK, start_date)
    last = pr.latest_price(c, pr.BENCHMARK)
    if p0 and last and last[1]:
        return (last[1] / p0 - 1) * 100
    return None


def digest_portfolio(pf):
    rows, totals = pr.compute_portfolio_snapshot(pf["id"])
    head = f"=== {pf['name']}"
    if pf["label"]:
        head += f"  [{pf['label']}]"
    head += f"  (inicio {pf['start_date']}) ==="
    print("\n" + head)

    if not rows:
        print("    (sin posiciones todavía)")
        return

    ret = totals.get("total_ret_pct")
    cost = totals.get("total_cost")
    val = totals.get("total_value")

    positions = pr.list_positions(pf["id"])
    with pr.get_conn() as c:
        starts = [p["entry_date"] for p in positions]
        spy_ret = _spy_return_since(c, min(starts)) if starts else None
    alpha = (ret - spy_ret) if (ret is not None and spy_ret is not None) else None

    if cost and val:
        print(f"    Costo USD {cost:,.0f}  ·  Valor USD {val:,.0f}")
    print(f"    Retorno total : {ret:+.1f}%" if ret is not None else
          "    Retorno total : n/d (faltan precios)")
    if spy_ret is not None:
        print(f"    SPY (ventana) : {spy_ret:+.1f}%   ·   Alpha: {alpha:+.1f}%")

    valid = [r for r in rows if r["Ret%"] is not None]
    if valid:
        best = max(valid, key=lambda r: r["Ret%"])
        worst = min(valid, key=lambda r: r["Ret%"])
        print(f"    Mejor : {best['Ticker']} {best['Ret%']:+.1f}%    "
              f"Peor : {worst['Ticker']} {worst['Ret%']:+.1f}%")

    flags = []
    for r in valid:
        if r["Ticker"] in SPEC_TICKERS:
            tp, stop = TRIGGERS_SPEC
        elif r["Ticker"] in AR_TICKERS:
            tp, stop = TRIGGERS_AR
        else:
            tp, stop = TRIGGERS_CORE
        if r["Ret%"] >= tp:
            flags.append(f"[TP]   {r['Ticker']:5s} {r['Ret%']:+.1f}%  (>= {tp:+.0f}%)  -> revisar tomar ganancia")
        elif r["Ret%"] <= stop:
            flags.append(f"[STOP] {r['Ticker']:5s} {r['Ret%']:+.1f}%  (<= {stop:+.0f}%)  -> revisar cortar")
    if flags:
        print("    Señales (revisar; NO son órdenes):")
        for f in flags:
            print("      " + f)
    else:
        print("    Señales: ninguna hoy.")


def main():
    pr.init_db()
    print(f"DIGEST  {dt.date.today().isoformat()}  ·  carteras simuladas")
    print("(los precios son el último cierre en tu DB; actualizá precios para que sea de hoy)")

    pfs = pr.list_portfolios()
    if not pfs:
        print("\nNo hay carteras. Corré seed_cartera_simulada.py y seed_cartera_agresiva.py.")
        return

    for pf in pfs:
        digest_portfolio(pf)

    print("\n----")
    print("Pegá esta salida en el chat y lo analizamos. No es asesoramiento financiero.")


if __name__ == "__main__":
    main()
