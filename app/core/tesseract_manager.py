"""
مدير ومتحكم محرك Tesseract OCR وPytesseract لنظام نَصّ (NASS).
يوفر فحص التثبيت والمسارات والتحقق من الاتصال وإرشادات التثبيت الرسمية وإعادة الضبط.
"""

from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

from app.config import (
    configure_pytesseract,
    find_tessdata_directory,
    find_tesseract_executable,
)
from app.core.settings_manager import SettingsManager
from app.utils.logger import logger


# روابط التنزيل الرسمية الموثوقة
OFFICIAL_DOWNLOAD_URLS = {
    "windows_ub_mannheim": "https://github.com/UB-Mannheim/tesseract/wiki",
    "windows_installer_latest": "https://digi.bib.uni-mannheim.de/tesseract/",
    "tesseract_github": "https://github.com/tesseract-ocr/tesseract",
    "tesseract_user_manual": "https://tesseract-ocr.github.io/tessdoc/",
    "tessdata_fast_github": "https://github.com/tesseract-ocr/tessdata_fast",
}


class TesseractManager:
    """إدارة محرك Tesseract والاتصال به وفحص التثبيت."""

    def __init__(self):
        self.settings = SettingsManager.get_instance()
        configure_pytesseract()

    def get_engine_status(self) -> Dict[str, Any]:
        """
        فحص شامل لحالة Tesseract ومساراته واتصاله مع pytesseract.
        """
        configure_pytesseract()

        exe_path = find_tesseract_executable()
        tessdata_dir = find_tessdata_directory()
        system_platform = platform.system()

        status: Dict[str, Any] = {
            "is_installed": False,
            "version": None,
            "executable_path": str(exe_path) if exe_path else None,
            "install_dir": str(exe_path.parent) if exe_path else None,
            "tessdata_path": str(tessdata_dir) if tessdata_dir else None,
            "pytesseract_connected": False,
            "available_languages": [],
            "error_message": None,
            "platform": system_platform,
            "is_custom_path": bool(self.settings.get("tesseract_custom_path")),
        }

        if not exe_path or not exe_path.exists():
            status["error_message"] = (
                "محرك Tesseract غير مثبت على هذا الجهاز أو لم يتم العثور على ملف التشغيل (tesseract.exe)."
            )
            return status

        # 1. اختبار تشغيل Tesseract كأمر مستقل للتحقق من الصلاحيات والإصدار
        try:
            cmd_output = subprocess.run(
                [str(exe_path), "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if cmd_output.returncode == 0:
                # السطر الأول عادة يحوي رقم الإصدار مثل: tesseract 5.5.0
                first_line = cmd_output.stdout.splitlines()[0] if cmd_output.stdout else ""
                version_raw = first_line.replace("tesseract", "").strip()
                status["version"] = version_raw
                status["is_installed"] = True
            else:
                status["error_message"] = f"أرجع Tesseract رمز خطأ: {cmd_output.stderr.strip()}"
                return status
        except Exception as e:
            logger.error(f"خطأ أثناء التحقق من أمر tesseract: {e}")
            status["error_message"] = f"تعذر تنفيذ ملف Tesseract: {e}"
            return status

        # 2. اختبار اتصال Pytesseract بالمحرك
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = str(exe_path)
            py_version = pytesseract.get_tesseract_version()
            if py_version:
                status["pytesseract_connected"] = True
                if not status["version"]:
                    status["version"] = str(py_version)
        except Exception as py_err:
            logger.warning(f"تعذر استدعاء Tesseract عبر pytesseract: {py_err}")
            status["pytesseract_connected"] = False
            status["error_message"] = f"Pytesseract غير قادر على التواصل مع المحرك: {py_err}"

        # 3. جلب قائمة اللغات المتوفرة
        status["available_languages"] = self.get_installed_languages(tessdata_dir)

        return status

    def get_installed_languages(self, tessdata_dir: Optional[Path] = None) -> List[str]:
        """استرجاع قائمة اللغات المثبتة في مجلد tessdata."""
        target_dir = tessdata_dir or find_tessdata_directory()
        if not target_dir or not target_dir.is_dir():
            return []

        # فحص ملفات *.traineddata
        try:
            files = list(target_dir.glob("*.traineddata"))
            # استبعاد اللغات الخاصة مثل osd إذا أردنا أو الاحتفاظ بها
            langs = sorted([f.stem for f in files if f.is_file()])
            return langs
        except Exception as e:
            logger.warning(f"خطأ أثناء فحص ملفات اللغات في {target_dir}: {e}")
            return []

    def set_custom_executable_path(self, path: Path | str) -> Tuple[bool, str, Optional[str]]:
        """
        تعيين والتحقق من مسار مخصص لـ tesseract.exe.
        يعيد (نجاح، رسالة، الإصدار_المكتشف).
        """
        p = Path(path).resolve()
        if not p.exists():
            return False, "المسار المحدد غير موجود على القرص.", None

        if not p.is_file():
            return False, "المسار المحدد هو مجلد وليس ملفاً قابلاً للتنفيذ.", None

        # اختبار تشغيل الملف للتحقق من أنه Tesseract حقيقي
        try:
            res = subprocess.run(
                [str(p), "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if res.returncode != 0 or "tesseract" not in (res.stdout + res.stderr).lower():
                return False, "الملف المحدد ليس ملف تشغيل Tesseract صالحاً.", None

            first_line = res.stdout.splitlines()[0] if res.stdout else ""
            version_str = first_line.replace("tesseract", "").strip()

            # حفظ في الإعدادات
            self.settings.set("tesseract_custom_path", str(p))
            configure_pytesseract()
            logger.info(f"تم تعيين مسار Tesseract المخصص بنجاح: {p} (v{version_str})")
            return True, f"تم التحقق من محرك Tesseract بنجاح (الإصدار {version_str}).", version_str

        except Exception as e:
            return False, f"فشل تشغيل الملف للتحقق منه: {e}", None

    def set_custom_tessdata_path(self, path: Path | str) -> Tuple[bool, str, int]:
        """
        تعيين مسار مخصص لمجلد حزم اللغات (tessdata).
        يعيد (نجاح، رسالة، عدد_اللغات_المكتشفة).
        """
        p = Path(path).resolve()
        if not p.exists() or not p.is_dir():
            return False, "المجلد المحدد غير موجود على القرص.", 0

        trained_files = list(p.glob("*.traineddata"))
        if not trained_files:
            return False, "المجلد المحدد لا يحتوي على أي ملفات حزم لغات (*.traineddata).", 0

        self.settings.set("tessdata_custom_path", str(p))
        configure_pytesseract()
        logger.info(f"تم تعيين مسار tessdata المخصص: {p} ({len(trained_files)} لغة)")
        return True, f"تم العثور على {len(trained_files)} لغة في المجلد المحدد.", len(trained_files)

    def reset_to_auto_discovery(self) -> Dict[str, Any]:
        """إلغاء المسارات المخصصة وإعادة تفعيل الاكتشاف التلقائي لمسارات النظام."""
        self.settings.set("tesseract_custom_path", None, auto_save=False)
        self.settings.set("tessdata_custom_path", None, auto_save=True)
        configure_pytesseract()
        logger.info("تمت إعادة ضبط مسار Tesseract للاكتشاف التلقائي.")
        return self.get_engine_status()

    def verify_installation(self) -> Tuple[bool, str, Dict[str, Any]]:
        """
        فحص متكامل وتجريبي لمحرك Tesseract عبر إجراء عملية OCR اختبارية في الذاكرة.
        """
        status = self.get_engine_status()
        if not status["is_installed"]:
            return False, "محرك Tesseract غير مثبت أو لم يتم العثور عليه.", status

        if not status["pytesseract_connected"]:
            return False, f"فشل اتصال Pytesseract بالمحرك: {status.get('error_message')}", status

        langs = status.get("available_languages", [])
        if not langs:
            return False, "المحرك مثبت ولكن لا توجد أي لغة في مجلد tessdata.", status

        # اختبار OCR مصغر على صورة في الذاكرة
        try:
            import pytesseract
            test_img = Image.new("RGB", (120, 40), color="white")
            # اختيار اللغة المتاحة الأولى
            test_lang = "eng" if "eng" in langs else langs[0]
            _ = pytesseract.image_to_string(test_img, lang=test_lang)
            return True, f"محرك Tesseract يعمل بكفاءة تامة (الإصدار {status['version']}) مع {len(langs)} لغة مثبتة.", status
        except Exception as e:
            return False, f"فشل الاختبار التجريبي لعملية التعرف: {e}", status

    @staticmethod
    def get_official_download_info() -> Dict[str, Any]:
        """
        إرجاع روابط التنزيل الرسمية وتعليمات التثبيت لكل نظام تشغيل.
        """
        current_os = platform.system()

        instructions = {
            "Windows": (
                "1. قم بزيارة صفحة التنزيل الرسمية لمثبت Windows (UB-Mannheim).\n"
                "2. نزّل أحدث مثبت بصيغة .exe (مثل: tesseract-ocr-w64-setup-v5.x.exe).\n"
                "3. شغّل المثبت، وفي خطوة 'Choose Components' اختر حزم اللغات الإضافية (مثل العربية Arabic script).\n"
                "4. بعد اكتمال التثبيت، اضغط زر 'إعادة فحص التثبيت' في التطبيق ليتم التعرف عليه تلقائياً."
            ),
            "Linux": (
                "1. على نظام Ubuntu/Debian: افتح الطرفية ونفذ:\n"
                "   sudo apt update && sudo apt install tesseract-ocr tesseract-ocr-ara tesseract-ocr-eng\n"
                "2. على Fedora: sudo dnf install tesseract tesseract-langpack-ara\n"
                "3. بعد انتهاء التثبيت، اضغط زر 'إعادة فحص التثبيت' هنا."
            ),
            "Darwin": (
                "1. على نظام macOS باستخدام Homebrew:\n"
                "   brew install tesseract tesseract-lang\n"
                "2. بعد اكتمال التثبيت، اضغط زر 'إعادة فحص التثبيت' في التطبيق."
            ),
        }

        return {
            "current_os": current_os,
            "urls": OFFICIAL_DOWNLOAD_URLS,
            "guide": instructions.get(current_os, instructions["Windows"]),
            "primary_url": (
                OFFICIAL_DOWNLOAD_URLS["windows_ub_mannheim"]
                if current_os == "Windows"
                else OFFICIAL_DOWNLOAD_URLS["tesseract_github"]
            ),
        }
