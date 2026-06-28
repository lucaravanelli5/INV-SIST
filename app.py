"""
app.py  —  Tablero web local (Streamlit)
========================================
  pip install streamlit
  streamlit run app.py
Junto a portfolio_research.py, universe_cedears.csv y universe_bonds.csv.

NOVEDAD (23/06/2026): el Screener suma "Canastas temáticas" — botones de un
toque que filtran el universo a los candidatos del informe con los ratios y el
orden ya seteados. Editá THEMATIC_BASKETS para ajustarlos.

NOVEDAD (26/06/2026): nueva solapa "📁 Carteras simuladas" — simulá carteras
de tesis (como MarketWatch pero local). Múltiples carteras con etiqueta y fecha
de inicio; posiciones por cantidad de acciones o por monto en USD; retorno,
alpha vs SPY, pesos y curva histórica de valor.
"""

import datetime as _dt
import streamlit as st
import portfolio_research as pr
import screener_score as sc

st.set_page_config(page_title="Research personal", layout="wide")
pr.init_db()
pr.seed_recommendations()
pr.seed_bonds()

have, total = pr.coverage()

st.title("📊 Mi tablero de research")
st.caption("Herramienta personal de apoyo a la decisión. No es asesoramiento financiero.")
st.markdown(f"**Universo acciones:** {total} · **Ratios cargados:** {have}/{total}")

c1, c2, c3 = st.columns([1.1, 1.4, 1.2])
with c1:
    if st.button("🔄 Actualizar precios (universo)"):
        with st.spinner("Bajando precios en lotes..."):
            pr.update_prices()
        st.success("Precios actualizados")
with c2:
    n = st.number_input("Ratios por tanda", 10, 200, 50, step=10)
    if st.button(f"🔄 Traer {int(n)} ratios"):
        with st.spinner("Bajando ratios..."):
            pr.update_fundamentals(limit=int(n))
        st.success("Hecho")
with c3:
    st.info("1ª vez: actualizá precios y traé ratios en tandas hasta 200/200.")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["📋 Scorecard", "🔎 Screener", "💹 Precio", "🇦🇷 Bonos", "📄 Informes",
     "📁 Carteras simuladas"])

# --- Tab 1: scorecard --------------------------------------------------------
with tab1:
    st.subheader("¿Cómo vienen las recomendaciones cargadas?")
    df = pr.scorecard_df()
    if df.empty or "Ret%" not in df.columns:
        st.warning("Todavía no hay precios. Apretá 'Actualizar precios' arriba.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption("Ret% = retorno desde el informe · Bench% = SPY misma ventana · "
                   "Alpha% = Ret% − Bench% · aObj% = avance al precio objetivo")

# --- Tab 2: SCREENER ---------------------------------------------------------
NUM_COLS = ["P/E", "P/E fwd", "P/BV", "FV/EBITDA", "ROE%", "Margen%", "Div.Yield", "MktCap",
            "CrecVtas%", "CrecGan%", "Deuda/Eq", "Liq.Corr", "Mom%"]
DEFAULTS = {"f_pe": False, "v_pe": 20.0, "f_pb": False, "v_pb": 3.0,
            "f_evt": False, "v_evt": 15.0, "f_roe": False, "v_roe": 15.0,
            "f_mar": False, "v_mar": 10.0, "f_dy": False, "v_dy": 0.03}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)
# estado extra para canastas y orden
st.session_state.setdefault("basket", None)
st.session_state.setdefault("order_by", "Score")
st.session_state.setdefault("asc_label", "Mayor→Menor")

