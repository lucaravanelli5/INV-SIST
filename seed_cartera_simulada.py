"""
seed_cartera_simulada.py
========================
Crea una cartera simulada de 100.000 USD en el tablero, a partir de las
convicciones de los informes de research (23-25/06/2026).

Uso (desde la carpeta del proyecto, con el venv activo):
    python seed_cartera_simulada.py

Requisitos previos:
    - Tener precios actualizados en research.db (boton "Actualizar precios"
      en el tablero, o `python portfolio_research.py update`). El script toma
      el PRECIO DE ENTRADA del cierre mas reciente que tengas cargado para
      cada ticker; NO inventa precios. Si a un ticker le falta precio, lo
      saltea y te avisa.

Nota: es una SIMULACION. No es asesoramiento financiero.
"""

import datetime as dt
import portfolio_research as pr

# --- Metadatos de la cartera -------------------------------------------------
PORTFOLIO_NAME  = "Tesis research jun-26"
PORTFOLIO_LABEL = "tematico + macro AR"
PORTFOLIO_NOTES = ("Cartera de simulacion armada con las convicciones de los "
                   "informes 23-25/06: infra de IA (picos y palas), megacap "
                   "como 'duenos de la energia' de la IA, rotacion ciclica, "
                   "y bloque Argentina (O&G Vaca Muerta + bancos por "
                   "desinflacion). Sin bonos: el tablero no simula bonos.")

# --- Posiciones: (ticker, monto_usd, nota). Total = 100.000 USD --------------
POSITIONS = [
    # --- Infra de IA (picos y palas) ~33k ---
    ("MU",    8000, "IA infra/memoria - valido demanda HBM (25/06)"),
    ("TSM",   8000, "IA infra - capex sin riesgo de modelo"),
    ("NVDA",  7000, "IA infra + pico-y-pala de robotica"),
    ("AVGO",  6000, "IA networking/infra"),
    ("ALAB",  4000, "IA connectivity (mas especulativo)"),
    # --- Megacap 'duenos de la energia de la IA' ~24k ---
    ("GOOGL", 8000, "Megacap - BDI buy; energia limpia para IA"),
    ("AMZN",  7000, "Megacap - incumbente en energia para data centers"),
    ("META",  5000, "Megacap - de-rating + capex IA"),
    ("MSFT",  4000, "Megacap - la rezagada (contrarian de-rating)"),
    # --- Energia para IA (opcion especulativa) ~3k ---
    ("OKLO",  3000, "SMR para data centers - especulativo, tamano chico"),
    # --- Rotacion ciclica / robotica / reshoring ~10k ---
    ("DE",    6000, "Rotacion ciclica + reshoring/robotica"),
    ("CAT",   4000, "Rotacion ciclica + reshoring"),
    # --- Argentina (macro) ~25k ---
    ("YPF",   6000, "O&G AR - Vaca Muerta (contracara: petroleo bajo)"),
    ("VIST",  4000, "O&G AR - Vaca Muerta"),
    ("PAM",   3000, "O&G/generacion AR"),
    ("GGAL",  5000, "Banco AR - desinflacion recompone rentabilidad"),
    ("BMA",   4000, "Banco AR - calidad de cartera"),
    ("CEPU",  3000, "Regulada AR - mejor binomio rentabilidad/precio"),
    # --- China (opcional, diversificacion) ~5k ---
    ("BABA",  5000, "China tech - barata, caja neta (riesgo regulatorio)"),
]


def main():
    today = dt.date.today().isoformat()
    pr.init_db()

    total = sum(a for _, a, _ in POSITIONS)
    print(f"Cartera: {PORTFOLIO_NAME}  .  total objetivo USD {total:,}")
    print(f"Fecha de inicio / entrada: {today}\n")

    # Evitar duplicar si ya existe una cartera con el mismo nombre
    for p in pr.list_portfolios():
        if p["name"] == PORTFOLIO_NAME:
            print(f"[aviso] Ya existe una cartera <<{PORTFOLIO_NAME}>> (id {p['id']}).")
            print("        Si querés recrearla, borrala primero desde el tablero")
            print("        (tab Carteras simuladas) y volvé a correr esto.\n")
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
            print(f"  [skip] {ticker}: sin precio en la DB "
                  f"(actualizá precios y reintentá)")
            continue
        pr.add_position(
            portfolio_id=pid, ticker=ticker, price_entry=price,
            entry_date=today, amount_usd=amount, note=note)
        invested += amount
        added += 1
        print(f"  [ok]   {ticker:5s}  USD {amount:>6,}  @ {price:,.2f}")

    print(f"\nListo: {added} posiciones cargadas . USD {invested:,.0f} asignados.")
    if skipped:
        print(f"Faltaron precios para: {', '.join(skipped)}.")
        print("Actualizá precios en el tablero y volvé a correr (o agregalas a mano).")
    print("\nAbrí el tablero -> tab 'Carteras simuladas' para verla y seguir su evolución.")


if __name__ == "__main__":
    main()
