#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ScholarForge — compatibility shim.

Keeps the historical invocation `python scholarforge.py ...` working while
the real code lives in the `scholarforge/` package. Prefer `python -m scholarforge`
in new scripts.
"""

from __future__ import annotations

import os
import sys

# Ensure the package directory (which sits alongside this file) is importable
# even when the script is run from elsewhere.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from scholarforge.app.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