# --- Canastas temáticas (del informe 23/06/2026) -----------------------------
THEMATIC_BASKETS = {
    "🤖 IA semis & net": {
        "tickers": ["NVDA", "AVGO", "MRVL", "ALAB", "TSM", "ASML", "AMAT",
                    "MU", "ARM", "QCOM", "SMH"],
        "filters": {"f_roe": True, "v_roe": 15.0, "f_mar": True, "v_mar": 15.0},
        "order_by": "FV/EBITDA", "asc": True},
    "🖥️ IA cómputo": {
        "tickers": ["CRWV", "IREN", "DELL", "SMCI", "HPQ"],
        "filters": {"f_mar": True, "v_mar": 5.0, "f_pb": True, "v_pb": 8.0},
        "order_by": "FV/EBITDA", "asc": True},
    "⚛️ IA energía": {
        "tickers": ["OKLO"],
        "filters": {},
        "order_by": "MktCap", "asc": False},
    "📉 Megacap de-rating": {
        "tickers": ["GOOGL", "GOOG", "MSFT", "META", "AMZN"],
        "filters": {"f_roe": True, "v_roe": 18.0, "f_mar": True, "v_mar": 18.0},
        "order_by": "P/E fwd", "asc": True},
    "🛡️ Ciber": {
        "tickers": ["CRWD", "PANW", "NET"],
        "filters": {},
        "order_by": "P/E fwd", "asc": True},
    "🛢️ Petróleo (cautela)": {
        "tickers": ["XOM", "CVX", "COP", "OXY", "SLB", "SHEL", "BP", "TTE", "ENB"],
        "filters": {"f_pe": True, "v_pe": 15.0, "f_dy": True, "v_dy": 0.03},
        "order_by": "Div.Yield", "asc": False},
    "🇨🇳 China tech": {
        "tickers": ["BABA", "BIDU", "PDD", "JD", "NTES"],
        "filters": {"f_pe": True, "v_pe": 15.0, "f_pb": True, "v_pb": 3.0},
        "order_by": "P/E", "asc": True},
    "🏦 Bancos AR": {
        "tickers": ["GGAL", "BMA", "BBAR", "SUPV"],
        "filters": {"f_roe": True, "v_roe": 15.0},
        "order_by": "P/BV", "asc": True},
    "⛽ O&G AR": {
        "tickers": ["YPF", "PAM", "VIST", "TGS"],
        "filters": {},
        "order_by": "FV/EBITDA", "asc": True},
    "🔌 Reguladas AR": {
        "tickers": ["CEPU", "EDN"],
        "filters": {"f_roe": True, "v_roe": 12.0},
        "order_by": "Div.Yield", "asc": False},
}


def _apply_basket(b):
    upd = {k: False for k in DEFAULTS if k.startswith("f_")}
    upd.update(b["filters"])
    upd["basket"] = list(b["tickers"])
    upd["order_by"] = b["order_by"]
    upd["asc_label"] = "Menor→Mayor" if b["asc"] else "Mayor→Menor"
    st.session_state.update(upd)
    st.rerun()


