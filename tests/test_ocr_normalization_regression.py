from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from app.engines.parser.math_ocr_normalizer import normalize_ocr_math_text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGRESSION_PATH = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "coco_ocr_regression_cases.json"
ACTUAL_OCR_PATH = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "coco_ocr_actual_cases.json"


def compact(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "").replace("**", "^"))


class OCRNormalizationRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(REGRESSION_PATH.read_text(encoding="utf-8"))
        cls.actual_payload = json.loads(ACTUAL_OCR_PATH.read_text(encoding="utf-8"))

    def test_regression_set_has_problem_bank_coverage(self) -> None:
        payload = self.payload
        coverage = payload["coverage"]

        self.assertEqual(payload["schema_version"], "coco_ocr_regression_cases.v1")
        self.assertGreaterEqual(coverage["case_count"], 100)
        self.assertGreaterEqual(coverage["by_bank"].get("competition_math", 0), 1)
        self.assertGreaterEqual(coverage["by_bank"].get("metamathqa", 0), 1)
        self.assertGreaterEqual(coverage["by_bank"].get("tal_scq5k", 0), 1)
        self.assertGreaterEqual(coverage["by_bank"].get("deepmind_mathematics", 0), 1)
        self.assertGreaterEqual(coverage["by_reason"].get("latex_runtime_rewrite", 0), 1)
        self.assertGreaterEqual(coverage["by_reason"].get("sqrt_spacing", 0), 1)
        self.assertGreaterEqual(coverage["by_reason"].get("power_degree_mark", 0), 1)

    def test_all_regression_cases_normalize_to_expected_expression(self) -> None:
        failures: list[str] = []
        for case in self.payload["cases"]:
            normalized = normalize_ocr_math_text(case["noisy_text"])
            expected = compact(case["expected_contains"])
            if expected not in compact(normalized):
                failures.append(
                    f"{case['case_id']} {case['reason']} expected={case['expected_contains']!r} got={normalized!r}"
                )

        self.assertFalse(failures, "\n".join(failures[:20]))

    def test_actual_ocr_capture_cases_have_grade_coverage(self) -> None:
        coverage = self.actual_payload["coverage"]

        self.assertEqual(self.actual_payload["schema_version"], "coco_ocr_actual_cases.v1")
        self.assertGreaterEqual(coverage["case_count"], 30)
        self.assertGreaterEqual(len(coverage["by_grade"]), 8)
        self.assertGreaterEqual(coverage["by_ocr_source"].get("pipeline_raw_text", 0), 1)

    def test_actual_ocr_capture_cases_still_normalize(self) -> None:
        failures: list[str] = []
        for case in self.actual_payload["cases"]:
            normalized = normalize_ocr_math_text(case["noisy_text"])
            expected = compact(case["expected_contains"])
            if expected not in compact(normalized):
                failures.append(
                    f"{case['case_id']} {case['problem_id']} expected={case['expected_contains']!r} got={normalized!r}"
                )

        self.assertFalse(failures, "\n".join(failures[:20]))


if __name__ == "__main__":
    unittest.main()
