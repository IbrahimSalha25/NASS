"""
Unit tests for mathematical formula recognition engine (Math Engine).
"""

from PIL import Image

from app.core.math_engine import (
    BuiltinMathDetector,
    MathRecognitionService,
    Pix2TexMathEngine,
)


def test_builtin_math_detector_fraction():
    detector = BuiltinMathDetector()
    text = "The formula is (x + 1)/(y - 2) = z"
    eqs = detector.extract_equations(text_context=text)
    assert len(eqs) > 0
    assert r"\frac" in eqs[0].latex or "=" in eqs[0].latex


def test_builtin_math_detector_square_root():
    detector = BuiltinMathDetector()
    text = "Find the value of sqrt(b^2 - 4ac) >= 0"
    eqs = detector.extract_equations(text_context=text)
    assert len(eqs) > 0
    assert r"\sqrt" in eqs[0].latex


def test_builtin_math_detector_greek_and_sum():
    detector = BuiltinMathDetector()
    text = "Total energy is ∑ E_i = alpha * beta + pi"
    eqs = detector.extract_equations(text_context=text)
    assert len(eqs) > 0
    assert r"\alpha" in eqs[0].latex or r"\sum" in eqs[0].latex


def test_pix2tex_engine_availability():
    engine = Pix2TexMathEngine()
    available, msg = engine.is_available()
    assert isinstance(available, bool)
    assert isinstance(msg, str)


def test_math_recognition_service():
    service = MathRecognitionService()
    status = service.get_engine_status()
    assert "builtin_available" in status
    assert status["builtin_available"] is True

    # Test extraction from equation-containing text
    text = "y = 2*x + 5"
    eqs = service.extract_equations(text_context=text)
    assert len(eqs) > 0
    assert "2 \\times x" in eqs[0].latex or "y" in eqs[0].latex
