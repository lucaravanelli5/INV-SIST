"""
seed_cartera_personal.py — Carga tu cartera REAL de Balanz en el tablero.
========================================================================
Lee las posiciones desde un CSV PRIVADO y NO versionado:
    private/cartera_personal.csv
Asi este archivo .py se puede subir al repo, pero tus tenencias reales NO
(la carpeta private/ y el .csv estan en .gitignore).

CSV esperado (una fila por tenencia). Columnas (las vacias se permiten):
    ticker,shares,amount_usd,price_entry,entry_date,note
  - ticker:      symbol como en yfinance (el subyacente del CEDEAR/ADR: AAPL, NVDA, YPF...)
  - shares:      cantidad de acciones equivalentes.  (usá ESTO **o** amount_usd)
  - amount_usd:  alternativa a shares: monto invertido en USD.
  - price_entry: precio PROMEDIO de compra en USD. Si lo dejas vacio, toma el
                 ultimo cierre cargado en tu DB (NO inventa precios).
  - entry_date:  AAAA-MM-DD. Si vacio, usa hoy.
  - note:        texto libre (opcional).

Uso:
    python seed_cartera_personal.py

OJO: los BONOS no entran en este modulo (se siguen en el tab Bonos). Cargá acá
solo acciones/CEDEARs/ADRs con precio de yfinance.

Es tu cartera real: esto NO es asesoramiento financiero, solo la carga para
poder seguirla con las mismas herramientas.
"""

import os
import csv
import datetime as dt
import portfolio_research as pr

CSV_PATH        = os.path.join("private", "cartera_personal.csv")
PORTFOLIO_NAME  = "Personal Balanz"
PORTFOLIO_LABEL = "real (privada)"
PORTFOLIO_NOTES = ("Cartera real en Balanz. Datos desde private/cartera_personal.csv "
                   "(no versionado). Solo acciones/CEDEARs; los bonos van en el tab Bonos.")


def _num(x):
    try:
        return float(str(x).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None


def main():
    if not os.path.exists(CSV_PATH):
        print(f"No encuentro {CSV_PATH}.")
        print("Creá la carpeta 'private/' y adentro 'cartera_personal.csv' con columnas:")
        print("   ticker,shares,amount_usd,price_entry,entry_date,note")
        return

    pr.init_db()
    today = dt.date.today().isoformat()

    for p in pr.list_portfolios():
        if p["name"] == PORTFOLIO_NAME:
            print(f"[aviso] Ya existe «{PORTFOLIO_NAME}» (id {p['id']}). "
                  f"Borrala desde el tablero si querés recargarla.")
            return

    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for d in csv.DictReader(f):
            t = (d.get("ticker") or "").strip().upper()
            if not t:
                continue
            rows.append({
                "ticker": t,
                "shares": _num(d.get("shares")),
                "amount_usd": _num(d.get("amount_usd")),
                "price_entry": _num(d.get("price_entry")),
                "entry_date": (d.get("entry_date") or "").strip() or today,
                "note": (d.get("note") or "").strip(),
            })
    if not rows:
        print("El CSV no tiene filas válidas.")
        return

    pid = pr.create_portfolio(name=PORTFOLIO_NAME, label=PORTFOLIO_LABEL,
                              start_date=today, notes=PORTFOLIO_NOTES)

    added, skipped = 0, []
    for r in rows:
        price = r["price_entry"]
        if price is None:
            with pr.get_conn() as c:
                price = pr.price_on_or_before(c, r["ticker"], r["entry_date"])
        if price is None:
            skipped.append(f"{r['ticker']} (sin precio)")
            print(f"  [skip] {r['ticker']}: sin precio (poné price_entry en el CSV o actualizá precios)")
            continue

        shares, amount = r["shares"], r["amount_usd"]
        if shares is not None:
            amount = None                      # preferí shares si están ambos
        if shares is None and amount is None:
            skipped.append(f"{r['ticker']} (sin cantidad)")
            print(f"  [skip] {r['ticker']}: falta 'shares' o 'amount_usd'")
            continue

        pr.add_position(portfolio_id=pid, ticker=r["ticker"], price_entry=price,
                        entry_date=r["entry_date"], shares=shares,
                        amount_usd=amount, note=r["note"])
        added += 1
        qty = f"{shares:g} sh" if shares is not None else f"USD {amount:,.0f}"
        print(f"  [ok]   {r['ticker']:6s} {qty:>12s} @ {price:,.2f}")

    print(f"\nListo: {added} posiciones cargadas.")
    if skipped:
        print(f"Saltadas: {', '.join(skipped)}")
    print("Abrí el tab «Carteras simuladas» para verla.")


if __name__ == "__main__":
    main()
