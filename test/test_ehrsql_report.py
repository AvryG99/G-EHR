import unittest

from evaluation.build_ehrsql_report import bucket, breakdown, physical_tables


class EHRSQLReportTests(unittest.TestCase):
    def record(self, sql='select * from patients', impossible=False, correct=True):
        return {'gold_sql': 'null' if impossible else sql, 'is_impossible': impossible,
                'correct': correct, 'executable': not impossible, 'abstained': impossible}

    def test_counts_distinct_gold_tables_and_ctes(self):
        self.assertEqual(physical_tables('select * from patients'), ['patients'])
        self.assertEqual(physical_tables('with p as (select * from patients) select * from p'), ['patients'])
        self.assertEqual(bucket(self.record('select * from patients p join admissions a on p.subject_id=a.subject_id'))[0], 'level_2')
        self.assertEqual(bucket(self.record('select 1'))[0], 'no_table')
        self.assertEqual(bucket(self.record(impossible=True))[0], 'unanswerable')

    def test_breakdown_keeps_unanswerable_in_report(self):
        report = breakdown([self.record(), self.record(impossible=True), self.record(correct=False)])
        groups = {group['key']: group for group in report['groups']}
        self.assertEqual(groups['level_1']['questions'], 2)
        self.assertEqual(groups['unanswerable']['questions'], 1)
        self.assertEqual(groups['unanswerable']['correct'], 1)

