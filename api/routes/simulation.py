import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.state import manager

router = APIRouter(prefix="/simulation", tags=["simulation"])


class SaveRequest(BaseModel):
    filename: str


class LoadStateRequest(BaseModel):
    path: str


@router.get("/state")
def get_state():
    if not manager.active:
        raise HTTPException(status_code=400, detail="No scenario loaded")
    return manager.get_full_state()


@router.post("/save")
def save_state(req: SaveRequest):
    if not manager.active:
        raise HTTPException(status_code=400, detail="No scenario loaded")
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    path = os.path.join(root, "saves", f"{req.filename}.json")
    manager.save(path)
    return {"ok": True, "path": path}


@router.post("/load-state")
def load_saved_state(req: LoadStateRequest):
    if not manager.active:
        raise HTTPException(status_code=400, detail="No scenario loaded first")
    manager.load_state(req.path)
    return {"ok": True, "state": manager.get_full_state()}
