import json
import unittest
from prompt.schema_context import build_schema_context, format_schema_context, select_schema_columns
from graph.tables import tables


class SchemaContextTests(unittest.TestCase):
    def rag(self, **columns):
        return {'tables_info': {table: {'columns': [{'name': name, 'score': .8} for name in names]} for table, names in columns.items()}}

    def test_medication_context_is_selective_and_grounded(self):
        rag = self.rag(prescriptions=['route'])
        context = build_schema_context(rag, [{'table': 'prescriptions', 'column': 'drug', 'value': 'Lidocaine 5% Ointment'}])
        info = context['tables']['prescriptions']
        self.assertIn('does not confirm administration', info['meaning'])
        self.assertEqual(set(info['columns']), {'drug', 'prod_strength', 'route'})
        self.assertEqual(len(context['lookup_values']), 1)
        self.assertLess(len(format_schema_context(rag)), len(json.dumps(tables['prescriptions'])))

    def test_join_keys_present_on_both_sides(self):
        selected = select_schema_columns(self.rag(prescriptions=['route'], icustays=['los'])['tables_info'])
        for table in ('prescriptions', 'icustays'):
            self.assertIn('icustay_id', {c['name'] for c in selected[table]['columns']})
        context = build_schema_context({'tables_info': selected})
        self.assertTrue(any('icustay_id' in join for join in context['joins']))

    def test_unknown_columns_and_lookup_values_are_excluded(self):
        context = build_schema_context(self.rag(admissions=['age', 'admittime']), [{'table': 'cost', 'column': 'cost', 'value': '10'}])
        self.assertNotIn('age', context['tables']['admissions']['columns'])
        self.assertEqual(context['lookup_values'], [])

    def test_serialization_and_selection_preserve_scores(self):
        rag = self.rag(prescriptions=['route'])
        self.assertEqual(json.loads(format_schema_context(rag)), build_schema_context(rag))
        columns = select_schema_columns(rag['tables_info'])['prescriptions']['columns']
        self.assertEqual(next(c['score'] for c in columns if c['name'] == 'route'), .8)
