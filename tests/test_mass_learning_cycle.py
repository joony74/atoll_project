from __future__ import annotations

import unittest

from scripts.run_mass_learning_cycle import build_report, build_steps, create_parser


class MassLearningCycleTests(unittest.TestCase):
    def test_builds_default_sequential_cycle(self) -> None:
        args = create_parser().parse_args(["--python", "python-test"])

        steps = build_steps(args)
        commands = [" ".join(step.command) for step in steps]

        self.assertEqual(steps[0].name, "Import MetaMathQA sample")
        self.assertIn("scripts/import_metamathqa_problem_bank.py --limit 20000", commands[0])
        self.assertIn("scripts/import_deepmind_mathematics_problem_bank.py --per-module 10", commands[1])
        self.assertIn("scripts/build_problem_generation_profile.py", commands[2])
        self.assertIn("scripts/build_math_normalization_profile.py", commands[3])
        self.assertIn("scripts/build_ocr_normalization_regression.py", commands[4])
        self.assertIn("scripts/capture_actual_ocr_regression_cases.py", commands[5])
        self.assertEqual(steps[-1].command, ("python-test", "-m", "unittest", "discover", "-s", "tests"))

    def test_skip_options_keep_profile_refresh(self) -> None:
        args = create_parser().parse_args(
            ["--python", "python-test", "--skip-import", "--skip-actual-ocr", "--skip-tests"]
        )

        commands = [" ".join(step.command) for step in build_steps(args)]

        self.assertFalse(any("import_metamathqa_problem_bank.py" in command for command in commands))
        self.assertFalse(any("capture_actual_ocr_regression_cases.py" in command for command in commands))
        self.assertFalse(any("unittest discover" in command for command in commands))
        self.assertTrue(any("build_problem_generation_profile.py" in command for command in commands))
        self.assertTrue(any("build_math_normalization_profile.py" in command for command in commands))

    def test_report_marks_failed_step(self) -> None:
        args = create_parser().parse_args(["--python", "python-test", "--skip-tests"])
        report = build_report(
            args,
            [
                {"name": "passed", "returncode": 0},
                {"name": "failed", "returncode": 2},
            ],
            1.25,
        )

        self.assertEqual(report["schema_version"], "coco_mass_learning_cycle_report.v1")
        self.assertFalse(report["success"])
        self.assertEqual(report["summary"]["failed_step_count"], 1)
        self.assertEqual(report["summary"]["failed_steps"], ["failed"])


if __name__ == "__main__":
    unittest.main()
