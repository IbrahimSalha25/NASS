"""
Tesseract language pack manager for NASS.
Handles listing installed/available languages, background downloading from tessdata_fast, and safe deletion.
"""

from __future__ import annotations

import os
import shutil
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from nass.core.config import LOCAL_TESSDATA, find_tessdata_directory
from nass.core.settings import SettingsManager
from nass.utils.logger import logger

# Official fast language pack repository
BASE_TESSDATA_URL = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main"

KNOWN_LANGUAGES: Dict[str, Dict[str, str]] = {
    "ara": {"name_ar": "العربية", "name_en": "Arabic"},
    "eng": {"name_ar": "الإنجليزية", "name_en": "English"},
    "fra": {"name_ar": "الفرنسية", "name_en": "French"},
    "deu": {"name_ar": "الألمانية", "name_en": "German"},
    "spa": {"name_ar": "الإسبانية", "name_en": "Spanish"},
    "tur": {"name_ar": "التركية", "name_en": "Turkish"},
    "fas": {"name_ar": "الفارسية", "name_en": "Persian"},
    "urd": {"name_ar": "الأردية", "name_en": "Urdu"},
    "rus": {"name_ar": "الروسية", "name_en": "Russian"},
    "ita": {"name_ar": "الإيطالية", "name_en": "Italian"},
    "por": {"name_ar": "البرتغالية", "name_en": "Portuguese"},
    "chi_sim": {"name_ar": "الصينية (المبسطة)", "name_en": "Chinese (Simplified)"},
    "chi_tra": {"name_ar": "الصينية (التقليدية)", "name_en": "Chinese (Traditional)"},
    "jpn": {"name_ar": "اليابانية", "name_en": "Japanese"},
    "kor": {"name_ar": "الكورية", "name_en": "Korean"},
    "hin": {"name_ar": "الهندية", "name_en": "Hindi"},
    "osd": {"name_ar": "كشف اتجاه الصفحة والنص (OSD)", "name_en": "Orientation & Script"},
}


@dataclass
class LanguageInfo:
    """Metadata representation for a language pack."""
    code: str
    name_ar: str
    name_en: str
    is_installed: bool
    file_path: Optional[Path] = None
    file_size_bytes: int = 0

    @property
    def display_name(self) -> str:
        return f"{self.name_ar} ({self.code})"

    @property
    def size_formatted(self) -> str:
        if self.file_size_bytes <= 0:
            return "-"
        mb = self.file_size_bytes / (1024 * 1024)
        return f"{mb:.1f} ميجابايت"


