"""
اختبارات وحدة لمدير Tesseract ومدير الإعدادات لنظام نَصّ (NASS).
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.core.settings_manager import AppSettings, SettingsManager
from app.core.tesseract_manager import OFFICIAL_DOWNLOAD_URLS, TesseractManager


def test_settings_manager_defaults():
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = Path(tmp_dir) / "test_settings.json"
        mgr = SettingsManager(config_file=config_path)

        assert mgr.get("default_language") == "ara+eng"
        assert mgr.get("dpi") == 300
        assert mgr.get("tesseract_custom_path") is None

        # تعديل خيار وحفظه
        mgr.set("dpi", 400)
        assert mgr.get("dpi") == 400
        assert config_path.exists()

        # قراءة من جديد
        mgr2 = SettingsManager(config_file=config_path)
        assert mgr2.get("dpi") == 400

        # استعادة الافتراضي
        mgr2.reset_to_defaults()
        assert mgr2.get("dpi") == 300


def test_tesseract_manager_download_info():
    info = TesseractManager.get_official_download_info()
    assert "current_os" in info
    assert "urls" in info
    assert "primary_url" in info
    assert "guide" in info
    assert OFFICIAL_DOWNLOAD_URLS["windows_ub_mannheim"] in info["urls"].values()


def test_tesseract_manager_get_status():
    mgr = TesseractManager()
    status = mgr.get_engine_status()
    assert "is_installed" in status
    assert "platform" in status
    assert "available_languages" in status
    assert isinstance(status["available_languages"], list)


def test_tesseract_manager_verify_installation():
    mgr = TesseractManager()
    success, msg, status = mgr.verify_installation()
    # إذا كان tesseract مثبتاً على الجهاز فيجب أن ينجح الفحص
    if status.get("is_installed") and status.get("pytesseract_connected") and status.get("available_languages"):
        assert success is True
        assert "يعمل بكفاءة" in msg


def test_tesseract_manager_set_custom_path_invalid():
    mgr = TesseractManager()
    success, msg, ver = mgr.set_custom_executable_path(Path("/non/existent/path/tesseract.exe"))
    assert success is False
    assert "غير موجود" in msg
    assert ver is None
