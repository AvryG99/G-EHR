import json
import unittest
from unittest.mock import MagicMock, patch

from medical_assistant import MedicalDatabaseAssistant
from prompt.result_review import review_payload, parse_review
from rag.query_context import apply_query_context
from prompt.query_validation import validate_revision_scope


def verdict(status='accepted'):
    return json.dumps({'status': status, 'issues': ['Arbitrary note limit loses history evidence']
                       if status == 'needs_revision' else [],
                       'suggested_fix': 'Remove the arbitrary limit' if status == 'needs_revision' else ''})


class ResultSelfDebuggingTests(unittest.TestCase):
    def setUp(self):
        self.llm = MagicMock()
        self.agent = MedicalDatabaseAssistant(self.llm, MagicMock(), MagicMock())
        self.rag = {'tables_info': apply_query_context('history of cva', {})}
        self.sql = 'SELECT text FROM noteevents WHERE subject_id=1 AND hadm_id=2 LIMIT 1'
        self.result = {'success': True, 'rows': [{'text': 'No stroke'}]}
        self.question = 'For patient subject_id = 1, hospital admission hadm_id = 2: history of cva?'
        self.logging = patch('medical_assistant.log_sql_prompt')
        self.logging.start()
        self.addCleanup(self.logging.stop)

    def test_accepted_keeps_array_and_does_not_reexecute(self):
        self.llm.generate.return_value = verdict()
        with patch.object(self.agent, 'generate_sql_with_retry') as run:
            sql, result = self.agent.review_and_revise(self.question, self.rag, self.sql, self.result)
        run.assert_not_called()
        self.assertEqual(sql, self.sql)
        self.assertEqual(result['rows'], self.result['rows'])
        self.assertEqual(result['review_status'], 'accepted')
        self.assertNotIn('reference_answers', self.llm.generate.call_args.args[0])

    def test_specific_issue_revises_and_rechecks(self):
        revised_sql = self.sql.removesuffix(' LIMIT 1')
        revised_result = {'success': True, 'rows': [{'text': 'Previous CVA'}]}
        self.llm.generate.side_effect = [verdict('needs_revision'), verdict()]
        with patch.object(self.agent, 'generate_sql_with_retry', return_value=(revised_sql, revised_result)) as run:
            sql, result = self.agent.review_and_revise(self.question, self.rag, self.sql, self.result)
        self.assertEqual(sql, revised_sql)
        self.assertEqual(result['rows'], revised_result['rows'])
        self.assertEqual(len(result['review_history']), 2)
        self.assertIn(self.question, run.call_args.kwargs['initial_prompt'])

    def test_revision_limit_is_two_even_when_reviewer_keeps_requesting(self):
        self.llm.generate.return_value = verdict('needs_revision')
        with patch.object(self.agent, 'generate_sql_with_retry', return_value=(self.sql, self.result)) as run:
            _, result = self.agent.review_and_revise(self.question, self.rag, self.sql, self.result)
        self.assertEqual(run.call_count, 2)
        self.assertEqual(self.llm.generate.call_count, 3)
        self.assertEqual(result['review_status'], 'revision_limit')

    def test_failed_revision_preserves_last_successful_sql_and_array(self):
        self.llm.generate.return_value = verdict('needs_revision')
        with patch.object(self.agent, 'generate_sql_with_retry', return_value=('bad SQL', {'success': False, 'error': 'budget exceeded'})):
            sql, result = self.agent.review_and_revise(self.question, self.rag, self.sql, self.result)
        self.assertEqual(sql, self.sql)
        self.assertTrue(result['success'])
        self.assertEqual(result['rows'], self.result['rows'])
        self.assertEqual(result['review_status'], 'revision_failed')

    def test_invalid_reviewer_response_and_insufficient_evidence(self):
        self.llm.generate.return_value = 'not JSON'
        _, result = self.agent.review_and_revise(self.question, self.rag, self.sql, self.result)
        self.assertEqual(result['review_status'], 'review_unavailable')
        self.llm.generate.return_value = verdict('insufficient_evidence')
        _, result = self.agent.review_and_revise(self.question, self.rag, self.sql, self.result)
        self.assertEqual(result['review_status'], 'insufficient_evidence')

    def test_failure_or_disabled_review_makes_no_model_calls(self):
        self.agent.review_and_revise(self.question, self.rag, self.sql, {'success': False})
        self.agent.max_semantic_retry = 0
        self.agent.review_and_revise(self.question, self.rag, self.sql, self.result)
        self.llm.generate.assert_not_called()

    def test_review_preview_is_bounded_and_explicitly_partial(self):
        rows = [{'text': 'x' * 1000}, {'text': 'CVA'}]
        payload = review_payload('history?', {}, 'SELECT text FROM noteevents', rows, max_chars=100)
        self.assertTrue(payload['evidence_truncated'])
        self.assertEqual(payload['total_rows'], 2)
        self.assertEqual(len(payload['result_array'][0]['partial_row_preview']), 100)
        self.assertEqual(len(rows[0]['text']), 1000)
        with self.assertRaises(ValueError):
            parse_review('{"status":"needs_revision","issues":[],"suggested_fix":""}')

    def test_semantic_revision_cannot_drop_scope_in_union_or_cte(self):
        scoped = 'SELECT text FROM noteevents WHERE subject_id=1 AND hadm_id=2'
        validate_revision_scope(scoped, self.question)
        validate_revision_scope(scoped + ' UNION ALL ' + scoped, self.question)
        validate_revision_scope('SELECT dob FROM patients WHERE subject_id=1', self.question)
        for sql in ('SELECT text FROM noteevents',
                    scoped + ' UNION ALL SELECT text FROM noteevents',
                    'WITH n AS (SELECT text FROM noteevents) SELECT text FROM n',
                    'SELECT text FROM noteevents WHERE subject_id=1 AND hadm_id=3'):
            with self.subTest(sql=sql), self.assertRaisesRegex(ValueError, 'explicit requested'):
                validate_revision_scope(sql, self.question)

    def test_query_integrates_review_without_prose(self):
        self.agent.retriever.rag_retrieve.return_value = self.rag
        self.llm.generate.return_value = verdict()
        with patch.object(self.agent, 'generate_sql_with_retry', return_value=(self.sql, self.result)), patch.object(self.agent, 'generate_natural_response') as prose:
            _, result = self.agent.query(self.question)
        self.assertEqual(result['review_status'], 'accepted')
        prose.assert_not_called()
