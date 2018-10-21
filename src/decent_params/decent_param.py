from contracts import contract, describe_type, describe_value

from decent_params import Choice

from .exceptions import DecentParamsSemanticError
# from optparse import Option


not_given = 'DefaultNotGiven'

class DecentParam(object):
    
    def __init__(self, ptype, name, default=not_given, help=None,  # @ReservedAssignment
                short=None, allow_multi=False, group=None):
        compulsory = (default == not_given)
        if compulsory: 
            default = None
        self.ptype = ptype
        self.name = name
        self.default = default  
        self.desc = help
        self.compulsory = compulsory
        self.short = short
        self.order = None
        self.allow_multi = allow_multi
        self.group = group

        self.params = None  # the DecentParams structure

        if self.default is not None:
            self.validate(self.default)
        
        
    def __repr__(self):
        return 'DecentParam(%r,%r)' % (self.ptype, self.name)
    
    def validate(self, value):
        self.check_type(value)
 
    def set_from_string(self, s):
        self._value = self.value_from_string(s)
                 
    def value_from_string(self, s):
        """ Possibly returns Choice(options) """
        print('%s %s' % (s, self.ptype))
        sep = ','
        if isinstance(s, str) and sep in s:
            return Choice([self.value_from_string(x) 
                           for x in s.split(sep)])
        
        if self.ptype == str:
            return str(s)
        if self.ptype == float:
            return float(s)
        if self.ptype == int:
            return int(s)  # TODO: check
        if self.ptype == bool:
            res = bool(s)  # TODO: check
            print('s %s -> %s' % (s, res))
            return res 
        msg = 'Unknown type %r' % self.ptype
        raise DecentParamsSemanticError(self.params, self, msg)
    
    def check_type(self, x):
        expected = self.ptype
        if self.ptype == float:
            expected = (float, int)
            
        if not isinstance(x, expected):
            msg = ("For param %r, expected %s, got %s.\n%s" % 
                    (self.name, self.ptype, describe_type(x),
                     describe_value(x)))
            raise DecentParamsSemanticError(self.params, self, msg)
    
    def get_desc(self):
        desc = self.desc
        if self.compulsory:
            desc = '[*required*] %s' % desc
        elif self.default is not None:
            desc = '[default: %8s] %s' % (self.default, desc) 
        return desc
    
    def populate(self, parser):
        option = '--%s' % self.name
        
        nargs = '+' if self.allow_multi else 1
        other = dict(help=self.get_desc(), default=self.default,
                     nargs=nargs)
        other['type'] = self.ptype
        if self.short is not None:
            parser.add_argument(self._get_short_option(), option, **other)
        else:
            parser.add_argument(option, **other)
         
    def _get_short_option(self):
        short = self.short
        short = short.replace('-', '')
        option1 = '-%s' % short
        return option1


class DecentParamsResults(object):
    def __init__(self, values, given, params, extra=None):
        self._values = values
        self._given = given
        self._params = params
        self._extra = extra

        for k, v in values.items():
            self.__dict__[k] = v

    def __repr__(self):
        return 'DecentParamsResults(%r,given=%r,extra=%r)' % (self._values, self._given, self._extra)

    def __str__(self):
        return 'DPR(values=%s;given=%s;extra=%s)' % (self._values, self._given, self._extra)

    def get_extra(self):
        return self._extra

    def get_params(self):
        """ Returns the DecentParams structure which originated these results. """
        return self._params

    def __getitem__(self, name):
        return self._values[name]

    def given(self, name):
        return name in self._given
    
# class MyOption(Option):
#
#     ACTIONS = Option.ACTIONS + ("extend",)
#     STORE_ACTIONS = Option.STORE_ACTIONS + ("extend",)
#     TYPED_ACTIONS = Option.TYPED_ACTIONS + ("extend",)
#     ALWAYS_TYPED_ACTIONS = Option.ALWAYS_TYPED_ACTIONS + ("extend",)
#
#     def take_action(self, action, dest, opt, value, values, parser):
#         if action == "extend":
#             lvalue = value.split(",")
#             values.ensure_value(dest, []).extend(lvalue)
#         else:
#             Option.take_action(
#                 self, action, dest, opt, value, values, parser)

class DecentParamMultiple(DecentParam):
    """ Allow multiple values """    
    
    def __init__(self, ptype, name, default=not_given, **args):
        if default is not not_given:
            if not isinstance(default, list):
                default = [default]
        DecentParam.__init__(self, ptype=ptype, name=name, default=default,
                             **args)
        
    @contract(s='str')
    def value_from_string(self, s):
        values = [DecentParam.value_from_string(self, x) for x in s.split(',')]
        return values

    def validate(self, value):
        if not isinstance(value, list):
            msg = "Should be a list, not %r" % value
            raise DecentParamsSemanticError(self.params, self, msg)
        for x in value:
            self.check_type(x)
    
    def populate(self, parser):
        option = '--%s' % self.name

        other = dict(nargs='+',type=self.ptype, 
                            help=self.get_desc(), default=self.default)

#         other = dict(nargs=1, type=self.ptype, action='append',
#                             help=self.get_desc(), default=self.default)

        if self.short is not None:
            parser.add_argument(self._get_short_option(), option, **other)
        else:
            parser.add_argument(option, **other)


              
class DecentParamFlag(DecentParam):
    def populate(self, parser, default=False):
        option = '--%s' % self.name
        other = dict(help=self.desc, default=default, action='store_true')

        if self.short is not None:
            parser.add_argument(self._get_short_option(), option, **other)
        else:
            parser.add_argument(option, **other)

      
        
class DecentParamChoice(DecentParam):
    def __init__(self, choices, **args):
        self.choices = choices
        DecentParam.__init__(self, **args)
        
    def validate(self, value):
        if not value in self.choices:
            msg = 'Not %r in %r' % (value, self.choices)
            raise DecentParamsSemanticError(self.params, self, msg)
    
