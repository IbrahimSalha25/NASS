"""
Core exceptions for the NASS application.
"""

from __future__ import annotations


class NassException(Exception):
    """Base exception for all NASS operations."""
    pass


class FileProcessingError(NassException):
    """Raised when an error occurs during file parsing or extraction."""
    pass


class UnsupportedFormatError(FileProcessingError):
    """Raised when an unsupported file format is encountered."""
    pass


class OcrEngineError(NassException):
    """Raised when an error occurs in the OCR engine or Tesseract."""
    pass


class LanguagePackError(NassException):
    """Raised when an error occurs during language pack downloading or installation."""
    pass
