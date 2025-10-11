# src/backends/google_backend.py
import os, re, json
from pathlib import Path
from typing import Dict
from ..prompts import PROMPT_TEMPLATE

class GoogleBackend:
    def __init__(self, cfg: dict):
        self.api_key = cfg.get("GOOGLE_API_KEY", "")
        self.creds_path = cfg.get("GOOGLE_APPLICATION_CREDENTIALS", "")
        self.gemini_model = cfg.get("TEXT_MODEL_GOOGLE", "gemini-1.5-flash")
        self.src_code = cfg.get("SOURCE_LANG_CODE", "id")
        self.tgt_code = cfg.get("TARGET_LANG_CODE", "nl")
        self.tts_lang = cfg.get("GOOGLE_TTS_LANGUAGE_CODE", "id-ID")
        self.tts_voice = cfg.get("GOOGLE_TTS_VOICE", "id-ID-Wavenet-C")
        self.audio_ext = cfg.get("AUDIO_EXT", "mp3")
        self.source_lang = cfg.get("SOURCE_LANG", "Indonesisch")
        self.target_lang = cfg.get("TARGET_LANG", "Nederlands")

    def generate_card(self, word: str, usage_notes: str) -> Dict[str,str]:
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        prompt = PROMPT_TEMPLATE.format(
            usage_notes=usage_notes,
            source_lang=self.source_lang,
            target_lang=self.target_lang,
            word=word
        )
        resp = genai.GenerativeModel(self.gemini_model).generate_content(prompt)
        text = resp.text.strip()
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            raise ValueError(f"Geen JSON in Gemini-output voor '{word}': {text}")
        data = json.loads(m.group(0))
        for k in ("translation", "example_src", "example_tgt", "note"):
            if k not in data or (k != "note" and not str(data[k]).strip()):
                raise ValueError(f"Gemini JSON onvolledig voor '{word}': {data}")
        return data

    def tts_word(self, text: str, out_audio: Path) -> None:
        from google.cloud import texttospeech
        if self.creds_path: os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.creds_path
        client = texttospeech.TextToSpeechClient()
        input_cfg = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(language_code=self.tts_lang, name=self.tts_voice)
        audio_cfg = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        resp = client.synthesize_speech(input=input_cfg, voice=voice, audio_config=audio_cfg)
        out_audio.parent.mkdir(parents=True, exist_ok=True)
        out_audio.write_bytes(resp.audio_content)

    def translate_oov_list(
        self, words, source_lang_label, target_lang_label, source_lang_code="", target_lang_code="nl"
    ):
        if not words:
            return {}
        try:
            from google.cloud import translate_v2 as translate
        except Exception:
            return {}
        if self.api_key:
            client = translate.Client(api_key=self.api_key)
        else:
            client = translate.Client()
        out = {}
        for w in sorted(set(words)):
            try:
                if source_lang_code:
                    res = client.translate(w, target_language=target_lang_code, source_language=source_lang_code)
                else:
                    res = client.translate(w, target_language=target_lang_code)
                out[w] = res["translatedText"]
            except Exception:
                continue
        return out
