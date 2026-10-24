import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); os.chdir(ROOT)   # funciona de qualquer diretório
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from src.core import Cfg, scenario, run, metrics
os.makedirs("results", exist_ok=True); os.makedirs("docs", exist_ok=True); c = Cfg(); sc = scenario(c)
dfb, ib = run(c, sc, False); dfs, i_s = run(c, sc, True); mb, ms = metrics(dfb, c, ib), metrics(dfs, c, i_s)
dfb.to_csv("results/baseline.csv", index=False); dfs.to_csv("results/inteligente.csv", index=False)
json.dump({"sem_gestao": mb, "inteligente": ms}, open("results/metricas.json", "w"), indent=2, ensure_ascii=False)
fig, ax = plt.subplots(3, 1, figsize=(11, 10), sharex=True)
ax[0].plot(dfb.h, dfb.grid, label="Sem gestão"); ax[0].plot(dfs.h, dfs.grid, label="Inteligente")
ax[0].axhline(c.grid_limit_kw, ls="--", c="r", label="Demanda contratada"); ax[0].set_ylabel("Rede (kW)"); ax[0].legend()
ax[1].plot(dfs.h, dfs.pv, label="FV"); ax[1].plot(dfs.h, dfs.load, label="Comércio"); ax[1].plot(dfs.h, dfs.ev, label="VEs"); ax[1].set_ylabel("kW"); ax[1].legend()
ax[2].plot(dfs.h, dfs.soc_bat, c="g"); ax[2].set_ylabel("SoC bateria (%)"); ax[2].set_xlabel("Hora"); plt.tight_layout(); plt.savefig("docs/resultado_simulacao.png", dpi=130)
rows = "\n".join(f"| {k} | {mb[k]} | {ms[k]} |" for k in mb)
tab = f"| Métrica | Sem gestão | Inteligente |\n|---|---|---|\n{rows}"
t = open("README.md", encoding="utf8").read()
open("README.md", "w", encoding="utf8").write(re.sub(r"<!--R-->.*?<!--/R-->", lambda m: f"<!--R-->\n{tab}\n<!--/R-->", t, flags=re.S))
print(tab)
