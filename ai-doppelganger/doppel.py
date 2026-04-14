#!/usr/bin/env python3
"""
doppel.py — AI Doppelganger
============================
One script. Three commands.

  setup   Extract your Messenger history, build a system prompt from
          the data, and create a local Ollama model called "doppel".

  chat    Chat with your doppelganger interactively.

  batch   Run a set of test prompts and print all replies.

Usage:
    # Full setup — run this once
    python doppel.py setup \\
        --input  "/path/to/facebook-export/messages" \\
        --my-name "Your Facebook Name"

    # Then just run:
    ollama run doppel

    # Or chat from this script:
    python doppel.py chat
    python doppel.py batch

Requirements:
    - Python 3.8+
    - Ollama installed and running  https://ollama.com/download
    - A base model pulled, e.g.:  ollama pull llama3
    - No pip dependencies for setup. Chat uses urllib (stdlib).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import textwrap
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

__version__ = "1.0.0"

DATASET_DIR_NAME  = "doppel-dataset"
MODEL_NAME        = "doppel"
DEFAULT_BASE_MODEL = "llama3"
OLLAMA_HOST       = "http://localhost:11434"


# ---------------------------------------------------------------------------
# Ollama API (urllib only — no pip deps)
# ---------------------------------------------------------------------------

def ollama_request(path: str, payload: dict) -> dict:
    url  = f"{OLLAMA_HOST}{path}"
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(url, data=data,
                                  headers={"Content-Type": "application/json"},
                                  method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        raise ConnectionError(f"Cannot reach Ollama at {OLLAMA_HOST}: {e.reason}") from e


def ollama_chat(model: str, messages: list) -> str:
    result = ollama_request("/api/chat", {"model": model, "messages": messages, "stream": False})
    return result["message"]["content"]


def ollama_list_models() -> list[str]:
    req = urllib.request.Request(f"{OLLAMA_HOST}/api/tags", method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return [m["name"].split(":")[0] for m in data.get("models", [])]
    except urllib.error.URLError as e:
        raise ConnectionError(f"Cannot reach Ollama at {OLLAMA_HOST}: {e.reason}") from e


def check_ollama(required_model: str | None = None) -> None:
    try:
        models = ollama_list_models()
    except ConnectionError as e:
        print(f"\n[ERROR] {e}")
        print("  Make sure Ollama is running:  ollama serve")
        sys.exit(1)

    if required_model and required_model not in models:
        print(f"\n[ERROR] Model '{required_model}' not found in Ollama.")
        print(f"  Available: {', '.join(models) or 'none'}")
        print(f"  Pull it:   ollama pull {required_model}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# System prompt auto-generation
# ---------------------------------------------------------------------------

def auto_generate_system_prompt(dataset_dir: Path, my_name: str) -> str:
    summary_path  = dataset_dir / "global_summary.json"
    profiles_path = dataset_dir / "style_profiles.json"

    if not summary_path.exists() or not profiles_path.exists():
        print("[ERROR] Dataset files not found. Run setup first.", file=sys.stderr)
        sys.exit(1)

    summary  = json.loads(summary_path.read_text(encoding="utf-8"))
    profiles = json.loads(profiles_path.read_text(encoding="utf-8"))

    # --- Language distribution ---
    lang_dist = summary.get("language_distribution", {})
    total_msgs = sum(lang_dist.values()) or 1
    lang_pct: dict[str, int] = {
        k: round(100 * v / total_msgs) for k, v in lang_dist.items()
    }

    lang_label = {
        "greek":            "Greek",
        "english_or_latin": "English",
        "mixed":            "mixed Greek/English",
        "unknown":          "other",
    }
    lang_line = ", ".join(
        f"{pct}% {lang_label.get(lang, lang)}"
        for lang, pct in sorted(lang_pct.items(), key=lambda x: -x[1])
        if pct >= 5
    )

    primary_lang = max(lang_dist, key=lang_dist.get) if lang_dist else "english_or_latin"
    primary_label = lang_label.get(primary_lang, primary_lang)

    # --- Message length ---
    avg_words_list = [
        p["average_word_count"]
        for p in profiles.values()
        if isinstance(p.get("average_word_count"), (int, float))
    ]
    overall_avg = round(sum(avg_words_list) / len(avg_words_list)) if avg_words_list else 8

    if overall_avg < 6:
        length_rule = f"Very short messages — typically 1–5 words. Rarely more than one sentence."
    elif overall_avg < 14:
        length_rule = f"Short messages — typically under 15 words. One or two sentences at most."
    elif overall_avg < 30:
        length_rule = f"Medium-length messages — 2–4 sentences. Expand only when the topic requires it."
    else:
        length_rule = f"Longer messages — several sentences or short paragraphs when needed."

    # --- Verbal tics (top terms across all conversations) ---
    all_terms: Counter = Counter()
    for profile in profiles.values():
        for term, count in profile.get("top_terms", []):
            all_terms[term] += count

    tics = [t for t, _ in all_terms.most_common(20) if len(t) >= 3][:12]
    tics_line = (
        f"You frequently use words and expressions like: {', '.join(tics)}."
        if tics else ""
    )

    # --- Activity patterns ---
    time_totals: Counter = Counter()
    for profile in profiles.values():
        for bucket, count in profile.get("time_of_day", {}).items():
            time_totals[bucket] += count
    peak_time = time_totals.most_common(1)[0][0] if time_totals else None
    time_line = f"You tend to be most active in the {peak_time}." if peak_time else ""

    # --- Dataset span ---
    first = summary.get("first_message", "")[:10]
    last  = summary.get("last_message",  "")[:10]
    msg_count = summary.get("message_count", 0)

    prompt = f"""\
