#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ███████╗  ██████╗  ██╗  ██╗  ██████╗  ██╗       █████╗  ██████╗          ║
║  ██╔════╝ ██╔════╝  ██║  ██║ ██╔═══██╗ ██║      ██╔══██╗ ██╔══██╗         ║
║  ███████╗ ██║       ███████║ ██║   ██║ ██║      ███████║ ██████╔╝          ║
║  ╚════██║ ██║       ██╔══██║ ██║   ██║ ██║      ██╔══██║ ██╔══██╗          ║
║  ███████║ ╚██████╗  ██║  ██║ ╚██████╔╝ ███████╗ ██║  ██║ ██║  ██║          ║
║  ╚══════╝  ╚═════╝  ╚═╝  ╚═╝  ╚═════╝  ╚══════╝ ╚═╝  ╚═╝ ╚═╝  ╚═╝          ║
║                                                                              ║
║       ███████╗  ██████╗  ██████╗   ██████╗  ███████╗                       ║
║       ██╔════╝ ██╔═══██╗ ██╔══██╗ ██╔════╝  ██╔════╝                       ║
║       █████╗   ██║   ██║ ██████╔╝ ██║  ███╗ █████╗                         ║
║       ██╔══╝   ██║   ██║ ██╔══██╗ ██║   ██║ ██╔══╝                         ║
║       ██║      ╚██████╔╝ ██║  ██║ ╚██████╔╝ ███████╗                       ║
║       ╚═╝       ╚═════╝  ╚═╝  ╚═╝  ╚═════╝  ╚══════╝                       ║
║                                                                              ║
║   Academic Research & Knowledge Pipeline  ·  v3.3.0                        ║
║   https://github.com/AnastasiosPapalias/scholarforge                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Scholar Forge — The definitive academic research pipeline tool.

Two powerful modes in one unified CLI:

  HARVEST   Search 20 academic APIs, score relevance, download open-access
            documents (PDF/EPUB/HTML/TXT) into an organized local library.

  FORGE     Scan a folder of documents, extract full text, chunk intelligently,
            and export a structured knowledge dataset ready for AI-assisted
            book writing or LLM ingestion.

  PIPELINE  Run both stages back-to-back: harvest → forge in one command.

Sources (Harvest):
  OpenAlex · Crossref · Semantic Scholar · OA.mg · CORE · DOAJ · Paperity
  arXiv · SSRN · PubMed · PMC Full-Text · Europe PMC · Zenodo · Figshare
  HAL · OpenAIRE · Google Books · Internet Archive · Open Library · EThOS/DART

Formats (Forge):
  PDF · DOCX · TXT · Markdown · HTML · XML · JSON · CSV · TSV · RTF · YAML · TeX

Requirements:
  Python 3.8+  (zero mandatory third-party deps)
  pip install pypdf python-docx   (optional, greatly improves PDF/DOCX extraction)

Usage:
  python scholarforge.py harvest
  python scholarforge.py forge /path/to/documents
  python scholarforge.py pipeline
  python scholarforge.py --help

Author: Anastasios Papalias
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# Standard Library Imports
# ─────────────────────────────────────────────────────────────────────────────

import argparse
import csv
import hashlib
import html
import json
import math
import mimetypes
import os
import re
import shutil
import sys
import time
import threading
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from textwrap import wrap
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union
from xml.etree import ElementTree as ET

# ─────────────────────────────────────────────────────────────────────────────
# Optional third-party imports
# ─────────────────────────────────────────────────────────────────────────────

try:
    from pypdf import PdfReader as _PdfReader  # type: ignore
    HAS_PYPDF = True
except Exception:
    _PdfReader = None
    HAS_PYPDF = False

try:
    import docx as _docx  # type: ignore
    HAS_DOCX = True
except Exception:
    _docx = None
    HAS_DOCX = False

# ─────────────────────────────────────────────────────────────────────────────
# Global API keys (loaded once at import time)
# ─────────────────────────────────────────────────────────────────────────────

try:
    from scholarforge.config.global_config import get_api_keys as _get_api_keys
    _API_KEYS = _get_api_keys()
except Exception:
    from types import SimpleNamespace
    _API_KEYS = SimpleNamespace(  # type: ignore[assignment]
        core_api_key="",
        semantic_scholar_key="",
        elsevier_api_key="",
        wiley_api_key="",
    )

# ─────────────────────────────────────────────────────────────────────────────
# Terminal / colour helpers
# ─────────────────────────────────────────────────────────────────────────────

_TERM_WIDTH = shutil.get_terminal_size((100, 24)).columns

def _supports_color() -> bool:
    """Detect if the terminal supports ANSI color codes."""
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except Exception:
            return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

_COLOR = _supports_color()

class C:
    """ANSI color codes — gracefully degrades when color is unavailable."""
    RESET   = "\033[0m"   if _COLOR else ""
    BOLD    = "\033[1m"   if _COLOR else ""
    DIM     = "\033[2m"   if _COLOR else ""
    ITALIC  = "\033[3m"   if _COLOR else ""
    UNDER   = "\033[4m"   if _COLOR else ""
    # Regular
    BLACK   = "\033[30m"  if _COLOR else ""
    RED     = "\033[31m"  if _COLOR else ""
    GREEN   = "\033[32m"  if _COLOR else ""
    YELLOW  = "\033[33m"  if _COLOR else ""
    BLUE    = "\033[34m"  if _COLOR else ""
    MAGENTA = "\033[35m"  if _COLOR else ""
    CYAN    = "\033[36m"  if _COLOR else ""
    WHITE   = "\033[37m"  if _COLOR else ""
    # Bright
    BRIGHT_BLACK   = "\033[90m"  if _COLOR else ""
    BRIGHT_RED     = "\033[91m"  if _COLOR else ""
    BRIGHT_GREEN   = "\033[92m"  if _COLOR else ""
    BRIGHT_YELLOW  = "\033[93m"  if _COLOR else ""
    BRIGHT_BLUE    = "\033[94m"  if _COLOR else ""
    BRIGHT_MAGENTA = "\033[95m"  if _COLOR else ""
    BRIGHT_CYAN    = "\033[96m"  if _COLOR else ""
    BRIGHT_WHITE   = "\033[97m"  if _COLOR else ""


def _c(text: str, *codes: str) -> str:
    if not codes:
        return text
    return "".join(codes) + text + C.RESET


def _rule(char: str = "─", color: str = C.DIM) -> str:
    return _c(char * _TERM_WIDTH, color)


def _box_line(text: str, width: int, left: str = "│", right: str = "│",
              pad: int = 2, text_color: str = "", border_color: str = C.CYAN) -> str:
    inner_width = width - 2 * pad - 2  # 2 for border chars
    text_display = text[:inner_width]
    padded = text_display.ljust(inner_width)
    colored_text = _c(padded, text_color) if text_color else padded
    return _c(left, border_color) + " " * pad + colored_text + " " * pad + _c(right, border_color)


# ─────────────────────────────────────────────────────────────────────────────
# UI Primitives
# ─────────────────────────────────────────────────────────────────────────────

def print_banner() -> None:
    """Print the application header banner.

    Stage 5: delegates to the calm scholarly wordmark in `scholarforge.tui.banner`.
    The old 16-line ASCII-block header is retired; version is now read from the
    package `__version__` rather than hardcoded.
    """
    from scholarforge.tui.banner import print_banner as _print_scholarly_banner
    _print_scholarly_banner(width=_TERM_WIDTH)


def print_section(title: str, icon: str = "◆") -> None:
    print()
    print(_c(f" {icon} {title} ", C.BOLD, C.BRIGHT_CYAN))
    print(_c("  " + "─" * (len(title) + 4), C.DIM))


def print_step(label: str, value: str = "", status: str = "info") -> None:
    icons = {"info": "·", "ok": "✓", "warn": "!", "error": "✗", "dl": "↓", "skip": "○", "search": "⌕"}
    colors = {
        "info": C.DIM, "ok": C.BRIGHT_GREEN, "warn": C.BRIGHT_YELLOW,
        "error": C.BRIGHT_RED, "dl": C.BRIGHT_CYAN, "skip": C.DIM, "search": C.BRIGHT_BLUE
    }
    icon = icons.get(status, "·")
    color = colors.get(status, C.DIM)
    icon_str = _c(f"  {icon}", color)
    label_str = _c(f" {label}", C.WHITE if status != "info" else C.DIM)
    val_str = _c(f"  {value}", C.BRIGHT_WHITE) if value else ""
    print(f"{icon_str}{label_str}{val_str}")


def print_kv(key: str, value: Any, indent: int = 4, key_color: str = C.CYAN) -> None:
    k = _c(str(key).rjust(indent + len(str(key))), key_color)
    print(f"{k}  {_c(str(value), C.WHITE)}")


def print_table(headers: List[str], rows: List[List[str]], col_widths: Optional[List[int]] = None) -> None:
    """Render a clean ASCII table."""
    if not rows:
        return
    if col_widths is None:
        col_widths = [max(len(str(h)), max(len(str(r[i])) for r in rows)) + 2
                      for i, h in enumerate(headers)]

    def fmt_row(cells: List[str], widths: List[int], color: str = "") -> str:
        parts = []
        for cell, w in zip(cells, widths):
            s = str(cell)[:w - 2]
            parts.append(_c(s.ljust(w), color) if color else s.ljust(w))
        return "  " + _c("│", C.DIM) + f" {_c('│', C.DIM)} ".join(parts) + _c(" │", C.DIM)

    header_sep = "  ├" + "┼".join("─" * w for w in col_widths) + "┤"
    top_sep    = "  ┌" + "┬".join("─" * w for w in col_widths) + "┐"
    bot_sep    = "  └" + "┴".join("─" * w for w in col_widths) + "┘"

    print(_c(top_sep, C.DIM))
    print(fmt_row(headers, col_widths, C.BRIGHT_CYAN))
    print(_c(header_sep, C.DIM))
    for row in rows:
        print(fmt_row(row, col_widths))
    print(_c(bot_sep, C.DIM))


class Spinner:
    """Non-blocking terminal spinner for long async tasks."""
    _FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message: str = "Working...") -> None:
        self._message = message
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> "Spinner":
        self._stop.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        return self

    def _spin(self) -> None:
        i = 0
        while not self._stop.is_set():
            frame = self._FRAMES[i % len(self._FRAMES)]
            sys.stdout.write(f"\r  {_c(frame, C.BRIGHT_CYAN)} {_c(self._message, C.DIM)}  ")
            sys.stdout.flush()
            time.sleep(0.08)
            i += 1

    def stop(self, final: str = "") -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=0.5)
        sys.stdout.write(f"\r{' ' * (_TERM_WIDTH - 1)}\r")
        if final:
            sys.stdout.write(final + "\n")
        sys.stdout.flush()


class ProgressBar:
    """Determinate progress bar with ETA."""
    def __init__(self, total: int, label: str = "", width: int = 40) -> None:
        self.total = max(1, total)
        self.label = label
        self.width = width
        self.current = 0
        self._start = time.monotonic()

    def update(self, n: int = 1) -> None:
        self.current = min(self.current + n, self.total)
        self._render()

    def set(self, n: int) -> None:
        self.current = min(n, self.total)
        self._render()

    def _render(self) -> None:
        elapsed = time.monotonic() - self._start
        frac = self.current / self.total
        filled = int(self.width * frac)
        bar = _c("█" * filled, C.BRIGHT_CYAN) + _c("░" * (self.width - filled), C.DIM)
        pct = f"{frac * 100:5.1f}%"
        if frac > 0 and elapsed > 0.5:
            eta_s = (elapsed / frac) - elapsed
            eta = f"ETA {int(eta_s)}s" if eta_s > 0 else "done"
        else:
            eta = "..."
        label_part = f" {_c(self.label, C.DIM)}" if self.label else ""
        line = f"\r  [{bar}] {_c(pct, C.BRIGHT_WHITE)} {_c(eta, C.DIM)}{label_part}  "
        sys.stdout.write(line)
        sys.stdout.flush()

    def finish(self, msg: str = "") -> None:
        self.set(self.total)
        bar = _c("█" * self.width, C.BRIGHT_GREEN)
        elapsed = time.monotonic() - self._start
        line = f"\r  [{bar}] {_c('100.0%', C.BRIGHT_GREEN)} {_c(f'{elapsed:.1f}s', C.DIM)}"
        if msg:
            line += f"  {_c(msg, C.BRIGHT_GREEN)}"
        sys.stdout.write(line + "\n")
        sys.stdout.flush()


def prompt_choice(question: str, choices: List[str], default: Optional[str] = None) -> str:
    """Interactive single-choice prompt with validation."""
    choices_lower = [c.lower() for c in choices]
    display = "/".join(_c(c.upper() if c == default else c, C.BRIGHT_CYAN) if c == default else c for c in choices)
    while True:
        print()
        ans = input(f"  {_c('?', C.BRIGHT_YELLOW)} {question} [{display}]: ").strip().lower()
        if not ans and default:
            return default
        if ans in choices_lower:
            return choices_lower[choices_lower.index(ans)]
        print(f"  {_c('✗', C.RED)} Please choose one of: {', '.join(choices)}")


def prompt_text(question: str, default: str = "", validator: Optional[Callable[[str], bool]] = None,
                hint: str = "") -> str:
    """Interactive text input with optional default and validator."""
    default_hint = f" [{_c(default, C.DIM)}]" if default else ""
    hint_str = f"  {_c('  ' + hint, C.DIM)}\n" if hint else ""
    while True:
        print()
        if hint_str:
            print(hint_str, end="")
        ans = input(f"  {_c('?', C.BRIGHT_YELLOW)} {question}{default_hint}: ").strip()
        if not ans:
            if default:
                return default
            if validator is None:
                continue
        if validator is None or validator(ans):
            return ans
        print(f"  {_c('✗', C.RED)} Invalid input. {hint}")


def prompt_int(question: str, default: int, min_val: int = 1, max_val: int = 10_000) -> int:
    while True:
        raw = prompt_text(question, str(default))
        try:
            v = int(raw)
            if min_val <= v <= max_val:
                return v
            print(f"  {_c('✗', C.RED)} Must be between {min_val} and {max_val}.")
        except ValueError:
            print(f"  {_c('✗', C.RED)} Please enter a number.")


def prompt_float(question: str, default: float) -> float:
    while True:
        raw = prompt_text(question, str(default))
        try:
            return float(raw)
        except ValueError:
            print(f"  {_c('✗', C.RED)} Please enter a number.")


def confirm(question: str, default: bool = True) -> bool:
    opts = ["Y", "n"] if default else ["y", "N"]
    ans = prompt_choice(question, ["y", "n"], "y" if default else "n")
    return ans == "y"


