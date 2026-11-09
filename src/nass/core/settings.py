"""
Local settings manager for the NASS application.
Persists application and OCR configuration to a local JSON file.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

from nass.core.config import PROJECT_ROOT
from nass.core.i18n import I18n
from nass.utils.logger import logger

# Configuration directory in user profile
USER_CONFIG_DIR = Path.home() / ".nass"
SETTINGS_FILE_PATH = USER_CONFIG_DIR / "settings.json"


@dataclass
class AppSettings:
    """Application preferences and engine settings."""
    app_language: str = "ar"
    tesseract_custom_path: Optional[str] = None
    tessdata_custom_path: Optional[str] = None

    default_language: str = "ara+eng"
    dpi: int = 300
    psm: int = 3
    oem: int = 3

    apply_enhancement: bool = False
    enhance_contrast: bool = False
    denoise: bool = False
    threshold: bool = False
    deskew: bool = False

    extract_embedded_first: bool = True
    math_enabled: bool = False
    math_engine: str = "builtin"

    export_default_format: str = "txt"
    remember_window_size: bool = True
    window_width: int = 1200
    window_height: int = 800

    tesseract_extra_config: str = ""


class SettingsManager:
    """Singleton manager for reading, updating, and saving application settings."""

    _instance: Optional[SettingsManager] = None

    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or SETTINGS_FILE_PATH
        self.settings: AppSettings = self.load()

    @classmethod
    def get_instance(cls) -> SettingsManager:
        """Get the shared singleton instance of SettingsManager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load(self) -> AppSettings:
        """Load settings from JSON file or return default configuration."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                valid_fields = {k: v for k, v in data.items() if hasattr(AppSettings, k)}
                logger.debug(f"Loaded settings from {self.config_file}")
                settings = AppSettings(**valid_fields)
                I18n.set_current_language(settings.app_language)
                return settings
            except Exception as e:
                logger.warning(f"Failed to read settings file ({e}). Using defaults.")
        default_settings = AppSettings()
        I18n.set_current_language(default_settings.app_language)
        return default_settings

    def save(self) -> bool:
        """Serialize current settings to the JSON configuration file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(asdict(self.settings), f, indent=2, ensure_ascii=False)
            logger.debug(f"Settings saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False

    def reset_to_defaults(self) -> AppSettings:
        """Reset all configuration values to defaults and save."""
        self.settings = AppSettings()
        self.save()
        return self.settings

    def get(self, key: str, default: Any = None) -> Any:
        """Get the value of a specific setting key."""
        return getattr(self.settings, key, default)

    def set(self, key: str, value: Any, auto_save: bool = True):
        """Update a specific setting key and optionally persist to disk."""
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)
            if key == "app_language":
                I18n.set_current_language(str(value))
            if auto_save:
                self.save()
        else:
            raise KeyError(f"Unknown setting key: {key}")
