import streamlit as st, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core import Cfg, scenario, run, metrics
from src.assistant import answer
st.set_page_config(page_title="GoodWe EV Commerce Hub", layout="wide")
st.title("⚡ GoodWe EV Commerce Hub — recarga inteligente para comércio")
c = Cfg(pv_kwp=st.sidebar.slider("FV (kWp)", 20, 150, 100), n_chargers=st.sidebar.slider("Carregadores HCA", 2, 12, 6),
        grid_limit_kw=st.sidebar.slider("Demanda contratada (kW)", 40, 200, 90), seed=int(st.sidebar.number_input("Semente", 1, 999, 7)))
sc = scenario(c); dfb, ib = run(c, sc, False); dfs, i_s = run(c, sc, True); mb, ms = metrics(dfb, c, ib), metrics(dfs, c, i_s)
for col, (k, lab) in zip(st.columns(4), [("pico_rede_kw", "Pico rede (kW)"), ("custo_energia_rs", "Custo energia (R$)"),
                                         ("ev_solar_pct", "VE com sol (%)"), ("co2_evitado_kg", "CO₂ evitado (kg)")]):
    col.metric(lab, ms[k], f"{ms[k]-mb[k]:+.1f} vs. sem gestão",
               delta_color="inverse" if k in ("pico_rede_kw", "custo_energia_rs") else "normal")
st.subheader("Potência na rede (kW) — sem gestão vs. inteligente")
st.line_chart({"Sem gestão": dfb.set_index("h").grid, "Inteligente": dfs.set_index("h").grid})
st.subheader("Fluxos (kW)"); st.area_chart(dfs.set_index("h")[["pv", "load", "ev"]])
st.subheader("Bateria (SoC %)"); st.line_chart(dfs.set_index("h").soc_bat)
hora = st.slider("Hora do dia", 0.0, 23.9, 12.0, 0.1); row = dfs.iloc[min(int(hora / c.dt), len(dfs) - 1)].to_dict()
q = st.text_input("💬 Pergunte ao assistente (ex.: 'quanto CO2 evitamos?')")
if q: st.info(answer(q, ms, row))
st.json({"sem_gestao": mb, "inteligente": ms})
