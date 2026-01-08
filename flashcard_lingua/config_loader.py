# src/config_loader.py
import json
from pathlib import Path

def load_config(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"config.json niet gevonden op: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
