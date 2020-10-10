import unittest as test
from importlib import import_module
import os
import sys

sys.path.append('../app/')
from FormalSystem import zeroth_order_logic as zol

class Test_true_and(test.TestCase):

    def setUp(self):
        self.rule = zol.RULES['true and'].func

    def test_basic(self):
        self.assertEqual(self.rule('<sentvar_p><and_^><sentvar_q>'),
                         (('<sentvar_p>', '<sentvar_q>'),))

    def test_basicbracket(self):
        self.assertEqual(
            self.rule('(<sentvar_p>)<and_^>(<sentvar_q>)'), (('<sentvar_p>', '<sentvar_q>'),))

    def test_double(self):
        self.assertEqual(self.rule('(<sentvar_p><and_^><sentvar_q>)<and_^><sentvar_r>'),
                         (('<sentvar_p><and_^><sentvar_q>', '<sentvar_r>'),))

    def test_wrong_rule(self):
        self.assertEqual(self.rule('<sentvar_p><or_or><sentvar_q>'), tuple())

    def test_brackets(self):
        self.assertEqual(self.rule('(<sentvar_p><or_or><sentvar_r>)<and_^>(<sentvar_q><or_or>(<not_~><sentvar_r>))'),
                         (('<sentvar_p><or_or><sentvar_r>', '<sentvar_q><or_or>(<not_~><sentvar_r>)'),))

    def test_more_brackets(self):
        self.assertEqual(self.rule('((<not_~><sentvar_q>)<or_or><sentvar_r>)<and_^>((<sentvar_q>)<or_or>(<not_~>(<sentvar_r>)))'),
                         (('(<not_~><sentvar_q>)<or_or><sentvar_r>', '(<sentvar_q>)<or_or>(<not_~>(<sentvar_r>))'),))


class Test_true_or(test.TestCase):

    def setUp(self):
        self.rule = zol.RULES['true or'].func

    def test_basic(self):
        self.assertEqual(self.rule('<sentvar_p><or_or><sentvar_q>'),
                         (('<sentvar_p>'), ('<sentvar_q>')))

    def test_basicbracket(self):
        self.assertEqual(self.rule(
            '(<sentvar_p>)<or_or>(<sentvar_q>)'), (('<sentvar_p>'), ('<sentvar_q>')))

    def test_double(self):
        self.assertEqual(self.rule('(<sentvar_p><or_or><sentvar_q>)<or_or>(<sentvar_r>)'), ((
            '<sentvar_p><or_or><sentvar_q>'), ('<sentvar_r>')))

    def test_wrong_rule(self):
        self.assertEqual(self.rule('<sentvar_p><and_^><sentvar_q>'), tuple())

    def test_brackets(self):
        self.assertEqual(self.rule('(<sentvar_p><and_and><sentvar_r>)<or_v>(<sentvar_q><or_or>(<not_~><sentvar_r>))'), ((
            '<sentvar_p><and_and><sentvar_r>'), ('<sentvar_q><or_or>(<not_~><sentvar_r>)')))

    def test_more_brackets(self):
        self.assertEqual(self.rule('((<not_~><sentvar_q>)<and_and><sentvar_r>)<or_v>((<sentvar_q>)<or_or>(<not_~>(<sentvar_r>)))'), ((
            '(<not_~><sentvar_q>)<and_and><sentvar_r>'), ('(<sentvar_q>)<or_or>(<not_~>(<sentvar_r>))')))


