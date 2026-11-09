"""
Tests for FileManager and handling of paths containing Arabic characters and spaces.
"""

from pathlib import Path
from app.core.file_manager import FileManager
from app.core.models import FileType


def test_detect_file_types():
    """Test detecting file types based on file extensions."""
    assert FileManager.detect_file_type(Path("document.pdf")) == FileType.PDF
    assert FileManager.detect_file_type(Path("IMAGE.PNG")) == FileType.IMAGE
    assert FileManager.detect_file_type(Path("photo.jpg")) == FileType.IMAGE
    assert FileManager.detect_file_type(Path("scan.tiff")) == FileType.IMAGE
    assert FileManager.detect_file_type(Path("graphic.webp")) == FileType.IMAGE
    assert FileManager.detect_file_type(Path("archive.zip")) == FileType.UNKNOWN


def test_discover_arabic_and_spaced_files(tmp_path: Path):
    """Test discovering files with paths containing Arabic characters and spaces."""
    folder = tmp_path / "مجلد مستندات وتجارب"
    folder.mkdir()

    file_ar = folder / "تقرير مالي 2026.pdf"
    file_en = folder / "invoice photo.png"
    file_unsupported = folder / "data.csv"

    file_ar.write_text("dummy pdf", encoding="utf-8")
    file_en.write_bytes(b"\x89PNG\r\n\x1a\nfake")
    file_unsupported.write_text("a,b,c", encoding="utf-8")

    discovered = FileManager.discover_files([folder])

    # Should discover PDF and Image only, ignoring unsupported CSV
    assert len(discovered) == 2
    assert file_ar in discovered
    assert file_en in discovered
    assert file_unsupported not in discovered
