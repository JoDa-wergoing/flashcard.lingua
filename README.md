# 🌐 flashcards.lingua
**AI-powered multilingual flashcard generator — Anki compatible**

flashcards.lingua is a command-line tool that transforms simple word lists into
**high-quality, Anki-compatible flashcard decks** with translations, example sentences,
and audio.
It is designed for serious language learners who want **structure, context, and sound**
without manual card creation.

The generated decks integrate seamlessly with **Anki** and can be used together with
**flashcard.audio** for audio-focused practice.

---

## 🎯 What does flashcards.lingua do?

Given a plain text word list (one word per line), flashcards.lingua automatically:

- Translates each word into a target language
- Generates a natural example sentence
- Translates the example sentence
- Generates audio for:
  - the word
  - the example sentence
- Optionally detects and lists **new words** appearing in example sentences
- Exports everything as an **Anki-compatible deck**

The result is a ready-to-study flashcard deck that emphasizes **meaning, usage, and pronunciation**.

---

## ▶️ Run the generator

From the project root (the folder that contains `config.json`):

```bash
python3 -m flashcard_lingua.runner words.txt

Example input file

Create a text file with one word (in the language you want to learn per line), for example words.txt:

makan
air
maaf
mana

Optional CLI flags

You can control how “usage notes” are generated:

python3 -m flashcard_lingua.runner words.txt --usage-notes auto
python3 -m flashcard_lingua.runner words.txt --usage-notes always
python3 -m flashcard_lingua.runner words.txt --usage-notes never


Most settings are configured in config.json (models, languages, cache/resume, audio options).
Where the output goes

After running, the output is written to the folder configured in config.json (default: out/):
out/anki_notes.tsv
out/anki_notes.apkg (if enabled)
out/media/ (audio files)
out/extra_words.txt (new words found in example sentences)

---

## ✅ Anki Compatibility

flashcards.lingua produces output that is fully compatible with:

- **Anki Desktop**
- **AnkiDroid**
- **AnkiMobile**

### Output formats
- `.tsv` — for manual import or inspection
- `.apkg` — ready-to-import Anki deck (recommended)

### Anki note fields

1. **Front**
2. **Back**
3. **Example Source**
4. **Example Target**
5. **Note**
6. **New Words**

---

## 🎧 Using flashcards.lingua with flashcard.audio

**flashcards.lingua** and **flashcard.audio** are complementary tools:

- **flashcards.lingua**
  - Generates structured flashcard decks
  - Focuses on vocabulary, context, and Anki integration

- **flashcard.audio**
  - Focuses on audio-first learning and repetition

---

## 🧠 Key Features

- 🌍 Multilingual (any source → target language)
- 🧠 AI-generated translations and examples
- 🔊 Built-in audio generation
- ⚡ Example sentence audio speed control
- 💾 Caching to reduce API usage and cost
- 🔄 Resume support if generation is interrupted
- 🧩 Automatic detection of new vocabulary
- 📦 Clean, Anki-ready output

---

## 📜 License

MIT License

---

## ⚖️ Legal Notice

flashcards.lingua is an independent, open-source project.

It is **not affiliated with, endorsed by, or sponsored by Anki** or any
third-party service mentioned in this documentation.
Anki is a registered trademark of its respective owner.

flashcards.lingua uses third-party APIs for content generation.
Users are responsible for complying with the terms of service of
OpenAI, Google, Anki, and any other services they choose to use.