def print_summary_box(title: str, items: Dict[str, Any], width: int = 60) -> None:
    """Print a structured summary box. Values that overflow are wrapped onto continuation lines."""
    # Auto-size to terminal but leave breathing room
    w = min(max(width, 50), _TERM_WIDTH - 6)
    inner_w = w - 2  # space between the two │ chars

    border   = _c("│", C.CYAN)
    pad_side = 2  # spaces on each side of content

    def box_line_raw(content_raw: str, content_colored: str) -> None:
        """Print one │-bordered line. content_raw is stripped of ANSI for length calc."""
        used    = len(content_raw)
        padding = max(0, inner_w - used)
        print("  " + border + content_colored + " " * padding + border)

    print()
    print("  " + _c("┌" + "─" * inner_w + "┐", C.CYAN))
    # Title row
    title_lpad = (inner_w - len(title)) // 2
    title_rpad = inner_w - title_lpad - len(title)
    print("  " + border + " " * title_lpad + _c(title, C.BOLD, C.BRIGHT_WHITE) + " " * title_rpad + border)
    print("  " + _c("├" + "─" * inner_w + "┤", C.CYAN))

    key_col = 16   # fixed key column width (truncated if needed)
    val_col = inner_w - key_col - pad_side * 2 - 2   # remaining space for value

    for key, val in items.items():
        key_str = str(key)
        val_str = str(val)

        # Truncate key if necessary
        key_display = key_str[:key_col].ljust(key_col)

        # Wrap value across multiple lines if it exceeds val_col
        if len(val_str) <= val_col:
            val_lines = [val_str]
        else:
            # First try word-wrapping on spaces
            val_lines = []
            words = val_str.split(" ")
            current = ""
            for word in words:
                if current and len(current) + 1 + len(word) > val_col:
                    val_lines.append(current)
                    current = word
                else:
                    current = (current + " " + word).strip() if current else word
            if current:
                val_lines.append(current)
            # If a single word is still too long (e.g. a path), hard-wrap it
            final_lines: List[str] = []
            for line in val_lines:
                while len(line) > val_col:
                    final_lines.append(line[:val_col])
                    line = line[val_col:]
                if line:
                    final_lines.append(line)
            val_lines = final_lines

        # First line: key + first value line
        first_val = val_lines[0]
        content_raw = " " * pad_side + key_display + "  " + first_val
        content_col = " " * pad_side + _c(key_display, C.CYAN) + "  " + _c(first_val, C.BRIGHT_WHITE)
        box_line_raw(content_raw, content_col)

        # Continuation lines (value only, indented to align under value column)
        indent = " " * (pad_side + key_col + 2)
        for extra_line in val_lines[1:]:
            content_raw = indent + extra_line
            content_col = indent + _c(extra_line, C.BRIGHT_WHITE)
            box_line_raw(content_raw, content_col)

    print("  " + _c("└" + "─" * inner_w + "┘", C.CYAN))


def print_dependency_status() -> None:
    """Print the status of optional dependencies."""
    print_section("Dependency Check", "⚙")
    items = [
        ("pypdf", HAS_PYPDF, "pip install pypdf", "PDF extraction"),
        ("python-docx", HAS_DOCX, "pip install python-docx", "DOCX extraction"),
    ]
    for name, available, install_cmd, purpose in items:
        if available:
            print_step(f"{name}  ({purpose})", "installed", "ok")
        else:
            print_step(f"{name}  ({purpose})", f"missing → {_c(install_cmd, C.DIM)}", "warn")


# ─────────────────────────────────────────────────────────────────────────────
# Inline contextual help system
# ─────────────────────────────────────────────────────────────────────────────

FIELD_HELP: Dict[str, Dict[str, str]] = {
    "study_type": {
        "title": "Study Type",
        "what":  "Selects which academic sources to query and how to filter results.",
        "book":  "Searches Google Books, Open Library, Internet Archive, OpenAlex, Crossref, Semantic Scholar. "
                 "Filters out audio/video records. Best for humanities, history, philosophy, literature.",
        "paper": "All book sources PLUS PubMed/PMC. Prioritises journal articles. "
                 "Best for science, medicine, engineering, social sciences.",
        "tip":   "You can mix both in a pipeline run — use 'book' to cast a wider net.",
    },
    "subjects": {
        "title": "Subjects / Topics",
        "what":  "A comma-separated list of search terms. Each subject is searched in two ways:\n"
                 "  1. Exact phrase  (\"quantum entanglement\")  → high precision\n"
                 "  2. Broad keyword (quantum entanglement)    → wider recall",
        "examples": [
            "quantum mechanics, wave-particle duality, Schrödinger equation",
            "cognitive neuroscience, working memory, prefrontal cortex",
            "Byzantine music, neumes, ison, modal theory",
            "machine learning, transformer architecture, attention mechanism",
        ],
        "tip":   "More subjects = more queries = more results, but also more API time. "
                 "3–6 focused subjects is the sweet spot for a book research session.",
    },
    "max_results": {
        "title": "Max Raw Results per Source per Query",
        "what":  "How many candidate records each API returns for each (subject × query_mode) combination.\n"
                 "With 3 subjects and 7 sources → up to 3 × 2 × 7 × N total raw records before filtering.",
        "range": "5 – 200. Default: 25.",
        "tradeoffs": [
            "N=10   Fast (~30 s). Good for a quick scan or topic exploration.",
            "N=25   Balanced (default). 1–2 minutes. Good for most book projects.",
            "N=50   Thorough (~4 min). Recommended for systematic literature reviews.",
            "N=200  Exhaustive (~15 min). Use for academic papers needing completeness.",
        ],
        "tip":   "Raw results are filtered by relevance score afterward, so a higher N "
                 "doesn't necessarily mean more downloads — just more candidates to evaluate.",
    },
    "min_score": {
        "title": "Minimum Relevance Score",
        "what":  "ScholarForge scores every record 0–∞ by matching your subjects against its title and abstract.\n"
                 "Only records with score ≥ this threshold are kept.",
        "scoring": [
            "+20 pts  Exact subject phrase found in title",
            "+11 pts  Exact subject phrase found in abstract",
            "+4.5 pts Per subject token found in title",
            "+1.5 pts Per subject token found in abstract",
            "-32 pts  Noisy/unrelated domain term found in title",
            "Bonus    Citation count (Semantic Scholar / OpenAlex)",
        ],
        "presets": [
            "Score  5   Very permissive — includes loosely related records",
            "Score 10   Balanced (default for books). Requires meaningful overlap.",
            "Score 12   Stricter (default for papers). Recommended for focused topics.",
            "Score 20+  Very tight — only highly relevant records pass through.",
        ],
        "tip":   "If you get too few results, lower the score. "
                 "If results are noisy, raise it. You can re-run with different values.",
    },
    "max_downloads": {
        "title": "Max Documents to Download",
        "what":  "After filtering by score, ScholarForge tries to download the actual files "
                 "(PDF, EPUB, HTML, TXT) for open-access records. This cap limits how many files are saved.",
        "details": [
            "Only open-access URLs are attempted — paywalled papers are never downloaded.",
            "Duplicates (same URL) are automatically skipped.",
            "Each download waits ~1 second between requests to be polite to servers.",
            "Set to 0 to disable downloading entirely (metadata-only run).",
        ],
        "tip":   "100 is a sensible default. For a focused book project, 50–200 is typical. "
                 "Use --no-download if you only want metadata (JSONL/CSV) without files.",
    },
    "chunk_size": {
        "title": "Characters per Chunk (Forge)",
        "what":  "Forge splits each document into overlapping text chunks for LLM/AI ingestion. "
                 "This controls how large each chunk is in characters.",
        "presets": [
            "1000–2000   Short. Good for Q&A and retrieval. Many chunks per page.",
            "3500        Default. Balanced for GPT-4 / Claude context windows.",
            "4000–6000   Longer context. Fewer chunks, more coherent passages.",
            "8000+       Very long. Use only with models that support large context.",
        ],
        "tip":   "1 page of text ≈ 2000–3000 characters. The default (3500) is roughly 1–1.5 pages per chunk.",
    },
    "overlap": {
        "title": "Chunk Overlap (Forge)",
        "what":  "How many characters from the end of one chunk are repeated at the start of the next. "
                 "Prevents important sentences from being split across chunk boundaries.",
        "range": "0 – chunk_size/2. Default: 350 (~10% of 3500).",
        "tip":   "A 10% overlap is standard. Too little and context is lost at boundaries; "
                 "too much and your dataset grows unnecessarily.",
    },
}


def print_field_help(field_key: str) -> None:
    """Print detailed contextual help for a specific field."""
    info = FIELD_HELP.get(field_key)
    if not info:
        print(_c("  No help available for this field.", C.DIM))
        return

    w = min(76, _TERM_WIDTH - 4)
    print()
    print("  " + _c("╔" + "═" * (w - 2) + "╗", C.BRIGHT_CYAN))
    # Title
    title = f"  Help: {info['title']}  "
    t_pad = (w - 2 - len(title)) // 2
    print("  " + _c("║", C.BRIGHT_CYAN) + " " * t_pad + _c(title, C.BOLD, C.BRIGHT_WHITE) + " " * (w - 2 - t_pad - len(title)) + _c("║", C.BRIGHT_CYAN))
    print("  " + _c("╠" + "═" * (w - 2) + "╣", C.BRIGHT_CYAN))

    def help_line(text: str, indent: int = 0, color: str = C.WHITE) -> None:
        prefix = "  " + " " * indent
        available = w - 2 - indent
        # word-wrap
        words = text.split(" ")
        line  = ""
        for word in words:
            if line and len(line) + 1 + len(word) > available:
                padded = (prefix + _c(line, color)).ljust(w - 2)
                pad = max(0, w - 2 - indent - len(line))
                print("  " + _c("║", C.BRIGHT_CYAN) + prefix[2:] + _c(line, color) + " " * pad + _c("║", C.BRIGHT_CYAN))
                line = word
            else:
                line = (line + " " + word).strip() if line else word
        if line:
            pad = max(0, w - 2 - indent - len(line))
            print("  " + _c("║", C.BRIGHT_CYAN) + prefix[2:] + _c(line, color) + " " * pad + _c("║", C.BRIGHT_CYAN))

    def blank_line() -> None:
        print("  " + _c("║", C.BRIGHT_CYAN) + " " * (w - 2) + _c("║", C.BRIGHT_CYAN))

    def section_header(label: str) -> None:
        pad = w - 2 - len(label) - 1
        print("  " + _c("║", C.BRIGHT_CYAN) + " " + _c(label, C.BRIGHT_YELLOW) + " " * pad + _c("║", C.BRIGHT_CYAN))

    blank_line()
    # What
    for line in info.get("what", "").split("\n"):
        help_line(line.strip(), indent=2, color=C.WHITE)
    blank_line()

    # Examples
    if "examples" in info:
        section_header("Examples:")
        for ex in info["examples"]:
            help_line("· " + ex, indent=4, color=C.DIM)
        blank_line()

    # Book / paper specific
    if "book" in info:
        section_header("book:")
        help_line(info["book"], indent=4, color=C.DIM)
        blank_line()
    if "paper" in info:
        section_header("paper:")
        help_line(info["paper"], indent=4, color=C.DIM)
        blank_line()

    # Range
    if "range" in info:
        section_header("Range:")
        help_line(info["range"], indent=4, color=C.DIM)
        blank_line()

    # Tradeoffs / presets / scoring / details
    for section_key, section_label in [
        ("tradeoffs", "Trade-offs:"), ("presets", "Presets:"),
        ("scoring", "Scoring breakdown:"), ("details", "Details:"),
    ]:
        if section_key in info:
            section_header(section_label)
            for item in info[section_key]:
                help_line("· " + item, indent=4, color=C.DIM)
            blank_line()

    # Tip
    if "tip" in info:
        section_header("Tip:")
        help_line(info["tip"], indent=4, color=C.BRIGHT_GREEN)
        blank_line()

    print("  " + _c("╚" + "═" * (w - 2) + "╝", C.BRIGHT_CYAN))
    print()


def prompt_with_help(
    question: str,
    field_key: str,
    default: str = "",
    validator: Optional[Callable[[str], bool]] = None,
    hint: str = "",
) -> str:
    """Like prompt_text but with an inline [h] help option."""
    default_hint = f" [{_c(default, C.DIM)}]" if default else ""
    help_hint    = _c("  (press h for help)", C.DIM)
    if hint:
        print(f"\n  {_c(hint, C.DIM)}")
    while True:
        ans = input(f"\n  {_c('?', C.BRIGHT_YELLOW)} {question}{default_hint}{help_hint}: ").strip()
        if ans.lower() in ("h", "help", "?"):
            print_field_help(field_key)
            continue
        if not ans:
            if default:
                return default
            if validator is None:
                continue
        if validator is None or validator(ans):
            return ans
        print(f"  {_c('✗', C.RED)} Invalid input.")


def prompt_int_with_help(question: str, field_key: str, default: int,
                         min_val: int = 1, max_val: int = 10_000) -> int:
    while True:
        raw = prompt_with_help(question, field_key, str(default))
        try:
            v = int(raw)
            if min_val <= v <= max_val:
                return v
            print(f"  {_c('✗', C.RED)} Must be between {min_val} and {max_val}.")
        except ValueError:
            print(f"  {_c('✗', C.RED)} Please enter a number.")


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

USER_AGENT         = "ScholarForge/3.0 (https://github.com/AnastasiosPapalias/scholarforge)"
REQUEST_TIMEOUT    = 45
DOWNLOAD_TIMEOUT   = 180

OPENALEX_BASE       = "https://api.openalex.org/works"
CROSSREF_BASE       = "https://api.crossref.org/works"
SEMANTIC_SCHOLAR    = "https://api.semanticscholar.org/graph/v1/paper/search"
GOOGLE_BOOKS_BASE   = "https://www.googleapis.com/books/v1/volumes"
IA_ADVANCED         = "https://archive.org/advancedsearch.php"
OPEN_LIBRARY_SEARCH = "https://openlibrary.org/search.json"
PUBMED_SEARCH       = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_SUMMARY      = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
PMC_LINKS           = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
EUROPE_PMC_BASE     = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
ARXIV_BASE          = "https://export.arxiv.org/api/query"
ZENODO_BASE         = "https://zenodo.org/api/records"
CORE_BASE           = "https://api.core.ac.uk/v3/search/works"
DOAJ_BASE           = "https://doaj.org/api/search/articles"
BASE_SEARCH         = "https://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi"
OPENAIRE_BASE       = "https://api.openaire.eu/search/publications"
FIGSHARE_BASE       = "https://api.figshare.com/v2/articles/search"
HAL_BASE            = "https://api.archives-ouvertes.fr/search/"
PAPERITY_BASE       = "https://paperity.org/search/json/"

ALLOWED_DOWNLOAD_EXTS = {".pdf", ".epub", ".txt", ".html", ".htm", ".xml", ".zip"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf", "application/epub+zip", "text/plain", "text/html",
    "application/xhtml+xml", "application/xml", "text/xml", "application/zip",
}

TEXT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".rst", ".log", ".ini", ".cfg", ".conf",
    ".yaml", ".yml", ".json", ".csv", ".tsv", ".xml", ".html", ".htm",
    ".rtf", ".tex"
}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | {".pdf", ".docx"}

DEFAULT_EXCLUDE_DIRS = {
    ".git", ".idea", ".vscode", "__pycache__", "node_modules", ".venv", "venv",
    "downloads", "knowledge_export", "bibliography_output",
}

NOISY_TERMS = {
    "bioprinting", "nursing", "cancer", "lumbar", "scoliosis", "pregnancy",
    "orthopedic", "biomedical", "nanoparticle", "vascular", "alloy",
    "dysmenorrhea", "neonate", "surgery",
}

SAFE_FILENAME_RE = re.compile(r"[^\w._ -]+", re.UNICODE)   # keeps Greek, Cyrillic, CJK etc.
WHITESPACE_RE    = re.compile(r"\s+")
YEAR_RE          = re.compile(r"\b(1[6-9]\d{2}|20\d{2})\b")

