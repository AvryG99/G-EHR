import unittest
from unittest.mock import MagicMock, patch
from rag.query_context import apply_query_context
from prompt.query_validation import validate_query
from medical_assistant import MedicalDatabaseAssistant


class NarrativeRegressions(unittest.TestCase):
    def test_narrative_drops_unneeded_join_candidates_but_mixed_keeps_labs(self):
        hits = {'admissions': {'columns': [{'name': 'admittime'}]}}
        self.assertEqual(set(apply_query_context('current lad status', hits)), {'noteevents'})
        mixed = apply_query_context('history and baseline creatinine results', hits)
        self.assertIn('noteevents', mixed)
        self.assertIn('labevents', mixed)

    def test_leaking_or_and_invalid_distinct_are_rejected(self):
        question = 'For patient subject_id = 1, hospital admission hadm_id = 2: history of cva?'
        with self.assertRaisesRegex(ValueError, 'OR branch'):
            validate_query("SELECT text FROM noteevents WHERE subject_id=1 AND hadm_id=2 AND text LIKE '%cva%' OR text LIKE '%stroke%'", question)
        validate_query("SELECT text FROM noteevents WHERE subject_id=1 AND hadm_id=2 AND (text LIKE '%cva%' OR text LIKE '%stroke%')", question)
        with self.assertRaisesRegex(ValueError, 'DISTINCT'):
            validate_query('SELECT DISTINCT text FROM noteevents ORDER BY chartdate', question)
        validate_query('SELECT DISTINCT text, chartdate FROM noteevents ORDER BY chartdate', question)

    def test_empty_narrative_retry_is_bounded_and_preserves_question(self):
        llm = MagicMock()
        llm.generate.return_value = 'SELECT text FROM noteevents WHERE subject_id=1 AND hadm_id=2'
        agent = MedicalDatabaseAssistant(llm, MagicMock(), MagicMock())
        rag = {'tables_info': apply_query_context('current lad status', {})}
        question = 'For patient subject_id = 1, hospital admission hadm_id = 2: current lad status?'
        with patch('medical_assistant.run_sql', return_value={'success': True, 'rows': []}) as run, patch('medical_assistant.log_sql_prompt'):
            _, result = agent.generate_sql_with_retry(question, rag)
        self.assertTrue(result['success'])
        self.assertEqual(run.call_count, 2)
        self.assertIn(question, llm.generate.call_args.args[0])
