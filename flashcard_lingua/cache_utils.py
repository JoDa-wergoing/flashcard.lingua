# src/cache_utils.py
import json
from pathlib import Path
from typing import Dict, Any

def make_cache_key(word: str, cfg: Dict, usage_notes: str, backend_name: str) -> str:
    model_name = cfg.get("TEXT_MODEL_OPENAI", cfg.get("TEXT_MODEL_GOOGLE", ""))
    return f"{backend_name}:{model_name}/{usage_notes}/{word}"

def cache_read(cache_dir: Path, key: str):
    fname = cache_dir / (key.replace("/", "_").replace(":", "_") + ".json")
    if fname.exists():
        try:
            return json.loads(fname.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None

def cache_write(cache_dir: Path, key: str, data: Dict[str, Any]) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    fname = cache_dir / (key.replace("/", "_").replace(":", "_") + ".json")
    fname.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def load_state(state_path: Path) -> Dict[str, Any]:
    if state_path.exists():
        try:
            return json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_state(state_path: Path, state: Dict[str, Any]) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
