from __future__ import annotations

import unittest

from app.engines.router.school_level_router import infer_school_profile, normalize_school_level


class SchoolLevelRouterTests(unittest.TestCase):
    def test_detects_elementary_profile_from_path(self) -> None:
        profile = infer_school_profile(
            "/tmp/01.초등/1학년/EDITE/초1-1_1단원_9까지의수_1회_p02_문항03.png",
            "ㅁ 안에 알맞은 수를 써넣으세요.",
        )

        self.assertEqual(profile.school_level, "elementary")
        self.assertEqual(profile.grade, 1)
        self.assertEqual(profile.semester, 1)
        self.assertEqual(profile.unit, "1단원 9까지의수")
        self.assertEqual(profile.profile, "elementary_visual")

    def test_detects_high_profile_from_text(self) -> None:
        profile = infer_school_profile("/tmp/problem.png", "함수 f(x)에 대하여 lim x->1 f(x)의 값을 구하시오.")

        self.assertEqual(profile.school_level, "high")
        self.assertEqual(profile.profile, "high_symbolic")

    def test_normalizes_korean_level_aliases(self) -> None:
        self.assertEqual(normalize_school_level("초등"), "elementary")
        self.assertEqual(normalize_school_level("중"), "middle")
        self.assertEqual(normalize_school_level("고등"), "high")


if __name__ == "__main__":
    unittest.main()
