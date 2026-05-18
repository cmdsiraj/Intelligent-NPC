import os
import yaml
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/scenarios", tags=["scenarios"])

SCENARIOS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scenarios")


@router.get("")
def list_scenarios():
    if not os.path.exists(SCENARIOS_DIR):
        return {"scenarios": []}
    files = [f for f in os.listdir(SCENARIOS_DIR) if f.endswith(".yaml")]
    result = []
    for f in files:
        path = os.path.join(SCENARIOS_DIR, f)
        with open(path, "r", encoding="utf-8") as fh:
            cfg = yaml.safe_load(fh)
        result.append({
            "filename":    f,
            "name":        cfg.get("name", f),
            "description": cfg.get("description", ""),
            "ticks":       cfg.get("ticks", 10),
            "npc_count":   len(cfg.get("npcs", [])),
        })
    return {"scenarios": result}


@router.get("/{filename}")
def get_scenario(filename: str):
    path = os.path.join(SCENARIOS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Scenario '{filename}' not found")
    with open(path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    return cfg
