# 🌐 anki-lingua
> **AI-powered multilingual flashcard generator for Anki**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![OpenAI API](https://img.shields.io/badge/API-OpenAI-orange)](https://platform.openai.com/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-required-lightgrey)](https://ffmpeg.org/)

---

### 🧠 What is anki-lingua?

**anki-lingua** turns your plain word lists into fully featured **Anki flashcards** with:
- ✅ **Automatic translation** between any supported languages  
- 🗣️ **AI-generated example sentences**
- 🔊 **Text-to-speech audio** for words and example sentences  
- 🕓 **Configurable playback speed** for the example audio  
- 💾 **Caching & retrying**, so you never lose progress  
- 🧩 **Optional Google backend** for low-cost TTS/Translate  
- 📘 **Anki-ready output** (`.tsv` + `.apkg`)

Whether you study **Indonesian, Japanese, Spanish, or Balinese dialects**,  
anki-lingua helps you build consistent and natural flashcards with minimal effort.

---

## 🚀 Quick Start

### 1️⃣ Install dependencies

```bash
git clone https://github.com/YOURNAME/anki-lingua.git
cd anki-lingua
python3 -m pip install -r requirements.txt
Ensure ffmpeg is installed:

bash
Code kopiëren
sudo apt-get install -y ffmpeg
2️⃣ Configure your API key
Copy the example config and edit it:

bash
Code kopiëren
cp config.example.json config.json
nano config.json
Set your OpenAI API key or Google credentials.

Example snippet:

json
Code kopiëren
{
  "BACKEND": "openai",
  "OPENAI_API_KEY": "sk-...",
  "TEXT_MODEL_OPENAI": "gpt-5-mini",
  "TTS_MODEL_OPENAI": "gpt-4o-mini-tts",
  "TTS_VOICE_OPENAI": "alloy",
  "SOURCE_LANG": "Indonesisch",
  "TARGET_LANG": "Nederlands",
  "EXAMPLE_AUDIO_RATE": 0.85,
  "ENABLE_CACHE": true
}
3️⃣ Run the generator
Provide a simple text file (one word per line):

nginx
Code kopiëren
air
makan
maaf
mana
Run the tool:

bash
Code kopiëren
python3 -m anki_builder.src.runner woorden.txt
After processing, you’ll find:

pgsql
Code kopiëren
out/
 ├── media/
 ├── anki_notes.tsv
 ├── anki_notes.apkg
 ├── state.json
 └── extra_words.txt
Import the .apkg file directly into Anki Desktop or sync with AnkiDroid.

⚙️ Configuration Overview
Key Description Default
BACKEND openai or google  "openai"
OPENAI_API_KEY  Your API key  
TEXT_MODEL_OPENAI GPT model for text generation "gpt-5-mini"
TTS_MODEL_OPENAI  Model for speech  "gpt-4o-mini-tts"
TTS_VOICE_OPENAI  Voice style "alloy"
SOURCE_LANG Source language label "Indonesisch"
TARGET_LANG Target language label "Nederlands"
EXAMPLE_AUDIO_RATE  Playback speed for example sentence (0.5–2.0) 1.0
ENABLE_CACHE  Use cached API responses  true
SHOW_NEW_WORDS_ON_BACK  Include new unknown words on back true
OOV_TRANSLATE Translate new words in example sentences  true
CREATE_APKG Build Anki package automatically  true

💡 Tips & Tricks
🗂 Duplicate words are processed only once — avoids redundant API calls.

🎧 Audio speed is handled locally via ffmpeg, not via extra API calls.

🔄 Cache & resume let you stop and restart generation at any time.

🧾 extra_words.txt lists new tokens found in example sentences — perfect for expanding your vocabulary list.

🌍 Works great for any language, but you can note regional variants manually (e.g., Balinese, Malay).

🧰 Troubleshooting
Issue Cause / Fix
ffmpeg not found  Install with sudo apt-get install ffmpeg
BadRequestError temperature Some TTS models don’t support temperature — update config.
Example audio mismatched  Sometimes API latency causes mix-ups; rerun with cache disabled.
Duplicates skipped  Normal behaviour; each unique word only once.

📜 License
This project is licensed under the MIT License.

❤️ Credits
Created with love (and a lot of tenacity 😄) to make language learning effortless.
Uses OpenAI GPT models, FFmpeg, and Anki.
