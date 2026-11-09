# Installation and Setup Guide

This guide covers setting up **نَصّ | NASS** on Windows, Linux, and macOS.

---

## 1. Prerequisites

- **Python 3.11 or higher** (Python 3.12 recommended)
- **Tesseract OCR 5.x engine** (Required for scanned documents and image OCR)
- **Git** (For cloning the repository)

---

## 2. Clone the Repository

```bash
git clone https://github.com/IbrahimSalha25/NASS.git
cd NASS
```

---

## 3. Python Environment Setup

Create and activate a virtual environment:

### On Windows:
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

### On Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install required Python packages:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Tesseract OCR Engine Setup

### A. Windows (Recommended)
1. Download the official Windows installer from UB-Mannheim:
   - **URL:** [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run the installer and during the component selection step:
   - Expand **Additional script data** and check **Arabic script**.
   - Expand **Additional language data** and check **Arabic** (`ara`).
3. Complete the installation (default path: `C:\Program Files\Tesseract-OCR`).
4. **NASS automatically discovers** Tesseract at this location. Alternatively, you can specify a custom path from within the application under **إعدادات محرك OCR** (OCR Settings).

### B. Linux (Ubuntu / Debian)
```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-ara tesseract-ocr-eng libgl1
```

### C. macOS (Homebrew)
```bash
brew install tesseract
brew install tesseract-lang
```

---

## 5. Language Packs (Tessdata)

NASS requires trained language data (`.traineddata`) for the languages you wish to recognize:
- **Arabic (`ara.traineddata`):** For Arabic text recognition.
- **English (`eng.traineddata`):** For English text and alphanumeric codes.

### In-App Language Management
NASS includes a built-in Language Manager accessible from the **إعدادات محرك OCR** tab:
1. Browse available language packs from the official `tessdata_fast` repository.
2. Click **تنزيل وتثبيت** (Download & Install) next to any language.
3. The pack will download in the background with progress reporting and verify integrity automatically.

---

## 6. Running the Application

Launch NASS directly with:
```bash
python main.py
```

Or install in editable development mode:
```bash
pip install -e .
nass
```

---

## 7. Running the Automated Tests

Verify that your environment is properly configured by executing the test suite:
```bash
pytest tests
```
All 55 unit and integration tests should pass.
