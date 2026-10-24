"""Assistente virtual PT-BR (intenções). Pode ser exposto a Alexa/Google via webhook."""
import re

def answer(q: str, m: dict, row: dict) -> str:
    q = q.lower().replace("₂", "2")   # aceita "CO₂" e "CO2"
    has = lambda pat: re.search(pat, q) is not None
    if has(r"bateria"):   # antes de "pico/rede" para "bateria no pico" cair aqui
        return f"Bateria em {row['soc_bat']:.0f}% e {'descarregando' if row['bat'] > 0 else 'carregando/em espera'} ({abs(row['bat']):.1f} kW)."
    if has(r"solar|\bsol\b|\bfv\b|painel|painéis|paineis"):
        return f"Agora o FV gera {row['pv']:.1f} kW. {m['ev_solar_pct']}% da energia dos VEs no dia vem direto do sol."
    if has(r"co2|carbono|ambient"):
        return f"Hoje evitamos {m['co2_evitado_kg']} kg de CO₂ frente a veículos a combustão."
    if has(r"cust|econom|lucro|margem"):   # "cust" cobre custo/custa
        return f"Margem do dia: R$ {m['margem_rs']} (receita R$ {m['receita_rs']} - energia R$ {m['custo_energia_rs']})."
    if has(r"pico|demanda|\brede\b"):
        return f"Pico na rede: {m['pico_rede_kw']} kW. Agora: {row['grid']:.1f} kW."
    if has(r"carregador|vaga|livre|ocupad"):
        return f"{int(row['plugged'])} veículo(s) carregando agora, consumindo {row['ev']:.1f} kW."
    return "Posso falar de: energia solar, CO₂, custo/margem, pico de demanda, bateria e carregadores."
