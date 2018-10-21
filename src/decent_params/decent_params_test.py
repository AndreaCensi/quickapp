from __future__ import print_function
from __future__ import print_function
from __future__ import print_function
import unittest

from nose.tools import raises

from decent_params import DecentParams, UserError, DecentParamsUnknownArgs


class ParamsTest(unittest.TestCase):
        
    def decent_params_test0(self):
        
        p = DecentParams()
        p.add_float_list('floats')
        
        args = ['--floats', '1.2', '2.3']
        
        try:    
            res = p.parse_args(args)
        except SystemExit as e:
            print(e)
            raise Exception(str(e))
        
        self.assertEqual(res.given('floats'), True)
        self.assertEqual(res.given('int1'), False)
        self.assertEqual(res['floats'], [1.2, 2.3])
        
    def decent_params_test1(self):
        
        p = DecentParams()
        p.add_string('vehicle', default='x')
        p.add_float('float1')
        p.add_float_list('floats')
        p.add_int('int1', default=0)
        p.add_int_list('ints')
        p.add_string_choice('ciao', ['2', '1'], default='1')
        p.add_int_choice('ciao2', [2, 1], default=1)
        
        args = ['--vehicle', 'y',
                '--float1', '1.2',
                '--floats', '1.2', '2.3',
                '--ints', '1', '2', '3']
        
        try:    
            res = p.parse_args(args)
        except SystemExit as e:
            print(e)
            raise Exception(str(e))
        
        self.assertEqual(res.given('floats'), True)
        self.assertEqual(res.given('int1'), False)
        self.assertEqual(res['ciao'], '1')
        self.assertEqual(res['ciao2'], 1)
        self.assertEqual(res.ciao, '1')
        self.assertEqual(res.ciao2, 1)
        self.assertEqual(res.floats, [1.2, 2.3])
        self.assertEqual(res.ints, [1, 2, 3])
        
    @raises(UserError)
    def decent_params_test2(self):
        """ Test compulsory """
        p = DecentParams()
        p.add_string('a')
        p.add_string('b')
        res = p.parse_args(['--b', '1'])
        print(res)
        
    
    def decent_params_test_notdefined(self):
        p = DecentParams()
        p.add_string('vehicle', default='x')
        
        self.assertRaises(DecentParamsUnknownArgs, p.parse_args, ['--b', '1'])
        