CHUNK_SIZE_DEFAULT  = 3500
CHUNK_OVERLAP_DEFAULT = 350


# ─────────────────────────────────────────────────────────────────────────────
# Data Models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class HarvestRecord:
    source: str
    study_type: str
    query: str
    query_mode: str
    title: str
    authors: str
    year: str
    doi: str
    url: str
    open_access_url: str
    pdf_url: str
    file_path: str
    file_status: str
    abstract: str
    language: str
    document_type: str
    source_id: str
    relevance_score: float
    matched_subjects: str
    citation_count: int = 0
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ForgeFileRecord:
    source_path: str
    relative_path: str
    file_name: str
    extension: str
    size_bytes: int
    status: str
    extracted_characters: int
    chunks: int
    notes: str = ""


@dataclass
class ForgeChunk:
    source_path: str
    relative_path: str
    file_name: str
    extension: str
    page: Optional[int]
    chunk_index: int
    text: str
    char_count: int
    text_sha256: str
    word_count: int = 0
    language_hint: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    text = html.unescape(text or "")
    text = text.replace("\x00", " ").replace("\r\n", "\n").replace("\r", "\n")
    text = WHITESPACE_RE.sub(" ", text).strip()
    return text


def safe_filename(name: str, max_len: int = 120) -> str:
    name = SAFE_FILENAME_RE.sub("_", name or "untitled").strip("._ ")
    return (name or "untitled")[:max_len]


def short_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8", errors="ignore")).hexdigest()[:10]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def format_bytes(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def format_number(n: int) -> str:
    return f"{n:,}"


def ensure_dirs(base: Path) -> Dict[str, Path]:
    downloads = base / "downloads"
    metadata  = base / "metadata"
    reports   = base / "reports"
    for p in (base, downloads, metadata, reports):
        p.mkdir(parents=True, exist_ok=True)
    return {"base": base, "downloads": downloads, "metadata": metadata, "reports": reports}


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


