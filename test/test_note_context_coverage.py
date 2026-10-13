import unittest
from rag.query_context import apply_query_context
from prompt.schema_context import build_schema_context
from executor.code_runner import RuntimeConfig, query_scan_limit
from unittest.mock import patch


class NoteContextCoverageTests(unittest.TestCase):
    def test_previously_missed_narrative_questions_include_text(self):
        for question in (
            'is the patient tachypnic',
            'what is the patient left lower leg extremity ischemia status',
            'is there a mention of coffee ground emesis in the records',
            'why is the patient on pleurodesis',
            'does the patient have any other history of diarrhea',
            'is there mention c / c / e anywhere in the record',
        ):
            with self.subTest(question=question):
                selected=apply_query_context(question, {'cptevents':{'columns':[{'name':'description'}]}})
                context=build_schema_context({'tables_info':selected})
                self.assertIn('text',context['tables']['noteevents']['columns'])
                self.assertEqual(context['tables']['noteevents']['role'], 'narrative_evidence')

    def test_note_table_never_loses_text_during_column_selection(self):
        context=build_schema_context({'tables_info':{'noteevents':{'columns':[{'name':'chartdate'}]}}})
        self.assertIn('text',context['tables']['noteevents']['columns'])
        self.assertIn('hadm_id',context['tables']['noteevents']['columns'])

    def test_structured_questions_keep_their_tables(self):
        for question,table,column in (('what is the latest glucose level','labevents','valuenum'),
                                      ('what is lidocaine route','prescriptions','route')):
            selected=apply_query_context(question,{table:{'columns':[{'name':column}]}})
            self.assertIn(table,selected)
            self.assertNotIn('noteevents',selected)
        selected=apply_query_context('what is the date of birth',{})
        self.assertEqual(set(selected),{'patients'})

    def test_updated_environment_defaults_and_limits(self):
        with patch('utils.config.load_project_env'),patch.dict('os.environ',{},clear=True):
            config=RuntimeConfig.from_env()
        self.assertEqual(query_scan_limit('SELECT * FROM patients',config),12_000_000_000)
        self.assertEqual(query_scan_limit('SELECT text FROM noteevents',config),30_000_000_000)
