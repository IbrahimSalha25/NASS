"""
Internationalization (i18n) module for NASS.
Provides bilingual translation dictionaries (Arabic and English) and helpers.
Default language is Arabic ("ar").
"""

from __future__ import annotations

from typing import Dict, Optional


TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # -------------------------------------------------------------
    # General & App Identity
    # -------------------------------------------------------------
    "app_name": {
        "ar": "نَصّ | NASS",
        "en": "NASS | Smart OCR",
    },
    "app_title_full": {
        "ar": "نَصّ | NASS — Smart Document & OCR Extractor",
        "en": "NASS — Smart Document & OCR Extractor",
    },
    "app_slogan": {
        "ar": "حيث تتحول الصور إلى كلمات.",
        "en": "Where images become words.",
    },
    "app_desc": {
        "ar": "تطبيقك المحلي لاستخراج النصوص الذكي من المستندات الرقمية والصور بأمان تام وبدون إنترنت.",
        "en": "Your local desktop application for smart text extraction from documents and images with complete privacy.",
    },
    "version": {
        "ar": "الإصدار",
        "en": "Version",
    },

    # -------------------------------------------------------------
    # Sidebar Navigation
    # -------------------------------------------------------------
    "nav_home": {
        "ar": "الرئيسية",
        "en": "Home",
    },
    "nav_extract": {
        "ar": "استخراج النصوص",
        "en": "Extract Text",
    },
    "nav_history": {
        "ar": "سجل العمليات",
        "en": "History",
    },
    "nav_ocr_settings": {
        "ar": "إعدادات OCR",
        "en": "OCR Settings",
    },
    "nav_app_settings": {
        "ar": "إعدادات التطبيق",
        "en": "App Settings",
    },
    "nav_about": {
        "ar": "حول التطبيق",
        "en": "About",
    },
    "engine_status_title": {
        "ar": "حالة Tesseract OCR:",
        "en": "Tesseract OCR Status:",
    },
    "engine_status_checking": {
        "ar": "جاري الفحص...",
        "en": "Checking...",
    },
    "engine_status_ready": {
        "ar": "جاهز للعمل",
        "en": "Ready",
    },
    "engine_status_not_installed": {
        "ar": "غير مثبت أو غير مكتشف",
        "en": "Not installed / undetected",
    },

    # -------------------------------------------------------------
    # Home View
    # -------------------------------------------------------------
    "home_welcome": {
        "ar": "كل ملفاتك تبدأ رحلتها من هنا.",
        "en": "All your documents start their journey here.",
    },
    "home_drop_title": {
        "ar": "اسحب ملفك وأفلته هنا، أو اختره من جهازك.",
        "en": "Drag & drop your file here, or select from device.",
    },
    "home_drop_sub": {
        "ar": "اختر ملفك، ودع الباقي علينا.",
        "en": "Choose your file, and leave the rest to us.",
    },
    "home_btn_select": {
        "ar": "  اختيار ملف للبدء  ",
        "en": "  Choose File to Start  ",
    },
    "home_formats_title": {
        "ar": "الصيغ المدعومة فعلياً:",
        "en": "Supported Formats:",
    },
    "home_formats_list": {
        "ar": "• مستندات وصور: PDF، PNG، JPG، JPEG، WEBP، BMP، TIFF\n• أوفيس وجداول: DOCX، XLSX، XLS، CSV، PPTX\n• نصوص وويب وبيانات: TXT، MD، RTF، HTML، XML، JSON، ODT، EPUB",
        "en": "• Documents & Images: PDF, PNG, JPG, JPEG, WEBP, BMP, TIFF\n• Office & Spreadsheets: DOCX, XLSX, XLS, CSV, PPTX\n• Text, Web & Data: TXT, MD, RTF, HTML, XML, JSON, ODT, EPUB",
    },
    "stat_engine_title": {
        "ar": "محرك Tesseract",
        "en": "Tesseract Engine",
    },
    "stat_engine_btn": {
        "ar": "إدارة المحرك",
        "en": "Manage Engine",
    },
    "stat_langs_title": {
        "ar": "اللغات المثبتة",
        "en": "Installed Languages",
    },
    "stat_langs_val": {
        "ar": "العربية + الإنجليزية",
        "en": "Arabic + English",
    },
    "stat_langs_sub": {
        "ar": "دعم النصوص المختلطة والثنائية",
        "en": "Mixed and bilingual text support",
    },
    "stat_privacy_title": {
        "ar": "الخصوصية والأمان",
        "en": "Privacy & Security",
    },
    "stat_privacy_val": {
        "ar": "معالجة محلية 100%",
        "en": "100% Local Processing",
    },
    "stat_privacy_sub": {
        "ar": "لا يتم إرسال أي مستند أو صورة لخوادم خارجية",
        "en": "No files or images sent to external servers",
    },

    # -------------------------------------------------------------
    # Extract View
    # -------------------------------------------------------------
    "extract_no_file_title": {
        "ar": "لا يوجد ما نعمل عليه الآن. اختر ملفاً للبدء.",
        "en": "Nothing to work on right now. Select a file to start.",
    },
    "extract_no_file_desc": {
        "ar": "قم بسحب أي ملف إلى هذه النافذة أو انقر على الزر لاختيار ملف من جهازك.",
        "en": "Drag any file into this window or click the button to browse your device.",
    },
    "extract_btn_browse": {
        "ar": "اختيار ملف للاستخراج",
        "en": "Choose File for Extraction",
    },
    "extract_btn_change": {
        "ar": "تغيير الملف",
        "en": "Change File",
    },
    "extract_btn_start": {
        "ar": "بدء استخراج النصوص",
        "en": "Start Extraction",
    },
    "extract_btn_stop": {
        "ar": "إيقاف المعالجة",
        "en": "Cancel Processing",
    },
    "extract_btn_copy_all": {
        "ar": "نسخ النص كاملاً",
        "en": "Copy All Text",
    },
    "extract_btn_copy_page": {
        "ar": "نسخ الصفحة الحالية",
        "en": "Copy Current Page",
    },
    "extract_btn_export": {
        "ar": "تصدير النتيجة...",
        "en": "Export Result...",
    },
    "extract_btn_export_txt": {
        "ar": "تصدير TXT",
        "en": "Export TXT",
    },
    "extract_btn_export_docx": {
        "ar": "تصدير Word",
        "en": "Export Word",
    },
    "extract_preview_title": {
        "ar": "معاينة المستند والصفحات",
        "en": "Document & Pages Preview",
    },
    "extract_results_title": {
        "ar": "النصوص المستخرجة",
        "en": "Extracted Text",
    },
    "extract_status_waiting": {
        "ar": "في انتظار بدء الاستخراج...",
        "en": "Ready to extract...",
    },
    "extract_status_reading": {
        "ar": "نقرأ محتوى ملفك الآن...",
        "en": "Reading your file content now...",
    },
    "extract_status_success": {
        "ar": "اكتملت العملية، وأصبح النص جاهزاً.",
        "en": "Process completed, text is ready.",
    },
    "extract_status_empty": {
        "ar": "لم نعثر على نص قابل للاستخراج في هذا الملف.",
        "en": "No extractable text found in this file.",
    },
    "extract_status_cancelled": {
        "ar": "تم إلغاء عملية الاستخراج.",
        "en": "Extraction was cancelled.",
    },
    "extract_status_failed": {
        "ar": "حدث خطأ أثناء معالجة الملف.",
        "en": "An error occurred while processing the file.",
    },
    "extract_stat_pages": {
        "ar": "الصفحات",
        "en": "Pages",
    },
    "extract_stat_words": {
        "ar": "الكلمات",
        "en": "Words",
    },
    "extract_stat_chars": {
        "ar": "الحروف",
        "en": "Characters",
    },
    "extract_stat_confidence": {
        "ar": "متوسط الدقة",
        "en": "Confidence",
    },
    "extract_stat_time": {
        "ar": "المدة",
        "en": "Duration",
    },

    # -------------------------------------------------------------
    # History View
    # -------------------------------------------------------------
    "history_title": {
        "ar": "سجل عمليات الاستخراج",
        "en": "Extraction History",
    },
    "history_desc": {
        "ar": "عرض أرشيف المستندات والملفات المعالجة خلال الجلسة الحالية",
        "en": "View session archive of processed documents and files",
    },
    "history_clear_btn": {
        "ar": "مسح السجل",
        "en": "Clear History",
    },
    "history_col_time": {
        "ar": "وقت المعالجة",
        "en": "Timestamp",
    },
    "history_col_name": {
        "ar": "اسم الملف",
        "en": "File Name",
    },
    "history_col_type": {
        "ar": "النوع",
        "en": "Type",
    },
    "history_col_method": {
        "ar": "طريقة الاستخراج",
        "en": "Method",
    },
    "history_col_pages": {
        "ar": "الصفحات",
        "en": "Pages",
    },
    "history_col_status": {
        "ar": "الحالة",
        "en": "Status",
    },
    "history_col_actions": {
        "ar": "إجراءات",
        "en": "Actions",
    },
    "history_btn_copy": {
        "ar": "نسخ النص",
        "en": "Copy Text",
    },
    "history_btn_rescan": {
        "ar": "إعادة المسح",
        "en": "Re-scan",
    },
    "history_file_same_msg": {
        "ar": "المسار ما زال مسجلاً:\n{path}\n\nسيتم فتح الملف في شاشة الاستخراج لإعادة معالجته دون الحاجة لتخزين نسخ منه.",
        "en": "File path is unchanged:\n{path}\n\nThe file will now open in the Extract view for re-processing without storing duplicates.",
    },
    "history_file_moved_title": {
        "ar": "تغير مسار الملف أو لم يعد موجوداً",
        "en": "File Moved or Missing",
    },
    "history_file_moved_msg": {
        "ar": "تعذر العثور على الملف في المسار المسجل:\n{path}\n\nيبدو أن الملف قد تم نقله أو حذفه أو إعادة تسميته من موقعه الأصلي. التطبيق لا يخزن نسخاً من ملفاتك للحفاظ على خصوصيتك وسعة جهازك.\n\nهل ترغب في تحديد المسار الجديد للملف؟",
        "en": "Could not locate file at original path:\n{path}\n\nThe file appears to have been moved, renamed, or deleted. NASS does not store copies of your files to ensure privacy and storage savings.\n\nWould you like to locate the file manually?",
    },

    # -------------------------------------------------------------
    # App Settings View
    # -------------------------------------------------------------
    "settings_title": {
        "ar": "إعدادات التطبيق العامة",
        "en": "General Application Settings",
    },
    "settings_desc": {
        "ar": "تخصيص لغة التطبيق، خيارات التصدير، وسلوك الواجهة",
        "en": "Customize application language, export defaults, and UI behavior",
    },
    "settings_grp_language": {
        "ar": "لغة واجهة التطبيق (Application Language)",
        "en": "Application Language (لغة واجهة التطبيق)",
    },
    "settings_lbl_language": {
        "ar": "اختر لغة الواجهة:",
        "en": "Select UI Language:",
    },
    "settings_lang_arabic": {
        "ar": "العربية (الافتراضية) - Arabic (Default)",
        "en": "العربية (Arabic)",
    },
    "settings_lang_english": {
        "ar": "English - الإنجليزية",
        "en": "English (Default)",
    },
    "settings_grp_export": {
        "ar": "خيارات تصدير النتائج الافتراضية",
        "en": "Default Results Export Options",
    },
    "settings_lbl_export_fmt": {
        "ar": "صيغة التصدير التلقائية:",
        "en": "Default Export Format:",
    },
    "settings_chk_embedded": {
        "ar": "استخراج النصوص الرقمية المدمجة في ملفات PDF افتراضياً قبل محاولة OCR",
        "en": "Extract digital embedded PDF text first before attempting OCR",
    },
    "settings_grp_ui": {
        "ar": "سلوك الواجهة والنافذة",
        "en": "UI & Window Behavior",
    },
    "settings_chk_remember_size": {
        "ar": "تذكر أبعاد وموضع النافذة عند إعادة تشغيل البرنامج",
        "en": "Remember window geometry and size upon restart",
    },
    "settings_btn_save": {
        "ar": "حفظ الإعدادات",
        "en": "Save Settings",
    },
    "settings_btn_reset": {
        "ar": "استعادة ضبط المصنع",
        "en": "Restore Defaults",
    },
    "settings_saved_msg": {
        "ar": "تم حفظ الإعدادات بنجاح.",
        "en": "Settings saved successfully.",
    },

    # -------------------------------------------------------------
    # Dialogs & Common
    # -------------------------------------------------------------
    "copied_title": {
        "ar": "تم النسخ",
        "en": "Copied",
    },
    "copied_msg": {
        "ar": "تم نسخ النص إلى الحافظة بنجاح.",
        "en": "Text copied to clipboard successfully.",
    },
    "warning_title": {
        "ar": "تنبيه",
        "en": "Warning",
    },
    "error_title": {
        "ar": "خطأ",
        "en": "Error",
    },
    "confirm_title": {
        "ar": "تأكيد",
        "en": "Confirmation",
    },
}


class I18n:
    """Internationalization helper class."""

    _current_lang: str = "ar"

    @classmethod
    def get_current_language(cls) -> str:
        """Returns currently active language code ('ar' or 'en')."""
        return cls._current_lang

    @classmethod
    def set_current_language(cls, lang: str) -> None:
        """Sets active language ('ar' or 'en')."""
        if lang in ("ar", "en"):
            cls._current_lang = lang

    @classmethod
    def is_rtl(cls) -> bool:
        """Returns True if the active language is Right-to-Left (Arabic)."""
        return cls._current_lang == "ar"

    @classmethod
    def tr(cls, key: str, **kwargs) -> str:
        """
        Translates a key into the active language, formatting placeholders if provided.

        Args:
            key: Translation key.
            **kwargs: Optional string format kwargs.

        Returns:
            Translated string or key fallback.
        """
        item = TRANSLATIONS.get(key)
        if not item:
            return key

        text = item.get(cls._current_lang) or item.get("ar", key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text


# Global convenient alias
tr = I18n.tr
