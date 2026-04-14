#!/usr/bin/env python3
"""
extract_messenger_personality.py
=================================
Extract Facebook Messenger messages from a Facebook data export and build
a structured dataset for AI fine-tuning, RAG pipelines, or writing-style
analysis.

Outputs (all in --output folder):
  messages.jsonl              — master dataset, one message per line
  messages.csv                — spreadsheet-friendly export
  messages.sqlite             — fully-indexed SQLite database
  style_profiles.json         — per-conversation style summaries (my messages only)
  global_summary.json         — whole-dataset statistics (my messages only)
  markdown_shards/            — messages grouped by conversation + month
  TRAINING_INSTRUCTIONS.md    — notes for AI/LLM use

Both sides of each conversation are stored. Use --my-name to distinguish
your messages (is_me=1) from others (is_me=0).

Run build_training_pairs.py on the output to generate fine-tuning pairs.

Supports English + Greek text. No external dependencies.

Usage:
    python extract_messenger_personality.py \\
        --input  "/path/to/facebook-export" \\
        --output "./messenger_output" \\
        --my-name "Your Facebook Name"

Optional flags:
    --include-group-chats     include group conversations (excluded by default)
    --min-chars N             minimum cleaned message length to keep (default: 2)

How to get your Facebook export:
    Facebook → Settings → Your Facebook information → Download your information
    → Select "Messages" → Format: JSON → Request download
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Tuple

__version__ = "2.0.0"
__author__  = "Anastasios Papalias"
__license__ = "MIT"

# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------

URL_RE        = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
MULTISPACE_RE = re.compile(r"\s+")
WORD_RE       = re.compile(r"\b\w+\b", re.UNICODE)

# Greek Unicode ranges
GREEK_RE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]")
LATIN_RE = re.compile(r"[A-Za-z]")

SYSTEM_MESSAGE_KEYS = {
    "photos", "videos", "audio_files", "files",
    "gifs", "sticker", "share", "call_duration", "missed", "is_unsent",
}

SKIP_CONTENT_EXACT = {""}

# ---------------------------------------------------------------------------
# Facebook encoding fix
# ---------------------------------------------------------------------------

# Match runs of latin-1 high-byte characters (0x80-0xFF).
# Facebook double-encodes UTF-8 as latin-1, so consecutive high bytes
# represent multi-byte UTF-8 sequences. We fix each run independently;
# runs that can't be decoded (corrupted sequences) are left unchanged.
_HIGHBYTE_RE = re.compile(r"[\x80-\xFF]+")

def fix_fb_encoding(text: str) -> str:
    """
    Facebook exports UTF-8 text as latin-1-decoded Unicode strings.
    Fix by finding runs of high-byte characters and re-encoding each
    run as UTF-8. Runs that fail (corrupted) are left as-is.

    Example: "Î§ÏÎ®ÏÏÎ·Ï" -> "Χρήστης"

    Uses run-based matching so that ASCII characters (including spaces)
    between garbled sequences don't prevent recovery of surrounding text.
    """
    if not text:
        return text

    def _fix_run(m: re.Match) -> str:
        s = m.group()
        try:
            return s.encode("latin-1").decode("utf-8")
        except (UnicodeDecodeError, UnicodeEncodeError):
            return s

    return _HIGHBYTE_RE.sub(_fix_run, text)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class MessageRecord:
    message_id:         str
    conversation_id:    str
    conversation_title: str
    is_group_chat:      bool
    participants:       List[str]
    sender_name:        str
    is_me:              bool      # True = sent by the subject (--my-name)
    timestamp_iso:      str
    timestamp_ms:       int
    year:               int
    month:              int
    day:                int
    hour:               int
    minute:             int
    weekday:            str
    text_original:      str
    text_clean:         str
    text_no_urls:       str
    char_count:         int
    word_count:         int
    language_guess:     str
    has_urls:           bool
    reaction_count:     int
    photos_count:       int
    videos_count:       int
    audio_count:        int
    files_count:        int
    gifs_count:         int
    shares_count:       int
    sticker_present:    bool
    source_json:        str
    source_folder:      str

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract Messenger messages into a structured dataset for AI fine-tuning.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--input",  required=True, help="Root folder of Facebook export")
    parser.add_argument("--output", required=True, help="Output folder")
    parser.add_argument("--my-name", required=True,
                        help="Your exact Facebook sender_name (as it appears in the export)")
    parser.add_argument("--include-group-chats", action="store_true",
                        help="Include group chats (default: 1-on-1 only)")
    parser.add_argument("--min-chars", type=int, default=2,
                        help="Minimum cleaned message length to keep (default: 2)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args()

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def safe_slug(text: str, max_len: int = 80) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_-]+", "_", text)
    return (text.strip("_") or "untitled")[:max_len]

def read_json_with_fallback(path: Path) -> Optional[dict]:
    """Try reading the file as utf-8 first, fall back to latin-1."""
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            with path.open("r", encoding=enc) as f:
                return json.load(f)
        except Exception:
            continue
    return None

def normalize_spaces(text: str) -> str:
    return MULTISPACE_RE.sub(" ", text).strip()

def strip_urls(text: str) -> str:
    return normalize_spaces(URL_RE.sub("", text))

def clean_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    return normalize_spaces(text)

def detect_language(text: str) -> str:
    if not text:
        return "unknown"
    greek = len(GREEK_RE.findall(text))
    latin = len(LATIN_RE.findall(text))
    if greek > 0 and latin == 0:
        return "greek"
    if latin > 0 and greek == 0:
        return "english_or_latin"
    if greek > 0 and latin > 0:
        return "mixed"
    return "unknown"

def count_words(text: str) -> int:
    return len(WORD_RE.findall(text))

def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()

def timestamp_to_dt(timestamp_ms: int) -> datetime:
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).astimezone()

def extract_participants(data: dict) -> List[str]:
    return sorted({
        clean_text(fix_fb_encoding(p.get("name", "").strip()))
        for p in data.get("participants", [])
        if p.get("name", "").strip()
    })

def conversation_identity(title: str, participants: List[str]) -> str:
    return sha1_text(f"{title.strip()}::{'|'.join(participants)}")

def message_identity(conversation_id: str, timestamp_ms: int,
                     sender_name: str, text: str) -> str:
    return sha1_text(f"{conversation_id}::{timestamp_ms}::{sender_name}::{text}")

def looks_like_noise(msg: dict, cleaned: str) -> bool:
    if msg.get("is_unsent"):
        return True
    if not cleaned and any(k in msg for k in SYSTEM_MESSAGE_KEYS):
        return True
    if not cleaned and not any(msg.get(k) for k in ("photos", "videos", "files")):
        return True
    return False

def count_field(msg: dict, field: str) -> int:
    v = msg.get(field, [])
    return len(v) if isinstance(v, list) else 0

def progress(current: int, total: int, width: int = 40) -> str:
    filled = int(width * current / total) if total else 0
    bar    = "█" * filled + "░" * (width - filled)
    pct    = 100 * current / total if total else 0
    return f"\r  [{bar}] {pct:5.1f}%  {current:,}/{total:,} files"

# ---------------------------------------------------------------------------
# Core extraction  (v2: stores BOTH sides, is_me properly detected)
# ---------------------------------------------------------------------------

def extract_records(
    input_root: Path,
    my_name: str,
    include_group_chats: bool,
    min_chars: int,
) -> List[MessageRecord]:

    json_files = sorted(input_root.rglob("message_*.json"))
    total      = len(json_files)
    records: List[MessageRecord] = []
    seen_ids: set                = set()

    print(f"  Found {total:,} JSON files. Extracting…")

    for i, json_file in enumerate(json_files, 1):
        if i % 100 == 0 or i == total:
            print(progress(i, total), end="", flush=True)

        data = read_json_with_fallback(json_file)
        if not data:
            continue

        conversation_title = clean_text(
            fix_fb_encoding(data.get("title", json_file.parent.name))
        )
        participants  = extract_participants(data)
        is_group_chat = len(participants) > 2

        if is_group_chat and not include_group_chats:
            continue

        conversation_id = conversation_identity(conversation_title, participants)

        for msg in data.get("messages", []):
            sender_raw  = msg.get("sender_name", "")
            sender_name = clean_text(fix_fb_encoding(sender_raw))

            # v2: process ALL senders, not just my_name
            is_me = (sender_name == my_name)

            content      = fix_fb_encoding(msg.get("content") or "")
            text_clean   = clean_text(content)
            text_no_urls = strip_urls(text_clean)

            if text_clean in SKIP_CONTENT_EXACT and looks_like_noise(msg, text_clean):
                continue
            if len(text_no_urls) < min_chars and looks_like_noise(msg, text_clean):
                continue

            timestamp_ms = msg.get("timestamp_ms")
            if not isinstance(timestamp_ms, int):
                continue

            dt  = timestamp_to_dt(timestamp_ms)
            mid = message_identity(conversation_id, timestamp_ms, sender_name, text_clean)

            if mid in seen_ids:
                continue
            seen_ids.add(mid)

            records.append(MessageRecord(
                message_id         = mid,
                conversation_id    = conversation_id,
                conversation_title = conversation_title,
                is_group_chat      = is_group_chat,
                participants       = participants,
                sender_name        = sender_name,
                is_me              = is_me,
                timestamp_iso      = dt.isoformat(),
                timestamp_ms       = timestamp_ms,
                year               = dt.year,
                month              = dt.month,
                day                = dt.day,
                hour               = dt.hour,
                minute             = dt.minute,
                weekday            = dt.strftime("%A"),
                text_original      = content,
                text_clean         = text_clean,
                text_no_urls       = text_no_urls,
                char_count         = len(text_clean),
                word_count         = count_words(text_clean),
                language_guess     = detect_language(text_clean),
                has_urls           = bool(URL_RE.search(text_clean)),
                reaction_count     = len(msg.get("reactions", []))
                                     if isinstance(msg.get("reactions"), list) else 0,
                photos_count       = count_field(msg, "photos"),
                videos_count       = count_field(msg, "videos"),
                audio_count        = count_field(msg, "audio_files"),
                files_count        = count_field(msg, "files"),
                gifs_count         = count_field(msg, "gifs"),
                shares_count       = 1 if msg.get("share") else 0,
                sticker_present    = bool(msg.get("sticker")),
                source_json        = str(json_file),
                source_folder      = str(json_file.parent),
            ))

    print()  # newline after progress bar
    records.sort(key=lambda r: r.timestamp_ms)
    return records

# ---------------------------------------------------------------------------
# Save outputs
# ---------------------------------------------------------------------------

def save_jsonl(records: List[MessageRecord], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")

def save_csv(records: List[MessageRecord], path: Path) -> None:
    if not records:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        for rec in records:
            row = asdict(rec)
            row["participants"] = json.dumps(row["participants"], ensure_ascii=False)
            writer.writerow(row)

def save_sqlite(records: List[MessageRecord], path: Path) -> None:
    conn = sqlite3.connect(path)
    cur  = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        message_id TEXT PRIMARY KEY,
        conversation_id TEXT, conversation_title TEXT,
        is_group_chat INTEGER, participants_json TEXT,
        sender_name TEXT, is_me INTEGER,
        timestamp_iso TEXT, timestamp_ms INTEGER,
        year INTEGER, month INTEGER, day INTEGER,
        hour INTEGER, minute INTEGER, weekday TEXT,
        text_original TEXT, text_clean TEXT, text_no_urls TEXT,
        char_count INTEGER, word_count INTEGER, language_guess TEXT,
        has_urls INTEGER, reaction_count INTEGER,
        photos_count INTEGER, videos_count INTEGER,
        audio_count INTEGER, files_count INTEGER,
        gifs_count INTEGER, shares_count INTEGER,
        sticker_present INTEGER, source_json TEXT, source_folder TEXT
    )""")

    for col in ("conversation_id", "timestamp_ms", "year", "month",
                "language_guess", "conversation_title", "is_me"):
        cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{col} ON messages({col})")

    cur.executemany("""
    INSERT OR REPLACE INTO messages VALUES (
        ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
    )""", [
        (r.message_id, r.conversation_id, r.conversation_title,
         int(r.is_group_chat),
         json.dumps(r.participants, ensure_ascii=False),
         r.sender_name, int(r.is_me),
         r.timestamp_iso, r.timestamp_ms,
         r.year, r.month, r.day, r.hour, r.minute, r.weekday,
         r.text_original, r.text_clean, r.text_no_urls,
         r.char_count, r.word_count, r.language_guess,
         int(r.has_urls), r.reaction_count,
         r.photos_count, r.videos_count, r.audio_count,
         r.files_count, r.gifs_count, r.shares_count,
         int(r.sticker_present), r.source_json, r.source_folder)
        for r in records
    ])
    conn.commit()
    conn.close()

