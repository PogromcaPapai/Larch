import unittest as test
from importlib import import_module
from logicninja import pop_engine
example1 = import_module('.example1','tests')

class Test_GenerateFuncDataStructure(test.TestCase):
        
    def test_addition(self):
        obj = pop_engine.gen_functionDS('', int, int, int)
        self.assertEqual(obj, ('', ((int, int), int)))

    def test_addition_list(self):
        obj = pop_engine.gen_functionDS('', int, *(int, int))
        self.assertEqual(obj, ('', ((int, int), int)))

    def test_NoArgs_None(self):
        obj = pop_engine.gen_functionDS('', None)
        self.assertEqual(obj, ('', ((), None)))

    def test_NoArgs_int(self):
        obj = pop_engine.gen_functionDS('', int)
        self.assertEqual(obj, ('', ((), int)))

    def test_4args_int(self):
        obj = pop_engine.gen_functionDS('', int, str, int, list, tuple)
        self.assertEqual(obj, ('', ((str, int, list, tuple), int)))

    
class TestFunctionFit(test.TestCase):

    def setUp(self):
        funcs = dict((
            pop_engine.gen_functionDS('add', int, int, int),
            pop_engine.gen_functionDS('sub', int, int, int),
            pop_engine.gen_functionDS('sub_wrongin', int, int, int),
            pop_engine.gen_functionDS('sub_wrongout', int, int, int),
            pop_engine.gen_functionDS('random', int),
            pop_engine.gen_functionDS('str_int_none', None, str, int)
        ))
        self.socket = pop_engine.Socket('test', funcs)

    def test_addition(self):
        self.assertTrue(self.socket._functionfit(example1.add))

    def test_str_int_none(self):
        self.assertTrue(self.socket._functionfit(example1.str_int_none))

    def test_no_in(self):
        self.assertTrue(self.socket._functionfit(example1.random))
    
    def test_not_plugged(self):
        self.assertTrue(self.socket._functionfit(example1.not_plugged))
    
    def test_sub_wrong_args(self):
        with self.assertRaises(pop_engine.FunctionInterfaceError):
            self.socket._functionfit(example1.sub_wrongin)

    def test_sub_wrong_return(self):
        with self.assertRaises(pop_engine.FunctionInterfaceError):
            self.socket._functionfit(example1.sub_wrongout)

# class TestSocketFit(test.TestCase):

#     def test_good_import(self):
        

if __name__ == "__main__":
    test.main()