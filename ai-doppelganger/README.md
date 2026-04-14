# ai-doppelganger

Build an AI that talks like you — trained on your own Facebook Messenger history and deployable locally via Ollama.

Four steps, each usable on its own:

1. **Extract** — Facebook Messenger export → structured dataset (SQLite / JSONL / CSV)
2. **Pair** — dataset → fine-tuning conversation pairs
3. **Train** — fine-tune an LLM on your pairs (OpenAI API, Google Colab, or local GPU)
4. **Run** — deploy via Ollama or any OpenAI-compatible endpoint

---

## Requirements

Python 3.8+. No external dependencies for extraction — standard library only.  
Training requires `openai` (Path A) or `torch` + `unsloth` (Paths B/C).

---

## Quick start

### Step 1 — Get your Facebook data

> Facebook → Settings → Your Facebook information → Download your information  
> Select **Messages** only → Format: **JSON** → Request download

### Step 2 — Extract

```bash
python extract_messenger_personality.py \
    --input  "/path/to/facebook-export/messages" \
    --output "./my-dataset" \
    --my-name "Your Name As On Facebook"
```

Outputs into `./my-dataset/`:

| File | Description |
|------|-------------|
| `messages.jsonl` | Master dataset — one JSON record per message, both sides |
| `messages.sqlite` | Fully-indexed SQLite database |
| `messages.csv` | Spreadsheet-friendly export |
| `style_profiles.json` | Per-conversation style summaries (your messages only) |
| `global_summary.json` | Whole-dataset statistics |
| `markdown_shards/` | Your messages grouped by conversation + month |

### Step 3 — Build a system prompt

Copy `system-prompt-template.md`, fill in your details using `style_profiles.json` and `markdown_shards/` as reference. Save it as `my-system-prompt.md`.

This alone is enough to run a doppelganger without any training — just pass it as the system prompt to any LLM.

### Step 4 — Build fine-tuning pairs

```bash
python build_training_pairs.py \
    --db     ./my-dataset/messages.sqlite \
    --output ./my-dataset/training_pairs.jsonl \
    --system-prompt ./my-system-prompt.md \
    --format openai \
    --context-turns 3 \
    --split
```

Supported formats: `openai` · `sharegpt` · `alpaca` · `raw`

### Step 5 — Train and deploy via Ollama

See `FINE_TUNING.md` for complete instructions. Three paths:

| Path | Cost | GPU | Result |
|------|------|-----|--------|
| OpenAI API | ~$1–5 | None | Fine-tuned GPT-4o-mini |
| Google Colab + Unsloth | Free | T4/A100 | Llama 3 8B → GGUF → Ollama |
| Local GPU (CUDA/ROCm) | Free | Your own | Same as Colab, on your hardware |

End result:

```bash
ollama run my-doppelganger
```

---

## No training? Use the system prompt directly

```python
import anthropic

with open("my-system-prompt.md") as f:
    system = f.read()

client = anthropic.Anthropic()
message = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    system=system,
    messages=[{"role": "user", "content": "Hey, what's up?"}]
)
print(message.content[0].text)
```

Works on Claude, GPT, Gemini, Ollama — any OpenAI-compatible endpoint.

---

## Files

| File | Purpose |
|------|---------|
| `extract_messenger_personality.py` | Step 1 — Facebook export → dataset |
| `build_training_pairs.py` | Step 2 — dataset → training pairs |
| `system-prompt-template.md` | System prompt template to fill in |
| `FINE_TUNING.md` | Full training guide (3 paths) |

---

## Options

### extract_messenger_personality.py

```
--input PATH            Root folder of the Facebook export (required)
--output PATH           Where to write the output files (required)
--my-name NAME          Your exact Facebook name as it appears in the export (required)
--include-group-chats   Include group conversations (default: 1-on-1 only)
--min-chars N           Minimum cleaned message length to keep (default: 2)
```

### build_training_pairs.py

```
--db PATH               Path to messages.sqlite (required)
--output PATH           Output JSONL path
--system-prompt PATH    Path to system prompt file (.txt or .md)
--format                openai | sharegpt | alpaca | raw (default: openai)
--context-turns N       Prior turns to include as context (default: 3)
--max-gap-minutes N     Max gap between trigger and reply (default: 120)
--min-words N           Min words in both messages (default: 2)
--split                 Write 90/10 train/val split
```

---

## How it handles encoding

Facebook exports encode UTF-8 text as latin-1-decoded Unicode, which garbles non-ASCII characters (Greek, accented letters, emoji in some locales). The extractor automatically detects and fixes these sequences so your messages appear correctly in the output.

---

## Privacy

- `markdown_shards/` contains raw conversation excerpts — do not share publicly
- `messages.jsonl` contains contact names — treat with care
- You have full consent over your own data; your contacts do not

---

## License

MIT — see [LICENSE](LICENSE)

---

## Author

Anastasios Papalias · [acopon.online](https://acopon.online) · [GitHub](https://github.com/AnastasiosPapalias)
