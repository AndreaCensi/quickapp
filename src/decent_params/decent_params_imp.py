from .decent_param import (DecentParam, DecentParamChoice, DecentParamFlag, 
    DecentParamMultiple, DecentParamsResults)
from .exceptions import (DecentParamsDefinitionError, DecentParamsUnknownArgs, 
    DecentParamsUserError)
from argparse import RawTextHelpFormatter
from contracts import contract
from decent_params import Choice
from pprint import pformat
import argparse

__all__ = ['DecentParams']

class DecentParams(object):
    
    def __init__(self, usage=None, prog=None):
        self.usage = usage
        self.prog = prog
        self.params = {}
        self.accepts_extra = False
    
    def __str__(self):
        return 'DecentParams(%s;extra=%s)' % (pformat(self.params), self.accepts_extra) 
     
    def _add(self, p):
        if p.name in self.params:
            msg = "I already know param %r." % p.name
            raise DecentParamsDefinitionError(msg)
        p.order = len(self.params)
        self.params[p.name] = p
        
    def accept_extra(self):
        """ Declares that extra arguments are ok. """
        self.accepts_extra = True
          
    def add_flag(self, name, **args):
        self._add(DecentParamFlag(ptype=bool, name=name, default=False, **args))

    def add_string(self, name, **args):
        self._add(DecentParam(ptype=str, name=name, **args))
        
    def add_float(self, name, **args):
        self._add(DecentParam(ptype=float, name=name, **args))

    def add_int(self, name, **args):
        self._add(DecentParam(ptype=int, name=name, **args))

    def add_string_list(self, name, **args):
        self._add(DecentParamMultiple(ptype=str, name=name, **args))
        
    def add_float_list(self, name, **args):
        self._add(DecentParamMultiple(ptype=float, name=name, **args))

    def add_int_list(self, name, **args):
        self._add(DecentParamMultiple(ptype=int, name=name, **args))
    
    def add_int_choice(self, name, choices, **args):
        self._add(DecentParamChoice(name=name, choices=choices, ptype=int, **args))

    def add_float_choice(self, name, choices, **args):
        self._add(DecentParamChoice(name=name, choices=choices, ptype=float, **args))

    def add_string_choice(self, name, choices, **args):
        self._add(DecentParamChoice(name=name, choices=choices, ptype=str, **args))
    
    def parse_args(self, args, allow_choice=True):  # TODO @UnusedVariable
        parser = self.create_parser() 
        values, given = self.parse_using_parser(parser, args)
        # TODO: check no Choice()
        res = DecentParamsResults(values, given, self.params) 
        return res

    @contract(args='list(str)', returns='tuple(dict, list(str))')    
    def parse_using_parser(self, parser, args):
        """ 
            Returns a dictionary with all values of parameters,
            but possibly some values are Choice() instances.
            
        """
        try:
            argparse_res, argv = parser.parse_known_args(args)
            if argv:
                msg = 'Extra arguments found: %s' % argv
                raise DecentParamsUnknownArgs(self, msg)
        except SystemExit:
            raise  # XXX
            # raise Exception(e)  # TODO
        
        values, given = self._interpret_args(argparse_res)
        return values, given
    
    @contract(args='list(str)', returns='tuple(dict, list(str), list(str))')    
    def parse_using_parser_extra(self, parser, args):
        """ 
            This returns also the extra parameters
            
            returns: values, given, argv
        """
        
        if self.accepts_extra:
            parser.add_argument('remainder', nargs=argparse.REMAINDER)

        try:
            argparse_res, unknown = parser.parse_known_args(args)
        except SystemExit:
            raise  # XXX
        
        if unknown:
            raise DecentParamsUnknownArgs(self, unknown)
    
        if self.accepts_extra:
            extra = argparse_res.remainder
        else:
            extra = []

        values, given = self._interpret_args(argparse_res)
        # TODO: raise if extra is given
        return values, given, extra
    
    def _interpret_args(self, argparse_res):
        parsed = vars(argparse_res)
        return self._interpret_args2(parsed)
    
    @contract(parsed='dict', returns='tuple(dict, list(str))')
    def _interpret_args2(self, parsed):
        values = dict()
        given = set()
        for k, v in self.params.items():
            # if v.compulsory and parsed[k] is None:
            if v.compulsory and (not k in parsed or parsed[k] is None):
                msg = 'Compulsory option %r not given.' % k
                raise DecentParamsUserError(self, msg)
            
            #warnings.warn('Not sure below')
            # if parsed[k] is not None:
            if k in parsed and parsed[k] is not None:
                if parsed[k] != self.params[k].default:
                    given.add(k)
                    if isinstance(self.params[k], DecentParamMultiple):
                        if isinstance(parsed[k], list):
                            values[k] = parsed[k]
                        else:
                            values[k] = [parsed[k]]
                    else:
                        if isinstance(parsed[k], list):
                            if len(parsed[k]) > 1:
                                values[k] = Choice(parsed[k])
                            else:
                                values[k] = parsed[k][0]
                        else:
                            values[k] = parsed[k]
                    # values[k] = self.params[k].value_from_string(parsed[k])
                else:
                    values[k] = self.params[k].default
            else:
                values[k] = self.params[k].default
        return values, list(given) 
        
    def _populate_parser(self, option_container, prog=None):
        groups = set(p.group for p in self.params.values())
        for g in groups:
            
            if g is None:  # normal arguments:
                title = 'Arguments for %s' % prog 
            else:
                title = str(g)
            description = None
            group = option_container.add_argument_group(title=title, description=description)
            g_params = [p for p in self.params.values() if p.group == g] 
            for p in g_params:
                p.populate(group)
#                 
#         print groups
#         params = sorted(self.params.values(), key=lambda x: x.order)
#         for p in params:
#             
    
    def create_parser(self, prog=None, usage=None, epilog=None,
                          description=None):
        def my_formatter(prog):
            return RawTextHelpFormatter(prog=prog,
                                        max_help_position=90, width=None)
        
        class MyParser(argparse.ArgumentParser):
            
            def error(self, msg):
                raise DecentParamsUserError(self, msg)
            
        parser = MyParser(prog=prog, usage=usage, epilog=epilog,
                                        description=description,
                                        formatter_class=my_formatter)
        self._populate_parser(option_container=parser, prog=prog)
        return parser
    
    
    @contract(args='list(str)')
    def get_dpr_from_args(self, args, prog=None, usage=None, epilog=None,
                          description=None):
        parser = self.create_parser(prog=prog, usage=usage, epilog=epilog, description=description)

        values, given, extra = self.parse_using_parser_extra(parser, args)
        if extra and not self.accepts_extra:
            msg = 'Found extra arguments not accepted: %s' % extra
            raise DecentParamsUserError(self, msg)
        dpr = DecentParamsResults(values, given, self, extra=extra)
        return dpr
    
 
    @contract(config='dict(str:*)')
    def get_dpr_from_dict(self, config):
        extra = []  # TODO 
        values, given = self._interpret_args2(config)
        dpr = DecentParamsResults(values, given, self, extra=extra)
        return dpr

