"""
مدير حزم لغات Tesseract OCR لنظام نَصّ (NASS).
يوفر استعراض اللغات المثبتة والمتاحة، تنزيل وتثبيت وحذف الحزم، والتحقق من سلامتها.
"""

from __future__ import annotations

import os
import shutil
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from app.config import LOCAL_TESSDATA, find_tessdata_directory
from app.core.settings_manager import SettingsManager
from app.utils.logger import logger


# مستودع حزم اللغات السريعة الرسمي (tessdata_fast)
BASE_TESSDATA_URL = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main"

# قاموس اللغات الشائعة مع أسمائها بالعربية والإنجليزية
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
    """معلومات حزمة لغة معينة."""
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
    """مدير تنزيل وتثبيت وإدارة حزم اللغات."""

    def __init__(self):
        self.settings = SettingsManager.get_instance()

    def get_tessdata_dir(self, ensure_writable: bool = False) -> Path:
        """
        الحصول على مسار مجلد tessdata الفعال.
        إذا كان المطلوب مجلداً قابلاً للكتابة، يتم التحقق من الصلاحيات والتحويل لمجلد محلي عند اللزوم.
        """
        current = find_tessdata_directory()

        if ensure_writable:
            # اختبار إمكانية الكتابة في المجلد الحالي
            target = current if (current and current.is_dir()) else LOCAL_TESSDATA
            if not self._is_writable_dir(target):
                # إذا كان المجلد الحالي غير قابل للكتابة (مثلاً C:\Program Files)، نستخدم المجلد المحلي للمشروع
                LOCAL_TESSDATA.mkdir(parents=True, exist_ok=True)
                return LOCAL_TESSDATA
            return target

        if current and current.is_dir():
            return current

        LOCAL_TESSDATA.mkdir(parents=True, exist_ok=True)
        return LOCAL_TESSDATA

    @staticmethod
    def _is_writable_dir(directory: Path) -> bool:
        """التحقق من إمكانية الكتابة في مجلد ما بإنشاء ملف مؤقت."""
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
        """استرجاع قائمة بكافة اللغات المثبتة حالياً."""
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

        # ترتيب اللغات: العربية أولاً ثم الإنجليزية ثم البقية
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
        عرض كتالوج اللغات المدعومة مع توضيح ما إذا كانت مثبتة أو متاحة للتنزيل،
        مع إمكانية الفلترة والبحث بالاسم أو الرمز.
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

            # تطبيق البحث
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
        """
        تنزيل وتثبيت حزمة لغة محددة من المستودع الرسمي.
        يعيد (نجاح، رسالة، مسار_الملف_المثبت).
        """
        clean_code = lang_code.strip().lower()
        if not clean_code:
            return False, "رمز اللغة غير محدد.", None

        # تحديد مسار التثبيت القابل للكتابة
        target_dir = self.get_tessdata_dir(ensure_writable=True)
        final_file_path = target_dir / f"{clean_code}.traineddata"
        temp_file_path = target_dir / f"{clean_code}.traineddata.tmp"

        download_url = f"{BASE_TESSDATA_URL}/{clean_code}.traineddata"
        logger.info(f"بدء تنزيل حزمة اللغة '{clean_code}' من: {download_url}")

        try:
            req = urllib.request.Request(
                download_url,
                headers={"User-Agent": "NASS-Smart-OCR/1.0"},
            )

            with urllib.request.urlopen(req, timeout=15) as response:
                total_size = int(response.headers.get("Content-Length", 0))
                downloaded_size = 0
                chunk_size = 64 * 1024  # 64 KB

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

            # التحقق من سلامة الملف المنزّل
            if not temp_file_path.exists() or temp_file_path.stat().st_size < 1024:
                temp_file_path.unlink(missing_ok=True)
                return False, "فشل التنزيل: الملف المنزّل فارغ أو تالف.", None

            # استبدال الملف النهائي بشكل آمن
            if final_file_path.exists():
                final_file_path.unlink()
            temp_file_path.rename(final_file_path)

            logger.info(f"تم تثبيت حزمة اللغة {clean_code} بنجاح في: {final_file_path}")
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
            logger.error(f"خطأ غير متوقع أثناء تنزيل اللغة {clean_code}: {e}")
            return False, f"فشل تثبيت اللغة: {e}", None

    def delete_language(self, lang_code: str) -> Tuple[bool, str]:
        """
        حذف حزمة لغة مثبتة بعد التحقق.
        """
        clean_code = lang_code.strip().lower()
        tessdata = self.get_tessdata_dir()
        target_file = tessdata / f"{clean_code}.traineddata"

        if not target_file.exists():
            return False, f"حزمة اللغة '{clean_code}' غير مثبتة أو الملف غير موجود."

        # منع حذف كل اللغات إذا لم يتبق سوى واحدة، أو تحذير
        installed = self.list_installed_languages()
        if len(installed) <= 1:
            return False, "لا يمكن حذف اللغة الوحيدة المتبقية في النظام."

        try:
            target_file.unlink()
            logger.info(f"تم حذف حزمة اللغة '{clean_code}' بنجاح.")
            return True, f"تم حذف حزمة اللغة '{clean_code}' بنجاح."
        except Exception as e:
            logger.error(f"فشل حذف ملف اللغة {target_file}: {e}")
            return False, f"تعذر حذف ملف اللغة: {e}"
