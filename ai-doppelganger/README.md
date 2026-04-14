# ai-doppelganger

Build an AI that talks like you, running locally via Ollama.

---

## Prerequisites

1. [Download Ollama](https://ollama.com/download) and install it
2. Pull a base model — `llama3` is a good default:
   ```bash
   ollama pull llama3
   ```
3. Get your Facebook Messenger export:
   > Facebook → Settings → Your Facebook information → Download your information  
   > Select **Messages** only → Format: **JSON** → Request download

---

## Setup

```bash
python doppel.py setup \
    --input  "/path/to/facebook-export/messages" \
    --my-name "Your Name As On Facebook"
```

That's it. The script:
1. Extracts your message history (both sides of every conversation)
2. Analyzes your language patterns, message length, and verbal style
3. Auto-generates a system prompt from your data
4. Creates an Ollama model called `doppel`

Then run:

```bash
ollama run doppel
```

---

## Chat from Python

```bash
# Interactive chat
python doppel.py chat

# Run a batch of test prompts
python doppel.py batch
```

---

## Options

```
setup
  --input PATH        Root folder of Facebook export (required)
  --my-name NAME      Your exact Facebook name as it appears in the export (required)
  --output PATH       Dataset output folder (default: doppel-dataset/)
  --base-model NAME   Ollama base model to use (default: llama3)
  --temperature N     Model temperature, 0.0–1.0 (default: 0.8)
  --include-groups    Include group chats (default: 1-on-1 only)

chat
  --model NAME        Ollama model name (default: doppel)

batch
  --model NAME        Ollama model name (default: doppel)
  --prompts-file PATH Text file with one prompt per line
```

---

## Tuning the persona

The auto-generated system prompt is saved at `doppel-dataset/system-prompt.txt`.
Edit it to add or remove traits, then rebuild the model:

```bash
ollama create doppel -f doppel-dataset/Modelfile
```

---

## Fine-tuning (optional)

The system prompt approach works well for style mimicry. For deeper behavioral
training, see `FINE_TUNING.md` — it covers three training paths:

| Path | Cost | GPU |
|------|------|-----|
| OpenAI API | ~$1–5 | None |
| Google Colab + Unsloth | Free | T4/A100 |
| Local GPU (CUDA/ROCm) | Free | Your own |

A fine-tuned model replaces the base model in your Modelfile.

---

## Files

| File | Purpose |
|------|---------|
| `doppel.py` | Main script: setup, chat, batch |
| `extract_messenger_personality.py` | Called by setup — Facebook export → dataset |
| `build_training_pairs.py` | Optional — dataset → fine-tuning pairs |
| `FINE_TUNING.md` | Fine-tuning guide (3 paths) |
| `system-prompt-template.md` | Manual template if you prefer to write your own prompt |

---

## Requirements

Python 3.8+. No pip dependencies. Ollama must be installed and running.

---

## License

MIT — see [LICENSE](LICENSE)

---

## Author

Anastasios Papalias · [acopon.online](https://acopon.online) · [GitHub](https://github.com/AnastasiosPapalias)
