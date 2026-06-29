"""
score_cartera.py — Puntúa las acciones de una cartera con el score compuesto.
============================================================================
Corre el scoring sobre TODO el universo (para que los percentiles por sector
tengan sentido) y después muestra solo los tickers de la cartera elegida.

Uso:
    python score_cartera.py "<cartera>"                      # lente por defecto
    python score_cartera.py "<cartera>" <estilo> <horizonte>
    python score_cartera.py                                  # lista las carteras

Ejemplos:
    python score_cartera.py "Agresiva 3M jun-26(CP)"            # growth / short-term
    python score_cartera.py "Personal Balanz" quality medium-term
    python score_cartera.py "Personal Balanz" value long-term

Estilos:    quality | value | GARP | growth | dividend | defensive
Horizontes: short-term | medium-term | long-term

Regla práctica: trading agresivo -> growth/short-term (pesa momentum).
                hold de largo plazo -> quality o GARP / medium o long-term.

No inventa datos: usa los ratios que ya bajaste con yfinance. Lo que no tenga
ratios aparece con cobertura baja o se omite. Los ETFs casi no puntúan (no
tienen ROE/margen/crecimiento): juzgalos por lo que replican, no por el score.
No es asesoramiento financiero.
"""

import sys
import portfolio_research as pr
import screener_score as sc

DEFAULT_STYLE   = "growth"
DEFAULT_HORIZON = "short-term"
MODE            = "sector"

VALID_STYLES   = {"quality", "value", "GARP", "growth", "dividend", "defensive"}
VALID_HORIZONS = {"short-term", "medium-term", "long-term"}


def main():
    pr.init_db()
    pfs = pr.list_portfolios()

    if len(sys.argv) < 2:
        print("Carteras disponibles:")
        for p in pfs:
            print(f"  - {p['name']}")
        print('\nUso: python score_cartera.py "<cartera>" [estilo] [horizonte]')
        return

    name  = sys.argv[1]
    style = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_STYLE
    horiz = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_HORIZON

    if style not in VALID_STYLES:
        print(f"Estilo inválido: {style}. Opciones: {', '.join(sorted(VALID_STYLES))}")
        return
    if horiz not in VALID_HORIZONS:
        print(f"Horizonte inválido: {horiz}. Opciones: {', '.join(sorted(VALID_HORIZONS))}")
        return

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

    fdf = fdf.merge(pr.momentum_df(), on="Ticker", how="left")
    scored = sc.score(fdf, style=style, horizon=horiz, mode=MODE, momentum_col="Mom%")

    cols = [c for c in ["Ticker", "Sector", "Score", "Rating", "Cobertura",
                        "Q", "Val", "Gro", "Saf", "Mom"] if c in scored.columns]
    sub = scored[scored["Ticker"].str.upper().isin(tickers)][cols]
    sub = sub.sort_values("Score", ascending=False, na_position="last")

    print(f"\nScore de «{pf['name']}»   (estilo={style}, horizonte={horiz}, modo={MODE})\n")
    print(sub.to_string(index=False))

    missing = sorted(tickers - set(scored["Ticker"].str.upper()))
    if missing:
        print(f"\nSin ratios en la DB (no puntuables): {', '.join(missing)}")
    print("\nQ=calidad  Val=valuación  Gro=crecimiento  Saf=solidez  Mom=momentum (0–10).")
    print("Rating: Fuerte >=7.5 · Bueno >=5.5 · Regular >=3.5 · Flojo <3.5.")
    print("No es asesoramiento financiero.")


if __name__ == "__main__":
    main()
