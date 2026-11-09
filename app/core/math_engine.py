"""
نظام التعرف على المعادلات الرياضية واستخراجها بصيغة LaTeX لنظام نَصّ (NASS).
نظام تركيبي مرن واختياري يدعم محرك pix2tex، والمكتشف الرياضي المدمج، والمزودات الخارجية.
"""

from __future__ import annotations

import abc
import importlib.util
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image

from app.utils.logger import logger


@dataclass
class MathEquation:
    """بيانات معادلة رياضية مستخرجة."""
    latex: str
    confidence: float = 1.0
    description: Optional[str] = None
    source: str = "auto"


class MathEngineBase(abc.ABC):
    """الواجهة الأساسية لأي محرك للتعرف على المعادلات الرياضية."""

    @abc.abstractmethod
    def is_available(self) -> Tuple[bool, str]:
        """التحقق مما إذا كان المحرك مثبتاً ومتوفراً للاستخدام."""
        pass

    @abc.abstractmethod
    def extract_equations(
        self,
        image: Optional[Image.Image] = None,
        text_context: Optional[str] = None,
    ) -> List[MathEquation]:
        """استخراج المعادلات الرياضية بصيغة LaTeX."""
        pass


class Pix2TexMathEngine(MathEngineBase):
    """
    محرك التعرف على المعادلات الرياضية باستخدام نماذج pix2tex والتعلم العميق.
    يعمل كإضافة اختيارية دون إلزام المستخدم بتنزيل مكتبات ضخمة إلا برغبته.
    """

    def __init__(self):
        self._model = None
        self._is_loading = False

    def is_available(self) -> Tuple[bool, str]:
        """فحص توفر مكتبة pix2tex ونموذجها."""
        has_pix2tex = importlib.util.find_spec("pix2tex") is not None
        has_torch = importlib.util.find_spec("torch") is not None

        if not has_torch or not has_pix2tex:
            return (
                False,
                "محرك pix2tex غير مثبت حالياً. هو إضافة اختيارية تتطلب تنزيل PyTorch و pix2tex."
            )
        return True, "محرك pix2tex مثبت وجاهز للتعرف على المعادلات."

    def _ensure_model_loaded(self):
        """تحميل نموذج pix2tex في الذاكرة عند الحاجة فقط."""
        if self._model is not None:
            return

        available, msg = self.is_available()
        if not available:
            raise RuntimeError(msg)

        try:
            from pix2tex.cli import LatexOCR
            self._model = LatexOCR()
            logger.info("تم تحميل نموذج pix2tex بنجاح.")
        except Exception as e:
            logger.error(f"فشل تحميل نموذج pix2tex: {e}")
            raise RuntimeError(f"تعذر تهيئة نموذج pix2tex: {e}")

    def extract_equations(
        self,
        image: Optional[Image.Image] = None,
        text_context: Optional[str] = None,
    ) -> List[MathEquation]:
        """تحويل الصورة إلى صيغة LaTeX عبر pix2tex."""
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
            logger.warning(f"تعذر استخراج المعادلة عبر pix2tex: {e}")

        return []


