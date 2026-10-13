import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from executor.code_runner import run_sql, _run_cloud, RuntimeConfig
from executor.error_parser import parse_sql_error
from medical_assistant import MedicalDatabaseAssistant, build_schema_context_for_repair
from rag.query_context import retrieval_question, preferred_tables
from rag.retrieve import MIMICColumnRetriever


class RecordedFailureTests(unittest.TestCase):
    def test_scope_is_removed_only_from_retrieval(self):
        question = 'For patient subject_id = 13702, hospital admission hadm_id = 196489: does the patient have copd exacerbation?'
        self.assertEqual(retrieval_question(question), 'does the patient have copd exacerbation?')
        self.assertEqual(preferred_tables(retrieval_question(question)), {'noteevents'})
        self.assertEqual(preferred_tables('date of birth?'), {'patients'})

    def test_shared_id_does_not_select_unrelated_table(self):
        retriever = MIMICColumnRetriever.__new__(MIMICColumnRetriever)
        cols = [{'column_name':'subject_id', 'tables':['admissions','patients'], 'description':'ID', 'similarity_score':1},
                {'column_name':'dob', 'tables':['patients'], 'description':'birth', 'similarity_score':.9}]
        self.assertEqual(set(retriever.organize_by_table(cols)), {'patients'})

    def test_syntax_error_enters_retry(self):
        result = run_sql('SELECT 1 OPTION (max_bytes_billed = 1)', config=RuntimeConfig('cloud', Path('/missing'), 'billing', 'data.notes', 1000))
        self.assertFalse(result['success'])
        self.assertIsInstance(build_schema_context_for_repair({'type':'syntax'}, 'SELECT 1 OPTION (bad = 1)'), dict)

    def test_budget_failure_stops_retry(self):
        llm = MagicMock()
        llm.generate.return_value = 'SELECT 1'
        agent = MedicalDatabaseAssistant(llm, MagicMock(), MagicMock())
        failure = {'success':False, 'error':'Query would process 2000 bytes, exceeding the configured limit of 1000 bytes'}
        with patch.object(agent, 'build_prompt', return_value='prompt'), patch('medical_assistant.log_sql_prompt'), patch('medical_assistant.run_sql', return_value=failure) as runner:
            _, result = agent.generate_sql_with_retry('test', {})
        self.assertEqual(result['reason'], 'scan_budget')
        self.assertEqual(runner.call_count, 1)
        self.assertIn('no result', agent.generate_natural_response('test', result, False))

    def test_notes_query_is_qualified(self):
        client = MagicMock()
        client.query.side_effect = [SimpleNamespace(total_bytes_processed=10), SimpleNamespace(result=lambda: [])]
        bq = SimpleNamespace(Client=lambda **kw:client, QueryJobConfig=lambda **kw:SimpleNamespace(**kw))
        with patch.dict('sys.modules', {'google.cloud':SimpleNamespace(bigquery=bq)}):
            _run_cloud('SELECT text FROM noteevents WHERE row_id = 177', RuntimeConfig('cloud', Path('/missing'), 'billing', 'data.clinical', 1000))
        for call in client.query.call_args_list:
            self.assertIn('physionet-data.mimiciii_notes.noteevents', call.args[0])

    def test_zero_does_not_prove_clinical_absence(self):
        llm = MagicMock()
        agent = MedicalDatabaseAssistant(llm, MagicMock(), MagicMock())
        answer = agent.generate_natural_response('does patient have dyspnea?', {'rows':[{'count':0}]}, True)
        self.assertIn('does not establish', answer)
        llm.generate.assert_not_called()
        self.assertEqual(parse_sql_error('Query would process 2000 bytes, exceeding the configured limit of 1000 bytes')['type'], 'scan_budget')
