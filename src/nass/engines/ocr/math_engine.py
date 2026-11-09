"""
Mathematical formula and equation extraction system for NASS.
Provides a modular architecture supporting built-in pattern detection and deep-learning pix2tex.
"""

from __future__ import annotations

import abc
import importlib.util
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image

from nass.utils.logger import logger


@dataclass
class MathEquation:
    """Extracted mathematical formula data in LaTeX format."""
    latex: str
    confidence: float = 1.0
    description: Optional[str] = None
    source: str = "auto"


class MathEngineBase(abc.ABC):
    """Abstract interface for mathematical formula recognition engines."""

    @abc.abstractmethod
    def is_available(self) -> Tuple[bool, str]:
        """Check if engine dependencies and models are available."""
        pass

    @abc.abstractmethod
    def extract_equations(
        self,
        image: Optional[Image.Image] = None,
        text_context: Optional[str] = None,
    ) -> List[MathEquation]:
        """Extract mathematical equations into LaTeX syntax."""
        pass


class Pix2TexMathEngine(MathEngineBase):
    """Deep learning math recognition using pix2tex."""

    def __init__(self):
        self._model = None

    def is_available(self) -> Tuple[bool, str]:
        """Check if pix2tex and torch dependencies are installed."""
        has_pix2tex = importlib.util.find_spec("pix2tex") is not None
        has_torch = importlib.util.find_spec("torch") is not None

        if not has_torch or not has_pix2tex:
            return (
                False,
                "محرك pix2tex غير مثبت حالياً. هو إضافة اختيارية تتطلب تنزيل PyTorch و pix2tex."
            )
        return True, "محرك pix2tex مثبت وجاهز للتعرف على المعادلات."

    def _ensure_model_loaded(self):
        """Lazy load pix2tex model into memory upon first use."""
        if self._model is not None:
            return

        available, msg = self.is_available()
        if not available:
            raise RuntimeError(msg)

        try:
            from pix2tex.cli import LatexOCR
            self._model = LatexOCR()
            logger.info("pix2tex model initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to load pix2tex model: {e}")
            raise RuntimeError(f"Could not load pix2tex: {e}")

    def extract_equations(
        self,
        image: Optional[Image.Image] = None,
        text_context: Optional[str] = None,
    ) -> List[MathEquation]:
        """Convert image region to LaTeX formula."""
        if image is None:
            return []

        try:
            self._ensure_model_loaded()
            latex_str = self._model(image)
            if latex_str and latex_str.strip():
                return [
                    MathEquation(
                        latex=latex_str.strip(),
                        confidence=0.95,
                        description="معادلة مستخرجة بنموذج pix2tex",
                        source="pix2tex",
                    )
                ]
        except Exception as e:
            logger.warning(f"Failed to extract equation via pix2tex: {e}")

        return []