def write_csv(path: Path, records: List[HarvestRecord]) -> None:
    fieldnames = [
        "source", "study_type", "query", "query_mode", "title", "authors", "year",
        "doi", "url", "open_access_url", "pdf_url", "file_path", "file_status",
        "abstract", "language", "document_type", "source_id", "relevance_score",
        "matched_subjects", "citation_count",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            row = {k: getattr(r, k, "") for k in fieldnames}
            writer.writerow(row)


def detect_language_hint(text: str) -> str:
    """Lightweight language hint based on common stop-words and Unicode block presence."""
    sample = text[:1500].lower()
    # Check for Greek Unicode block characters (U+0370–U+03FF) before stop-word matching,
    # because Greek stop-words may be stripped by normalisation in some pipelines.
    if re.search(r"[\u0370-\u03ff\u1f00-\u1fff]", sample):
        return "el"
    if re.search(r"\b(the|and|this|that|with|from|have|been|were|they|their)\b", sample):
        return "en"
    if re.search(r"\b(und|die|der|das|den|von|ist|mit|eine|nicht)\b", sample):
        return "de"
    if re.search(r"\b(les|des|une|dans|pour|avec|sur|plus|comme|aussi)\b", sample):
        return "fr"
    if re.search(r"\b(los|las|del|con|por|para|una|como|pero|muy)\b", sample):
        return "es"
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# Harvest: Network layer
# ─────────────────────────────────────────────────────────────────────────────

def request_with_retry(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    expect_json: bool = False,
    timeout: int = REQUEST_TIMEOUT,
    max_attempts: int = 6,
    headers: Optional[Dict[str, str]] = None,
) -> Any:
    """HTTP GET with exponential back-off on 429/5xx."""
    query = urllib.parse.urlencode(params or {}, doseq=True)
    full_url = f"{url}?{query}" if query else url
    req_headers = {"User-Agent": USER_AGENT}
    if headers:
        req_headers.update(headers)

    last_error: Optional[Exception] = None
    for attempt in range(1, max_attempts + 1):
        try:
            req = urllib.request.Request(full_url, headers=req_headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
                text = data.decode("utf-8", errors="ignore")
                if expect_json:
                    return json.loads(text)
                return text
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code in (429, 500, 502, 503, 504):
                retry_after = exc.headers.get("Retry-After")
                sleep_s = int(retry_after) if (retry_after and retry_after.isdigit()) else min(60, int(1.8 ** attempt))
                time.sleep(sleep_s)
                continue
            raise
        except Exception as exc:
            last_error = exc
            time.sleep(min(30, int(1.8 ** attempt)))
    if last_error:
        raise last_error
    raise RuntimeError("Unknown request failure")


# ─────────────────────────────────────────────────────────────────────────────
# Harvest: Relevance scoring
# ─────────────────────────────────────────────────────────────────────────────

def parse_subjects(raw: str) -> List[str]:
    return [clean_text(x) for x in raw.split(",") if clean_text(x)]


def subject_tokens(subject: str) -> List[str]:
    """Split a subject phrase into searchable tokens, Unicode-aware (supports Greek, etc.)."""
    return [
        t for t in re.split(r"[^\w]+", subject.lower(), flags=re.UNICODE)
        if len(t) >= 3 and not t.isdigit()
    ]


def build_query_forms(subject: str) -> List[Tuple[str, str]]:
    """Return [(query_string, mode_label)]."""
    return [
        (f'"{subject}"', "exact_phrase"),
        (subject, "broad"),
    ]


def normalize_unicode(text: str) -> str:
    """
    Lowercase + NFD decomposition + strip combining marks (accents/tonos).
    Allows accent-insensitive matching across languages:
      'καβείρια' → 'καβειρια',  'café' → 'cafe'
    """
    return "".join(
        c for c in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(c) != "Mn"
    )


def compute_relevance(title: str, abstract: str, subjects: List[str]) -> Tuple[float, List[str]]:
    """Score a record against the subject list. Higher = more relevant.

    Matching is done in two passes:
      1. Exact string match (preserving accents) — highest weight.
      2. Accent-normalised match — catches e.g. 'μυστήρια' in a title that writes 'μυστηρια'.
    """
    # Original (accent-preserved) haystacks
    hay_title_orig = clean_text(title).lower()
    hay_abs_orig   = clean_text(abstract).lower()

    # Accent-stripped haystacks for fuzzy matching
    hay_title_norm = normalize_unicode(hay_title_orig)
    hay_abs_norm   = normalize_unicode(hay_abs_orig)

    score   = 0.0
    matched: List[str] = []

    for subj in subjects:
        subj_l    = subj.lower()
        subj_norm = normalize_unicode(subj_l)
        toks      = subject_tokens(subj)
        toks_norm = [normalize_unicode(t) for t in toks]

        # ── Phrase matching ──────────────────────────────────────────────────
        in_title = subj_l in hay_title_orig or subj_norm in hay_title_norm
        in_abs   = subj_l in hay_abs_orig   or subj_norm in hay_abs_norm

        if in_title:
            score += 20
            matched.append(subj)
        elif in_abs:
            score += 11
            matched.append(subj)

        # ── Token matching ───────────────────────────────────────────────────
        for tok, tok_n in zip(toks, toks_norm):
            if tok in hay_title_orig or tok_n in hay_title_norm:
                score += 4.5
            if tok in hay_abs_orig or tok_n in hay_abs_norm:
                score += 1.5

    for bad in NOISY_TERMS:
        if bad in hay_title_orig:
            score -= 32
        elif bad in hay_abs_orig:
            score -= 14

    if not title:
        score -= 10

    return score, sorted(set(matched))


def normalize_authors(names: List[str]) -> str:
    return "; ".join(clean_text(n) for n in names if clean_text(n))


def record_from_basic(
    source: str, study_type: str, query: str, query_mode: str,
    title: str, authors: str, year: str, doi: str, url: str,
    open_access_url: str, pdf_url: str, abstract: str,
    language: str, document_type: str, source_id: str,
    raw: Dict[str, Any], subjects: List[str],
    citation_count: int = 0,
) -> HarvestRecord:
    score, matched = compute_relevance(title, abstract, subjects)
    return HarvestRecord(
        source=source, study_type=study_type, query=query, query_mode=query_mode,
        title=clean_text(title), authors=clean_text(authors), year=str(year or ""),
        doi=clean_text(doi), url=clean_text(url), open_access_url=clean_text(open_access_url),
        pdf_url=clean_text(pdf_url), file_path="", file_status="not_attempted",
        abstract=clean_text(abstract)[:4000], language=clean_text(language),
        document_type=clean_text(document_type), source_id=clean_text(source_id),
        relevance_score=round(score, 2), matched_subjects="; ".join(matched),
        citation_count=citation_count, raw=raw,
    )


def dedupe_records(records: List[HarvestRecord]) -> List[HarvestRecord]:
    seen:   set   = set()
    unique: List[HarvestRecord] = []
    for r in sorted(records, key=lambda x: (-x.relevance_score, x.year or "", x.title.lower())):
        key = ((r.doi or "").lower().strip(), clean_text(r.title).lower(), (r.year or "").strip())
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)
    return unique


def filter_records(records: List[HarvestRecord], min_score: float) -> List[HarvestRecord]:
    """Keep records scoring above threshold. No document-type discrimination."""
    return [r for r in records
            if r.relevance_score >= min_score
            and (r.document_type or "").lower() not in {"image", "audio", "video"}]


# ─────────────────────────────────────────────────────────────────────────────
# Harvest: Source-specific search functions
# ─────────────────────────────────────────────────────────────────────────────

def search_openalex(query: str, query_mode: str, subjects: List[str], per_page: int = 25) -> List[HarvestRecord]:
    data    = request_with_retry(OPENALEX_BASE, {"search": query, "per-page": per_page}, expect_json=True)
    results = data.get("results", [])
    out     = []
    for item in results:
        title    = item.get("display_name", "") or ""
        abstract = ""
        inv      = item.get("abstract_inverted_index") or {}
        if inv:
            max_pos = max((max(v) for v in inv.values() if v), default=0)
            words   = [""] * (max_pos + 1)
            for word, positions in inv.items():
                for p in positions:
                    if 0 <= p < len(words):
                        words[p] = word
            abstract = " ".join(words)
        loc      = item.get("primary_location") or {}
        best_oa  = item.get("best_oa_location") or {}
        authors  = normalize_authors([a.get("author", {}).get("display_name", "") for a in item.get("authorships", [])])
        cites    = item.get("cited_by_count", 0) or 0
        out.append(record_from_basic(
            source="OpenAlex", study_type="any", query=query, query_mode=query_mode,
            title=title, authors=authors, year=str(item.get("publication_year") or ""),
            doi=(item.get("doi") or "").replace("https://doi.org/", ""),
            url=item.get("id", "") or "",
            open_access_url=best_oa.get("landing_page_url") or loc.get("landing_page_url") or "",
            pdf_url=best_oa.get("pdf_url") or "",
            abstract=abstract, language="", document_type=item.get("type") or "",
            source_id=item.get("id", "") or "", raw=item, subjects=subjects, citation_count=cites,
        ))
    return out


def search_crossref(query: str, query_mode: str, subjects: List[str], rows: int = 25) -> List[HarvestRecord]:
    data  = request_with_retry(CROSSREF_BASE, {"query.bibliographic": query, "rows": rows}, expect_json=True)
    items = data.get("message", {}).get("items", [])
    out   = []
    for item in items:
        title   = (item.get("title") or [""])[0]
        authors = normalize_authors(
            [" ".join([a.get("given", ""), a.get("family", "")]).strip() for a in (item.get("author") or [])]
        )
        year = ""
        issued = item.get("issued", {}).get("date-parts", [])
        if issued and issued[0]:
            year = str(issued[0][0])
        pdf_url = ""
        for link in (item.get("link") or []):
            if "pdf" in (link.get("content-type") or "").lower():
                pdf_url = link.get("URL", "") or ""
                break
        cites = item.get("is-referenced-by-count", 0) or 0
        out.append(record_from_basic(
            source="Crossref", study_type="any", query=query, query_mode=query_mode,
            title=title, authors=authors, year=year, doi=item.get("DOI", "") or "",
            url=item.get("URL", "") or "",
            open_access_url=pdf_url or item.get("URL", "") or "",
            pdf_url=pdf_url, abstract=item.get("abstract", "") or "",
            language=item.get("language", "") or "", document_type=item.get("type", "") or "",
            source_id=item.get("DOI", "") or "", raw=item, subjects=subjects, citation_count=cites,
        ))
    return out


def search_google_books(query: str, query_mode: str, subjects: List[str], max_results: int = 20) -> List[HarvestRecord]:
    data  = request_with_retry(GOOGLE_BOOKS_BASE, {"q": query, "maxResults": min(max_results, 40), "printType": "books"}, expect_json=True)
    items = data.get("items", []) or []
    out   = []
    for item in items:
        info    = item.get("volumeInfo", {}) or {}
        access  = item.get("accessInfo", {}) or {}
        authors = normalize_authors(info.get("authors", []) or [])
        year    = ""
        m       = YEAR_RE.search(info.get("publishedDate", "") or "")
        if m:
            year = m.group(0)
        pdf_url = ""
        if (access.get("pdf") or {}).get("isAvailable"):
            pdf_url = (access.get("pdf") or {}).get("downloadLink", "") or ""
        out.append(record_from_basic(
            source="Google Books", study_type="any", query=query, query_mode=query_mode,
            title=info.get("title", "") or "", authors=authors, year=year, doi="",
            url=info.get("infoLink", "") or item.get("selfLink", "") or "",
            open_access_url=pdf_url or info.get("previewLink", "") or info.get("infoLink", "") or "",
            pdf_url=pdf_url, abstract=info.get("description", "") or "",
            language=info.get("language", "") or "", document_type="book",
            source_id=item.get("id", "") or "", raw=item, subjects=subjects,
        ))
    return out


def search_open_library(query: str, query_mode: str, subjects: List[str], limit: int = 20) -> List[HarvestRecord]:
    data  = request_with_retry(OPEN_LIBRARY_SEARCH, {"q": query, "limit": limit}, expect_json=True)
    docs  = data.get("docs", []) or []
    out   = []
    for item in docs:
        title   = item.get("title", "") or ""
        authors = normalize_authors(item.get("author_name", []) or [])
        year    = str(item.get("first_publish_year") or "")
        key     = item.get("key", "") or ""
        url     = f"https://openlibrary.org{key}" if key else ""
        out.append(record_from_basic(
            source="Open Library", study_type="any", query=query, query_mode=query_mode,
            title=title, authors=authors, year=year, doi="", url=url, open_access_url=url,
            pdf_url="", abstract="", language="", document_type="book",
            source_id=key, raw=item, subjects=subjects,
        ))
    return out


def search_internet_archive(query: str, query_mode: str, subjects: List[str], rows: int = 20) -> List[HarvestRecord]:
    q      = f"title:({query}) OR subject:({query})"
    params = {"q": q, "fl[]": ["identifier", "title", "creator", "year", "language", "mediatype"],
               "rows": rows, "page": 1, "output": "json"}
    data   = request_with_retry(IA_ADVANCED, params, expect_json=True)
    docs   = data.get("response", {}).get("docs", []) or []
    out    = []
    for item in docs:
        identifier = item.get("identifier", "") or ""
        title      = item.get("title", "") or identifier
        creator    = item.get("creator", "")
        authors    = normalize_authors(creator if isinstance(creator, list) else [str(creator or "")])
        year       = str(item.get("year") or "")
        url        = f"https://archive.org/details/{identifier}" if identifier else ""
        out.append(record_from_basic(
            source="Internet Archive", study_type="any", query=query, query_mode=query_mode,
            title=title, authors=authors, year=year, doi="", url=url, open_access_url=url,
            pdf_url="", abstract="", language=str(item.get("language") or ""),
            document_type=str(item.get("mediatype") or "text"),
            source_id=identifier, raw=item, subjects=subjects,
        ))
    return out


def search_pubmed(query: str, query_mode: str, subjects: List[str], retmax: int = 20) -> List[HarvestRecord]:
    data = request_with_retry(PUBMED_SEARCH,
        {"db": "pubmed", "term": query, "retmode": "json", "retmax": retmax, "sort": "relevance"}, expect_json=True)
    ids  = data.get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []
    summary = request_with_retry(PUBMED_SUMMARY, {"db": "pubmed", "id": ",".join(ids), "retmode": "json"}, expect_json=True)
    out = []
    for pmid in ids:
        item    = summary.get("result", {}).get(pmid, {})
        title   = item.get("title", "") or ""
        authors = normalize_authors([a.get("name", "") for a in (item.get("authors") or [])])
        pubdate = item.get("pubdate", "") or ""
        m       = YEAR_RE.search(pubdate)
        year    = m.group(0) if m else ""
        pmc_url = ""
        pmc_pdf = ""
        try:
            xml = request_with_retry(PMC_LINKS, {"dbfrom": "pubmed", "db": "pmc", "id": pmid, "retmode": "xml"})
            root    = ET.fromstring(xml)
            pmc_ids = [n.text for n in root.findall(".//LinkSetDb/Link/Id") if n.text]
            if pmc_ids:
                pmcid   = pmc_ids[0]
                pmc_url = f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{pmcid}/"
                pmc_pdf = f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{pmcid}/pdf/"
        except Exception:
            pass
        out.append(record_from_basic(
            source="PubMed", study_type="any", query=query, query_mode=query_mode,
            title=title, authors=authors, year=year, doi="",
            url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            open_access_url=pmc_url or f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            pdf_url=pmc_pdf, abstract="", language="", document_type="journal article",
            source_id=pmid, raw=item, subjects=subjects,
        ))
    return out


def search_semantic_scholar(query: str, query_mode: str, subjects: List[str], limit: int = 20) -> List[HarvestRecord]:
    """Semantic Scholar Graph API — free, no key required for basic use."""
    params = {"query": query, "limit": limit,
               "fields": "title,authors,year,abstract,citationCount,openAccessPdf,externalIds"}
    s2_headers: Optional[Dict[str, str]] = None
    if _API_KEYS.semantic_scholar_key:
        s2_headers = {"x-api-key": _API_KEYS.semantic_scholar_key}
    try:
        data  = request_with_retry(SEMANTIC_SCHOLAR, params, expect_json=True, headers=s2_headers)
    except Exception:
        return []
    items = data.get("data", []) or []
    out   = []
    for item in items:
        title   = item.get("title", "") or ""
        authors = normalize_authors([(a.get("name") or "") for a in (item.get("authors") or [])])
        year    = str(item.get("year") or "")
        cites   = item.get("citationCount", 0) or 0
        ext     = item.get("externalIds") or {}
        doi     = ext.get("DOI", "") or ""
        oa      = item.get("openAccessPdf") or {}
        pdf_url = oa.get("url", "") or ""
        ss_id   = item.get("paperId", "") or ""
        url     = f"https://www.semanticscholar.org/paper/{ss_id}" if ss_id else ""
        out.append(record_from_basic(
            source="Semantic Scholar", study_type="any", query=query, query_mode=query_mode,
            title=title, authors=authors, year=year, doi=doi, url=url,
            open_access_url=pdf_url or url, pdf_url=pdf_url,
            abstract=item.get("abstract", "") or "", language="",
            document_type="journal article", source_id=ss_id, raw=item, subjects=subjects,
            citation_count=cites,
        ))
    return out


def search_arxiv(query: str, query_mode: str, subjects: List[str], max_results: int = 20) -> List[HarvestRecord]:
    """arXiv — preprints in physics, maths, CS, biology, economics. Free PDF for every paper."""
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    try:
        xml_text = request_with_retry(ARXIV_BASE, params, expect_json=False)
        root = ET.fromstring(xml_text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        out: List[HarvestRecord] = []
        for entry in root.findall("atom:entry", ns):
            title    = (entry.findtext("atom:title", "", ns) or "").replace("\n", " ").strip()
            abstract = (entry.findtext("atom:summary", "", ns) or "").replace("\n", " ").strip()
            arxiv_id = (entry.findtext("atom:id", "", ns) or "").split("/abs/")[-1].strip()
            year     = ""
            pub = entry.findtext("atom:published", "", ns) or ""
            m = YEAR_RE.search(pub)
            if m:
                year = m.group(0)
            authors = normalize_authors([
                (a.findtext("atom:name", "", ns) or "")
                for a in entry.findall("atom:author", ns)
            ])
            pdf_url  = ""
            page_url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""
            for link in entry.findall("atom:link", ns):
                if link.get("type") == "application/pdf":
                    pdf_url = link.get("href", "") or ""
            if not pdf_url and arxiv_id:
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
            doi = ""
            doi_el = entry.find("{http://arxiv.org/schemas/atom}doi")
            if doi_el is not None and doi_el.text:
                doi = doi_el.text.strip()
            out.append(record_from_basic(
                source="arXiv", study_type="any", query=query, query_mode=query_mode,
                title=title, authors=authors, year=year, doi=doi,
                url=page_url, open_access_url=pdf_url or page_url, pdf_url=pdf_url,
                abstract=abstract, language="", document_type="preprint",
                source_id=arxiv_id, raw={"id": arxiv_id}, subjects=subjects,
            ))
        return out
    except Exception:
        return []


def search_zenodo(query: str, query_mode: str, subjects: List[str], max_results: int = 20) -> List[HarvestRecord]:
    """Zenodo (CERN) — open-access research across all disciplines including datasets and theses."""
    params = {
        "q": query,
        "size": max_results,
        "sort": "bestmatch",
        "access_right": "open",
    }
    try:
        data = request_with_retry(ZENODO_BASE, params, expect_json=True)
        out: List[HarvestRecord] = []
        for item in data.get("hits", {}).get("hits", []):
            meta    = item.get("metadata", {})
            title   = meta.get("title", "") or ""
            authors = normalize_authors([
                (c.get("name") or (c.get("given", "") + " " + c.get("family", "")).strip())
                for c in (meta.get("creators") or [])
            ])
            year    = str(meta.get("publication_date", "")[:4]) if meta.get("publication_date") else ""
            doi     = meta.get("doi", "") or ""
            rec_id  = str(item.get("id", ""))
            page_url= f"https://zenodo.org/record/{rec_id}" if rec_id else ""
            pdf_url = ""
            for f in (item.get("files") or []):
                if (f.get("key", "") or "").endswith(".pdf"):
                    pdf_url = f.get("links", {}).get("self", "") or ""
                    break
            abstract = meta.get("description", "") or ""
            doc_type = (meta.get("resource_type", {}).get("type") or "")
            out.append(record_from_basic(
                source="Zenodo", study_type="any", query=query, query_mode=query_mode,
                title=title, authors=authors, year=year, doi=doi,
                url=page_url, open_access_url=pdf_url or page_url, pdf_url=pdf_url,
                abstract=abstract, language="", document_type=doc_type,
                source_id=rec_id, raw=item, subjects=subjects,
            ))
        return out
    except Exception:
        return []


def search_core(query: str, query_mode: str, subjects: List[str], max_results: int = 20) -> List[HarvestRecord]:
    """CORE — 260M+ open-access full-text papers harvested from repositories worldwide."""
    params = {"q": query, "limit": max_results, "offset": 0}
    core_headers: Optional[Dict[str, str]] = None
    if _API_KEYS.core_api_key:
        core_headers = {"Authorization": f"Bearer {_API_KEYS.core_api_key}"}
    try:
        data = request_with_retry(CORE_BASE, params, expect_json=True, headers=core_headers)
        out: List[HarvestRecord] = []
        for item in (data.get("results") or []):
            title    = item.get("title", "") or ""
            abstract = item.get("abstract", "") or ""
            authors  = normalize_authors([
                (a.get("name") or "") for a in (item.get("authors") or [])
            ])
            year     = ""
            yr = item.get("yearPublished") or item.get("publishedDate", "")
            m = YEAR_RE.search(str(yr))
            if m:
                year = m.group(0)
            doi      = item.get("doi", "") or ""
            pdf_url  = item.get("downloadUrl", "") or ""
            page_url = item.get("sourceFulltextUrls", [None])[0] or \
                       f"https://core.ac.uk/works/{item.get('id', '')}"
            out.append(record_from_basic(
                source="CORE", study_type="any", query=query, query_mode=query_mode,
                title=title, authors=authors, year=year, doi=doi,
                url=page_url, open_access_url=pdf_url or page_url, pdf_url=pdf_url,
                abstract=abstract, language="", document_type="journal article",
                source_id=str(item.get("id", "")), raw=item, subjects=subjects,
            ))
        return out
    except Exception:
        return []


def search_europe_pmc(query: str, query_mode: str, subjects: List[str], max_results: int = 20) -> List[HarvestRecord]:
    """Europe PMC — 40M+ life science papers, books, theses, preprints with full-text links."""
    params = {
        "query": query,
        "resultType": "core",
        "pageSize": max_results,
        "format": "json",
        "sort": "CITED desc",
    }
    try:
        data = request_with_retry(EUROPE_PMC_BASE, params, expect_json=True)
        out: List[HarvestRecord] = []
        for item in (data.get("resultList", {}).get("result") or []):
            title    = item.get("title", "") or ""
            abstract = item.get("abstractText", "") or ""
            authors  = normalize_authors([
                a.get("fullName", "") for a in (item.get("authorList", {}).get("author") or [])
            ])
            year     = str(item.get("pubYear", "") or "")
            doi      = item.get("doi", "") or ""
            pmcid    = item.get("pmcid", "") or ""
            pmid     = item.get("pmid", "") or ""
            pdf_url  = f"https://europepmc.org/articles/{pmcid}/pdf/" if pmcid else ""
            page_url = (f"https://europepmc.org/article/MED/{pmid}" if pmid
                        else f"https://europepmc.org/article/PMC/{pmcid}" if pmcid else "")
            full_url = item.get("fullTextUrlList", {}).get("fullTextUrl", [{}])[0].get("url", "") or ""
            out.append(record_from_basic(
                source="Europe PMC", study_type="any", query=query, query_mode=query_mode,
                title=title, authors=authors, year=year, doi=doi,
                url=page_url, open_access_url=pdf_url or full_url or page_url,
                pdf_url=pdf_url or full_url,
                abstract=abstract, language="", document_type=item.get("pubType", "journal article"),
                source_id=pmcid or pmid, raw=item, subjects=subjects,
            ))
        return out
    except Exception:
        return []


def search_doaj(query: str, query_mode: str, subjects: List[str], max_results: int = 20) -> List[HarvestRecord]:
    """DOAJ — Directory of Open Access Journals. Only fully OA, peer-reviewed articles."""
    params = {"q": query, "pageSize": max_results, "page": 1, "sort": "relevance"}
    try:
        data = request_with_retry(DOAJ_BASE, params, expect_json=True)
        out: List[HarvestRecord] = []
        for item in (data.get("results") or []):
            bib     = item.get("bibjson", {})
            title   = bib.get("title", "") or ""
            abstract= bib.get("abstract", "") or ""
            authors = normalize_authors([
                a.get("name", "") for a in (bib.get("author") or [])
            ])
            year    = str(bib.get("year", "") or "")
            doi     = ""
            pdf_url = ""
            for ident in (bib.get("identifier") or []):
                if ident.get("type") == "doi":
                    doi = ident.get("id", "") or ""
            for link in (bib.get("link") or []):
                if link.get("type") == "fulltext":
                    pdf_url = link.get("url", "") or ""
            out.append(record_from_basic(
                source="DOAJ", study_type="any", query=query, query_mode=query_mode,
                title=title, authors=authors, year=year, doi=doi,
                url=pdf_url, open_access_url=pdf_url, pdf_url=pdf_url,
                abstract=abstract, language=bib.get("language", [""])[0] if bib.get("language") else "",
                document_type="journal article",
                source_id=item.get("id", ""), raw=item, subjects=subjects,
            ))
        return out
    except Exception:
        return []


def search_openaire(query: str, query_mode: str, subjects: List[str], max_results: int = 20) -> List[HarvestRecord]:
    """OpenAIRE — European open research infrastructure, strong in EU-funded research."""
    params = {
        "keywords": query,
        "format": "json",
        "size": max_results,
        "page": 1,
        "hasdownloadablefiles": "true",
    }
    try:
        data = request_with_retry(OPENAIRE_BASE, params, expect_json=True)
        out: List[HarvestRecord] = []
        results = (data.get("response", {}).get("results", {}) or {}).get("result") or []
        if not isinstance(results, list):
            results = [results]
        for item in results:
            meta    = item.get("metadata", {}).get("oaf:entity", {}).get("oaf:result", {})
            title   = ""
            titles  = meta.get("title", [])
            if isinstance(titles, list) and titles:
                title = (titles[0].get("$", "") or "") if isinstance(titles[0], dict) else str(titles[0])
            elif isinstance(titles, dict):
                title = titles.get("$", "") or ""
            authors_raw = meta.get("creator", [])
            if isinstance(authors_raw, dict):
                authors_raw = [authors_raw]
            authors = normalize_authors([
                (a.get("$", "") if isinstance(a, dict) else str(a)) for a in authors_raw
            ])
            year    = str(meta.get("dateofacceptance", "")[:4]) if meta.get("dateofacceptance") else ""
            pdf_url = ""
            children = meta.get("children", {})
            instances = children.get("instance", [])
            if isinstance(instances, dict):
                instances = [instances]
            for inst in instances:
                wl = inst.get("webresource", {})
                if isinstance(wl, dict):
                    url = wl.get("url", {}).get("$", "") or ""
                    if url:
                        pdf_url = url
                        break
            out.append(record_from_basic(
                source="OpenAIRE", study_type="any", query=query, query_mode=query_mode,
                title=title, authors=authors, year=year, doi="",
                url=pdf_url, open_access_url=pdf_url, pdf_url=pdf_url,
                abstract="", language="", document_type="publication",
                source_id=item.get("header", {}).get("dri:objIdentifier", {}).get("$", ""),
                raw=item, subjects=subjects,
            ))
        return out
    except Exception:
        return []


def search_figshare(query: str, query_mode: str, subjects: List[str], max_results: int = 20) -> List[HarvestRecord]:
    """Figshare — open research: papers, datasets, posters, theses, code. Free PDF always."""
    # Figshare search uses POST with JSON body
    url = "https://api.figshare.com/v2/articles/search"
    payload = json.dumps({
        "search_for": query,
        "page_size":  min(max_results, 100),
        "page":       1,
        "item_type":  None,  # all types
    }).encode("utf-8")
    try:
        req = urllib.request.Request(
            url, data=payload,
            headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            items = json.loads(resp.read().decode("utf-8", errors="ignore"))
        out: List[HarvestRecord] = []
        for item in (items or []):
            title    = item.get("title", "") or ""
            authors  = normalize_authors([a.get("full_name", "") for a in (item.get("authors") or [])])
            year     = ""
            pub = item.get("published_date", "") or item.get("created_date", "") or ""
            m = YEAR_RE.search(pub)
            if m:
                year = m.group(0)
            doi      = item.get("doi", "") or ""
            page_url = item.get("url_public_html", "") or item.get("url", "") or ""
            pdf_url  = item.get("url_public_pdf", "") or ""
            # Try to get direct download from files list
            if not pdf_url:
                for f in (item.get("files") or []):
                    if (f.get("name", "") or "").lower().endswith(".pdf"):
                        pdf_url = f.get("download_url", "") or f.get("url", "") or ""
                        break
            doc_type = (item.get("defined_type_name") or item.get("defined_type") or "")
            out.append(record_from_basic(
                source="Figshare", study_type="any", query=query, query_mode=query_mode,
                title=title, authors=authors, year=year, doi=doi,
                url=page_url, open_access_url=pdf_url or page_url, pdf_url=pdf_url,
                abstract=item.get("description", "") or "",
                language="", document_type=str(doc_type),
                source_id=str(item.get("id", "")), raw=item, subjects=subjects,
            ))
        return out
    except Exception:
        return []


def search_hal(query: str, query_mode: str, subjects: List[str], max_results: int = 20) -> List[HarvestRecord]:
    """HAL (Hyper Articles en Ligne) — 4.4M+ French & international papers, strong humanities."""
    params = {
        "q":    query,
        "wt":   "json",
        "rows": max_results,
        "fl":   "halId_s,title_s,authFullName_s,producedDate_s,doiId_s,fileMain_s,uri_s,abstract_s,docType_s,language_s",
        "sort": "score desc",
        "fq":   "openAccess_bool:true",
    }
    try:
        data = request_with_retry("https://api.archives-ouvertes.fr/search/", params, expect_json=True)
        docs = data.get("response", {}).get("docs", []) or []
        out: List[HarvestRecord] = []
        for item in docs:
            title   = (item.get("title_s") or [""])[0] if isinstance(item.get("title_s"), list) else (item.get("title_s") or "")
            authors_raw = item.get("authFullName_s") or []
            authors = normalize_authors(authors_raw if isinstance(authors_raw, list) else [authors_raw])
            year    = ""
            m = YEAR_RE.search(str(item.get("producedDate_s", "") or ""))
            if m:
                year = m.group(0)
            doi     = item.get("doiId_s", "") or ""
            hal_id  = item.get("halId_s", "") or ""
            page_url= item.get("uri_s", "") or (f"https://hal.science/{hal_id}" if hal_id else "")
            pdf_url = item.get("fileMain_s", "") or ""
            if not pdf_url and hal_id:
                pdf_url = f"https://hal.science/{hal_id}/document"
            abstract_raw = item.get("abstract_s", "") or ""
            abstract = (abstract_raw[0] if isinstance(abstract_raw, list) else abstract_raw)
            lang_raw = item.get("language_s", "") or ""
            lang     = (lang_raw[0] if isinstance(lang_raw, list) else lang_raw)
            out.append(record_from_basic(
                source="HAL", study_type="any", query=query, query_mode=query_mode,
                title=title, authors=authors, year=year, doi=doi,
                url=page_url, open_access_url=pdf_url or page_url, pdf_url=pdf_url,
                abstract=abstract, language=lang,
                document_type=item.get("docType_s", "") or "",
                source_id=hal_id, raw=item, subjects=subjects,
            ))
        return out
    except Exception:
        return []


def search_ssrn(query: str, query_mode: str, subjects: List[str], max_results: int = 20) -> List[HarvestRecord]:
    """SSRN — Social Science Research Network. Economics, law, finance, social sciences.
    No official API: uses the public search page and Crossref DOI fallback for PDF links."""
    # SSRN papers are indexed in Crossref — use Crossref with SSRN filter
    # and also try direct SSRN abstract URLs
    try:
        params = {
            "query.bibliographic": query,
            "filter": "prefix:10.2139",  # 10.2139 is SSRN's DOI prefix
            "rows":   min(max_results, 50),
        }
        data = request_with_retry(CROSSREF_BASE, params, expect_json=True)
        items = data.get("message", {}).get("items", []) or []
        out: List[HarvestRecord] = []
        for item in items:
            title   = (item.get("title") or [""])[0]
            authors = normalize_authors([
                " ".join([a.get("given", ""), a.get("family", "")]).strip()
                for a in (item.get("author") or [])
            ])
            year = ""
            issued = item.get("issued", {}).get("date-parts", [])
            if issued and issued[0]:
                year = str(issued[0][0])
            doi = item.get("DOI", "") or ""
            # SSRN PDF pattern: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=XXXXXXX
            # Extract abstract_id from DOI: 10.2139/ssrn.XXXXXXX
            ssrn_id = doi.replace("10.2139/ssrn.", "") if "10.2139/ssrn." in doi else ""
            page_url = f"https://papers.ssrn.com/sol3/papers.cfm?abstract_id={ssrn_id}" if ssrn_id else item.get("URL", "") or ""
            pdf_url  = f"https://papers.ssrn.com/sol3/Delivery.cfm/{ssrn_id}.pdf" if ssrn_id else ""
            out.append(record_from_basic(
                source="SSRN", study_type="any", query=query, query_mode=query_mode,
                title=title, authors=authors, year=year, doi=doi,
                url=page_url, open_access_url=pdf_url or page_url, pdf_url=pdf_url,
                abstract=item.get("abstract", "") or "",
                language=item.get("language", "") or "",
                document_type=item.get("type", "working-paper") or "working-paper",
                source_id=doi, raw=item, subjects=subjects,
            ))
        return out
    except Exception:
        return []


def search_paperity(query: str, query_mode: str, subjects: List[str], max_results: int = 20) -> List[HarvestRecord]:
    """Paperity — aggregator of 100% Open Access journals only. Every paper is free."""
    params = {
        "q":        query,
        "format":   "json",
        "limit":    min(max_results, 100),
        "offset":   0,
    }
    try:
        data = request_with_retry("https://paperity.org/search/json/", params, expect_json=True)
        papers = data if isinstance(data, list) else data.get("papers", []) or []
        out: List[HarvestRecord] = []
        for item in papers:
            title   = item.get("title", "") or ""
            authors = normalize_authors((item.get("authors") or "").split(", "))
            year    = str(item.get("year", "") or "")
            doi     = item.get("doi", "") or ""
            pdf_url = item.get("pdfUrl", "") or item.get("pdf", "") or ""
            page_url= item.get("url", "") or ""
            out.append(record_from_basic(
                source="Paperity", study_type="any", query=query, query_mode=query_mode,
                title=title, authors=authors, year=year, doi=doi,
                url=page_url, open_access_url=pdf_url or page_url, pdf_url=pdf_url,
                abstract=item.get("abstract", "") or "",
                language=item.get("language", "") or "",
                document_type="journal article",
                source_id=doi or item.get("id", ""), raw=item, subjects=subjects,
            ))
        return out
    except Exception:
        return []


def search_ethesis(query: str, query_mode: str, subjects: List[str], max_results: int = 15) -> List[HarvestRecord]:
    """EThOS (British Library) + DART-Europe — UK & European doctoral theses, mostly free PDF."""
    out: List[HarvestRecord] = []

    # EThOS uses OAI-PMH ListRecords — instead use their public search API
    try:
        ethos_url = "https://ethos.bl.uk/api/search"
        params = {"query": query, "rows": min(max_results, 25), "start": 0}
        data = request_with_retry(ethos_url, params, expect_json=True)
        for item in (data.get("docs") or data.get("results") or []):
            title   = item.get("thesis_title", "") or item.get("title", "") or ""
            authors = item.get("author", "") or ""
            year    = str(item.get("awarded_date", "") or "")[:4]
            ethos_id= item.get("EThOS_ID", "") or item.get("id", "") or ""
            page_url= f"https://ethos.bl.uk/OrderDetails.do?uin={ethos_id}" if ethos_id else ""
            pdf_url = item.get("full_text_url", "") or ""
            out.append(record_from_basic(
                source="EThOS", study_type="any", query=query, query_mode=query_mode,
                title=title, authors=normalize_authors([authors]), year=year, doi="",
                url=page_url, open_access_url=pdf_url or page_url, pdf_url=pdf_url,
                abstract=item.get("abstract", "") or "",
                language="en", document_type="thesis",
                source_id=ethos_id, raw=item, subjects=subjects,
            ))
    except Exception:
        pass

    # DART-Europe: European theses via OAI-PMH search proxy
    try:
        dart_params = {
            "q":      query,
            "format": "json",
            "rows":   min(max_results, 25),
        }
        dart_data = request_with_retry("https://www.dart-europe.org/api/theses/", dart_params, expect_json=True)
        for item in (dart_data.get("theses") or dart_data.get("docs") or []):
            title   = item.get("title", "") or ""
            authors = item.get("author", "") or ""
            year    = str(item.get("date", "") or "")[:4]
            url_val = item.get("url", "") or ""
            pdf_url = item.get("fulltext_url", "") or ""
            out.append(record_from_basic(
                source="DART-Europe", study_type="any", query=query, query_mode=query_mode,
                title=title, authors=normalize_authors([authors]), year=year, doi="",
                url=url_val, open_access_url=pdf_url or url_val, pdf_url=pdf_url,
                abstract="", language="", document_type="thesis",
                source_id=url_val, raw=item, subjects=subjects,
            ))
    except Exception:
        pass

    return out


def search_pmc_fulltext(query: str, query_mode: str, subjects: List[str], max_results: int = 20) -> List[HarvestRecord]:
    """PubMed Central Full-Text — NIH's free full-text biomedical archive. Guaranteed PDF."""
    params = {
        "db":     "pmc",
        "term":   query,
        "retmode":"json",
        "retmax": max_results,
        "sort":   "relevance",
    }
    try:
        data = request_with_retry(PUBMED_SEARCH.replace("esearch", "esearch"), params, expect_json=True)
        # Use the PMC esearch endpoint
        pmc_search = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        data = request_with_retry(pmc_search, {
            "db": "pmc", "term": query, "retmode": "json", "retmax": max_results
        }, expect_json=True)
        ids = data.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []
        summary = request_with_retry(PUBMED_SUMMARY, {
            "db": "pmc", "id": ",".join(ids), "retmode": "json"
        }, expect_json=True)
        out: List[HarvestRecord] = []
        for pmcid in ids:
            item = summary.get("result", {}).get(pmcid, {})
            title   = item.get("title", "") or ""
            authors = normalize_authors([a.get("name", "") for a in (item.get("authors") or [])])
            pubdate = item.get("pubdate", "") or ""
            m       = YEAR_RE.search(pubdate)
            year    = m.group(0) if m else ""
            page_url= f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{pmcid}/"
            pdf_url = f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{pmcid}/pdf/"
            out.append(record_from_basic(
                source="PMC Full-Text", study_type="any", query=query, query_mode=query_mode,
                title=title, authors=authors, year=year, doi="",
                url=page_url, open_access_url=pdf_url, pdf_url=pdf_url,
                abstract="", language="", document_type="journal article",
                source_id=f"PMC{pmcid}", raw=item, subjects=subjects,
            ))
        return out
    except Exception:
        return []


def search_oamg(query: str, query_mode: str, subjects: List[str], max_results: int = 20) -> List[HarvestRecord]:
    """OA.mg — 250M+ OA papers search engine. Uses OpenAlex under the hood for API."""
    # OA.mg doesn't have a public search API, but its data comes from OpenAlex.
    # We query OpenAlex with the OA filter (is_oa:true) to get OA.mg-equivalent results.
    params = {
        "search":   query,
        "per-page": min(max_results, 50),
        "filter":   "is_oa:true",
        "sort":     "relevance_score:desc",
    }
    try:
        data    = request_with_retry(OPENALEX_BASE, params, expect_json=True)
        results = data.get("results", []) or []
        out: List[HarvestRecord] = []
        for item in results:
            title    = item.get("display_name", "") or ""
            abstract = ""
            inv      = item.get("abstract_inverted_index") or {}
            if inv:
                max_pos = max((max(v) for v in inv.values() if v), default=0)
                words   = [""] * (max_pos + 1)
                for word, positions in inv.items():
                    for p in positions:
                        if 0 <= p < len(words):
                            words[p] = word
                abstract = " ".join(words)
            best_oa = item.get("best_oa_location") or {}
            authors = normalize_authors([
                a.get("author", {}).get("display_name", "")
                for a in item.get("authorships", [])
            ])
            year    = str(item.get("publication_year") or "")
            doi     = (item.get("doi") or "").replace("https://doi.org/", "")
            pdf_url = best_oa.get("pdf_url") or ""
            page_url= best_oa.get("landing_page_url") or item.get("id", "") or ""
            # Build OA.mg link from DOI
            oamg_url= f"https://oa.mg/{doi}" if doi else page_url
            out.append(record_from_basic(
                source="OA.mg", study_type="any", query=query, query_mode=query_mode,
                title=title, authors=authors, year=year, doi=doi,
                url=oamg_url, open_access_url=pdf_url or oamg_url, pdf_url=pdf_url,
                abstract=abstract, language="", document_type=item.get("type") or "",
                source_id=item.get("id", "") or "",
                raw=item, subjects=subjects,
                citation_count=item.get("cited_by_count", 0) or 0,
            ))
        return out
    except Exception:
        return []


def choose_sources() -> List[Tuple[str, Any]]:
    """Return ALL sources — no book/paper split. Every source is always active."""
    return [
        # ── Metadata & citation backbone ──────────────────────────────────────
        ("OpenAlex",         search_openalex),
        ("Crossref",         search_crossref),
        ("Semantic Scholar", search_semantic_scholar),
        # ── OA-first search engines ───────────────────────────────────────────
        ("OA.mg",            search_oamg),
        ("CORE",             search_core),
        ("DOAJ",             search_doaj),
        ("Paperity",         search_paperity),
        # ── Preprint & discipline repositories ────────────────────────────────
        ("arXiv",            search_arxiv),
        ("SSRN",             search_ssrn),
        # ── Biomedical full-text ──────────────────────────────────────────────
        ("PubMed",           search_pubmed),
        ("PMC Full-Text",    search_pmc_fulltext),
        ("Europe PMC",       search_europe_pmc),
        # ── Open repositories ─────────────────────────────────────────────────
        ("Zenodo",           search_zenodo),
        ("Figshare",         search_figshare),
        ("HAL",              search_hal),
        ("OpenAIRE",         search_openaire),
        # ── Books & general ───────────────────────────────────────────────────
        ("Google Books",     search_google_books),
        ("Internet Archive", search_internet_archive),
        ("Open Library",     search_open_library),
        # ── Theses ───────────────────────────────────────────────────────────
        ("EThOS/DART",       search_ethesis),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Harvest: Download helpers
# ─────────────────────────────────────────────────────────────────────────────

def inspect_remote_file(url: str) -> Tuple[str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return (resp.headers.get_content_type() or "").lower(), resp.geturl()
    except Exception:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return (resp.headers.get_content_type() or "").lower(), resp.geturl()


def choose_download_url(record: HarvestRecord) -> str:
    for candidate in [record.pdf_url, record.open_access_url]:
        if candidate and candidate.startswith("http"):
            return candidate
    return ""


def should_download(record: HarvestRecord) -> Tuple[bool, str]:
    url = choose_download_url(record)
    if not url:
        return False, "no_open_url"
    parsed = urllib.parse.urlparse(url)
    ext    = Path(parsed.path).suffix.lower()
    if ext and ext in ALLOWED_DOWNLOAD_EXTS:
        return True, "allowed_extension"
    try:
        ctype, final_url = inspect_remote_file(url)
        final_ext = Path(urllib.parse.urlparse(final_url).path).suffix.lower()
        if ctype in ALLOWED_CONTENT_TYPES:
            return True, f"allowed_content_type:{ctype}"
        if final_ext in ALLOWED_DOWNLOAD_EXTS:
            return True, f"allowed_final_ext:{final_ext}"
        return False, f"rejected:{ctype or 'unknown'}"
    except Exception as exc:
        return False, f"inspect_failed:{exc}"


def download_file(url: str, dest_dir: Path, title_hint: str) -> Tuple[str, str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as resp:
            ctype     = (resp.headers.get_content_type() or "").lower()
            final_url = resp.geturl()
            ext       = Path(urllib.parse.urlparse(final_url).path).suffix.lower()
            if ctype not in ALLOWED_CONTENT_TYPES and ext not in ALLOWED_DOWNLOAD_EXTS:
                return "", f"rejected_type:{ctype or 'unknown'}"
            if not ext:
                guessed = mimetypes.guess_extension(ctype or "") or ".bin"
                ext     = guessed if guessed in ALLOWED_DOWNLOAD_EXTS else ".bin"
            if ext not in ALLOWED_DOWNLOAD_EXTS:
                return "", f"rejected_ext:{ext}"
            filename = f"{safe_filename(title_hint)}__{short_hash(final_url)}{ext}"
            dest     = dest_dir / filename
            if dest.exists() and dest.stat().st_size > 0:
                return str(dest), "exists"
            with dest.open("wb") as f:
                shutil.copyfileobj(resp, f)
            if dest.stat().st_size == 0:
                return str(dest), "empty_file"
            return str(dest), "downloaded"
    except Exception as exc:
        return "", f"failed:{exc}"


def download_records(
    records: List[HarvestRecord],
    downloads_dir: Path,
    max_downloads: int = 100,
    on_progress: Optional[Callable[[int, int, str], None]] = None,
) -> Tuple[List[HarvestRecord], List[str]]:
    failures = []
    count    = 0
    seen:    set = set()
    downloadable = [r for r in records if choose_download_url(r)]
    total    = len(downloadable)

    for i, record in enumerate(records):
        if on_progress:
            on_progress(i, len(records), record.title[:60])

        if count >= max_downloads:
            record.file_status = "budget_exhausted"
            continue
        url = choose_download_url(record)
        if not url:
            record.file_status = "no_open_url"
            continue
        if url in seen:
            record.file_status = "duplicate_url"
            continue
        seen.add(url)
        ok, reason = should_download(record)
        if not ok:
            record.file_status = reason
            continue
        path, status = download_file(url, downloads_dir, record.title or record.source_id or "untitled")
        record.file_path   = path
        record.file_status = status
        if status in {"downloaded", "exists"}:
            count += 1
        elif any(status.startswith(p) for p in ("failed", "rejected", "empty")):
            failures.append(f"{record.source} | {record.title[:60]} | {url[:80]} | {status}")
        time.sleep(0.9)

    return records, failures


def manual_links(subjects: List[str]) -> List[str]:
    out = []
    for s in subjects:
        q = urllib.parse.quote_plus(f'"{s}"')
        out += [
            f"https://scholar.google.com/scholar?q={q}",
            f"https://books.google.com/books?q={q}",
            f"https://archive.org/search?query={q}",
            f"https://openlibrary.org/search?q={q}",
            f"https://www.semanticscholar.org/search?q={q}&sort=Relevance",
        ]
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Forge: Text extraction
# ─────────────────────────────────────────────────────────────────────────────

def read_plain_text(path: Path) -> str:
    for enc in ["utf-8", "utf-8-sig", "cp1253", "cp1252", "latin-1"]:
        try:
            return path.read_text(encoding=enc)
        except Exception:
            continue
    return path.read_bytes().decode("utf-8", errors="ignore")


def strip_html(raw: str) -> str:
    raw = re.sub(r"(?is)<script.*?>.*?</script>", " ", raw)
    raw = re.sub(r"(?is)<style.*?>.*?</style>",  " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    return clean_forge_text(raw)


def strip_rtf(raw: str) -> str:
    raw = re.sub(r"\\'[0-9a-fA-F]{2}", " ", raw)
    raw = re.sub(r"\\[a-zA-Z]+\d* ?", " ", raw)
    raw = re.sub(r"[{}]", " ", raw)
    return clean_forge_text(raw)


def clean_forge_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\x00", " ")
    text = html.unescape(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def read_pdf_pages(path: Path) -> List[str]:
    if not HAS_PYPDF:
        raise RuntimeError("pypdf is not installed. Run: pip install pypdf")
    reader = _PdfReader(str(path))
    pages: List[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        pages.append(clean_forge_text(text))
    return pages


def read_docx_text(path: Path) -> str:
    if not HAS_DOCX:
        raise RuntimeError("python-docx is not installed. Run: pip install python-docx")
    document = _docx.Document(str(path))
    paragraphs = [p.text for p in document.paragraphs if p.text and p.text.strip()]
    return clean_forge_text("\n".join(paragraphs))


def read_json_as_text(path: Path) -> str:
    raw = read_plain_text(path)
    try:
        obj = json.loads(raw)
        return clean_forge_text(json.dumps(obj, ensure_ascii=False, indent=2))
    except Exception:
        return clean_forge_text(raw)


def read_csv_as_text(path: Path) -> str:
    rows: List[str] = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.reader(f):
                rows.append(" | ".join(cell.strip() for cell in row))
    except Exception:
        with path.open("r", encoding="cp1252", errors="ignore", newline="") as f:
            for row in csv.reader(f):
                rows.append(" | ".join(cell.strip() for cell in row))
    return clean_forge_text("\n".join(rows))


def read_xml_as_text(path: Path) -> str:
    try:
        root  = ET.parse(path).getroot()
        texts = [t.strip() for t in root.itertext() if t and t.strip()]
        return clean_forge_text("\n".join(texts))
    except Exception:
        return clean_forge_text(read_plain_text(path))


def extract_text_by_type(path: Path) -> Tuple[Optional[str], Optional[List[str]], str]:
    """Returns (full_text, page_texts_or_None, notes)."""
    ext = path.suffix.lower()
    if ext == ".pdf":
        pages = read_pdf_pages(path)
        full  = clean_forge_text("\n\n".join(f"[Page {i+1}]\n{p}" for i, p in enumerate(pages) if p))
        return full, pages, ""
    if ext == ".docx":
        return read_docx_text(path), None, ""
    if ext in {".txt", ".md", ".markdown", ".rst", ".log", ".ini", ".cfg", ".conf", ".yaml", ".yml", ".tex"}:
        return clean_forge_text(read_plain_text(path)), None, ""
    if ext == ".json":
        return read_json_as_text(path), None, ""
    if ext in {".csv", ".tsv"}:
        return read_csv_as_text(path), None, ""
    if ext in {".html", ".htm"}:
        return strip_html(read_plain_text(path)), None, ""
    if ext == ".xml":
        return read_xml_as_text(path), None, ""
    if ext == ".rtf":
        return strip_rtf(read_plain_text(path)), None, ""
    if ext in TEXT_EXTENSIONS:
        return clean_forge_text(read_plain_text(path)), None, ""
    return None, None, "Unsupported extension"


# ─────────────────────────────────────────────────────────────────────────────
# Forge: Chunking
# ─────────────────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE_DEFAULT, overlap: int = CHUNK_OVERLAP_DEFAULT) -> List[str]:
    """
    Semantic-aware character chunking with paragraph-boundary snapping.
    Tries to cut on paragraph > sentence > line boundaries before hard cut.
    """
    text = clean_forge_text(text)
    if not text:
        return []
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be larger than overlap.")

    chunks: List[str] = []
    start  = 0
    length = len(text)

    while start < length:
        end   = min(start + chunk_size, length)
        chunk = text[start:end]

        if end < length:
            # Try to snap to a semantic boundary
            min_cut = int(chunk_size * 0.55)
            for sep in ["\n\n", ". ", ".\n", "\n", " "]:
                idx = chunk.rfind(sep, min_cut)
                if idx != -1:
                    end   = start + idx + len(sep)
                    chunk = text[start:end]
                    break

        chunk = chunk.strip()
        if chunk:
            chunks.append(chunk)
        if end >= length:
            break
        start = max(end - overlap, 0)

    return chunks


def iter_files(root: Path, include_hidden: bool = False) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        dirnames[:] = [
            d for d in dirnames
            if d not in DEFAULT_EXCLUDE_DIRS and (include_hidden or not d.startswith("."))
        ]
        for fname in filenames:
            if not include_hidden and fname.startswith("."):
                continue
            yield current / fname


# ─────────────────────────────────────────────────────────────────────────────
# Main workflow functions
# ─────────────────────────────────────────────────────────────────────────────

def run_harvest(
    subjects: List[str],
    output_dir: Path,
    max_results: int = 25,
    min_score: float = 10.0,
    max_downloads: int = 100,
    skip_download: bool = False,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Core harvest pipeline. Returns a summary dict."""
    dirs = ensure_dirs(output_dir)

    print_section("Harvest Configuration", "◉")
    print_summary_box("Search Parameters", {
        "Subjects":     ", ".join(subjects),
        "Output dir":   str(output_dir),
        "Min score":    min_score,
        "Max results":  f"{max_results} per source per query",
        "Max downloads": "disabled" if skip_download else max_downloads,
        "Sources":      ", ".join(n for n, _ in choose_sources()),
    })

    all_raw:    List[HarvestRecord]              = []
    per_source: Dict[str, List[HarvestRecord]]  = {}
    errors:     List[str]                        = []

    sources = choose_sources()
    total_queries = len(subjects) * 2 * len(sources)  # 2 query forms

    print_section("Searching Academic Sources", "⌕")

    pb = ProgressBar(total_queries, "queries", width=38)
    query_count = 0

    for subject in subjects:
        forms = build_query_forms(subject)
        for q, mode in forms:
            icon = "exact" if mode == "exact_phrase" else "broad"
            for sname, fn in sources:
                pb.update(0)
                try:
                    records = fn(q, mode, subjects, max_results)
                    per_source.setdefault(sname, []).extend(records)
                    all_raw.extend(records)
                    if verbose:
                        pb.finish("")
                        print_step(f"{sname:<20} [{icon}] {subject[:40]}", f"{len(records)} records", "search")
                        pb = ProgressBar(total_queries - query_count - 1, "queries remaining", 38)
                    time.sleep(0.7)
                except Exception as exc:
                    msg = f"{subject} | {mode} | {sname} | {exc}"
                    errors.append(msg)
                    if verbose:
                        pb.finish("")
                        print_step(f"{sname:<20} [{icon}] {subject[:40]}", str(exc)[:60], "error")
                        pb = ProgressBar(total_queries - query_count - 1, "queries remaining", 38)
                query_count += 1
                pb.update(1)

    pb.finish(f"{format_number(len(all_raw))} records fetched")

    print_section("Processing & Deduplication", "◈")
    spinner = Spinner("Scoring relevance and deduplicating…").start()
    filtered = filter_records(all_raw, min_score)
    filtered = dedupe_records(filtered)
    filtered = sorted(filtered, key=lambda r: (-r.relevance_score, -(int(r.year) if r.year.isdigit() else 0), r.title.lower()))
    spinner.stop(f"  {_c('✓', C.BRIGHT_GREEN)} {format_number(len(filtered))} relevant records after filtering")

    print_kv("Raw records", format_number(len(all_raw)))
    print_kv("After filtering (score ≥ {:.0f})".format(min_score), format_number(len(filtered)))
    print_kv("Unique sources", len({r.source for r in filtered}))

    if not skip_download:
        print_section("Downloading Open-Access Documents", "↓")
        dl_progress = ProgressBar(len(filtered), "files", width=38)

        def on_dl(i: int, total: int, title: str) -> None:
            dl_progress.set(i)

        filtered, failures = download_records(filtered, dirs["downloads"], max_downloads, on_progress=on_dl)
        dl_progress.finish()

        downloaded = sum(1 for r in filtered if r.file_status in {"downloaded", "exists"})
        print_kv("Documents downloaded", f"{downloaded} / {len(filtered)}")
        if failures:
            print_kv("Failed downloads", len(failures), key_color=C.YELLOW)
    else:
        failures = []
        print_step("Download skipped", "(--no-download flag)", "skip")

    print_section("Saving Outputs", "⊙")
    spinner = Spinner("Writing metadata files…").start()

    for sname, recs in per_source.items():
        fname = safe_filename(sname.lower().replace(" ", "_")) + ".jsonl"
        write_jsonl(dirs["metadata"] / fname, [asdict(r) for r in recs])

    write_jsonl(dirs["metadata"] / "raw_records.jsonl",      [asdict(r) for r in all_raw])
    write_jsonl(dirs["metadata"] / "filtered_records.jsonl", [asdict(r) for r in filtered])
    write_csv(dirs["metadata"] / "filtered_records.csv",     filtered)

    with (dirs["reports"] / "manual_search_links.txt").open("w", encoding="utf-8") as f:
        for link in manual_links(subjects):
            f.write(link + "\n")
    with (dirs["reports"] / "errors.txt").open("w", encoding="utf-8") as f:
        for e in errors:
            f.write(e + "\n")
    with (dirs["reports"] / "failed_downloads.txt").open("w", encoding="utf-8") as f:
        for line in failures:
            f.write(line + "\n")

    summary: Dict[str, Any] = {
        "mode":                "harvest",
        "subjects":            subjects,
        "min_score":           min_score,
        "output_dir":          str(output_dir),
        "raw_records":         len(all_raw),
        "filtered_records":    len(filtered),
        "downloaded":          sum(1 for r in filtered if r.file_status in {"downloaded", "exists"}),
        "no_open_url":         sum(1 for r in filtered if r.file_status == "no_open_url"),
        "errors":              len(errors),
        "failed_downloads":    len(failures),
        "timestamp":           datetime.now().isoformat(),
    }
    (dirs["reports"] / "harvest_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    spinner.stop(f"  {_c('✓', C.BRIGHT_GREEN)} All metadata saved")

    return {**summary, "_dirs": dirs, "_filtered": filtered}


def run_forge(
    source_dir: Path,
    output_dir: Path,
    chunk_size: int = CHUNK_SIZE_DEFAULT,
    overlap: int = CHUNK_OVERLAP_DEFAULT,
    include_extensions: Optional[List[str]] = None,
    include_hidden: bool = False,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Core forge pipeline. Returns a summary dict."""
    output_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path   = output_dir / "knowledge_dataset.jsonl"
    csv_path     = output_dir / "knowledge_sources.csv"
    md_path      = output_dir / "knowledge_corpus.md"
    summary_path = output_dir / "knowledge_summary.json"

    include_set: Optional[set] = None
    if include_extensions:
        include_set = {(ext if ext.startswith(".") else f".{ext}").lower() for ext in include_extensions}

    # First pass: count files
    print_section("Scanning Source Folder", "⌖")
    spinner = Spinner("Discovering files…").start()
    all_paths = list(iter_files(source_dir, include_hidden=include_hidden))
    target_paths = [
        p for p in all_paths
        if not p.is_dir() and (
            (include_set and p.suffix.lower() in include_set) or
            (not include_set and (p.suffix.lower() in SUPPORTED_EXTENSIONS or p.suffix.lower() in TEXT_EXTENSIONS))
        )
    ]
    spinner.stop(f"  {_c('✓', C.BRIGHT_GREEN)} {len(target_paths)} files to process")

    if not target_paths:
        print_step("No supported files found in", str(source_dir), "warn")
        return {"mode": "forge", "source_dir": str(source_dir), "files_seen": 0, "total_chunks": 0}

    # Extension breakdown
    ext_counts: Dict[str, int] = {}
    for p in target_paths:
        ext_counts[p.suffix.lower()] = ext_counts.get(p.suffix.lower(), 0) + 1
    rows = [[ext, str(count)] for ext, count in sorted(ext_counts.items(), key=lambda x: -x[1])]
    print_table(["Extension", "Files"], rows, [14, 10])

    print_section("Extracting & Chunking Text", "◎")
    pb = ProgressBar(len(target_paths), "files", width=38)

    file_records:  List[ForgeFileRecord] = []
    total_chunks   = 0
    total_chars    = 0
    warnings:      List[str] = []

    with jsonl_path.open("w", encoding="utf-8") as jf, \
         md_path.open("w", encoding="utf-8") as mf:

        mf.write("# Unified Knowledge Corpus\n\n")
        mf.write(f"Source folder: `{source_dir}`\n")
        mf.write(f"Generated: {datetime.now().isoformat()}\n\n")

        for path in target_paths:
            pb.update(0)
            ext           = path.suffix.lower()
            relative_path = str(path.relative_to(source_dir))
            size_bytes    = path.stat().st_size

            try:
                full_text, page_texts, notes = extract_text_by_type(path)
                full_text = clean_forge_text(full_text or "")

                if not full_text:
                    file_records.append(ForgeFileRecord(
                        source_path=str(path), relative_path=relative_path,
                        file_name=path.name, extension=ext, size_bytes=size_bytes,
                        status="skipped", extracted_characters=0, chunks=0,
                        notes=notes or "No extractable text found.",
                    ))
                    pb.update(1)
                    continue

                file_chunk_count = 0
                lang_hint        = detect_language_hint(full_text)

                if ext == ".pdf" and page_texts:
                    for page_num, page_text in enumerate(page_texts, start=1):
                        page_text = clean_forge_text(page_text)
                        if not page_text:
                            continue
                        for ci, chunk in enumerate(chunk_text(page_text, chunk_size, overlap), start=1):
                            payload = {
                                "source_path": str(path), "relative_path": relative_path,
                                "file_name": path.name, "extension": ext,
                                "page": page_num, "chunk_index": ci,
                                "text": chunk, "char_count": len(chunk),
                                "word_count": len(chunk.split()),
                                "text_sha256": sha256_text(chunk),
                                "language_hint": lang_hint,
                            }
                            jf.write(json.dumps(payload, ensure_ascii=False) + "\n")
                            file_chunk_count += 1
                            total_chunks += 1
                else:
                    for ci, chunk in enumerate(chunk_text(full_text, chunk_size, overlap), start=1):
                        payload = {
                            "source_path": str(path), "relative_path": relative_path,
                            "file_name": path.name, "extension": ext,
                            "page": None, "chunk_index": ci,
                            "text": chunk, "char_count": len(chunk),
                            "word_count": len(chunk.split()),
                            "text_sha256": sha256_text(chunk),
                            "language_hint": lang_hint,
                        }
                        jf.write(json.dumps(payload, ensure_ascii=False) + "\n")
                        file_chunk_count += 1
                        total_chunks += 1

                mf.write(f"## {relative_path}\n\n")
                mf.write(full_text + "\n\n---\n\n")
                total_chars += len(full_text)

                file_records.append(ForgeFileRecord(
                    source_path=str(path), relative_path=relative_path,
                    file_name=path.name, extension=ext, size_bytes=size_bytes,
                    status="ok", extracted_characters=len(full_text),
                    chunks=file_chunk_count, notes=notes,
                ))
                if verbose:
                    pb.finish("")
                    print_step(path.name[:60], f"{file_chunk_count} chunks", "ok")
                    pb = ProgressBar(len(target_paths) - len(file_records), "remaining", 38)

            except Exception as exc:
                warnings.append(f"{relative_path}: {exc}")
                file_records.append(ForgeFileRecord(
                    source_path=str(path), relative_path=relative_path,
                    file_name=path.name, extension=ext, size_bytes=size_bytes,
                    status="error", extracted_characters=0, chunks=0, notes=str(exc),
                ))
                if verbose:
                    pb.finish("")
                    print_step(path.name[:60], str(exc)[:60], "error")
                    pb = ProgressBar(len(target_paths) - len(file_records), "remaining", 38)

            pb.update(1)

    pb.finish(f"{format_number(total_chunks)} chunks produced")

    # Write CSV
    if file_records:
        with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(asdict(file_records[0]).keys()))
            writer.writeheader()
            for r in file_records:
                writer.writerow(asdict(r))

    summary: Dict[str, Any] = {
        "mode":             "forge",
        "source_dir":       str(source_dir),
        "output_dir":       str(output_dir),
        "files_seen":       len(file_records),
        "files_ok":         sum(1 for r in file_records if r.status == "ok"),
        "files_skipped":    sum(1 for r in file_records if r.status == "skipped"),
        "files_error":      sum(1 for r in file_records if r.status == "error"),
        "total_chunks":     total_chunks,
        "total_characters": total_chars,
        "chunk_size":       chunk_size,
        "overlap":          overlap,
        "warnings":         warnings,
        "supported_extensions": sorted(list(SUPPORTED_EXTENSIONS)),
        "timestamp":        datetime.now().isoformat(),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    return summary


# ─────────────────────────────────────────────────────────────────────────────
# Interactive prompts for each mode
# ─────────────────────────────────────────────────────────────────────────────

def interactive_harvest(args: argparse.Namespace) -> int:
    print_section("Harvest Mode  —  Academic Source Search & Download", "◉")
    print(_c("  Search 7 academic APIs, score by relevance, and download open-access documents.", C.DIM))
    print(_c("  At any prompt, press  h  + Enter  to get detailed help for that field.\n", C.BRIGHT_CYAN))

    # Study type
    print(_c("  " + "─" * 60, C.DIM))
    print(_c("  STEP 1 of 3  —  What kind of material?", C.BRIGHT_WHITE))
    print(_c("  " + "─" * 60, C.DIM))
    # Subjects
    print()
    print(_c("  " + "─" * 60, C.DIM))
    print(_c("  STEP 2 of 3  —  What topics?", C.BRIGHT_WHITE))
    print(_c("  " + "─" * 60, C.DIM))
    subject_line = prompt_with_help(
        "Subjects / topics (comma-separated)",
        field_key="subjects",
        hint="Example: quantum mechanics, wave-particle duality, quantum entanglement",
        validator=lambda s: len(s.strip()) > 0,
    )
    subjects = parse_subjects(subject_line)
    if not subjects:
        print_step("No valid subjects entered.", status="error")
        return 1

    # Output dir
    print()
    print(_c("  " + "─" * 60, C.DIM))
    print(_c("  STEP 3 of 3  —  Where to save?", C.BRIGHT_WHITE))
    print(_c("  " + "─" * 60, C.DIM))
    default_out    = f"./scholarforge_harvest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir_raw = prompt_text("Output folder", default_out)
    output_dir     = Path(output_dir_raw).expanduser().resolve()

    # Advanced options
    print()
    if confirm("Configure advanced options?  (max results, score threshold, downloads)", default=False):
        print(_c("\n  Advanced options — press h at any prompt for detailed help.\n", C.DIM))
        max_results   = prompt_int_with_help("Max raw results per source per query", "max_results", 25, 5, 200)
        raw_score     = prompt_with_help("Minimum relevance score", "min_score", "10.0")
        try:
            min_score = float(raw_score)
        except ValueError:
            min_score = default_score
        max_downloads = prompt_int_with_help("Max documents to download", "max_downloads", 100, 0, 5000)
        skip_download = not confirm("Download open-access documents?", default=True)
        verbose       = confirm("Verbose output (per-source details)?", default=False)
    else:
        max_results   = 25
        min_score     = 10.0
        max_downloads = 100
        skip_download = False
        verbose       = False

    print()
    if not confirm("Ready to start harvest?", default=True):
        print_step("Harvest cancelled.", status="skip")
        return 0

    result = run_harvest(
        subjects=subjects, output_dir=output_dir,
        max_results=max_results, min_score=min_score, max_downloads=max_downloads,
        skip_download=skip_download, verbose=verbose,
    )

    _print_harvest_final(result)
    return 0


def interactive_forge(args: argparse.Namespace) -> int:
    print_section("Forge Mode  —  Knowledge Dataset Builder", "◎")
    print(_c("  Extract, clean, and chunk documents into an AI-ready knowledge dataset.", C.DIM))
    print(_c("  At any prompt, press  h  + Enter  to get detailed help for that field.\n", C.BRIGHT_CYAN))

    # Source dir — from args or prompt
    if args.source_dir:
        source_dir = Path(args.source_dir).expanduser().resolve()
    else:
        source_raw = prompt_text(
            "Source folder to scan",
            hint="All PDFs, DOCX, TXT, MD, HTML, XML etc. will be processed recursively.",
            validator=lambda s: Path(s).expanduser().exists(),
        )
        source_dir = Path(source_raw).expanduser().resolve()

    if not source_dir.exists() or not source_dir.is_dir():
        print_step(f"Folder not found: {source_dir}", status="error")
        return 1

    default_out = str(source_dir / "knowledge_export")
    output_dir_raw = prompt_text("Output folder", default_out)
    output_dir = Path(output_dir_raw).expanduser().resolve()

    if confirm("Configure advanced options?  (chunk size, overlap, extensions)", default=False):
        print(_c("\n  Advanced options — press h at any prompt for detailed help.\n", C.DIM))
        chunk_size     = prompt_int_with_help("Characters per chunk", "chunk_size", CHUNK_SIZE_DEFAULT, 500, 50000)
        overlap        = prompt_int_with_help("Overlap between chunks (chars)", "overlap", CHUNK_OVERLAP_DEFAULT, 0, 5000)
        include_hidden = confirm("Include hidden files/folders?", default=False)
        ext_raw        = prompt_text(
            "Limit to specific extensions? (space-separated, e.g. pdf txt docx)",
            default="",
        )
        include_ext = ext_raw.split() if ext_raw.strip() else None
        verbose     = confirm("Verbose output (per-file details)?", default=False)
    else:
        chunk_size     = CHUNK_SIZE_DEFAULT
        overlap        = CHUNK_OVERLAP_DEFAULT
        include_hidden = False
        include_ext    = None
        verbose        = False

    print()
    if not confirm("Ready to start forging?", default=True):
        print_step("Forge cancelled.", status="skip")
        return 0

    summary = run_forge(
        source_dir=source_dir, output_dir=output_dir,
        chunk_size=chunk_size, overlap=overlap,
        include_extensions=include_ext, include_hidden=include_hidden,
        verbose=verbose,
    )

    _print_forge_final(summary, output_dir)
    return 0


def interactive_pipeline(args: argparse.Namespace) -> int:
    """Harvest → Forge in one seamless pipeline."""
    print_section("Pipeline Mode  —  Harvest → Forge", "⚡")
    print(_c("  Stage 1: Search academic APIs and download open-access documents.", C.DIM))
    print(_c("  Stage 2: Extract, chunk, and export a knowledge dataset from downloaded files.", C.DIM))
    print(_c("  At any prompt, press  h  + Enter  to get detailed help for that field.\n", C.BRIGHT_CYAN))

    # ── STAGE 1 CONFIG ────────────────────────────────────────────────────────
    print(_c("  " + "─" * 60, C.DIM))
    print(_c("  STAGE 1 of 2  —  Harvest Settings", C.BRIGHT_MAGENTA, C.BOLD))
    print(_c("  " + "─" * 60, C.DIM))

    # Subjects
    subject_line = prompt_with_help(
        "Subjects / topics (comma-separated)",
        field_key="subjects",
        hint="Example: quantum computing, qubit error correction, superconducting qubits",
        validator=lambda s: len(s.strip()) > 0,
    )
    subjects = parse_subjects(subject_line)
    if not subjects:
        print_step("No valid subjects.", status="error")
        return 1

    # Output root
    default_out    = f"./scholarforge_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir_raw = prompt_text("Pipeline root folder", default_out)
    output_dir     = Path(output_dir_raw).expanduser().resolve()
    harvest_dir    = output_dir / "harvest"
    forge_dir      = output_dir / "knowledge_export"

    # Harvest advanced options
    print()
    if confirm("Configure harvest options?  (max results, score threshold, downloads)", default=False):
        print(_c("\n  Harvest options — press h at any prompt for detailed help.\n", C.DIM))
        max_results   = prompt_int_with_help("Max raw results per source per query", "max_results", 25, 5, 200)
        raw_score     = prompt_with_help("Minimum relevance score", "min_score", "10.0")
        try:
            min_score = float(raw_score)
        except ValueError:
            min_score = default_score
        max_downloads = prompt_int_with_help("Max documents to download", "max_downloads", 100, 0, 5000)
        skip_download = not confirm("Download open-access documents?", default=True)
        harvest_verbose = confirm("Verbose harvest output?", default=False)
    else:
        max_results     = 25
        min_score       = 10.0
        max_downloads   = 100
        skip_download   = False
        harvest_verbose = False

    # ── STAGE 2 CONFIG ────────────────────────────────────────────────────────
    print()
    print(_c("  " + "─" * 60, C.DIM))
    print(_c("  STAGE 2 of 2  —  Forge Settings", C.BRIGHT_CYAN, C.BOLD))
    print(_c("  " + "─" * 60, C.DIM))

    if confirm("Configure forge options?  (chunk size, overlap)", default=False):
        print(_c("\n  Forge options — press h at any prompt for detailed help.\n", C.DIM))
        chunk_size    = prompt_int_with_help("Characters per chunk", "chunk_size", CHUNK_SIZE_DEFAULT, 500, 50000)
        overlap       = prompt_int_with_help("Overlap between chunks (chars)", "overlap", CHUNK_OVERLAP_DEFAULT, 0, 5000)
        forge_verbose = confirm("Verbose forge output?", default=False)
    else:
        chunk_size    = CHUNK_SIZE_DEFAULT
        overlap       = CHUNK_OVERLAP_DEFAULT
        forge_verbose = False

    # ── CONFIRM ───────────────────────────────────────────────────────────────
    print()
    print_summary_box("Pipeline Preview", {
        "Subjects":       ", ".join(subjects),
        "Output root":    str(output_dir),
        "Max results":    f"{max_results} per source per query",
        "Min score":      min_score,
        "Max downloads":  "disabled" if skip_download else max_downloads,
        "Chunk size":     chunk_size,
        "Overlap":        overlap,
        "Sources":        ", ".join(n for n, _ in choose_sources()),
    })

    print()
    if not confirm("Start pipeline (harvest → forge)?", default=True):
        print_step("Pipeline cancelled.", status="skip")
        return 0

    # ── RUN STAGE 1: HARVEST ─────────────────────────────────────────────────
    print()
    print(_c("  ⚡ Stage 1 / 2  —  Harvesting…", C.BRIGHT_MAGENTA, C.BOLD))
    harvest_result = run_harvest(
        subjects=subjects, output_dir=harvest_dir,
        max_results=max_results, min_score=min_score,
        max_downloads=max_downloads, skip_download=skip_download,
        verbose=harvest_verbose,
    )
    _print_harvest_final(harvest_result)

    downloads_dir = harvest_result["_dirs"]["downloads"]
    dl_count = sum(1 for _ in downloads_dir.iterdir() if _.is_file()) if downloads_dir.exists() else 0

    if dl_count == 0:
        print_step("No files downloaded — forge stage skipped.", status="warn")
        print_step("Tip: lower --min-score or raise --max-results and re-run.", status="info")
        return 0

    # ── RUN STAGE 2: FORGE ───────────────────────────────────────────────────
    print()
    print(_c(f"  ⚡ Stage 2 / 2  —  Forging {dl_count} downloaded files into knowledge dataset…", C.BRIGHT_CYAN, C.BOLD))
    forge_summary = run_forge(
        source_dir=downloads_dir, output_dir=forge_dir,
        chunk_size=chunk_size, overlap=overlap,
        verbose=forge_verbose,
    )
    _print_forge_final(forge_summary, forge_dir)

    # ── FINAL SUMMARY ─────────────────────────────────────────────────────────
    print_section("Pipeline Complete", "★")
    print_summary_box("Pipeline Summary", {
        "Subjects searched":    ", ".join(subjects),
        "Records harvested":    format_number(harvest_result.get("filtered_records", 0)),
        "Documents downloaded": format_number(harvest_result.get("downloaded", 0)),
        "Knowledge chunks":     format_number(forge_summary.get("total_chunks", 0)),
        "Total characters":     format_number(forge_summary.get("total_characters", 0)),
        "Output root":          str(output_dir),
        "Downloads":            str(harvest_dir / "downloads"),
        "Knowledge dataset":    str(forge_dir / "knowledge_dataset.jsonl"),
    })
    return 0


def _print_harvest_final(result: Dict[str, Any]) -> None:
    print_section("Harvest Complete", "★")
    dirs = result.get("_dirs", {})
    print_summary_box("Results", {
        "Raw records fetched":  format_number(result.get("raw_records", 0)),
        "Relevant (filtered)":  format_number(result.get("filtered_records", 0)),
        "Documents downloaded": format_number(result.get("downloaded", 0)),
        "No open URL":          format_number(result.get("no_open_url", 0)),
        "API errors":           result.get("errors", 0),
        "Failed downloads":     result.get("failed_downloads", 0),
    })
    print()
    if dirs:
        print_step("Downloads:",          str(dirs.get("downloads", "")), "ok")
        print_step("Metadata (JSONL/CSV):", str(dirs.get("metadata", "")), "ok")
        print_step("Reports:",             str(dirs.get("reports", "")), "ok")

    filtered = result.get("_filtered", [])
    if filtered:
        print()
        print_section("Top 10 Results by Relevance Score", "◆")
        rows = []
        for r in filtered[:10]:
            year    = r.year or "—"
            title   = r.title[:42] if r.title else "—"
            authors = r.authors[:28] if r.authors else "—"
            score   = f"{r.relevance_score:.1f}"
            rows.append([title, authors, year, r.source[:16], score])
        print_table(["Title", "Authors", "Year", "Source", "Score"],
                    rows, [44, 30, 6, 18, 7])


def _print_forge_final(summary: Dict[str, Any], output_dir: Path) -> None:
    print_section("Forge Complete", "★")
    print_summary_box("Results", {
        "Files processed":  summary.get("files_ok", 0),
        "Files skipped":    summary.get("files_skipped", 0),
        "Files with errors": summary.get("files_error", 0),
        "Total chunks":     format_number(summary.get("total_chunks", 0)),
        "Total characters": format_number(summary.get("total_characters", 0)),
    })
    print()
    print_step("knowledge_dataset.jsonl", str(output_dir / "knowledge_dataset.jsonl"), "ok")
    print_step("knowledge_sources.csv",   str(output_dir / "knowledge_sources.csv"),   "ok")
    print_step("knowledge_corpus.md",     str(output_dir / "knowledge_corpus.md"),     "ok")
    print_step("knowledge_summary.json",  str(output_dir / "knowledge_summary.json"),  "ok")
    if summary.get("warnings"):
        print()
        print_section("Warnings", "!")
        for w in summary["warnings"][:10]:
            print_step(w[:100], status="warn")


# ─────────────────────────────────────────────────────────────────────────────
# CLI argument parsing
# ─────────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="scholarforge",
        description="ScholarForge — Academic Research & Knowledge Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
MODES
  harvest           Interactive wizard: search academic APIs, download documents
  forge [DIR]       Extract & chunk all documents in DIR into AI dataset
  pipeline          Run harvest then forge in sequence

EXAMPLES
  python scholarforge.py harvest
  python scholarforge.py forge /path/to/my/books
  python scholarforge.py forge /path/to/books -o /path/to/export --chunk-size 4000
  python scholarforge.py pipeline

  # Non-interactive (all flags provided):
  python scholarforge.py harvest \\
      --subjects "quantum mechanics, wave-particle duality" \\
      --study-type book \\
      --output ./output \\
      --max-results 30 \\
      --min-score 10

  python scholarforge.py forge /books \\
      --output /export \\
      --chunk-size 4000 \\
      --overlap 400 \\
      --extensions pdf txt docx

SOURCES (Harvest)
  OpenAlex · Crossref · Google Books · Internet Archive · Open Library
  Semantic Scholar · PubMed (scientific paper mode only)

FORMATS (Forge)
  PDF · DOCX · TXT · Markdown · HTML · XML · JSON · CSV · TSV · RTF · YAML · TeX
        """,
    )

    try:
        from scholarforge import __version__ as _SF_VERSION
    except Exception:
        _SF_VERSION = "3.4.0-dev"
    p.add_argument("--version", action="version", version=f"ScholarForge {_SF_VERSION}")
    p.add_argument("--no-banner", action="store_true", help="Suppress the ASCII banner")
    p.add_argument("--no-color",  action="store_true", help="Disable ANSI color output")
    p.add_argument("--verbose", "-v", action="store_true", help="Verbose per-item output")
    p.add_argument("--deps", action="store_true", help="Show dependency status and exit")
    p.add_argument(
        "--explain", metavar="FIELD",
        help=(
            "Print detailed help for a specific field and exit. "
            "Fields: subjects, max_results, min_score, max_downloads, chunk_size, overlap"
        ),
    )

    subparsers = p.add_subparsers(dest="mode", metavar="MODE")
    subparsers.required = False

    # ── harvest ───────────────────────────────────────────────────────────────
    h = subparsers.add_parser("harvest", help="Search academic APIs and download documents")
    h.add_argument("--subjects",   "-s",  metavar="SUBJECTS",  help="Comma-separated subject list")
    h.add_argument("--output",     "-o",  metavar="DIR",  help="Output directory")
    h.add_argument("--max-results", type=int, default=25, metavar="N")
    h.add_argument("--min-score",   type=float, default=None)
    h.add_argument("--max-downloads", type=int, default=100, metavar="N")
    h.add_argument("--no-download", action="store_true", help="Skip downloading files")

    # ── forge ─────────────────────────────────────────────────────────────────
    f = subparsers.add_parser("forge", help="Build AI-ready knowledge dataset from a document folder")
    f.add_argument("source_dir", nargs="?", metavar="DIR",    help="Folder to scan")
    f.add_argument("--output",   "-o",      metavar="DIR",    help="Output directory")
    f.add_argument("--chunk-size",  type=int, default=CHUNK_SIZE_DEFAULT)
    f.add_argument("--overlap",     type=int, default=CHUNK_OVERLAP_DEFAULT)
    f.add_argument("--extensions",  nargs="*", metavar="EXT", help="Whitelist of extensions, e.g. pdf txt")
    f.add_argument("--include-hidden", action="store_true")

    # ── pipeline ──────────────────────────────────────────────────────────────
    pl = subparsers.add_parser("pipeline", help="Harvest then forge in one command")
    pl.add_argument("--subjects",    "-s", metavar="SUBJECTS")
    pl.add_argument("--output",      "-o", metavar="DIR")

    return p


# ─────────────────────────────────────────────────────────────────────────────
# Non-interactive mode runners (when all flags are provided via CLI)
# ─────────────────────────────────────────────────────────────────────────────

def cli_harvest(args: argparse.Namespace) -> int:
    """Run harvest without interactive prompts if all required args are given."""
    subjects = parse_subjects(args.subjects) if args.subjects else []

    # Fall back to interactive if required args are missing
    if not subjects or not args.output:
        return interactive_harvest(args)

    output_dir = Path(args.output).expanduser().resolve()
    min_score  = args.min_score if args.min_score is not None else 10.0

    result = run_harvest(
        subjects=subjects, output_dir=output_dir,
        max_results=args.max_results, min_score=min_score,
        max_downloads=args.max_downloads, skip_download=args.no_download,
        verbose=args.verbose,
    )
    _print_harvest_final(result)
    return 0


def cli_forge(args: argparse.Namespace) -> int:
    """Run forge without interactive prompts if all required args are given."""
    if not args.source_dir:
        return interactive_forge(args)

    source_dir = Path(args.source_dir).expanduser().resolve()
    if not source_dir.exists():
        print_step(f"Source folder not found: {source_dir}", status="error")
        return 1

    output_dir = Path(args.output).expanduser().resolve() if args.output else source_dir / "knowledge_export"

    summary = run_forge(
        source_dir=source_dir, output_dir=output_dir,
        chunk_size=args.chunk_size, overlap=args.overlap,
        include_extensions=args.extensions,
        include_hidden=args.include_hidden,
        verbose=args.verbose,
    )
    _print_forge_final(summary, output_dir)
    return 0


def cli_pipeline(args: argparse.Namespace) -> int:
    subjects = parse_subjects(args.subjects) if args.subjects else []
    if not subjects or not args.output:
        return interactive_pipeline(args)

    output_dir = Path(args.output).expanduser().resolve()
    harvest_dir = output_dir / "harvest"
    forge_dir   = output_dir / "knowledge_export"

    harvest_result = run_harvest(
        subjects=subjects, output_dir=harvest_dir,
        max_results=25, min_score=10.0, max_downloads=100,
    )
    _print_harvest_final(harvest_result)

    downloads_dir = harvest_result["_dirs"]["downloads"]
    dl_count = sum(1 for _ in downloads_dir.iterdir() if _.is_file()) if downloads_dir.exists() else 0
    if dl_count == 0:
        print_step("No files downloaded; forge stage skipped.", status="warn")
        return 0

    forge_summary = run_forge(
        source_dir=downloads_dir, output_dir=forge_dir,
        chunk_size=CHUNK_SIZE_DEFAULT, overlap=CHUNK_OVERLAP_DEFAULT,
    )
    _print_forge_final(forge_summary, forge_dir)
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = build_parser()
    args   = parser.parse_args()

    # Global flags
    if args.no_color:
        # Monkey-patch C to empty strings
        for attr in dir(C):
            if not attr.startswith("_"):
                setattr(C, attr, "")

    if not args.no_banner:
        print_banner()

    if args.deps:
        print_dependency_status()
        return 0

    if getattr(args, "explain", None):
        print_field_help(args.explain)
        return 0

    if not args.mode:
        # Interactive main menu
        print_section("Main Menu", "◆")
        print(_c("  Choose a mode to continue:\n", C.DIM))
        print(f"    {_c('[1]', C.BRIGHT_CYAN)} {_c('harvest', C.BOLD)}   Search academic APIs and download open-access documents")
        print(f"    {_c('[2]', C.BRIGHT_CYAN)} {_c('forge', C.BOLD)}     Build AI knowledge dataset from a folder of documents")
        print(f"    {_c('[3]', C.BRIGHT_CYAN)} {_c('pipeline', C.BOLD)}  Harvest + forge in sequence")
        print(f"    {_c('[h]', C.BRIGHT_YELLOW)} Field reference  — explain any option in detail")
        print(f"    {_c('[q]', C.DIM)} Quit\n")
        while True:
            choice = input(f"  {_c('→', C.BRIGHT_YELLOW)} Your choice [1/2/3/h/q]: ").strip().lower()
            if choice in ("1", "harvest"):
                args.mode = "harvest"
                for attr in ["subjects", "study_type", "output", "max_results", "min_score", "max_downloads", "no_download"]:
                    if not hasattr(args, attr):
                        setattr(args, attr, None if attr not in ("max_results", "max_downloads") else 25)
                return interactive_harvest(args)
            elif choice in ("2", "forge"):
                args.mode = "forge"
                for attr in ["source_dir", "output", "chunk_size", "overlap", "extensions", "include_hidden"]:
                    if not hasattr(args, attr):
                        setattr(args, attr, None)
                if not hasattr(args, "chunk_size") or args.chunk_size is None:
                    args.chunk_size = CHUNK_SIZE_DEFAULT
                if not hasattr(args, "overlap") or args.overlap is None:
                    args.overlap = CHUNK_OVERLAP_DEFAULT
                return interactive_forge(args)
            elif choice in ("3", "pipeline"):
                args.mode = "pipeline"
                for attr in ["subjects", "study_type", "output"]:
                    if not hasattr(args, attr):
                        setattr(args, attr, None)
                return interactive_pipeline(args)
            elif choice in ("h", "help", "?"):
                print()
                print(_c("  Available field explanations  (run: python scholarforge.py --explain FIELD)\n", C.BRIGHT_YELLOW))
                fields = [
                    ("study_type",     "What 'book' vs 'paper' mode means and which sources are used"),
                    ("subjects",       "How to write good subject queries and what happens internally"),
                    ("max_results",    "Trade-off between speed and completeness — with time estimates"),
                    ("min_score",      "How the relevance scoring algorithm works, with score presets"),
                    ("max_downloads",  "Controls on the automatic file download stage"),
                    ("chunk_size",     "How large each text chunk is in the Forge output dataset"),
                    ("overlap",        "How much text repeats between consecutive chunks"),
                ]
                for fname, desc in fields:
                    print(f"    {_c(fname.ljust(18), C.BRIGHT_CYAN)}  {_c(desc, C.DIM)}")
                print()
                print(_c("  Inside any mode, type  h  at any prompt for context-specific help.\n", C.DIM))
            elif choice in ("q", "quit", "exit"):
                print(_c("  Goodbye.\n", C.DIM))
                return 0
            else:
                print(f"  {_c('✗', C.RED)} Please enter 1, 2, 3, h, or q.")

    dispatch = {
        "harvest":  lambda: cli_harvest(args),
        "forge":    lambda: cli_forge(args),
        "pipeline": lambda: cli_pipeline(args),
    }
    handler = dispatch.get(args.mode)
    if handler:
        return handler()

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
