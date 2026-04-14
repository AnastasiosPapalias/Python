#!/usr/bin/env python3
"""
test_doppelganger.py
=====================
Interactive chat with your AI doppelganger running locally via Ollama.

Usage:
    python test_doppelganger.py --model my-doppelganger

    # Or test against a system-prompt-only model (no fine-tuning needed):
    python test_doppelganger.py --model llama3 --system-prompt ./my-system-prompt.md

    # Run a batch of predefined test prompts instead of interactive mode:
    python test_doppelganger.py --model my-doppelganger --batch

Requirements:
    pip install ollama
    Ollama must be running: ollama serve
"""

import argparse
import sys
from pathlib import Path

try:
    from ollama import Client
except ImportError:
    print("[ERROR] ollama package not found. Install it with: pip install ollama")
    sys.exit(1)


DEFAULT_BATCH_PROMPTS = [
    "Hey, how are you?",
    "What are you up to today?",
    "Can you help me with something?",
    "Long time no talk!",
    "What do you think about AI?",
    "Tell me something interesting.",
]


def load_system_prompt(path: str) -> str:
    p = Path(path)
    if not p.exists():
        print(f"[ERROR] System prompt file not found: {path}", file=sys.stderr)
        sys.exit(1)

    text = p.read_text(encoding="utf-8")

    # If it's a template .md file with fenced code blocks, extract the first block
    import re
    blocks = re.findall(r"```\n(.*?)```", text, re.DOTALL)
    if blocks:
        return blocks[0].strip()
    return text.strip()


def chat(client: Client, model: str, history: list, system_prompt: str) -> str:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(history)

    response = client.chat(model=model, messages=messages)
    return response["message"]["content"]


def run_interactive(client: Client, model: str, system_prompt: str) -> None:
    print(f"\n  Model   : {model}")
    if system_prompt:
        print(f"  Prompt  : {len(system_prompt)} chars")
    print("  Type 'exit' or Ctrl+C to quit.")
    print("  Type 'reset' to clear conversation history.\n")
    print("─" * 50)

    history = []

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye.")
            break

        if not user_input:
            continue
        if user_input.lower() == "exit":
            break
        if user_input.lower() == "reset":
            history = []
            print("  [conversation reset]")
            continue

        history.append({"role": "user", "content": user_input})

        try:
            reply = chat(client, model, history, system_prompt)
        except Exception as e:
            print(f"[ERROR] {e}")
            history.pop()
            continue

        history.append({"role": "assistant", "content": reply})
        print(f"\nDoppelganger: {reply}")


def run_batch(client: Client, model: str, system_prompt: str, prompts: list) -> None:
    print(f"\n  Model   : {model}")
    print(f"  Prompts : {len(prompts)}\n")
    print("─" * 50)

    passed = 0
    for i, prompt in enumerate(prompts, 1):
        print(f"\n[{i}/{len(prompts)}] You: {prompt}")
        try:
            reply = chat(client, model, [{"role": "user", "content": prompt}], system_prompt)
            print(f"        Doppelganger: {reply}")
            passed += 1
        except Exception as e:
            print(f"        [ERROR] {e}")

    print("\n" + "─" * 50)
    print(f"  Completed: {passed}/{len(prompts)} prompts answered\n")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Test your AI doppelganger via Ollama.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--model",         required=True, help="Ollama model name (e.g. my-doppelganger)")
    p.add_argument("--system-prompt", default=None,  help="Path to system prompt file (.md or .txt)")
    p.add_argument("--host",          default="http://localhost:11434", help="Ollama host (default: localhost:11434)")
    p.add_argument("--batch",         action="store_true", help="Run predefined batch prompts instead of interactive chat")
    p.add_argument("--prompts-file",  default=None, help="Path to a text file with one prompt per line (used with --batch)")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    client = Client(host=args.host)

    # Verify Ollama is running and model exists
    try:
        models = [m["name"] for m in client.list()["models"]]
    except Exception as e:
        print(f"[ERROR] Cannot connect to Ollama at {args.host}")
        print(f"  Make sure Ollama is running: ollama serve")
        print(f"  Details: {e}")
        sys.exit(1)

    # Normalize model name for comparison (strip :latest tag for display)
    model_names_normalized = [m.split(":")[0] for m in models]
    if args.model not in models and args.model not in model_names_normalized:
        print(f"[ERROR] Model '{args.model}' not found in Ollama.")
        print(f"  Available models: {', '.join(models) or 'none'}")
        print(f"  Pull it with: ollama pull {args.model}")
        print(f"  Or create it from a Modelfile: ollama create {args.model} -f Modelfile")
        sys.exit(1)

    system_prompt = ""
    if args.system_prompt:
        system_prompt = load_system_prompt(args.system_prompt)

    if args.batch:
        prompts = DEFAULT_BATCH_PROMPTS
        if args.prompts_file:
            pf = Path(args.prompts_file)
            if not pf.exists():
                print(f"[ERROR] Prompts file not found: {args.prompts_file}", file=sys.stderr)
                sys.exit(1)
            prompts = [l.strip() for l in pf.read_text(encoding="utf-8").splitlines() if l.strip()]
        run_batch(client, args.model, system_prompt, prompts)
    else:
        run_interactive(client, args.model, system_prompt)


if __name__ == "__main__":
    main()