class BuiltinMathDetector(MathEngineBase):
    """
    Lightweight, fast built-in mathematical pattern detector.
    Recognizes fractions, roots, exponents, Greek symbols, integrals, and sums,
    converting them to standardized LaTeX.
    """

    GREEK_SYMBOLS = {
        "alpha": r"\alpha", "beta": r"\beta", "gamma": r"\gamma",
        "theta": r"\theta", "lambda": r"\lambda", "pi": r"\pi",
        "sigma": r"\sigma", "omega": r"\omega", "delta": r"\delta",
        "α": r"\alpha", "β": r"\beta", "γ": r"\gamma", "θ": r"\theta",
        "λ": r"\lambda", "π": r"\pi", "σ": r"\sigma", "ω": r"\omega",
        "Δ": r"\Delta", "∑": r"\sum", "∫": r"\int", "√": r"\sqrt",
        "∞": r"\infty", "±": r"\pm", "≤": r"\le", "≥": r"\ge", "≠": r"\ne",
    }

    def is_available(self) -> Tuple[bool, str]:
        return True, "المكتشف الرياضي المدمج متوفر ويعمل تلقائياً."

    def extract_equations(
        self,
        image: Optional[Image.Image] = None,
        text_context: Optional[str] = None,
    ) -> List[MathEquation]:
        """Extract mathematical equations from extracted text context."""
        if not text_context or not text_context.strip():
            return []

        results: List[MathEquation] = []
        lines = text_context.splitlines()

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            has_math_indicator = any(
                sym in line_str for sym in ["=", "∫", "∑", "√", "±", "≤", "≥", "≠", "lim", "sin", "cos", "tan", "log", "ln"]
            ) or ("^" in line_str) or ("/" in line_str and any(c.isdigit() for c in line_str))

            if has_math_indicator:
                latex_expr = self._convert_to_latex(line_str)
                if latex_expr:
                    results.append(
                        MathEquation(
                            latex=latex_expr,
                            confidence=0.85,
                            description=f"تعبير رياضي: {line_str[:40]}",
                            source="builtin",
                        )
                    )

        return results

    def _convert_to_latex(self, expr: str) -> Optional[str]:
        """Convert plain text mathematical expression into valid LaTeX string."""
        s = expr.strip()
        s = re.sub(r"^[•\-\*\d+\.\)]\s*", "", s)

        if len(s) < 3:
            return None

        for sym, replacement in self.GREEK_SYMBOLS.items():
            s = s.replace(sym, f" {replacement} ")

        s = re.sub(r"sqrt\s*\(([^)]+)\)", r"\\sqrt{\1}", s, flags=re.IGNORECASE)
        s = re.sub(r"√\s*\(([^)]+)\)", r"\\sqrt{\1}", s)
        s = re.sub(r"√([a-zA-Z\d]+)", r"\\sqrt{\1}", s)
        s = re.sub(r"\^(\d+|[a-zA-Z])", r"^{\1}", s)
        s = re.sub(r"\(([^)]+)\)\s*/\s*\(([^)]+)\)", r"\\frac{\1}{\2}", s)
        s = re.sub(r"(\d+)\s*[\*×]\s*(\d+)", r"\1 \\times \2", s)
        s = re.sub(r"\s+", " ", s).strip()

        if not s.startswith("$"):
            return f"$${s}$$"
        return s


class MathRecognitionService:
    """High-level coordinator for mathematical formula extraction."""

    def __init__(self, preferred_engine: str = "builtin"):
        self.preferred_engine = preferred_engine
        self.builtin_engine = BuiltinMathDetector()
        self.pix2tex_engine = Pix2TexMathEngine()

    def get_engine_status(self) -> Dict[str, Any]:
        """Check status of all math engines."""
        p_ok, p_msg = self.pix2tex_engine.is_available()
        b_ok, b_msg = self.builtin_engine.is_available()

        return {
            "pix2tex_available": p_ok,
            "pix2tex_message": p_msg,
            "builtin_available": b_ok,
            "builtin_message": b_msg,
            "preferred_engine": self.preferred_engine,
        }

    def extract_equations(
        self,
        image: Optional[Image.Image] = None,
        text_context: Optional[str] = None,
    ) -> List[MathEquation]:
        """Safely extract formulas without interrupting normal workflow."""
        equations: List[MathEquation] = []

        if self.preferred_engine == "pix2tex" and image is not None:
            available, _ = self.pix2tex_engine.is_available()
            if available:
                try:
                    p_eqs = self.pix2tex_engine.extract_equations(image=image)
                    equations.extend(p_eqs)
                except Exception as e:
                    logger.warning(f"pix2tex extraction failed: {e}")

        if text_context:
            try:
                b_eqs = self.builtin_engine.extract_equations(text_context=text_context)
                existing_latex = {eq.latex for eq in equations}
                for eq in b_eqs:
                    if eq.latex not in existing_latex:
                        equations.append(eq)
            except Exception as e:
                logger.warning(f"Built-in math detector failed: {e}")

        return equations


# Compatibility alias
MathRecognitionEngine = MathRecognitionService
