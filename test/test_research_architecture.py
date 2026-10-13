import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from executor.code_runner import (
    RuntimeConfig,
    run_sql,
    transpile_for_duckdb,
    validate_scan_guards,
)
from graph.graph_builder import describe_join_paths
from rag.clinical_semantics import normalize_clinical_entities


class RuntimeConfigTests(unittest.TestCase):
    def test_environment_toggle(self):
        with patch.dict(os.environ, {"MIMIC_ENV": "cloud"}, clear=True):
            config = RuntimeConfig.from_env()
        self.assertEqual(config.environment, "cloud")

    def test_invalid_environment_is_rejected(self):
        with patch.dict(os.environ, {"MIMIC_ENV": "staging"}, clear=True):
            with self.assertRaises(ValueError):
                RuntimeConfig.from_env()


class SqlSandboxTests(unittest.TestCase):
    def test_bigquery_sql_is_transpiled(self):
        translated = transpile_for_duckdb(
            "SELECT DATE_DIFF(DATE '2020-01-02', DATE '2020-01-01', DAY) AS days"
        )
        self.assertIn("DATE_DIFF", translated.upper())

    def test_high_volume_scan_requires_itemid(self):
        with self.assertRaisesRegex(ValueError, "itemid constraint"):
            validate_scan_guards("SELECT * FROM chartevents WHERE subject_id = 1")

    def test_null_check_does_not_bypass_scan_guard(self):
        with self.assertRaisesRegex(ValueError, "itemid constraint"):
            validate_scan_guards(
                "SELECT * FROM labevents WHERE itemid IS NOT NULL"
            )

    def test_high_volume_scan_with_itemid_is_allowed(self):
        validate_scan_guards(
            "SELECT * FROM chartevents WHERE subject_id = 1 AND itemid = 220045"
        )

    def test_local_runtime_executes_transpiled_query(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "sandbox.duckdb"
            import duckdb

            with duckdb.connect(str(database)) as connection:
                connection.execute("CREATE TABLE patients(subject_id INTEGER)")
                connection.execute("INSERT INTO patients VALUES (1)")

            result = run_sql(
                "SELECT subject_id FROM patients",
                config=RuntimeConfig("local", database, None, None, 1_000_000),
            )
        self.assertTrue(result["success"])
        self.assertEqual(result["rows"], [{"subject_id": 1}])


class ClinicalContextTests(unittest.TestCase):
    def test_clinical_synonym_normalization(self):
        normalized = normalize_clinical_entities(
            "Patients admitted after a heart attack"
        )
        self.assertEqual(
            normalized, "Patients admitted after a myocardial infarction"
        )

    def test_graph_returns_join_keys(self):
        paths = describe_join_paths({"patients", "diagnoses_icd"})
        keys = [join["key"] for join in paths[0]["joins"]]
        self.assertEqual(keys, ["subject_id"])


if __name__ == "__main__":
    unittest.main()