You are {my_name}. Respond exactly as {my_name} would — not as an assistant, as a person.

## Language
Your messages are {lang_line}.
Default to {primary_label}. Match the language of whoever is writing to you.
Code-switch naturally for technical terms.

## Message style
{length_rule}
Never pad. Never repeat what the other person said. Get to the point.

## Tone
Direct. Dry. Occasionally witty, never trying too hard.
Warm with close contacts, brief with everyone else.
{tics_line}
{time_line}

## Hard rules
- Never start with: "Certainly!", "Of course!", "Great question!", "I'd be happy to", "As an AI"
- Never explain your reasoning unless explicitly asked
- Never add a sign-off or signature
- Do not use emojis unless the other person used them first
- Do not over-elaborate — if one sentence answers it, use one sentence

## Context
This persona is derived from {msg_count:,} real messages sent between {first} and {last}.\
"""
    return prompt.strip()


# ---------------------------------------------------------------------------
# Setup command
# ---------------------------------------------------------------------------

def cmd_setup(args: argparse.Namespace) -> None:
    script_dir  = Path(__file__).parent.resolve()
    extractor   = script_dir / "extract_messenger_personality.py"
    dataset_dir = Path(args.output).resolve()

    if not extractor.exists():
        print(f"[ERROR] extract_messenger_personality.py not found in {script_dir}", file=sys.stderr)
        sys.exit(1)

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"[ERROR] Facebook export folder not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Check Ollama + base model before doing any work
    print(f"\ndoppel v{__version__} — setup\n")
    print("  Checking Ollama…")
    check_ollama(args.base_model)
    print(f"  Ollama OK  (base model: {args.base_model})")

    # Step 1 — Extract
    print(f"\n  Step 1/4  Extracting messages from Facebook export…")
    result = subprocess.run(
        [sys.executable, str(extractor),
         "--input",   str(input_path),
         "--output",  str(dataset_dir),
         "--my-name", args.my_name]
        + (["--include-group-chats"] if args.include_groups else []),
        check=False,
    )
    if result.returncode != 0:
        print("\n[ERROR] Extraction failed. See output above.", file=sys.stderr)
        sys.exit(1)

    # Step 2 — Generate system prompt
    print("  Step 2/4  Generating system prompt from your data…")
    system_prompt = auto_generate_system_prompt(dataset_dir, args.my_name)
    prompt_path   = dataset_dir / "system-prompt.txt"
    prompt_path.write_text(system_prompt, encoding="utf-8")
    print(f"  Saved: {prompt_path}")

    # Step 3 — Write Modelfile
    print("  Step 3/4  Writing Ollama Modelfile…")
    modelfile_path = dataset_dir / "Modelfile"
    modelfile_content = textwrap.dedent(f"""\
        FROM {args.base_model}
        SYSTEM \"\"\"{system_prompt}\"\"\"
        PARAMETER temperature {args.temperature}
        PARAMETER top_p 0.9
        PARAMETER repeat_penalty 1.1
    """)
    modelfile_path.write_text(modelfile_content, encoding="utf-8")
    print(f"  Saved: {modelfile_path}")

    # Step 4 — Create Ollama model
    print(f"  Step 4/4  Creating Ollama model '{MODEL_NAME}'…")
    result = subprocess.run(
        ["ollama", "create", MODEL_NAME, "-f", str(modelfile_path)],
        check=False,
    )
    if result.returncode != 0:
        print(f"\n[ERROR] ollama create failed.", file=sys.stderr)
        print(f"  You can retry manually:", file=sys.stderr)
        print(f"    ollama create {MODEL_NAME} -f {modelfile_path}", file=sys.stderr)
        sys.exit(1)

    print(f"""
  ✓ Done.

  Your doppelganger is ready:

      ollama run {MODEL_NAME}

  To adjust the persona, edit:
      {prompt_path}
  then re-run:
      ollama create {MODEL_NAME} -f {modelfile_path}
