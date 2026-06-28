"""
seed_cartera_agresiva.py
========================
Crea una SEGUNDA cartera simulada de 100.000 USD, agresiva y concentrada,
a 3 meses, alineada a las tendencias de IA-infra (jun-2026).

NO toca la cartera anterior ("Tesis research jun-26"): crea una nueva.

Uso (desde la carpeta del proyecto, con el venv activo):
    python seed_cartera_agresiva.py

Requisito: tener precios actualizados en research.db (botón "Actualizar
precios" o `python portfolio_research.py update`). El precio de entrada sale
del último cierre cargado en tu DB; NO se inventa. Si falta, saltea y avisa.

Es una SIMULACION. No es asesoramiento financiero.
"""

import datetime as dt
import portfolio_research as pr

PORTFOLIO_NAME  = "Agresiva 3M jun-26"
PORTFOLIO_LABEL = "agresiva / IA infra"
PORTFOLIO_NOTES = ("Cartera agresiva, concentrada, horizonte 3 meses. Maximo "
                   "retorno asumiendo mucho riesgo. Nucleo en IA-infra/memoria "
                   "(jun-26): lideres en pullback (NVDA/AVGO/AMD) + momentum de "
                   "memoria (MU) + speculativos de alto octanaje (ALAB/OKLO/CRWV). "
                   "Sleeve contrarian Argentina (YPF/GGAL): apuesta a rebote del "
                   "crudo y compresion de riesgo pais, contra la tendencia actual.")

# (ticker, monto_usd, nota con lectura de entrada/tendencia)
POSITIONS = [
    # --- Nucleo AI-infra (con la tendencia) ---
    ("NVDA", 17000, "Lider AI-infra; ~18% bajo su ATH, beta ~2,2 - entrada en pullback"),
    ("MU",   15000, "Super-ciclo memoria + guia disparada. OJO: +700% 1y, extendido"),
    ("AVGO", 15000, "Networking AI; cayo ~22% en una semana = mejor entrada"),
    ("AMD",  12000, "Alta beta; deal MI450/Meta 6GW; acompano la correccion"),
    # --- Speculativos de alto octanaje ---
    ("ALAB", 10000, "Connectivity AI, beta altisima - especulativo"),
    ("OKLO",  9000, "SMR (energia para IA), pre-ingresos - loteria"),
    ("CRWV",  9000, "Computo AI puro, beta muy alta - especulativo"),
    # --- Sleeve contrarian Argentina (contra la tendencia, apuesta de rebote) ---
    ("YPF",   8000, "O&G AR castigada por el crudo - bet contrarian a rebote"),
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
            print(f"[aviso] Ya existe una cartera <<{PORTFOLIO_NAME}>> (id {p['id']}).")
            print("        Borrala desde el tablero si querés recrearla, y reintentá.\n")
            return

    pid = pr.create_portfolio(
        name=PORTFOLIO_NAME, label=PORTFOLIO_LABEL,
        start_date=today, notes=PORTFOLIO_NOTES)

    added, skipped, invested = 0, [], 0.0
    for ticker, amount, note in POSITIONS:
        with pr.get_conn() as c:
            price = pr.price_on_or_before(c, ticker, today)
        if not price:
            skipped.append(ticker)
            print(f"  [skip] {ticker}: sin precio en la DB (actualizá precios y reintentá)")
            continue
        pr.add_position(
            portfolio_id=pid, ticker=ticker, price_entry=price,
            entry_date=today, amount_usd=amount, note=note)
        invested += amount
        added += 1
        print(f"  [ok]   {ticker:5s}  USD {amount:>6,}  @ {price:,.2f}")

    print(f"\nListo: {added} posiciones cargadas . USD {invested:,.0f} asignados.")
    if skipped:
        print(f"Faltaron precios para: {', '.join(skipped)}. "
              f"Actualizá precios y volvé a correr (o cargalas a mano).")
    print("\nAbrí el tablero -> tab 'Carteras simuladas' para verla.")


if __name__ == "__main__":
    main()