with tab2:
    st.subheader("Screener: filtrá y rankeá el universo")
    fdf = pr.fundamentals_df()
    if fdf.empty:
        st.warning("Todavía no hay ratios. Traelos con el botón de arriba.")
    else:
        # --- Score compuesto (estilo + horizonte + modo) --------------------
        with st.expander("⚙️ Score compuesto", expanded=True):
            scc1, scc2, scc3 = st.columns(3)
            estilo = scc1.selectbox(
                "Estilo",
                ["quality", "value", "GARP", "growth", "dividend", "defensive"],
                key="score_style")
            horiz = scc2.selectbox(
                "Horizonte", ["long-term", "medium-term", "short-term"],
                key="score_horizon")
            modo_lbl = scc3.selectbox(
                "Modo", ["Por sector (recomendado)", "Umbrales absolutos"],
                key="score_mode")
            modo = "sector" if modo_lbl.startswith("Por sector") else "absolute"
            st.caption("Por sector: cada empresa se compara con las de su rubro. "
                       "Sectores con menos de 5 empresas usan umbrales fijos.")
        # Se puntúa TODO el universo, para que los percentiles usen todos los pares.
        fdf = fdf.merge(pr.momentum_df(), on="Ticker", how="left")   # agrega "Mom%"
        fdf = sc.score(fdf, style=estilo, horizon=horiz, mode=modo,
                       momentum_col="Mom%")

        with st.expander("🧺 Canastas temáticas (del informe 23/06)", expanded=False):
            st.caption("Un toque = filtra a esos tickers con ratios y orden ya seteados. "
                       "Los que no tengan ratios cargados no aparecen.")
            names = list(THEMATIC_BASKETS.keys())
            row1 = st.columns(5)
            for i, name in enumerate(names[:5]):
                if row1[i].button(name, use_container_width=True, key=f"bk_{i}"):
                    _apply_basket(THEMATIC_BASKETS[name])
            row2 = st.columns(5)
            for j, name in enumerate(names[5:]):
                if row2[j].button(name, use_container_width=True, key=f"bk_{j+5}"):
                    _apply_basket(THEMATIC_BASKETS[name])

        st.write("**Presets** (después podés ajustar a mano):")
        p1, p2, p3, p4 = st.columns(4)
        if p1.button("💲 Value"):
            st.session_state.update({"f_pe": True, "v_pe": 15.0, "f_pb": True, "v_pb": 2.0,
                                     "f_roe": False, "f_mar": False, "f_dy": False, "f_evt": False,
                                     "basket": None})
            st.rerun()
        if p2.button("⭐ Calidad"):
            st.session_state.update({"f_roe": True, "v_roe": 15.0, "f_mar": True, "v_mar": 10.0,
                                     "f_pe": False, "f_pb": False, "f_dy": False, "f_evt": False,
                                     "basket": None})
            st.rerun()
        if p3.button("💵 Dividendos"):
            st.session_state.update({"f_dy": True, "v_dy": 0.03, "f_pe": False, "f_pb": False,
                                     "f_roe": False, "f_mar": False, "f_evt": False,
                                     "basket": None})
            st.rerun()
        if p4.button("🧹 Limpiar"):
            st.session_state.update({k: False for k in DEFAULTS if k.startswith("f_")})
            st.session_state["basket"] = None
            st.rerun()

        st.divider()
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            st.checkbox("Filtrar P/E", key="f_pe")
            st.number_input("P/E máximo", 0.0, 500.0, step=1.0, key="v_pe")
            st.checkbox("Filtrar P/BV", key="f_pb")
            st.number_input("P/BV máximo", 0.0, 100.0, step=0.5, key="v_pb")
        with fc2:
            st.checkbox("Filtrar FV/EBITDA", key="f_evt")
            st.number_input("FV/EBITDA máximo", 0.0, 500.0, step=1.0, key="v_evt")
            st.checkbox("Filtrar ROE", key="f_roe")
            st.number_input("ROE% mínimo", -100.0, 300.0, step=1.0, key="v_roe")
        with fc3:
            st.checkbox("Filtrar Margen", key="f_mar")
            st.number_input("Margen% mínimo", -100.0, 100.0, step=1.0, key="v_mar")
            st.checkbox("Filtrar Div.Yield", key="f_dy")
            st.number_input("Div.Yield mínimo (crudo)", 0.0, 1.0, step=0.005,
                            format="%.3f", key="v_dy")

        sectores = sorted([s for s in fdf["Sector"].dropna().unique()])
        sel = st.multiselect("Sector", sectores)

        v = fdf.copy()
        s = st.session_state
        if s.f_pe:  v = v[v["P/E"].notna() & (v["P/E"] > 0) & (v["P/E"] <= s.v_pe)]
        if s.f_pb:  v = v[v["P/BV"].notna() & (v["P/BV"] <= s.v_pb)]
        if s.f_evt: v = v[v["FV/EBITDA"].notna() & (v["FV/EBITDA"] <= s.v_evt)]
        if s.f_roe: v = v[v["ROE%"].notna() & (v["ROE%"] >= s.v_roe)]
        if s.f_mar: v = v[v["Margen%"].notna() & (v["Margen%"] >= s.v_mar)]
        if s.f_dy:  v = v[v["Div.Yield"].notna() & (v["Div.Yield"] >= s.v_dy)]
        if sel:     v = v[v["Sector"].isin(sel)]

        basket = st.session_state.get("basket")
        if basket:
            have_set = set(fdf["Ticker"])
            missing = [t for t in basket if t not in have_set]
            bc1, bc2 = st.columns([4, 1])
            bc1.info("🧺 Canasta activa: " + ", ".join(basket))
            if bc2.button("✖ Quitar canasta"):
                st.session_state["basket"] = None
                st.rerun()
            if missing:
                st.caption("Sin ratios cargados (no aparecen): " + ", ".join(missing))
            v = v[v["Ticker"].isin(basket)]

        oc1, oc2 = st.columns([2, 1])
        with oc1:
            order_by = st.selectbox("Ordenar por", ["Score"] + NUM_COLS, key="order_by")
        with oc2:
            asc = st.radio("Orden", ["Menor→Mayor", "Mayor→Menor"],
                           horizontal=True, key="asc_label") == "Menor→Mayor"
        v = v.sort_values(order_by, ascending=asc, na_position="last")
        st.caption(f"**{len(v)}** de {len(fdf)} empresas cumplen los filtros.")
        st.dataframe(v, use_container_width=True, hide_index=True)

