#!/usr/bin/env python
import unittest
from filesort import unify_case

class UnifyCaseTests(unittest.TestCase):
    non_capital_words = ('to', 'a', 'from', 'is', 'and', 'the')
    non_capital_words_cases = (('test to case', 'Test to Case'),
        ('test a case', 'Test a Case'),
        ('test from case', 'Test from Case'),
        ('test is case', 'Test is Case'),
        ('test and case', 'Test and Case'),
        ('test the case', 'Test the Case'),
    )

    def test_does_capitalize_first_letter_of_each_word(self):
        self.assertEqual(unify_case('complete this test'),
            'Complete This Test')

    def test_only_first_letter_of_each_word_capitalized(self):
        self.assertEqual(unify_case('COMPLETE THIS TEST'),
            'Complete This Test')

    def test_does_not_capitalize_special_cases_in_middle_of_string(self):
        for case,result in self.non_capital_words_cases:
            self.assertEqual(unify_case(case), result)

    def test_does_capitalize_special_cases_at_begin_of_string(self):
        for word in self.non_capital_words:
            self.assertEqual(unify_case(word), word.title())

    def test_converts_dots_into_spaces(self):
        self.assertEqual(unify_case('test.case'), 'Test Case')

    def test_removes_leading_whitespace(self):
        self.assertEqual(unify_case('    test'), 'Test')

    def test_removes_trailing_whitespace(self):
        self.assertEqual(unify_case('test    '), 'Test')

    def test_removes_extra_whitespace_between_words(self):
        self.assertEqual(unify_case('test    case'), 'Test Case')

if __name__ == '__main__':
    unittest.main()
