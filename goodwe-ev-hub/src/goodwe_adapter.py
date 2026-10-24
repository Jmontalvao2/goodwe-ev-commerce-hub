"""Adaptador GoodWe: leitura REAL via biblioteca `goodwe` (UDP/Modbus) ou fallback simulado."""
import asyncio

async def read_real(host: str) -> dict:
    import goodwe  # pip install goodwe
    inv = await goodwe.connect(host)
    d = await inv.read_runtime_data()
    return {"pv_kw": d.get("ppv", 0) / 1000, "bat_soc": d.get("battery_soc"),
            "load_kw": d.get("house_consumption", 0) / 1000, "grid_w": d.get("active_power")}

def read(host=None, sim_row=None) -> dict:
    if host:
        try: return asyncio.run(read_real(host))
        except Exception as ex: print("GoodWe indisponível, usando simulação:", ex)
    r = sim_row or {}
    return {"pv_kw": r.get("pv", 0), "bat_soc": r.get("soc_bat"), "load_kw": r.get("load", 0), "grid_w": r.get("grid", 0) * 1000}

class ChargerHCA:
    """Interface de comando do carregador (na prática via SEMS Portal / Modbus-TCP / OCPP)."""
    def __init__(self, cid, max_kw=22): self.cid, self.max_kw, self.setpoint = cid, max_kw, 0.0
    def set_power(self, kw): self.setpoint = max(0.0, min(kw, self.max_kw)); return self.setpoint
