import unittest

from applied_ai_rig.intake import MODULE_IDS, QUESTIONS, recommend_modules


class IntakeTests(unittest.TestCase):
    def test_each_risk_answer_recommends_expected_module_with_reason(self) -> None:
        expected = {
            "external_model_api": "model-api",
            "sensitive_or_supplied_data": "data",
            "persist_model_content": "data",
            "quality_claims": "evaluation",
            "side_effects": "agentic-runtime",
            "production_use": "operations",
        }

        for question_id, module_id in expected.items():
            with self.subTest(question_id=question_id):
                recommendations = recommend_modules({question_id: True})
                self.assertIn(module_id, recommendations)
                self.assertTrue(recommendations[module_id])

    def test_negative_answers_recommend_no_optional_module(self) -> None:
        answers = {question.id: False for question in QUESTIONS}

        self.assertEqual(recommend_modules(answers), {})

    def test_unknown_answer_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown question ID"):
            recommend_modules({"future_question": True})

    def test_public_ids_are_stable_and_unique(self) -> None:
        self.assertEqual(
            MODULE_IDS,
            ("model-api", "data", "evaluation", "agentic-runtime", "operations"),
        )
        self.assertEqual(len({question.id for question in QUESTIONS}), len(QUESTIONS))


if __name__ == "__main__":
    unittest.main()
