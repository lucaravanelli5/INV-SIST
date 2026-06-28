"""
score_cartera.py — Puntúa las acciones de una cartera con el score compuesto.
============================================================================
Corre el scoring sobre TODO el universo (para que los percentiles por sector
tengan sentido) y después muestra solo los tickers de la cartera elegida.

Uso:
    python score_cartera.py "Agresiva 3M jun-26"
    python score_cartera.py              # sin argumento: lista las carteras

Lente por defecto, pensada para una cartera AGRESIVA de CORTO PLAZO:
    estilo = growth, horizonte = short-term
(En short-term el momentum pesa x1.6 y calidad/valuación/solidez se descuentan:
 es la vara correcta para esta cartera. Si la puntuás con quality/long-term
 —el default del tablero— los nombres agresivos se ven mal a propósito.)

No inventa datos: usa los ratios que ya bajaste con yfinance. Lo que no tenga
ratios aparece con cobertura baja o 's/d'. No es asesoramiento financiero.
"""

import sys
import portfolio_research as pr
import screener_score as sc

STYLE   = "growth"
HORIZON = "short-term"
MODE    = "sector"      # percentil intra-sector; cae a umbrales si <5 pares


def main():
    pr.init_db()
    pfs = pr.list_portfolios()

    if len(sys.argv) < 2:
        print("Carteras disponibles:")
        for p in pfs:
            print(f"  - {p['name']}")
        print('\nUso: python score_cartera.py "<nombre de la cartera>"')
        return

    name = sys.argv[1]
    pf = next((p for p in pfs if p["name"] == name), None)
    if not pf:
        print(f"No encuentro la cartera <<{name}>>. Corré sin argumento para ver la lista.")
        return

    tickers = {pos["ticker"].upper() for pos in pr.list_positions(pf["id"])}
    if not tickers:
        print("La cartera no tiene posiciones.")
        return

    fdf = pr.fundamentals_df()
    if fdf.empty:
        print("No hay ratios cargados. Traelos con el botón del tablero (Screener).")
        return

    # Scoreamos TODO el universo y después filtramos (los percentiles necesitan los pares)
    fdf = fdf.merge(pr.momentum_df(), on="Ticker", how="left")
    scored = sc.score(fdf, style=STYLE, horizon=HORIZON, mode=MODE, momentum_col="Mom%")

    cols = [c for c in ["Ticker", "Sector", "Score", "Rating", "Cobertura",
                        "Q", "Val", "Gro", "Saf", "Mom"] if c in scored.columns]
    sub = scored[scored["Ticker"].str.upper().isin(tickers)][cols]
    sub = sub.sort_values("Score", ascending=False, na_position="last")

    print(f"\nScore de «{pf['name']}»   (estilo={STYLE}, horizonte={HORIZON}, modo={MODE})\n")
    print(sub.to_string(index=False))

    missing = sorted(tickers - set(scored["Ticker"].str.upper()))
    if missing:
        print(f"\nSin ratios en la DB (no se pudieron puntuar): {', '.join(missing)}")
    print("\nQ=calidad  Val=valuación  Gro=crecimiento  Saf=solidez  Mom=momentum (0–10).")
    print("Rating: Fuerte >=7.5 · Bueno >=5.5 · Regular >=3.5 · Flojo <3.5.")
    print("No es asesoramiento financiero.")


if __name__ == "__main__":
    main()
