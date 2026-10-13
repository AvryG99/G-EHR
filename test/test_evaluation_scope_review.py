import unittest
from evaluation.scope_review import scope_violation


class ScopeReviewTests(unittest.TestCase):
    def test_actual_leaking_or_query(self):
        self.assertTrue(scope_violation("SELECT text FROM noteevents WHERE subject_id=13702 AND hadm_id=196489 AND LOWER(text) LIKE '%mi%' OR LOWER(text) LIKE '%myocardial infarction%'",13702,196489))

    def test_parenthesized_text_alternatives_are_safe(self):
        self.assertFalse(scope_violation("SELECT text FROM noteevents WHERE subject_id=13702 AND hadm_id=196489 AND (LOWER(text) LIKE '%mi%' OR LOWER(text) LIKE '%myocardial infarction%')",13702,196489))

    def test_each_or_branch_scoped_is_safe(self):
        self.assertFalse(scope_violation('SELECT text FROM noteevents WHERE (subject_id=1 AND hadm_id=2) OR (subject_id=1 AND hadm_id=2 AND text IS NOT NULL)',1,2))

    def test_complex_query_requires_separate_review(self):
        self.assertFalse(scope_violation('WITH n AS (SELECT * FROM noteevents) SELECT * FROM n WHERE subject_id=1 AND hadm_id=2',1,2))
