from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import database
import load_manager as lm
from models import ApplianceCreate, ApplianceStateUpdate

app = FastAPI(title="Inverter Load Manager")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
database.init_db()

def run(fn, *args):
    with database.get_db() as conn:

        try: 
            fn(conn, *args)
        except lm.ApplianceNotFound as e:
            raise HTTPException(404, str(e))
        except lm.CapacityRejected as e:
            raise HTTPException(409, e.message)
        return lm.get_status(conn)

@app.get("/status")
def get_status():
    with database.get_db() as conn:
        return lm.get_status(conn)


@app.post("/appliances", status_code=201)
def create_appliance(p: ApplianceCreate):
    return run(lambda c, *_: lm.register_appliance(c, p.name, p.wattage, p.priority))

@app.delete("/appliances/{appliance_id}")
def delete_appliance(appliance_id: int):
    return run(lm.delete_appliance, appliance_id)

@app.post("/appliances/{appliance_id}/state")
def set_state(appliance_id: int, p: ApplianceStateUpdate):
    action = lm.turn_on if p.action == 'on' else lm.turn_off
    return run(action, appliance_id)

@app.get("/events")
def get_events():
    with database.get_db() as conn:
        rows = conn.execute("SELECT * FROM event_log ORDER BY id DESC LIMIT 100").fetchall()
        return [dict(r) for r in rows]