# --- Tab 3: precio -----------------------------------------------------------
with tab3:
    tickers = pr.list_price_tickers()
    if not tickers:
        st.warning("Primero actualizá precios.")
    else:
        t = st.selectbox("Elegí una acción", tickers)
        h = pr.price_history_df(t)
        if h.empty:
            st.info("No hay historial para ese ticker.")
        else:
            ratios = pr.load_cedear_ratios()
            ratio = ratios.get(t)
            modo = st.radio("Ver precio en",
                            ["USD (acción subyacente)", "ARS (CEDEAR, estimado)"],
                            horizontal=True, key="precio_moneda")

            if modo.startswith("ARS") and ratio is None:
                st.warning(f"No tengo el ratio de conversión de **{t}** cargado en "
                           f"`{pr.RATIOS_FILE}`. Puede ser un ADR argentino que se compra "
                           f"local (no es CEDEAR) o que falte cargarlo. Lo muestro en USD.")
                modo = "USD"

            if modo.startswith("ARS"):
                ccl = st.session_state.get("ccl_valor")
                cca, ccb = st.columns([1, 3])
                if cca.button("🔄 Traer CCL") or ccl is None:
                    with st.spinner("Trayendo CCL..."):
                        ccl = pr.fetch_ccl()
                    st.session_state["ccl_valor"] = ccl
                if not ccl:
                    st.error("No pude traer el CCL ahora (probá de nuevo o revisá tu "
                             "conexión). Muestro en USD.")
                    st.line_chart(h.set_index("date")["close"], height=380)
                    st.caption(f"Cierre ajustado de {t} (USD).")
                else:
                    hp = h.copy()
                    hp["close"] = hp["close"] * ccl / ratio
                    st.line_chart(hp.set_index("date")["close"], height=380)
                    ult = hp["close"].iloc[-1]
                    st.metric(f"Precio CEDEAR estimado de {t}", f"$ {ult:,.0f}")
                    rtxt = f"{ratio:g}:1" if ratio >= 1 else f"1:{1 / ratio:g}"
                    st.caption(f"Estimado = precio acción (USD) × CCL ÷ ratio. "
                               f"CCL ≈ $ {ccl:,.0f} · ratio {rtxt}. Usa el CCL de **hoy**, "
                               f"así que los valores de fechas pasadas son orientativos (el "
                               f"CCL de cada día era distinto). Comparalo con el último precio "
                               f"de Balanz, no con el histórico.")
            else:
                st.line_chart(h.set_index("date")["close"], height=380)
                cap = f"Cierre ajustado de {t} (acción subyacente, USD)."
                if ratio:
                    cap += f" Ratio CEDEAR {ratio:g}:1." if ratio >= 1 else \
                           f" Ratio CEDEAR 1:{1 / ratio:g}."
                st.caption(cap)

