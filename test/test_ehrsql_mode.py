import json
import unittest
from unittest.mock import MagicMock

from ehrsql.assistant import EHRSQLAssistant, extract_sql, retrieve_examples
from ehrsql.executor import execute, official_answer, post_process_sql, run_sql
from ehrsql.schema import load_schema, prompt_schema
from evaluation.run_ehrsql_batch import official_metrics


class EHRSQLModeTests(unittest.TestCase):
    def test_official_cleaned_schema_shape(self):
        schema = load_schema()
        prompt = prompt_schema()
        self.assertEqual(schema['db_id'], 'mimic_iii')
        self.assertEqual(len(prompt['tables']), 17)
        self.assertEqual(sum(map(len, prompt['tables'].values())), 113)
        self.assertEqual(len(prompt['foreign_keys']), 25)
        self.assertIn('age', {c['name'] for c in prompt['tables']['admissions']})
        self.assertIn('cost', prompt['tables'])
        self.assertNotIn('noteevents', prompt['tables'])

    def test_local_sqlite_and_official_normalization(self):
        rows = execute("select distinct prescriptions.route from prescriptions where prescriptions.drug = 'danazol'")
        self.assertEqual(official_answer(rows), '["(\'po\',)"]')
        self.assertIn("2105-12-31", post_process_sql('select current_time'))
        self.assertEqual(run_sql('null')['abstained'], True)
        self.assertFalse(run_sql('delete from patients')['success'])

    def test_examples_come_only_from_training_data(self):
        examples = retrieve_examples('what is the route of danazol?', 4)
        self.assertEqual(len(examples), 4)
        self.assertTrue(all(example['split'] == 'train' for example in examples))

    def test_assistant_abstains_and_repairs_execution_errors(self):
        llm = MagicMock()
        llm.generate.return_value = 'null'
        sql, result = EHRSQLAssistant(llm).query('draw a chart of future visits')
        self.assertEqual(sql, 'null')
        self.assertTrue(result['success'])
        llm.reset_mock()
        llm.generate.side_effect = ['select missing from patients', 'select gender from patients limit 1']
        sql, result = EHRSQLAssistant(llm).query('give one gender')
        self.assertTrue(result['success'])
        self.assertEqual(llm.generate.call_count, 2)
        self.assertIn('SQLite error', llm.generate.call_args.args[0])

    def test_official_metrics_include_answerability_and_execution(self):
        rows = [
            {'correct': True, 'executable': True, 'abstained': False, 'is_impossible': False},
            {'correct': True, 'executable': False, 'abstained': True, 'is_impossible': True},
            {'correct': False, 'executable': False, 'abstained': True, 'is_impossible': False},
        ]
        metrics = official_metrics(rows)
        self.assertAlmostEqual(metrics['success_rate_percent'], 200/3)
        self.assertEqual(metrics['precision_ans'], 100)
        self.assertEqual(metrics['recall_ans'], 50)
        self.assertEqual(metrics['precision_exec'], 100)
        self.assertEqual(metrics['recall_exec'], 50)

    def test_extracts_plain_or_fenced_sql(self):
        self.assertEqual(extract_sql('```sql\nselect 1;\n```'), 'select 1')
        self.assertEqual(extract_sql('null'), 'null')
