import unittest as test
from importlib import import_module
import os
import sys

sys.path.append('../app/')
from Syntax import basic

class TestTokenize(test.TestCase):
    # TODO: Rozbudować

    def test_word(self):
        self.assertEqual(basic.tokenize("p or q", ['or']).replace(" ", ""), "p<c_or_or>q")

    def test_symbol(self):
        self.assertEqual(basic.tokenize("p v q", ['or']).replace(" ", ""), "p<c_or_v>q")

    def test_full(self):
        self.assertEqual(basic.tokenize("p v q", ['or', 'sentence']).replace(" ", ""), "<v_sentence_p><c_or_v><v_sentence_q>")

    def test_bracket(self):
        self.assertEqual(basic.tokenize("(p v q)", ['or', 'sentence']).replace(" ", ""), "(<v_sentence_p><c_or_v><v_sentence_q>)")


if __name__ == "__main__":
    test.main()
