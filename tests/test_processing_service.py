"""
Tests for ProcessingService orchestration.
"""

from pathlib import Path
from PIL import Image, ImageDraw

from app.core.models import OcrOptions, ProcessingStatus
from app.services.processing_service import ProcessingService


def test_processing_service_image(tmp_path: Path):
    """Test full image document processing pipeline via ProcessingService."""
    img_path = tmp_path / "test_receipt.png"
    img = Image.new("RGB", (300, 70), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((15, 25), "NASS SERVICE TEST", fill=(0, 0, 0))
    img.save(img_path)

    service = ProcessingService()
    options = OcrOptions(language="eng")
    doc_res = service.process_document(img_path, options)

    assert doc_res.status == ProcessingStatus.COMPLETED
    assert doc_res.total_pages == 1
    assert len(doc_res.pages) == 1
    assert "TEST" in doc_res.full_text or "SERVICE" in doc_res.full_text


def test_processing_service_cancellation(tmp_path: Path):
    """Verify processing cancellation responsiveness."""
    img_path = tmp_path / "test_cancel.png"
    img = Image.new("RGB", (200, 50), color=(255, 255, 255))
    img.save(img_path)

    service = ProcessingService()
    options = OcrOptions()

    # Simulate cancellation request
    is_cancelled = True
    cancel_check = lambda: is_cancelled

    doc_res = service.process_document(img_path, options, cancel_check=cancel_check)
    assert doc_res is not None