""")


# ---------------------------------------------------------------------------
# Chat command
# ---------------------------------------------------------------------------

def cmd_chat(args: argparse.Namespace) -> None:
    check_ollama(args.model)

    print(f"\n  Model: {args.model}")
    print("  Type 'exit' or Ctrl+C to quit. Type 'reset' to clear history.\n")
    print("─" * 50)

    history: list[dict] = []

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            break
        if user_input.lower() == "reset":
            history = []
            print("  [conversation reset]")
            continue

        history.append({"role": "user", "content": user_input})

        try:
            reply = ollama_chat(args.model, history)
        except Exception as e:
            print(f"[ERROR] {e}")
            history.pop()
            continue

        history.append({"role": "assistant", "content": reply})
        print(f"\n{args.model}: {reply}")


# ---------------------------------------------------------------------------
# Batch command
# ---------------------------------------------------------------------------

DEFAULT_PROMPTS = [
    "Hey, how are you?",
    "What are you up to today?",
    "Long time no talk!",
    "What do you think about AI?",
    "Can you help me with something?",
    "Tell me something interesting.",
]


def cmd_batch(args: argparse.Namespace) -> None:
    check_ollama(args.model)

    prompts = DEFAULT_PROMPTS
    if args.prompts_file:
        pf = Path(args.prompts_file).resolve()
        if not pf.exists():
            print(f"[ERROR] Prompts file not found: {pf}", file=sys.stderr)
            sys.exit(1)
        prompts = [l.strip() for l in pf.read_text(encoding="utf-8").splitlines() if l.strip()]

    print(f"\n  Model: {args.model}   Prompts: {len(prompts)}\n")
    print("─" * 50)

    passed = 0
    for i, prompt in enumerate(prompts, 1):
        print(f"\n[{i}/{len(prompts)}] You: {prompt}")
        try:
            reply = ollama_chat(args.model, [{"role": "user", "content": prompt}])
            print(f"       {args.model}: {reply}")
            passed += 1
        except Exception as e:
            print(f"       [ERROR] {e}")

    print(f"\n  {passed}/{len(prompts)} prompts answered.\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="doppel.py",
        description="Build and chat with an AI doppelganger via Ollama.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    # setup
    s = sub.add_parser("setup", help="Extract messages and create the Ollama model")
    s.add_argument("--input",          required=True, help="Root folder of Facebook export")
    s.add_argument("--my-name",        required=True, help="Your exact Facebook sender name")
    s.add_argument("--output",         default=DATASET_DIR_NAME,
                                       help=f"Dataset output folder (default: {DATASET_DIR_NAME})")
    s.add_argument("--base-model",     default=DEFAULT_BASE_MODEL,
                                       help=f"Ollama base model to use (default: {DEFAULT_BASE_MODEL})")
    s.add_argument("--temperature",    type=float, default=0.8,
                                       help="Model temperature (default: 0.8)")
    s.add_argument("--include-groups", action="store_true",
                                       help="Include group chats (default: 1-on-1 only)")

    # chat
    c = sub.add_parser("chat", help="Chat with your doppelganger interactively")
    c.add_argument("--model", default=MODEL_NAME, help=f"Ollama model name (default: {MODEL_NAME})")

    # batch
    b = sub.add_parser("batch", help="Run batch test prompts")
    b.add_argument("--model",        default=MODEL_NAME, help=f"Ollama model name (default: {MODEL_NAME})")
    b.add_argument("--prompts-file", default=None,       help="Text file with one prompt per line")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "setup":
        cmd_setup(args)
    elif args.command == "chat":
        cmd_chat(args)
    elif args.command == "batch":
        cmd_batch(args)


if __name__ == "__main__":
    main()
