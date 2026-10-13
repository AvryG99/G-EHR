import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from executor.code_runner import RuntimeConfig, query_scan_limit, _run_cloud


class ScanBudgetTests(unittest.TestCase):
    def setUp(self):
        self.config = RuntimeConfig('cloud', Path('/missing'), 'billing', 'data.clinical', 1_000_000_000)

    def test_table_references_select_budget(self):
        for sql in ('SELECT text FROM noteevents', 'SELECT value FROM `physionet-data.mimiciii_clinical.chartevents`',
                    'SELECT * FROM patients p JOIN chartevents c USING (subject_id)',
                    'SELECT * FROM patients WHERE subject_id IN (SELECT subject_id FROM chartevents)',
                    'WITH n AS (SELECT text FROM noteevents) SELECT * FROM n'):
            with self.subTest(sql=sql):
                self.assertEqual(query_scan_limit(sql, self.config), 30_000_000_000)

    def test_literals_comments_cte_names_do_not_raise_budget(self):
        for sql in ("SELECT 'chartevents' AS name", 'SELECT * FROM patients -- noteevents',
                    'WITH chartevents AS (SELECT subject_id FROM patients) SELECT * FROM chartevents',
                    'SELECT * FROM labevents'):
            with self.subTest(sql=sql):
                self.assertEqual(query_scan_limit(sql, self.config), 1_000_000_000)

    def test_dry_run_and_execution_share_large_budget(self):
        client = MagicMock()
        client.query.side_effect = [SimpleNamespace(total_bytes_processed=5_000_000_000), SimpleNamespace(result=lambda: [])]
        bq = SimpleNamespace(Client=lambda **kw: client, QueryJobConfig=lambda **kw:SimpleNamespace(**kw))
        with patch.dict('sys.modules', {'google.cloud':SimpleNamespace(bigquery=bq)}):
            result = _run_cloud('SELECT value FROM chartevents WHERE itemid=1', self.config)
        self.assertTrue(result['success'])
        self.assertEqual(result['maximum_bytes_billed'], 30_000_000_000)
        self.assertEqual(client.query.call_args_list[1].kwargs['job_config'].maximum_bytes_billed, 30_000_000_000)

    def test_above_large_budget_is_blocked(self):
        client = MagicMock()
        client.query.return_value.total_bytes_processed = 30_000_000_001
        bq = SimpleNamespace(Client=lambda **kw: client, QueryJobConfig=lambda **kw:SimpleNamespace(**kw))
        with patch.dict('sys.modules', {'google.cloud':SimpleNamespace(bigquery=bq)}):
            with self.assertRaisesRegex(RuntimeError, '30000000000'):
                _run_cloud('SELECT text FROM noteevents', self.config)
        self.assertEqual(client.query.call_count, 1)
