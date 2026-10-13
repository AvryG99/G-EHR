import unittest
from unittest.mock import MagicMock, patch
from medical_assistant import MedicalDatabaseAssistant
from evaluation.run_array_batch import summary


class SqlOnlyQueryTests(unittest.TestCase):
    def test_query_executes_without_prose_generation(self):
        agent = MedicalDatabaseAssistant(MagicMock(), MagicMock(), MagicMock(), max_semantic_retry=0)
        agent.retriever.rag_retrieve.return_value = {'tables_info':{}}
        result = {'success':True, 'rows':[{'dob':'2099-12-31'}]}
        with patch.object(agent, 'generate_sql_with_retry', return_value=('SELECT dob FROM patients', result)), patch.object(agent, 'generate_natural_response') as prose:
            sql, output = agent.query('what is the date of birth?')
        self.assertEqual(output['rows'], [{'dob':'2099-12-31'}])
        prose.assert_not_called()
        agent.llm.generate.assert_not_called()

    def test_query_retains_scope_for_sql_but_not_retrieval(self):
        agent = MedicalDatabaseAssistant(MagicMock(), MagicMock(), MagicMock())
        question = 'For patient subject_id = 1, hospital admission hadm_id = 2: birth date?'
        with patch.object(agent, 'generate_sql_with_retry', return_value=('SELECT 1', {'success':True})) as generate:
            agent.query(question)
        agent.retriever.rag_retrieve.assert_called_once_with('birth date?')
        self.assertEqual(generate.call_args.args[0], question)

    def test_summary_distinguishes_incorrect_and_unscored(self):
        rows = [{'correct':True,'execution_success':True}, {'correct':False,'execution_success':False}, {'correct':None,'execution_success':True}]
        result = summary(rows, 3)
        self.assertEqual(result['correct'], 1)
        self.assertEqual(result['incorrect'], 1)
        self.assertEqual(result['unscored'], 1)
        self.assertAlmostEqual(result['accuracy_percent'], 100/3)
