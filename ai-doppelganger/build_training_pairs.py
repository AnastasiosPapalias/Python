#!/usr/bin/env python3
"""
build_training_pairs.py
========================
Build fine-tuning conversation pairs from a messenger dataset produced by
extract_messenger_personality.py v2.0+.

A "training pair" is: someone sends a message → subject replies.
Pairs are extracted by finding adjacent (other → me) message sequences
within the same conversation and a configurable time window.

Output formats:
  --format openai     OpenAI fine-tuning JSONL (chat format, system prompt included)
  --format alpaca     Alpaca instruction format (instruction/input/output)
  --format sharegpt   ShareGPT multi-turn format (used by Axolotl, LLaMA Factory)
  --format raw        Simple prompt/completion pairs

Usage:
    python build_training_pairs.py \\
        --db     /path/to/messages.sqlite \\
        --output /path/to/training_pairs.jsonl \\
        --system-prompt /path/to/system-prompt.txt \\
        --format openai \\
        --context-turns 3 \\
        --max-gap-minutes 120

Options:
    --db                  Path to messages.sqlite (required)
    --output              Output JSONL path (default: training_pairs.jsonl)
    --system-prompt       Path to a .txt or .md file with your system prompt
    --format              Output format: openai | alpaca | sharegpt | raw (default: openai)
    --context-turns       Number of prior turns to include as context (default: 3)
    --max-gap-minutes     Max minutes between trigger and reply (default: 120)
    --min-words           Minimum word count for both sides of a pair (default: 2)
    --exclude-urls        Exclude messages that are only URLs (default: True)
    --dedupe              Remove near-duplicate pairs (default: True)
    --split               Write train/val split at 90/10 (default: False)
    --stats               Print statistics after building (default: True)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sqlite3
import sys
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

__version__ = "1.0.0"

URL_ONLY_RE = re.compile(r"^https?://\S+$")
WORD_RE     = re.compile(r"\b\w+\b", re.UNICODE)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build fine-tuning pairs from a Messenger SQLite dataset.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--db",             required=True,  help="Path to messages.sqlite")
    p.add_argument("--output",         default="training_pairs.jsonl")
    p.add_argument("--system-prompt",  default=None,   help="Path to system prompt file (.txt or .md)")
    p.add_argument("--format",         default="openai",
                   choices=["openai", "alpaca", "sharegpt", "raw"],
                   help="Output format (default: openai)")
    p.add_argument("--context-turns",  type=int,   default=3,
                   help="Prior turns to include as context (default: 3)")
    p.add_argument("--max-gap-minutes",type=int,   default=120,
                   help="Max minutes between trigger message and reply (default: 120)")
    p.add_argument("--min-words",      type=int,   default=2,
                   help="Min words in both messages of a pair (default: 2)")
    p.add_argument("--no-exclude-urls",action="store_true",
                   help="Keep URL-only messages (default: exclude)")
    p.add_argument("--no-dedupe",      action="store_true",
                   help="Skip deduplication (default: dedupe enabled)")
    p.add_argument("--split",          action="store_true",
                   help="Write 90/10 train/val split")
    p.add_argument("--no-stats",       action="store_true",
                   help="Skip stats output")
    p.add_argument("--version",        action="version", version=f"%(prog)s {__version__}")
    return p.parse_args()

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_messages(db_path: Path) -> Dict[str, List[dict]]:
    """Load all messages from SQLite, grouped by conversation_id, sorted by time."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Verify both sides exist in the DB
    cur.execute("SELECT is_me, COUNT(*) FROM messages GROUP BY is_me")
    distribution = dict(cur.fetchall())
    me_count    = distribution.get(1, 0)
    other_count = distribution.get(0, 0)

    if other_count == 0:
        print("[ERROR] This dataset only contains the subject's messages (is_me=1 for all).")
        print("  Re-run extract_messenger_personality.py v2.0+ to capture both sides.")
        conn.close()
        sys.exit(1)

    print(f"  Dataset: {me_count:,} subject messages + {other_count:,} other messages")

    cur.execute("""
        SELECT conversation_id, conversation_title, is_group_chat,
               sender_name, is_me, timestamp_ms, text_clean,
               word_count, language_guess, has_urls
        FROM messages
        WHERE text_clean IS NOT NULL AND text_clean != ''
        ORDER BY conversation_id, timestamp_ms
    """)

    by_conv: Dict[str, List[dict]] = defaultdict(list)
    for row in cur.fetchall():
        by_conv[row["conversation_id"]].append(dict(row))

    conn.close()
    return by_conv