# --- Tab 4: BONOS ------------------------------------------------------------
with tab4:
    st.subheader("Bonos soberanos argentinos")
    bca, bcb = st.columns([1.4, 2])
    with bca:
        if st.button("🔄 Actualizar bonos (precio + TIR)"):
            with st.spinner("Bajando precios de data912 y calculando..."):
                nq = pr.update_bond_prices()
                nc = pr.update_bond_metrics()
            if nq:
                st.success(f"{nq} precios traídos · TIR/duration/paridad de {nc} bonos")
            else:
                st.error("No se pudo traer precios de data912 (¿sin internet o bloqueo?).")
            st.rerun()
    with bcb:
        hc, tc = pr.cashflow_coverage()
        st.caption(f"Todo automático: el **precio** viene de data912 (delay ~2h) y la "
                   f"**TIR, duration y paridad** las calcula la herramienta con el flujo de "
                   f"fondos. **{hc}/{tc}** bonos con flujo cargado.")

    bdf = pr.bonds_df().rename(columns={
        "ticker": "Bono", "name": "Nombre", "law": "Ley", "maturity": "Vence",
        "price": "Precio USD", "tir": "TIR %", "parity": "Paridad %",
        "duration": "Duration", "updated_at": "Act."})
    cols = ["Bono", "Nombre", "Ley", "Vence", "Precio USD", "TIR %",
            "Paridad %", "Duration", "Act."]
    st.dataframe(bdf[cols], use_container_width=True, hide_index=True)

    with st.expander("Ver panel completo de data912 (todos los símbolos disponibles)"):
        qdf = pr.bond_quotes_df()
        if qdf.empty:
            st.caption("Todavía no trajiste precios. Apretá el botón de arriba.")
        else:
            st.dataframe(qdf, use_container_width=True, hide_index=True)

    cdf = pr.bonds_df().dropna(subset=["duration", "tir"])
    if not cdf.empty:
        st.write("**Curva: TIR vs duration** (cada punto un bono)")
        st.scatter_chart(cdf, x="duration", y="tir", color="ticker", height=340)
        st.caption("Por encima de la curva = más TIR para igual plazo (los relativamente baratos).")
    else:
        st.info("Apretá 'Actualizar bonos' para calcular y ver la curva.")

    st.divider()
    st.write("**Riesgo país (EMBI, en puntos básicos)**")
    if st.button("🔄 Actualizar riesgo país (automático)"):
        with st.spinner("Bajando la serie de ArgentinaDatos..."):
            nr = pr.update_riesgo_pais_auto()
        if nr:
            st.success(f"{nr} días de riesgo país actualizados")
        else:
            st.error("No se pudo traer (¿sin internet o bloqueo temporal?).")
        st.rerun()
    rpdf = pr.riesgo_pais_df()
    if not rpdf.empty:
        st.line_chart(rpdf.set_index("date")["value"], height=260)
    else:
        st.caption("Apretá 'Actualizar riesgo país (automático)' para traer la serie.")

# --- Tab 5: INFORMES ---------------------------------------------------------
with tab5:
    st.subheader("Bitácora de research")
    st.caption("Tus informes diarios en un solo lugar. Formato principal: Markdown "
               "(.md), que se lee acá adentro. Si dejás un .pdf o .tex con el mismo "
               "nombre al lado, aparecen como descarga.")

    with st.expander("⬆️ Subir un informe"):
        up = st.file_uploader("Archivo (.md, .pdf o .tex)",
                              type=["md", "pdf", "tex"], key="rep_upload")
        if up is not None:
            saved = st.session_state.setdefault("_saved_uploads", set())
            if up.name not in saved:
                pr.save_report(up.name, up.getvalue())
                saved.add(up.name)
                st.success(f"Guardado: {up.name}")
        st.caption(f"Se guardan en la carpeta `{pr.REPORTS_DIR}/`, al lado de la app. "
                   f"Convención de nombre: `informe_research_AAAAMMDD.md`.")

    reports = pr.list_reports()
    if not reports:
        st.info(f"Todavía no hay informes. Generá uno en .md y ponelo en la carpeta "
                f"`{pr.REPORTS_DIR}/` (o subilo arriba).")
    else:
        q = st.text_input("🔎 Buscar en los informes",
                          placeholder="ej: GD41, Vaca Muerta, riesgo país")
        if q:
            hits = pr.search_reports(q)
            if not hits:
                st.warning("Sin coincidencias.")
            else:
                st.caption(f"{len(hits)} informe(s) mencionan «{q}»:")
                for item, snippet in hits:
                    st.markdown(f"**{item['date']} — {item['title']}**  \n…{snippet}")
            st.divider()

        labels = [f"{r['date']} — {r['title']}" for r in reports]
        idx = st.selectbox("Elegí un informe", range(len(reports)),
                           format_func=lambda i: labels[i])
        sel = reports[idx]
        base = sel["path"].rsplit(".", 1)[0]
        stem = sel["file"].rsplit(".", 1)[0]

        d1, d2, d3 = st.columns(3)
        with open(sel["path"], "rb") as f:
            d1.download_button("⬇️ .md", f.read(), file_name=sel["file"],
                               mime="text/markdown", use_container_width=True)
        if sel["has_pdf"]:
            with open(base + ".pdf", "rb") as f:
                d2.download_button("⬇️ .pdf", f.read(), file_name=stem + ".pdf",
                                   mime="application/pdf", use_container_width=True)
        if sel["has_tex"]:
            with open(base + ".tex", "rb") as f:
                d3.download_button("⬇️ .tex", f.read(), file_name=stem + ".tex",
                                   mime="text/x-tex", use_container_width=True)

        st.divider()
        st.markdown(pr.read_report(sel["path"]))

