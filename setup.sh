#!/usr/bin/env bash
set -euo pipefail

CONFIG_FILE="config.json"
if [ ! -f "$CONFIG_FILE" ]; then
  echo "config.json ontbreekt. Maak die eerst aan."
  exit 1
fi

BACKEND=$(python3 - <<'PY'
import json
cfg=json.load(open("config.json","r",encoding="utf-8"))
print(cfg.get("BACKEND","openai").lower())
PY
)

echo "→ Gekozen backend: $BACKEND"
if [ "$BACKEND" = "openai" ]; then
  python3 -m pip install --upgrade openai requests tenacity tqdm pandas genanki
elif [ "$BACKEND" = "google" ]; then
  python3 -m pip install --upgrade google-cloud-translate google-generativeai google-cloud-texttospeech tqdm tenacity pandas genanki
else
  echo "BACKEND moet 'openai' of 'google' zijn."
  exit 1
fi

echo "✅ Setup klaar."
