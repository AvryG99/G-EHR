import unittest
from evaluation.run_bigquery_batch import scores, summarize


class EvaluationScoringTests(unittest.TestCase):
    def test_normalized_exact_match(self):
        self.assertEqual(scores('The COPD exacerbation.', ['copd exacerbation']), (1, 1))

    def test_best_reference_and_partial_f1(self):
        em, f1 = scores('acute copd', ['unrelated finding', 'acute copd exacerbation'])
        self.assertEqual(em, 0)
        self.assertAlmostEqual(f1, .8)

    def test_failed_queries_count_in_denominator(self):
        records = [dict(semantic_correct=True, execution_success=True, row_count=1, exact_match=0, token_f1=.5),
                   dict(semantic_correct=False, execution_success=False, exact_match=0, token_f1=0)]
        result = summarize(records, 2)
        self.assertEqual(result['semantic_accuracy_percent'], 50)
        self.assertEqual(result['token_f1_percent'], 25)
        self.assertEqual(result['status'], 'complete')
