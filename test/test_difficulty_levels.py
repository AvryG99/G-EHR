import unittest
from evaluation.difficulty_levels import physical_tables


class DifficultyTests(unittest.TestCase):
    def test_cte_and_self_join_do_not_inflate_count(self):
        names,status=physical_tables('WITH x AS (SELECT * FROM patients) SELECT * FROM x JOIN patients p ON x.subject_id=p.subject_id JOIN admissions a ON p.subject_id=a.subject_id')
        self.assertEqual(names,['admissions','patients'])
        self.assertEqual(status,'parsed')

    def test_subquery_and_qualified_tables_are_counted(self):
        names,_=physical_tables('SELECT * FROM `physionet-data.mimiciii_notes.noteevents` WHERE subject_id IN (SELECT subject_id FROM patients)')
        self.assertEqual(names,['noteevents','patients'])

    def test_missing_sql_is_unclassified(self):
        self.assertEqual(physical_tables(None),([], 'missing_sql'))
