# Inverter Load Manager

A web app that manages appliance load against an 800W invertor capacity, auto-shedding low-priority appliances when needed and auto restoring them when capacity frees up.

## Tech Stack
-Backend: Python, FastAPI, SQLite
-Frontend: React(Vite)

## How to run it

**Backend:**
```bash
cd backend
source venv/bin/activate        #Windows: venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL given in the frontend terminal.
Backend will start on http://localhost:8000.
APIs can be seen at http://localhost:8000/docs.


## Design Notes

- State is a single cloumn ('running'/'off'/'shed'), not separate booleans - avoid contradictory states.
- Shed/resstore logic lives in 'load_manager.py', isolated from the API layer.
- Auto-restore walks shed application in priority order(most important first).
- Explicit OFF on a shed application cancels it permanently, per spec.
- Event log records every change with its cause, surfaced in the UI rejections.