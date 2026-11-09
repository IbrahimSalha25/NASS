"""
Unit tests for LanguageManager in NASS.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.core.language_manager import LanguageManager, KNOWN_LANGUAGES


def test_list_installed_languages():
    mgr = LanguageManager()
    installed = mgr.list_installed_languages()
    assert isinstance(installed, list)
    # tessdata contains ara, eng, and osd by default
    installed_codes = {lang.code for lang in installed}
    assert "ara" in installed_codes
    assert "eng" in installed_codes


def test_list_all_catalog_languages():
    mgr = LanguageManager()
    catalog = mgr.list_all_catalog_languages()
    assert len(catalog) >= len(KNOWN_LANGUAGES)

    # Test search query functionality
    search_res = mgr.list_all_catalog_languages(search_query="عربية")
    assert any(x.code == "ara" for x in search_res)

    search_eng = mgr.list_all_catalog_languages(search_query="eng")
    assert any(x.code == "eng" for x in search_eng)


def test_delete_language_non_existent():
    mgr = LanguageManager()
    success, msg = mgr.delete_language("nonexistent_lang_xyz")
    assert success is False
    assert "غير مثبتة" in msg


def test_download_language_mock():
    mgr = LanguageManager()
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        with patch.object(mgr, "get_tessdata_dir", return_value=tmp_path):
            with patch("urllib.request.urlopen") as mock_urlopen:
                mock_response = MagicMock()
                mock_response.headers = {"Content-Length": "2048"}
                mock_response.read.side_effect = [b"A" * 1024, b"B" * 1024, b""]
                mock_urlopen.return_value.__enter__.return_value = mock_response

                progress_calls = []

                def on_progress(d, t):
                    progress_calls.append((d, t))

                success, msg, path = mgr.download_and_install_language("fra", progress_callback=on_progress)
                assert success is True
                assert path is not None
                assert path.exists()
                assert len(progress_calls) >= 2
                assert (tmp_path / "fra.traineddata").exists()

                # Delete language after installing in temporary directory
                # Add a dummy second language so "single remaining language" check does not prevent deletion
                (tmp_path / "dummy.traineddata").write_bytes(b"dummy")
                del_success, del_msg = mgr.delete_language("fra")
                assert del_success is True
                assert not (tmp_path / "fra.traineddata").exists()