def load_system_prompt(path: Optional[str]) -> str:
    if not path:
        return (
            "You are the subject of this dataset. Respond as they would — "
            "match their language, message length, tone, and style as shown "
            "in their conversation history."
        )
    p = Path(path)
    if not p.exists():
        print(f"[WARN] System prompt file not found: {path}. Using default.")
        return load_system_prompt(None)

    text = p.read_text(encoding="utf-8")

    # If it's the full system-prompt.md file, extract just the short version block
    if "```" in text:
        blocks = re.findall(r"```\n(.*?)```", text, re.DOTALL)
        if blocks:
            # Return the first code block (the short deployable prompt)
            return blocks[0].strip()
    return text.strip()

# ---------------------------------------------------------------------------
# Pair extraction
# ---------------------------------------------------------------------------

def is_url_only(text: str) -> bool:
    return bool(URL_ONLY_RE.match(text.strip()))

def word_count(text: str) -> int:
    return len(WORD_RE.findall(text))

def pair_fingerprint(trigger: str, reply: str) -> str:
    return hashlib.md5(f"{trigger[:80]}|||{reply[:80]}".encode()).hexdigest()

def extract_pairs(
    by_conv: Dict[str, List[dict]],
    max_gap_ms: int,
    min_words: int,
    exclude_urls: bool,
    context_turns: int,
) -> List[dict]:
    """
    For each conversation, find sequences where:
      1. A non-subject message (is_me=0) is sent
      2. The subject (is_me=1) replies within max_gap_ms
      3. Both messages meet minimum word count

    Returns list of pair dicts with full context.
    """
    pairs = []

    for conv_id, messages in by_conv.items():
        if not messages:
            continue

        conv_title    = messages[0]["conversation_title"]
        is_group_chat = messages[0]["is_group_chat"]

        # Build index of messages for context lookup
        for idx, msg in enumerate(messages):
            # We need a non-subject message as the trigger
            if msg["is_me"]:
                continue

            trigger_text = msg["text_clean"] or ""
            if word_count(trigger_text) < min_words:
                continue
            if exclude_urls and is_url_only(trigger_text):
                continue

            # Find subject's first reply after this message within the time window
            reply = None
            for j in range(idx + 1, len(messages)):
                gap_ms = messages[j]["timestamp_ms"] - msg["timestamp_ms"]
                if gap_ms > max_gap_ms:
                    break
                if messages[j]["is_me"]:
                    # Check the reply is actually a response (not part of a different thread)
                    reply_text = messages[j]["text_clean"] or ""
                    if word_count(reply_text) < min_words:
                        continue
                    if exclude_urls and is_url_only(reply_text):
                        continue
                    reply = messages[j]
                    break

            if not reply:
                continue

            # Gather context: up to context_turns turns before the trigger
            context = []
            context_start = max(0, idx - (context_turns * 2))
            for k in range(context_start, idx):
                m = messages[k]
                if m["text_clean"]:
                    context.append({
                        "role":    "assistant" if m["is_me"] else "user",
                        "content": m["text_clean"],
                        "lang":    m["language_guess"],
                    })

            pairs.append({
                "conversation_title": conv_title,
                "is_group_chat":      is_group_chat,
                "trigger": {
                    "text":       trigger_text,
                    "sender":     msg["sender_name"],
                    "timestamp":  msg["timestamp_ms"],
                    "lang":       msg["language_guess"],
                    "words":      msg["word_count"],
                },
                "reply": {
                    "text":       reply["text_clean"],
                    "timestamp":  reply["timestamp_ms"],
                    "lang":       reply["language_guess"],
                    "words":      reply["word_count"],
                    "gap_seconds": (reply["timestamp_ms"] - msg["timestamp_ms"]) // 1000,
                },
                "context": context,
            })

    return pairs

