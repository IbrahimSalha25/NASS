"""
Root launch entry point for NASS (نَصّ | Smart Document & OCR Extractor).
Delegates execution to nass.main.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on sys.path for direct python main.py invocation
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from nass.main import main


if __name__ == "__main__":
    sys.exit(main())
