# 📚 Anki Flashcard Builder

Genereer automatisch **Anki-flashcards** vanuit een woordenlijst. Het script gebruikt **OpenAI** (en optioneel Google) voor:
- vertaling van het doelwoord,
- één voorbeeldzin + vertaling,
- audio voor het woord én (optioneel) de voorbeeldzin,
- een **langzame** audio-variant voor alleen de voorbeeldzin (geen extra API-kosten).

## 🚀 Features
- Meertalig (brontaal/doeltaal in `config.json`)
- LLM output in **stabiel JSON** (robuste parsing)
- Resume + Cache voor snelheid/kosten
- Retry/backoff bij netwerk/rate-limit problemen
- **OOV**: extra woorden uit voorbeeldzinnen (met optionele vertalingen) op de achterkant van de kaart
- **Slow Audio** voor voorbeeldzin via `ffmpeg` (lokaal tijdrekken, geen extra tokens)
- Output: `.tsv` + `.apkg` (Anki Desktop & AnkiDroid)

## 🛠 Installatie
### Vereisten
- Python 3.11+
- `pip`
- OpenAI API key (betaald account)
- (Optioneel) Google Cloud service-account JSON voor Google TTS/Translate
- `ffmpeg` (voor slow-audio)
  ```bash
  sudo apt-get update && sudo apt-get install -y ffmpeg
  ```

### Packages
```bash
python3 -m pip install -r requirements.txt
```

### Config
Kopieer `config.example.json` → `config.json` en vul je sleutels/voorkeuren in.

## ▶️ Gebruik
### Woordenlijst
Eén woord per regel, bijv. `woorden.txt`:
```
maaf
mana
air
```

### Run
```bash
python3 -m anki_builder.src.runner woorden.txt
```
Resultaat in `out/`:
- `anki_notes.tsv`
- `anki_deck.apkg`
- `media/` (audio)
- `extra_words.txt` (OOV uit voorbeeldzinnen)

## 📦 Import in Anki
- **Anki Desktop**: *Bestand → Importeren* → kies `anki_deck.apkg` of `anki_notes.tsv`
- **AnkiDroid**: kopieer `.apkg` naar je toestel → open in AnkiDroid

## ⚙️ Belangrijke opties in `config.json`
- `"REGENERATE_AUDIO_ALWAYS"`: forceer audio opnieuw genereren (voorkomt mismatch met oude bestanden)
- `"GENERATE_SLOW_AUDIO"` / `"SLOW_AUDIO_RATE"` / `"INCLUDE_SLOW_ON_CARD"`: slow-audio voor **alleen** de voorbeeldzin
- `"SHOW_NEW_WORDS_ON_BACK"`: zet OOV-woorden (met evt. vertalingen) op de achterkant
- `"ENABLE_CACHE"` / `"RESUME_ENABLED"`: snel/zuinig werken zonder dubbele LLM-calls

## 🐢 Slow Audio (voorbeeldzin)
- Geen extra API-calls; `ffmpeg` maakt lokaal een tragere kopie (bijv. 0.75×).
- Op de kaart verschijnt (optioneel): `Langzaam: [sound:<..._ex_slow.mp3>]`

## 🔧 Reset / Clean
Alles opnieuw genereren? Verwijder output, media, cache en state:
```bash
rm -f out/anki_notes.tsv out/anki_deck.apkg out/extra_words.txt out/state.json
rm -rf out/media cache
```

## 📁 Structuur
```
anki_builder/
  └─ src/
     ├─ runner.py
     ├─ prompts.py
     ├─ config_loader.py
     ├─ io_utils.py
     ├─ packaging.py
     ├─ cache_utils.py
     ├─ backends/
     │  ├─ openai_backend.py
     │  └─ google_backend.py
     └─ services/           # (gereserveerd voor toekomstige refactor)
``

## ⚠️ Veilig met geheimen
- Commit **nooit** `config.json` met echte keys. Gebruik `config.example.json` in git, en zet `config.json` in `.gitignore`.
