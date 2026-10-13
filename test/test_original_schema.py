import unittest
from graph.tables import tables, unique_columns


class OriginalSchemaTests(unittest.TestCase):
    def test_original_tables_and_columns(self):
        self.assertEqual(len(tables), 26)
        self.assertEqual(sum(len(t['attributes']) for t in tables.values()), 324)
        self.assertNotIn('cost', tables)
        self.assertNotIn('age', tables['admissions']['attributes'])
        for name in ('diagnoses_icd', 'procedures_icd'):
            self.assertNotIn('charttime', tables[name]['attributes'])
            self.assertIn('seq_num', tables[name]['attributes'])
            self.assertTrue(tables[name]['attributes']['icd9_code']['datatype'].startswith('VARCHAR('))
        self.assertEqual(tables['patients']['attributes']['dob']['datatype'], 'TIMESTAMP')

    def test_foreign_keys_reference_existing_columns(self):
        for table in tables.values():
            for fk in table['foreign_keys']:
                self.assertIn(fk['column'], table['attributes'])
                self.assertIn(fk['references'], tables[fk['table']]['attributes'])

    def test_retrieval_metadata_matches_schema(self):
        for column, info in unique_columns().items():
            self.assertEqual(set(info['tables']), {t for t, s in tables.items() if column in s['attributes']})
