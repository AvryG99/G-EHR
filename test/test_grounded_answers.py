import unittest
from unittest.mock import MagicMock
from medical_assistant import MedicalDatabaseAssistant


class GroundedAnswerTests(unittest.TestCase):
    def setUp(self):
        self.llm = MagicMock()
        self.retriever = MagicMock()
        self.agent = MedicalDatabaseAssistant(self.llm, self.retriever, MagicMock())

    def test_empty_results_do_not_invoke_model(self):
        answer = self.agent.generate_natural_response('route?', {'rows': []}, True)
        self.assertIn('No matching records', answer)
        self.llm.generate.assert_not_called()

    def test_null_results_do_not_invoke_model(self):
        answer = self.agent.generate_natural_response('route?', {'rows': [{'route': None}]}, True)
        self.assertIn('no value', answer)
        self.llm.generate.assert_not_called()

    def test_answer_prompt_contains_actual_values_and_grounding(self):
        self.agent.generate_natural_response('route?', {'rows': [{'route': 'TOP'}]}, True)
        prompt = self.llm.generate.call_args.args[0]
        self.assertIn('"route": "TOP"', prompt)
        self.assertIn('using ONLY the returned database values', prompt)
        self.assertIn('do not infer', prompt)

    def test_cost_question_is_unsupported_without_query(self):
        answer, sql, result = self.agent.answer('how much does it cost to receive a diagnosis for leukocytosis nos?', [])
        self.assertIn('does not contain cost', answer)
        self.assertIsNone(sql)
        self.assertEqual(result['reason'], 'unsupported_schema')
        self.retriever.rag_retrieve.assert_not_called()
        self.llm.generate.assert_not_called()
