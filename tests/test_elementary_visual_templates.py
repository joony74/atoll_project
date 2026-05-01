from __future__ import annotations

import unittest

from app.core.pipeline import run_solve_pipeline
from app.engines.parser.elementary_visual_templates import infer_elementary_visual_template
from app.models.problem_schema import ProblemSchema


class ElementaryVisualTemplateTests(unittest.TestCase):
    def test_infers_grade1_numbers_to_9_card_template(self) -> None:
        template = infer_elementary_visual_template(
            "/tmp/초1-1_1단원_9까지의수_1회_p01_문항10.png",
        )

        self.assertIsNotNone(template)
        assert template is not None
        self.assertEqual(template.expression, "answer=6")
        self.assertIn("1 큰 수", template.problem_text)

    def test_infers_toctoc_grade1_write_numbers_page_template(self) -> None:
        template = infer_elementary_visual_template(
            "/tmp/19605e1f6a9d_toctoc_g1_s1_똑똑수학탐험대_1학년_1학기_함께학습지_p15.png",
        )

        self.assertIsNotNone(template)
        assert template is not None
        self.assertEqual(template.expression, "answer_text=6, 7, 8, 9")
        self.assertEqual(template.rule_id, "toctoc_grade1_write_numbers_6_to_9_page15")

    def test_infers_grade1_page2_visual_templates(self) -> None:
        template = infer_elementary_visual_template(
            "/tmp/초1-1_1단원_9까지의수_1회_p02_문항08.png",
        )

        self.assertIsNotNone(template)
        assert template is not None
        self.assertEqual(template.expression, "answer_text=(1) 1, 2, 3 / (2) 6, 7, 8")
        self.assertIn("맞는 수", template.problem_text)

    def test_infers_grade1_round2_page2_visual_templates(self) -> None:
        cases = {
            "문항03": "answer_text=빈칸: 9, 6, 5, 3, 2",
            "문항05": "answer=7",
            "문항07": "answer_text=9, 4, 2",
            "문항08": "answer_text=3개",
            "문항09": "answer_text=민수",
            "문항11": "answer_text=8살",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-1_1단원_9까지의수_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_round2_page1_visual_templates(self) -> None:
        cases = {
            "문항01": "answer_text=(1) ○ 3개, (2) ○ 6개",
            "문항02": "answer_text=하나, 일",
            "문항03": "answer=8",
            "문항04": "answer_text=1, 2, 3",
            "문항05": "answer=6",
            "문항06": "answer=6",
            "문항07": "answer_text=첫째-나, 셋째-가, 넷째-다, 둘째-라, 다섯째-마",
            "문항08": "answer_text=빈칸: 여섯째, 여덟째",
            "문항09": "answer_text=수박",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-1_1단원_9까지의수_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_round3_page1_visual_templates(self) -> None:
        cases = {
            "문항02": "answer_text=5 / 다섯, 오",
            "문항03": "answer=7",
            "문항04": "answer_text=7, 8, 9",
            "문항05": "answer=8",
            "문항06": "answer=7",
            "문항07": "answer_text=첫째-다, 둘째-나, 셋째-라, 넷째-마, 다섯째-가",
            "문항08": "answer_text=왼쪽에서 여섯째 꽃",
            "문항09": "answer=8",
            "문항10": "answer_text=빈칸: 3, 6",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-1_1단원_9까지의수_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_round3_page2_visual_templates(self) -> None:
        cases = {
            "문항01": "answer_text=빈칸: 7, 6, 4, 1",
            "문항03": "answer=6",
            "문항05": "answer=1",
            "문항06": "answer_text=3개",
            "문항07": "answer_text=5살",
            "문항10": "answer_text=지수",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-1_1단원_9까지의수_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_shapes_round1_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=3개",
            ("p01", "문항02"): "answer_text=3개",
            ("p01", "문항03"): "answer_text=3개",
            ("p01", "문항04"): "answer_text=상자 모양",
            ("p01", "문항05"): "answer_text=둥근기둥 모양",
            ("p01", "문항06"): "answer_text=풍선-공 모양, 음료수 캔-둥근기둥 모양, 휴지상자-상자 모양",
            ("p01", "문항07"): "answer_text=다",
            ("p01", "문항08"): "answer_text=휴지상자",
            ("p02", "문항01"): "answer_text=나",
            ("p02", "문항02"): "answer_text=가",
            ("p02", "문항03"): "answer_text=야구공-공 모양, 전자레인지-상자 모양, 롤티슈-둥근기둥 모양",
            ("p02", "문항04"): "answer_text=상자 모양, 둥근기둥 모양, 공 모양",
            ("p02", "문항05"): "answer_text=롤티슈",
            ("p02", "문항06"): "answer_text=상자 모양-상자, 둥근기둥 모양-둥근기둥, 공 모양-공",
            ("p02", "문항07"): "answer_text=공 모양",
            ("p02", "문항08"): "answer_text=은아",
            ("p03", "문항01"): "answer_text=2개",
            ("p03", "문항02"): "answer_text=공 모양",
            ("p03", "문항03"): "answer_text=상자 모양 1개, 둥근기둥 모양 4개, 공 모양 2개",
            ("p03", "문항04"): "answer_text=공 모양",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-1_2단원_여러가지모양_1회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "geometry")
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_shapes_round2_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=4개",
            ("p01", "문항02"): "answer_text=1개",
            ("p01", "문항03"): "answer_text=2개",
            ("p01", "문항04"): "answer_text=둥근기둥 모양",
            ("p01", "문항05"): "answer_text=둥근기둥 모양",
            ("p01", "문항06"): "answer_text=참치캔-둥근기둥 모양, 농구공-공 모양, 지우개-상자 모양",
            ("p01", "문항07"): "answer_text=나",
            ("p02", "문항01"): "answer_text=축구공",
            ("p02", "문항02"): "answer_text=나",
            ("p02", "문항03"): "answer_text=나",
            ("p03", "문항01"): "answer_text=동준",
            ("p03", "문항05"): "answer_text=둥근기둥 모양",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-1_2단원_여러가지모양_2회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "geometry")
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_shapes_round3_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=2개",
            ("p01", "문항02"): "answer_text=2개",
            ("p01", "문항03"): "answer_text=2개",
            ("p01", "문항04"): "answer_text=공 모양",
            ("p01", "문항05"): "answer_text=상자 모양",
            ("p01", "문항06"): "answer_text=축구공-공 모양, 동화책-상자 모양, 통-둥근기둥 모양",
            ("p01", "문항07"): "answer_text=가",
            ("p02", "문항01"): "answer_text=휴지상자",
            ("p02", "문항02"): "answer_text=가",
            ("p02", "문항03"): "answer_text=나",
            ("p02", "문항05"): "answer_text=상자 모양, 둥근기둥 모양",
            ("p02", "문항06"): "answer_text=연필꽂이",
            ("p03", "문항01"): "answer_text=찬우",
            ("p03", "문항02"): "answer_text=3개",
            ("p03", "문항03"): "answer_text=공 모양",
            ("p03", "문항04"): "answer_text=상자 모양 1개, 둥근기둥 모양 5개, 공 모양 4개",
            ("p03", "문항05"): "answer_text=둥근기둥 모양",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-1_2단원_여러가지모양_3회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "geometry")
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_shape_visual_template(self) -> None:
        template = infer_elementary_visual_template(
            "/tmp/초1-1_2단원_여러가지모양_2회_p01_문항04.png",
        )

        self.assertIsNotNone(template)
        assert template is not None
        self.assertEqual(template.topic, "geometry")
        self.assertEqual(template.expression, "answer_text=둥근기둥 모양")

    def test_infers_grade1_second_semester_shapes_round1_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=1번: ○ 모양 2개 색칠 / 2번: 세모 모양 카드",
            ("p01", "문항03"): "answer_text=□ 2개, △ 2개, ○ 2개",
            ("p01", "문항06"): "answer=5",
            ("p02", "문항01"): "answer_text=주차금지 표지판",
            ("p02", "문항05"): "answer_text=△ 모양",
            ("p02", "문항09"): "answer_text=○ 모양",
            ("p03", "문항01"): "answer=2",
            ("p03", "문항04"): "answer=5",
            ("p03", "문항05"): "answer_text=오른쪽 모양",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-2_3단원_여러가지모양_1회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "geometry")
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_second_semester_shapes_round2_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=□ 모양 2개 색칠",
            ("p01", "문항04"): "answer_text=□ 2개, △ 3개, ○ 1개",
            ("p01", "문항07"): "answer=4",
            ("p02", "문항01"): "answer_text=동화책",
            ("p02", "문항06"): "answer_text=세 번째 물건",
            ("p02", "문항09"): "answer_text=△ 모양",
            ("p03", "문항01"): "answer=5",
            ("p03", "문항04"): "answer=6",
            ("p03", "문항05"): "answer_text=오른쪽 모양",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-2_3단원_여러가지모양_2회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "geometry")
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_second_semester_shapes_round3_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=동전",
            ("p01", "문항04"): "answer_text=□ 1개, △ 2개, ○ 3개",
            ("p01", "문항06"): "answer=2",
            ("p02", "문항01"): "answer_text=시계",
            ("p02", "문항06"): "answer_text=첫 번째 물건",
            ("p02", "문항08"): "answer_text=지훈",
            ("p03", "문항01"): "answer_text=□ 모양",
            ("p03", "문항03"): "answer=3",
            ("p03", "문항06"): "answer_text=오른쪽 모양",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-2_3단원_여러가지모양_3회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "geometry")
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_shapes_round1_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=다, 마",
            ("p01", "문항04"): "answer_text=삼각형이 2개 더 많습니다",
            ("p01", "문항08"): (
                "answer_text=사각형: 변 4, 꼭짓점 4 / 오각형: 변 5, 꼭짓점 5 / 육각형: 변 6, 꼭짓점 6"
            ),
            ("p02", "문항01"): "answer_text=사",
            ("p02", "문항03"): "answer=4",
            ("p02", "문항04"): "answer_text=삼각형 5개, 사각형 2개",
            ("p02", "문항05"): "answer_text=(1) 다, (2) 가, (3) 나",
            ("p03", "문항02"): "answer=6",
            ("p03", "문항03"): "answer_text=삼각형, 사각형",
            ("p03", "문항04"): "answer_text=3개",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-1_2단원_여러가지도형_1회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "geometry")
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_shapes_round2_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=마",
            ("p01", "문항02"): "answer_text=가, 라, 바",
            ("p01", "문항04"): "answer_text=삼각형 4개, 사각형 1개",
            ("p01", "문항07"): "answer_text=변 5개, 꼭짓점 5개",
            ("p02", "문항01"): "answer=10",
            ("p02", "문항02"): "answer_text=3개, 1개",
            ("p02", "문항04"): "answer_text=삼각형 4개, 사각형 2개",
            ("p02", "문항07"): "answer_text=오른쪽",
            ("p02", "문항08"): "answer_text=사각형, 삼각형, 평행사변형",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-1_2단원_여러가지도형_2회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "geometry")
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_shapes_round3_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=다, 라",
            ("p01", "문항02"): "answer_text=나, 라",
            ("p01", "문항04"): "answer=1",
            ("p01", "문항07"): "answer_text=다",
            ("p02", "문항01"): "answer=7",
            ("p02", "문항02"): "answer_text=2개, 2개",
            ("p02", "문항05"): "answer_text=삼각형 4개, 사각형 3개",
            ("p02", "문항07"): "answer_text=가운데",
            ("p03", "문항01"): "answer_text=삼각형, 사각형, 오각형",
            ("p03", "문항05"): "answer_text=오른쪽",
            ("p03", "문항06"): "answer_text=ㄴ",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-1_2단원_여러가지도형_3회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "geometry")
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_second_semester_clock_pattern_round1_templates(self) -> None:
        cases = {
            ("p01", "문항01"): ("measurement", "answer_text=5시"),
            ("p01", "문항02"): ("measurement", "answer_text=4시"),
            ("p01", "문항04"): ("measurement", "answer_text=1시 30분"),
            ("p01", "문항07"): ("measurement", "answer_text=오른쪽 시계"),
            ("p02", "문항01"): ("pattern", "answer_text=검은색"),
            ("p02", "문항05"): ("measurement", "answer=6"),
            ("p02", "문항09"): ("pattern", "answer_text=21, 31"),
            ("p03", "문항01"): ("pattern", "answer_text=13, 16, 19, 22, 25, 28"),
            ("p03", "문항02"): ("measurement", "answer_text=6시 30분"),
            ("p03", "문항03"): ("pattern", "answer=9"),
        }

        for (page, card_label), (topic, expression) in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-2_5단원_시계보기와규칙찾기_1회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_second_semester_clock_pattern_round2_templates(self) -> None:
        cases = {
            ("p01", "문항01"): ("measurement", "answer_text=2시"),
            ("p01", "문항02"): ("measurement", "answer_text=11시"),
            ("p01", "문항04"): ("measurement", "answer_text=10시 30분"),
            ("p01", "문항07"): ("measurement", "answer_text=오른쪽 시계"),
            ("p02", "문항01"): ("pattern", "answer_text=흰색"),
            ("p02", "문항05"): ("measurement", "answer=12"),
            ("p02", "문항08"): ("pattern", "answer_text=①"),
            ("p02", "문항09"): ("pattern", "answer_text=9, 6"),
        }

        for (page, card_label), (topic, expression) in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-2_5단원_시계보기와규칙찾기_2회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_second_semester_clock_pattern_round3_templates(self) -> None:
        cases = {
            ("p01", "문항01"): ("measurement", "answer_text=8시"),
            ("p01", "문항02"): ("measurement", "answer_text=7시"),
            ("p01", "문항04"): ("measurement", "answer_text=11시 30분"),
            ("p01", "문항07"): ("measurement", "answer_text=오른쪽 시계"),
            ("p01", "문항09"): ("pattern", "answer_text=흰색"),
            ("p02", "문항02"): ("measurement", "answer_text=11시 30분"),
            ("p02", "문항03"): ("measurement", "answer_text=시작: 5시 30분 / 끝: 7시"),
            ("p02", "문항05"): ("measurement", "answer=6"),
            ("p02", "문항08"): ("pattern", "answer_text=①"),
            ("p03", "문항04"): ("pattern", "answer=3"),
        }

        for (page, card_label), (topic, expression) in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-2_5단원_시계보기와규칙찾기_3회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_addition_subtraction_visual_templates(self) -> None:
        cases = {
            "문항01": "answer=5",
            "문항04": "answer=1",
            "문항05": "answer_text=2 + 3 = 5",
            "문항08": "answer_text=빈칸: 3, 7",
            "문항09": "answer_text=다",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-1_3단원_덧셈과뺄셈_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_addition_subtraction_page2_visual_templates(self) -> None:
        cases = {
            "문항02": "answer_text=3개",
            "문항04": "answer=2",
            "문항06": "answer_text=합: 6 / 차: 4",
            "문항09": "answer_text=8 - 2 = 6",
            "문항11": "answer_text=4 - 0 = 4",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-1_3단원_덧셈과뺄셈_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_addition_subtraction_round2_visual_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer=7",
            ("p01", "문항08"): "answer_text=빈칸: 3, 5",
            ("p02", "문항01"): "answer_text=3개",
            ("p02", "문항04"): "answer=0",
            ("p02", "문항06"): "answer_text=합: 9 / 차: 5",
            ("p02", "문항11"): "answer_text=6 - 0 = 6",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-1_3단원_덧셈과뺄셈_2회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_addition_subtraction_round3_visual_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer=6",
            ("p01", "문항08"): "answer_text=빈칸: 2, 3",
            ("p02", "문항01"): "answer_text=4자루",
            ("p02", "문항04"): "answer=3",
            ("p02", "문항06"): "answer_text=합: 5 / 차: 3",
            ("p02", "문항11"): "answer_text=8 - 8 = 0",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-1_3단원_덧셈과뺄셈_3회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_comparison_visual_templates(self) -> None:
        cases = {
            ("p01", "문항03"): ("measurement", "answer_text=위에서부터 2, 1, 3"),
            ("p01", "문항05"): ("measurement", "answer_text=많다, 적다"),
            ("p02", "문항01"): ("measurement", "answer_text=가운데 ○표, 오른쪽 △표"),
            ("p02", "문항02"): ("measurement", "answer_text=위치순: 2, 3, 1"),
            ("p02", "문항04"): ("measurement", "answer_text=민석"),
            ("p02", "문항06"): ("measurement", "answer_text=위치순: 2, 1, 3"),
            ("p03", "문항02"): ("measurement", "answer_text=동준"),
            ("p03", "문항03"): ("measurement", "answer_text=위치순: 2, 1, 3"),
            ("p03", "문항05"): ("measurement", "answer_text=담을 수 있는 양"),
        }

        for (page, card_label), (topic, expression) in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-1_4단원_비교하기_1회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_comparison_round2_visual_templates(self) -> None:
        cases = {
            ("p01", "문항03"): ("measurement", "answer_text=위에서부터 3, 1, 2"),
            ("p01", "문항05"): ("measurement", "answer_text=길다, 짧다"),
            ("p01", "문항07"): ("measurement", "answer_text=왼쪽 △표, 가운데 ○표"),
            ("p02", "문항01"): ("measurement", "answer_text=위치순: 1, 2, 3"),
            ("p02", "문항03"): ("measurement", "answer_text=야구공"),
            ("p02", "문항07"): ("measurement", "answer_text=공원"),
            ("p03", "문항02"): ("measurement", "answer_text=수지"),
            ("p03", "문항03"): ("measurement", "answer_text=위치순: 3, 1, 2"),
            ("p03", "문항05"): ("measurement", "answer_text=넓이"),
        }

        for (page, card_label), (topic, expression) in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-1_4단원_비교하기_2회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_comparison_round3_visual_templates(self) -> None:
        cases = {
            ("p01", "문항03"): ("measurement", "answer_text=위에서부터 3, 2, 1"),
            ("p01", "문항04"): ("measurement", "answer_text=가"),
            ("p01", "문항05"): ("measurement", "answer_text=무겁다, 가볍다"),
            ("p02", "문항01"): ("measurement", "answer_text=셋째 △표, 넷째 ○표"),
            ("p02", "문항02"): ("measurement", "answer_text=위치순: 1, 3, 2"),
            ("p02", "문항04"): ("measurement", "answer_text=귤"),
            ("p02", "문항08"): ("measurement", "answer_text=방"),
            ("p03", "문항02"): ("measurement", "answer_text=하은"),
            ("p03", "문항04"): ("measurement", "answer_text=위치순: 3, 1, 2"),
            ("p03", "문항05"): ("measurement", "answer_text=무게"),
        }

        for (page, card_label), (topic, expression) in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-1_4단원_비교하기_3회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_numbers_to_50_round1_visual_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=쓰기: 12 / 읽기: 십이, 열둘",
            ("p01", "문항02"): "answer_text=빈칸: 15, 6",
            ("p01", "문항04"): "answer_text=민희",
            ("p01", "문항05"): "answer_text=빈칸: 16, 18, 10, 12",
            ("p02", "문항01"): "answer_text=가운데 ○표",
            ("p02", "문항03"): "answer_text=빈칸: 5, 50, 5, 50",
            ("p02", "문항05"): "answer_text=빈칸: 36, 45",
            ("p02", "문항09"): "answer_text=13, 25, 35, 38, 47",
            ("p03", "문항01"): "answer=47",
            ("p03", "문항03"): "answer_text=3개",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-1_5단원_50까지의수_1회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_numbers_to_50_round2_visual_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=쓰기: 11 / 읽기: 십일, 열하나",
            ("p01", "문항02"): "answer_text=빈칸: 11, 9",
            ("p01", "문항04"): "answer_text=연희",
            ("p01", "문항05"): "answer_text=빈칸: 12, 14, 15, 17",
            ("p02", "문항01"): "answer_text=왼쪽 ○표",
            ("p02", "문항03"): "answer_text=빈칸: 3, 40",
            ("p02", "문항09"): "answer_text=12, 29, 32, 39, 43",
            ("p02", "문항12"): "answer_text=4개",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-1_5단원_50까지의수_2회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_numbers_to_50_round3_visual_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=쓰기: 10 / 읽기: 십, 열",
            ("p01", "문항02"): "answer_text=빈칸: 16, 9",
            ("p01", "문항04"): "answer_text=서준",
            ("p01", "문항05"): "answer_text=빈칸: 14, 16, 17, 19",
            ("p02", "문항01"): "answer_text=오른쪽 ○표",
            ("p02", "문항03"): "answer_text=빈칸: 5, 20",
            ("p02", "문항09"): "answer_text=19, 21, 28, 33, 42",
            ("p03", "문항03"): "answer_text=5개",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-1_5단원_50까지의수_3회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_numbers_to_100_page1_visual_templates(self) -> None:
        cases = {
            "1회": {
                "문항01": "answer_text=10개씩 묶음: 6, 낱개: 2 / 62",
                "문항02": "answer_text=6상자",
                "문항03": "answer_text=6묶음-60-육십/예순, 7묶음-70-칠십/일흔, 8묶음-80-팔십/여든, 9묶음-90-구십/아흔",
                "문항04": "answer_text=80 / 팔십, 여든",
                "문항05": "answer_text=53: 5묶음 3낱개 / 78: 7묶음 8낱개 / 84",
                "문항06": "answer_text=95개",
                "문항07": "answer_text=⑤",
                "문항08": "answer_text=예순",
                "문항09": "answer_text=54 / 오십사, 쉰넷",
            },
            "2회": {
                "문항01": "answer_text=10개씩 묶음: 8, 낱개: 4 / 84",
                "문항02": "answer_text=7상자",
                "문항03": "answer_text=칠십-70",
                "문항04": "answer_text=60 / 육십, 예순",
                "문항05": "answer_text=64: 6묶음 4낱개 / 59: 5묶음 9낱개 / 97",
                "문항06": "answer_text=78개",
                "문항07": "answer_text=①, ③, ④, ⑤",
                "문항08": "answer_text=여든",
                "문항09": "answer_text=87 / 팔십칠, 여든일곱",
            },
            "3회": {
                "문항01": "answer_text=10개씩 묶음: 7, 낱개: 5 / 75",
                "문항02": "answer_text=9상자",
                "문항03": "answer_text=팔십-80",
                "문항04": "answer_text=90 / 구십, 아흔",
                "문항05": "answer_text=87: 8묶음 7낱개 / 67: 6묶음 7낱개 / 77",
                "문항06": "answer_text=79장",
                "문항07": "answer_text=①",
                "문항08": "answer_text=아흔",
                "문항09": "answer_text=71 / 칠십일, 일흔하나",
                "문항10": "answer_text=94",
            },
        }

        for round_label, round_cases in cases.items():
            for card_label, expression in round_cases.items():
                with self.subTest(round_label=round_label, card_label=card_label):
                    template = infer_elementary_visual_template(
                        f"/tmp/초1-2_1단원_100가지의수_{round_label}_p01_{card_label}.png",
                    )

                    self.assertIsNotNone(template)
                    assert template is not None
                    self.assertEqual(template.expression, expression)

    def test_infers_grade1_numbers_to_100_round1_page2_visual_templates(self) -> None:
        cases = {
            "문항02": "answer_text=빈칸: 61, 60",
            "문항03": "answer_text=<",
            "문항04": "answer_text=95에 ○표, 79에 △표",
            "문항05": "answer=100",
            "문항07": "answer_text=55, 56, 57",
            "문항08": "answer_text=0, 1",
            "문항09": "answer=74",
            "문항10": "answer_text=홀수: 2개 / 짝수: 4개",
            "문항11": "answer_text=63, 71",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-2_1단원_100가지의수_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_numbers_to_100_round2_page2_visual_templates(self) -> None:
        cases = {
            "문항02": "answer_text=빈칸: 77, 75",
            "문항03": "answer_text=<",
            "문항04": "answer_text=98에 ○표, 78에 △표",
            "문항05": "answer=80",
            "문항07": "answer_text=70, 71",
            "문항08": "answer_text=0, 1, 2, 3",
            "문항09": "answer=96",
            "문항10": "answer_text=홀수: 4개 / 짝수: 2개",
            "문항11": "answer_text=27, 57",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-2_1단원_100가지의수_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_numbers_to_100_round3_page2_visual_templates(self) -> None:
        cases = {
            "문항01": "answer_text=빈칸: 87, 86",
            "문항02": "answer_text=>",
            "문항03": "answer_text=95에 ○표, 59에 △표",
            "문항04": "answer=90",
            "문항06": "answer_text=89, 90, 91, 92",
            "문항07": "answer_text=0, 1, 2",
            "문항08": "answer=28",
            "문항09": "answer_text=홀수: 3개 / 짝수: 3개",
            "문항10": "answer_text=68, 86",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-2_1단원_100가지의수_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_add_sub_100_round1_visual_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=빈칸: 10, 40",
            ("p01", "문항04"): "answer_text=22 + 32에 ○표",
            ("p01", "문항05"): "answer=25",
            ("p02", "문항03"): "answer_text=빈칸: 20, 27, 27, 3, 24",
            ("p02", "문항05"): "answer_text=>",
            ("p02", "문항07"): "answer_text=합: 67 / 차: 45",
            ("p03", "문항01"): "answer_text=38명",
            ("p03", "문항02"): "answer_text=11개",
            ("p03", "문항03"): "answer_text=26권",
            ("p03", "문항04"): "answer_text=축구공, 35개",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-2_2단원_덧셈과뺄셈_1__1회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_add_sub_100_round2_visual_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=빈칸: 7, 37",
            ("p01", "문항04"): "answer_text=20 + 56에 ○표",
            ("p01", "문항05"): "answer=39",
            ("p02", "문항02"): "answer_text=빈칸: 10, 44, 44, 3, 41",
            ("p02", "문항06"): "answer_text=합: 97 / 차: 53",
            ("p02", "문항09"): "answer_text=58명",
            ("p03", "문항01"): "answer_text=36자루",
            ("p03", "문항03"): "answer_text=닭장 안, 11마리",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-2_2단원_덧셈과뺄셈_1__2회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_add_sub_100_round3_visual_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=빈칸: 6, 46",
            ("p01", "문항04"): "answer_text=32 + 44에 ○표",
            ("p01", "문항05"): "answer=42",
            ("p02", "문항03"): "answer_text=빈칸: 20, 60, 6, 2, 60, 62",
            ("p02", "문항05"): "answer_text=<",
            ("p02", "문항07"): "answer_text=합: 86 / 차: 44",
            ("p03", "문항01"): "answer_text=89송이",
            ("p03", "문항04"): "answer_text=영희, 16개",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-2_2단원_덧셈과뺄셈_1__3회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_add_sub_10_three_terms_round1_visual_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=빈칸: 3, 3, 2, 8",
            ("p01", "문항04"): "answer_text=빈칸: 8, 7",
            ("p01", "문항06"): "answer_text=9 + 1에 ○표",
            ("p02", "문항01"): "answer_text=1 + 4 + 9에 ○표",
            ("p02", "문항05"): "answer=6",
            ("p02", "문항08"): "answer=9",
            ("p03", "문항01"): "answer_text=4자루",
            ("p03", "문항04"): "answer_text=2명",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-2_4단원_덧셈과뺄셈_2__1회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_add_sub_10_three_terms_round2_visual_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=빈칸: 2, 2, 3, 7",
            ("p01", "문항04"): "answer_text=빈칸: 9, 8",
            ("p01", "문항06"): "answer_text=8 + 2에 ○표",
            ("p02", "문항01"): "answer_text=3 + 1 + 7에 ○표",
            ("p02", "문항05"): "answer=8",
            ("p02", "문항08"): "answer=9",
            ("p02", "문항09"): "answer_text=2살",
            ("p03", "문항01"): "answer_text=12장",
            ("p03", "문항03"): "answer_text=3명",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-2_4단원_덧셈과뺄셈_2__2회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_add_sub_10_three_terms_round3_visual_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=빈칸: 4, 3, 2, 9",
            ("p01", "문항04"): "answer_text=빈칸: 6, 7",
            ("p01", "문항06"): "answer_text=6 + 4에 ○표",
            ("p02", "문항01"): "answer_text=5 + 4 + 5에 ○표",
            ("p02", "문항05"): "answer=7",
            ("p02", "문항09"): "answer_text=3개",
            ("p03", "문항01"): "answer_text=12자루",
            ("p03", "문항03"): "answer_text=2개",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-2_4단원_덧셈과뺄셈_2__3회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_clock_pattern_visual_templates(self) -> None:
        cases = {
            "/tmp/초1-2_5단원_시계보기와규칙찾기_1회_p01_문항01.png": "answer_text=5시",
            "/tmp/초1-2_5단원_시계보기와규칙찾기_2회_p01_문항01.png": "answer_text=2시",
            "/tmp/초1-2_5단원_시계보기와규칙찾기_2회_p03_문항03.png": "answer=4",
            "/tmp/초1-2_5단원_시계보기와규칙찾기_3회_p01_문항01.png": "answer_text=8시",
            "/tmp/초1-2_5단원_시계보기와규칙찾기_3회_p03_문항01.png": "answer_text=51, 56, 61, 66, 71",
        }

        for image_path, expression in cases.items():
            with self.subTest(image_path=image_path):
                template = infer_elementary_visual_template(image_path)

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_add_sub_20_round1_visual_templates(self) -> None:
        cases = {
            "문항01": "answer_text=빈칸: 12, 12, 2",
            "문항04": "answer_text=8 + 3, 3 + 8",
            "문항05": "answer=9",
            "문항10": "answer_text=<",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-2_6단원_덧셈과뺄셈_3__1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_add_sub_20_round1_page2_templates(self) -> None:
        cases = {
            "문항02": "answer_text=9, 8, 7, 6 / 작아집니다에 ○표",
            "문항03": "answer_text=6, 7, 8, 9",
            "문항08": "answer_text=수호",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-2_6단원_덧셈과뺄셈_3__1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_add_sub_20_round2_visual_templates(self) -> None:
        cases = {
            "문항01": "answer_text=빈칸: 16, 16, 6",
            "문항04": "answer_text=6 + 6, 7 + 5",
            "문항05": "answer=9",
            "문항08": "answer=12",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-2_6단원_덧셈과뺄셈_3__2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_add_sub_20_round2_page2_templates(self) -> None:
        cases = {
            "문항02": "answer_text=6, 6, 6, 6",
            "문항05": "answer_text=12 - 3에 ○표",
            "문항08": "answer_text=서준",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-2_6단원_덧셈과뺄셈_3__2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_add_sub_20_round3_visual_templates(self) -> None:
        cases = {
            "문항01": "answer_text=빈칸: 15, 15, 5",
            "문항04": "answer_text=7 + 7, 6 + 8",
            "문항05": "answer=8",
            "문항09": "answer_text=빈칸: 11, 7",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-2_6단원_덧셈과뺄셈_3__3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade1_add_sub_20_round3_page2_templates(self) -> None:
        cases = {
            "문항02": "answer_text=9, 8, 7, 6 / 작아집니다에 ○표",
            "문항05": "answer_text=13 - 4에 ○표",
            "문항08": "answer_text=준서",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초1-2_6단원_덧셈과뺄셈_3__3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_generic_make_ten_compose_decompose_from_ocr_text(self) -> None:
        template = infer_elementary_visual_template(
            "/tmp/capture.png",
            raw_text=(
                "1. 10을 이용하여 모으기와 가르기를 한 것입니\n"
                "다. 빈칸에 알맞은 수를 넣어 보세요.\n"
                "9 6\n10\n91 618"
            ),
        )

        self.assertIsNotNone(template)
        assert template is not None
        self.assertEqual(template.rule_id, "generic_make_ten_compose_decompose")
        self.assertEqual(template.expression, "answer_text=빈칸: 15, 5")

    def test_infers_generic_make_ten_subtraction_from_ocr_text(self) -> None:
        template = infer_elementary_visual_template(
            "/tmp/capture.png",
            raw_text="2. □ 안에 알맞은 수를 써넣으시오.\n14-6ㅋ |\n2",
        )

        self.assertIsNotNone(template)
        assert template is not None
        self.assertEqual(template.rule_id, "generic_make_ten_subtraction_decomposition")
        self.assertEqual(template.expression, "answer_text=빈칸: 8, 4")

    def test_infers_grade2_three_digits_round1_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=(1) 287 / (2) 507 / (3) 920 / (4) 411",
            "문항02": "answer_text=빈칸: 529, 559",
            "문항03": "answer=400",
            "문항04": "answer_text=③",
            "문항05": "answer_text=468, 사백육십팔",
            "문항06": "answer=90",
            "문항07": "answer_text=(1) 973 / (2) 203",
            "문항08": "answer_text=837, 팔백삼십칠",
            "문항09": "answer_text=285, 2, 8, 5",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-1_1단원_세자리수_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_three_digits_round1_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=빈칸: 498, 508",
            "문항02": "answer=383",
            "문항03": "answer_text=(1) 307 < 370 / (2) 578 > 378",
            "문항04": "answer_text=(1) 0, 1, 2 / (2) 8, 9",
            "문항05": "answer_text=(1) 731 / (2) 137",
            "문항06": "answer_text=798, 799, 800, 801, 802",
            "문항07": "answer=398",
            "문항08": "answer=199",
            "문항09": "answer_text=7개",
            "문항10": "answer_text=300송이",
            "문항11": "answer_text=성희",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-1_1단원_세자리수_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_three_digits_round2_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=사백육십",
            "문항02": "answer_text=938, 948, 958, 968",
            "문항03": "answer=60",
            "문항04": "answer_text=450, 750에 ○표",
            "문항05": "answer=346",
            "문항06": "answer=80",
            "문항07": "answer=652",
            "문항08": "answer=40",
            "문항09": "answer_text=일의 자리 5",
            "문항10": "answer_text=680, 730, 780, 830",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-1_1단원_세자리수_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_three_digits_round2_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=660, 650, 640",
            "문항02": "answer=490",
            "문항03": "answer_text=오백이십",
            "문항04": "answer_text=759, 595, 559",
            "문항05": "answer_text=5명",
            "문항06": "answer=928",
            "문항07": "answer=568",
            "문항08": "answer_text=3자루",
            "문항09": "answer_text=565장",
            "문항10": "answer_text=690원",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-1_1단원_세자리수_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_three_digits_round3_page1_templates(self) -> None:
        cases = {
            "문항01": "answer=508",
            "문항02": "answer_text=726, 756, 766",
            "문항03": "answer=8",
            "문항04": "answer=765",
            "문항05": "answer=100",
            "문항06": "answer=99",
            "문항07": "answer=157",
            "문항08": "answer=30",
            "문항09": "answer_text=십의 자리 2",
            "문항10": "answer_text=410, 440, 470, 500",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-1_1단원_세자리수_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_three_digits_round3_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=499, 498, 497",
            "문항02": "answer=710",
            "문항03": "answer_text=>",
            "문항04": "answer_text=821, 128",
            "문항05": "answer_text=6명",
            "문항06": "answer=601",
            "문항07": "answer=578",
            "문항08": "answer_text=7개",
            "문항09": "answer_text=807개",
            "문항10": "answer_text=희선",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-1_1단원_세자리수_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_shapes_round2_page3_templates(self) -> None:
        cases = {
            "문항01": "answer_text=4개",
            "문항02": "answer_text=원",
            "문항03": "answer_text=8개",
            "문항04": "answer_text=①",
            "문항05": "answer_text=㉡",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-1_2단원_여러가지도형_2회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "geometry")
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_shapes_page1_review_templates(self) -> None:
        cases = {
            ("초2-1_2단원_여러가지도형_1회_p01", "문항03"): "answer_text=㉠ 꼭짓점, ㉡ 변",
            ("초2-1_2단원_여러가지도형_2회_p01", "문항03"): "answer_text=변 3개, 꼭짓점 3개",
            ("초2-1_2단원_여러가지도형_3회_p01", "문항05"): "answer_text=삼각형의 곧은 선 3개, 사각형의 굽은 선 0개",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(f"/tmp/{page}_{card_label}.png")

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "geometry")
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_add_sub_round1_page1_templates(self) -> None:
        cases = {
            "문항01": "answer=53",
            "문항02": "answer_text=㉠ 119, ㉡ 34, ㉢ 80, ㉣ 73",
            "문항03": "answer_text=㉠ 6, ㉡ 8",
            "문항04": "answer_text=<",
            "문항05": "answer=43",
            "문항06": "answer_text=합: 48 / 차: 36",
            "문항07": "answer_text=35, 83, 60",
            "문항08": "answer_text=<",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-1_3단원_덧셈과뺄셈_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_add_sub_round1_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=1, 2, 3",
            "문항02": "answer_text=㉠ 6, ㉡ 4",
            "문항03": "answer_text=37, 18, 49",
            "문항04": "answer_text=㉠ 6, ㉡ 5, ㉢ 18, ㉣ 17",
            "문항05": "answer_text=㉠ 47, ㉡ 5, ㉢ 52, ㉣ 47",
            "문항06": "answer=57",
            "문항07": "answer_text=22명",
            "문항08": "answer_text=47번",
            "문항09": "answer_text=24명",
            "문항10": "answer=81",
            "문항11": "answer=51",
            "문항12": "answer_text=4권",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-1_3단원_덧셈과뺄셈_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_add_sub_round2_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=77, 58",
            "문항02": "answer=121",
            "문항03": "answer_text=7, 11, 91",
            "문항04": "answer=19",
            "문항05": "answer_text=85, 58, 27 / 85, 27, 58",
            "문항06": "answer_text=합: 56 / 차: 38",
            "문항07": "answer_text=48, 28",
            "문항08": "answer=9",
            "문항09": "answer_text=26, 27에 ○표",
            "문항10": "answer_text==",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-1_3단원_덧셈과뺄셈_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_add_sub_round2_page2_templates(self) -> None:
        cases = {
            "문항01": "answer=130",
            "문항02": "answer=8",
            "문항03": "answer_text=<",
            "문항04": "answer=81",
            "문항05": "answer=27",
            "문항06": "answer=153",
            "문항07": "answer=35",
            "문항08": "answer_text=145번",
            "문항09": "answer_text=37쪽",
            "문항10": "answer_text=21자루",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-1_3단원_덧셈과뺄셈_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_add_sub_round3_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=66, 43",
            "문항02": "answer=117",
            "문항03": "answer_text=7, 15, 95",
            "문항04": "answer=18",
            "문항05": "answer_text=92, 43, 49 / 92, 49, 43",
            "문항06": "answer_text=합: 33 / 차: 17",
            "문항07": "answer_text=56, 18",
            "문항08": "answer=5",
            "문항09": "answer_text=17, 18에 ○표",
            "문항10": "answer_text=<",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-1_3단원_덧셈과뺄셈_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_add_sub_round3_page2_templates(self) -> None:
        cases = {
            "문항01": "answer=130",
            "문항02": "answer=6",
            "문항03": "answer_text=>",
            "문항04": "answer=46",
            "문항05": "answer=37",
            "문항06": "answer=141",
            "문항07": "answer=65",
            "문항08": "answer_text=134권",
            "문항09": "answer_text=윤철, 15개",
            "문항10": "answer_text=57명",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-1_3단원_덧셈과뺄셈_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_length_round1_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=5번",
            ("p01", "문항02"): "answer_text=6 cm",
            ("p01", "문항04"): "answer_text=1 센티미터, 1 cm",
            ("p01", "문항05"): "answer_text=나",
            ("p01", "문항06"): "answer_text=어림한 길이: (예) 7 cm / 자로 잰 길이: 6 cm",
            ("p01", "문항08"): "answer_text=32 cm",
            ("p02", "문항01"): "answer_text=(1) 다, (2) 가",
            ("p02", "문항02"): "answer_text=나",
            ("p02", "문항07"): "answer_text=7 cm",
            ("p02", "문항08"): "answer_text=냉장고",
            ("p03", "문항01"): "answer_text=유진",
            ("p03", "문항02"): "answer_text=8 cm",
            ("p03", "문항04"): "answer_text=은희",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-1_4단원_길이재기_1회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "measurement")
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_length_round2_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=6번",
            ("p01", "문항02"): "answer_text=7번",
            ("p01", "문항03"): "answer_text=3뼘",
            ("p01", "문항04"): "answer_text=세 번째에 ○표",
            ("p01", "문항06"): "answer_text=약 5 cm / 5 cm",
            ("p01", "문항08"): "answer_text=재희",
            ("p02", "문항01"): "answer_text=지수",
            ("p02", "문항02"): "answer_text=3 cm",
            ("p02", "문항05"): "answer_text=4칸 색칠",
            ("p02", "문항08"): "answer_text=약 7 cm",
            ("p03", "문항01"): "answer_text=서윤",
            ("p03", "문항02"): "answer_text=3 cm에 ○표",
            ("p03", "문항04"): "answer_text=젓가락, 연필, 풀",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-1_4단원_길이재기_2회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "measurement")
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_length_round3_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=5번",
            ("p01", "문항02"): "answer_text=8번",
            ("p01", "문항03"): "answer_text=4뼘",
            ("p01", "문항04"): "answer_text=파란색에 ○표",
            ("p01", "문항07"): "answer_text=초록색",
            ("p02", "문항01"): "answer_text=민호",
            ("p02", "문항02"): "answer_text=지은",
            ("p02", "문항04"): "answer_text=5번",
            ("p02", "문항08"): "answer_text=첫 번째에 ○표",
            ("p03", "문항01"): "answer_text=약 6 cm",
            ("p03", "문항02"): "answer_text=희철",
            ("p03", "문항05"): "answer_text=9, 1, 7",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-1_4단원_길이재기_3회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "measurement")
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_multiplication_round1_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=6, 3",
            ("p01", "문항02"): "answer=21",
            ("p01", "문항03"): "answer_text=56, 8, 7, 56",
            ("p01", "문항05"): "answer_text=6, 4, 24",
            ("p01", "문항08"): "answer=20",
            ("p01", "문항09"): "answer_text=<",
            ("p02", "문항02"): "answer_text=②, ⑤",
            ("p02", "문항03"): "answer_text=(1) 6, (2) 3, (3) 2",
            ("p02", "문항04"): "answer_text=2 × 7 = 14",
            ("p02", "문항07"): "answer_text=25개",
            ("p02", "문항11"): "answer_text=27개",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-1_6단원_곱셈_1회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_multiplication_round2_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=12개",
            ("p01", "문항02"): "answer_text=4, 8",
            ("p01", "문항03"): "answer_text=28, 4, 7, 28",
            ("p01", "문항04"): "answer_text=9 × 4 = 36",
            ("p01", "문항05"): "answer_text=2, 7, 14 / 7, 2, 14",
            ("p01", "문항06"): "answer_text=㉢",
            ("p01", "문항10"): "answer=10",
            ("p02", "문항01"): "answer_text=<",
            ("p02", "문항02"): "answer_text=두 번째에 ○표",
            ("p02", "문항03"): "answer_text=㉡, ㉢, ㉠",
            ("p02", "문항04"): "answer_text=36개",
            ("p02", "문항05"): "answer_text=32개",
            ("p02", "문항08"): "answer_text=7봉지",
            ("p02", "문항10"): "answer_text=8개",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-1_6단원_곱셈_2회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_multiplication_round3_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=10개",
            ("p01", "문항02"): "answer_text=4, 12",
            ("p01", "문항03"): "answer_text=48, 6, 8, 48",
            ("p01", "문항04"): "answer_text=7 + 7 + 7 + 7 = 28",
            ("p01", "문항05"): "answer_text=8 / 2, 4, 8",
            ("p01", "문항06"): "answer_text=3, 7, 7, 7, 21",
            ("p01", "문항09"): "answer_text=5, 25",
            ("p02", "문항01"): "answer=1",
            ("p02", "문항02"): "answer_text=>",
            ("p02", "문항03"): "answer_text=세 번째에 ○표",
            ("p02", "문항04"): "answer_text=㉠, ㉢, ㉡",
            ("p02", "문항05"): "answer_text=9개",
            ("p02", "문항06"): "answer_text=56개",
            ("p02", "문항08"): "answer_text=25개",
            ("p02", "문항11"): "answer_text=18개",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-1_6단원_곱셈_3회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_four_digits_round1_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer=1000",
            ("p01", "문항02"): "answer=2125",
            ("p01", "문항03"): "answer_text=3, 8, 2, 5",
            ("p01", "문항04"): "answer_text=2, 9, 4, 7",
            ("p01", "문항05"): "answer_text=2550, 2650, 2850",
            ("p01", "문항06"): "answer_text=>",
            ("p01", "문항08"): "answer_text=7432, 6501, 7432",
            ("p02", "문항01"): "answer=90",
            ("p02", "문항02"): "answer_text=두 번째에 ○표",
            ("p02", "문항03"): "answer_text=<",
            ("p02", "문항04"): "answer_text=2개",
            ("p02", "문항05"): "answer_text=8531, 1358",
            ("p02", "문항08"): "answer_text=3개",
            ("p02", "문항12"): "answer_text=5000개",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-2_1단원_네자리수_1회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_four_digits_round2_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer=4357",
            ("p01", "문항02"): "answer=4000",
            ("p01", "문항03"): "answer=8406",
            ("p01", "문항04"): "answer_text=팔천십이",
            ("p01", "문항05"): "answer=100",
            ("p01", "문항06"): "answer_text=6247에 ○표, 2916에 △표",
            ("p01", "문항08"): "answer=6758",
            ("p01", "문항10"): "answer=500",
            ("p02", "문항01"): "answer_text=>",
            ("p02", "문항02"): "answer_text=2개",
            ("p02", "문항03"): "answer_text=9432, 2349",
            ("p02", "문항05"): "answer_text=5047, 5067",
            ("p02", "문항08"): "answer_text=4000원",
            ("p02", "문항10"): "answer_text=3100원",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-2_1단원_네자리수_2회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_four_digits_round3_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer=5000",
            ("p01", "문항02"): "answer=1000",
            ("p01", "문항03"): "answer=5183",
            ("p01", "문항04"): "answer=9704",
            ("p01", "문항05"): "answer_text=6056, 7056, 9056",
            ("p01", "문항06"): "answer_text=첫 번째에 ○표",
            ("p01", "문항08"): "answer=3846",
            ("p01", "문항09"): "answer_text=7000, 5, 500, 7500",
            ("p02", "문항01"): "answer_text=첫 번째에 ○표",
            ("p02", "문항02"): "answer_text=>",
            ("p02", "문항03"): "answer_text=2개",
            ("p02", "문항04"): "answer_text=8754, 4578",
            ("p02", "문항06"): "answer_text=8428, 8430",
            ("p02", "문항08"): "answer=6290",
            ("p02", "문항11"): "answer_text=4개",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-2_1단원_네자리수_3회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_times_table_round1_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=6, 12",
            ("p01", "문항02"): "answer_text=6, 3",
            ("p01", "문항03"): "answer_text==",
            ("p01", "문항04"): "answer_text=28, 49",
            ("p01", "문항05"): "answer_text=16개",
            ("p01", "문항06"): "answer_text=45명",
            ("p01", "문항08"): "answer=6",
            ("p01", "문항11"): "answer=1",
            ("p02", "문항01"): "answer_text=9, 63",
            ("p02", "문항02"): "answer_text=0, 1, 2, 3, 4",
            ("p02", "문항03"): "answer_text=⑤",
            ("p02", "문항04"): "answer=6",
            ("p02", "문항05"): "answer_text=0, 0, 0 / 6, 15, 21 / 12, 30, 42",
            ("p02", "문항07"): "answer_text=41세",
            ("p02", "문항09"): "answer_text=39개",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-2_2단원_곱셈구구_1회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_times_table_round2_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=3, 15",
            ("p01", "문항02"): "answer_text=9, 6",
            ("p01", "문항03"): "answer_text=<",
            ("p01", "문항04"): "answer_text=16, 64",
            ("p01", "문항05"): "answer_text=14짝",
            ("p01", "문항06"): "answer_text=40명",
            ("p01", "문항08"): "answer=8",
            ("p01", "문항10"): "answer_text=64개",
            ("p02", "문항01"): "answer=0",
            ("p02", "문항02"): "answer_text=9, 54",
            ("p02", "문항03"): "answer_text=0, 1, 2, 3, 4, 5",
            ("p02", "문항04"): "answer=4",
            ("p02", "문항05"): "answer=6",
            ("p02", "문항06"): "answer_text=0, 3, 5 / 0, 6, 10 / 0, 21, 35",
            ("p02", "문항10"): "answer_text=62개",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-2_2단원_곱셈구구_2회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_times_table_round3_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=27개",
            ("p01", "문항02"): "answer_text=4, 24",
            ("p01", "문항03"): "answer_text=㉠, ㉢, ㉣, ㉡",
            ("p01", "문항04"): "answer_text=42, 54",
            ("p01", "문항05"): "answer_text=18명",
            ("p01", "문항06"): "answer_text=30병",
            ("p01", "문항08"): "answer=2",
            ("p01", "문항11"): "answer=0",
            ("p02", "문항01"): "answer_text=6, 48",
            ("p02", "문항02"): "answer_text=0, 1, 2, 3",
            ("p02", "문항03"): "answer=6",
            ("p02", "문항04"): "answer=3",
            ("p02", "문항05"): "answer_text=1, 6, 8 / 5, 30, 40 / 9, 54, 72",
            ("p02", "문항07"): "answer_text=35세",
            ("p02", "문항09"): "answer_text=39개",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-2_2단원_곱셈구구_3회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_second_semester_length_round1_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer=400",
            ("p01", "문항02"): "answer_text=1 m 45 cm",
            ("p01", "문항03"): "answer_text=500, 7",
            ("p01", "문항04"): "answer=10",
            ("p01", "문항05"): "answer_text=첫 번째에 ○표",
            ("p01", "문항06"): "answer_text=160, 1, 60",
            ("p01", "문항08"): "answer_text=<",
            ("p02", "문항01"): "answer_text=4 m 75 cm",
            ("p02", "문항02"): "answer_text=3 m 15 cm",
            ("p02", "문항03"): "answer_text=2 m 33 cm",
            ("p02", "문항05"): "answer_text=5 m 16 cm",
            ("p02", "문항07"): "answer_text=정류장, 15 m 50 cm",
            ("p03", "문항01"): "answer_text=②",
            ("p03", "문항02"): "answer_text=52 cm",
            ("p03", "문항03"): "answer_text=72 cm",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-2_3단원_길이재기_1회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "measurement")
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_second_semester_length_round2_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer=900",
            ("p01", "문항02"): "answer_text=5 미터 29 센티미터",
            ("p01", "문항03"): "answer_text=300, 4",
            ("p01", "문항07"): "answer_text=④",
            ("p01", "문항08"): "answer_text=>",
            ("p01", "문항09"): "answer_text=10 m 91 cm",
            ("p02", "문항01"): "answer_text=2 m 70 cm",
            ("p02", "문항02"): "answer_text=1 m 25 cm",
            ("p02", "문항03"): "answer_text=5 m 6 cm",
            ("p02", "문항04"): "answer_text=7 m 65 cm",
            ("p02", "문항05"): "answer_text=2 m 87 cm",
            ("p02", "문항07"): "answer_text=집, 5 m 88 cm",
            ("p03", "문항01"): "answer_text=약 2 m",
            ("p03", "문항02"): "answer_text=①",
            ("p03", "문항03"): "answer_text=40 cm",
            ("p03", "문항04"): "answer_text=5 m",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-2_3단원_길이재기_2회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "measurement")
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_second_semester_length_round3_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer=8",
            ("p01", "문항02"): "answer_text=3 m 20 cm",
            ("p01", "문항03"): "answer_text=900, 3",
            ("p01", "문항04"): "answer_text=1 m",
            ("p01", "문항05"): "answer_text=숟가락의 길이에 ○표",
            ("p01", "문항06"): "answer_text=130, 1, 30",
            ("p01", "문항07"): "answer_text=5 cm",
            ("p01", "문항08"): "answer_text==",
            ("p01", "문항09"): "answer_text=8 m 72 cm",
            ("p02", "문항01"): "answer_text=678 cm",
            ("p02", "문항02"): "answer_text=2 m 54 cm",
            ("p02", "문항03"): "answer_text=4 m 18 cm",
            ("p02", "문항04"): "answer_text=2 m 40 cm",
            ("p02", "문항05"): "answer_text=2 m 63 cm",
            ("p02", "문항06"): "answer_text=870 cm",
            ("p02", "문항07"): "answer_text=도서관, 8 m 75 cm",
            ("p03", "문항01"): "answer_text=약 30 m",
            ("p03", "문항02"): "answer_text=④",
            ("p03", "문항03"): "answer_text=19 cm",
            ("p03", "문항04"): "answer_text=30 cm",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-2_3단원_길이재기_3회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "measurement")
                self.assertEqual(template.expression, expression)

    def test_infers_generic_centimeter_to_meter_centimeter_list(self) -> None:
        template = infer_elementary_visual_template(
            "/tmp/toctoc_g2_s2_똑똑수학탐험대_2학년_2학기_함께학습지_p44.png",
            raw_text=(
                "2cm보다 더 큰 단위를 알아볼까요\n"
                "1. 보기처럼 m로 나타내 보세요.\n"
                "1 300cm m 2 500cm m 3 900cm m "
                "4 150cm m 50cm 5 345cm m 45cm 6 777cm m 77cm"
            ),
        )

        self.assertIsNotNone(template)
        assert template is not None
        self.assertEqual(template.topic, "measurement")
        self.assertEqual(
            template.expression,
            "answer_text=3 m, 5 m, 9 m, 1 m 50 cm, 3 m 45 cm, 7 m 77 cm",
        )

    def test_infers_generic_meter_centimeter_context_operations(self) -> None:
        sum_template = infer_elementary_visual_template(
            "/tmp/toctoc_g2_s2_똑똑수학탐험대_2학년_2학기_함께학습지_p49.png",
            raw_text="3. 굴렁쇠가 굴러간 거리는 얼마일까요? 10m 45cm 6m 10cm",
        )
        diff_template = infer_elementary_visual_template(
            "/tmp/toctoc_g2_s2_똑똑수학탐험대_2학년_2학기_함께학습지_p51.png",
            raw_text="3. 사용한 색 테이프의 길이를 구해 보세요. 처음 길이 3m 75cm 남은 길이 1m",
        )

        self.assertIsNotNone(sum_template)
        self.assertIsNotNone(diff_template)
        assert sum_template is not None
        assert diff_template is not None
        self.assertEqual(sum_template.expression, "answer_text=16 m 55 cm")
        self.assertEqual(diff_template.expression, "answer_text=2 m 75 cm")

    def test_infers_generic_length_estimate_choice(self) -> None:
        template = infer_elementary_visual_template(
            "/tmp/toctoc_g2_s2_똑똑수학탐험대_2학년_2학기_함께학습지_p55.png",
            raw_text="필통의 길이는 약 □입니다. 집에서 볼 수 있는 여러 물건들의 길이를 어림해 보세요.",
        )

        self.assertIsNotNone(template)
        assert template is not None
        self.assertEqual(template.topic, "measurement")
        self.assertEqual(template.expression, "answer_text=약 20 cm")

    def test_infers_toctoc_grade3_vertical_multiplication_page_templates(self) -> None:
        cases = {
            "p17": "answer_text=180, 792, 966, 775 / 도전: 23×12=276개",
            "p19": "answer_text=1206, 1505, 1404, 2268 / 도전: 52×71=3692",
        }

        for page, expression in cases.items():
            with self.subTest(page=page):
                template = infer_elementary_visual_template(
                    f"/tmp/toctoc_g3_s2_똑똑수학탐험대_3학년_2학기_함께학습지_{page}.png",
                    raw_text="* 1 5 * 3 6",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "arithmetic")
                self.assertEqual(template.expression, expression)

    def test_infers_toctoc_grade4_multiplication_division_page_templates(self) -> None:
        cases = {
            "p48": "answer_text=325÷25의 몫은 10보다 크고 20보다 작습니다. / 225÷15=15, 234÷13=18",
            "p50": "answer_text=820×12=9840원, 360×14=5040g, 196×11=2156L",
        }

        for page, expression in cases.items():
            with self.subTest(page=page):
                template = infer_elementary_visual_template(
                    f"/tmp/toctoc_g4_s1_똑똑수학탐험대_4학년_1학기_함께학습지_{page}.png",
                    raw_text="영희가 과자의 값을 계산하기 위해 모두 얼마를 내야 하는지 계산",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "arithmetic")
                self.assertEqual(template.expression, expression)

    def test_infers_toctoc_grade5_fraction_decimal_page_templates(self) -> None:
        cases = {
            ("s1", "p25"): ("arithmetic", "answer_text=30=3×5×2, 45=3×5×3, 최대공약수 3×5=15 / 21과 35의 최대공약수 7 / 24와 18의 최대공약수 6명"),
            ("s1", "p57"): ("fraction_ratio", "answer_text=3/8+1/4=5/8, 1/4+1/8=3/8, 2/5+1/6=17/30, 1/6+3/12=5/12, 1/3+4/11=23/33, 1/4+1/6=5/12컵"),
            ("s1", "p59"): ("fraction_ratio", "answer_text=5/8+7/12=1 5/24, 3/4+4/5=1 11/20, 2/5+7/10=1 1/10, 5/6+4/9=1 5/18, 3/9+13/18=1 1/18, 3/8+5/6=1 5/24"),
            ("s1", "p63"): ("fraction_ratio", "answer_text=5/6-3/8=11/24, 5/6-3/10=8/15, 3/5-1/2=1/10, 7/12-7/24=7/24, 2/3-3/5=1/15, 효주가 11/24컵 더 많이 사용"),
            ("s2", "p61"): ("fraction_ratio", "answer_text=0.6×0.5=0.3, 0.21×0.7=0.147, 0.95×0.48≈0.456, 0.8×0.73=0.584kg"),
            ("s2", "p63"): ("fraction_ratio", "answer_text=1.27×4.8=6.096, 9.1×8.4=76.44, 97.3×0.79=76.867, 새 놀이터 가로 14.4m, 세로 12.3m, 넓이 177.12m²"),
            ("s2", "p75"): ("geometry", "answer_text=4×(6+7+12)=100cm"),
        }

        for (semester, page), (topic, expression) in cases.items():
            with self.subTest(semester=semester, page=page):
                template = infer_elementary_visual_template(
                    f"/tmp/toctoc_g5_{semester}_똑똑수학탐험대_5학년_{'1' if semester == 's1' else '2'}학기_함께학습지_{page}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_toctoc_grade5_decimal_segment_templates(self) -> None:
        cases = {
            1: "answer_text=6.096, 76.44",
            2: "answer_text=97.3×0.79=76.867",
            3: "answer_text=가로 14.4m, 세로 12.3m, 넓이 177.12m²",
        }

        for index, expression in cases.items():
            with self.subTest(index=index):
                template = infer_elementary_visual_template(
                    f"/tmp/toctoc_g5_s2_똑똑수학탐험대_5학년_2학기_함께학습지_p63_문항{index:02d}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_second_semester_time_round1_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=5, 35",
            ("p01", "문항02"): "answer_text=8, 25",
            ("p01", "문항03"): "answer_text=9 시 45 분",
            ("p01", "문항04"): "answer_text=2 시 39 분",
            ("p01", "문항05"): "answer_text=2, 55, 3, 5",
            ("p01", "문항06"): "answer_text=5, 10",
            ("p01", "문항07"): "answer_text=1일 6시간에 ○표",
            ("p01", "문항08"): "answer_text=오후",
            ("p02", "문항01"): "answer_text=15일에 ○표",
            ("p02", "문항02"): "answer_text=12 분",
            ("p02", "문항03"): "answer_text=1 시간 20 분",
            ("p02", "문항04"): "answer_text=5 바퀴",
            ("p02", "문항05"): "answer_text=12 시간",
            ("p02", "문항06"): "answer_text=④",
            ("p02", "문항07"): "answer_text=24 시간",
            ("p02", "문항08"): "answer=11",
            ("p02", "문항09"): "answer_text=16 일",
            ("p02", "문항10"): "answer_text=토요일",
            ("p02", "문항11"): "answer_text=91 일",
            ("p02", "문항12"): "answer_text=16 일",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-2_4단원_시각과시간_1회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "measurement")
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_second_semester_time_round2_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=12, 15",
            ("p01", "문항02"): "answer_text=7, 5",
            ("p01", "문항03"): "answer_text=8 시 50 분",
            ("p01", "문항04"): "answer_text=6 시 12 분",
            ("p01", "문항05"): "answer_text=10, 45, 11, 15",
            ("p01", "문항06"): "answer_text=3, 5",
            ("p01", "문항07"): "answer_text=40시간에 ○표",
            ("p01", "문항08"): "answer_text=오전",
            ("p02", "문항01"): "answer_text=20일에 ○표",
            ("p02", "문항02"): "answer_text=205 분",
            ("p02", "문항03"): "answer_text=1 시간 30 분",
            ("p02", "문항04"): "answer_text=4 바퀴",
            ("p02", "문항05"): "answer_text=24 시간",
            ("p02", "문항06"): "answer_text=①",
            ("p02", "문항07"): "answer_text=12 시간",
            ("p02", "문항08"): "answer=16",
            ("p02", "문항09"): "answer_text=26 일",
            ("p02", "문항10"): "answer_text=일요일",
            ("p02", "문항11"): "answer_text=61 일",
            ("p02", "문항12"): "answer_text=23 일",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-2_4단원_시각과시간_2회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "measurement")
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_second_semester_time_round3_templates(self) -> None:
        cases = {
            ("p01", "문항01"): "answer_text=3, 45",
            ("p01", "문항02"): "answer_text=6, 45",
            ("p01", "문항03"): "answer_text=1 시 15 분",
            ("p01", "문항04"): "answer_text=9 시 26 분",
            ("p01", "문항05"): "answer_text=4, 45, 5, 15",
            ("p01", "문항06"): "answer_text=3, 45",
            ("p01", "문항07"): "answer_text=2일 5시간에 ○표",
            ("p01", "문항08"): "answer_text=오후",
            ("p02", "문항01"): "answer_text=25일에 ○표",
            ("p02", "문항02"): "answer_text=30 분",
            ("p02", "문항03"): "answer_text=1 시간 10 분",
            ("p02", "문항04"): "answer_text=3 바퀴",
            ("p02", "문항05"): "answer_text=12 바퀴",
            ("p02", "문항06"): "answer_text=⑤",
            ("p02", "문항07"): "answer_text=12 시간",
            ("p02", "문항08"): "answer_text=25 일",
            ("p02", "문항09"): "answer_text=19 일",
            ("p02", "문항10"): "answer_text=화요일",
            ("p02", "문항11"): "answer_text=61 일",
            ("p02", "문항12"): "answer_text=17 일",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-2_4단원_시각과시간_3회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "measurement")
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_second_semester_table_graph_round1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=8일",
            "문항02": "answer_text=6칸",
            "문항03": "answer_text=연필 3, 지우개 3, 가위 2, 공책 2, 합계 10",
            "문항04": "answer_text=10개",
            "문항05": "answer=1",
            "문항06": "answer_text=13일",
            "문항07": "answer_text=맑음, 7일",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-2_5단원_표와그래프_1회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "statistics")
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_second_semester_table_graph_page1_review_templates(self) -> None:
        cases = {
            ("초2-2_5단원_표와그래프_1회_p01", "문항02"): "answer_text=서연, 태민",
            ("초2-2_5단원_표와그래프_1회_p01", "문항03"): (
                "answer_text=사자 3명, 코끼리 2명, 기린 3명, 판다 4명, 합계 12명"
            ),
            ("초2-2_5단원_표와그래프_1회_p01", "문항04"): "answer_text=3명",
            ("초2-2_5단원_표와그래프_1회_p01", "문항06"): (
                "answer_text=1: 2번, 2: 1번, 3: 3번, 4: 1번, 5: 2번, 6: 3번, 합계 12번"
            ),
            ("초2-2_5단원_표와그래프_1회_p01", "문항07"): (
                "answer_text=주사위 눈 1:2, 2:1, 3:3, 4:1, 5:2, 6:3"
            ),
            ("초2-2_5단원_표와그래프_1회_p01", "문항08"): "answer_text=주사위의 눈",
            ("초2-2_5단원_표와그래프_1회_p02", "문항01"): (
                "answer_text=준혁 2개, 가영 3개, 승민 2개, 수진 4개"
            ),
            ("초2-2_5단원_표와그래프_1회_p02", "문항02"): (
                "answer_text=1번 2명, 2번 3명, 3번 2명, 4번 4명"
            ),
            ("초2-2_5단원_표와그래프_1회_p02", "문항03"): (
                "answer_text=피아노 6명, 기타 2명, 바이올린 5명, 플루트 4명"
            ),
            ("초2-2_5단원_표와그래프_1회_p02", "문항04"): "answer_text=17명",
            ("초2-2_5단원_표와그래프_1회_p02", "문항05"): "answer_text=피아노",
            ("초2-2_5단원_표와그래프_2회_p01", "문항01"): "answer_text=데이지에 ○표",
            ("초2-2_5단원_표와그래프_2회_p01", "문항02"): "answer_text=준호, 윤호, 민서",
            ("초2-2_5단원_표와그래프_2회_p01", "문항03"): "answer_text=12명",
            ("초2-2_5단원_표와그래프_2회_p01", "문항04"): "answer_text=4명",
            ("초2-2_5단원_표와그래프_2회_p01", "문항05"): "answer_text=12명",
            ("초2-2_5단원_표와그래프_2회_p02", "문항01"): (
                "answer_text=빨강 6개, 노랑 5개, 초록 2개, 파랑 5개, 합계 18개"
            ),
            ("초2-2_5단원_표와그래프_2회_p02", "문항04"): "answer_text=4개",
            ("초2-2_5단원_표와그래프_2회_p02", "문항05"): "answer_text=10명",
            ("초2-2_5단원_표와그래프_2회_p03", "문항01"): (
                "answer_text=독서 3명, 게임 4명, 운동 6명"
            ),
            ("초2-2_5단원_표와그래프_2회_p03", "문항03"): "answer_text=8칸",
            ("초2-2_5단원_표와그래프_2회_p03", "문항05"): (
                "answer_text=빨강 6개, 노랑 5개, 초록 2개, 파랑 5개, 합계 18개"
            ),
            ("초2-2_5단원_표와그래프_2회_p03", "문항08"): "answer_text=감, 1개",
            ("초2-2_5단원_표와그래프_3회_p01", "문항02"): "answer_text=서연, 선아, 시연",
            ("초2-2_5단원_표와그래프_3회_p01", "문항03"): "answer_text=2, 3, 1, 2, 8",
            ("초2-2_5단원_표와그래프_3회_p01", "문항04"): "answer_text=2명",
            ("초2-2_5단원_표와그래프_3회_p01", "문항05"): "answer_text=8명",
            ("초2-2_5단원_표와그래프_3회_p01", "문항06"): (
                "answer_text=A형 3명, B형 3명, AB형 2명, O형 1명, 합계 9명"
            ),
            ("초2-2_5단원_표와그래프_3회_p01", "문항07"): (
                "answer_text=A형 3명, B형 3명, AB형 2명, O형 1명"
            ),
            ("초2-2_5단원_표와그래프_3회_p01", "문항08"): "answer_text=혈액형",
            ("초2-2_5단원_표와그래프_3회_p02", "문항01"): "answer_text=12명",
            ("초2-2_5단원_표와그래프_3회_p02", "문항02"): "answer_text=1, 3, 3, 4, 2",
            ("초2-2_5단원_표와그래프_3회_p02", "문항04"): "answer_text=8명",
            ("초2-2_5단원_표와그래프_3회_p02", "문항06"): "answer_text=17명",
        }

        for (page, card_label), expression in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(f"/tmp/{page}_{card_label}.png")

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "statistics")
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_second_semester_table_graph_round3_templates(self) -> None:
        cases = {
            "문항01": "answer_text=6칸",
            "문항02": "answer_text=딸기 4, 귤 3, 바나나 3, 멜론 2, 합계 12",
            "문항03": "answer_text=4개",
            "문항04": "answer_text=12개",
            "문항05": "answer_text=12명",
            "문항06": "answer=9",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초2-2_5단원_표와그래프_3회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "statistics")
                self.assertEqual(template.expression, expression)

    def test_infers_grade2_classification_and_rules_review_templates(self) -> None:
        cases = {
            ("초2-1_5단원_분류하기_1회_p01", "문항05"): ("statistics", "answer_text=알파벳과 숫자"),
            ("초2-1_5단원_분류하기_1회_p01", "문항06"): ("statistics", "answer_text=사회, 과학"),
            ("초2-1_5단원_분류하기_1회_p02", "문항01"): ("statistics", "answer_text=③ 축구, 수영"),
            ("초2-1_5단원_분류하기_1회_p02", "문항03"): ("statistics", "answer_text=가, 라"),
            ("초2-1_5단원_분류하기_1회_p02", "문항06"): (
                "statistics",
                "answer_text=노란색 3명, 파란색 4명, 보라색 2명, 빨간색 3명",
            ),
            ("초2-1_5단원_분류하기_1회_p03", "문항02"): ("statistics", "answer_text=과학책 6권"),
            ("초2-1_5단원_분류하기_1회_p03", "문항04"): ("statistics", "answer_text=라면"),
            ("초2-1_5단원_분류하기_1회_p03", "문항06"): ("statistics", "answer_text=축구"),
            ("초2-1_5단원_분류하기_2회_p03", "문항07"): ("statistics", "answer=3"),
            ("초2-1_5단원_분류하기_3회_p01", "문항01"): ("statistics", "answer_text=모양"),
            ("초2-1_5단원_분류하기_3회_p01", "문항05"): (
                "statistics",
                "answer_text=빨간색: 3, 4, 6, 9 / 초록색: 2, 10 / 파란색: 1, 5, 7, 8",
            ),
            ("초2-1_5단원_분류하기_3회_p01", "문항07"): ("statistics", "answer_text=2개"),
            ("초2-1_5단원_분류하기_3회_p02", "문항04"): (
                "statistics",
                "answer_text=먹이가 풀인 것: 소, 양, 염소, 기린 / 먹이가 고기인 것: 호랑이, 사자, 하이에나",
            ),
            ("초2-1_5단원_분류하기_3회_p02", "문항06"): ("statistics", "answer_text=잠자리"),
            ("초2-1_5단원_분류하기_3회_p03", "문항03"): ("statistics", "answer_text=승용차, 3대"),
            ("초2-1_5단원_분류하기_3회_p03", "문항06"): (
                "statistics",
                "answer_text=채소: 파프리카, 오이 / 과일: 사과, 딸기, 귤, 감, 배",
            ),
            ("초2-1_5단원_분류하기_3회_p03", "문항07"): ("statistics", "answer_text=과일, 3개"),
            ("초2-2_6단원_규칙찾기_1회_p01", "문항02"): ("pattern", "answer=1"),
            ("초2-2_6단원_규칙찾기_1회_p01", "문항03"): ("pattern", "answer=2"),
            ("초2-2_6단원_규칙찾기_1회_p01", "문항06"): ("pattern", "answer_text=같습니다에 ○표"),
            ("초2-2_6단원_규칙찾기_1회_p02", "문항02"): ("pattern", "answer_text=13, 12, 13"),
            ("초2-2_6단원_규칙찾기_1회_p02", "문항03"): ("pattern", "answer_text=24, 20, 25"),
            ("초2-2_6단원_규칙찾기_1회_p02", "문항07"): (
                "pattern",
                "answer_text=1 3 2 2 1 3 2 2 1 3 2 2 1 3 2 2 1 3 2 2 1",
            ),
            ("초2-2_6단원_규칙찾기_1회_p03", "문항02"): ("pattern", "answer_text=7개"),
            ("초2-2_6단원_규칙찾기_1회_p03", "문항04"): ("pattern", "answer_text=5, 12, 19, 26일"),
            ("초2-2_6단원_규칙찾기_1회_p03", "문항06"): ("pattern", "answer_text=30"),
            ("초2-2_6단원_규칙찾기_1회_p03", "문항07"): ("pattern", "answer_text=3, 4"),
            ("초2-2_6단원_규칙찾기_2회_p01", "문항02"): ("pattern", "answer=2"),
            ("초2-2_6단원_규칙찾기_2회_p01", "문항03"): ("pattern", "answer=4"),
            ("초2-2_6단원_규칙찾기_2회_p01", "문항06"): ("pattern", "answer_text=홀수에 ○표"),
            ("초2-2_6단원_규칙찾기_2회_p02", "문항02"): ("pattern", "answer_text=68"),
            ("초2-2_6단원_규칙찾기_2회_p02", "문항07"): (
                "pattern",
                "answer_text=1 2 2 3 1 2 2 3 1 2 2 3 1 2 2 3 1 2",
            ),
            ("초2-2_6단원_규칙찾기_2회_p03", "문항02"): ("pattern", "answer_text=10개"),
            ("초2-2_6단원_규칙찾기_2회_p03", "문항06"): ("pattern", "answer_text=68"),
            ("초2-2_6단원_규칙찾기_2회_p03", "문항07"): ("pattern", "answer_text=5, 4"),
            ("초2-2_6단원_규칙찾기_3회_p01", "문항02"): ("pattern", "answer=2"),
            ("초2-2_6단원_규칙찾기_3회_p01", "문항03"): ("pattern", "answer=4"),
            ("초2-2_6단원_규칙찾기_3회_p01", "문항06"): ("pattern", "answer_text=짝수에 ○표"),
            ("초2-2_6단원_규칙찾기_3회_p02", "문항01"): ("pattern", "answer_text=4번"),
            ("초2-2_6단원_규칙찾기_3회_p02", "문항02"): ("pattern", "answer_text=13, 12, 13"),
            ("초2-2_6단원_규칙찾기_3회_p02", "문항07"): ("pattern", "answer_text=순서대로"),
            ("초2-2_6단원_규칙찾기_3회_p03", "문항01"): ("pattern", "answer_text=7개"),
            ("초2-2_6단원_규칙찾기_3회_p03", "문항02"): ("pattern", "answer_text=4번"),
            ("초2-2_6단원_규칙찾기_3회_p03", "문항05"): ("pattern", "answer_text=2, 3"),
        }

        for (page, card_label), (topic, expression) in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(f"/tmp/{page}_{card_label}.png")

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_diagnostic_round3_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=3, 2, 5",
            "문항02": "answer_text=742, 852",
            "문항03": "answer_text=삼각형: 변 3개, 꼭짓점 3개 / 사다리꼴: 변 4개, 꼭짓점 4개",
            "문항04": "answer_text=62, 34",
            "문항05": "answer_text=28+37에 ○표",
            "문항06": "answer_text=6칸 색칠",
            "문항07": "answer_text=첫 번째에 ○표",
            "문항08": "answer_text=오렌지, 4",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0011__무료_PDF__초3__수학__진단평가_기초학력_진단평가__연습용문제__3회__초3__진단평가_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_diagnostic_round3_page2_templates(self) -> None:
        cases = {
            "문항01": "answer=10",
            "문항02": "answer_text=3, 7, 7, 7, 21",
            "문항03": "answer_text=3, 8, 5, 2",
            "문항04": "answer_text=>",
            "문항05": "answer=6",
            "문항06": "answer_text=0, 1, 2, 3, 4, 5",
            "문항07": "answer_text=>",
            "문항08": "answer_text=③",
            "문항09": "answer_text=11 시 55 분",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0011__무료_PDF__초3__수학__진단평가_기초학력_진단평가__연습용문제__3회__초3__진단평가_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_diagnostic_round3_page3_templates(self) -> None:
        cases = {
            "문항01": "answer_text=7명",
            "문항02": "answer_text=10개",
            "문항03": "answer_text=115분",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0011__무료_PDF__초3__수학__진단평가_기초학력_진단평가__연습용문제__3회__초3__진단평가_3회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_diagnostic_round2_page1_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=<"),
            "문항02": ("arithmetic", "answer_text=594"),
            "문항03": ("geometry", "answer_text=(1) 선분 ㄷㄹ, (2) 직선 ㄷㄹ, (3) 반직선 ㄷㄹ"),
            "문항04": ("arithmetic", "answer_text=24÷6=4"),
            "문항05": ("arithmetic", "answer_text=8 개"),
            "문항06": ("arithmetic", "answer_text=30"),
            "문항07": ("arithmetic", "answer_text=294 쪽"),
            "문항08": ("measurement", "answer_text=합 28 km 204 m, 차 3 km 744 m"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0009__무료_PDF__초4__수학__진단평가_기초학력_진단평가__연습용문제__2회__초4__진단평가_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_diagnostic_round2_page2_templates(self) -> None:
        cases = {
            "문항01": ("measurement", "answer_text=12 시 39 분 20 초"),
            "문항02": ("fraction_ratio", "answer_text=>"),
            "문항03": ("arithmetic", "answer_text=471×6 ↔ 2826, 326×4 ↔ 1304"),
            "문항04": ("arithmetic", "answer_text=1307 개"),
            "문항05": ("arithmetic", "answer_text=44÷4 ↔ 11, 39÷3 ↔ 13, 24÷2 ↔ 12"),
            "문항06": ("measurement", "answer_text=12 cm"),
            "문항07": ("geometry", "answer_text=3 cm"),
            "문항08": ("fraction_ratio", "answer_text=7"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0009__무료_PDF__초4__수학__진단평가_기초학력_진단평가__연습용문제__2회__초4__진단평가_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_diagnostic_round2_page3_templates(self) -> None:
        cases = {
            "문항01": ("fraction_ratio", "answer_text=5/9 에 ○표"),
            "문항02": ("measurement", "answer_text=2 L 900 mL"),
            "문항03": ("measurement", "answer_text=③, ⑤"),
            "문항04": ("statistics", "answer_text=51 개"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0009__무료_PDF__초4__수학__진단평가_기초학력_진단평가__연습용문제__2회__초4__진단평가_2회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_diagnostic_round1_page1_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=(1) 1003, (2) 345"),
            "문항02": ("arithmetic", "answer_text=지민, 22 장"),
            "문항03": ("measurement", "answer_text=6 cm"),
            "문항04": ("arithmetic", "answer_text=7"),
            "문항05": ("arithmetic", "answer_text=8 개"),
            "문항06": ("arithmetic", "answer_text=232"),
            "문항07": ("arithmetic", "answer_text=160 자루"),
            "문항08": ("measurement", "answer_text=④"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0010__무료_PDF__초4__수학__진단평가_기초학력_진단평가__연습용문제__1회__초4__진단평가_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_diagnostic_round1_page2_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=세 번째에 ○표"),
            "문항02": ("fraction_ratio", "answer_text=1/12"),
            "문항03": ("arithmetic", "answer_text=40×30 ↔ 1200, 20×80 ↔ 1600, 60×40 ↔ 2400"),
            "문항04": ("arithmetic", "answer_text=1488"),
            "문항05": ("arithmetic", "answer_text=다, 가, 나"),
            "문항06": ("arithmetic", "answer_text=18 개"),
            "문항07": ("geometry", "answer_text=반지름 7 cm, 지름 14 cm"),
            "문항08": ("arithmetic", "answer_text=5 개"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0010__무료_PDF__초4__수학__진단평가_기초학력_진단평가__연습용문제__1회__초4__진단평가_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_diagnostic_round1_page3_templates(self) -> None:
        cases = {
            "문항01": ("fraction_ratio", "answer_text=3, 15"),
            "문항02": ("measurement", "answer_text=가 컵"),
            "문항03": ("measurement", "answer_text=16006"),
            "문항04": ("statistics", "answer_text=사이다"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0010__무료_PDF__초4__수학__진단평가_기초학력_진단평가__연습용문제__1회__초4__진단평가_1회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_big_number_round1_page1_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=(1) 80000, 30, 1, (2) 40000+3000+1"),
            "문항02": ("arithmetic", "answer_text=9999"),
            "문항03": ("arithmetic", "answer_text=팔만 이천팔, 80160"),
            "문항04": ("arithmetic", "answer_text=영수"),
            "문항05": ("arithmetic", "answer_text=100000 배"),
            "문항06": ("arithmetic", "answer_text=(1) 5, (2) 3"),
            "문항07": ("pattern", "answer_text=8400"),
            "문항08": ("arithmetic", "answer_text=96532"),
            "문항09": ("arithmetic", "answer_text=5, 6, 7, 8, 9"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_1단원_큰수_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_big_number_round1_page2_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=다, 라, 가, 나"),
            "문항02": ("arithmetic", "answer_text=3440100"),
            "문항03": ("arithmetic", "answer_text=100 배"),
            "문항04": ("arithmetic", "answer_text=3 조 950 억"),
            "문항05": ("arithmetic", "answer_text=백사십구억 육천만 킬로미터"),
            "문항06": ("arithmetic", "answer_text=30 개"),
            "문항07": (
                "arithmetic",
                "answer_text=700만의 1000배 ↔ 70억, 7000만의 10배 ↔ 7억, 7억의 100배 ↔ 700억",
            ),
            "문항08": ("arithmetic", "answer_text=다"),
            "문항09": ("arithmetic", "answer_text=139700 원"),
            "문항10": ("measurement", "answer_text=10 km"),
            "문항11": ("arithmetic", "answer_text=200000"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_1단원_큰수_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_big_number_round2_page1_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=3000"),
            "문항02": ("arithmetic", "answer_text=오만이천구백칠십사, 52974"),
            "문항03": ("arithmetic", "answer_text=130245"),
            "문항04": ("arithmetic", "answer_text=③"),
            "문항05": ("arithmetic", "answer_text=만의 자리"),
            "문항06": ("arithmetic", "answer_text=100 배"),
            "문항07": ("arithmetic", "answer_text=32"),
            "문항08": ("arithmetic", "answer_text=1억"),
            "문항09": ("arithmetic", "answer_text=1 억"),
            "문항10": ("arithmetic", "answer_text=3000000000000"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_1단원_큰수_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_big_number_round2_page2_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=3015842605970043"),
            "문항02": ("arithmetic", "answer_text=2"),
            "문항03": ("arithmetic", "answer_text=5 개"),
            "문항04": ("arithmetic", "answer_text=400억"),
            "문항05": ("arithmetic", "answer_text=71410 원"),
            "문항06": ("arithmetic", "answer_text=2100000 개"),
            "문항07": ("arithmetic", "answer_text=375 장"),
            "문항08": ("arithmetic", "answer_text=1230000 원"),
            "문항09": ("arithmetic", "answer_text=20020000 개"),
            "문항10": ("arithmetic", "answer_text=0, 1, 2"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_1단원_큰수_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_big_number_round3_page1_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=200"),
            "문항02": ("arithmetic", "answer_text=87625"),
            "문항03": ("arithmetic", "answer_text=23459"),
            "문항04": ("arithmetic", "answer_text=①"),
            "문항05": ("arithmetic", "answer_text=백만의 자리"),
            "문항06": ("arithmetic", "answer_text=1000 배"),
            "문항07": ("arithmetic", "answer_text=650"),
            "문항08": ("arithmetic", "answer_text=1억"),
            "문항09": ("arithmetic", "answer_text=10 억"),
            "문항10": ("arithmetic", "answer_text=324500420008000"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_1단원_큰수_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_big_number_round3_page2_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=5026937036292534"),
            "문항02": ("arithmetic", "answer_text=5"),
            "문항03": ("arithmetic", "answer_text=7 개"),
            "문항04": ("arithmetic", "answer_text=7 번"),
            "문항05": ("arithmetic", "answer_text=65450 원"),
            "문항06": ("arithmetic", "answer_text=800000 개"),
            "문항07": ("arithmetic", "answer_text=2470 장"),
            "문항08": ("measurement", "answer_text=1496 배"),
            "문항09": ("arithmetic", "answer_text=20008000 개"),
            "문항10": ("arithmetic", "answer_text=5, 6, 7, 8, 9"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_1단원_큰수_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_angle_round1_page1_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=나, 다, 가, 라"),
            "문항02": ("geometry", "answer_text=55°"),
            "문항03": ("geometry", "answer_text=어림한 각도 : 125° 잰 각도: 125°"),
            "문항04": ("geometry", "answer_text=⑴ 70° ⑵ 55°"),
            "문항05": ("geometry", "answer_text=가, 다, 나"),
            "문항06": ("geometry", "answer_text=가. 85 나. 100"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_2단원_각도_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_angle_round1_page2_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=⑴ 3 ⑵ 4"),
            "문항02": ("geometry", "answer_text=⑴ 둔각 ⑵ 직각"),
            "문항03": ("geometry", "answer_text=⑴ 200° ⑵ 150°"),
            "문항04": ("geometry", "answer_text=11 개"),
            "문항05": ("geometry", "answer_text=나"),
            "문항06": ("geometry", "answer_text=15°"),
            "문항07": ("geometry", "answer_text=⑴ 205° ⑵ 78°"),
            "문항08": ("geometry", "answer_text=25°"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_2단원_각도_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_angle_round1_page3_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=55°"),
            "문항02": ("geometry", "answer_text=85°"),
            "문항03": ("geometry", "answer_text=150°"),
            "문항04": ("geometry", "answer_text=35°"),
            "문항05": ("geometry", "answer_text=150°"),
            "문항06": ("geometry", "answer_text=18°"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_2단원_각도_1회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_angle_round2_page1_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=㉠, ㉣, ㉢, ㉡"),
            "문항02": ("geometry", "answer_text=③"),
            "문항03": ("geometry", "answer_text=⑤"),
            "문항04": ("geometry", "answer_text=50°"),
            "문항05": ("geometry", "answer_text=65°"),
            "문항06": ("geometry", "answer_text=③"),
            "문항07": ("geometry", "answer_text=3 개"),
            "문항08": ("geometry", "answer_text=295°"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_2단원_각도_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_angle_round2_page2_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=88°"),
            "문항02": ("geometry", "answer_text=>"),
            "문항03": ("geometry", "answer_text=85°"),
            "문항04": ("geometry", "answer_text=60°"),
            "문항05": ("geometry", "answer_text=90°"),
            "문항06": ("geometry", "answer_text=108°"),
            "문항07": ("geometry", "answer_text=③"),
            "문항08": ("geometry", "answer_text=( ○ ) ( )"),
            "문항09": ("geometry", "answer_text=150°"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_2단원_각도_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_angle_round2_page3_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=120°"),
            "문항02": ("geometry", "answer_text=90°"),
            "문항03": ("geometry", "answer_text=130°"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_2단원_각도_2회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_angle_round3_page1_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=( ) ( ) ( ○ ) ( )"),
            "문항02": ("geometry", "answer_text=②"),
            "문항03": ("geometry", "answer_text=③"),
            "문항04": ("geometry", "answer_text=130°"),
            "문항05": ("geometry", "answer_text=40°"),
            "문항06": ("geometry", "answer_text=둔각, 직각, 예각"),
            "문항07": ("geometry", "answer_text=5 개"),
            "문항08": ("geometry", "answer_text=222°"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_2단원_각도_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_angle_round3_page2_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=57°"),
            "문항02": ("geometry", "answer_text=>"),
            "문항03": ("geometry", "answer_text=85°"),
            "문항04": ("geometry", "answer_text=110°"),
            "문항05": ("geometry", "answer_text=80°"),
            "문항06": ("geometry", "answer_text=54°"),
            "문항07": ("geometry", "answer_text=④"),
            "문항08": ("geometry", "answer_text=35"),
            "문항09": ("geometry", "answer_text=75°"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_2단원_각도_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_angle_round3_page3_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=60°"),
            "문항02": ("geometry", "answer_text=30°"),
            "문항03": ("geometry", "answer_text=132°"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_2단원_각도_3회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_mult_div_round1_page1_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=②"),
            "문항02": ("arithmetic", "answer_text=5000"),
            "문항03": ("arithmetic", "answer_text=20 장"),
            "문항04": ("arithmetic", "answer_text=30"),
            "문항05": ("arithmetic", "answer_text=10530 개"),
            "문항06": ("arithmetic", "answer_text=2520 자루"),
            "문항07": ("measurement", "answer_text=21750 km"),
            "문항08": ("arithmetic", "answer_text=10759"),
            "문항09": ("measurement", "answer_text=2024 cm"),
            "문항10": ("arithmetic", "answer_text=30"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_3단원_곱셈과나눗셈_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_mult_div_round1_page2_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=①"),
            "문항02": ("measurement", "answer_text=7 cm"),
            "문항03": ("arithmetic", "answer_text=몫 : 9, 나머지 : 67"),
            "문항04": ("arithmetic", "answer_text=360 개"),
            "문항05": ("arithmetic", "answer_text=6"),
            "문항06": ("arithmetic", "answer_text=나, 다, 가"),
            "문항07": ("arithmetic", "answer_text=12 개"),
            "문항08": ("arithmetic", "answer_text=33"),
            "문항09": ("arithmetic", "answer_text=<"),
            "문항10": ("measurement", "answer_text=8 개, 20 cm"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_3단원_곱셈과나눗셈_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_mult_div_round2_page1_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=③"),
            "문항02": ("arithmetic", "answer_text=20800"),
            "문항03": ("arithmetic", "answer_text=39 장"),
            "문항04": ("arithmetic", "answer_text=20"),
            "문항05": ("arithmetic", "answer_text=29200 일"),
            "문항06": ("arithmetic", "answer_text=2670 개"),
            "문항07": ("measurement", "answer_text=42000 m"),
            "문항08": ("arithmetic", "answer_text=12402"),
            "문항09": ("measurement", "answer_text=3216 cm"),
            "문항10": ("arithmetic", "answer_text=12"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_3단원_곱셈과나눗셈_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_mult_div_round2_page2_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=①"),
            "문항02": ("measurement", "answer_text=2 번"),
            "문항03": ("arithmetic", "answer_text=9"),
            "문항04": ("measurement", "answer_text=4 개, 71 cm"),
            "문항05": ("arithmetic", "answer_text=5"),
            "문항06": ("arithmetic", "answer_text=①, ②"),
            "문항07": ("arithmetic", "answer_text=7 봉지"),
            "문항08": ("arithmetic", "answer_text=55"),
            "문항09": ("arithmetic", "answer_text=몫 : 6, 나머지 : 36"),
            "문항10": ("arithmetic", "answer_text=9 상자, 19 개"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_3단원_곱셈과나눗셈_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_mult_div_round3_page1_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=⑤"),
            "문항02": ("arithmetic", "answer_text=㉠ 5, ㉡ 9, ㉢ 1"),
            "문항03": ("measurement", "answer_text=8000 mL"),
            "문항04": ("arithmetic", "answer_text=30"),
            "문항05": ("arithmetic", "answer_text=6350 개"),
            "문항06": ("arithmetic", "answer_text=5000 개"),
            "문항07": ("arithmetic", "answer_text=900"),
            "문항08": ("arithmetic", "answer_text=19872"),
            "문항09": ("measurement", "answer_text=1689 cm"),
            "문항10": ("arithmetic", "answer_text=11"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_3단원_곱셈과나눗셈_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_mult_div_round3_page2_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=가, 다, 라, 나"),
            "문항02": ("arithmetic", "answer_text=7 개"),
            "문항03": ("arithmetic", "answer_text=몫 : 9, 나머지 : 4"),
            "문항04": ("arithmetic", "answer_text=20 자루"),
            "문항05": ("arithmetic", "answer_text=가"),
            "문항06": ("arithmetic", "answer_text=5"),
            "문항07": ("arithmetic", "answer_text=4 명"),
            "문항08": ("arithmetic", "answer_text=10"),
            "문항09": ("arithmetic", "answer_text=40"),
            "문항10": ("arithmetic", "answer_text=127"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_3단원_곱셈과나눗셈_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_bar_graph_round1_page1_templates(self) -> None:
        cases = {
            "문항01": ("statistics", "answer_text=사과 5 명, 배 4 명, 포도 2 명, 감 4 명, 합계 15 명"),
            "문항02": ("statistics", "answer_text=사과 5 명, 배 4 명, 포도 2 명, 감 4 명 막대그래프"),
            "문항03": ("statistics", "answer_text=2 명"),
            "문항04": ("statistics", "answer_text=가 140 상자, 나 100 상자, 다 220 상자, 라 200 상자, 합계 660 상자"),
            "문항05": ("statistics", "answer_text=16 명"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_5단원_막대그래프_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_bar_graph_round2_page2_and_page3_templates(self) -> None:
        cases = {
            "p02_문항01": ("statistics", "answer_text=90 kg"),
            "p02_문항02": ("statistics", "answer_text=③"),
            "p02_문항03": ("statistics", "answer_text=2 배"),
            "p02_문항04": ("statistics", "answer_text=닭"),
            "p03_문항01": ("statistics", "answer_text=1 일"),
            "p03_문항02": ("statistics", "answer_text=28 대"),
            "p03_문항03": ("statistics", "answer_text=①"),
            "p03_문항04": ("statistics", "answer_text=3 칸"),
            "p03_문항05": ("statistics", "answer_text=3 칸"),
            "p04_문항01": ("statistics", "answer_text=다, 라, 가, 나"),
            "p04_문항02": ("statistics", "answer_text=야구 7 명, 탁구 6 명"),
            "p04_문항03": ("statistics", "answer_text=30 장"),
            "p04_문항04": ("statistics", "answer_text=23 명"),
            "p04_문항05": ("statistics", "answer_text=29회 베이징"),
        }

        for card_ref, (topic, expression) in cases.items():
            page, card_label = card_ref.split("_")
            with self.subTest(card_ref=card_ref):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_5단원_막대그래프_2회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_bar_graph_round3_page2_and_page3_templates(self) -> None:
        cases = {
            "p02_문항01": ("statistics", "answer_text=②, ③"),
            "p02_문항02": ("statistics", "answer_text=③"),
            "p02_문항03": ("statistics", "answer_text=윷놀이 9 명, 팽이치기 7 명, 제기차기 4 명, 연날리기 4 명, 합계 24 명"),
            "p02_문항04": ("statistics", "answer_text=2반"),
            "p03_문항01": ("statistics", "answer_text=50 분"),
            "p03_문항02": ("statistics", "answer_text=1100 대"),
            "p03_문항03": ("statistics", "answer_text=①"),
            "p03_문항04": ("statistics", "answer_text=26 칸"),
            "p03_문항05": ("statistics", "answer_text=5 칸"),
            "p03_문항06": ("statistics", "answer_text=다, 가, 나, 라"),
            "p04_문항01": ("statistics", "answer_text=야구 7 명, 탁구 6 명"),
            "p04_문항02": ("statistics", "answer_text=30 장"),
            "p04_문항03": ("statistics", "answer_text=23 명"),
            "p04_문항04": ("statistics", "answer_text=29회 베이징"),
        }

        for card_ref, (topic, expression) in cases.items():
            page, card_label = card_ref.split("_")
            with self.subTest(card_ref=card_ref):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_5단원_막대그래프_3회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_rules_round1_templates(self) -> None:
        cases = {
            "p01_문항01": ("pattern", "answer_text=● 2038, ▲ 2058"),
            "p01_문항02": ("pattern", "answer_text=⑤"),
            "p01_문항03": ("pattern", "answer_text=47"),
            "p01_문항04": ("pattern", "answer_text=486"),
            "p01_문항05": ("pattern", "answer_text=4412"),
            "p01_문항06": ("pattern", "answer_text=ㄱ 12, ㄴ 80, ㄷ 18"),
            "p01_문항07": ("pattern", "answer_text=■ 0, ● 9"),
            "p02_문항01": ("pattern", "answer_text=11 개"),
            "p02_문항02": ("pattern", "answer_text=초록색, 사각형"),
            "p02_문항03": ("pattern", "answer_text=15 개"),
            "p02_문항04": ("pattern", "answer_text=325, 767"),
            "p02_문항05": ("pattern", "answer_text=①"),
            "p02_문항06": ("pattern", "answer_text=③"),
            "p02_문항07": ("pattern", "answer_text=550 + 460 = 560 + 450"),
            "p03_문항01": ("pattern", "answer_text=라"),
            "p03_문항02": ("pattern", "answer_text=⑤"),
            "p03_문항03": ("pattern", "answer_text=9000002, 999999"),
            "p03_문항04": ("pattern", "answer_text=나"),
            "p03_문항05": ("pattern", "answer_text=3, 3, 3, 214"),
            "p03_문항06": ("pattern", "answer_text=18"),
        }

        for card_ref, (topic, expression) in cases.items():
            page, card_label = card_ref.split("_")
            with self.subTest(card_ref=card_ref):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_6단원_규칙찾기_1회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_rules_round2_page1_and_page2_templates(self) -> None:
        cases = {
            "p01_문항01": ("pattern", "answer_text=■ 3307, ● 5307"),
            "p01_문항02": ("pattern", "answer_text=900"),
            "p01_문항03": ("pattern", "answer_text=11/15, 20/27"),
            "p01_문항04": ("pattern", "answer_text=324"),
            "p01_문항05": ("pattern", "answer_text=42094"),
            "p01_문항06": ("pattern", "answer_text=ㄱ 27, ㄴ 108, ㄷ 405"),
            "p01_문항07": ("pattern", "answer_text=■ 8, ● 9"),
            "p02_문항01": ("pattern", "answer_text=13 개"),
            "p02_문항02": ("pattern", "answer_text=보라색, 삼각형"),
            "p02_문항03": ("pattern", "answer_text=10 개"),
            "p02_문항04": ("pattern", "answer_text=③"),
            "p02_문항05": ("pattern", "answer_text=②"),
            "p02_문항06": ("pattern", "answer_text=350, 1150"),
            "p02_문항07": ("pattern", "answer_text=다"),
            "p03_문항01": ("pattern", "answer_text=350 + 220 - 100 = 470"),
            "p03_문항02": ("pattern", "answer_text=12 + 15 + 18 = 45"),
            "p03_문항03": ("pattern", "answer_text=다"),
            "p03_문항04": ("pattern", "answer_text=1111112, 9999999"),
            "p03_문항05": ("pattern", "answer_text=3, 3, 3, 329"),
            "p03_문항06": ("pattern", "answer_text=17"),
        }

        for card_ref, (topic, expression) in cases.items():
            page, card_label = card_ref.split("_")
            with self.subTest(card_ref=card_ref):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_6단원_규칙찾기_2회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_rules_round3_templates(self) -> None:
        cases = {
            "p01_문항01": ("pattern", "answer_text=2202, 2402"),
            "p01_문항02": ("pattern", "answer_text=④"),
            "p01_문항03": ("pattern", "answer_text=다"),
            "p01_문항04": ("pattern", "answer_text=164"),
            "p01_문항05": ("pattern", "answer_text=20292"),
            "p01_문항06": ("pattern", "answer_text=ㄱ 64, ㄴ 256, ㄷ 384"),
            "p02_문항01": ("pattern", "answer_text=● 2, ▲ 3"),
            "p02_문항02": ("pattern", "answer_text=16 개"),
            "p02_문항03": ("pattern", "answer_text=③"),
            "p02_문항04": ("pattern", "answer_text=초록색, 사각형"),
            "p02_문항05": ("pattern", "answer_text=36 개"),
            "p02_문항06": ("pattern", "answer_text=라"),
            "p03_문항01": ("pattern", "answer_text=②"),
            "p03_문항02": ("pattern", "answer_text=3900, 5400"),
            "p03_문항03": ("pattern", "answer_text=나"),
            "p03_문항04": ("pattern", "answer_text=③"),
            "p03_문항05": ("pattern", "answer_text=6600 - 2400 = 4200"),
            "p03_문항06": ("pattern", "answer_text=6666662, 3333339"),
            "p04_문항01": ("pattern", "answer_text=3, 3, 3, 158"),
            "p04_문항02": ("pattern", "answer_text=22"),
        }

        for card_ref, (topic, expression) in cases.items():
            page, card_label = card_ref.split("_")
            with self.subTest(card_ref=card_ref):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_6단원_규칙찾기_3회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_bar_graph_round1_page2_templates(self) -> None:
        cases = {
            "문항01": ("statistics", "answer_text=60 분"),
            "문항02": ("statistics", "answer_text=16 칸"),
            "문항03": ("statistics", "answer_text=④"),
            "문항04": ("statistics", "answer_text=나"),
            "문항05": ("statistics", "answer_text=오세아니아"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_5단원_막대그래프_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_bar_graph_round1_page3_templates(self) -> None:
        cases = {
            "문항01": ("statistics", "answer_text=크림빵, 16 개"),
            "문항02": ("statistics", "answer_text=13 일"),
            "문항03": ("statistics", "answer_text=①"),
            "문항04": ("statistics", "answer_text=6 칸"),
            "문항05": ("statistics", "answer_text=7 칸"),
            "문항06": ("statistics", "answer_text=다, 나, 가, 라"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_5단원_막대그래프_1회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_bar_graph_round1_page4_templates(self) -> None:
        cases = {
            "문항01": ("statistics", "answer_text=4, 10"),
            "문항02": ("statistics", "answer_text=92 권"),
            "문항03": ("statistics", "answer_text=26 명"),
            "문항04": ("statistics", "answer_text=다"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_5단원_막대그래프_1회_p04_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_bar_graph_round2_page1_templates(self) -> None:
        cases = {
            "문항01": ("statistics", "answer_text=32 일"),
            "문항02": ("statistics", "answer_text=18 일"),
            "문항03": ("statistics", "answer_text=월별 비가 온 날수"),
            "문항04": ("statistics", "answer_text=6 월, 4 월, 5 월, 3 월"),
            "문항05": ("statistics", "answer_text=10 점"),
            "문항06": ("statistics", "answer_text=봄 24 명, 여름 16 명, 가을 28 명, 겨울 34 명, 합계 102 명"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_5단원_막대그래프_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_bar_graph_round3_page1_templates(self) -> None:
        cases = {
            "문항01": ("statistics", "answer_text=11 명"),
            "문항02": ("statistics", "answer_text=방과 후 활동별 학생 수"),
            "문항03": ("statistics", "answer_text=그림 그리기, 바둑, 수영, 종이접기"),
            "문항04": ("statistics", "answer_text=막대그래프"),
            "문항05": ("statistics", "answer_text=20 분"),
            "문항06": (
                "statistics",
                "answer_text=3학년 30 명, 4학년 40 명, 5학년 45 명, 6학년 60 명, 합계 175 명",
            ),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_5단원_막대그래프_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_fraction_add_sub_round1_page1_templates(self) -> None:
        cases = {
            "문항01": ("fraction_ratio", "answer_text=(1) 4 1/4, (2) 2/5"),
            "문항02": ("fraction_ratio", "answer_text=19/23"),
            "문항03": ("fraction_ratio", "answer_text=3 4/6, 5 3/6"),
            "문항04": ("fraction_ratio", "answer_text=3/20"),
            "문항05": ("fraction_ratio", "answer_text=4, 8, 3"),
            "문항06": ("fraction_ratio", "answer_text=1 3/7"),
            "문항07": ("fraction_ratio", "answer_text=1 2/9 m"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_1단원_분수의덧셈과뺄셈_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_fraction_add_sub_round1_page2_templates(self) -> None:
        cases = {
            "문항01": ("measurement", "answer_text=2 2/13 m"),
            "문항02": ("fraction_ratio", "answer_text=7/9"),
            "문항03": ("fraction_ratio", "answer_text=승희, 3/15"),
            "문항04": ("fraction_ratio", "answer_text=㉠ 11/13, ㉡ 8/13"),
            "문항05": ("fraction_ratio", "answer_text=4/11"),
            "문항06": ("fraction_ratio", "answer_text=180 조각"),
            "문항07": ("fraction_ratio", "answer_text=<"),
            "문항08": ("fraction_ratio", "answer_text=32"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_1단원_분수의덧셈과뺄셈_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_fraction_add_sub_round1_page3_templates(self) -> None:
        cases = {
            "문항01": ("measurement", "answer_text=4 2/6 m"),
            "문항02": ("measurement", "answer_text=2 11/17 kg"),
            "문항03": ("measurement", "answer_text=14 5/7 L"),
            "문항04": ("measurement", "answer_text=48 4/7 cm"),
            "문항05": ("measurement", "answer_text=수지, 4/5 m"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_1단원_분수의덧셈과뺄셈_1회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_fraction_add_sub_round2_page1_templates(self) -> None:
        cases = {
            "문항01": ("fraction_ratio", "answer_text=>"),
            "문항02": ("fraction_ratio", "answer_text=1 1/3"),
            "문항03": ("fraction_ratio", "answer_text=4/7"),
            "문항04": ("fraction_ratio", "answer_text=1 2/7"),
            "문항05": ("fraction_ratio", "answer_text=105 쪽"),
            "문항06": ("measurement", "answer_text=2 1/6 m"),
            "문항07": ("fraction_ratio", "answer_text=9/11"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_1단원_분수의덧셈과뺄셈_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_fraction_add_sub_round2_page2_templates(self) -> None:
        cases = {
            "문항01": ("fraction_ratio", "answer_text=딸기, 1/12 kg"),
            "문항02": ("fraction_ratio", "answer_text=14/15, 7/15"),
            "문항03": ("fraction_ratio", "answer_text=나"),
            "문항04": ("fraction_ratio", "answer_text=490 쪽"),
            "문항05": ("fraction_ratio", "answer_text=23/9, 15/9"),
            "문항06": ("measurement", "answer_text=8 1/5 cm"),
            "문항07": ("fraction_ratio", "answer_text=식: 2 9/13+2 7/13, 답: 5 3/13"),
            "문항08": ("fraction_ratio", "answer_text=3 2/9"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_1단원_분수의덧셈과뺄셈_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_fraction_add_sub_round2_page3_templates(self) -> None:
        cases = {
            "문항01": ("fraction_ratio", "answer_text=9"),
            "문항02": ("fraction_ratio", "answer_text=7 5/9"),
            "문항03": ("fraction_ratio", "answer_text=8 4/9 kg"),
            "문항04": ("measurement", "answer_text=8 2/7 cm"),
            "문항05": ("measurement", "answer_text=3 3/8 L"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_1단원_분수의덧셈과뺄셈_2회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_fraction_add_sub_round3_page1_templates(self) -> None:
        cases = {
            "문항01": ("fraction_ratio", "answer_text=(1) 6, (2) 2/3"),
            "문항02": ("fraction_ratio", "answer_text=>"),
            "문항03": ("fraction_ratio", "answer_text=3/11"),
            "문항04": ("fraction_ratio", "answer_text=5/7"),
            "문항05": ("fraction_ratio", "answer_text=4 1/8"),
            "문항06": ("fraction_ratio", "answer_text=2 3/6"),
            "문항07": ("fraction_ratio", "answer_text=96 쪽"),
            "문항08": ("measurement", "answer_text=2 6/7 cm"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_1단원_분수의덧셈과뺄셈_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_fraction_add_sub_round3_page2_templates(self) -> None:
        cases = {
            "문항01": ("fraction_ratio", "answer_text=1 1/9"),
            "문항02": ("fraction_ratio", "answer_text=6/20 cm"),
            "문항03": ("fraction_ratio", "answer_text=5 개, 2/20 kg"),
            "문항04": ("fraction_ratio", "answer_text=1 4/9"),
            "문항05": ("fraction_ratio", "answer_text=2 1/11"),
            "문항06": ("fraction_ratio", "answer_text=56 2/8 kg"),
            "문항07": ("fraction_ratio", "answer_text=9 6/7 kg"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_1단원_분수의덧셈과뺄셈_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_fraction_add_sub_round3_page3_templates(self) -> None:
        cases = {
            "문항01": ("measurement", "answer_text=19 2/6 cm"),
            "문항02": ("measurement", "answer_text=4 3/7 km"),
            "문항03": ("fraction_ratio", "answer_text=ㄱ"),
            "문항04": ("measurement", "answer_text=3 5/9 m"),
            "문항05": ("fraction_ratio", "answer_text=3 2/8"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_1단원_분수의덧셈과뺄셈_3회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_triangle_round1_page1_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=④"),
            "문항02": ("geometry", "answer_text=5 cm"),
            "문항03": ("geometry", "answer_text=다, 라, 나, 라, 이등변삼각형, 정삼각형"),
            "문항04": ("geometry", "answer_text=7 cm, 11 cm"),
            "문항05": ("geometry", "answer_text=20"),
            "문항06": ("geometry", "answer_text=18 cm"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_2단원_삼각형_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_triangle_round1_page2_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=24 cm"),
            "문항02": ("geometry", "answer_text=15 cm"),
            "문항03": ("geometry", "answer_text=직, 예, 둔"),
            "문항04": ("geometry", "answer_text=13 개"),
            "문항05": ("geometry", "answer_text=30°"),
            "문항06": ("geometry", "answer_text=87 cm"),
            "문항07": ("geometry", "answer_text=108°"),
            "문항08": ("geometry", "answer_text=4 개"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_2단원_삼각형_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_triangle_round1_page3_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=④"),
            "문항02": ("geometry", "answer_text=⑤"),
            "문항03": ("geometry", "answer_text=4 개"),
            "문항04": ("geometry", "answer_text=바"),
            "문항05": ("geometry", "answer_text=80°"),
            "문항06": ("geometry", "answer_text=110°"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_2단원_삼각형_1회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_triangle_round2_page1_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=8 cm"),
            "문항02": ("geometry", "answer_text=38 cm"),
            "문항03": ("geometry", "answer_text=다"),
            "문항04": ("geometry", "answer_text=8 개"),
            "문항05": ("geometry", "answer_text=15 cm"),
            "문항06": ("geometry", "answer_text=14 cm"),
            "문항07": ("geometry", "answer_text=20 cm"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_2단원_삼각형_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_triangle_round2_page2_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=10 cm"),
            "문항02": ("geometry", "answer_text=㉠: 80°, ㉡: 140°"),
            "문항03": ("geometry", "answer_text=240°"),
            "문항04": ("geometry", "answer_text=80°"),
            "문항05": ("geometry", "answer_text=2 개"),
            "문항06": ("geometry", "answer_text=㉠ 1 개, ㉡ 3 개"),
            "문항07": ("geometry", "answer_text=둔각삼각형"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_2단원_삼각형_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_triangle_round2_page3_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=가, 다"),
            "문항02": ("geometry", "answer_text=1 개"),
            "문항03": ("geometry", "answer_text=2 개"),
            "문항04": ("geometry", "answer_text=④"),
            "문항05": ("geometry", "answer_text=15°"),
            "문항06": ("geometry", "answer_text=15°"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_2단원_삼각형_2회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_triangle_round3_page1_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=33 cm"),
            "문항02": ("geometry", "answer_text=48 cm"),
            "문항03": ("geometry", "answer_text=라"),
            "문항04": ("geometry", "answer_text=12 cm"),
            "문항05": ("geometry", "answer_text=80°"),
            "문항06": ("geometry", "answer_text=12 cm"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_2단원_삼각형_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_triangle_round3_page2_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=15°"),
            "문항02": ("geometry", "answer_text=⑤"),
            "문항03": ("geometry", "answer_text=100°"),
            "문항04": ("geometry", "answer_text=70°"),
            "문항05": ("geometry", "answer_text=㉠ 3, ㉡ 1"),
            "문항06": ("geometry", "answer_text=7 개"),
            "문항07": ("geometry", "answer_text=라, 마, 나 / 가, 다, 바"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_2단원_삼각형_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_triangle_round3_page3_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=①, ②, ③"),
            "문항02": ("geometry", "answer_text=3 개"),
            "문항03": ("geometry", "answer_text=2 개"),
            "문항04": ("geometry", "answer_text=예각삼각형"),
            "문항05": ("geometry", "answer_text=70°, 70°"),
            "문항06": ("geometry", "answer_text=30°"),
            "문항07": ("geometry", "answer_text=120°"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_2단원_삼각형_3회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_decimal_add_sub_round1_page1_templates(self) -> None:
        cases = {
            "문항01": ("fraction_ratio", "answer_text=48/100, 0.48"),
            "문항02": ("fraction_ratio", "answer_text=0.035, 영점영삼오"),
            "문항03": ("fraction_ratio", "answer_text=소수 둘째, 0.07"),
            "문항04": ("fraction_ratio", "answer_text=7, 0.07"),
            "문항05": ("fraction_ratio", "answer_text=6, 0.6, 0.06, 0.006"),
            "문항06": (
                "fraction_ratio",
                "answer_text=0.03, 0.3, 3, 30, 300 / 0.002, 0.02, 0.2, 2, 20",
            ),
            "문항07": ("fraction_ratio", "answer_text=20.62"),
            "문항08": ("fraction_ratio", "answer_text=100 배"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_3단원_소수의덧셈과뺄셈_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_decimal_add_sub_round1_page2_templates(self) -> None:
        cases = {
            "문항01": ("measurement", "answer_text=③"),
            "문항02": ("fraction_ratio", "answer_text=1.06"),
            "문항03": ("fraction_ratio", "answer_text=2.5"),
            "문항04": ("fraction_ratio", "answer_text=7.11, 9.35"),
            "문항05": ("measurement", "answer_text=2.73, 0.57, 3.3"),
            "문항06": ("measurement", "answer_text=1.05 L"),
            "문항07": ("fraction_ratio", "answer_text=ㄴ, ㄹ, ㄱ, ㄷ"),
            "문항08": ("fraction_ratio", "answer_text=0.35"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_3단원_소수의덧셈과뺄셈_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_decimal_add_sub_round1_page3_templates(self) -> None:
        cases = {
            "문항01": ("fraction_ratio", "answer_text=10.09"),
            "문항02": ("measurement", "answer_text=54.73 cm"),
            "문항03": ("fraction_ratio", "answer_text=1.38"),
            "문항04": ("measurement", "answer_text=재희, 0.26 kg"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_3단원_소수의덧셈과뺄셈_1회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_decimal_add_sub_round2_page1_templates(self) -> None:
        cases = {
            "문항01": ("fraction_ratio", "answer_text=74/100, 0.74"),
            "문항02": ("fraction_ratio", "answer_text=0.4, 0.04"),
            "문항03": ("fraction_ratio", "answer_text=7, 0.7, 0.07, 0.007"),
            "문항04": ("fraction_ratio", "answer_text=0.007"),
            "문항05": ("fraction_ratio", "answer_text=4.35"),
            "문항06": ("fraction_ratio", "answer_text=①"),
            "문항07": ("fraction_ratio", "answer_text=1000 배"),
            "문항08": ("fraction_ratio", "answer_text=0.837"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_3단원_소수의덧셈과뺄셈_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_decimal_add_sub_round2_page2_templates(self) -> None:
        cases = {
            "문항01": ("measurement", "answer_text=③"),
            "문항02": ("fraction_ratio", "answer_text=8, 8, 1"),
            "문항03": ("fraction_ratio", "answer_text=9.15"),
            "문항04": ("fraction_ratio", "answer_text=다, 라, 가, 나"),
            "문항05": ("measurement", "answer_text=5.91 km"),
            "문항06": ("fraction_ratio", "answer_text=="),
            "문항07": ("fraction_ratio", "answer_text=13.2"),
            "문항08": ("fraction_ratio", "answer_text=나"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_3단원_소수의덧셈과뺄셈_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_decimal_add_sub_round2_page3_templates(self) -> None:
        cases = {
            "문항01": ("measurement", "answer_text=한라봉, 2.06 kg"),
            "문항02": ("measurement", "answer_text=1.76 L"),
            "문항03": ("fraction_ratio", "answer_text=3.1"),
            "문항04": ("fraction_ratio", "answer_text=4.95"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_3단원_소수의덧셈과뺄셈_2회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_decimal_add_sub_round3_page1_templates(self) -> None:
        cases = {
            "문항01": ("fraction_ratio", "answer_text=2.708, 이점칠영팔"),
            "문항02": ("fraction_ratio", "answer_text=소수 셋째, 0.009"),
            "문항03": ("fraction_ratio", "answer_text=24.5, 245"),
            "문항04": (
                "fraction_ratio",
                "answer_text=0.2, 2, 20, 200, 2000 / 0.05, 0.5, 5, 50, 500",
            ),
            "문항05": ("fraction_ratio", "answer_text=218.84"),
            "문항06": ("fraction_ratio", "answer_text=0.98"),
            "문항07": ("fraction_ratio", "answer_text=10000 배"),
            "문항08": ("fraction_ratio", "answer_text=③"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_3단원_소수의덧셈과뺄셈_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_decimal_add_sub_round3_page2_templates(self) -> None:
        cases = {
            "문항01": ("measurement", "answer_text=④"),
            "문항02": ("fraction_ratio", "answer_text=다"),
            "문항03": ("fraction_ratio", "answer_text=5.88"),
            "문항04": ("fraction_ratio", "answer_text=2.17, 1.3"),
            "문항05": ("fraction_ratio", "answer_text=3.4"),
            "문항06": ("measurement", "answer_text=0.7 km"),
            "문항07": ("fraction_ratio", "answer_text=4.5"),
            "문항08": ("measurement", "answer_text=1.27 m"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_3단원_소수의덧셈과뺄셈_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_decimal_add_sub_round3_page3_templates(self) -> None:
        cases = {
            "문항01": ("measurement", "answer_text=0.08 m"),
            "문항02": ("measurement", "answer_text=62.33 g"),
            "문항03": ("fraction_ratio", "answer_text=41.38"),
            "문항04": ("measurement", "answer_text=2.78 L"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_3단원_소수의덧셈과뺄셈_3회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_quadrilateral_round1_page1_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=직선 가"),
            "문항02": ("geometry", "answer_text=③"),
            "문항03": ("geometry", "answer_text=60°"),
            "문항04": ("geometry", "answer_text=123°"),
            "문항05": ("geometry", "answer_text=4 쌍"),
            "문항06": ("geometry", "answer_text=①"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_4단원_사각형_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_quadrilateral_round1_page2_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=5 cm"),
            "문항02": ("geometry", "answer_text=6 cm"),
            "문항03": ("geometry", "answer_text=2 개"),
            "문항04": ("geometry", "answer_text=②, ③, ⑤"),
            "문항05": ("geometry", "answer_text=6 cm"),
            "문항06": ("geometry", "answer_text=사다리꼴"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_4단원_사각형_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_shape_movement_round1_templates(self) -> None:
        cases = {
            "p01_문항01": "answer_text=③ 위치",
            "p01_문항02": "answer_text=④, ⑤",
            "p01_문항03": "answer_text=3번",
            "p01_문항04": "answer_text=오른쪽으로 민 도형",
            "p01_문항05": "answer_text=가",
            "p01_문항06": "answer_text=보기 모양을 오른쪽으로 이어 민 무늬",
            "p01_문항07": "answer_text=왼쪽으로 3칸 민 도형",
            "p01_문항08": "answer_text=51",
            "p02_문항01": "answer_text=아래쪽으로 뒤집은 65",
            "p02_문항02": "answer_text=좌우로 뒤집어 새긴 파도",
            "p02_문항03": "answer_text=8개",
            "p02_문항04": "answer_text=시계 방향으로 180° 돌린 도형",
            "p02_문항05": "answer_text=시계 방향으로 90° 돌린 도형",
            "p02_문항06": "answer_text=③",
            "p02_문항07": "answer_text=오른쪽으로 뒤집은 뒤 시계 방향으로 270° 돌린 아",
            "p03_문항01": "answer_text=②",
            "p03_문항02": "answer_text=⑤",
            "p03_문항03": "answer_text=나",
            "p03_문항04": "answer_text=①, ②, ③, ④",
            "p03_문항05": "answer_text=27",
        }

        for card_ref, expression in cases.items():
            page, card_label = card_ref.split("_")
            with self.subTest(card_ref=card_ref):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_4단원_평면도형의이동_1회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "geometry")
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_shape_movement_round2_templates(self) -> None:
        cases = {
            "p01_문항01": "answer_text=②",
            "p01_문항02": "answer_text=②",
            "p01_문항03": "answer_text=1번",
            "p01_문항04": "answer_text=왼쪽으로 뒤집은 도형",
            "p01_문항05": "answer_text=ㄱ, ㄷ",
            "p01_문항06": "answer_text=보기 모양을 돌려 이어 만든 무늬",
            "p01_문항07": "answer_text=처음과 같은 도형",
            "p02_문항01": "answer_text=위쪽",
            "p02_문항02": "answer_text=3",
            "p02_문항03": "answer_text=③",
            "p02_문항04": "answer_text=4개",
            "p02_문항05": "answer_text=왼쪽으로 7 cm 밀었습니다",
            "p02_문항06": "answer_text=시계 방향으로 90° 돌린 도형",
            "p02_문항07": "answer_text=②",
            "p03_문항01": "answer_text=위쪽으로 뒤집은 뒤 시계 방향으로 90° 돌린 도형",
            "p03_문항02": "answer_text=③",
            "p03_문항03": "answer_text=②",
            "p03_문항04": "answer_text=나",
            "p03_문항05": "answer_text=②, ⑤",
            "p03_문항06": "answer_text=99",
        }

        for card_ref, expression in cases.items():
            page, card_label = card_ref.split("_")
            with self.subTest(card_ref=card_ref):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_4단원_평면도형의이동_2회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "geometry")
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_shape_movement_round3_page1_and_page2_templates(self) -> None:
        cases = {
            "p01_문항01": "answer_text=②",
            "p01_문항02": "answer_text=④",
            "p01_문항03": "answer_text=360°",
            "p01_문항04": "answer_text=오른쪽으로 7 cm, 위쪽으로 1 cm 민 도형",
            "p01_문항05": "answer_text=②, ⑤",
            "p01_문항06": "answer_text=보기 모양을 돌려 이어 만든 무늬",
            "p01_문항07": "answer_text=보기를 시계 방향으로 180° 돌린 처음 도형",
            "p02_문항01": "answer_text=③",
            "p02_문항02": "answer_text=①",
            "p02_문항03": "answer_text=왼쪽으로 뒤집은 도형",
            "p02_문항04": "answer_text=4개",
            "p02_문항05": "answer_text=처음과 같은 도형",
            "p02_문항06": "answer_text=나",
            "p02_문항07": "answer_text=가",
            "p03_문항01": "answer_text=①, ②, ④, ⑥",
            "p03_문항02": "answer_text=84를 같은 규칙으로 움직인 모양",
            "p03_문항03": "answer_text=⑤",
            "p03_문항04": "answer_text=ㄱ",
            "p03_문항05": "answer_text=③",
            "p03_문항06": "answer_text=776",
        }

        for card_ref, expression in cases.items():
            page, card_label = card_ref.split("_")
            with self.subTest(card_ref=card_ref):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-1_4단원_평면도형의이동_3회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "geometry")
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_quadrilateral_round1_page3_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=30 cm"),
            "문항02": ("geometry", "answer_text=①, ③"),
            "문항03": ("geometry", "answer_text=48 cm"),
            "문항04": ("geometry", "answer_text=9 cm"),
            "문항05": ("measurement", "answer_text=13 cm"),
            "문항06": ("geometry", "answer_text=135°"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_4단원_사각형_1회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_quadrilateral_round1_page4_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=36°"),
            "문항02": ("geometry", "answer_text=12 cm"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_4단원_사각형_1회_p04_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_quadrilateral_round2_page1_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=②"),
            "문항02": ("geometry", "answer_text=선분 ㄱㄹ"),
            "문항03": ("geometry", "answer_text=80°"),
            "문항04": ("geometry", "answer_text=④, ⑥"),
            "문항05": ("geometry", "answer_text=③, ⑤, ⑦"),
            "문항06": ("geometry", "answer_text=12 cm"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_4단원_사각형_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_quadrilateral_round2_page2_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=6 cm"),
            "문항02": ("geometry", "answer_text=12 cm"),
            "문항03": ("geometry", "answer_text=사다리꼴"),
            "문항04": ("geometry", "answer_text=12 cm"),
            "문항05": ("geometry", "answer_text=5 개"),
            "문항06": ("geometry", "answer_text=65°"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_4단원_사각형_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_quadrilateral_round2_page3_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=48 cm"),
            "문항02": (
                "geometry",
                "answer_text=평행한 변이 1쌍: 나, 다, 라 / 평행한 변이 2쌍: 가, 마, 바 / 평행사변형: 가, 마, 바",
            ),
            "문항03": ("geometry", "answer_text=68 cm"),
            "문항04": ("geometry", "answer_text=13 cm"),
            "문항05": ("geometry", "answer_text=5 cm"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_4단원_사각형_2회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_quadrilateral_round2_page4_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=④"),
            "문항02": ("geometry", "answer_text=45°"),
            "문항03": ("geometry", "answer_text=직사각형"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_4단원_사각형_2회_p04_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_quadrilateral_round3_page1_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=3 개"),
            "문항02": ("geometry", "answer_text=③"),
            "문항03": ("geometry", "answer_text=40°"),
            "문항04": ("geometry", "answer_text=135°"),
            "문항05": ("geometry", "answer_text=④"),
            "문항06": ("geometry", "answer_text=②, ④, ⑤"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_4단원_사각형_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_quadrilateral_round3_page2_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=6 cm"),
            "문항02": ("geometry", "answer_text=점 ㄹ"),
            "문항03": ("geometry", "answer_text=9 cm"),
            "문항04": ("geometry", "answer_text=①"),
            "문항05": ("geometry", "answer_text=6 개"),
            "문항06": ("geometry", "answer_text=125°"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_4단원_사각형_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_quadrilateral_round3_page3_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=16 cm"),
            "문항02": ("geometry", "answer_text=가, 나"),
            "문항03": ("geometry", "answer_text=32 cm"),
            "문항04": ("geometry", "answer_text=92 cm"),
            "문항05": ("geometry", "answer_text=55°"),
            "문항06": ("geometry", "answer_text=36 cm"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_4단원_사각형_3회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_quadrilateral_round3_page4_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=정사각형"),
            "문항02": ("geometry", "answer_text=70°"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초4-2_4단원_사각형_3회_p04_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade5_diagnostic_round3_page1_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=육천칠백사만"),
            "문항02": ("arithmetic", "answer_text=1000 배"),
            "문항03": ("measurement", "answer_text=>"),
            "문항04": ("arithmetic", "answer_text=1660 개"),
            "문항05": ("arithmetic", "answer_text=㉡, ㉢, ㉣, ㉠"),
            "문항06": ("arithmetic", "answer_text=95"),
            "문항07": ("statistics", "answer_text=20 권"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0005_[무료_PDF]_초5_'수학'_진단평가_[초5]_진단평가_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

        sanitized_template = infer_elementary_visual_template(
            "/tmp/skai_0005__무료_PDF__초5__수학__진단평가_기초학력__초5__진단평가_3회_p01_문항01.png",
        )
        self.assertIsNotNone(sanitized_template)
        assert sanitized_template is not None
        self.assertEqual(sanitized_template.expression, "answer_text=육천칠백사만")

    def test_infers_grade5_diagnostic_round3_page2_templates(self) -> None:
        cases = {
            "문항01": ("statistics", "answer_text=30 kg"),
            "문항02": ("arithmetic", "answer_text=3, 3, 510"),
            "문항03": ("pattern", "answer_text=26 개"),
            "문항04": ("fraction_ratio", "answer_text=6 1/3"),
            "문항05": ("fraction_ratio", "answer_text=1 2/9 m"),
            "문항06": ("geometry", "answer_text=2 개"),
            "문항07": ("arithmetic", "answer_text=0.25"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0005__무료_PDF__초5__수학__진단평가_기초학력__초5__진단평가_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade5_diagnostic_round3_page3_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=9.04"),
            "문항02": ("geometry", "answer_text=직사각형"),
            "문항03": ("geometry", "answer_text=22 cm"),
            "문항04": ("statistics", "answer_text=④"),
            "문항05": ("geometry", "answer_text=26"),
            "문항06": ("geometry", "answer_text=마름모"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0005__무료_PDF__초5__수학__진단평가_기초학력__초5__진단평가_3회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade5_diagnostic_round2_page1_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=70000, 1000, 600, 80, 4"),
            "문항02": ("arithmetic", "answer_text=2165"),
            "문항03": ("measurement", "answer_text=예각, 둔각, 예각"),
            "문항04": ("arithmetic", "answer_text=31440"),
            "문항05": ("arithmetic", "answer_text=③"),
            "문항06": ("geometry", "answer_text=왼쪽으로 뒤집은 도형"),
            "문항07": ("statistics", "answer_text=③"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0006__무료_PDF__초5__수학__진단평가_기초학력__초5__진단평가_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade5_diagnostic_round2_page2_templates(self) -> None:
        cases = {
            "문항01": ("statistics", "answer_text=10 명"),
            "문항02": ("pattern", "answer_text=2000000 - 1222221 = 777779"),
            "문항03": ("pattern", "answer_text=15 개"),
            "문항04": ("fraction_ratio", "answer_text=1 7/8"),
            "문항05": ("fraction_ratio", "answer_text=3/9"),
            "문항06": ("geometry", "answer_text=라"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0006__무료_PDF__초5__수학__진단평가_기초학력__초5__진단평가_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade5_diagnostic_round2_page3_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=㉠"),
            "문항02": ("arithmetic", "answer_text=<"),
            "문항03": ("geometry", "answer_text=4 쌍"),
            "문항04": ("geometry", "answer_text=15 cm"),
            "문항05": ("statistics", "answer_text=③, ④"),
            "문항06": ("geometry", "answer_text=정육각형"),
            "문항07": ("geometry", "answer_text=5 개"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0006__무료_PDF__초5__수학__진단평가_기초학력__초5__진단평가_2회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade5_diagnostic_round1_page1_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=㉡"),
            "문항02": ("arithmetic", "answer_text=㉢"),
            "문항03": ("measurement", "answer_text=㉢"),
            "문항04": ("arithmetic", "answer_text=>"),
            "문항05": ("arithmetic", "answer_text=869"),
            "문항06": ("geometry", "answer_text=오른쪽 7 cm, 위쪽 1 cm 이동한 도형"),
            "문항07": ("statistics", "answer_text=④"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0007__무료_PDF__초5__수학__진단평가_기초학력__초5__진단평가_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade5_diagnostic_round1_page2_templates(self) -> None:
        cases = {
            "문항01": ("statistics", "answer_text=오세아니아"),
            "문항02": ("pattern", "answer_text=1100"),
            "문항03": ("pattern", "answer_text=16 개"),
            "문항04": ("fraction_ratio", "answer_text=4 1/8"),
            "문항05": ("fraction_ratio", "answer_text=2 3/10"),
            "문항06": ("geometry", "answer_text=①"),
            "문항07": ("geometry", "answer_text=18"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0007__무료_PDF__초5__수학__진단평가_기초학력__초5__진단평가_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade5_diagnostic_round1_page3_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=0.82"),
            "문항02": ("arithmetic", "answer_text=1000 배"),
            "문항03": ("geometry", "answer_text=3 개"),
            "문항04": ("geometry", "answer_text=④, ⑤"),
            "문항05": ("statistics", "answer_text=③, ④"),
            "문항06": ("geometry", "answer_text=④"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0007__무료_PDF__초5__수학__진단평가_기초학력__초5__진단평가_1회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade5_natural_mixed_calc_round1_page1_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=53"),
            "문항02": ("arithmetic", "answer_text=5"),
            "문항03": ("arithmetic", "answer_text=4"),
            "문항04": ("arithmetic", "answer_text=22"),
            "문항05": ("arithmetic", "answer_text=70"),
            "문항06": ("arithmetic", "answer_text=<"),
            "문항07": ("arithmetic", "answer_text=민선"),
            "문항08": ("arithmetic", "answer_text=빈칸: 6, 30"),
            "문항09": ("arithmetic", "answer_text=②, ④"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초5-1_1단원_자연수의혼합계산_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade5_natural_mixed_calc_round1_page2_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=13+8×6-5→56 / (13+8)×6-5→121 / 13+8×(6-5)→21"),
            "문항02": ("arithmetic", "answer_text=나"),
            "문항03": ("arithmetic", "answer_text=31"),
            "문항04": ("arithmetic", "answer_text=168"),
            "문항05": ("arithmetic", "answer_text=(1)-다, (2)-나, (3)-가"),
            "문항06": ("measurement", "answer_text=35 cm"),
            "문항07": ("arithmetic", "answer_text=47"),
            "문항08": ("arithmetic", "answer_text=8"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초5-1_1단원_자연수의혼합계산_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade5_natural_mixed_calc_round1_page3_templates(self) -> None:
        cases = {
            "문항01": ("geometry", "answer_text=③"),
            "문항02": ("arithmetic", "answer_text=①"),
            "문항03": ("measurement", "answer_text=154 cm"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초5-1_1단원_자연수의혼합계산_1회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade6_diagnostic_round3_page1_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=19, 33, 33"),
            "문항02": ("arithmetic", "answer_text=식: (34-21)×5+24 / 답: 89"),
            "문항03": ("arithmetic", "answer_text=1, 3, 5, 15"),
            "문항04": ("arithmetic", "answer_text=7, 539"),
            "문항05": ("sequence", "answer_text=⑤"),
            "문항06": ("fraction_ratio", "answer_text=28/60, 27/60"),
            "문항07": ("fraction_ratio", "answer_text=<"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0002__무료_PDF__초6__수학__진단평가_기초학력__초6__진단평가_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade6_diagnostic_round3_page2_templates(self) -> None:
        cases = {
            "문항01": ("fraction_ratio", "answer_text=2 1/6+2 6/7→5 1/42 / 3 5/14+1 1/3→4 29/42"),
            "문항02": ("fraction_ratio", "answer_text=㉡"),
            "문항03": ("geometry", "answer_text=68 cm²"),
            "문항04": ("arithmetic", "answer_text=6, 24, 16"),
            "문항05": ("arithmetic", "answer_text=㉡"),
            "문항06": ("fraction_ratio", "answer_text=2 3/4"),
            "문항07": ("fraction_ratio", "answer_text=11 11/12"),
            "문항08": ("geometry", "answer_text=왼쪽에서부터 5, 90"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0002__무료_PDF__초6__수학__진단평가_기초학력__초6__진단평가_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade6_diagnostic_round3_page3_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=2.016"),
            "문항02": ("arithmetic", "answer_text=25 개"),
            "문항03": ("geometry", "answer_text=㉣"),
            "문항04": ("geometry", "answer_text=26 개"),
            "문항05": ("statistics", "answer_text=㉡, ㉣"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0002__무료_PDF__초6__수학__진단평가_기초학력__초6__진단평가_3회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade6_diagnostic_round2_page1_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=가"),
            "문항02": ("arithmetic", "answer_text=70÷7-2+5→13 / 70÷7-(2+5)→3 / 70÷(7-2)+5→19"),
            "문항03": ("arithmetic", "answer_text=④"),
            "문항04": ("arithmetic", "answer_text=최소공배수: 70 / 공배수: 70, 140, 210"),
            "문항05": ("pattern", "answer_text=사각형 5개와 삼각형 5개가 이어진 모양"),
            "문항06": ("fraction_ratio", "answer_text=30/48"),
            "문항07": ("fraction_ratio", "answer_text=>"),
            "문항08": ("fraction_ratio", "answer_text=㉠"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0003__무료_PDF__초6__수학__진단평가_기초학력__초6__진단평가_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade6_diagnostic_round2_page2_templates(self) -> None:
        cases = {
            "문항01": ("measurement", "answer_text=4 3/8 m"),
            "문항02": ("geometry", "answer_text=㉢, ㉠, ㉡"),
            "문항03": ("arithmetic", "answer_text=27, 28, 29, 30, 31"),
            "문항04": ("arithmetic", "answer_text=13310"),
            "문항05": ("fraction_ratio", "answer_text=2/9×3/8→1/4×1/3 / 4×7/8→5×7/10"),
            "문항06": ("fraction_ratio", "answer_text=16 1/2"),
            "문항07": ("geometry", "answer_text=40 cm"),
            "문항08": ("arithmetic", "answer_text=10000배"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0003__무료_PDF__초6__수학__진단평가_기초학력__초6__진단평가_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade6_diagnostic_round2_page3_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=39.33"),
            "문항02": ("geometry", "answer_text=64 cm"),
            "문항03": ("geometry", "answer_text=③"),
            "문항04": ("statistics", "answer_text=88회"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0003__무료_PDF__초6__수학__진단평가_기초학력__초6__진단평가_2회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade6_diagnostic_round1_page1_templates(self) -> None:
        cases = {
            "문항01": ("arithmetic", "answer_text=31"),
            "문항02": ("arithmetic", "answer_text=⑤"),
            "문항03": ("arithmetic", "answer_text=배수, 약수"),
            "문항04": ("arithmetic", "answer_text=252"),
            "문항05": ("pattern", "answer_text=사각형 4개와 원 8개가 이어진 모양"),
            "문항06": ("fraction_ratio", "answer_text=8, 15, 16"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0004__무료_PDF__초6__수학__진단평가_기초학력__초6__진단평가_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade6_diagnostic_round1_page2_templates(self) -> None:
        cases = {
            "문항01": ("fraction_ratio", "answer_text=(1) 18/24, 20/24 / (2) 9/12, 10/12"),
            "문항02": ("fraction_ratio", "answer_text=8/45"),
            "문항03": ("measurement", "answer_text=46/63 kg"),
            "문항04": ("measurement", "answer_text=㉡"),
            "문항05": ("arithmetic", "answer_text=44, 32.7, 40, 35"),
            "문항06": ("arithmetic", "answer_text=5200, 5100, 5200"),
            "문항07": ("fraction_ratio", "answer_text=5 5/8"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0004__무료_PDF__초6__수학__진단평가_기초학력__초6__진단평가_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade6_diagnostic_round1_page3_templates(self) -> None:
        cases = {
            "문항01": ("measurement", "answer_text=12 kg"),
            "문항02": ("geometry", "answer_text=5 cm"),
            "문항03": ("arithmetic", "answer_text=0.3×0.27→0.081 / 0.76×0.35→0.266"),
            "문항04": ("arithmetic", "answer_text=<"),
            "문항05": ("geometry", "answer_text=가, 다, 라"),
            "문항06": ("geometry", "answer_text=③"),
            "문항07": ("statistics", "answer_text=6회"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0004__무료_PDF__초6__수학__진단평가_기초학력__초6__진단평가_1회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_diagnostic_round3_page2_templates(self) -> None:
        cases = {
            "문항01": ("measurement", "answer_text=3274 m"),
            "문항02": ("fraction_ratio", "answer_text=5, 3, 2"),
            "문항03": ("measurement", "answer_text=28 cm"),
            "문항04": ("arithmetic", "answer_text=1593"),
            "문항05": ("arithmetic", "answer_text=7 에 ○표"),
            "문항06": ("arithmetic", "answer_text=28"),
            "문항07": ("geometry", "answer_text=④"),
            "문항08": ("geometry", "answer_text=5 cm"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0008__무료_PDF__초4__수학__진단평가_기초학력_진단평가__연습용문제__3회__초4__진단평가_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade4_diagnostic_round3_page3_templates(self) -> None:
        cases = {
            "문항01": ("fraction_ratio", "answer_text=㉠ 20, ㉡ 7"),
            "문항02": ("fraction_ratio", "answer_text=6 2/7 ↔ 44/7, 46/7 ↔ 6 4/7, 7 1/7 ↔ 50/7"),
            "문항03": ("measurement", "answer_text=①, ④"),
            "문항04": ("measurement", "answer_text=나"),
            "문항05": ("statistics", "answer_text=소설책 230, 유아 서적 340, 학습지 160, 잡지 250, 합계 980"),
        }

        for card_label, (topic, expression) in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0008__무료_PDF__초4__수학__진단평가_기초학력_진단평가__연습용문제__3회__초4__진단평가_3회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_diagnostic_round2_page1_templates(self) -> None:
        cases = {
            "문항01": "answer=40",
            "문항02": "answer=925",
            "문항03": "answer_text=원",
            "문항04": "answer_text=56, 38",
            "문항05": "answer_text=81, 18",
            "문항06": "answer_text=3뼘",
            "문항07": "answer_text=세 번째에 ○표",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0012__무료_PDF__초3__수학__진단평가_기초학력_진단평가__연습용문제__2회__초3__진단평가_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_diagnostic_round2_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=연예인, 3",
            "문항02": "answer_text=6, 18",
            "문항03": "answer_text=㉢",
            "문항04": "answer_text=팔천칠백삼십사",
            "문항05": "answer=7928",
            "문항06": "answer_text=⑤",
            "문항07": "answer=6",
            "문항08": "answer=10",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0012__무료_PDF__초3__수학__진단평가_기초학력_진단평가__연습용문제__2회__초3__진단평가_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_diagnostic_round2_page3_templates(self) -> None:
        cases = {
            "문항01": "answer_text=500, 7",
            "문항02": "answer_text=5 시 35 분",
            "문항03": "answer_text=8 시 55 분",
            "문항04": "answer_text=3, 2, 3, 4, 12",
            "문항05": "answer_text=7개",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0012__무료_PDF__초3__수학__진단평가_기초학력_진단평가__연습용문제__2회__초3__진단평가_2회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_diagnostic_round1_page1_templates(self) -> None:
        cases = {
            "문항01": "answer=702",
            "문항02": "answer=871",
            "문항03": "answer_text=2개",
            "문항04": "answer_text=61, 45",
            "문항05": "answer_text==",
            "문항06": "answer_text=5번",
            "문항07": "answer_text=3 cm",
            "문항08": "answer_text=4개",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0013__무료_PDF__초3__수학__진단평가_기초학력_진단평가__연습용문제__1회__초3__진단평가_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_diagnostic_round1_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=9, 27",
            "문항02": "answer_text=㉡, ㉢, ㉠",
            "문항03": "answer=443",
            "문항04": "answer_text=오른쪽에 ○표",
            "문항05": "answer=1",
            "문항06": "answer_text=곱셈표 완성",
            "문항07": "answer=500",
            "문항08": "answer_text=3 m 35 cm",
            "문항09": "answer_text=4 시 50 분",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0013__무료_PDF__초3__수학__진단평가_기초학력_진단평가__연습용문제__1회__초3__진단평가_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_diagnostic_round1_page3_templates(self) -> None:
        cases = {
            "문항01": "answer_text=10 시 35 분",
            "문항02": "answer_text=8일",
            "문항03": "answer_text=초록색 삼각형",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/skai_0013__무료_PDF__초3__수학__진단평가_기초학력_진단평가__연습용문제__1회__초3__진단평가_1회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_add_sub_round1_page1_templates(self) -> None:
        cases = {
            "문항01": "answer=623",
            "문항02": "answer=183",
            "문항03": "answer=1253",
            "문항04": "answer=378",
            "문항05": "answer=1401",
            "문항06": "answer_text=㉠ 7, ㉡ 9",
            "문항07": "answer=1474",
            "문항08": "answer_text=㉠ 437, ㉡ 783",
            "문항09": "answer_text=㉠ 466, ㉡ 1115, ㉢ 910, ㉣ 671",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_1단원_덧셈과뺄셈_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_plane_shapes_round2_page1_review_templates(self) -> None:
        cases = {
            "문항01": "answer_text=직선 ㄷㄹ",
            "문항02": "answer_text=5개",
            "문항03": "answer_text=ㄴ",
            "문항04": "answer_text=직선 ㄷㄹ",
            "문항05": "answer_text=15개",
            "문항06": "answer_text=첫째, 셋째",
            "문항07": "answer_text=3개",
            "문항08": "answer_text=변, 꼭짓점",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_2단원_평면도형_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "geometry")
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_plane_shapes_round2_page2_and_page3_templates(self) -> None:
        cases = {
            "p02_문항01": "answer_text=10개",
            "p02_문항02": "answer_text=3개",
            "p02_문항03": "answer_text=③",
            "p02_문항04": "answer_text=8개",
            "p02_문항05": "answer_text=④",
            "p02_문항06": "answer_text=직각삼각형",
            "p02_문항07": "answer_text=③",
            "p02_문항08": "answer_text=4개",
            "p03_문항01": "answer_text=①, ④, ⑤",
            "p03_문항02": "answer_text=26 cm",
            "p03_문항03": "answer_text=④, ⑤",
            "p03_문항04": "answer_text=3개",
        }

        for card_ref, expression in cases.items():
            page, card_label = card_ref.split("_")
            with self.subTest(card_ref=card_ref):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_2단원_평면도형_2회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "geometry")
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_plane_shapes_round3_templates(self) -> None:
        cases = {
            "p01_문항01": "answer_text=선분 ㄷㄹ",
            "p01_문항02": "answer_text=0개",
            "p01_문항03": "answer_text=ㄴ",
            "p01_문항04": "answer_text=반직선 ㄷㄹ",
            "p01_문항05": "answer_text=5개",
            "p01_문항06": "answer_text=셋째",
            "p01_문항07": "answer_text=6개",
            "p01_문항08": "answer_text=각 ㅁㅂㅅ",
            "p03_문항01": "answer_text=ㄴ",
            "p03_문항02": "answer_text=12 cm",
            "p03_문항03": "answer_text=②, ④",
            "p03_문항04": "answer_text=8개",
        }

        for card_ref, expression in cases.items():
            page, card_label = card_ref.split("_")
            with self.subTest(card_ref=card_ref):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_2단원_평면도형_3회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "geometry")
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_plane_shapes_round1_templates(self) -> None:
        cases = {
            "p01_문항01": "answer_text=2 개",
            "p01_문항02": "answer_text=6 개",
            "p01_문항03": "answer_text=6 개",
            "p01_문항04": "answer_text=㉠ 변, ㉡ 꼭짓점, ㉢ 변",
            "p01_문항05": "answer_text=⑴ ○ ⑵ × ⑶ × ⑷ ○",
            "p01_문항06": "answer_text=⑴ ○ ⑵ × ⑶ × ⑷ ○",
            "p02_문항01": "answer_text=10 개",
            "p02_문항02": "answer_text=다",
            "p02_문항03": "answer_text=9 시",
            "p02_문항04": "answer_text=9 시",
            "p02_문항05": "answer_text=②",
            "p02_문항06": "answer_text=직각삼각형",
            "p02_문항07": "answer_text=3 개",
            "p02_문항08": "answer_text=3 개",
            "p03_문항01": "answer_text=직각",
            "p03_문항02": "answer_text=10 개",
            "p03_문항03": "answer_text=다",
            "p03_문항04": "answer_text=다",
            "p03_문항05": "answer_text=15 cm",
            "p03_문항06": "answer_text=13 cm",
        }

        for card_ref, expression in cases.items():
            page, card_label = card_ref.split("_")
            with self.subTest(card_ref=card_ref):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_2단원_평면도형_1회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "geometry")
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_multiplication_round1_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=120, 240, 360",
            "문항02": "answer=6",
            "문항03": "answer_text=⑤",
            "문항04": "answer_text=㉠ 24, ㉡ 48",
            "문항05": "answer_text=>",
            "문항06": "answer_text=㉠ 2, ㉡ 9",
            "문항07": "answer_text=㉠ 106, ㉡ 128, ㉢ 144",
            "문항08": "answer=30",
            "문항09": "answer_text=㉠ 84, ㉡ 144, ㉢ 56, ㉣ 216",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_4단원_곱셈_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_multiplication_round1_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=(1) 300, (2) 256",
            "문항02": "answer_text=가, 다, 나, 라",
            "문항03": "answer_text=76 cm",
            "문항04": "answer=12",
            "문항05": "answer_text=94 개",
            "문항06": "answer_text=90 분",
            "문항07": "answer_text=106 개",
            "문항08": "answer_text=189 쪽",
            "문항09": "answer_text=6 상자",
            "문항10": "answer=96",
            "문항11": "answer_text=38 개",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_4단원_곱셈_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_multiplication_round2_page1_templates(self) -> None:
        cases = {
            "문항01": "answer=240",
            "문항02": "answer=84",
            "문항03": "answer=188",
            "문항04": "answer_text=26×3-78, 14×6-84, 38×2-76",
            "문항05": "answer_text=가운데 식에 ○표",
            "문항06": "answer=126",
            "문항07": "answer=261",
            "문항08": "answer=138",
            "문항09": "answer=440",
            "문항10": "answer_text=오른쪽 식에 ○표",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_4단원_곱셈_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_multiplication_round2_page2_templates(self) -> None:
        cases = {
            "문항01": "answer=8",
            "문항02": "answer_text=9 자루",
            "문항03": "answer_text=84 명",
            "문항04": "answer_text=185 쪽",
            "문항05": "answer_text=74 세",
            "문항06": "answer_text=132 cm",
            "문항07": "answer_text=66 개",
            "문항08": "answer_text=131 개",
            "문항09": "answer_text=140 자루",
            "문항10": "answer_text=3 cm",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_4단원_곱셈_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_multiplication_round3_page1_templates(self) -> None:
        cases = {
            "문항01": "answer=400",
            "문항02": "answer=99",
            "문항03": "answer=146",
            "문항04": "answer_text=28×2-56, 16×5-80, 18×4-72",
            "문항05": "answer_text=오른쪽 식에 ○표",
            "문항06": "answer=168",
            "문항07": "answer=234",
            "문항08": "answer=265",
            "문항09": "answer=44",
            "문항10": "answer_text=가운데 식에 ○표",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_4단원_곱셈_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_multiplication_round3_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=가운데 식에 ○표",
            "문항02": "answer=6",
            "문항03": "answer_text=28 자루",
            "문항04": "answer_text=75 권",
            "문항05": "answer_text=450 마리",
            "문항06": "answer_text=90 개",
            "문항07": "answer_text=84 cm",
            "문항08": "answer_text=95 개",
            "문항09": "answer_text=136 점",
            "문항10": "answer_text=483 개",
            "문항11": "answer_text=9 cm",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_4단원_곱셈_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_length_time_round1_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=8, 2",
            "문항02": "answer=160",
            "문항03": "answer_text=mm, cm",
            "문항04": "answer_text=6km400m-6400m, 6km40m-6040m, 6km4m-6004m",
            "문항05": "answer_text=㉠ 15 cm 6 mm, ㉡ 156 mm",
            "문항06": "answer_text=㉠ 13, ㉡ 4, ㉢ 4, ㉣ 3",
            "문항07": "answer_text=14 km 620 m",
            "문항08": "answer_text=㉠ 1, ㉡ 7, ㉢ 3, ㉣ 8",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_5단원_길이와시간_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_length_time_round1_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=나",
            "문항02": "answer_text=6 cm 6 mm",
            "문항03": "answer_text=240, 260",
            "문항04": "answer=25",
            "문항05": "answer_text=8, 16, 23",
            "문항06": "answer_text=>",
            "문항07": "answer_text=8 시간 24 분 22 초",
            "문항08": "answer_text=3 시 9 분 52 초",
            "문항09": "answer_text=10 cm 7 mm",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_5단원_길이와시간_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_length_time_round1_page3_templates(self) -> None:
        cases = {
            "문항01": "answer_text=3800 m",
            "문항02": "answer_text=5 시 30 분 1 초",
            "문항03": "answer_text=3 시간 31 분 38 초",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_5단원_길이와시간_1회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_length_time_round2_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=③",
            "문항02": "answer_text=6, 7",
            "문항03": "answer_text=9, 22, 56",
            "문항04": "answer_text=10 mm",
            "문항05": "answer_text=2600 m",
            "문항06": "answer_text=④",
            "문항07": "answer=79",
            "문항08": "answer=630",
            "문항09": "answer_text=③",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_5단원_길이와시간_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_length_time_round2_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=28 km 142 m",
            "문항02": "answer_text=②",
            "문항03": "answer_text=㉠, ㉣",
            "문항04": "answer_text=6 시간 16 분 13 초",
            "문항05": "answer_text=82 mm",
            "문항06": "answer_text=1200 m",
            "문항07": "answer_text=12 시 35 분 47 초",
            "문항08": "answer_text=27 초",
            "문항09": "answer_text=3185 m",
            "문항10": "answer_text=오후 5 시 25 분",
            "문항11": "answer_text=9 mm",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_5단원_길이와시간_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_length_time_round3_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=②",
            "문항02": "answer=4",
            "문항03": "answer_text=12, 53, 28",
            "문항04": "answer_text=10 cm",
            "문항05": "answer_text=4800 m",
            "문항06": "answer_text=②",
            "문항07": "answer=253",
            "문항08": "answer=935",
            "문항09": "answer_text=②",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_5단원_길이와시간_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_length_time_round3_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=13 km 400 m",
            "문항02": "answer_text=⑤",
            "문항03": "answer_text=㉡, ㉣",
            "문항04": "answer_text=5 시 55 분",
            "문항05": "answer_text=214 mm",
            "문항06": "answer_text=2800 m",
            "문항07": "answer_text=4 시 55 분 47 초",
            "문항08": "answer_text=오후 3 시 58 분 25 초",
            "문항09": "answer_text=2195 m",
            "문항10": "answer_text=오후 9 시",
            "문항11": "answer_text=60 mm",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_5단원_길이와시간_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_fraction_decimal_round1_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=⑴ 3 ⑵ 8",
            "문항02": "answer_text=⑴ 0.2, 영점 이 ⑵ 0.7, 영점 칠 ⑶ 0.3, 영점 삼",
            "문항03": "answer_text=⑴ 2 ⑵ 4 ⑶ 5",
            "문항04": "answer_text=28, 25, 2.8",
            "문항05": "answer_text=4 배",
            "문항06": "answer_text=다",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_6단원_분수와소수_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_fraction_decimal_round1_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=분수: 4/10, 소수: 0.4",
            "문항02": "answer_text=3/4, 사분의 삼",
            "문항03": "answer=2",
            "문항04": "answer_text=⑴ 4/10 ⑵ 0.4",
            "문항05": "answer_text=1/6, 1/2, 1/4",
            "문항06": "answer_text=1/9",
            "문항07": "answer_text=7/10, 0.5",
            "문항08": "answer_text=4/5, 4/7, 4/9",
            "문항09": "answer_text=⑴ 0.8 ⑵ 7",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_6단원_분수와소수_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_fraction_decimal_round1_page3_templates(self) -> None:
        cases = {
            "문항01": "answer_text=2.7 컵",
            "문항02": "answer_text=1/6",
            "문항03": "answer_text=18.8 cm",
            "문항04": "answer_text=희수, 2.8 cm",
            "문항05": "answer_text=0.7",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_6단원_분수와소수_1회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_fraction_decimal_round2_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=②, ⑤",
            "문항02": "answer=4",
            "문항03": "answer_text=4/6",
            "문항04": "answer_text=3.4",
            "문항05": "answer_text=4 배",
            "문항06": "answer_text=③",
            "문항07": "answer_text=1/14",
            "문항08": "answer_text=18 cm",
            "문항09": "answer_text=3/6 m",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_6단원_분수와소수_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_fraction_decimal_round2_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=3, 5, 4",
            "문항02": "answer_text=1/11",
            "문항03": "answer_text=2/10",
            "문항04": "answer_text=>",
            "문항05": "answer_text=1/8",
            "문항06": "answer_text=1",
            "문항07": "answer_text=8.4 cm",
            "문항08": "answer_text=132.8 cm",
            "문항09": "answer_text=6 개",
            "문항10": "answer_text=5/9",
            "문항11": "answer_text=30 바퀴",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_6단원_분수와소수_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_fraction_decimal_round3_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=③, ④",
            "문항02": "answer=5",
            "문항03": "answer_text=2/5",
            "문항04": "answer_text=2.5",
            "문항05": "answer_text=3 배",
            "문항06": "answer_text=②",
            "문항07": "answer_text=1/7",
            "문항08": "answer_text=14 cm",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_6단원_분수와소수_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_fraction_decimal_round3_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=5 배",
            "문항02": "answer=10",
            "문항03": "answer_text=8/10",
            "문항04": "answer_text=1/5",
            "문항05": "answer_text=>",
            "문항06": "answer_text=7/9",
            "문항07": "answer_text=9/10",
            "문항08": "answer_text=1.4 cm",
            "문항09": "answer_text=6.5 cm",
            "문항10": "answer_text=3 개",
            "문항11": "answer_text=5/11",
            "문항12": "answer_text=0.6 m",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_6단원_분수와소수_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_multiplication_round1_page1_templates(self) -> None:
        cases = {
            "문항01": "answer=76",
            "문항02": "answer_text=(1)-③, (2)-①",
            "문항03": "answer_text=600, 1800",
            "문항04": "answer_text=③",
            "문항05": "answer_text=844 cm",
            "문항06": "answer_text=4, 4",
            "문항07": "answer_text=⑴ 1216 ⑵ 1241",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_1단원_곱셈_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_multiplication_round1_page2_templates(self) -> None:
        cases = {
            "문항01": "answer=5040",
            "문항02": "answer_text=다, 나, 가",
            "문항03": "answer=1026",
            "문항04": "answer=768",
            "문항05": "answer_text=1754 cm",
            "문항06": "answer_text=인영, 100 번",
            "문항07": "answer=734",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_1단원_곱셈_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_multiplication_round1_page3_templates(self) -> None:
        cases = {
            "문항01": "answer_text=2700 번",
            "문항02": "answer_text=1000 개",
            "문항03": "answer_text=395 m",
            "문항04": "answer_text=1392 개",
            "문항05": "answer_text=164 개",
            "문항06": "answer=3510",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_1단원_곱셈_1회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_multiplication_round2_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=가",
            "문항02": "answer_text=④",
            "문항03": "answer_text=(1)-나, (2)-다, (3)-가",
            "문항04": "answer=406",
            "문항05": "answer_text=488 개",
            "문항06": "answer_text=2, 0, 8",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_1단원_곱셈_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_multiplication_round2_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=⑴ 1075 ⑵ 3496",
            "문항02": "answer=243",
            "문항03": "answer_text=5, 120, 1200",
            "문항04": "answer_text=⑴ < ⑵ >",
            "문항05": "answer_text=1750 개",
            "문항06": "answer=2547",
            "문항07": "answer=4",
            "문항08": "answer_text=996 cm",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_1단원_곱셈_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_multiplication_round2_page3_templates(self) -> None:
        cases = {
            "문항01": "answer_text=3600 초",
            "문항02": "answer_text=파란 색종이, 50 장",
            "문항03": "answer_text=9 cm씩 자른 철사, 15 cm",
            "문항04": "answer_text=1176 대",
            "문항05": "answer=672",
            "문항06": "answer=3010",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_1단원_곱셈_2회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_multiplication_round3_page1_templates(self) -> None:
        cases = {
            "문항01": "answer=1800",
            "문항02": "answer_text=나",
            "문항03": "answer_text=(1)-다, (2)-나, (3)-가",
            "문항04": "answer_text=930 원",
            "문항05": "answer_text=1, 2",
            "문항06": "answer=4150",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_1단원_곱셈_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_multiplication_round3_page2_templates(self) -> None:
        cases = {
            "문항01": "answer=2700",
            "문항02": "answer_text=2, 1, 8",
            "문항03": "answer=5",
            "문항04": "answer_text=1456, 208",
            "문항05": "answer=4624",
            "문항06": "answer_text=④, ⑤",
            "문항07": "answer_text=588 m",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_1단원_곱셈_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_multiplication_round3_page3_templates(self) -> None:
        cases = {
            "문항01": "answer=1526",
            "문항02": "answer_text=10 원",
            "문항03": "answer_text=빨간 색종이, 49 장",
            "문항04": "answer_text=216 cm",
            "문항05": "answer_text=1316 쪽",
            "문항06": "answer_text=22 봉지",
            "문항07": "answer_text=175 권",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_1단원_곱셈_3회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_division_round1_page1_templates(self) -> None:
        cases = {
            "문항01": "answer=20",
            "문항02": "answer=14",
            "문항03": "answer_text=가, 나, 다",
            "문항04": "answer_text=10 cm",
            "문항05": "answer_text=①",
            "문항06": "answer_text=1, 3, 7",
            "문항07": "answer_text=나",
            "문항08": "answer_text=①, ③, ⑤",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_2단원_나눗셈_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_division_round1_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=56÷4",
            "문항02": "answer_text=②",
            "문항03": "answer_text=7, 2, 4, 2, 1, 2, 1, 2, 0",
            "문항04": "answer_text=3 개",
            "문항05": "answer_text=14 cm",
            "문항06": "answer_text=21 마리",
            "문항07": "answer_text=10 개",
            "문항08": "answer=4",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_2단원_나눗셈_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_division_round1_page3_templates(self) -> None:
        cases = {
            "문항01": "answer_text=몫 21, 나머지 1",
            "문항02": "answer_text=8 봉지, 2 개",
            "문항03": "answer_text=2 개",
            "문항04": "answer_text=15 그루",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_2단원_나눗셈_1회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_division_round2_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=10, 10",
            "문항02": "answer=12",
            "문항03": "answer_text=ㄱ",
            "문항04": "answer=20",
            "문항05": "answer_text=⑤",
            "문항06": "answer_text=3, 5, 6",
            "문항07": "answer_text=나",
            "문항08": "answer_text=3 개",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_2단원_나눗셈_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_division_round2_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=②",
            "문항02": "answer_text=78÷3",
            "문항03": "answer_text=6 개",
            "문항04": "answer_text=(1)-①, (2)-②, (3)-③",
            "문항05": "answer_text=1, 0, 2, 7, 1, 7, 1, 4, 3",
            "문항06": "answer_text=22 cm",
            "문항07": "answer_text=41 마리",
            "문항08": "answer=7",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_2단원_나눗셈_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_division_round2_page3_templates(self) -> None:
        cases = {
            "문항01": "answer_text=5 명, 3 장",
            "문항02": "answer_text=76÷4=19",
            "문항03": "answer_text=1 개",
            "문항04": "answer_text=4 개",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_2단원_나눗셈_2회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_division_round3_page1_templates(self) -> None:
        cases = {
            "문항01": "answer=30",
            "문항02": "answer=13",
            "문항03": "answer=40",
            "문항04": "answer=15",
            "문항05": "answer_text=다, 가, 나",
            "문항06": "answer_text=6",
            "문항07": "answer_text=(1)-②, (2)-①, (3)-③",
            "문항08": "answer_text=2, 6, 4",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_2단원_나눗셈_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_division_round3_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=다",
            "문항02": "answer_text=②, ③, ④",
            "문항03": "answer=95",
            "문항04": "answer_text=20 개",
            "문항05": "answer_text=17 cm",
            "문항06": "answer_text=몫 13, 나머지 5",
            "문항07": "answer_text=13 명, 2 개",
            "문항08": "answer_text=85÷3=28 ... 1",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_2단원_나눗셈_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_division_round3_page3_templates(self) -> None:
        cases = {
            "문항01": "answer_text=26 그루",
            "문항02": "answer_text=1 자루",
            "문항03": "answer=36",
            "문항04": "answer=55",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_2단원_나눗셈_3회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_circle_round1_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=7 cm",
            "문항02": "answer_text=그리기 문제",
            "문항03": "answer_text=㉠",
            "문항04": "answer_text=그리기 문제",
            "문항05": "answer_text=8 cm",
            "문항06": "answer_text=9 cm",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_3단원_원_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_circle_round1_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=다, 가, 나",
            "문항02": "answer_text=③",
            "문항03": "answer_text=6 cm",
            "문항04": "answer_text=6 cm",
            "문항05": "answer_text=3 cm",
            "문항06": "answer_text=28 cm",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_3단원_원_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_circle_round1_page3_templates(self) -> None:
        cases = {
            "문항01": "answer_text=9 cm",
            "문항02": "answer_text=240 cm",
            "문항03": "answer_text=7 cm",
            "문항04": "answer_text=20 cm",
            "문항05": "answer_text=30 cm",
            "문항06": "answer_text=3 cm",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_3단원_원_1회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_circle_round1_page4_templates(self) -> None:
        cases = {
            "문항01": "answer_text=나",
            "문항02": "answer_text=정국",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_3단원_원_1회_p04_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_circle_round2_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=선분 ㄱㅇ, 선분 ㄴㅇ",
            "문항02": "answer_text=반지름 7 cm, 지름 14 cm",
            "문항03": "answer_text=그리기 문제",
            "문항04": "answer_text=㉤",
            "문항05": "answer_text=2 cm",
            "문항06": "answer_text=④",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_3단원_원_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_circle_round2_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=20 mm",
            "문항02": "answer_text=7 cm",
            "문항03": "answer_text=28 cm",
            "문항04": "answer_text=32 cm",
            "문항05": "answer_text=8 cm",
            "문항06": "answer_text=60 cm",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_3단원_원_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_circle_round2_page3_templates(self) -> None:
        cases = {
            "문항01": "answer_text=6 cm",
            "문항02": "answer_text=21 cm",
            "문항03": "answer_text=나",
            "문항04": "answer_text=18 cm",
            "문항05": "answer_text=4 군데",
            "문항06": "answer_text=45 cm",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_3단원_원_2회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_circle_round2_page4_templates(self) -> None:
        cases = {
            "문항01": "answer_text=다",
            "문항02": "answer_text=1, 1",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_3단원_원_2회_p04_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_circle_round3_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=반지름 6 cm, 지름 12 cm",
            "문항02": "answer_text=그리기 문제",
            "문항03": "answer_text=3 cm",
            "문항04": "answer_text=10 cm",
            "문항05": "answer_text=③",
            "문항06": "answer_text=④",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_3단원_원_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_circle_round3_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=20 mm",
            "문항02": "answer_text=6 cm",
            "문항03": "answer_text=11 cm",
            "문항04": "answer_text=15 cm",
            "문항05": "answer_text=6 cm",
            "문항06": "answer_text=18 cm",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_3단원_원_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_circle_round3_page3_templates(self) -> None:
        cases = {
            "문항01": "answer_text=12 cm",
            "문항02": "answer_text=8 cm",
            "문항03": "answer_text=16 cm",
            "문항04": "answer_text=36 cm",
            "문항05": "answer_text=56 cm",
            "문항06": "answer_text=4 개",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_3단원_원_3회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_circle_round3_page4_templates(self) -> None:
        cases = {
            "문항01": "answer_text=㉠",
            "문항02": "answer_text=2, 1",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_3단원_원_3회_p04_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_fraction_round1_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=1/4",
            "문항02": "answer_text=2/6",
            "문항03": "answer_text=4 개",
            "문항04": "answer_text=5/7",
            "문항05": "answer_text=5/16",
            "문항06": "answer_text=8 시간",
            "문항07": "answer_text=4 자루",
            "문항08": "answer_text=<",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_4단원_분수_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_fraction_round1_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=유진",
            "문항02": "answer=15",
            "문항03": "answer_text=18 cm",
            "문항04": "answer_text=6 개",
            "문항05": "answer_text=4 개",
            "문항06": "answer=35",
            "문항07": "answer_text=가",
            "문항08": "answer_text=라",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_4단원_분수_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_fraction_round1_page3_templates(self) -> None:
        cases = {
            "문항01": "answer_text=5 개",
            "문항02": "answer_text=영수",
            "문항03": "answer_text=45 개",
            "문항04": "answer_text=하나, 9 쪽",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_4단원_분수_1회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_fraction_round2_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=1/3",
            "문항02": "answer=8",
            "문항03": "answer=7",
            "문항04": "answer_text=7/9",
            "문항05": "answer_text=2/5",
            "문항06": "answer=31",
            "문항07": "answer_text=5 개",
            "문항08": "answer_text=⑤",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_4단원_분수_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_fraction_round2_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=ㄱ",
            "문항02": "answer_text=40 cm",
            "문항03": "answer_text=3 시간",
            "문항04": "answer_text=7/15",
            "문항05": "answer_text=6 개",
            "문항06": "answer=6",
            "문항07": "answer=157",
            "문항08": "answer=5",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_4단원_분수_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_fraction_round2_page3_templates(self) -> None:
        cases = {
            "문항01": "answer_text=다, 가",
            "문항02": "answer=12",
            "문항03": "answer_text=승민",
            "문항04": "answer_text=시후, 1 권",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_4단원_분수_2회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_fraction_round3_page1_templates(self) -> None:
        cases = {
            "문항01": "answer=12",
            "문항02": "answer_text=(1) 5/8, (2) 11/10",
            "문항03": "answer_text=5/6",
            "문항04": "answer_text=5 개",
            "문항05": "answer_text=2/9",
            "문항06": "answer=2",
            "문항07": "answer_text=④",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_4단원_분수_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_fraction_round3_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=나, 가, 라, 다",
            "문항02": "answer_text=20 명",
            "문항03": "answer=2",
            "문항04": "answer=40",
            "문항05": "answer_text=85 cm",
            "문항06": "answer_text=8 시간",
            "문항07": "answer_text=나",
            "문항08": "answer_text=4 개",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_4단원_분수_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_fraction_round3_page3_templates(self) -> None:
        cases = {
            "문항01": "answer_text=③",
            "문항02": "answer_text=2 4/5 km",
            "문항03": "answer_text=9 개",
            "문항04": "answer_text=세훈, 3 개",
            "문항05": "answer_text=32 cm",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_4단원_분수_3회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_volume_weight_round1_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=(가)",
            "문항02": "answer_text=가, 다, 라, 나",
            "문항03": "answer_text=2 L 900 mL",
            "문항04": "answer_text=(1) >, (2) <",
            "문항05": "answer_text=라, 가, 나, 다",
            "문항06": "answer_text=재민",
            "문항07": "answer_text=가",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_5단원_들이와무게_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "measurement")
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_volume_weight_round1_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=6, 600",
            "문항02": "answer_text=사과 주스, 2 병",
            "문항03": "answer_text=100, 2",
            "문항04": "answer_text=3400 mL",
            "문항05": "answer_text=수박",
            "문항06": "answer_text=350 g",
            "문항07": "answer_text=500 kg",
            "문항08": "answer_text=나",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_5단원_들이와무게_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "measurement")
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_volume_weight_round1_page3_templates(self) -> None:
        cases = {
            "문항01": "answer_text=나",
            "문항02": "answer_text=1000 g",
            "문항03": "answer_text=합: 10 kg 800 g, 차: 4 kg 400 g",
            "문항04": "answer_text=5 kg 300 g",
            "문항05": "answer_text=1 kg 300 g",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_5단원_들이와무게_1회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "measurement")
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_volume_weight_round2_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=다",
            "문항02": "answer_text=④",
            "문항03": "answer_text=①, ④",
            "문항04": "answer_text=다, 가, 라, 나",
            "문항05": "answer_text=오렌지 주스",
            "문항06": "answer_text=(1) 분무기, (2) 종이컵, (3) 욕조",
            "문항07": "answer_text=나",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_5단원_들이와무게_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "measurement")
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_volume_weight_round2_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=9, 700",
            "문항02": "answer_text=5 L 200 mL",
            "문항03": "answer_text=22400 원",
            "문항04": "answer_text=200 mL",
            "문항05": "answer_text=1 L 900 mL",
            "문항06": "answer_text=나, 라, 가, 다",
            "문항07": "answer_text=볼펜, 색연필, 연필",
            "문항08": "answer_text=3650 g",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_5단원_들이와무게_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_volume_weight_round2_page3_templates(self) -> None:
        cases = {
            "문항01": "answer=18007",
            "문항02": "answer_text=④",
            "문항03": "answer_text=63 kg 400 g",
            "문항04": "answer_text=가",
            "문항05": "answer_text=300 g",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_5단원_들이와무게_2회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "measurement")
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_volume_weight_round3_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=나, 가, 다",
            "문항02": "answer_text=3 배",
            "문항03": "answer_text=1 L 600 mL",
            "문항04": "answer_text=⑤",
            "문항05": "answer_text=화요일",
            "문항06": "answer_text=주경",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_5단원_들이와무게_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "measurement")
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_volume_weight_round3_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=8300 mL",
            "문항02": "answer_text=5, 600",
            "문항03": "answer_text=3 L 500 mL",
            "문항04": "answer_text=2 L 600 mL",
            "문항05": "answer_text=다, 나, 가",
            "문항06": "answer_text=5 L 800 mL",
            "문항07": "answer_text=다, 가, 나",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_5단원_들이와무게_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "measurement")
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_volume_weight_round3_page3_templates(self) -> None:
        cases = {
            "문항01": "answer_text=④",
            "문항02": "answer_text=4 kg 750 g",
            "문항03": "answer_text=③, ⑤",
            "문항04": "answer_text=다, 나, 라, 가",
            "문항05": "answer_text==",
            "문항06": "answer_text=13 kg 540 g",
            "문항07": "answer_text=4 kg 500 g",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_5단원_들이와무게_3회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, "measurement")
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_pictograph_round1_templates(self) -> None:
        cases = {
            ("p01", "문항01"): ("statistics", "answer_text=남학생: 수영 3, 태권도 4, 야구 4, 축구 5, 합계 16 / 여학생: 수영 6, 태권도 3, 야구 2, 축구 3, 합계 14"),
            ("p01", "문항02"): ("statistics", "answer_text=사이다"),
            ("p01", "문항03"): ("statistics", "answer_text=43 가구"),
            ("p01", "문항04"): ("statistics", "answer_text=참치 김밥"),
            ("p02", "문항01"): ("statistics", "answer_text=월요일 11, 화요일 34, 수요일 17, 목요일 26, 합계 88"),
            ("p02", "문항02"): ("statistics", "answer_text=8 명"),
            ("p02", "문항03"): ("statistics", "answer_text=220 권"),
            ("p02", "문항04"): ("statistics", "answer_text=210 개"),
            ("p03", "문항01"): ("statistics", "answer_text=가 320, 나 240, 다 300, 라 430, 합계 1290"),
            ("p03", "문항02"): ("statistics", "answer_text=신선 농장: 23 상자, 푸른 농장: 48 상자"),
            ("p03", "문항03"): ("statistics", "answer_text=19 명"),
            ("p03", "문항04"): ("statistics", "answer_text=69 명"),
            ("p04", "문항01"): ("statistics", "answer_text=3 배"),
            ("p04", "문항02"): ("statistics", "answer_text=①, ③"),
            ("p04", "문항03"): ("statistics", "answer_text=1221 권"),
            ("p04", "문항04"): ("statistics", "answer_text=440 명"),
            ("p05", "문항01"): ("statistics", "answer_text=74 권"),
            ("p05", "문항02"): ("statistics", "answer_text=112000 원"),
            ("p05", "문항03"): ("statistics", "answer_text=7월: 18일, 8월: 12일, 9월: 14일, 10월: 8일"),
            ("p05", "문항04"): ("statistics", "answer_text=가 130, 나 250, 다 120, 라 300, 합계 800"),
        }

        for (page, card_label), (topic, expression) in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_6단원_그림그래프_1회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_pictograph_round2_templates(self) -> None:
        cases = {
            ("p01", "문항01"): ("statistics", "answer_text=3 학년"),
            ("p01", "문항02"): ("statistics", "answer_text=26 개"),
            ("p01", "문항03"): ("statistics", "answer_text=소설책 230, 유아 서적 340, 학습지 160, 잡지 250, 합계 980"),
            ("p01", "문항04"): ("statistics", "answer_text=2 반, 1 반, 3 반"),
            ("p02", "문항01"): ("statistics", "answer_text=칼국수 26, 짜장면 62, 비빔밥 44, 합계 132"),
            ("p02", "문항02"): ("statistics", "answer_text=토스트"),
            ("p02", "문항03"): ("statistics", "answer_text=9 대"),
            ("p02", "문항04"): ("statistics", "answer_text=나 마을: 15 명, 라 마을: 24 명"),
            ("p03", "문항01"): ("statistics", "answer_text=유아 서적: 220 권, 학습지: 280 권"),
            ("p03", "문항02"): ("statistics", "answer_text=6 명"),
            ("p03", "문항03"): ("statistics", "answer_text=2 배"),
            ("p03", "문항04"): ("statistics", "answer_text=가, 다"),
            ("p04", "문항01"): ("statistics", "answer_text=식빵, 19 개"),
            ("p04", "문항02"): ("statistics", "answer_text=93 권"),
            ("p04", "문항03"): ("statistics", "answer_text=8 명"),
            ("p04", "문항04"): ("statistics", "answer_text=8400000 원"),
            ("p05", "문항01"): ("statistics", "answer_text=22 명"),
            ("p05", "문항02"): ("statistics", "answer_text=9 월"),
            ("p05", "문항03"): ("statistics", "answer_text=76 개"),
            ("p05", "문항04"): ("statistics", "answer_text=나 마을: 35 그루"),
        }

        for (page, card_label), (topic, expression) in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_6단원_그림그래프_2회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_2_pictograph_round3_templates(self) -> None:
        cases = {
            ("p01", "문항01"): (
                "statistics",
                "answer_text=여학생: 강아지 3, 고양이 5, 앵무새 3, 햄스터 4, 합계 15 / 남학생: 강아지 4, 고양이 4, 앵무새 5, 햄스터 3, 합계 16",
            ),
            ("p01", "문항02"): ("statistics", "answer_text=짜장면"),
            ("p01", "문항03"): ("statistics", "answer_text=연두색"),
            ("p01", "문항04"): ("statistics", "answer_text=1240 대"),
            ("p02", "문항01"): ("statistics", "answer_text=9월 45, 10월 51, 11월 72, 12월 28, 합계 196"),
            ("p02", "문항02"): ("statistics", "answer_text=1340 마리"),
            ("p02", "문항03"): ("statistics", "answer_text=86 명"),
            ("p02", "문항04"): ("statistics", "answer_text=딸기 주스: 38 병, 포도 주스: 40 병"),
            ("p03", "문항01"): ("statistics", "answer_text=가 기계: 35 kg, 라 기계: 48 kg"),
            ("p03", "문항02"): ("statistics", "answer_text=16 명"),
            ("p03", "문항03"): ("statistics", "answer_text=2 배"),
            ("p03", "문항04"): ("statistics", "answer_text=15 명"),
            ("p04", "문항01"): ("statistics", "answer_text=나, 다"),
            ("p04", "문항02"): ("statistics", "answer_text=4 명"),
            ("p04", "문항03"): ("statistics", "answer_text=1142 자루"),
            ("p04", "문항04"): ("statistics", "answer_text=9 명"),
            ("p05", "문항01"): ("statistics", "answer_text=2280000 원"),
            ("p05", "문항02"): ("statistics", "answer_text=23 명"),
            ("p05", "문항03"): ("statistics", "answer_text=비빔밥: 430 그릇, 냉면: 150 그릇"),
            ("p05", "문항04"): ("statistics", "answer_text=가 마을: 150 가구, 다 마을: 130 가구"),
        }

        for (page, card_label), (topic, expression) in cases.items():
            with self.subTest(page=page, card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-2_6단원_그림그래프_3회_{page}_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.topic, topic)
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_add_sub_round1_page2_templates(self) -> None:
        cases = {
            "문항01": "answer=1421",
            "문항02": "answer=186",
            "문항03": "answer_text=합: 1033, 차: 315",
            "문항04": "answer=454",
            "문항05": "answer_text=<",
            "문항06": "answer=457",
            "문항07": "answer_text=813 접시",
            "문항08": "answer=1222",
            "문항09": "answer_text=276 명",
            "문항10": "answer_text=267 m",
            "문항11": "answer_text=153 개",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_1단원_덧셈과뺄셈_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_add_sub_round2_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=887 cm",
            "문항02": "answer=410",
            "문항03": "answer=807",
            "문항04": "answer=253",
            "문항05": "answer=782",
            "문항06": "answer_text=>",
            "문항07": "answer=1012",
            "문항08": "answer=729",
            "문항09": "answer=358",
            "문항10": "answer=655",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_1단원_덧셈과뺄셈_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_add_sub_round2_page2_templates(self) -> None:
        cases = {
            "문항01": "answer=544",
            "문항02": "answer=278",
            "문항03": "answer_text=5, 8",
            "문항04": "answer=745",
            "문항05": "answer_text=㉠, ㉢, ㉡",
            "문항06": "answer_text=920 개",
            "문항07": "answer_text=철희, 63 장",
            "문항08": "answer=454",
            "문항09": "answer_text=연희, 126 m",
            "문항10": "answer=693",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_1단원_덧셈과뺄셈_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_add_sub_round3_page1_templates(self) -> None:
        cases = {
            "문항01": "answer=777",
            "문항02": "answer=322",
            "문항03": "answer=976",
            "문항04": "answer=364",
            "문항05": "answer=792",
            "문항06": "answer_text=>",
            "문항07": "answer=1151",
            "문항08": "answer=387",
            "문항09": "answer=179",
            "문항10": "answer=624",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_1단원_덧셈과뺄셈_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_add_sub_round3_page2_templates(self) -> None:
        cases = {
            "문항01": "answer=457",
            "문항02": "answer=258",
            "문항03": "answer_text=2, 7",
            "문항04": "answer=632",
            "문항05": "answer_text=㉡, ㉢, ㉠",
            "문항06": "answer_text=634 쪽",
            "문항07": "answer_text=148 명",
            "문항08": "answer=1043",
            "문항09": "answer_text=위인전, 134 권",
            "문항10": "answer=495",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_1단원_덧셈과뺄셈_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_division_round1_page1_templates(self) -> None:
        cases = {
            "문항01": "answer=8",
            "문항02": "answer_text=32 ÷ 8 = 4",
            "문항03": "answer_text=8 ÷ 4 = 2",
            "문항04": "answer_text=6 ÷ 2 = 3",
            "문항05": "answer_text=12 ÷ 3 = 4",
            "문항06": "answer_text=가",
            "문항07": "answer_text=다",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_3단원_나눗셈_1회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_division_round1_page2_templates(self) -> None:
        cases = {
            "문항01": "answer_text=준수",
            "문항02": "answer_text=빈칸: 6, 7, 42, 7, 6",
            "문항03": "answer_text=②, ④",
            "문항04": "answer_text=5, 8, 5",
            "문항05": "answer_text=다",
            "문항06": "answer_text=㉠ 3, ㉡ 4",
            "문항07": "answer_text=7 개",
            "문항08": "answer_text=8 송이",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_3단원_나눗셈_1회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_division_round1_page3_templates(self) -> None:
        cases = {
            "문항01": "answer_text=㉠ 9, ㉡ 6",
            "문항02": "answer=36",
            "문항03": "answer=7",
            "문항04": "answer_text=나, 가, 다",
            "문항05": "answer_text=6 m",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_3단원_나눗셈_1회_p03_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_division_round2_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=4 개",
            "문항02": "answer=5",
            "문항03": "answer_text=27 ÷ 9 = 3",
            "문항04": "answer=8",
            "문항05": "answer=8",
            "문항06": "answer_text=24 ÷ 6 = 4",
            "문항07": "answer_text=<",
            "문항08": "answer_text=9 개",
            "문항09": "answer=6",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_3단원_나눗셈_2회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_division_round2_page2_templates(self) -> None:
        cases = {
            "문항01": "answer=21",
            "문항02": "answer_text=6 개",
            "문항03": "answer_text=42, 6",
            "문항04": "answer_text=가운데 식에 ○표",
            "문항05": "answer_text=9 개",
            "문항06": "answer_text=9 대",
            "문항07": "answer=8",
            "문항08": "answer_text=5 개",
            "문항09": "answer_text=9 개",
            "문항10": "answer=8",
            "문항11": "answer_text=14 cm",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_3단원_나눗셈_2회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_division_round3_page1_templates(self) -> None:
        cases = {
            "문항01": "answer_text=7 개",
            "문항02": "answer=5",
            "문항03": "answer_text=28 ÷ 7 = 4",
            "문항04": "answer=6",
            "문항05": "answer=7",
            "문항06": "answer_text=36 ÷ 9 = 4",
            "문항07": "answer_text=<",
            "문항08": "answer_text=6 줄",
            "문항09": "answer=2",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_3단원_나눗셈_3회_p01_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_grade3_division_round3_page2_templates(self) -> None:
        cases = {
            "문항01": "answer=8",
            "문항02": "answer_text=4 개",
            "문항03": "answer_text=7, 7",
            "문항04": "answer_text=왼쪽 식에 ○표",
            "문항05": "answer_text=8 개",
            "문항06": "answer_text=8 대",
            "문항07": "answer=9",
            "문항08": "answer_text=8 개",
            "문항09": "answer_text=9 쪽",
            "문항10": "answer=4",
            "문항11": "answer_text=26 cm",
        }

        for card_label, expression in cases.items():
            with self.subTest(card_label=card_label):
                template = infer_elementary_visual_template(
                    f"/tmp/초3-1_3단원_나눗셈_3회_p02_{card_label}.png",
                )

                self.assertIsNotNone(template)
                assert template is not None
                self.assertEqual(template.expression, expression)

    def test_infers_generic_make_ten_addition_from_ocr_text(self) -> None:
        template = infer_elementary_visual_template(
            "/tmp/capture.png",
            raw_text="3. | ㅣ 안에 알맞은 수를 써넣으시오.\n8+5ㅋ |\n2 | |",
        )

        self.assertIsNotNone(template)
        assert template is not None
        self.assertEqual(template.rule_id, "generic_make_ten_addition_decomposition")
        self.assertEqual(template.expression, "answer_text=빈칸: 13, 3")

    def test_infers_generic_tens_box_count_from_ocr_text(self) -> None:
        template = infer_elementary_visual_template(
            "/tmp/capture.png",
            raw_text="2. 연필이 한 상자에 10자루씩 들어 있습니다. 연필을 60자루 사려면 몇 상자를 사야 합니까?",
        )

        self.assertIsNotNone(template)
        assert template is not None
        self.assertEqual(template.rule_id, "generic_tens_box_count")
        self.assertEqual(template.expression, "answer_text=6상자")

    def test_infers_generic_tens_bundle_write_read_from_ocr_text(self) -> None:
        template = infer_elementary_visual_template(
            "/tmp/capture.png",
            raw_text="4. 나타내는 수를 쓰고 읽어 보세요. 10개씩 묶음 8개",
        )

        self.assertIsNotNone(template)
        assert template is not None
        self.assertEqual(template.rule_id, "generic_tens_bundle_write_read")
        self.assertEqual(template.expression, "answer_text=쓰기: 80 / 읽기: 팔십, 여든")

    def test_infers_generic_tens_bundle_and_extra_count_from_ocr_text(self) -> None:
        template = infer_elementary_visual_template(
            "/tmp/capture.png",
            raw_text="6. 초콜릿이 10개 묶음 8개와 날개 15개가 있습니다. 초콜릿은 모두 몇 개입니까?",
        )

        self.assertIsNotNone(template)
        assert template is not None
        self.assertEqual(template.rule_id, "generic_tens_bundle_and_extra_count")
        self.assertEqual(template.expression, "answer_text=95개")

    def test_infers_generic_tens_bundle_and_extra_count_with_sheet_unit(self) -> None:
        template = infer_elementary_visual_template(
            "/tmp/capture.png",
            raw_text="6. 색종이가 10장씩 묶음 6개와 날개 19장이 있습니다. 색종이는 모두 몇 장입니까?",
        )

        self.assertIsNotNone(template)
        assert template is not None
        self.assertEqual(template.rule_id, "generic_tens_bundle_and_extra_count")
        self.assertEqual(template.expression, "answer_text=79장")

    def test_infers_birth_season_strip_graph_ratio(self) -> None:
        template = infer_elementary_visual_template(
            "/tmp/capture.png",
            raw_text=(
                "□ 안에 알맞은 수를 써 넣어 띠그래프를 완성해 보세요. "
                "태어난 계절별 학생 수 봄 (40%) 여름 가을 (30%) 겨울 "
                "봄에 태어난 학생은 겨울에 태어난 학생의 몇 배인가요?"
            ),
        )

        self.assertIsNotNone(template)
        assert template is not None
        self.assertEqual(template.rule_id, "generic_birth_season_strip_graph_ratio")
        self.assertEqual(template.expression, "answer_text=여름 20%, 겨울 10%, 봄은 겨울의 4배")

    def test_infers_birth_season_strip_graph_completion(self) -> None:
        template = infer_elementary_visual_template(
            "/tmp/capture.png",
            raw_text=(
                "안에 알맞은 수를 써 넣어 띠그래프를 완성해 보세요. "
                "태어난 계절별 학생 수 0 10 20 30 40 50 60 70 80 90 100(%) "
                "봄 (40%) 여름 가을 (30%) 겨울 "
                "여름: 100/500 x 100 = □ 이므로 □% 겨울: 50/500 x 100 = □ 이므로 □%"
            ),
        )

        self.assertIsNotNone(template)
        assert template is not None
        self.assertEqual(template.rule_id, "generic_birth_season_strip_graph_complete")
        self.assertEqual(template.expression, "answer_text=여름 100명, 20%; 겨울 50명, 10%")

    def test_infers_division_to_fraction_model_from_app_ocr(self) -> None:
        template = infer_elementary_visual_template(
            "/tmp/capture.png",
            raw_text=(
                "04 5 +45 그림에 나타내고, SS BAS 나타내어 보세요.\n"
                "04 5 + 4를 그림에 나타내고, FS 분수로 나타내어 보세요."
            ),
        )

        self.assertIsNotNone(template)
        assert template is not None
        self.assertEqual(template.rule_id, "generic_division_to_fraction_model")
        self.assertEqual(template.expression, "answer_text=5/4 = 1 1/4")

    def test_solves_text_answer_template_expression(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="수를 두 가지로 읽어 보세요.",
            expressions=["answer_text=(1) 셋, 삼 / (2) 넷, 사"],
            math_topic="arithmetic",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "visual_template_solver")
        self.assertEqual(solved.computed_answer, "(1) 셋, 삼 / (2) 넷, 사")
        self.assertEqual(solved.validation_status, "verified")


if __name__ == "__main__":
    unittest.main()
