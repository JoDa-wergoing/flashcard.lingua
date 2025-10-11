# src/runner.py
import sys
import time
import csv
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm

from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception, before_sleep_log

from .config_loader import load_config
from .io_utils import read_wordlist, safe_filename, tokenize_words
from .packaging import build_apkg
from .cache_utils import make_cache_key, cache_read, cache_write, load_state, save_state

logger = logging.getLogger("anki_builder")

class RetryableError(Exception):
    pass

def is_retryable_exception(e: Exception) -> bool:
    s = str(e).lower()
    # Rate limits, server errors, timeouts, TLS/verbinding issues
    return (
        "429" in s or "rate limit" in s or
        "503" in s or "502" in s or "504" in s or "service unavailable" in s or
        "timeout" in s or "timed out" in s or
        "read error" in s or "connection reset" in s or "ssl" in s or
        "temporary failure in name resolution" in s or "failed to establish a new connection" in s
    )

def make_retry_decorator(max_attempts: int):
    return retry(
        retry=retry_if_exception(is_retryable_exception),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        stop=stop_after_attempt(max_attempts),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )

def _ffmpeg_available() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return True
    except Exception:
        return False

def adjust_audio_rate(in_path: Path, out_path: Path, rate: float) -> None:
    """
    Pas afspeelsnelheid aan met pitch-preserving time-stretch via ffmpeg 'atempo'.
    Geldige rate: 0.5..2.0 (1.0 = ongewijzigd)
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not _ffmpeg_available():
        raise RuntimeError("ffmpeg niet gevonden. Installeer met: sudo apt-get install -y ffmpeg")
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(in_path),
        "-filter:a", f"atempo={rate}",
        str(out_path)
    ]
    subprocess.run(cmd, check=True)

def main():
    import argparse
    ap = argparse.ArgumentParser(
        description="Flashcards bouwer (OpenAI/Google) + cache + resume + retry + OOV + voorbeeld-audio (met configureerbare snelheid)."
    )
    ap.add_argument("input", help="Woordenlijst .txt of .csv")
    ap.add_argument("--usage-notes", choices=["auto", "always", "never"])
    args = ap.parse_args()

    cfg = load_config(Path("config.json"))

    # Logging
    log_level = getattr(logging, cfg.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
    third_party_level = getattr(logging, cfg.get("THIRD_PARTY_LOG_LEVEL", "WARNING").upper(), logging.WARNING)
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s: %(message)s")
    logger.setLevel(log_level)
    for _name in ("httpx", "httpcore", "openai", "urllib3"):
        _lg = logging.getLogger(_name)
        _lg.setLevel(third_party_level)
        _lg.propagate = False

    usage_notes = args.usage_notes or cfg.get("USAGE_NOTES_DEF", "auto")
    max_retries = int(cfg.get("MAX_RETRIES", 6))
    retry_deco = make_retry_decorator(max_retries)

    # Backend
    backend_name = cfg.get("BACKEND", "openai").lower()
    if backend_name == "openai":
        from .backends.openai_backend import OpenAIBackend as Backend
    elif backend_name == "google":
        from .backends.google_backend import GoogleBackend as Backend
    else:
        raise ValueError("BACKEND moet 'openai' of 'google' zijn.")
    backend = Backend(cfg)

    # Invoer
    words: List[str] = read_wordlist(Path(args.input))
    if not words:
        print("Geen woorden in invoer.")
        sys.exit(1)

    # Vocab & OOV
    vocab = {w.strip().lower() for w in words}
    extra_words_global = set()

    # Output paden
    out_dir = Path(cfg.get("OUTPUT_DIR", "out")); out_dir.mkdir(exist_ok=True)
    media_dir = out_dir / cfg.get("OUTPUT_MEDIA_DIR", "media"); media_dir.mkdir(parents=True, exist_ok=True)
    out_tsv = out_dir / cfg.get("OUTPUT_TSV", "anki_notes.tsv")
    extra_path = Path(cfg.get("EXTRA_WORDS_FILE", "out/extra_words.txt"))

    # Cache & resume
    cache_enabled = bool(cfg.get("ENABLE_CACHE", True))
    cache_dir = Path(cfg.get("CACHE_DIR", "cache"))
    resume_enabled = bool(cfg.get("RESUME_ENABLED", True))
    state_path = Path(cfg.get("STATE_FILE", "out/state.json"))
    state: Dict[str, Any] = load_state(state_path) if resume_enabled else {}
    processed = set(state.get("processed", [])) if state else set()

    # Config labels
    audio_ext = cfg.get("AUDIO_EXT", "mp3")
    source_lang = cfg.get("SOURCE_LANG", "Bron")
    target_lang = cfg.get("TARGET_LANG", "Doel")
    source_code = (cfg.get("SOURCE_LANG_CODE", "") or "")
    target_code = (cfg.get("TARGET_LANG_CODE", "") or "")
    sleep_between = float(cfg.get("SLEEP_BETWEEN_CALLS", 0.03))
    add_example_audio = bool(cfg.get("ADD_EXAMPLE_AUDIO", True))
    show_new_on_back = bool(cfg.get("SHOW_NEW_WORDS_ON_BACK", True))
    oov_translate = bool(cfg.get("OOV_TRANSLATE", True))
    regenerate_audio = bool(cfg.get("REGENERATE_AUDIO_ALWAYS", False))

    # Voorbeeld-audio snelheid (één bestand, snelheid ingebakken)
    example_rate = float(cfg.get("EXAMPLE_AUDIO_RATE", 1.0))
    if not (0.5 <= example_rate <= 2.0):
        raise ValueError("EXAMPLE_AUDIO_RATE moet tussen 0.5 en 2.0 liggen (bijv. 0.85 of 1.25)")

    print(f"Backend: {backend_name} | Bron: {source_lang} → Doel: {target_lang}")

    # TTS override (optioneel, standaard openai)
    tts_override = (cfg.get("OVERRIDE_TTS_BACKEND", "openai") or "openai").lower()
    google_tts_client = None
    if tts_override in ("auto", "google"):
        if tts_override == "google" or (tts_override == "auto" and source_code.lower() == "id"):
            try:
                from .backends.google_backend import GoogleBackend as GTT
                google_tts_client = GTT(cfg)
            except Exception as e:
                print("[WAARSCHUWING] Google TTS init mislukt, val terug op OpenAI:", e)
                google_tts_client = None

    # Retry-wrappers
    @retry_deco
    def safe_generate(word: str) -> Dict[str, Any]:
        try:
            return backend.generate_card(word, usage_notes)
        except Exception as e:
            if is_retryable_exception(e):
                raise RetryableError(str(e))
            raise

    @retry_deco
    def safe_tts(text: str, out_path: Path) -> None:
        try:
            backend.tts_word(text, out_path)
        except Exception as e:
            if is_retryable_exception(e):
                raise RetryableError(str(e))
            raise

    @retry_deco
    def safe_translate_oov(tokens: List[str]) -> Dict[str, str]:
        try:
            return backend.translate_oov_list(tokens, source_lang, target_lang, source_code, target_code)
        except Exception as e:
            if is_retryable_exception(e):
                raise RetryableError(str(e))
            raise

    rows = []
    for w in tqdm(words):
        lw = w.strip().lower()
        if resume_enabled and lw in processed:
            continue

        # 1) LLM data (met cache)
        data = None
        cache_key = make_cache_key(w, cfg, usage_notes, backend_name)
        if cache_enabled:
            cached = cache_read(cache_dir, cache_key)
            if cached and all(k in cached for k in ("translation", "example_src", "example_tgt", "note")):
                data = cached
        if data is None:
            data = safe_generate(w)
            if cache_enabled:
                cache_write(cache_dir, cache_key, data)

        # 2) TTS: woord (normaal tempo; geen rate-aanpassing)
        word_audio_name = f"{safe_filename(w)}.{audio_ext}"
        word_audio_path = media_dir / word_audio_name
        if regenerate_audio or not word_audio_path.exists():
            try:
                if google_tts_client is not None:
                    google_tts_client.tts_word(w, word_audio_path)
                else:
                    safe_tts(w, word_audio_path)
            except Exception as e:
                print(f"[TTS fout] woord '{w}': {e}")
                if google_tts_client is not None:
                    try:
                        safe_tts(w, word_audio_path)
                    except Exception as e2:
                        print(f"[TTS fout] (OpenAI fallback) woord '{w}': {e2}")
                        word_audio_name = ""

        # 3) TTS: voorbeeld (één bestand, met instelbare snelheid)
        example_src = data["example_src"]
        example_src_with_audio = example_src
        if add_example_audio and example_src.strip():
            ex_audio_name = f"{safe_filename(w)}_ex.{audio_ext}"
            ex_audio_path = media_dir / ex_audio_name
            # Normale synthese
            need_synthesize = regenerate_audio or not ex_audio_path.exists()
            if need_synthesize:
                try:
                    if google_tts_client is not None:
                        google_tts_client.tts_word(example_src, ex_audio_path)
                    else:
                        safe_tts(example_src, ex_audio_path)
                except Exception as e:
                    print(f"[TTS fout] voorbeeld '{w}': {e}")
                    if google_tts_client is not None:
                        try:
                            safe_tts(example_src, ex_audio_path)
                        except Exception as e2:
                            print(f"[TTS fout] (OpenAI fallback) voorbeeld '{w}': {e2}")

            # Snelheid toepassen (overschrijft het originele bestand)
            if ex_audio_path.exists() and abs(example_rate - 1.0) > 1e-6:
                tmp_path = ex_audio_path.with_suffix(f".rate_tmp.{ex_audio_path.suffix[1:]}")
                try:
                    adjust_audio_rate(ex_audio_path, tmp_path, example_rate)
                    ex_audio_path.unlink(missing_ok=True)
                    tmp_path.rename(ex_audio_path)
                except Exception as e:
                    print(f"[Audio-snelheid fout] voorbeeld '{w}': {e}")

            if ex_audio_path.exists():
                example_src_with_audio = f"{example_src}<br>[sound:{ex_audio_name}]"

        # 4) OOV tokens
        oov_local = []
        for tok in tokenize_words(data["example_src"]):
            if len(tok) < 2:
                continue
            if tok != lw and tok not in vocab:
                oov_local.append(tok)
                extra_words_global.add(tok)

        # 5) New words (met vertalingen)
        new_words_field = ""
        if show_new_on_back and oov_local:
            mapping: Dict[str, str] = {}
            if oov_translate:
                try:
                    mapping = safe_translate_oov(oov_local)
                except Exception as e:
                    logger.warning(f"OOV-vertaling overgeslagen: {e}")
                    mapping = {}
            lines, done = [], set()
            for t in oov_local:
                if t in done:
                    continue
                done.add(t)
                tr = mapping.get(t, "")
                lines.append(f"{t} = {tr}" if tr else t)
            new_words_field = "\n".join(lines)

        # 6) Rij
        front = (
            f"{w}<br>[sound:{word_audio_name}]"
            if (media_dir / word_audio_name).exists()
            else w
        )
        rows.append([
            front,
            data["translation"],
            example_src_with_audio,
            data["example_tgt"],
            data.get("note", ""),
            new_words_field,
        ])

        # 7) Resume-state
        if resume_enabled:
            processed.add(lw)
            save_state(state_path, {"processed": sorted(list(processed))})

        time.sleep(sleep_between)

    # 8) TSV
    with out_tsv.open("w", newline="", encoding="utf-8") as f:
        wri = csv.writer(f, delimiter="\t")
        wri.writerow([
            f"Front ({source_lang} + Audio)",
            f"Back ({target_lang})",
            f"Example ({source_lang})",
            f"Example ({target_lang})",
            "Note",
            "New words",
        ])
        wri.writerows(rows)
    print("✅ TSV klaar:", out_tsv)

    # 9) APKG
    if cfg.get("CREATE_APKG", True):
        apkg = build_apkg(cfg, rows, media_dir)
        print("📦 APKG gemaakt:", apkg)

    # 10) Los OOV-bestand
    if extra_words_global:
        extra_path.parent.mkdir(parents=True, exist_ok=True)
        extra_path.write_text("\n".join(sorted(extra_words_global)) + "\n", encoding="utf-8")
        print(f"📝 Extra woorden uit voorbeeldzinnen: {extra_path} ({len(extra_words_global)} items)")
    else:
        print("📝 Geen extra woorden gevonden in voorbeeldzinnen.")

    print(f"📁 Media: {media_dir}")
    if resume_enabled:
        print(f"💾 State: {state_path} (processed={len(processed)})")


if __name__ == "__main__":
    main()
