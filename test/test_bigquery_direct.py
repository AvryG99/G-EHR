import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from executor.code_runner import RuntimeConfig, run_sql, _run_cloud


class BigQueryDirectTests(unittest.TestCase):
    def config(self):
        return RuntimeConfig('cloud', Path('/missing.duckdb'), 'billing-project', 'data-project.mimiciii', 1000, 'US')

    def test_cloud_skips_local_database(self):
        with patch('executor.code_runner.validate_scan_guards'), patch('executor.code_runner._run_local') as local, patch('executor.code_runner._run_cloud', return_value={'success': True}) as cloud:
            self.assertTrue(run_sql('SELECT 1', config=self.config())['success'])
            local.assert_not_called()
            cloud.assert_called_once()

    def test_cloud_job_configs_and_result(self):
        client = MagicMock()
        client.query.side_effect = [SimpleNamespace(total_bytes_processed=10), SimpleNamespace(result=lambda: [{'subject_id': 1}])]
        bigquery = SimpleNamespace(Client=MagicMock(return_value=client), QueryJobConfig=lambda **kw: SimpleNamespace(**kw))
        with patch.dict('sys.modules', {'google': SimpleNamespace(cloud=SimpleNamespace(bigquery=bigquery)), 'google.cloud': SimpleNamespace(bigquery=bigquery)}):
            result = _run_cloud('SELECT subject_id FROM patients LIMIT 1', self.config())
        self.assertEqual(result['rows'], [{'subject_id': 1}])
        configs = [call.kwargs['job_config'] for call in client.query.call_args_list]
        self.assertTrue(configs[0].dry_run)
        for config in configs:
            self.assertEqual(config.default_dataset, 'data-project.mimiciii')
            self.assertFalse(config.use_legacy_sql)
        self.assertEqual(configs[1].maximum_bytes_billed, 1000)

    def test_over_budget_query_is_not_executed(self):
        client = MagicMock()
        client.query.return_value.total_bytes_processed = 1001
        bigquery = SimpleNamespace(Client=lambda **kw: client, QueryJobConfig=lambda **kw: SimpleNamespace(**kw))
        with patch.dict('sys.modules', {'google': SimpleNamespace(cloud=SimpleNamespace(bigquery=bigquery)), 'google.cloud': SimpleNamespace(bigquery=bigquery)}):
            with self.assertRaisesRegex(RuntimeError, 'exceeding'):
                _run_cloud('SELECT 1', self.config())
        self.assertEqual(client.query.call_count, 1)
