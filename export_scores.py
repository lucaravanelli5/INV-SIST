"""
export_scores.py — Exporta el score de TODO el universo a un CSV para analizar.
==============================================================================
Corre el scoring sobre los ~415 tickers y guarda un CSV con: score compuesto,
las dimensiones (Q/Val/Gro/Saf/Mom...) y los ratios crudos (PE, ROE, etc.).
Subís ese CSV al chat y lo analizamos.

Uso:
    python export_scores.py                      # growth / medium-term (por defecto)
    python export_scores.py quality long-term
    python export_scores.py value medium-term

Estilos:    quality | value | GARP | growth | dividend | defensive
Horizontes: short-term | medium-term | long-term

Tip: las DIMENSIONES (Q/Val/Gro/Saf/Mom) casi no cambian con la lente; lo que
cambia es cómo se ponderan. Así que con un solo export que las incluya, yo puedo
re-pesar para cualquier estilo/horizonte sin que vuelvas a correr nada.

No inventa datos: usa lo que hay en research.db. No es asesoramiento financiero.
"""

import sys
import pandas as pd
import portfolio_research as pr
import screener_score as sc

STYLE   = sys.argv[1] if len(sys.argv) > 1 else "growth"
HORIZON = sys.argv[2] if len(sys.argv) > 2 else "medium-term"
MODE    = "sector"


def main():
    pr.init_db()
    fdf = pr.fundamentals_df()
    if fdf.empty:
        print("No hay fundamentals cargados. Actualizá ratios en el tablero (Screener).")
        return

    fdf = fdf.merge(pr.momentum_df(), on="Ticker", how="left")
    scored = sc.score(fdf, style=STYLE, horizon=HORIZON, mode=MODE, momentum_col="Mom%")

    # Traigo los ratios crudos de la DB para tener contexto, sin depender de
    # que 'scored' los conserve.
    with pr.get_conn() as c:
        raw = pd.read_sql_query("SELECT * FROM fundamentals", c)
    out = scored.merge(raw, left_on="Ticker", right_on="ticker",
                       how="left", suffixes=("", "_raw"))

    want = ["Ticker", "Sector", "Score", "Rating", "Cobertura",
            "Q", "Val", "Gro", "Saf", "Mom", "Inc",
            "pe", "forward_pe", "pb", "ev_ebitda", "roe", "profit_margin",
            "revenue_growth", "earnings_growth", "debt_to_equity",
            "dividend_yield", "Mom%"]
    cols = [c for c in want if c in out.columns]
    out = out[cols].sort_values("Score", ascending=False, na_position="last")

    fname = f"scored_universe_{STYLE}_{HORIZON}.csv"
    out.to_csv(fname, index=False)

    print(f"Guardado: {fname}   ({len(out)} filas)")
    print(f"Lente: estilo={STYLE}, horizonte={HORIZON}, modo={MODE}\n")
    show = [c for c in ["Ticker", "Sector", "Score", "Rating"] if c in out.columns]
    print("Top 15 por score:")
    print(out.head(15)[show].to_string(index=False))
    print(f"\n>>> Subí «{fname}» al chat y lo analizamos.")


if __name__ == "__main__":
    main()