class Test_false_and(test.TestCase):

    def setUp(self):
        self.rule = zol.RULES['false and'].func

    def test_basic(self):
        self.assertEqual(self.rule('<not_~>(<sentvar_p><and_^><sentvar_q>)'), ((
            '<not_~><sentvar_p>'), ('<not_~><sentvar_q>')))

    def test_basicbracket(self):
        self.assertEqual(self.rule('<not_~>((<sentvar_p>)<and_^>(<sentvar_q>))'), ((
            '<not_~><sentvar_p>'), ('<not_~><sentvar_q>')))

    def test_double(self):
        self.assertEqual(self.rule('<not_~>((<sentvar_p><and_^><sentvar_q>)<and_^><sentvar_r>)'), ((
            '<not_~>(<sentvar_p><and_^><sentvar_q>)'), ('<not_~><sentvar_r>')))

    def test_wrong_rule(self):
        self.assertEqual(
            self.rule('<not_~>(<sentvar_p><or_or><sentvar_q>)'), tuple())

    def test_fist_negated(self):
        self.assertEqual(
            self.rule('<not_~><sentvar_p><and_^><sentvar_q>'), tuple())

    def test_brackets(self):
        self.assertEqual(self.rule('<not_~>((<sentvar_p><or_or><sentvar_r>)<and_^>(<sentvar_q><or_or>(<not_~><sentvar_r>)))'), ((
            '<not_~>(<sentvar_p><or_or><sentvar_r>)'), ('<not_~>(<sentvar_q><or_or>(<not_~><sentvar_r>))')))

    def test_more_brackets(self):
        self.assertEqual(self.rule('<not_~>(((<not_~><sentvar_q>)<or_or><sentvar_r>)<and_^>((<sentvar_q>)<or_or>(<not_~>(<sentvar_r>))))'), ((
            '<not_~>((<not_~><sentvar_q>)<or_or><sentvar_r>)'), ('<not_~>((<sentvar_q>)<or_or>(<not_~>(<sentvar_r>)))')))


class Test_false_or(test.TestCase):

    def setUp(self):
        self.rule = zol.RULES['false or'].func

    def test_basic(self):
        self.assertEqual(self.rule('<not_~>(<sentvar_p><or_or><sentvar_q>)'),
                         (('<not_~><sentvar_p>', '<not_~><sentvar_q>'),))

    def test_basicbracket(self):
        self.assertEqual(self.rule('<not_~>((<sentvar_p>)<or_or>(<sentvar_q>))'),
                         (('<not_~><sentvar_p>', '<not_~><sentvar_q>'),))

    def test_double(self):
        self.assertEqual(self.rule('<not_~>((<sentvar_p><or_or><sentvar_q>)<or_or>(<sentvar_r>))'),
                         (('<not_~>(<sentvar_p><or_or><sentvar_q>)', '<not_~><sentvar_r>'),))

    def test_wrong_rule(self):
        self.assertEqual(
            self.rule('<not_~>(<sentvar_p><and_^><sentvar_q>)'), tuple())

    def test_fist_negated(self):
        self.assertEqual(
            self.rule('<not_~><sentvar_p><or_or><sentvar_q>'), tuple())

    def test_brackets(self):
        self.assertEqual(self.rule('<not_~>((<sentvar_p><and_and><sentvar_r>)<or_v>(<sentvar_q><or_or>(<not_~><sentvar_r>)))'),
                         (('<not_~>(<sentvar_p><and_and><sentvar_r>)', '<not_~>(<sentvar_q><or_or>(<not_~><sentvar_r>))'),))

    def test_more_brackets(self):
        self.assertEqual(self.rule('<not_~>(((<not_~><sentvar_q>)<and_and><sentvar_r>)<or_v>((<sentvar_q>)<or_or>(<not_~>(<sentvar_r>))))'),
                         (('<not_~>((<not_~><sentvar_q>)<and_and><sentvar_r>)', '<not_~>((<sentvar_q>)<or_or>(<not_~>(<sentvar_r>)))'),))


class Test_double_neg(test.TestCase):

    def setUp(self):
        self.rule = zol.RULES['double not'].func

    def test_basic(self):
        self.assertEqual(self.rule(
            '<not_~><not_~>(<sentvar_p><or_or><sentvar_q>)'), ('<sentvar_p><or_or><sentvar_q>'))

    def test_wrong_amount1(self):
        self.assertEqual(
            self.rule('<not_~>(<sentvar_p><and_^><sentvar_q>)'), tuple())

    def test_wrong_amount0(self):
        self.assertEqual(self.rule('<sentvar_p><and_^><sentvar_q>'), tuple())

    def test_long(self):
        self.assertEqual(self.rule('<not_~><not_~>(((<not_~><sentvar_q>)<and_and><sentvar_r>)<or_v>((<sentvar_q>)<or_or>(<not_~>(<sentvar_r>))))'),
                         ('((<not_~><sentvar_q>)<and_and><sentvar_r>)<or_v>((<sentvar_q>)<or_or>(<not_~>(<sentvar_r>)))'))

    def test_middlebracket(self):
        self.assertEqual(self.rule(
            '<not_~>(<not_~>(<sentvar_p><or_or><sentvar_q>))'), ('<sentvar_p><or_or><sentvar_q>'))

    def test_nobracket(self):
        self.assertEqual(
            self.rule('<not_~><not_~><sentvar_p>'), ('<sentvar_p>'))