class LanguageManager:
    """Manager for downloading, installing, and deleting language traineddata files."""

    def __init__(self):
        self.settings = SettingsManager.get_instance()

    def get_tessdata_dir(self, ensure_writable: bool = False) -> Path:
        """
        Locate active tessdata directory.
        If write access is required, falls back to project local directory if system dir is protected.
        """
        current = find_tessdata_directory()

        if ensure_writable:
            target = current if (current and current.is_dir()) else LOCAL_TESSDATA
            if not self._is_writable_dir(target):
                LOCAL_TESSDATA.mkdir(parents=True, exist_ok=True)
                return LOCAL_TESSDATA
            return target

        if current and current.is_dir():
            return current

        LOCAL_TESSDATA.mkdir(parents=True, exist_ok=True)
        return LOCAL_TESSDATA

    @staticmethod
    def _is_writable_dir(directory: Path) -> bool:
        """Check if write permissions exist for a given directory."""
        if not directory.exists():
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except Exception:
                return False
        test_file = directory / ".write_test.tmp"
        try:
            with open(test_file, "w") as f:
                f.write("test")
            test_file.unlink(missing_ok=True)
            return True
        except Exception:
            return False

    def list_installed_languages(self) -> List[LanguageInfo]:
        """List all language packages currently available on disk."""
        tessdata = self.get_tessdata_dir()
        installed_map: Dict[str, Path] = {}

        if tessdata.is_dir():
            for f in tessdata.glob("*.traineddata"):
                if f.is_file():
                    installed_map[f.stem] = f

        result: List[LanguageInfo] = []
        for code, path in installed_map.items():
            known = KNOWN_LANGUAGES.get(code, {"name_ar": code.upper(), "name_en": code.upper()})
            size = path.stat().st_size if path.exists() else 0
            result.append(
                LanguageInfo(
                    code=code,
                    name_ar=known["name_ar"],
                    name_en=known["name_en"],
                    is_installed=True,
                    file_path=path,
                    file_size_bytes=size,
                )
            )

        def sort_priority(item: LanguageInfo) -> int:
            if item.code == "ara":
                return 0
            if item.code == "eng":
                return 1
            if item.code == "osd":
                return 99
            return 10

        result.sort(key=lambda x: (sort_priority(x), x.name_ar))
        return result

    def list_all_catalog_languages(self, search_query: str = "") -> List[LanguageInfo]:
        """
        List all catalog languages with installation status and optional query filter.
        """
        installed = {lang.code: lang for lang in self.list_installed_languages()}
        catalog: List[LanguageInfo] = []
        query = search_query.strip().lower()

        for code, names in KNOWN_LANGUAGES.items():
            is_inst = code in installed
            info = installed[code] if is_inst else LanguageInfo(
                code=code,
                name_ar=names["name_ar"],
                name_en=names["name_en"],
                is_installed=False,
            )

            if query:
                if not (
                    query in code.lower()
                    or query in info.name_ar.lower()
                    or query in info.name_en.lower()
                ):
                    continue

            catalog.append(info)

        return catalog

    def download_and_install_language(
        self,
        lang_code: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> Tuple[bool, str, Optional[Path]]:
        """Download and install a language pack from official GitHub tessdata_fast repository."""
        clean_code = lang_code.strip().lower()
        if not clean_code:
            return False, "رمز اللغة غير محدد.", None

        target_dir = self.get_tessdata_dir(ensure_writable=True)
        final_file_path = target_dir / f"{clean_code}.traineddata"
        temp_file_path = target_dir / f"{clean_code}.traineddata.tmp"

        download_url = f"{BASE_TESSDATA_URL}/{clean_code}.traineddata"
        logger.info(f"Downloading language pack '{clean_code}' from: {download_url}")

        try:
            req = urllib.request.Request(
                download_url,
                headers={"User-Agent": "NASS-Smart-OCR/1.0"},
            )

            with urllib.request.urlopen(req, timeout=15) as response:
                total_size = int(response.headers.get("Content-Length", 0))
                downloaded_size = 0
                chunk_size = 64 * 1024

                with open(temp_file_path, "wb") as out_file:
                    while True:
                        if cancel_check and cancel_check():
                            temp_file_path.unlink(missing_ok=True)
                            return False, "تم إلغاء التنزيل من قبل المستخدم.", None

                        chunk = response.read(chunk_size)
                        if not chunk:
                            break

                        out_file.write(chunk)
                        downloaded_size += len(chunk)

                        if progress_callback:
                            progress_callback(downloaded_size, total_size)

            if not temp_file_path.exists() or temp_file_path.stat().st_size < 1024:
                temp_file_path.unlink(missing_ok=True)
                return False, "فشل التنزيل: الملف المنزّل فارغ أو تالف.", None

            if final_file_path.exists():
                final_file_path.unlink()
            temp_file_path.rename(final_file_path)

            logger.info(f"Language pack installed: {final_file_path}")
            return True, f"تم تنزيل وتثبيت حزمة اللغة '{clean_code}' بنجاح.", final_file_path

        except urllib.error.HTTPError as http_err:
            temp_file_path.unlink(missing_ok=True)
            if http_err.code == 404:
                return False, f"حزمة اللغة '{clean_code}' غير موجودة في المستودع الرسمي.", None
            return False, f"خطأ خادم أثناء التنزيل: كود {http_err.code}", None
        except urllib.error.URLError as url_err:
            temp_file_path.unlink(missing_ok=True)
            return False, f"تعذر الاتصال بالإنترنت لتنزيل اللغة: {url_err.reason}", None
        except Exception as e:
            temp_file_path.unlink(missing_ok=True)
            logger.error(f"Unexpected error downloading language {clean_code}: {e}")
            return False, f"فشل تثبيت اللغة: {e}", None

    def delete_language(self, lang_code: str) -> Tuple[bool, str]:
        """Delete an installed language pack after verification."""
        clean_code = lang_code.strip().lower()
        tessdata = self.get_tessdata_dir()
        target_file = tessdata / f"{clean_code}.traineddata"

        if not target_file.exists():
            return False, f"حزمة اللغة '{clean_code}' غير مثبتة أو الملف غير موجود."

        installed = self.list_installed_languages()
        if len(installed) <= 1:
            return False, "لا يمكن حذف اللغة الوحيدة المتبقية في النظام."

        try:
            target_file.unlink()
            logger.info(f"Deleted language pack: {clean_code}")
            return True, f"تم حذف حزمة اللغة '{clean_code}' بنجاح."
        except Exception as e:
            logger.error(f"Failed to delete language file {target_file}: {e}")
            return False, f"تعذر حذف ملف اللغة: {e}"
