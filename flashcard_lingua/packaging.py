# src/packaging.py
import genanki
import hashlib
import re
from pathlib import Path
from typing import List, Dict

def _stable_id(text: str) -> int:
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()
    return int(h[:8], 16)

def _collect_media_from_rows(rows: List[List[str]]) -> List[str]:
    sound_re = re.compile(r"\[sound:([^\]]+)\]", re.IGNORECASE)
    seen = set()
    ordered = []
    for r in rows:
        for cell in (r or []):
            for f in sound_re.findall(cell or ""):
                if f not in seen:
                    seen.add(f)
                    ordered.append(f)
    return ordered

def build_apkg(cfg: Dict, rows: List[List[str]], media_dir: Path) -> Path:
    deck_name   = cfg.get("DECK_NAME", "My Deck")
    model_name  = cfg.get("MODEL_NAME", "My Model")
    apkg_path   = Path(cfg.get("APKG_PATH", "out/anki_deck.apkg"))
    source_lang = cfg.get("SOURCE_LANG", "Bron")
    target_lang = cfg.get("TARGET_LANG", "Doel")
    show_new    = bool(cfg.get("SHOW_NEW_WORDS_ON_BACK", True))

    fields = [
        {"name": f"Front ({source_lang} + Audio)"},
        {"name": f"Back ({target_lang})"},
        {"name": f"Example ({source_lang})"},
        {"name": f"Example ({target_lang})"},
        {"name": "Note"},
        {"name": "New words"}
    ]

    front_tmpl = "{{" + f"Front ({source_lang} + Audio)" + "}}"

    back_tmpl = (
        "{{" + f"Front ({source_lang} + Audio)" + "}}"
        + "\n\n<hr id=answer>\n\n"
        + "<b>Betekenis:</b> {{" + f"Back ({target_lang})" + "}}<br>\n"
        + "<b>Voorbeeld (" + source_lang + "):</b> {{" + f"Example ({source_lang})" + "}}<br>\n"
        + "<b>Voorbeeld (" + target_lang + "):</b> {{" + f"Example ({target_lang})" + "}}<br>\n"
        + "{{#Note}}<b>Opmerking:</b> {{Note}}<br>{{/Note}}\n"
    )
    if show_new:
        back_tmpl += "{{#New words}}<b>Nieuwe woorden:</b><br><pre>{{New words}}</pre>{{/New words}}"

    css = '''
.card { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; font-size: 20px; color: #222; background-color: #fff; }
hr#answer { margin: 16px 0; }
pre { white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.95em; }
'''  # noqa

    model = genanki.Model(
        model_id=_stable_id("model:" + model_name),
        name=model_name,
        fields=fields,
        templates=[{"name": "Card 1", "qfmt": front_tmpl, "afmt": back_tmpl}],
        css=css
    )

    deck = genanki.Deck(_stable_id("deck:" + deck_name), deck_name)

    for r in rows:
        deck.add_note(genanki.Note(model=model, fields=r))

    media_files_used = _collect_media_from_rows(rows)
    media_paths = [str(media_dir / f) for f in media_files_used if (media_dir / f).exists()]

    pkg = genanki.Package(deck)
    if media_paths:
        pkg.media_files = media_paths
    apkg_path.parent.mkdir(parents=True, exist_ok=True)
    pkg.write_to_file(str(apkg_path))
    return apkg_path
