"""Gêmeo digital de um hub comercial de recarga de VEs (GoodWe): FV + bateria + carregadores AC."""
import numpy as np, pandas as pd
from dataclasses import dataclass

@dataclass
class Cfg:
    pv_kwp: float = 100         # FV com inversor GoodWe trifásico (série MT/ET)
    n_chargers: int = 6         # carregadores AC GoodWe HCA
    charger_kw: float = 22
    grid_limit_kw: float = 90   # demanda contratada
    bat_kwh: float = 40         # bateria GoodWe Lynx
    bat_kw: float = 20
    bat_min: float = 0.10
    tar_off: float = 0.55; tar_peak: float = 1.90; peak: tuple = (18, 21)  # R$/kWh (premissas)
    price_ev: float = 2.20; export_price: float = 0.25
    grid_co2: float = 0.0385    # kgCO2/kWh rede BR (premissa; ajustar)
    ice_co2_km: float = 0.17; ev_kwh_km: float = 0.16
    arrivals_h: float = 2.2; seed: int = 7; dt: float = 5 / 60

def scenario(c: Cfg):
    r = np.random.default_rng(c.seed); n = int(24 / c.dt); h = np.arange(n) * c.dt
    cloud = np.clip(0.4 + 1.2 * np.convolve(r.random(n), np.ones(12) / 12, "same"), 0.4, 1)
    pv = c.pv_kwp * 0.85 * np.clip(np.sin(np.pi * (h - 6) / 12), 0, None) ** 1.3 * cloud
    load = 18 + 22 * ((h >= 8) & (h < 20)) + r.normal(0, 1.5, n)
    arr = []
    for i in range(n):
        if 8 <= h[i] < 19:
            for _ in range(r.poisson(c.arrivals_h * c.dt)):
                arr.append(dict(i=i, cap=float(r.choice([40, 55, 64, 75])), soc=r.uniform(.15, .5), tgt=.8,
                                pmax=float(min(r.choice([7.4, 11, 22]), c.charger_kw)), stay=r.uniform(1, 4)))
    return h, pv, load, arr

def run(c: Cfg, sc, smart: bool):
    h, pv, load, arr = sc; dt = c.dt; evs = []; rows = []; k = 0
    sb = 0.5 * c.bat_kwh; lost = unmet = served = 0
    for i in range(len(h)):
        while k < len(arr) and arr[k]["i"] == i:
            e = dict(arr[k]); k += 1
            if len(evs) < c.n_chargers: e["dep"] = h[i] + e["stay"]; evs.append(e); served += 1
            else: lost += 1
        keep = []
        for e in evs:
            if e["soc"] >= e["tgt"] - 1e-6: continue
            if h[i] >= e["dep"]: unmet += (e["tgt"] - e["soc"]) * e["cap"]; continue
            keep.append(e)
        evs = keep
        peak = c.peak[0] <= h[i] < c.peak[1]; net = load[i] - pv[i]; surplus = max(0, -net)
        rem = [(e["tgt"] - e["soc"]) * e["cap"] for e in evs]
        if smart:   # just-in-time (menor folga) + reforço com excedente solar
            p = [min(e["pmax"], 2 * r_ / max(e["dep"] - h[i], dt)) for e, r_ in zip(evs, rem)]
            spare = surplus - sum(p)
            for j, e in enumerate(evs):
                if spare <= 0: break
                a = max(0, min(e["pmax"] - p[j], spare, rem[j] / dt - p[j])); p[j] += a; spare -= a
        else:
            p = [min(e["pmax"], r_ / dt) for e, r_ in zip(evs, rem)]
        pb = 0.0; tot = net + sum(p)
        if smart:
            if peak or tot > c.grid_limit_kw:
                pb = min(c.bat_kw, max(0, tot - (0 if peak else c.grid_limit_kw)), max(0, sb - c.bat_min * c.bat_kwh) / dt)
            elif tot < 0:
                pb = -min(c.bat_kw, -tot, (c.bat_kwh - sb) / dt)
            sb -= pb * dt if pb > 0 else pb * dt * 0.95
            if tot - pb > c.grid_limit_kw and sum(p) > 0:   # gerenciamento de demanda
                f = max(0, 1 - (tot - pb - c.grid_limit_kw) / sum(p)); p = [x * f for x in p]
        for e, x in zip(evs, p): e["soc"] += x * dt / e["cap"]
        grid = net + sum(p) - pb
        rows.append(dict(h=h[i], pv=pv[i], load=load[i], ev=sum(p), bat=pb, grid=grid, soc_bat=sb / c.bat_kwh * 100,
                         peak=peak, ev_solar=min(sum(p), max(pv[i] - load[i], 0)), plugged=len(evs)))
    df = pd.DataFrame(rows)
    return df, dict(lost=lost, served=served, unmet_kwh=unmet)

def metrics(df, c, info):
    dt = c.dt; imp = df.grid.clip(lower=0); exp = (-df.grid).clip(lower=0)
    price = np.where(df.peak, c.tar_peak, c.tar_off)
    cost = float(((imp * price) - exp * c.export_price).sum() * dt)
    ev = float(df.ev.sum() * dt); sol = float(df.ev_solar.sum() * dt)
    ev_co2 = (ev - sol) * c.grid_co2; avoided = ev / c.ev_kwh_km * c.ice_co2_km - ev_co2
    return dict(ev_kwh=round(ev, 1), ev_solar_pct=round(100 * sol / max(ev, 1e-9), 1),
                pico_rede_kw=round(float(df.grid.max()), 1), custo_energia_rs=round(cost, 2),
                receita_rs=round(ev * c.price_ev, 2), margem_rs=round(ev * c.price_ev - cost, 2),
                autoconsumo_fv_pct=round(100 * (1 - float(exp.sum()) / float(df.pv.sum())), 1),
                import_pico_kwh=round(float(imp[df.peak].sum() * dt), 1),
                co2_evitado_kg=round(avoided, 1), nao_atendido_kwh=round(info["unmet_kwh"], 1),
                veiculos_atendidos=info["served"], veiculos_perdidos=info["lost"])
