# src/prompts.py

SYSTEM_NOTE = (
    "Je bent een nauwkeurige helper voor woordenschat-flashcards. "
    "Genereer korte, natuurlijke output en, indien relevant, usage notes. "
    "Behandel brontaal en doeltaal precies zoals gespecificeerd."
)

PROMPT_TEMPLATE = """Bron-taal (SOURCE_LANG): {source_lang}
Doel-taal (TARGET_LANG): {target_lang}
Gebruik van usage notes: {usage_notes}

Doelwoord: "{word}"

Taken:
1) Vertaal het {source_lang}-woord naar {target_lang}.
2) Maak één natuurlijke voorbeeldzin in het {source_lang}.
3) Geef de {target_lang}-vertaling van die zin.
4) OPMERKING: alleen indien relevant (kort en duidelijk).

JSON-output:
{{
  "translation": "...",
  "example_src": "...",
  "example_tgt": "...",
  "note": "..."  // mag leeg zijn
}}
"""
