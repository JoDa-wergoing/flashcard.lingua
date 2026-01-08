# src/io_utils.py
import csv
import re
from pathlib import Path
from typing import List

def read_wordlist(path: Path) -> List[str]:
    if not path.exists():
        return []
    if path.suffix.lower() == ".csv":
        out = []
        with path.open("r", encoding="utf-8", newline="") as f:
            rdr = csv.reader(f)
            for row in rdr:
                if not row: 
                    continue
                w = (row[0] or '').strip()
                if w: 
                    out.append(w)
        return out
    # txt
    return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]

def safe_filename(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")

def tokenize_words(text: str) -> List[str]:
    return re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿĀ-žḀ-ỿ]+(?:'[A-Za-zÀ-ÖØ-öø-ÿĀ-žḀ-ỿ]+)?", text)
