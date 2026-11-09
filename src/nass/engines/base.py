"""
Abstract base class for all file text extractors in NASS.
"""

from __future__ import annotations

import abc
from pathlib import Path
from typing import Callable, Optional

from nass.core.models import DocumentResult, ExtractionMethod, OcrOptions, PageResult


class BaseExtractor(abc.ABC):
    """Abstract text extractor providing a unified interface for all supported formats."""

    @abc.abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """Return True if this extractor supports the given file format."""
        pass

    @abc.abstractmethod
    def extract(
        self,
        file_path: Path,
        options: OcrOptions,
        progress_callback: Optional[Callable[[int, int, PageResult], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> DocumentResult:
        """
        Extract text content from the given file path.
        Returns a populated DocumentResult instance.
        """
        pass

    @property
    def extraction_method(self) -> ExtractionMethod:
        """Default extraction method for this extractor."""
        return ExtractionMethod.NATIVE
