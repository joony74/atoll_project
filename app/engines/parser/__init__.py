"""Parser engines."""
"""Math parsing helpers used between OCR and solver routing."""

from app.engines.parser.math_candidate_ranker import (
    RankedMathCandidate,
    extract_expression_texts,
    iter_ranked_math_candidates,
    select_problem_statement,
)
from app.engines.parser.math_ocr_normalizer import clean_visible_math_text, normalize_ocr_math_text
from app.engines.parser.school_math_taxonomy import classify_school_math_topic, topic_label

__all__ = [
    "RankedMathCandidate",
    "classify_school_math_topic",
    "clean_visible_math_text",
    "extract_expression_texts",
    "iter_ranked_math_candidates",
    "normalize_ocr_math_text",
    "select_problem_statement",
    "topic_label",
]
