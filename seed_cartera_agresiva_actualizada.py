"""
seed_cartera_agresiva_CP_VST.py — Cartera NUEVA: la (CP) + VST.
==============================================================
Crea una cartera ADICIONAL, no toca ninguna existente. Es la "Agresiva (CP)"
pero con VST (Vistra) incorporado: la pata de "energia para IA" con fundamentals
reales (ROE ~43%, crecimiento ~43%, forward PE ~15), financiada recortando AMD
(12k->6k) y ALAB (11k->5k). Sirve para comparar en paralelo (CP) vs (CP+VST).

Uso (desde la carpeta del proyecto, con el venv activo):
    1) Actualizá precios (asegurate de que VST tenga precio en la DB).
    2) python seed_cartera_agresiva_CP_VST.py

No borra nada. El precio de entrada sale del último cierre cargado en tu DB;
NO se inventa. Es una SIMULACION. No es asesoramiento financiero.
"""

import datetime as dt
import portfolio_research as pr

PORTFOLIO_NAME  = "Agresiva 3M jun-26(CP+VST)"
PORTFOLIO_LABEL = "agresiva / IA infra + energia"
PORTFOLIO_NOTES = ("Variante de la (CP) con VST agregado (energia para IA con "
                   "fundamentals), financiado recortando AMD y ALAB. Existe en "
                   "paralelo a la (CP) original para comparar el efecto de sumar VST.")

# (ticker, monto_usd, nota)
POSITIONS = [
    ("NVDA", 18000, "Lider AI-infra; pullback bajo ATH; calidad+crec+momentum altos"),
    ("MU",   16000, "Memoria: margenes y crecimiento disparados. CAP por riesgo de ciclo"),
    ("AVGO", 16000, "Networking AI; fundamentals solidos"),
    ("TSM",  14000, "El AI-infra de mejor calidad/valuacion; score alto"),
    ("VST",  12000, "NUEVO: energia para IA. ROE ~43%, crec ~43%, fwd PE ~15. OJO deuda alta"),
    ("YPF",   8000, "O&G AR castigada por el crudo - bet contrarian a rebote"),
    ("AMD",   6000, "Recortado (12->6): valuacion cara, la pata mas floja del nucleo tech"),
    ("ALAB",  5000, "Recortado (11->5): especulativo; se le saca al pop de +16%"),
    ("GGAL",  5000, "Banco AR - desinflacion; bet a compresion de riesgo pais"),
]


def main():
    today = dt.date.today().isoformat()
    pr.init_db()

    total = sum(a for _, a, _ in POSITIONS)
    print(f"Cartera: {PORTFOLIO_NAME}  .  total objetivo USD {total:,}")
    print(f"Fecha de inicio / entrada: {today}\n")

    for p in pr.list_portfolios():
        if p["name"] == PORTFOLIO_NAME:
            print(f"[aviso] Ya existe «{PORTFOLIO_NAME}» (id {p['id']}). "
                  f"Borrala desde el tablero si querés recrearla.\n")
            return

    pid = pr.create_portfolio(name=PORTFOLIO_NAME, label=PORTFOLIO_LABEL,
                              start_date=today, notes=PORTFOLIO_NOTES)

    added, skipped, invested = 0, [], 0.0
    for ticker, amount, note in POSITIONS:
        with pr.get_conn() as c:
            price = pr.price_on_or_before(c, ticker, today)
        if not price:
            skipped.append(ticker)
            print(f"  [skip] {ticker}: sin precio en la DB (actualizá precios y reintentá)")
            continue
        pr.add_position(portfolio_id=pid, ticker=ticker, price_entry=price,
                        entry_date=today, amount_usd=amount, note=note)
        invested += amount
        added += 1
        print(f"  [ok]   {ticker:5s}  USD {amount:>6,}  @ {price:,.2f}")

    print(f"\nListo: {added} posiciones cargadas . USD {invested:,.0f} asignados.")
    if skipped:
        print(f"Faltaron precios para: {', '.join(skipped)}. Actualizá y reintentá.")
    print("\nAbrí el tab 'Carteras simuladas' para verla, al lado de la (CP).")


if __name__ == "__main__":
    main()
