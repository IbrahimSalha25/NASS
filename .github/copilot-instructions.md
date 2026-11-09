# GitHub Copilot Instructions for NASS (نَصّ)

NASS is a local-first, smart document text extraction and OCR desktop application built with Python, PySide6, and Tesseract OCR.

## Core Directives
1. **Local-First & Offline:** No external cloud OCR APIs or telemetry. All processing runs on the user's workstation.
2. **Technical Artifacts in English:** All Python code, function/class names, variables, docstrings, comments, tests, and logs must be in English.
3. **Arabic RTL User Interface:** The application interface is native Arabic (RTL). Never use emojis in UI widgets; use vector icons from `nass.ui.icons.AppIcons`.
4. **Architectural Separation:** UI layer (`src/nass/ui/`) is strictly decoupled from extraction engines (`src/nass/engines/`), document processors (`src/nass/processors/`), background workers (`src/nass/workers/`), and services (`src/nass/services/`).
5. **Non-blocking Concurrency:** Never execute OCR or file parsing on the UI thread. Use `QThread` workers with fine-grained progress, status, and cancellation signals.
6. **Safe File Handling:** Never modify or delete user input files. Fully support UTF-8 paths containing Arabic characters and spaces.
7. **Testing:** Write pytest tests for all new extractors or behaviors and verify them before declaring a task complete.
