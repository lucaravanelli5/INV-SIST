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

PORTFOLIO_NAME  = "Agresiva 3M jun-26(CP)"
PORTFOLIO_LABEL = "agresiva / IA infra"
PORTFOLIO_NOTES = ("Cartera agresiva, concentrada, horizonte 3 meses. Maximo "
                   "retorno asumiendo mucho riesgo. v2: revisada con el score "
                   "compuesto. Nucleo IA-infra que combina momentum Y fundamentals "
                   "(NVDA/MU/AVGO/TSM/AMD), un solo speculativo con ingresos (ALAB), "
                   "y sleeve contrarian Argentina (YPF/GGAL). Se sacaron OKLO y CRWV: "
                   "pre-ingresos / margenes finos, el score no los puede validar.")

# (ticker, monto_usd, nota con lectura de entrada/tendencia)
POSITIONS = [
    # --- Nucleo AI-infra (alto momentum Y fundamentals que el score premia) ---
    ("NVDA", 18000, "Lider AI-infra; pullback ~18% bajo ATH. Score: calidad+crec+momentum altos"),
    ("MU",   16000, "Memoria: margenes y crecimiento disparados (score alto). CAP por riesgo de ciclo"),
    ("AVGO", 16000, "Networking AI; pullback -22% semanal mejora entrada; fundamentals solidos"),
    ("TSM",  14000, "NUEVO: el AI-infra de mejor calidad/valuacion; entra alto en el score"),
    ("AMD",  12000, "Alta beta + crecimiento data center; valuacion cara (la pata mas floja del nucleo)"),
    # --- Unico speculativo (con ingresos reales, puntuable) ---
    ("ALAB", 11000, "Connectivity AI, beta altisima; tiene ingresos (a diferencia de OKLO/CRWV)"),
    # --- Sleeve contrarian Argentina (apuesta de rebote; el score la castiga por momentum) ---
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
