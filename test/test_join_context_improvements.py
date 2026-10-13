import unittest
from unittest.mock import MagicMock, patch
from graph.graph_builder import describe_join_paths
from graph.tables import tables
from rag.query_context import apply_query_context
from prompt.schema_context import build_schema_context
from prompt.schema_validation import validate_schema_context
from medical_assistant import MedicalDatabaseAssistant
from rag.retrieve import expand_query


class JoinContextImprovements(unittest.TestCase):
    def context(self, question, initial=None):
        return build_schema_context({'tables_info':apply_query_context(question,initial or {})})

    def test_query_expansion_does_not_corrupt_latest(self):
        question='latest glucose level'
        self.assertEqual(expand_query(question),[question])
        expanded=expand_query('antibiotics prescribed')
        self.assertIn('antimicrobial prescribed',expanded)
        self.assertEqual(expanded,expand_query('antibiotics prescribed'))

    def test_mixed_lab_history_keeps_both_sources(self):
        ctx=self.context('when was the patient evaluated for chronic renal insufficiency and what are baseline creatinine results')
        for table in ('labevents','d_labitems','noteevents'):
            self.assertIn(table,ctx['tables'])
        self.assertIn('valuenum',ctx['tables']['labevents']['columns'])
        self.assertIn('label',ctx['tables']['d_labitems']['columns'])

    def test_event_dictionary_added_without_query_keywords(self):
        ctx=build_schema_context({'tables_info':{'chartevents':{'columns':[{'name':'valuenum'}]}}})
        self.assertIn('d_items',ctx['tables'])
        self.assertNotIn('d_labitems',ctx['tables'])
        self.assertTrue(any('chartevents.itemid' in j and 'd_items.itemid' in j for j in ctx['joins']))

    def test_heart_rate_and_abbreviated_labs_route_to_correct_domain(self):
        self.assertIn('chartevents',self.context('when did his heart rate go up to 90s')['tables'])
        self.assertIn('labevents',self.context('what was his wbc count in the ed')['tables'])
        self.assertIn('labevents',self.context("is the patient's hct stable")['tables'])
        ctx=self.context('did the patient become hypotensive to sbp of 80s-90s')
        self.assertIn('chartevents',ctx['tables'])
        self.assertNotIn('labevents',ctx['tables'])

    def test_shared_admission_join_includes_both_keys(self):
        ctx=self.context('history and lactate results')
        self.assertTrue(any('labevents.subject_id = noteevents.subject_id AND labevents.hadm_id = noteevents.hadm_id'==j for j in ctx['joins']))

    def test_fk_columns_really_exist_on_both_sides(self):
        for path in describe_join_paths(tables):
            for join in path['joins']:
                self.assertIn(join['left_key'],tables[join['left']]['attributes'])
                self.assertIn(join['right_key'],tables[join['right']]['attributes'])
        ctx=build_schema_context({'tables_info':{'microbiologyevents':{'columns':[]}}})
        self.assertIn('d_items.itemid = microbiologyevents.spec_itemid',ctx['joins'])
        self.assertIn('d_items.itemid = microbiologyevents.org_itemid',ctx['joins'])
        self.assertIn('d_items.itemid = microbiologyevents.ab_itemid',ctx['joins'])

    def test_context_guard_accepts_correlated_cte_and_nested_lookup(self):
        rag={'tables_info':apply_query_context('last lactate',{})}
        validate_schema_context("SELECT le.valuenum FROM labevents le WHERE le.itemid IN (SELECT itemid FROM d_labitems WHERE LOWER(label)='lactate')",rag)
        validate_schema_context('WITH labs AS (SELECT valuenum FROM labevents) SELECT valuenum FROM labs',rag)
        with self.assertRaisesRegex(ValueError,'table prescriptions'):
            validate_schema_context('SELECT drug FROM prescriptions',rag)
        with self.assertRaisesRegex(ValueError,'labevents.label'):
            validate_schema_context('SELECT le.label FROM labevents le',rag)

    def test_unknown_table_is_repaired_before_any_database_call(self):
        llm=MagicMock();llm.generate.side_effect=['SELECT drug FROM prescriptions','SELECT dob FROM patients']
        agent=MedicalDatabaseAssistant(llm,MagicMock(),MagicMock(),max_retry=1)
        rag={'tables_info':{'patients':{'columns':[{'name':'dob'}]}}}
        with patch.object(agent,'build_prompt',return_value='prompt'),patch('medical_assistant.log_sql_prompt'),patch('medical_assistant.run_sql',return_value={'success':True,'rows':[]}) as run:
            sql,result=agent.generate_sql_with_retry('birth date?',rag)
        self.assertEqual(run.call_count,1)
        self.assertEqual(sql,'SELECT dob FROM patients')
        self.assertTrue(result['success'])
        self.assertIn('allowed_schema',llm.generate.call_args.args[0])
