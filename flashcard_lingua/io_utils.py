import csv
import hashlib
import re
from pathlib import Path
from typing import List


def read_wordlist(path: Path) -> List[str]:
    if not path.exists():
        return []

    if path.suffix.lower() == ".csv":
        out: List[str] = []
        with path.open("r", encoding="utf-8", newline="") as f:
            rdr = csv.reader(f)
            for row in rdr:
                if not row:
                    continue
                w = (row[0] or "").strip()
                if w:
                    out.append(w)
        return out

    return [
        ln.strip()
        for ln in path.read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]


def safe_filename(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def tokenize_words(text: str) -> List[str]:
    return re.findall(r"[^\W\d_]+", text, flags=re.UNICODE)


def media_hash(text: str, prefix: str = "", length: int = 12) -> str:
    raw = f"{prefix}|{text}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:length]


def word_audio_filename(word: str, source_lang: str, ext: str = "mp3") -> str:
    h = media_hash(word, prefix=f"{source_lang}|word")
    return f"{h}_w.{ext}"


def example_audio_filename(example_text: str, source_lang: str, ext: str = "mp3") -> str:
    h = media_hash(example_text, prefix=f"{source_lang}|example")
    return f"{h}_ex.{ext}"