def deduplicate(pairs: List[dict]) -> List[dict]:
    seen = set()
    result = []
    for pair in pairs:
        fp = pair_fingerprint(pair["trigger"]["text"], pair["reply"]["text"])
        if fp not in seen:
            seen.add(fp)
            result.append(pair)
    return result

# ---------------------------------------------------------------------------
# Format converters
# ---------------------------------------------------------------------------

def to_openai_format(pair: dict, system_prompt: str) -> dict:
    """OpenAI fine-tuning chat format."""
    messages = [{"role": "system", "content": system_prompt}]

    # Add context turns
    for turn in pair["context"]:
        messages.append({"role": turn["role"], "content": turn["content"]})

    # Add the trigger and reply
    messages.append({"role": "user",      "content": pair["trigger"]["text"]})
    messages.append({"role": "assistant", "content": pair["reply"]["text"]})

    return {"messages": messages}

def to_alpaca_format(pair: dict, system_prompt: str) -> dict:
    """Alpaca instruction format."""
    context_str = ""
    if pair["context"]:
        lines = []
        for turn in pair["context"]:
            role = "Subject" if turn["role"] == "assistant" else "Other"
            lines.append(f"{role}: {turn['content']}")
        context_str = "\n".join(lines) + "\n\n"

    return {
        "instruction": system_prompt,
        "input": f"{context_str}{pair['trigger']['text']}",
        "output": pair["reply"]["text"],
    }

def to_sharegpt_format(pair: dict, system_prompt: str) -> dict:
    """ShareGPT format (used by Axolotl, LLaMA Factory, etc.)."""
    conversations = []

    if system_prompt:
        conversations.append({"from": "system", "value": system_prompt})

    for turn in pair["context"]:
        role = "gpt" if turn["role"] == "assistant" else "human"
        conversations.append({"from": role, "value": turn["content"]})

    conversations.append({"from": "human", "value": pair["trigger"]["text"]})
    conversations.append({"from": "gpt",   "value": pair["reply"]["text"]})

    return {"conversations": conversations}

def to_raw_format(pair: dict, system_prompt: str) -> dict:
    """Simple prompt/completion format."""
    context_str = ""
    if pair["context"]:
        lines = []
        for turn in pair["context"]:
            role = "Subject" if turn["role"] == "assistant" else "Other"
            lines.append(f"{role}: {turn['content']}")
        context_str = "\n".join(lines) + "\n"

    prompt = f"{context_str}Other: {pair['trigger']['text']}\nSubject:"
    return {
        "prompt":     prompt,
        "completion": f" {pair['reply']['text']}",
    }

FORMATTERS = {
    "openai":   to_openai_format,
    "alpaca":   to_alpaca_format,
    "sharegpt": to_sharegpt_format,
    "raw":      to_raw_format,
}

# ---------------------------------------------------------------------------
# Write output
# ---------------------------------------------------------------------------

