# messenger-personality-extractor

Extract your Facebook Messenger history into a structured dataset for AI fine-tuning, RAG pipelines, or writing-style analysis.

Give it your Facebook data export. It gives you your entire messaging history — both sides of every conversation — cleaned, structured, language-detected, and organised by conversation — ready to feed into an LLM.

---

## What it does

Reads every `message_*.json` file in a Facebook export and extracts **both sides** of every conversation. Outputs:

| File | Description |
|------|-------------|
| `messages.jsonl` | Master dataset — one JSON record per message |
| `messages.csv` | Spreadsheet-friendly export |
| `messages.sqlite` | Fully-indexed SQLite database |
| `style_profiles.json` | Per-conversation style summary |
| `global_summary.json` | Whole-dataset statistics |
| `markdown_shards/` | Messages grouped by conversation + month |
| `TRAINING_INSTRUCTIONS.md` | Notes for AI/LLM use |

Each message record includes:
- Cleaned text (original + URL-stripped version)
- Language detection: `greek` / `english_or_latin` / `mixed` / `unknown`
- Temporal metadata: year, month, day, hour, weekday
- Conversation context: title, participants, group/DM flag
- Attachment counts: photos, videos, audio, files, GIFs, stickers
- Reaction count

---

## Quick start

**Step 1 — Get your Facebook data**

> Facebook → Settings → Your Facebook information → Download your information  
> Select **Messages** only → Format: **JSON** → Request download

**Step 2 — Extract**

```bash
python extract_messenger_personality.py \
    --input  "/path/to/facebook-export" \
    --output "./messenger_output" \
    --my-name "Your Name As On Facebook"
```

**Step 3 — Use the data**

```bash
# Quick stats
python -c "
import json
s = json.load(open('messenger_output/global_summary.json'))
print(f\"{s['message_count']:,} messages across {s['conversation_count']} conversations\")
print('Languages:', s['language_distribution'])
"

# Query the database
sqlite3 messenger_output/messages.sqlite \
  "SELECT conversation_title, COUNT(*) as n FROM messages GROUP BY 1 ORDER BY 2 DESC LIMIT 10"
```

---

## Options

```
--input PATH            Root folder of the Facebook export (required)
--output PATH           Where to write the output files (required)
--my-name NAME          Your exact Facebook name as it appears in the export (required)
--include-group-chats   Include group conversations (default: 1-on-1 only)
--min-chars N           Minimum cleaned message length to keep (default: 2)
--version               Show version and exit
```

---

## Example output

```
messenger-personality-extractor v2.0.0
  Input  : /Users/you/Downloads/facebook-export
  Output : ./messenger_output
  Name   : Your Name
  Groups : no

  Found 5,968 JSON files. Extracting…
  [████████████████████████████████████████] 100.0%  5,968/5,968 files

┌─────────────────────────────────────────────┐
│         messenger-personality-extractor      │
│              Extraction complete             │
├─────────────────────────────────────────────┤
│  Total messages (all)   :    238,160         │
│  Subject messages (me)  :    115,503         │
│  Conversations          :      4,785         │
│  Avg words/msg (mine)   :        8.3         │
│  First message          : 2009-05-23         │
│  Last message           : 2024-12-02         │
├─────────────────────────────────────────────┤
│  Language breakdown (my messages):          │
│    greek                   78,337  (67.8%)   │
│    mixed                   20,095  (17.4%)   │
│    english_or_latin        12,934  (11.2%)   │
│    unknown                  4,137   (3.6%)   │
└─────────────────────────────────────────────┘

  Next step: run build_training_pairs.py to generate fine-tuning data.
```

---

## Step 2 — Build fine-tuning pairs

After extraction, run `build_training_pairs.py` to generate (prompt → response) pairs for LLM training:

```bash
python build_training_pairs.py \
    --db     ./messenger_output/messages.sqlite \
    --output ./training_pairs.jsonl \
    --system-prompt ./my-system-prompt.md \
    --format openai \
    --context-turns 3 \
    --split
```

Supported output formats: `openai` (GPT fine-tuning), `sharegpt` (Axolotl / LLaMA Factory), `alpaca`, `raw`.

`--split` writes a 90/10 train/val split automatically.

---

## Use cases

**AI doppelganger / digital twin**  
Feed `messages.jsonl` or `style_profiles.json` into a fine-tuning pipeline or RAG system to model how you write to specific people, at specific times of day, in Greek or English.

**Writing style analysis**  
Use the SQLite database to query patterns: when do you write the most? Which conversations are Greek vs. English? How has your average message length changed over the years?

**LLM persona prompting**  
Use `style_profiles.json` per conversation to build context-aware system prompts: _"When talking to X, this person writes short Greek messages, mostly in the evening, and rarely shares links."_

---

## How it handles Greek text

Facebook exports encode text using a latin-1/utf-8 double-encoding that garbles non-ASCII characters. This tool automatically fixes the encoding so Greek names and messages render correctly.

---

## Requirements

Python 3.8+. No external dependencies — standard library only.

---

## License

MIT — see [LICENSE](LICENSE)

---

## Author

Anastasios Papalias  
[acopon.online](https://acopon.online) · [GitHub](https://github.com/AnastasiosPapalias)