class Test_check_contradict(test.TestCase):

    def test_true_basic(self):
        self.assertIs(zol.check_contradict(
            '<not_~><sentvar_p>', '<sentvar_p>'), True)

    def test_false_basic(self):
        self.assertIs(zol.check_contradict(
            '<sentvar_p>', '<sentvar_p>'), False)

    def test_double_neg(self):
        self.assertIs(zol.check_contradict(
            '<not_~><not_~><sentvar_p>', '<sentvar_p>'), False)

    def test_true_notation_change(self):
        self.assertIs(zol.check_contradict(
            '<not_not><sentvar_p>', '<sentvar_p>'), True)

    def test_true_long(self):
        self.assertIs(zol.check_contradict('<not_~>((<sentvar_p><and_^><sentvar_q>)<and_^><sentvar_r>)',
                                           '(<sentvar_p><and_^><sentvar_q>)<and_^><sentvar_r>'), True)

    def test_true_reversed(self):
        self.assertIs(zol.check_contradict(
            '<sentvar_p>', '<not_~><sentvar_p>'), True)


class Test_bracket_reduction(test.TestCase):

    def test_nobrackets(self):
        self.assertEqual(zol.reduce_brackets(
            '<sentvar_p><and_^><sentvar_q>'), '<sentvar_p><and_^><sentvar_q>')

    def test_simple(self):
        self.assertEqual(zol.reduce_brackets(
            '(<sentvar_p><and_^><sentvar_q>)'), '<sentvar_p><and_^><sentvar_q>')

    def test_left_not_reductable(self):
        self.assertEqual(zol.reduce_brackets(
            '<not_~>(<sentvar_p><and_^><sentvar_q>)'), '<not_~>(<sentvar_p><and_^><sentvar_q>)')

    def test_right_not_reductable(self):
        self.assertEqual(zol.reduce_brackets('(<sentvar_p><and_^><sentvar_q>)<and_^><sentvar_q>'),
                         '(<sentvar_p><and_^><sentvar_q>)<and_^><sentvar_q>')

    def test_complex_reductable(self):
        self.assertEqual(zol.reduce_brackets('((<not_~>((<sentvar_p><and_^><sentvar_q>)<and_^><sentvar_r>)))'),
                         '<not_~>((<sentvar_p><and_^><sentvar_q>)<and_^><sentvar_r>)')

    def test_complex(self):
        self.assertEqual(zol.reduce_brackets('<not_~>((<sentvar_p><and_^><sentvar_q>)<and_^><sentvar_r>)'),
                         '<not_~>((<sentvar_p><and_^><sentvar_q>)<and_^><sentvar_r>)')

    def test_double_and(self):
        self.assertEqual(zol.reduce_brackets('(<sentvar_p><and_^><sentvar_q>)<and_^>(<sentvar_p><and_^><sentvar_q>)'),
                         '(<sentvar_p><and_^><sentvar_q>)<and_^>(<sentvar_p><and_^><sentvar_q>)')

    def test_double_and_reductable(self):
        self.assertEqual(zol.reduce_brackets('((((<sentvar_p><and_^><sentvar_q>)<and_^>(<sentvar_p><and_^><sentvar_q>))))'),
                         '(<sentvar_p><and_^><sentvar_q>)<and_^>(<sentvar_p><and_^><sentvar_q>)')

    def test_long_complex_reductable(self):
        self.assertEqual(zol.reduce_brackets('((<not_~>(<not_~>(((<not_~><sentvar_q>)<and_and><sentvar_r>)<or_v>((<sentvar_q>))<or_or>(<not_~>(<sentvar_r>))))))'),
                         '<not_~>(<not_~>(((<not_~><sentvar_q>)<and_and><sentvar_r>)<or_v>((<sentvar_q>))<or_or>(<not_~>(<sentvar_r>))))')

    def test_long_complex(self):
        self.assertEqual(zol.reduce_brackets('<not_~>(<not_~>(((<not_~><sentvar_q>)<and_and><sentvar_r>)<or_v>((<sentvar_q>))<or_or>(<not_~>(<sentvar_r>))))'),
                         '<not_~>(<not_~>(((<not_~><sentvar_q>)<and_and><sentvar_r>)<or_v>((<sentvar_q>))<or_or>(<not_~>(<sentvar_r>))))')

if __name__ == "__main__":
    test.main()
