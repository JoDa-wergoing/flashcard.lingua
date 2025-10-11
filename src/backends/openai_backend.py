# src/backends/openai_backend.py
import re
import requests
import json as _json
from pathlib import Path
from typing import Dict, List

from openai import OpenAI
from ..prompts import SYSTEM_NOTE, PROMPT_TEMPLATE

class OpenAIBackend:
    def __init__(self, cfg: dict):
        self.key = cfg["OPENAI_API_KEY"]
        self.text_model = cfg.get("TEXT_MODEL_OPENAI", "gpt-5-mini")
        self.tts_model = cfg.get("TTS_MODEL_OPENAI", "gpt-4o-mini-tts")
        self.voice = cfg.get("TTS_VOICE_OPENAI", "alloy")
        self.audio_ext = cfg.get("AUDIO_EXT", "mp3")
        self.source_lang = cfg.get("SOURCE_LANG", "Indonesisch")
        self.target_lang = cfg.get("TARGET_LANG", "Nederlands")
        self.temperature_cfg = cfg.get("TEMPERATURE", None)
        self.client = OpenAI(api_key=self.key)

    def _chat_complete(self, messages, temperature_cfg):
        if temperature_cfg is not None:
            try:
                return self.client.chat.completions.create(
                    model=self.text_model, messages=messages, temperature=float(temperature_cfg)
                )
            except Exception as e:
                if "temperature" in str(e).lower() and "unsupported" in str(e).lower():
                    return self.client.chat.completions.create(model=self.text_model, messages=messages)
                raise
        return self.client.chat.completions.create(model=self.text_model, messages=messages)

    def generate_card(self, word: str, usage_notes: str) -> Dict[str, str]:
        messages = [
            {"role": "system", "content": SYSTEM_NOTE},
            {
                "role": "user",
                "content": PROMPT_TEMPLATE.format(
                    usage_notes=usage_notes,
                    source_lang=self.source_lang,
                    target_lang=self.target_lang,
                    word=word,
                ),
            },
        ]
        resp = self._chat_complete(messages, self.temperature_cfg)
        text = resp.choices[0].message.content.strip()
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            raise ValueError(f"Geen JSON in OpenAI-output voor '{word}': {text}")
        data = _json.loads(m.group(0))
        for k in ("translation", "example_src", "example_tgt", "note"):
            if k not in data or (k != "note" and not str(data[k]).strip()):
                raise ValueError(f"OpenAI JSON onvolledig voor '{word}': {data}")
        return data

    def tts_word(self, text: str, out_audio: Path) -> None:
        url = "https://api.openai.com/v1/audio/speech"
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        payload = {"model": self.tts_model, "voice": self.voice, "input": text, "format": self.audio_ext}
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        if r.status_code != 200:
            raise RuntimeError(f"OpenAI TTS fout (HTTP {r.status_code}): {r.text}")
        out_audio.parent.mkdir(parents=True, exist_ok=True)
        out_audio.write_bytes(r.content)

    def translate_oov_list(
        self, words: List[str], source_lang_label: str, target_lang_label: str,
        source_lang_code: str = "", target_lang_code: str = ""
    ) -> Dict[str, str]:
        if not words:
            return {}
        uniq = sorted(set(w.strip() for w in words if w.strip()))
        prompt = (
            "Vertaal elk van de volgende woorden van {src} naar {tgt}. "
            "Geef uitsluitend JSON terug met een mapping {{woord: korte vertaling}}; geen extra tekst.\n"
            "Woorden: " + ", ".join(uniq)
        ).format(src=source_lang_label, tgt=target_lang_label)
        msg = [
            {"role": "system", "content": "Je geeft alleen JSON terug met woord->korte vertaling (max 3 woorden)."},
            {"role": "user", "content": prompt},
        ]
        resp = self._chat_complete(msg, self.temperature_cfg)
        text = resp.choices[0].message.content.strip()
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return {}
        try:
            data = _json.loads(m.group(0))
            return {str(k).strip(): str(v).strip() for k, v in data.items()}
        except Exception:
            return {}