# ---------------------------------------------------------------------------
# Markdown shards  (my messages only — same as v1)
# ---------------------------------------------------------------------------

def build_markdown_shards(records: List[MessageRecord], md_root: Path) -> None:
    my_records = [r for r in records if r.is_me]
    grouped: Dict[Tuple[str, int, int], List[MessageRecord]] = defaultdict(list)
    for rec in my_records:
        grouped[(rec.conversation_title, rec.year, rec.month)].append(rec)

    for (title, year, month), msgs in grouped.items():
        folder = md_root / safe_slug(title)
        ensure_dir(folder)
        path = folder / f"{year:04d}-{month:02d}.md"
        with path.open("w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            f.write(f"- Period: {year}-{month:02d}\n")
            f.write(f"- Messages: {len(msgs)}\n\n---\n\n")
            for m in msgs:
                f.write(f"## {m.timestamp_iso}\n\n")
                f.write(f"- {m.weekday}  {m.hour:02d}:{m.minute:02d}"
                        f"  lang:{m.language_guess}  words:{m.word_count}\n\n")
                f.write(f"```\n{m.text_clean}\n```\n\n")

# ---------------------------------------------------------------------------
# Style profiles  (my messages only — same as v1)
# ---------------------------------------------------------------------------

def top_terms(texts: List[str], limit: int = 40) -> List[Tuple[str, int]]:
    STOPWORDS = {
        "the","and","to","a","i","you","it","is","in","of","for","on","that","this",
        "me","my","we","our","your","be","are","am","was","were","with","at","as",
        "but","if","so","not","do","did","have","has","had","will","would","can",
        "could","just","im","its","ill","dont","yeah","ok","okay","yes","no","hi",
        "και","να","σε","το","τη","της","των","τα","με","για","που","από","στο",
        "στη","στον","στην","είναι","θα","δεν","μια","ένα","έχω","έχει","πως","τι",
        "την","τον","οι","ο","η","μου","σου","μας","σας","τους","τις","σαν","αλλά",
        "αν","ότι","κάτι","κάποιος","εδώ","εκεί","τώρα","πότε","πού","πώς","ναι",
    }
    counter: Counter = Counter()
    for text in texts:
        for token in WORD_RE.findall(text.lower()):
            if len(token) >= 2 and token not in STOPWORDS:
                counter[token] += 1
    return counter.most_common(limit)

def hour_bucket(hour: int) -> str:
    if 5  <= hour < 12: return "morning"
    if 12 <= hour < 17: return "afternoon"
    if 17 <= hour < 22: return "evening"
    return "night"

def infer_style_hints(msgs: List[MessageRecord]) -> Dict[str, Any]:
    if not msgs:
        return {}
    avg_words  = mean(m.word_count for m in msgs)
    avg_chars  = mean(m.char_count for m in msgs)
    greek_n    = sum(1 for m in msgs if m.language_guess == "greek")
    english_n  = sum(1 for m in msgs if m.language_guess == "english_or_latin")
    mixed_n    = sum(1 for m in msgs if m.language_guess == "mixed")

    if   avg_words < 6:  length_style = "very_short"
    elif avg_words < 14: length_style = "short"
    elif avg_words < 30: length_style = "medium"
    else:                length_style = "long"

    totals = greek_n + english_n + mixed_n
    if totals == 0:
        dominant_language = "unclear"
    elif greek_n >= english_n and greek_n >= mixed_n:
        dominant_language = "greek"
    elif english_n >= greek_n and english_n >= mixed_n:
        dominant_language = "english"
    else:
        dominant_language = "mixed"

    night_ratio = sum(1 for m in msgs if hour_bucket(m.hour) == "night") / len(msgs)
    url_ratio   = sum(1 for m in msgs if m.has_urls) / len(msgs)

    return {
        "dominant_language":  dominant_language,
        "length_style":       length_style,
        "night_heavy":        night_ratio > 0.35,
        "often_shares_links": url_ratio   > 0.10,
        "average_chars":      round(avg_chars, 2),
        "average_words":      round(avg_words, 2),
    }

def build_style_summaries(records: List[MessageRecord], output_path: Path) -> None:
    # Style summaries are computed over subject's messages only
    my_records = [r for r in records if r.is_me]
    by_conv: Dict[str, List[MessageRecord]] = defaultdict(list)
    for rec in my_records:
        by_conv[rec.conversation_title].append(rec)

    summaries = {}
    for title, msgs in sorted(by_conv.items()):
        texts = [m.text_clean for m in msgs if m.text_clean]
        if not texts:
            continue
        summaries[title] = {
            "conversation_title":     title,
            "participants":           msgs[0].participants,
            "is_group_chat":          msgs[0].is_group_chat,
            "message_count":          len(msgs),
            "first_message":          msgs[0].timestamp_iso,
            "last_message":           msgs[-1].timestamp_iso,
            "average_word_count":     round(mean(m.word_count for m in msgs), 2),
            "average_char_count":     round(mean(m.char_count for m in msgs), 2),
            "language_distribution":  dict(Counter(m.language_guess for m in msgs)),
            "time_of_day":            dict(Counter(hour_bucket(m.hour) for m in msgs)),
            "weekday_distribution":   dict(Counter(m.weekday for m in msgs)),
            "month_distribution":     dict(Counter(f"{m.year}-{m.month:02d}" for m in msgs)),
            "messages_with_urls":     sum(1 for m in msgs if m.has_urls),
            "top_terms":              top_terms(texts),
            "style_hints":            infer_style_hints(msgs),
        }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------------------
# Global summary  (my messages only — comparable to v1)
# ---------------------------------------------------------------------------

def save_global_summary(records: List[MessageRecord], path: Path) -> None:
    my_records = [r for r in records if r.is_me]
    all_count  = len(records)
    my_count   = len(my_records)

    if not my_records:
        summary = {"message_count": 0}
    else:
        by_conv  = Counter(r.conversation_title for r in my_records)
        by_lang  = Counter(r.language_guess for r in my_records)
        by_year  = Counter(r.year for r in my_records)
        by_month = Counter(f"{r.year:04d}-{r.month:02d}" for r in my_records)
        summary  = {
            "version":                __version__,
            "total_messages_all":     all_count,
            "message_count":          my_count,
            "conversation_count":     len(by_conv),
            "language_distribution":  dict(by_lang),
            "messages_per_year":      {str(k): v for k, v in sorted(by_year.items())},
            "messages_per_month":     dict(by_month),
            "top_conversations":      by_conv.most_common(50),
            "first_message":          my_records[0].timestamp_iso,
            "last_message":           my_records[-1].timestamp_iso,
        }
    with path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------------------
# Training instructions
# ---------------------------------------------------------------------------

def save_training_instructions(path: Path) -> None:
    path.write_text("""\
# Personality Dataset — Training Instructions

This folder contains a structured export of Facebook Messenger conversations.
Both sides of each conversation are stored (is_me=1 for subject, is_me=0 for others).

## Files

| File | Description |
|------|-------------|
| messages.jsonl | Master dataset — one JSON object per line (both sides) |
| messages.csv | Spreadsheet-friendly export |
| messages.sqlite | Fully-indexed SQLite database |
| style_profiles.json | Per-conversation style summaries (subject's messages only) |
| global_summary.json | Whole-dataset statistics (subject's messages only) |
| markdown_shards/ | Subject's messages grouped by conversation and month |
| training_pairs.jsonl | Fine-tuning pairs (run build_training_pairs.py to generate) |

## Intended use

Use messages.jsonl / messages.sqlite to build conversation pairs for fine-tuning.
Run build_training_pairs.py to generate training_pairs.jsonl in your desired format.

## Rules

1. Do not copy messages verbatim.
2. Learn tone, rhythm, and phrasing patterns.
3. Adapt based on context: who, when, what topic.
4. Use retrieval over memorisation for specific facts.
""", encoding="utf-8")

# ---------------------------------------------------------------------------
# Pretty stats printer
# ---------------------------------------------------------------------------

def print_stats(records: List[MessageRecord], output_root: Path) -> None:
    if not records:
        return

    my_records = [r for r in records if r.is_me]
    by_lang  = Counter(r.language_guess for r in my_records)
    by_year  = Counter(r.year for r in my_records)
    by_conv  = Counter(r.conversation_title for r in my_records)
    avg_words = mean(r.word_count for r in my_records) if my_records else 0

    print()
    print("┌─────────────────────────────────────────────┐")
    print("│         messenger-personality-extractor      │")
    print("│              Extraction complete             │")
    print("├─────────────────────────────────────────────┤")
    print(f"│  Total messages (all)   : {len(records):>8,}             │")
    print(f"│  Subject messages (me)  : {len(my_records):>8,}             │")
    print(f"│  Conversations          : {len(by_conv):>8,}             │")
    print(f"│  Avg words/msg (mine)   : {avg_words:>8.1f}             │")
    print(f"│  First message          : {my_records[0].timestamp_iso[:10] if my_records else 'n/a'}              │")
    print(f"│  Last message           : {my_records[-1].timestamp_iso[:10] if my_records else 'n/a'}              │")
    print("├─────────────────────────────────────────────┤")
    print("│  Language breakdown (my messages):          │")
    for lang, count in by_lang.most_common():
        pct = 100 * count / len(my_records) if my_records else 0
        print(f"│    {lang:<22} {count:>8,}  ({pct:4.1f}%)   │")
    print("├─────────────────────────────────────────────┤")
    print("│  Top conversations (by my message count):   │")
    for title, count in by_conv.most_common(5):
        title_short = title[:28].ljust(28)
        print(f"│    {title_short} {count:>6,}          │")
    print("├─────────────────────────────────────────────┤")
    print("│  My messages per year:                      │")
    for year, count in sorted(by_year.items()):
        bar = "▓" * min(20, count // 500)
        print(f"│    {year}  {bar:<20} {count:>6,}     │")
    print("├─────────────────────────────────────────────┤")
    print(f"│  Output: {str(output_root)[:37]:<37}│")
    print("└─────────────────────────────────────────────┘")
    print()
    print("  Next step: run build_training_pairs.py to generate fine-tuning data.")
    print()

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    input_root  = Path(args.input).expanduser().resolve()
    output_root = Path(args.output).expanduser().resolve()

    if not input_root.exists():
        print(f"[ERROR] Input folder not found: {input_root}", file=sys.stderr)
        sys.exit(1)

    ensure_dir(output_root)

    print(f"\nmessenger-personality-extractor v{__version__}")
    print(f"  Input  : {input_root}")
    print(f"  Output : {output_root}")
    print(f"  Name   : {args.my_name}")
    print(f"  Groups : {'yes' if args.include_group_chats else 'no'}\n")

    records = extract_records(
        input_root          = input_root,
        my_name             = args.my_name,
        include_group_chats = args.include_group_chats,
        min_chars           = args.min_chars,
    )

    if not records:
        print("[ERROR] No messages found.", file=sys.stderr)
        print("  Check that --my-name matches exactly as it appears in the export.", file=sys.stderr)
        sys.exit(1)

    my_count = sum(1 for r in records if r.is_me)
    if my_count == 0:
        print(f"[ERROR] No messages found for '{args.my_name}'.", file=sys.stderr)
        print("  Check that --my-name matches exactly (case-sensitive).", file=sys.stderr)
        sys.exit(1)

    print(f"  Saving messages.jsonl  ({len(records):,} records)…")
    save_jsonl(records, output_root / "messages.jsonl")

    print("  Saving messages.csv …")
    save_csv(records, output_root / "messages.csv")

    print("  Saving messages.sqlite …")
    save_sqlite(records, output_root / "messages.sqlite")

    print("  Building markdown shards (subject's messages only)…")
    build_markdown_shards(records, output_root / "markdown_shards")

    print("  Building style profiles (subject's messages only)…")
    build_style_summaries(records, output_root / "style_profiles.json")

    print("  Saving global summary (subject's messages only)…")
    save_global_summary(records, output_root / "global_summary.json")

    print("  Saving training instructions…")
    save_training_instructions(output_root / "TRAINING_INSTRUCTIONS.md")

    print_stats(records, output_root)


if __name__ == "__main__":
    main()
