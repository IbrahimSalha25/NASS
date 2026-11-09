# Contributing to NASS

Thank you for your interest in contributing to **نَصّ | NASS**! We welcome bug reports, feature requests, documentation improvements, and code contributions from everyone.

---

## Code of Conduct

By participating in this project, you agree to abide by the [Code of Conduct](CODE_OF_CONDUCT.md). Please treat all contributors with respect and professionalism.

---

## Architectural & Coding Guidelines

To maintain architectural integrity and clean code standards, please adhere strictly to these rules:

1. **Local-First & Offline Guarantee:**
   - NASS is strictly an offline application. Never add third-party cloud OCR APIs, telemetry, or remote dependencies that compromise user data confidentiality.
2. **Language Separation:**
   - **Technical artifacts:** All Python code, function/class/variable names, docstrings, inline comments, log messages, and technical exception messages must be in **English**.
   - **User Interface:** All user-facing strings, buttons, labels, dialogs, tooltips, and microcopy must be in **Arabic** (Right-to-Left).
3. **No Emoji in UI:**
   - Do not use emoji characters in the application interface. Always use vector icons from `nass.ui.icons.AppIcons`.
4. **Clean Code & Type Hints:**
   - Use Python 3.11+ type hints across all function and method signatures.
   - Use `pathlib.Path` for all filesystem operations.
   - Keep functions concise with single responsibilities.

---

## Git Workflow & Branching Model

We follow a disciplined branching workflow:

| Branch Prefix | Purpose | Example |
|---|---|---|
| `feature/` | New user-facing capabilities or extractors | `feature/epub-metadata` |
| `refactor/` | Code structure and architecture cleanup | `refactor/pipeline-optimization` |
| `bugfix/` | Bug fixes and patches | `bugfix/arabic-diacritics` |
| `docs/` | Documentation additions and improvements | `docs/installation-guide` |
| `chore/` | Maintenance, dependencies, and configuration | `chore/update-requirements` |

### Step-by-Step Contribution Process

1. **Fork the repository** on GitHub.
2. **Clone your fork** and set up the development environment:
   ```bash
   git clone https://github.com/<your-username>/NASS.git
   cd NASS
   python -m venv .venv
   .\.venv\Scripts\activate   # Or source .venv/bin/activate on Unix
   pip install -r requirements.txt
   ```
3. **Create a branch** for your work:
   ```bash
   git checkout -b feature/my-new-feature
   ```
4. **Make your changes** following the coding guidelines.
5. **Run the test suite** to ensure no regressions:
   ```bash
   pytest tests
   ```
6. **Commit your changes** with descriptive commit messages:
   ```bash
   git commit -m "feat(docx): preserve table cell borders during extraction"
   ```
7. **Push to your fork** and submit a Pull Request to `main`.

---

## Reporting Issues

If you find a bug or have a suggestion, please open an issue using our [GitHub Issue Templates](.github/ISSUE_TEMPLATE/). Provide as much relevant context as possible, including:
- Operating system and version.
- Tesseract OCR version and installed languages.
- Sample document (make sure it does not contain private or sensitive data).
- Full console error log.
