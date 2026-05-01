from __future__ import annotations

import unittest
from unittest.mock import patch

from app.core import pipeline
from app.models.problem_schema import ProblemSchema
from app.models.solve_result import SolveResult


class UnifiedServiceEngineTests(unittest.TestCase):
    def test_service_image_analysis_wraps_single_solve_pipeline_entrypoint(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="3+4",
            expressions=["3+4"],
            math_topic="arithmetic",
            metadata={"content_hash": "case-1"},
        )
        solved = SolveResult(
            solver_name="arithmetic_solver",
            computed_answer="7",
            validation_status="verified",
        )

        with patch.object(
            pipeline,
            "run_solve_pipeline",
            return_value={
                "structured_problem": problem,
                "solve_result": solved,
                "debug": {"analysis_engine": pipeline.service_engine_info(mode="service_image_analysis")},
            },
        ) as run_solve:
            analysis = pipeline.run_service_image_analysis("/tmp/case.png", user_query="풀이", debug=True)

        run_solve.assert_called_once_with(image_path="/tmp/case.png", user_query="풀이", debug=True)
        self.assertEqual(analysis["analysis_engine"]["engine_id"], pipeline.SERVICE_ENGINE_ID)
        self.assertEqual(analysis["analysis_engine"]["pipeline_entrypoint"], "app.core.pipeline.run_solve_pipeline")
        self.assertEqual(analysis["structured_problem"]["normalized_problem_text"], "3+4")
        self.assertEqual(analysis["solve_result"]["computed_answer"], "7")

    def test_solve_pipeline_stamps_engine_metadata_for_structured_problem(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="3+4",
            expressions=["3+4"],
            math_topic="arithmetic",
        )

        payload = pipeline.run_solve_pipeline(structured_problem=problem, debug=True)

        metadata = payload["structured_problem"].metadata
        debug = payload["debug"]
        self.assertEqual(metadata["analysis_engine"]["engine_id"], pipeline.SERVICE_ENGINE_ID)
        self.assertEqual(debug["analysis_engine"]["engine_version"], pipeline.SERVICE_ENGINE_VERSION)


if __name__ == "__main__":
    unittest.main()