def write_jsonl(records: List[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def print_stats(pairs: List[dict], fmt: str) -> None:
    if not pairs:
        print("  No pairs generated.")
        return

    lang_dist = Counter(p["reply"]["lang"] for p in pairs)
    gap_dist  = Counter(
        "< 5min"   if p["reply"]["gap_seconds"] < 300   else
        "5-30min"  if p["reply"]["gap_seconds"] < 1800  else
        "30-120min"
        for p in pairs
    )
    reply_wc  = [p["reply"]["words"] for p in pairs]
    avg_words = sum(reply_wc) / len(reply_wc)

    convs = Counter(p["conversation_title"] for p in pairs)

    print()
    print("┌──────────────────────────────────────────────┐")
    print("│          build_training_pairs complete        │")
    print("├──────────────────────────────────────────────┤")
    print(f"│  Training pairs generated : {len(pairs):>8,}          │")
    print(f"│  Output format            : {fmt:<16}  │")
    print(f"│  Avg reply words          : {avg_words:>8.1f}          │")
    print("├──────────────────────────────────────────────┤")
    print("│  Reply language distribution:                │")
    for lang, count in lang_dist.most_common():
        pct = 100 * count / len(pairs)
        print(f"│    {lang:<24} {count:>7,}  ({pct:4.1f}%)  │")
    print("├──────────────────────────────────────────────┤")
    print("│  Reply gap distribution:                     │")
    for bucket, count in sorted(gap_dist.items()):
        pct = 100 * count / len(pairs)
        print(f"│    {bucket:<24} {count:>7,}  ({pct:4.1f}%)  │")
    print("├──────────────────────────────────────────────┤")
    print("│  Top conversations (by pair count):          │")
    for title, count in convs.most_common(5):
        title_short = title[:27].ljust(27)
        print(f"│    {title_short}  {count:>6,}         │")
    print("└──────────────────────────────────────────────┘")
    print()

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    db_path     = Path(args.db).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not db_path.exists():
        print(f"[ERROR] Database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    max_gap_ms    = args.max_gap_minutes * 60 * 1000
    exclude_urls  = not args.no_exclude_urls
    dedupe        = not args.no_dedupe

    print(f"\nbuild_training_pairs v{__version__}")
    print(f"  DB            : {db_path}")
    print(f"  Output        : {output_path}")
    print(f"  Format        : {args.format}")
    print(f"  Context turns : {args.context_turns}")
    print(f"  Max gap       : {args.max_gap_minutes} minutes")
    print(f"  Min words     : {args.min_words}")
    print()

    print("  Loading messages…")
    by_conv = load_messages(db_path)
    print(f"  Loaded {len(by_conv):,} conversations.")

    system_prompt = load_system_prompt(args.system_prompt)
    print(f"  System prompt: {len(system_prompt)} chars")

    print("  Extracting pairs…")
    pairs = extract_pairs(
        by_conv       = by_conv,
        max_gap_ms    = max_gap_ms,
        min_words     = args.min_words,
        exclude_urls  = exclude_urls,
        context_turns = args.context_turns,
    )
    print(f"  Raw pairs: {len(pairs):,}")

    if dedupe:
        before = len(pairs)
        pairs  = deduplicate(pairs)
        print(f"  After dedup: {len(pairs):,} (removed {before - len(pairs):,})")

    # Shuffle for better training distribution
    random.seed(42)
    random.shuffle(pairs)

    formatter = FORMATTERS[args.format]
    formatted = [formatter(p, system_prompt) for p in pairs]

    if args.split:
        split_idx = int(len(formatted) * 0.9)
        train     = formatted[:split_idx]
        val       = formatted[split_idx:]
        train_path = output_path.with_stem(output_path.stem + "_train")
        val_path   = output_path.with_stem(output_path.stem + "_val")
        write_jsonl(train, train_path)
        write_jsonl(val,   val_path)
        print(f"  Written: {train_path.name} ({len(train):,} pairs)")
        print(f"  Written: {val_path.name}   ({len(val):,} pairs)")
    else:
        write_jsonl(formatted, output_path)
        print(f"  Written: {output_path.name} ({len(formatted):,} pairs)")

    if not args.no_stats:
        print_stats(pairs, args.format)

    print("  Next steps:")
    print("  → OpenAI fine-tuning : see FINE_TUNING.md for upload + training commands")
    print("  → Local (Unsloth)    : use --format sharegpt, then follow Unsloth Colab notebook")
    print("  → Ollama Modelfile   : use persona/system-prompt.md directly (no training needed)")
    print()


if __name__ == "__main__":
    main()
