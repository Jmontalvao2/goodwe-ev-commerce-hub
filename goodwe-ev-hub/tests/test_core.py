import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core import Cfg, scenario, run, metrics
def test_smart_beats_baseline():
    c = Cfg(); sc = scenario(c); b = run(c, sc, False); s = run(c, sc, True)
    mb, ms = metrics(*b[:1], c, b[1]), metrics(*s[:1], c, s[1])
    assert ms["pico_rede_kw"] <= mb["pico_rede_kw"] and ms["custo_energia_rs"] <= mb["custo_energia_rs"]

from src.assistant import answer
def test_demanda_contratada_respeitada():
    c = Cfg(); df, _ = run(c, scenario(c), True)
    assert df.grid.max() <= c.grid_limit_kw + 1e-6
def test_assistente_variacoes():
    m = dict(ev_solar_pct=1, co2_evitado_kg=2, margem_rs=3, receita_rs=4, custo_energia_rs=5, pico_rede_kw=6)
    row = dict(pv=1.0, grid=2.0, soc_bat=50, bat=1.0, plugged=2, ev=3.0)
    assert "CO₂" in answer("quanto CO₂ evitamos?", m, row) and "evitamos 2" in answer("quanto CO2 evitamos?", m, row)
    assert "Margem" in answer("quanto custa a energia?", m, row)
    assert "FV gera" in answer("como está o sol?", m, row)
    assert "Bateria" in answer("bateria no pico?", m, row)
    assert "FV gera" not in answer("como está o console?", m, row)
