# Changelog

All notable changes to the **نَصّ | NASS** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-11-09

### Added
- **Multi-Format Document Extraction Suite:**
  - **Images (`.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.tiff`):** High-accuracy OCR powered by Tesseract 5.x.
  - **PDF Documents (`.pdf`):** Intelligent hybrid extraction pulling digital vector text first and falling back to OCR only for scanned/raster pages.
  - **Microsoft Word (`.docx`):** Lossless native extraction of headings, paragraphs, and tables.
  - **Microsoft Excel & Data (`.xlsx`, `.xls`, `.csv`):** Native spreadsheet extraction across multiple sheets with cell-delimiter preservation.
  - **Microsoft PowerPoint (`.pptx`):** Native extraction of slide text frames, titles, and notes.
  - **Plain Text & Markdown (`.txt`, `.md`, `.rtf`):** Multi-encoding auto-detection (UTF-8, Arabic CP1256, Latin-1) and RTF control word stripping.
  - **Web & Markup (`.html`, `.htm`, `.xml`):** Semantic parsing stripping scripts/styles and preserving hierarchical data.
  - **Structured Data (`.json`):** Formatted key-value tree extraction.
  - **OpenDocument & eBooks (`.odt`, `.ods`, `.odp`, `.epub`):** Direct zip parsing extracting XML content and EPUB book chapters without external dependencies.
- **Mathematical Formula Recognition:**
  - Built-in regex and symbol parser detecting fractions, roots, superscripts, subscripts, Greek characters, and converting them into standard LaTeX equations.
  - Architecture ready for deep-learning `pix2tex` model integration.
- **Dedicated Tesseract OCR Engine Management:**
  - Real-time engine health and connection status indicators.
  - Windows registry, PATH, and common program directory auto-discovery.
  - Manual executable selection for custom installation locations.
  - Official download guidance and interactive installer launcher.
- **In-App Language Pack Manager:**
  - Real-time catalog of available languages from the official `tessdata_fast` repository.
  - Background downloader with non-blocking progress bars and cancellation support.
  - File integrity validation and language deletion with user confirmation.
- **Advanced OCR Options & Pre-processing Filters:**
  - Page Segmentation Mode (PSM) and OCR Engine Mode (OEM) selector.
  - Configurable image filters: Grayscale conversion, Otsu-style thresholding, contrast enhancement, denoising, and horizontal deskewing.
  - Custom Tesseract command-line flags persistence.
- **Modern PySide6 Desktop Interface:**
  - 100% Right-to-Left (RTL) Arabic layout.
  - Unified color scheme: Deep Navy (`#0F172A`), Royal Blue (`#1E40AF`), and Soft Purple accent (`#7C3AED`).
  - Right-docked sidebar navigation with persistent state.
  - Official slogan: «حيث تتحول الصور إلى كلمات.»
  - Friendly Arabic microcopy across all operational states.
- **Multi-Format Results Export:**
  - Plain Text (`.txt`): UTF-8 encoded with configurable page headers.
  - Microsoft Word (`.docx`): Formatted document with Right-to-Left paragraph alignment and visual page dividers.
  - LaTeX (`.tex`): Formatted math documents with `amsmath` package support.
- **About & Developer Attribution:**
  - Developer card for **Ibrahim Salha** (Intelligent Systems & Computer Engineering Student) with clickable GitHub link.
  - 100% Local & Offline Privacy Guarantee statement.
- **Open-Source Readiness & Automated Testing:**
  - 55 unit and integration tests passing with 100% success rate.
  - Bilingual documentation (English `README.md` and Arabic `README.ar.md`).
  - GitHub Actions CI workflow, issue templates, and pull request template.
