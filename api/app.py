"""
FastAPI application entry point.
Run from the project root:
    uvicorn api.app:app --reload --port 8000
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from api.routes.scenarios import router as scenarios_router
from api.routes.simulation import router as simulation_router
from api.ws.handler import handle_websocket

app = FastAPI(title="Intelligent NPC API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scenarios_router)
app.include_router(simulation_router)


@app.get("/")
def root():
    return {"status": "ok", "service": "intelligent-npc-api"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await handle_websocket(websocket)