class BuiltinMathDetector(MathEngineBase):
    """
    مكتشف ومحلل رياضي مدمج وخفيف الوزن.
    يكتشف الرموز والصيغ الرياضية (الكسور، الجذور، الأسس، الرموز الإغريقية، التكامل، المجموع)
    ويحولها إلى صيغة LaTeX نقية ومنسقة بدون الحاجة إلى مكتبات خارجية ضخمة.
    """

    # أنماط التعرف على التعابير الرياضية
    MATH_PATTERNS = [
        # المعادلات الحسابية مع علامة = أو ≈ أو ≠
        re.compile(r"([a-zA-Z\d\(\)\[\]\+\-\*/\^]+\s*[=≈≠<>≤≥]\s*[a-zA-Z\d\(\)\[\]\+\-\*/\^]+)"),
        # الجذور (مثل sqrt(x) أو جذر)
        re.compile(r"sqrt\(([^)]+)\)", re.IGNORECASE),
        # الكسور مثل (a)/(b) أو a/b
        re.compile(r"(\([a-zA-Z\d\+\-\*]+\)\s*/\s*\([a-zA-Z\d\+\-\*]+\))"),
        # التكامل والمجموع
        re.compile(r"(\\?int|∫)\s*([^\s=]+)\s*d([a-zA-Z])"),
        re.compile(r"(\\?sum|∑)\s*([^\n]+)"),
    ]

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
        """استخراج وتنسيق المعادلات من النص المستخرج وتحويلها إلى LaTeX."""
        if not text_context or not text_context.strip():
            return []

        results: List[MathEquation] = []
        lines = text_context.splitlines()

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # فحص إذا كان السطر يحتوي على مؤشرات رياضية قوية
            has_math_indicator = any(
                sym in line_str for sym in ["=", "∫", "∑", "√", "±", "≤", "≥", "≠", "lim", "sin", "cos", "tan", "log", "ln"]
            ) or ("^" in line_str) or ("/" in line_str and any(c.isdigit() for c in line_str))

            if has_math_indicator:
                # تحويل السطر أو التعبير إلى صيغة LaTeX نظيفة
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
        """تحويل تعبير رياضي خام إلى كود LaTeX صالح."""
        s = expr.strip()
        # إزالة النقاط أو العبارات غير الرياضية إذا كانت في بداية/نهاية السطر
        s = re.sub(r"^[•\-\*\d+\.\)]\s*", "", s)

        if len(s) < 3:
            return None

        # استبدال الرموز الخاصة
        for sym, replacement in self.GREEK_SYMBOLS.items():
            s = s.replace(sym, f" {replacement} ")

        # استبدال sqrt(x) بـ \sqrt{x}
        s = re.sub(r"sqrt\s*\(([^)]+)\)", r"\\sqrt{\1}", s, flags=re.IGNORECASE)
        s = re.sub(r"√\s*\(([^)]+)\)", r"\\sqrt{\1}", s)
        s = re.sub(r"√([a-zA-Z\d]+)", r"\\sqrt{\1}", s)

        # استبدال الأسس x^2 أو x^n
        s = re.sub(r"\^(\d+|[a-zA-Z])", r"^{\1}", s)

        # استبدال الكسر (a)/(b) بـ \frac{a}{b}
        s = re.sub(r"\(([^)]+)\)\s*/\s*\(([^)]+)\)", r"\\frac{\1}{\2}", s)

        # استبدال علامة الضرب * أو x بين الأرقام
        s = re.sub(r"(\d+)\s*[\*×]\s*(\d+)", r"\1 \\times \2", s)

        # تنظيف الفراغات المكررة
        s = re.sub(r"\s+", " ", s).strip()

        # إحاطة التعبير بـ $$ إذا لم يكن محاطاً
        if not s.startswith("$"):
            return f"$${s}$$"
        return s


class MathRecognitionService:
    """خدمة تنسيق واستدعاء محركات التعرف على المعادلات الرياضية."""

    def __init__(self, preferred_engine: str = "builtin"):
        self.preferred_engine = preferred_engine
        self.builtin_engine = BuiltinMathDetector()
        self.pix2tex_engine = Pix2TexMathEngine()

    def get_engine_status(self) -> Dict[str, Any]:
        """الحصول على حالة المحركات الرياضية المتوفرة."""
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
        """
        استخراج المعادلات الرياضية بأمان دون إيقاف البرنامج عند أي خطأ.
        """
        equations: List[MathEquation] = []

        # 1. إذا كان pix2tex مفضلاً ومتاحاً ولدينا صورة
        if self.preferred_engine == "pix2tex" and image is not None:
            available, _ = self.pix2tex_engine.is_available()
            if available:
                try:
                    p_eqs = self.pix2tex_engine.extract_equations(image=image)
                    equations.extend(p_eqs)
                except Exception as e:
                    logger.warning(f"فشل محرك pix2tex: {e}")

        # 2. الاستعانة بالمكتشف المدمج للنصوص المستخرجة
        if text_context:
            try:
                b_eqs = self.builtin_engine.extract_equations(text_context=text_context)
                # دمج النتائج بدون تكرار
                existing_latex = {eq.latex for eq in equations}
                for eq in b_eqs:
                    if eq.latex not in existing_latex:
                        equations.append(eq)
            except Exception as e:
                logger.warning(f"فشل المكتشف المدمج للمعادلات: {e}")

        return equations
