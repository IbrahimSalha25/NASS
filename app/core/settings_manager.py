"""
مدير حفظ واسترجاع إعدادات تطبيق نَصّ (NASS).
يحفظ الإعدادات في ملف JSON محلي ويدعم استعادة القيم الافتراضية.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from app.config import PROJECT_ROOT
from app.utils.logger import logger


# مسار ملف الإعدادات المفضل: مجلد المستخدم ~/.nass/settings.json
USER_CONFIG_DIR = Path.home() / ".nass"
SETTINGS_FILE_PATH = USER_CONFIG_DIR / "settings.json"


@dataclass
class AppSettings:
    """بيانات إعدادات التطبيق والمحرك."""
    # مسارات المحرك
    tesseract_custom_path: Optional[str] = None
    tessdata_custom_path: Optional[str] = None

    # خيارات OCR الأساسية
    default_language: str = "ara+eng"
    dpi: int = 300
    psm: int = 3
    oem: int = 3

    # خيارات معالجة الصور
    apply_enhancement: bool = False
    enhance_contrast: bool = False
    denoise: bool = False
    threshold: bool = False
    deskew: bool = False

    # خيارات PDF
    extract_embedded_first: bool = True

    # خيارات المعادلات الرياضية
    math_enabled: bool = False
    math_engine: str = "pix2tex"

    # خيارات التصدير والواجهة
    export_default_format: str = "txt"
    remember_window_size: bool = True
    window_width: int = 1200
    window_height: int = 800

    # إعدادات إضافية متقدمة
    tesseract_extra_config: str = ""


class SettingsManager:
    """فئة إدارة وقراءة وحفظ الإعدادات."""

    _instance: Optional[SettingsManager] = None

    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or SETTINGS_FILE_PATH
        self.settings: AppSettings = self.load()

    @classmethod
    def get_instance(cls) -> SettingsManager:
        """الحصول على النسخة المشتركة من مدير الإعدادات."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load(self) -> AppSettings:
        """قراءة الإعدادات من الملف أو إنشاء الإعدادات الافتراضية."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                valid_fields = {k: v for k, v in data.items() if hasattr(AppSettings, k)}
                logger.debug(f"تم تحميل الإعدادات من: {self.config_file}")
                return AppSettings(**valid_fields)
            except Exception as e:
                logger.warning(f"تعذر قراءة ملف الإعدادات ({e})، سيتم استخدام الإعدادات الافتراضية.")
        return AppSettings()

    def save(self) -> bool:
        """حفظ الإعدادات الحالية في ملف JSON."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(asdict(self.settings), f, indent=2, ensure_ascii=False)
            logger.debug(f"تم حفظ الإعدادات بنجاح في: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"فشل حفظ الإعدادات: {e}")
            return False

    def reset_to_defaults(self) -> AppSettings:
        """استعادة الإعدادات الافتراضية وحفظها."""
        self.settings = AppSettings()
        self.save()
        return self.settings

    def get(self, key: str, default: Any = None) -> Any:
        """الحصول على قيمة خيار معين."""
        return getattr(self.settings, key, default)

    def set(self, key: str, value: Any, auto_save: bool = True):
        """تحديث خيار معين مع إمكانية الحفظ التلقائي."""
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)
            if auto_save:
                self.save()
        else:
            raise KeyError(f"خيار غير معروف في الإعدادات: {key}")