# =============================================================================
# --- Tab 6: CARTERAS SIMULADAS -----------------------------------------------
# =============================================================================
with tab6:
    st.subheader("Carteras simuladas")
    st.caption(
        "Simulá carteras de tesis (tipo MarketWatch, pero local y sin login). "
        "Cada cartera tiene nombre, etiqueta y fecha de inicio. "
        "Las posiciones usan los precios del subyacente en USD (yfinance). "
        "No es asesoramiento financiero; es una herramienta de seguimiento de ideas."
    )

    # ---- Panel izquierdo: gestión de carteras | Panel derecho: detalle ------
    left, right = st.columns([1, 2.4])

    with left:
        st.markdown("#### Mis carteras")

        # Crear nueva cartera
        with st.expander("➕ Nueva cartera", expanded=False):
            new_name  = st.text_input("Nombre", placeholder="Tesis IA jun-26",
                                      key="new_pf_name")
            new_label = st.text_input("Etiqueta (opcional)",
                                      placeholder="IA / macro / bonos",
                                      key="new_pf_label")
            new_start = st.date_input("Fecha de inicio",
                                      value=_dt.date.today(),
                                      key="new_pf_start")
            new_notes = st.text_area("Notas (tesis resumida)", height=80,
                                     key="new_pf_notes")
            if st.button("Crear cartera", use_container_width=True):
                if not new_name.strip():
                    st.error("El nombre no puede estar vacío.")
                else:
                    pr.create_portfolio(
                        name=new_name.strip(),
                        label=new_label.strip(),
                        start_date=str(new_start),
                        notes=new_notes.strip())
                    st.success(f"Cartera «{new_name}» creada.")
                    st.rerun()

        # Listado de carteras
        pfls = pr.list_portfolios()
        if not pfls:
            st.info("Todavía no creaste ninguna cartera.")
            st.stop()

        pf_labels = [
            f"{p['name']}" + (f"  [{p['label']}]" if p["label"] else "")
            + f"\n{p['start_date']}"
            for p in pfls
        ]
        sel_idx = st.radio(
            "Seleccioná una cartera",
            range(len(pfls)),
            format_func=lambda i: pf_labels[i],
            key="sel_pf_idx",
        )
        sel_pf = pfls[sel_idx]

        st.divider()

        # Editar / eliminar la cartera seleccionada
        with st.expander("✏️ Editar / eliminar cartera"):
            ed_name  = st.text_input("Nombre", value=sel_pf["name"],  key="ed_pf_name")
            ed_label = st.text_input("Etiqueta", value=sel_pf["label"] or "",
                                     key="ed_pf_label")
            ed_start = st.date_input(
                "Fecha de inicio",
                value=_dt.date.fromisoformat(sel_pf["start_date"]),
                key="ed_pf_start")
            ed_notes = st.text_area("Notas", value=sel_pf["notes"] or "",
                                    height=80, key="ed_pf_notes")
            if st.button("💾 Guardar cambios", use_container_width=True):
                pr.update_portfolio_meta(
                    sel_pf["id"], ed_name.strip(), ed_label.strip(),
                    str(ed_start), ed_notes.strip())
                st.success("Guardado.")
                st.rerun()

            st.divider()
            confirm_del = st.checkbox(
                f"⚠️ Confirmar eliminación de «{sel_pf['name']}»",
                key="confirm_del_pf")
            if st.button("🗑️ Eliminar cartera", disabled=not confirm_del,
                         use_container_width=True):
                pr.delete_portfolio(sel_pf["id"])
                st.success("Cartera eliminada.")
                st.rerun()

    # ---- Panel derecho: posiciones + métricas de la cartera seleccionada ----
    with right:
        pf_id   = sel_pf["id"]
        pf_name = sel_pf["name"]
        pf_label = sel_pf["label"] or ""
        pf_start = sel_pf["start_date"]
        pf_notes = sel_pf["notes"] or ""

        header_txt = f"### {pf_name}"
        if pf_label:
            header_txt += f"  `{pf_label}`"
        st.markdown(header_txt)
        if pf_notes:
            st.caption(f"Tesis: {pf_notes}")
        st.caption(f"Inicio: {pf_start}")

        # ---- Agregar posición -----------------------------------------------
        with st.expander("➕ Agregar posición", expanded=False):
            all_tickers = pr.list_price_tickers()
            ticker_input = st.selectbox(
                "Ticker", [""] + all_tickers, key=f"pos_ticker_{pf_id}",
                help="Solo aparecen tickers con precios descargados. "
                     "Si el que buscás no está, actualizá precios primero.")

            pos_date = st.date_input(
                "Fecha de entrada", value=_dt.date.today(),
                key=f"pos_date_{pf_id}")

            # --- Precio de referencia: buscar en la DB para el ticker + fecha ---
            # Muestra el precio histórico de esa fecha (o el más cercano anterior)
            # y lo usa como valor por defecto del campo precio de entrada.
            ref_price = None
            if ticker_input:
                with pr.get_conn() as _c:
                    ref_price = pr.price_on_or_before(
                        _c, ticker_input, str(pos_date))
                    current_price_row = pr.latest_price(_c, ticker_input)

                current_price = current_price_row[1] if current_price_row else None
                current_date  = current_price_row[0] if current_price_row else None

                # Mostrar precio actual como referencia
                if current_price:
                    st.info(
                        f"**{ticker_input}** — precio más reciente en tu DB: "
                        f"**USD {current_price:,.2f}** ({current_date}). "
                        f"El precio de entrada se precargó con el cierre de la fecha elegida."
                    )
                else:
                    st.warning(
                        f"No hay precios descargados para {ticker_input}. "
                        "Actualizá precios desde el botón de arriba antes de agregar la posición."
                    )

                if ref_price is None:
                    st.caption(
                        f"⚠️ No hay cierre disponible para {ticker_input} en o antes del "
                        f"{pos_date} en tu DB. Ingresá el precio manualmente."
                    )

            # Valor por defecto del campo: precio histórico si existe, sino 1.0
            price_default = float(ref_price) if ref_price else 1.0

            pos_mode = st.radio(
                "Definir posición por",
                ["Cantidad de acciones", "Monto en USD"],
                horizontal=True, key=f"pos_mode_{pf_id}")

            col_a, col_b = st.columns(2)
            with col_a:
                if pos_mode == "Cantidad de acciones":
                    pos_shares = st.number_input(
                        "Cantidad (shares)", min_value=0.0001, value=1.0,
                        step=1.0, format="%.4f", key=f"pos_shares_{pf_id}")
                    pos_amount = None
                else:
                    pos_amount = st.number_input(
                        "Monto (USD)", min_value=0.01, value=1000.0,
                        step=100.0, key=f"pos_amount_{pf_id}")
                    pos_shares = None
            with col_b:
                pos_price = st.number_input(
                    "Precio de entrada (USD)", min_value=0.001,
                    value=price_default, step=0.01, format="%.2f",
                    key=f"pos_price_{pf_id}",
                    help="Precio del subyacente en USD (acción, no CEDEAR). "
                         "Se precarga con el cierre de yfinance de la fecha elegida. "
                         "Podés editarlo si querés usar un precio distinto (ej: el de Balanz).")
                if ref_price and ticker_input:
                    st.caption(
                        f"Precargado con el cierre de {ticker_input} "
                        f"del {pos_date} según yfinance."
                    )

            pos_note = st.text_input(
                "Nota (opcional)", placeholder="p.ej. tesis IA capex",
                key=f"pos_note_{pf_id}")

            if st.button("Agregar", use_container_width=True, key=f"btn_add_{pf_id}"):
                if not ticker_input:
                    st.error("Elegí un ticker.")
                elif pos_price <= 0:
                    st.error("El precio de entrada tiene que ser mayor a 0.")
                else:
                    pr.add_position(
                        portfolio_id=pf_id,
                        ticker=ticker_input,
                        price_entry=pos_price,
                        entry_date=str(pos_date),
                        shares=pos_shares,
                        amount_usd=pos_amount,
                        note=pos_note.strip())
                    st.success(f"Posición en {ticker_input} agregada.")
                    st.rerun()

        st.divider()

        # ---- Snapshot actual ------------------------------------------------
        rows, totals = pr.compute_portfolio_snapshot(pf_id)

        if not rows:
            st.info("Esta cartera no tiene posiciones todavía. Agregá una arriba.")
        else:
            # métricas resumen
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("Posiciones", totals.get("n_positions", 0))
            mc2.metric("Costo base", f"USD {totals['total_cost']:,.0f}"
                       if totals.get("total_cost") else "—")
            mc3.metric("Valor actual", f"USD {totals['total_value']:,.0f}"
                       if totals.get("total_value") else "—")
            ret_val = totals.get("total_ret_pct")
            mc4.metric("Retorno total", f"{ret_val:+.1f}%" if ret_val is not None else "—",
                       delta=f"{ret_val:+.1f}%" if ret_val is not None else None)

            st.markdown("**Posiciones**")

            import pandas as pd
            pos_df = pd.DataFrame(rows)

            # columnas que mostramos (sin pos_id interno)
            display_cols = ["Ticker", "Entrada", "Shares", "Costo base",
                            "P. entrada", "P. actual", "Valor USD",
                            "Ret%", "Alpha%", "Peso%", "Nota"]
            st.dataframe(
                pos_df[display_cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Ret%":   st.column_config.NumberColumn("Ret%",   format="%.1f%%"),
                    "Alpha%": st.column_config.NumberColumn("Alpha%", format="%.1f%%"),
                    "Peso%":  st.column_config.NumberColumn("Peso%",  format="%.1f%%"),
                    "Costo base": st.column_config.NumberColumn("Costo base", format="$%.2f"),
                    "Valor USD":  st.column_config.NumberColumn("Valor USD",  format="$%.2f"),
                    "P. entrada": st.column_config.NumberColumn("P. entrada", format="$%.2f"),
                    "P. actual":  st.column_config.NumberColumn("P. actual",  format="$%.2f"),
                }
            )
            st.caption(
                "Alpha% = Ret% − retorno de SPY en la misma ventana de cada posición. "
                "Precio = subyacente en USD (yfinance, sin ajuste de CCL ni ratio CEDEAR)."
            )

            # ---- Eliminar posición ------------------------------------------
            with st.expander("🗑️ Eliminar una posición"):
                if rows:
                    del_options = {
                        f"{r['Ticker']} — entrada {r['Entrada']} "
                        f"({'%.4g shares' % r['Shares'] if r['Shares'] else 'monto'})": r["pos_id"]
                        for r in rows
                    }
                    del_label = st.selectbox(
                        "Posición a eliminar", list(del_options.keys()),
                        key=f"del_pos_{pf_id}")
                    if st.button("Eliminar posición seleccionada",
                                 key=f"btn_del_pos_{pf_id}"):
                        pr.remove_position(del_options[del_label])
                        st.success("Posición eliminada.")
                        st.rerun()

            st.divider()

            # ---- Gráfico histórico ------------------------------------------
            st.markdown("**Evolución histórica del valor (USD)**")
            freq_sel = st.radio("Frecuencia", ["Semanal", "Diaria"],
                                horizontal=True, key=f"freq_{pf_id}")
            freq_map = {"Semanal": "W", "Diaria": "D"}
            hist = pr.portfolio_history_df(pf_id, freq=freq_map[freq_sel])

            if hist.empty or "value_usd" not in hist.columns:
                st.info("No hay suficiente historial de precios para graficar. "
                        "Actualizá precios desde el botón de arriba.")
            else:
                chart_data = hist.set_index("date")[["value_usd"]]
                if "spy_norm" in hist.columns:
                    chart_data["SPY (norm.)"] = hist.set_index("date")["spy_norm"]
                st.line_chart(chart_data, height=340)
                st.caption(
                    "Valor de la cartera en USD a lo largo del tiempo. "
                    "SPY (norm.) = SPY escalado al valor inicial de la cartera, "
                    "para comparar la evolución relativa."
                )

            # ---- Distribución por ticker (torta simple) ---------------------
            val_by_ticker = {
                r["Ticker"]: r["Valor USD"]
                for r in rows if r["Valor USD"] is not None
            }
            if len(val_by_ticker) > 1:
                st.markdown("**Distribución del valor por ticker**")
                pie_df = pd.DataFrame(
                    list(val_by_ticker.items()), columns=["Ticker", "Valor USD"]
                ).sort_values("Valor USD", ascending=False)
                st.bar_chart(pie_df.set_index("Ticker"), height=220)
